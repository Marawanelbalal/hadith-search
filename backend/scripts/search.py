import pickle
import os
from scripts.preprocess import preprocess_arabic,preprocess_english,remove_stopwords_english
import sqlite3
import pandas as pd
from math import log10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EN_II_DIR = os.path.join(BASE_DIR,"..","data","english_inverted_index.pkl")
AR_II_DIR = os.path.join(BASE_DIR,"..","data","arabic_inverted_index.pkl")
DOC_LEN_DIR = os.path.join(BASE_DIR,"..","data","document_lengths.pkl")

InvertedIndex = dict[str, list[tuple[int, int]]]

_arabic_inverted_index = None
_english_inverted_index = None
_document_lengths = None

def get_arabic_inverted_index():
    global _arabic_inverted_index
    if _arabic_inverted_index is None:
        _arabic_inverted_index = load_arabic_inverted_index()
    return _arabic_inverted_index

def get_english_inverted_index():
    global _english_inverted_index
    if _english_inverted_index is None:
        _english_inverted_index = load_english_inverted_index()
    return _english_inverted_index

def get_document_lengths():
    global _document_lengths
    if _document_lengths is None:
        _document_lengths = load_document_lengths()
    return _document_lengths

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
        inverted_index = get_english_inverted_index()
    elif language == "AR":
        inverted_index = get_arabic_inverted_index()
    else:
        raise ValueError(f"Invalid language: {language}. Expected 'EN' or 'AR'")
    
    preprocessed_query = preprocess_arabic(query) if language == "AR" else preprocess_english(query)
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

    sorted_hadiths = dict(sorted(
        valid_hadiths.items(),
        key=lambda item: (-item[1], item[0])  # count desc, doc_id asc
    ))    
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

from collections import Counter

def query_expansion(query: str, top_hadiths: list[str], language: str = "EN", top_n: int = 3, alpha: float = 1.0, beta: float = 0.5) -> dict[str, float]:
    inverted_index, preprocessed_query = load_index_and_preprocess(query, language)
    document_lengths = load_document_lengths()
    total_docs = len(document_lengths)
    
    original_terms = preprocessed_query.split()
    query_vector = {term: alpha for term in original_terms}
    
    hadiths_string = " ".join(top_hadiths)
    local_tf = Counter(hadiths_string.split())
    
    pool_scores = {}
    for term, tf in local_tf.items():
        if term not in inverted_index or term in query_vector:
            continue
            
        df = len(inverted_index[term])
        idf = log10((total_docs - df + 0.5) / (df + 0.5))
        
        pool_scores[term] = (tf / len(top_hadiths)) * idf 
        
    sorted_expansion = sorted(pool_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    max_pool_score = max(pool_scores.values()) if pool_scores else 1
    for term, score in sorted_expansion:
        normalized_score = score / max_pool_score  # now in [0,1]
        query_vector[term] = normalized_score * beta  # beta=0.5 → max 0.5, always below alpha=1.0
    print(f"\n\n Custom Weights (New Query): \n {query_vector} \n\n")

    return query_vector

def bm25(query: str, language: str = "EN", k1: float = 1.2, b: float = 0.75, custom_weights: dict = None) -> dict[int, float]:
    language = language.upper()
    inverted_index, preprocessed_query = load_index_and_preprocess(query, language)
    document_lengths = load_document_lengths()
    
    lang_idx = 0 if language == "AR" else 1
    lavg = sum(v[lang_idx] for v in document_lengths.values()) / len(document_lengths)
    
    if custom_weights: #If we choose to do relevance feedback, pass it to the function and use it
        term_query_frequency = custom_weights
    else:
        query_terms = preprocessed_query.split()
        term_query_frequency = {}
        for term in query_terms:
            term_query_frequency[term] = term_query_frequency.get(term, 0) + 1
            
    document_scores = {}
    for term, qtf in term_query_frequency.items():
        if term not in inverted_index:
            continue
        postings = inverted_index[term]
        df = len(postings)
        idf = log10((len(document_lengths) - df + 0.5) / (df + 0.5))
        
        for hadith_id, tf in postings:
            ld = document_lengths[hadith_id][lang_idx]
            tf_component = ((k1 + 1) * tf) / (k1 * ((1 - b) + b * (ld / lavg)) + tf)
            
            document_scores[hadith_id] = document_scores.get(hadith_id, 0) + (tf_component * idf * qtf)

    return dict(sorted(document_scores.items(), key=lambda x: x[1], reverse=True))

def get_ranked_ids(results: dict[int, float]) -> list[int]:
    return [docid for docid, _ in sorted(results.items(), key=lambda x: x[1], reverse=True)]

def bm25_with_expansion(
    query: str,
    language: str = "EN",
    k: int = 5,
    top_n: int = 3
) -> dict[int, float]:
    initial_results = bm25(query, language)
    top_ids = get_ranked_ids(initial_results)[:k]
    
    col = "Preprocessed_English" if language == "EN" else "Preprocessed_Arabic"
    top_hadiths = [
        get_hadith(hadith_id)[col]
        for hadith_id in top_ids
    ]
    
    # Rocchio
    custom_weights = query_expansion(
        query=query,
        top_hadiths=top_hadiths,
        language=language,
        top_n=top_n
    )
    
    return bm25(query=query, language=language, custom_weights=custom_weights)
def bm25_tfidf_hybrid(query: str, language: str = "EN", alpha: float = 0.8) -> dict[int, float]:
    bm25_scores = bm25(query, language)
    tfidf_scores = tf_idf(query, language)
    
    bm25_max = max(bm25_scores.values(), default=1)
    tfidf_max = max(tfidf_scores.values(), default=1)
    
    all_ids = set(bm25_scores) | set(tfidf_scores)
    return {
        doc_id: alpha * (bm25_scores.get(doc_id, 0) / bm25_max) +
                (1 - alpha) * (tfidf_scores.get(doc_id, 0) / tfidf_max)
        for doc_id in all_ids
    }

def hybrid_with_expansion(query: str, language: str = "EN", k: int = 5, top_n: int = 3) -> dict[int, float]:
    initial_results = bm25_tfidf_hybrid(query, language)
    top_ids = get_ranked_ids(initial_results)[:k]
    
    col = "Preprocessed_English" if language == "EN" else "Preprocessed_Arabic"
    top_hadiths = [get_hadith(hadith_id)[col] for hadith_id in top_ids]
    
    custom_weights = query_expansion(
        query=query,
        top_hadiths=top_hadiths,
        language=language,
        top_n=top_n
    )
    return bm25(query=query, language=language, custom_weights=custom_weights)
def get_hadith(hadith_id: int) -> dict:
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths WHERE id = ?", connection, params=(hadith_id,))
    if df.empty:
        return {"error": "not found"}

    return df.iloc[0].to_dict()

def print_top_10_hadiths(hadith_dict : dict[int, float | int]) -> None:
    top_10 = sorted(hadith_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    for doc_id, score in top_10:
        hadith = get_hadith(doc_id)
        print(f"Score: {score}")
        print(f"English: {hadith['English_Text']}")
        print(f"Arabic: {hadith['Arabic_Text']}\n")

# def query_expansion(query:str,top_hadiths:list[str],language="EN"): #top hadiths come in preprocessed
#     original_terms = query.split()
#     query_vector = {original_term:1 for original_term in original_terms}
#     hadiths_string = " ".join(top_hadiths)        

if __name__ == "__main__":
    query = input("Enter Query: ")
    language = input("Enter Language: ").upper()
    bm25_hadiths = bm25(query,language)
    print("Before Query Expansion:\n")
    print_top_10_hadiths(bm25_hadiths)
    k = 5
    top_hadiths = []
    i = 0
    
    for hadith_id in bm25_hadiths.keys():
        while i < k:
            top_hadiths.append(get_hadith(hadith_id)["Preprocessed_English" if language == "EN" else "Preprocessed_Arabic"])
            i += 1
    custom_weights = query_expansion(query=query,top_hadiths=top_hadiths,language=language,top_n=k)
    expanded_bm25 = bm25(query=query,language=language,custom_weights=custom_weights)
    print("\n\nAfter Query Expansion:\n")
    print_top_10_hadiths(expanded_bm25)
