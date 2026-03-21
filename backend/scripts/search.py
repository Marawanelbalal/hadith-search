import pickle
import os
from scripts.preprocess import preprocess_arabic,preprocess_english
from nltk.stem import WordNetLemmatizer
import qalsadi.lemmatizer
import sqlite3
import pandas as pd
from math import log10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EN_II_DIR = os.path.join(BASE_DIR,"..","data","english_inverted_index.pkl")
AR_II_DIR = os.path.join(BASE_DIR,"..","data","arabic_inverted_index.pkl")
DOC_LEN_DIR = os.path.join(BASE_DIR,"..","data","document_lengths.pkl")

InvertedIndex = dict[str, list[tuple[int, int]]]

def load_english_inverted_index() -> InvertedIndex:
    with open(EN_II_DIR, 'rb') as file:
        english_inverted_index = pickle.load(file)
    return english_inverted_index

def load_arabic_inverted_index() -> InvertedIndex:
    with open(AR_II_DIR, 'rb') as file:
        arabic_inverted_index = pickle.load(file)
    return arabic_inverted_index    

def load_document_lengths() -> dict[int, tuple[int, int]]:
    with open(DOC_LEN_DIR, 'rb') as file:
        document_lengths = pickle.load(file)
    return document_lengths

def load_index_and_preprocess(query: str, language: str = "EN") -> tuple[InvertedIndex, str]:
    language = language.upper()
    if language == "EN":
        inverted_index = load_english_inverted_index()
        lemmatizer = WordNetLemmatizer()
    elif language == "AR":
        inverted_index = load_arabic_inverted_index()
        lemmatizer = qalsadi.lemmatizer.Lemmatizer()
    else:
        raise ValueError(f"Invalid language: {language}. Expected 'EN' or 'AR'")
    
    preprocessed_query = preprocess_arabic(query, lemmatizer) if language == "AR" else preprocess_english(query, lemmatizer)
    return inverted_index, preprocessed_query

def ranked_boolean_retrieval(query : str,language: str ="EN") -> dict[int,int]:
    inverted_index,query = load_index_and_preprocess(query,language)
    query_terms = query.split()
    valid_hadiths = {}
    for term in set(query_terms):
        if term not in inverted_index:
            continue
        term_postings = inverted_index[term]
        term_hadith_ids = [posting[0] for posting in term_postings]

        for hadith_id in term_hadith_ids:
            valid_hadiths[hadith_id] = valid_hadiths.get(hadith_id,0) + 1

    sorted_hadiths = dict(sorted(valid_hadiths.items(), key=lambda item: item[1], reverse=True))
    return sorted_hadiths


def tf_idf(query: str,language: str ="EN") -> dict[int,float]:
    inverted_index,query = load_index_and_preprocess(query,language)
    document_scores = {}
    term_query_frequency = {}
    document_lengths = load_document_lengths()
    query_terms = query.split()
    for term in query_terms:
        term_query_frequency[term] = term_query_frequency.get(term,0) + 1

    for term in term_query_frequency:
        if term not in inverted_index:
            continue
        postings = inverted_index[term]
        idf = log10(len(document_lengths) / len(postings))
        for posting in postings: #posting = (hadith_id,term_frequency)
            hadith_id = posting[0]
            normalized_tf = 1 + log10(posting[1])
            tf_idf_score = normalized_tf * idf
            final_score = term_query_frequency[term] * tf_idf_score
            document_scores[hadith_id] = document_scores.get(hadith_id, 0) + final_score
    sorted_hadiths = dict(sorted(document_scores.items(), key=lambda item: item[1], reverse=True))

    return sorted_hadiths


def bm25(query : str,language : str ="EN",k1 : float =1.2,b : float=0.75) -> dict[int,float]:
    language = language.upper()
    inverted_index,query = load_index_and_preprocess(query,language)
    document_scores = {}
    term_query_frequency = {}
    document_lengths = load_document_lengths()
    query_terms = query.split()

    for term in query_terms:
        term_query_frequency[term] = term_query_frequency.get(term,0) + 1

    for term in term_query_frequency:
        if term not in inverted_index:
            continue
        postings = inverted_index[term]
        df = len(postings)
        idf_component = log10((len(document_lengths) - df + 0.5) / (df + 0.5))
        for posting in postings: #posting = (hadith_id,term_frequency)
            hadith_id = posting[0]
            tf = posting[1]
            ld = document_lengths[hadith_id][0 if language == "AR" else 1] #length of document
            lavg = sum(document_lengths.keys()) / len(document_lengths) #average length of all docs
            tf_component = ((k1 + 1) * tf) / k1 * ((1-b) + b*(ld/lavg)) + tf
            bm25_score = tf_component * idf_component
            document_scores[hadith_id] = document_scores.get(hadith_id, 0) + bm25_score
    sorted_hadiths = dict(sorted(document_scores.items(), key=lambda item: item[1], reverse=True))

    return sorted_hadiths

def get_hadith(hadith_id: int) -> dict:
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths WHERE id = ?", connection, params=(hadith_id,))
    if df.empty:
        return {"error": "not found"}

    return df.iloc[0].to_dict()

def print_top_10_hadiths(hadith_dict : dict[int,float | int]) -> None:
    top_10 = sorted(hadith_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    for doc_id, score in top_10:
        hadith = get_hadith(doc_id)
        print(f"Score: {score}")
        print(f"English: {hadith['English_Text']}")
        print(f"Arabic: {hadith['Arabic_Text']}\n")

if __name__ == "__main__":
    query = input("Enter Query: ")
    language = input("Enter Language: ")
    boolean_hadiths = ranked_boolean_retrieval(query,language)
    tf_idf_hadiths = tf_idf(query,language)
    bm25_hadiths = bm25(query,language)
    print_top_10_hadiths(bm25_hadiths)