import os
import pandas as pd
import sqlite3
import pickle



english_inverted_index = {}
arabic_inverted_index = {}
document_lengths = {} # store document lengths for each document as a tuple: {doc_id:(arabic_length,english_length)}
def create_term_frequency_dict(text):
    terms = text.split()
    term_frequency_dict = {}
    for term in terms:
        if term in term_frequency_dict:
            term_frequency_dict[term] += 1
        else:
            term_frequency_dict[term] = 1
    return term_frequency_dict


def build_inverted_index():
    global english_inverted_index, arabic_inverted_index, document_lengths
    import sqlite3, pandas as pd, os
    conn = sqlite3.connect(DB_PATH)
    sample = pd.read_sql("SELECT Arabic_Text, Preprocessed_Arabic FROM hadiths LIMIT 5", conn)
    conn.close()

    for _, row in sample.iterrows():
        original_len = len(row["Arabic_Text"].split())
        preprocessed_len = len(row["Preprocessed_Arabic"].split())
        print(f"Original:     {original_len} tokens | {row['Arabic_Text'][:80]}")
        print(f"Preprocessed: {preprocessed_len} tokens | {row['Preprocessed_Arabic'][:80]}")
        print(f"Reduction:    {round((1 - preprocessed_len/original_len)*100)}%\n")
    
    for _,row in df.iterrows():
        english_text = row["Preprocessed_English"]
        arabic_text = row["Preprocessed_Arabic"]
        english_terms = english_text.split()
        arabic_terms = arabic_text.split()

        document_lengths[row['id']] = (len(arabic_terms),len(english_terms)) #for and bm25
        arabic_term_frequency_dict = create_term_frequency_dict(arabic_text)
        english_term_frequency_dict = create_term_frequency_dict(english_text)
        for term in english_term_frequency_dict.keys():
            if term not in english_inverted_index:
                english_inverted_index[term] = [(row['id'],english_term_frequency_dict[term])]
            else:
                english_inverted_index[term].append((row['id'],english_term_frequency_dict[term]))

        for term in arabic_term_frequency_dict.keys():
            if term not in arabic_inverted_index:
                arabic_inverted_index[term] = [(row['id'],arabic_term_frequency_dict[term])]
            else:
                arabic_inverted_index[term].append((row['id'],arabic_term_frequency_dict[term]))

    for term in english_inverted_index.keys():
        english_inverted_index[term] = sorted(english_inverted_index[term], key=lambda x: x[0])

    for term in arabic_inverted_index.keys():
        arabic_inverted_index[term] = sorted(arabic_inverted_index[term], key=lambda x: x[0])

    with open(os.path.join(DATA_DIR, "english_inverted_index.pkl"), "wb") as f:
        pickle.dump(english_inverted_index, f)

    with open(os.path.join(DATA_DIR, "arabic_inverted_index.pkl"), "wb") as f:
        pickle.dump(arabic_inverted_index, f)

    with open(os.path.join(DATA_DIR, "document_lengths.pkl"), "wb") as f:
        pickle.dump(document_lengths,f)


def run():
    global english_inverted_index, arabic_inverted_index, document_lengths
    english_inverted_index = {}
    arabic_inverted_index = {}
    document_lengths = {}

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM HADITHS", connection)
    import time
    start = time.perf_counter()
    build_inverted_index()
    end = time.perf_counter()
    print(f"Inverted Index building took {round(end-start,3)}s")

if __name__ == "__main__":
    run()