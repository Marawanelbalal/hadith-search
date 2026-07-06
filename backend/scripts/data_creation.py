import os
import re
import shutil
import sqlite3
import subprocess
import json
from pathlib import Path

import pandas as pd


LK_REPO_URL = "https://github.com/ShathaTm/LK-Hadith-Corpus.git"

SCRIPTS_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR.parent / "data"
DB_PATH = DATA_DIR / "hadiths.db"
DROPPED_ROWS_PATH = DATA_DIR / "dropped_lk_rows.json"
RAW_DATA_DIR = DATA_DIR / "raw"
DEFAULT_LK_PATH = RAW_DATA_DIR / "LK-Hadith-Corpus"

BOOK_ORDER = ["Bukhari", "Muslim", "AbuDaud", "Nesai", "IbnMaja", "Tirmizi"]
BOOK_NAME_MAP = {
    "Bukhari": "Sahih al-Bukhari",
    "Muslim": "Sahih Muslim",
    "AbuDaud": "Sunan Abi Dawud",
    "Nesai": "Sunan an-Nasa'i",
    "IbnMaja": "Sunan Ibn Majah",
    "Tirmizi": "Jami` at-Tirmidhi",
}

REQUIRED_COLUMNS = {
    "Chapter_Number",
    "Chapter_English",
    "Chapter_Arabic",
    "Section_Number",
    "Section_English",
    "Section_Arabic",
    "Hadith_number",
    "English_Hadith",
    "English_Isnad",
    "English_Matn",
    "Arabic_Hadith",
    "Arabic_Isnad",
    "Arabic_Matn",
    "English_Grade",
    "Arabic_Grade",
}

PREPROCESSING_COLUMNS = [
    "Preprocessed_English",
    "Preprocessed_Arabic",
    "Preprocessed_English_Isnad",
    "Preprocessed_Arabic_Isnad",
    "Preprocessed_English_Matn",
    "Preprocessed_Arabic_Matn",
]


def _clean_text(value):
    if pd.isna(value):
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _has_text(value):
    return bool(_clean_text(value))


def _source_for(value):
    return "lk_original" if _has_text(value) else "missing"


def _norm_ws(value):
    return re.sub(r"\s+", " ", _clean_text(value)).strip()


def _remove_prefix(full, prefix):
    full_clean = _norm_ws(full)
    prefix_clean = _norm_ws(prefix)
    if not full_clean or not prefix_clean or not full_clean.startswith(prefix_clean):
        return ""
    return full_clean[len(prefix_clean):].strip()


def _remove_suffix(full, suffix):
    full_clean = _norm_ws(full)
    suffix_clean = _norm_ws(suffix)
    if not full_clean or not suffix_clean or not full_clean.endswith(suffix_clean):
        return ""
    return full_clean[: -len(suffix_clean)].strip()


def _grade_flags(text):
    value = _clean_text(text).lower()
    if not value:
        return set()

    flags = set()
    if re.search(r"\b(sahih|saheeh|authentic)\b", value) or "صحيح" in value:
        flags.add("Sahih")
    if re.search(r"\b(hasan|good)\b", value) or "حسن" in value:
        flags.add("Hasan")
    if re.search(r"\b(da[\W_]*if|daeef|weak)\b", value) or "ضعيف" in value:
        flags.add("Da'if")
    if re.search(r"\b(maw?du[\W_]*|fabricated|forged)\b", value) or "موضوع" in value:
        flags.add("Mawdu")
    return flags


def normalize_grade(*grade_values):
    flags = set()
    for value in grade_values:
        flags.update(_grade_flags(value))

    if not flags:
        return "Unknown"
    if "Mawdu" in flags:
        return "Mawdu" if len(flags) == 1 else "Unknown"
    if "Da'if" in flags:
        return "Da'if" if len(flags) == 1 else "Unknown"
    if flags == {"Sahih"}:
        return "Sahih"
    if flags == {"Hasan"}:
        return "Hasan"
    if flags == {"Sahih", "Hasan"}:
        return "Hasan"
    return "Unknown"


def resolve_lk_source():
    env_path = os.environ.get("LK_HADITH_CORPUS_PATH")
    if env_path:
        source_path = Path(env_path).expanduser().resolve()
        if not source_path.is_dir():
            raise FileNotFoundError(f"LK_HADITH_CORPUS_PATH does not exist: {source_path}")
        return source_path

    if DEFAULT_LK_PATH.is_dir():
        return DEFAULT_LK_PATH

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not shutil.which("git"):
        raise RuntimeError(
            "git is required to clone LK-Hadith-Corpus. Install git or set LK_HADITH_CORPUS_PATH."
        )

    print(f"Cloning LK Hadith Corpus into {DEFAULT_LK_PATH}...")
    subprocess.run(["git", "clone", LK_REPO_URL, str(DEFAULT_LK_PATH)], check=True)
    return DEFAULT_LK_PATH


def get_source_commit(source_path):
    git_dir = source_path / ".git"
    if not git_dir.is_dir() or not shutil.which("git"):
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(source_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _read_csv(path):
    for encoding in ("utf-8-sig", "utf-8", "cp1256"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def _load_book(source_path, book_key):
    book_dir = source_path / book_key
    if not book_dir.is_dir():
        raise FileNotFoundError(f"Missing LK book directory: {book_dir}")

    csv_paths = sorted(book_dir.rglob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found under LK book directory: {book_dir}")

    frames = []
    for csv_path in csv_paths:
        frame = _read_csv(csv_path)
        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"{csv_path} is missing required LK columns: {sorted(missing)}")
        frame = frame.copy()
        frame["LK_Book"] = book_key
        frame["Source_File"] = str(csv_path.relative_to(source_path))
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def load_lk_dataframe(source_path):
    frames = [_load_book(source_path, book_key) for book_key in BOOK_ORDER]
    df = pd.concat(frames, ignore_index=True)
    if len(df) < 30000:
        raise RuntimeError(f"Loaded only {len(df)} LK rows; refusing to build a likely partial DB.")
    return df


def transform_lk_dataframe(df):
    output = pd.DataFrame()
    output["Book"] = df["LK_Book"].map(BOOK_NAME_MAP)
    output["LK_Book"] = df["LK_Book"]
    output["Source_File"] = df["Source_File"]

    output["Chapter_Number"] = df["Chapter_Number"]
    output["Chapter_Title_English"] = df["Chapter_English"].map(_clean_text)
    output["Chapter_Title_Arabic"] = df["Chapter_Arabic"].map(_clean_text)
    output["Chapter_English"] = output["Chapter_Title_English"]
    output["Chapter_Arabic"] = output["Chapter_Title_Arabic"]

    output["Section_Number"] = df["Section_Number"]
    output["Section_English"] = df["Section_English"].map(_clean_text)
    output["Section_Arabic"] = df["Section_Arabic"].map(_clean_text)
    output["Hadith_Number"] = df["Hadith_number"]

    output["English_Hadith"] = df["English_Hadith"].map(_clean_text)
    output["English_Text"] = output["English_Hadith"]
    output["English_Isnad"] = df["English_Isnad"].map(_clean_text)
    output["English_Matn"] = df["English_Matn"].map(_clean_text)
    output["English_Text_Source"] = output["English_Text"].map(_source_for)
    output["English_Isnad_Source"] = output["English_Isnad"].map(_source_for)
    output["English_Matn_Source"] = output["English_Matn"].map(_source_for)

    output["Arabic_Hadith"] = df["Arabic_Hadith"].map(_clean_text)
    output["Arabic_Text"] = output["Arabic_Hadith"]
    output["Arabic_Isnad"] = df["Arabic_Isnad"].map(_clean_text)
    output["Arabic_Matn"] = df["Arabic_Matn"].map(_clean_text)
    output["Arabic_Text_Source"] = output["Arabic_Text"].map(_source_for)
    output["Arabic_Isnad_Source"] = output["Arabic_Isnad"].map(_source_for)
    output["Arabic_Matn_Source"] = output["Arabic_Matn"].map(_source_for)
    output["Arabic_Comment"] = df["Arabic_Comment"].map(_clean_text) if "Arabic_Comment" in df else ""

    output["English_Grade"] = df["English_Grade"].map(_clean_text)
    output["Arabic_Grade"] = df["Arabic_Grade"].map(_clean_text)
    output["Grade"] = output["English_Grade"]
    output["Normalized_Grade"] = [
        normalize_grade(en_grade, ar_grade)
        for en_grade, ar_grade in zip(output["English_Grade"], output["Arabic_Grade"])
    ]

    reconstruction_summary = apply_deterministic_reconstruction(output)
    output["Has_English_Content"] = [
        int(any(_has_text(row[column]) for column in ["English_Text", "English_Isnad", "English_Matn"]))
        for _, row in output.iterrows()
    ]
    output["Has_Arabic_Content"] = [
        int(any(_has_text(row[column]) for column in ["Arabic_Text", "Arabic_Isnad", "Arabic_Matn"]))
        for _, row in output.iterrows()
    ]
    output["Has_English_Matn"] = output["English_Matn"].map(lambda value: int(_has_text(value)))
    output["Has_Arabic_Matn"] = output["Arabic_Matn"].map(lambda value: int(_has_text(value)))

    output.insert(0, "id_before_drop", range(1, len(output) + 1))
    output, dropped_rows = drop_rows_missing_bilingual_matn(output)
    output.insert(0, "id", range(1, len(output) + 1))

    for column in PREPROCESSING_COLUMNS:
        output[column] = ""

    output.attrs["reconstruction_summary"] = reconstruction_summary
    output.attrs["dropped_rows"] = dropped_rows
    return output


def apply_deterministic_reconstruction(df):
    summary = {
        "English_Text_reconstructed_from_isnad_matn": 0,
        "Arabic_Text_reconstructed_from_isnad_matn": 0,
        "English_Matn_reconstructed_from_full_minus_isnad": 0,
        "Arabic_Matn_reconstructed_from_full_minus_isnad": 0,
        "English_Isnad_reconstructed_from_full_minus_matn": 0,
        "Arabic_Isnad_reconstructed_from_full_minus_matn": 0,
    }

    for idx, row in df.iterrows():
        for language in ["English", "Arabic"]:
            text_col = f"{language}_Text"
            hadith_col = f"{language}_Hadith"
            isnad_col = f"{language}_Isnad"
            matn_col = f"{language}_Matn"
            text_source_col = f"{language}_Text_Source"
            isnad_source_col = f"{language}_Isnad_Source"
            matn_source_col = f"{language}_Matn_Source"

            text = df.at[idx, text_col]
            isnad = df.at[idx, isnad_col]
            matn = df.at[idx, matn_col]

            if not _has_text(text) and (_has_text(isnad) or _has_text(matn)):
                reconstructed = " ".join(part for part in [_clean_text(isnad), _clean_text(matn)] if part).strip()
                if reconstructed:
                    df.at[idx, text_col] = reconstructed
                    df.at[idx, hadith_col] = reconstructed
                    df.at[idx, text_source_col] = "reconstructed_from_isnad_matn"
                    summary[f"{language}_Text_reconstructed_from_isnad_matn"] += 1
                    text = reconstructed

            if not _has_text(matn) and _has_text(text) and _has_text(isnad):
                reconstructed = _remove_prefix(text, isnad)
                if reconstructed:
                    df.at[idx, matn_col] = reconstructed
                    df.at[idx, matn_source_col] = "reconstructed_from_full_minus_isnad"
                    summary[f"{language}_Matn_reconstructed_from_full_minus_isnad"] += 1
                    matn = reconstructed

            if not _has_text(isnad) and _has_text(text) and _has_text(matn):
                reconstructed = _remove_suffix(text, matn)
                if reconstructed:
                    df.at[idx, isnad_col] = reconstructed
                    df.at[idx, isnad_source_col] = "reconstructed_from_full_minus_matn"
                    summary[f"{language}_Isnad_reconstructed_from_full_minus_matn"] += 1

    return summary


def drop_rows_missing_bilingual_matn(df):
    drop_mask = ~(df["Has_English_Matn"].astype(bool) & df["Has_Arabic_Matn"].astype(bool))
    dropped = df.loc[drop_mask].copy()
    kept = df.loc[~drop_mask].copy()

    audit_rows = []
    for row in dropped.itertuples(index=False):
        audit_rows.append({
            "id_before_drop": getattr(row, "id_before_drop"),
            "LK_Book": getattr(row, "LK_Book"),
            "Book": getattr(row, "Book"),
            "Source_File": getattr(row, "Source_File"),
            "Chapter_Number": getattr(row, "Chapter_Number"),
            "Hadith_Number": getattr(row, "Hadith_Number"),
        })

    return kept.drop(columns=["id_before_drop"]), audit_rows


def create_database(df):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)
    try:
        df.to_sql("HADITHS", connection, if_exists="replace", index=False)
        connection.execute("CREATE UNIQUE INDEX idx_hadiths_id ON HADITHS(id)")
        connection.execute("CREATE INDEX idx_hadiths_book ON HADITHS(Book)")
        connection.execute("CREATE INDEX idx_hadiths_grade ON HADITHS(Normalized_Grade)")
        connection.commit()
    finally:
        connection.close()


def write_dropped_rows_audit(dropped_rows):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "reason": "missing_bilingual_matn_after_reconstruction",
        "count": len(dropped_rows),
        "rows": dropped_rows,
    }
    with open(DROPPED_ROWS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def run():
    source_path = resolve_lk_source()
    print(f"Using LK source: {source_path}")

    raw_df = load_lk_dataframe(source_path)
    db_df = transform_lk_dataframe(raw_df)
    write_dropped_rows_audit(db_df.attrs.get("dropped_rows", []))
    create_database(db_df)

    print(f"Created {DB_PATH} with {len(db_df)} hadiths")
    print("Reconstruction summary:")
    for key, count in db_df.attrs.get("reconstruction_summary", {}).items():
        print(f"  {key}: {count}")
    print(f"Dropped rows missing bilingual matn: {len(db_df.attrs.get('dropped_rows', []))}")
    print("Rows by book:")
    for book, count in db_df["Book"].value_counts().sort_index().items():
        print(f"  {book}: {count}")
    print("Normalized grade distribution:")
    for grade, count in db_df["Normalized_Grade"].value_counts(dropna=False).items():
        print(f"  {grade}: {count}")


if __name__ == "__main__":
    run()
