import os
import pandas as pd
import json
import sqlite3
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

#English Inverted Index first
connection = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT * FROM HADITHS", connection)

english_inverted_index = {}
arabic_inverted_index = {}

def create_posting_english(term,document):
    tokens = document['preprocessed_english'].split()
    return {"doc_id":document['id'],"tf":tokens.count(term)}

def create_posting_arabic(term,document):
    tokens = document['preprocessed_arabic'].split()
    return {"doc_id":document['id'],"tf":tokens.count(term)}
for _,row in df.iterrows():
    english_text = row["preprocessed_english"]
    arabic_text = row["preprocessed_arabic"]
    english_terms = set(english_text.split())
    arabic_terms = set(arabic_text.split())
    for term in english_terms:
        if term not in english_inverted_index:
            english_inverted_index[term] = {"doc_frequency": 1,"postings":[create_posting_english(term,row)]}
        else:
            english_inverted_index[term]["doc_frequency"] += 1
            english_inverted_index[term]["postings"].append(create_posting_english(term,row))

    for term in arabic_terms:
        if term not in arabic_inverted_index:
            arabic_inverted_index[term] = {"doc_frequency": 1,"postings":[create_posting_arabic(term,row)]}
        else:
            arabic_inverted_index[term]["doc_frequency"] += 1
            arabic_inverted_index[term]["postings"].append(create_posting_arabic(term,row))
    

for term in english_inverted_index:
    english_inverted_index[term]["postings"] = sorted(
        english_inverted_index[term]["postings"], 
        key=lambda x: x["doc_id"]
    )
for i, ((english_key, english_value), (arabic_key, arabic_value)) in enumerate(zip(english_inverted_index.items(), arabic_inverted_index.items())):
    if i == 20:
        break
    print(f"English Term ({english_key}): {english_value}\n")
    print(f"Arabic Term ({arabic_key}): {arabic_value}\n")

with open(os.path.join(DATA_DIR, "english_inverted_index.pkl"), "wb") as f:
    pickle.dump(english_inverted_index, f)
with open(os.path.join(DATA_DIR, "arabic_inverted_index.pkl"), "wb") as f:
    pickle.dump(arabic_inverted_index, f)
