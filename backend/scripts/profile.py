import os
import json
import re
import sqlite3
import sys

import pandas as pd


SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPTS_DIR, "..", "data", "hadiths.db")
DROPPED_ROWS_PATH = os.path.join(SCRIPTS_DIR, "..", "data", "dropped_lk_rows.json")

TEXT_COLUMNS = [
    "English_Text",
    "Arabic_Text",
    "English_Isnad",
    "Arabic_Isnad",
    "English_Matn",
    "Arabic_Matn",
]

LENGTH_COLUMNS = [
    "English_Text",
    "Arabic_Text",
    "English_Isnad",
    "Arabic_Isnad",
    "English_Matn",
    "Arabic_Matn",
]

SOURCE_COLUMNS = [
    "English_Text_Source",
    "Arabic_Text_Source",
    "English_Isnad_Source",
    "Arabic_Isnad_Source",
    "English_Matn_Source",
    "Arabic_Matn_Source",
]

FLAG_COLUMNS = [
    "Has_English_Content",
    "Has_Arabic_Content",
    "Has_English_Matn",
    "Has_Arabic_Matn",
]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _empty_mask(series):
    return series.isna() | (series.astype(str).str.strip() == "")


def _present_mask(series):
    return ~_empty_mask(series)


def _clean(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _grade_flags(*values):
    flags = set()
    for value in values:
        text = _clean(value).lower()
        if not text or text == "nan":
            continue
        if re.search(r"\b(sahih|saheeh|authentic)\b", text) or "صحيح" in text:
            flags.add("Sahih")
        if re.search(r"\b(hasan|good)\b", text) or "حسن" in text:
            flags.add("Hasan")
        if re.search(r"\b(da[\W_]*if|daeef|weak)\b", text) or "ضعيف" in text:
            flags.add("Da'if")
        if re.search(r"\b(maw?du[\W_]*|fabricated|forged)\b", text) or "موضوع" in text:
            flags.add("Mawdu")
    return flags


def _unknown_grade_reason(row):
    english = _clean(row.get("English_Grade", ""))
    arabic = _clean(row.get("Arabic_Grade", ""))
    english_missing = not english or english.lower() == "nan"
    arabic_missing = not arabic or arabic.lower() == "nan"

    if not row.get("Normalized_Grade") == "Unknown":
        return "not_unknown"
    if english_missing and arabic_missing:
        return "missing_both"

    english_flags = _grade_flags(english)
    arabic_flags = _grade_flags(arabic)
    combined = english_flags | arabic_flags
    if len(combined) > 1:
        return "mixed_conflicting"
    if english_missing:
        return "english_missing_arabic_unrecognized"
    if arabic_missing:
        return "arabic_missing_english_unrecognized"
    return "unrecognized_both"


def _norm_ws(value):
    return re.sub(r"\s+", " ", _clean(value)).strip()


def _starts_with(full, prefix):
    full = _norm_ws(full)
    prefix = _norm_ws(prefix)
    return bool(full and prefix and full.startswith(prefix))


def _ends_with(full, suffix):
    full = _norm_ws(full)
    suffix = _norm_ws(suffix)
    return bool(full and suffix and full.endswith(suffix))


def _prefix_remainder(full, prefix):
    full = _norm_ws(full)
    prefix = _norm_ws(prefix)
    if not full or not prefix or not full.startswith(prefix):
        return ""
    return full[len(prefix):].strip()


def _suffix_remainder(full, suffix):
    full = _norm_ws(full)
    suffix = _norm_ws(suffix)
    if not full or not suffix or not full.endswith(suffix):
        return ""
    return full[: -len(suffix)].strip()


def _print_section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def _print_samples(df, title, mask, columns, limit=5):
    sample = df.loc[mask, columns].head(limit)
    _print_section(title)
    if sample.empty:
        print("None")
    else:
        print(sample.to_string(index=False, max_colwidth=100))


def _print_grade_diagnostics(df):
    _print_section("Grade Normalization Diagnostics")
    en_missing = _empty_mask(df["English_Grade"])
    ar_missing = _empty_mask(df["Arabic_Grade"])
    normalized_known = df["Normalized_Grade"].ne("Unknown")

    rows = [
        {"metric": "English_Grade missing/empty", "count": int(en_missing.sum())},
        {"metric": "Arabic_Grade missing/empty", "count": int(ar_missing.sum())},
        {"metric": "Both grade fields missing/empty", "count": int((en_missing & ar_missing).sum())},
        {
            "metric": "English missing but Arabic recovered normalized grade",
            "count": int((en_missing & ~ar_missing & normalized_known).sum()),
        },
        {
            "metric": "Arabic missing but English recovered normalized grade",
            "count": int((ar_missing & ~en_missing & normalized_known).sum()),
        },
        {"metric": "Unknown normalized grades", "count": int(df["Normalized_Grade"].eq("Unknown").sum())},
    ]
    print(pd.DataFrame(rows).to_string(index=False))

    reasons = df.apply(_unknown_grade_reason, axis=1)
    unknown_reasons = reasons[reasons.ne("not_unknown")].value_counts()
    print("\nUnknown reason buckets:")
    print(unknown_reasons.to_string() if not unknown_reasons.empty else "None")

    unknown = df.loc[df["Normalized_Grade"].eq("Unknown")].copy()
    if not unknown.empty:
        unknown["Unknown_Reason"] = reasons.loc[unknown.index]
        print("\nTop raw English/Arabic grade pairs among Unknown:")
        pairs = (
            unknown.assign(
                English_Grade=unknown["English_Grade"].replace("", pd.NA),
                Arabic_Grade=unknown["Arabic_Grade"].replace("", pd.NA),
            )
            .groupby(["English_Grade", "Arabic_Grade", "Unknown_Reason"], dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(30)
        )
        print(pairs.to_string(index=False, max_colwidth=80))


def _reconstruction_rows(df, label, full_col, isnad_col, matn_col):
    full_missing = _empty_mask(df[full_col])
    isnad_missing = _empty_mask(df[isnad_col])
    matn_missing = _empty_mask(df[matn_col])
    full_present = ~full_missing
    isnad_present = ~isnad_missing
    matn_present = ~matn_missing

    matn_exact = df.apply(lambda row: bool(_prefix_remainder(row[full_col], row[isnad_col])), axis=1)
    isnad_exact = df.apply(lambda row: bool(_suffix_remainder(row[full_col], row[matn_col])), axis=1)

    return [
        {"language": label, "case": "Full text missing", "count": int(full_missing.sum())},
        {"language": label, "case": "Full missing, isnad + matn present", "count": int((full_missing & isnad_present & matn_present).sum())},
        {"language": label, "case": "Full missing, isnad only present", "count": int((full_missing & isnad_present & matn_missing).sum())},
        {"language": label, "case": "Full missing, matn only present", "count": int((full_missing & isnad_missing & matn_present).sum())},
        {"language": label, "case": "Full missing, neither split present", "count": int((full_missing & isnad_missing & matn_missing).sum())},
        {"language": label, "case": "Full reconstructable from any split", "count": int((full_missing & (isnad_present | matn_present)).sum())},
        {"language": label, "case": "Matn missing", "count": int(matn_missing.sum())},
        {"language": label, "case": "Matn missing, full text present", "count": int((matn_missing & full_present).sum())},
        {"language": label, "case": "Matn missing, isnad present", "count": int((matn_missing & isnad_present).sum())},
        {"language": label, "case": "Matn missing, full + isnad present", "count": int((matn_missing & full_present & isnad_present).sum())},
        {"language": label, "case": "Matn reconstructable: non-empty full minus isnad", "count": int((matn_missing & full_present & isnad_present & matn_exact).sum())},
        {"language": label, "case": "Isnad missing", "count": int(isnad_missing.sum())},
        {"language": label, "case": "Isnad missing, full text present", "count": int((isnad_missing & full_present).sum())},
        {"language": label, "case": "Isnad missing, matn present", "count": int((isnad_missing & matn_present).sum())},
        {"language": label, "case": "Isnad missing, full + matn present", "count": int((isnad_missing & full_present & matn_present).sum())},
        {"language": label, "case": "Isnad reconstructable: non-empty full minus matn", "count": int((isnad_missing & full_present & matn_present & isnad_exact).sum())},
    ]


def _print_reconstruction_diagnostics(df):
    _print_section("Text Reconstruction Feasibility")
    rows = []
    rows.extend(_reconstruction_rows(df, "English", "English_Text", "English_Isnad", "English_Matn"))
    rows.extend(_reconstruction_rows(df, "Arabic", "Arabic_Text", "Arabic_Isnad", "Arabic_Matn"))
    print(pd.DataFrame(rows).to_string(index=False))

    sample_columns = [
        "id",
        "Book",
        "Hadith_Number",
        "English_Text",
        "English_Isnad",
        "English_Matn",
        "Arabic_Text",
        "Arabic_Isnad",
        "Arabic_Matn",
    ]
    sample_columns = [column for column in sample_columns if column in df.columns]

    _print_samples(
        df,
        "Sample English full missing but split present",
        _empty_mask(df["English_Text"]) & (_present_mask(df["English_Isnad"]) | _present_mask(df["English_Matn"])),
        sample_columns,
    )
    _print_samples(
        df,
        "Sample English matn missing but full + isnad present",
        _empty_mask(df["English_Matn"]) & _present_mask(df["English_Text"]) & _present_mask(df["English_Isnad"]),
        sample_columns,
    )
    _print_samples(
        df,
        "Sample English isnad missing but full + matn present",
        _empty_mask(df["English_Isnad"]) & _present_mask(df["English_Text"]) & _present_mask(df["English_Matn"]),
        sample_columns,
    )
    _print_samples(
        df,
        "Sample Arabic full missing but split present",
        _empty_mask(df["Arabic_Text"]) & (_present_mask(df["Arabic_Isnad"]) | _present_mask(df["Arabic_Matn"])),
        sample_columns,
    )
    _print_samples(
        df,
        "Sample Arabic matn missing but full + isnad present",
        _empty_mask(df["Arabic_Matn"]) & _present_mask(df["Arabic_Text"]) & _present_mask(df["Arabic_Isnad"]),
        sample_columns,
    )
    _print_samples(
        df,
        "Sample Arabic isnad missing but full + matn present",
        _empty_mask(df["Arabic_Isnad"]) & _present_mask(df["Arabic_Text"]) & _present_mask(df["Arabic_Matn"]),
        sample_columns,
    )


def _print_provenance_and_flags(df):
    _print_section("Field Provenance")
    for column in SOURCE_COLUMNS:
        if column in df.columns:
            print(f"\n{column}")
            print(df[column].replace("", pd.NA).value_counts(dropna=False).to_string())

    _print_section("Content Flags")
    rows = []
    for column in FLAG_COLUMNS:
        if column in df.columns:
            rows.append({"flag": column, "count_true": int(df[column].astype(bool).sum()), "count_false": int((~df[column].astype(bool)).sum())})

    if {"Has_English_Content", "Has_Arabic_Content"}.issubset(df.columns):
        en = df["Has_English_Content"].astype(bool)
        ar = df["Has_Arabic_Content"].astype(bool)
        rows.extend([
            {"flag": "Both languages have content", "count_true": int((en & ar).sum()), "count_false": int((~(en & ar)).sum())},
            {"flag": "English-only content", "count_true": int((en & ~ar).sum()), "count_false": int((~(en & ~ar)).sum())},
            {"flag": "Arabic-only content", "count_true": int((~en & ar).sum()), "count_false": int((~(~en & ar)).sum())},
        ])

    if {"Has_English_Matn", "Has_Arabic_Matn"}.issubset(df.columns):
        en_matn = df["Has_English_Matn"].astype(bool)
        ar_matn = df["Has_Arabic_Matn"].astype(bool)
        rows.append({"flag": "Both languages have matn", "count_true": int((en_matn & ar_matn).sum()), "count_false": int((~(en_matn & ar_matn)).sum())})

    print(pd.DataFrame(rows).to_string(index=False) if rows else "No content flags found")

    _print_section("Dropped LK Rows Audit")
    if not os.path.exists(DROPPED_ROWS_PATH):
        print("No dropped-row audit file found")
        return
    with open(DROPPED_ROWS_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    print(f"Reason: {payload.get('reason')}")
    print(f"Count: {payload.get('count')}")
    rows = payload.get("rows", [])
    if rows:
        print(pd.DataFrame(rows).head(20).to_string(index=False))


def profile_hadith_df(df):
    _print_section("Overview")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(", ".join(df.columns))

    _print_section("Rows By Book")
    print(df["Book"].value_counts().sort_index().to_string())

    _print_section("Grade Distribution")
    if "Grade" in df.columns:
        print("Raw Grade:")
        print(df["Grade"].replace("", pd.NA).value_counts(dropna=False).head(40).to_string())
    if "Normalized_Grade" in df.columns:
        print("\nNormalized Grade:")
        print(df["Normalized_Grade"].replace("", pd.NA).value_counts(dropna=False).to_string())

    _print_grade_diagnostics(df)

    _print_section("Missing Or Empty Coverage")
    rows = []
    for column in TEXT_COLUMNS:
        if column not in df.columns:
            continue
        missing = int(_empty_mask(df[column]).sum())
        present = len(df) - missing
        rows.append({
            "column": column,
            "present": present,
            "missing_or_empty": missing,
            "coverage_pct": round((present / len(df)) * 100, 2) if len(df) else 0,
        })
    print(pd.DataFrame(rows).to_string(index=False))

    _print_section("Missing Or Empty Coverage By Book")
    for column in TEXT_COLUMNS:
        if column not in df.columns:
            continue
        coverage = (
            df.assign(_missing=_empty_mask(df[column]))
            .groupby("Book")
            .agg(rows=("id", "count"), missing=("_missing", "sum"))
        )
        coverage["coverage_pct"] = round(((coverage["rows"] - coverage["missing"]) / coverage["rows"]) * 100, 2)
        print(f"\n{column}")
        print(coverage.to_string())

    _print_section("Length Statistics")
    length_rows = []
    for column in LENGTH_COLUMNS:
        if column not in df.columns:
            continue
        lengths = df[column].fillna("").astype(str).str.len()
        stats = lengths.describe(percentiles=[0.25, 0.5, 0.75, 0.9]).to_dict()
        length_rows.append({
            "column": column,
            "min": int(stats["min"]),
            "p25": round(stats["25%"], 1),
            "median": round(stats["50%"], 1),
            "p75": round(stats["75%"], 1),
            "p90": round(stats["90%"], 1),
            "max": int(stats["max"]),
            "mean": round(stats["mean"], 1),
        })
    print(pd.DataFrame(length_rows).to_string(index=False))

    _print_section("Duplicate Checks")
    duplicate_book_hadith = df.duplicated(["Book", "Hadith_Number"], keep=False).sum()
    duplicate_chapter_hadith = df.duplicated(["Book", "Chapter_Number", "Hadith_Number"], keep=False).sum()
    print(f"Duplicate Book + Hadith_Number rows: {duplicate_book_hadith}")
    print(f"Duplicate Book + Chapter_Number + Hadith_Number rows: {duplicate_chapter_hadith}")

    sample_columns = [
        "id",
        "Book",
        "Hadith_Number",
        "English_Grade",
        "Arabic_Grade",
        "Normalized_Grade",
        "English_Matn",
        "Arabic_Matn",
    ]
    sample_columns = [column for column in sample_columns if column in df.columns]
    _print_samples(df, "Sample Missing English Matn", _empty_mask(df["English_Matn"]), sample_columns)
    _print_samples(df, "Sample Missing Arabic Matn", _empty_mask(df["Arabic_Matn"]), sample_columns)
    _print_samples(df, "Sample Unknown Grades", df["Normalized_Grade"].eq("Unknown"), sample_columns)
    _print_reconstruction_diagnostics(df)
    _print_provenance_and_flags(df)


def run():
    print(os.path.abspath(DB_PATH))
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM HADITHS", connection)
    finally:
        connection.close()

    profile_hadith_df(df)


if __name__ == "__main__":
    run()
