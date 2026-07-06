import os
import pandas as pd
import sqlite3
import pickle
import time


def has_text(value):
    if pd.isna(value):
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"nan", "none", "null"}


def create_term_frequency_dict(text):
    terms = text.split()
    term_frequency_dict = {}
    for term in terms:
        if term in term_frequency_dict:
            term_frequency_dict[term] += 1
        else:
            term_frequency_dict[term] = 1
    return term_frequency_dict


def build_inverted_index(df, data_dir):
    english_inverted_index = {}
    arabic_inverted_index = {}
    document_lengths = {}

    for _, row in df.iterrows():
        matn_en = row.get("Preprocessed_English_Matn")
        if not has_text(matn_en):
            raise ValueError(f"Hadith id {row['id']} has empty Preprocessed_English_Matn; refusing to build matn-only index")
        english_text = str(matn_en).strip()

        matn_ar = row.get("Preprocessed_Arabic_Matn")
        if not has_text(matn_ar):
            raise ValueError(f"Hadith id {row['id']} has empty Preprocessed_Arabic_Matn; refusing to build matn-only index")
        arabic_text = str(matn_ar).strip()

        english_terms = english_text.split()
        arabic_terms = arabic_text.split()

        document_lengths[row['id']] = (len(arabic_terms), len(english_terms))

        arabic_term_freq = create_term_frequency_dict(arabic_text)
        english_term_freq = create_term_frequency_dict(english_text)

        for term in english_term_freq:
            if term not in english_inverted_index:
                english_inverted_index[term] = [(row['id'], english_term_freq[term])]
            else:
                english_inverted_index[term].append((row['id'], english_term_freq[term]))

        for term in arabic_term_freq:
            if term not in arabic_inverted_index:
                arabic_inverted_index[term] = [(row['id'], arabic_term_freq[term])]
            else:
                arabic_inverted_index[term].append((row['id'], arabic_term_freq[term]))

    for term in english_inverted_index:
        english_inverted_index[term] = sorted(english_inverted_index[term], key=lambda x: x[0])

    for term in arabic_inverted_index:
        arabic_inverted_index[term] = sorted(arabic_inverted_index[term], key=lambda x: x[0])

    with open(os.path.join(data_dir, "english_inverted_index.pkl"), "wb") as f:
        pickle.dump(english_inverted_index, f)

    with open(os.path.join(data_dir, "arabic_inverted_index.pkl"), "wb") as f:
        pickle.dump(arabic_inverted_index, f)

    with open(os.path.join(data_dir, "document_lengths.pkl"), "wb") as f:
        pickle.dump(document_lengths, f)

    return len(english_inverted_index), len(arabic_inverted_index)


def run():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM HADITHS", connection)
    connection.close()

    print(f"Loaded {len(df)} hadiths")
    print("Indexing Preprocessed_English_Matn / Preprocessed_Arabic_Matn only...")

    start = time.perf_counter()
    en_terms, ar_terms = build_inverted_index(df, DATA_DIR)
    elapsed = time.perf_counter() - start

    print(f"English inverted index: {en_terms} unique terms")
    print(f"Arabic inverted index: {ar_terms} unique terms")
    print(f"Inverted index building took {elapsed:.3f}s")


if __name__ == "__main__":
    run()
