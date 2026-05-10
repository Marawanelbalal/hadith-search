from dotenv import load_dotenv
import os
from scripts.preprocess import preprocess_arabic,preprocess_english
import sqlite3
import numpy as np
import pandas as pd
from math import log10
from scripts.loading import get_english_inverted_index, get_arabic_inverted_index, get_document_lengths, get_hadith_ids, get_hadiths_df
import requests
from collections import Counter

InvertedIndex = dict[str, list[tuple[int, int]]]

load_dotenv()
JINA_API_KEY = os.getenv("JINA_API_KEY")

def ranked_boolean_retrieval(query: str, language: str, inverted_index) -> dict[int, int]:
    query = preprocess_arabic(query) if language == "AR" else preprocess_english(query)
    query_terms = query.split()
    valid_hadiths = {}
    for term in set(query_terms):
        if term not in inverted_index:
            continue
        term_postings = inverted_index[term]
        term_hadith_ids = [posting[0] for posting in term_postings]
        for hadith_id in term_hadith_ids:
            valid_hadiths[hadith_id] = valid_hadiths.get(hadith_id, 0) + 1
    sorted_hadiths = dict(sorted(
        valid_hadiths.items(),
        key=lambda item: (-item[1], item[0])
    ))
    return sorted_hadiths


def tf_idf(query: str, language: str, inverted_index, document_lengths) -> dict[int, float]:
    query = preprocess_arabic(query) if language == "AR" else preprocess_english(query)
    document_scores = {}
    term_query_frequency = {}
    query_terms = query.split()
    for term in query_terms:
        term_query_frequency[term] = term_query_frequency.get(term, 0) + 1
    for term in term_query_frequency:
        if term not in inverted_index:
            continue
        postings = inverted_index[term]
        idf = log10(len(document_lengths) / len(postings))
        for posting in postings:
            hadith_id = posting[0]
            normalized_tf = 1 + log10(posting[1])
            tf_idf_score = normalized_tf * idf
            final_score = term_query_frequency[term] * tf_idf_score
            document_scores[hadith_id] = document_scores.get(hadith_id, 0) + final_score
    sorted_hadiths = dict(sorted(document_scores.items(), key=lambda item: item[1], reverse=True))
    return sorted_hadiths


def query_expansion(query: str, top_hadiths: list[str], language: str, inverted_index, document_lengths, top_n: int = 3, alpha: float = 1.0, beta: float = 0.5) -> dict[str, float]:
    preprocessed_query = preprocess_arabic(query) if language == "AR" else preprocess_english(query)
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
        normalized_score = score / max_pool_score
        query_vector[term] = normalized_score * beta
    return query_vector

def bm25(query: str, language: str, inverted_index, document_lengths, k1: float = 1.2, b: float = 0.75, custom_weights: dict = None) -> dict[int, float]:
    preprocessed_query = preprocess_arabic(query) if language == "AR" else preprocess_english(query)
    lang_idx = 0 if language == "AR" else 1
    lavg = sum(v[lang_idx] for v in document_lengths.values()) / len(document_lengths)
    if custom_weights:
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
    language: str,
    inverted_index,
    document_lengths,
    get_hadith_fn,
    k: int = 5,
    top_n: int = 3
) -> dict[int, float]:
    initial_results = bm25(query, language, inverted_index, document_lengths)
    top_ids = get_ranked_ids(initial_results)[:k]
    col = "Preprocessed_English" if language == "EN" else "Preprocessed_Arabic"
    top_hadiths = [get_hadith_fn(hadith_id)[col] for hadith_id in top_ids]
    custom_weights = query_expansion(
        query=query,
        top_hadiths=top_hadiths,
        language=language,
        inverted_index=inverted_index,
        document_lengths=document_lengths,
        top_n=top_n
    )
    return bm25(query=query, language=language, inverted_index=inverted_index, document_lengths=document_lengths, custom_weights=custom_weights)

def bm25_tfidf_hybrid(query: str, language: str, inverted_index, document_lengths, alpha: float = 0.8) -> dict[int, float]:
    bm25_scores = bm25(query, language, inverted_index, document_lengths)
    tfidf_scores = tf_idf(query, language, inverted_index, document_lengths)
    bm25_max = max(bm25_scores.values(), default=1)
    tfidf_max = max(tfidf_scores.values(), default=1)
    all_ids = set(bm25_scores) | set(tfidf_scores)
    return {
        doc_id: alpha * (bm25_scores.get(doc_id, 0) / bm25_max) +
                (1 - alpha) * (tfidf_scores.get(doc_id, 0) / tfidf_max)
        for doc_id in all_ids
    }

def hybrid_with_expansion(query: str, language: str, inverted_index, document_lengths, get_hadith_fn, k: int = 5, top_n: int = 3) -> dict[int, float]:
    initial_results = bm25_tfidf_hybrid(query, language, inverted_index, document_lengths)
    top_ids = get_ranked_ids(initial_results)[:k]
    col = "Preprocessed_English" if language == "EN" else "Preprocessed_Arabic"
    top_hadiths = [get_hadith_fn(hadith_id)[col] for hadith_id in top_ids]
    custom_weights = query_expansion(
        query=query,
        top_hadiths=top_hadiths,
        language=language,
        inverted_index=inverted_index,
        document_lengths=document_lengths,
        top_n=top_n
    )
    return bm25(query=query, language=language, inverted_index=inverted_index, document_lengths=document_lengths, custom_weights=custom_weights)

EPS = 1e-12

def normalize_embeddings(embeddings: np.ndarray, eps: float = EPS) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / (norms + eps)

def build_id2idx(hadith_ids: np.ndarray) -> dict[int, int]:
    return {int(hid): i for i, hid in enumerate(hadith_ids)}

def cosine_similarity_search(
    query_embedding: np.ndarray,
    corpus_embeddings_normed: np.ndarray,
    hadith_ids: np.ndarray,
    top_k: int = 50,
) -> dict[int, float]:
    """
    corpus_embeddings_normed must already be L2-normalized row-wise.
    query_embedding should be normalized inside this function.
    """
    q_norm = np.linalg.norm(query_embedding)
    query_norm = query_embedding / (q_norm + EPS)

    scores = corpus_embeddings_normed @ query_norm

    top_k = min(top_k, len(scores))
    top_k_indices = np.argpartition(-scores, top_k - 1)[:top_k]
    top_k_indices = top_k_indices[np.argsort(-scores[top_k_indices])]

    return {
        int(hadith_ids[idx]): float(scores[idx])
        for idx in top_k_indices
    }
def semantic_search_e5(
    query: str,
    model,
    corpus_embeddings_normed: np.ndarray,
    hadith_ids: np.ndarray,
    top_k: int = 50,
) -> dict[int, float]:
    """
    Dense semantic retrieval using E5-style query formatting.
    """
    query_text = f"query: {query}"
    query_embedding = model.encode([query_text])[0]

    return cosine_similarity_search(
        query_embedding=query_embedding,
        corpus_embeddings_normed=corpus_embeddings_normed,
        hadith_ids=hadith_ids,
        top_k=top_k,
    )

def semantic_reranker(query: str, candidate_ids: list[int], model, embeddings: np.ndarray, hadith_ids: np.ndarray, top_k: int = 50) -> dict[int, float]:
    e5_query = f"query: {query}" if query.startswith("AR") else query
    query_embedding = model.encode([e5_query])[0]
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
    scores = {}
    for hadith_id in candidate_ids:
        idx = np.where(hadith_ids == hadith_id)[0][0]
        doc_embedding = embeddings[idx]
        doc_embedding = doc_embedding / np.linalg.norm(doc_embedding)
        scores[hadith_id] = float(np.dot(query_embedding, doc_embedding))
    
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k])

def rrf_fusion(
    ranked_lists: list[dict[int, int]],
    k: int = 60
) -> dict[int, float]:
    """
    Each input dict is {hadith_id: rank}, where rank is 1-indexed.
    """
    scores: dict[int, float] = {}

    for ranked_list in ranked_lists:
        for hadith_id, rank in ranked_list.items():
            scores[hadith_id] = scores.get(hadith_id, 0.0) + 1.0 / (k + rank)

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def bm25_semantic_rrf(
    query: str,
    language: str,
    index,
    doc_lengths,
    corpus_embeddings_normed: np.ndarray,
    hadith_ids: np.ndarray,
    model,
    candidate_k: int = 500,
    top_k: int = 50,
    rrf_k: int = 60,
    judged_ids: set[int] | None = None,
) -> dict[int, float]:
    """
    Returns fused RRF scores over BM25 and dense semantic search.
    """

    # BM25 full ranked list
    bm25_scores = bm25(query, language, index, doc_lengths)
    bm25_ranked_ids = list(bm25_scores.keys())

    if judged_ids is not None:
        bm25_ranked_ids = [hid for hid in bm25_ranked_ids if int(hid) in judged_ids]

    bm25_ranked = {
        int(hid): rank + 1
        for rank, hid in enumerate(bm25_ranked_ids[:candidate_k])
    }

    # Dense ranked list
    semantic_scores = semantic_search_e5(
        query=query,
        model=model,
        corpus_embeddings_normed=corpus_embeddings_normed,
        hadith_ids=hadith_ids,
        top_k=candidate_k,
    )

    semantic_ranked_ids = list(semantic_scores.keys())
    if judged_ids is not None:
        semantic_ranked_ids = [hid for hid in semantic_ranked_ids if int(hid) in judged_ids]

    semantic_ranked = {
        int(hid): rank + 1
        for rank, hid in enumerate(semantic_ranked_ids[:candidate_k])
    }

    # Fuse
    fused = rrf_fusion([bm25_ranked, semantic_ranked], k=rrf_k)

    return dict(list(fused.items())[:top_k])
import time
def cross_encoder_rerank(
    query: str,
    candidate_ids: list[int],
    hadith_texts: dict[int, str],
    top_k: int = 50
) -> dict[int, float]:

    valid_ids = [hid for hid in candidate_ids if hid in hadith_texts]

    if not valid_ids:
        return {}

    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": [hadith_texts[hid] for hid in valid_ids],
            "top_n": top_k
        }
    )
    time.sleep(20) #avoid hitting Jina API rate limits during testing
    results = response.json()["results"]
    return {
        valid_ids[r["index"]]: float(r["relevance_score"])
        for r in results
    }


def bm25_cross_encoder_rerank(
    query: str,
    language: str,
    index,
    doc_lengths,
    hadiths_df,
    candidate_k: int = 50,
    top_k: int = 10
) -> dict[int, float]:

    bm25_scores = bm25(query, language, index, doc_lengths)
    candidate_ids = list(bm25_scores.keys())[:candidate_k]

    text_col = "English_Text" if language.upper() == "EN" else "Arabic_Text"
    hadith_texts = {
        hid: hadiths_df.loc[hid][text_col]
        for hid in candidate_ids
        if hid in hadiths_df.index
    }

    return cross_encoder_rerank(query, candidate_ids, hadith_texts, top_k)
def final_search_pipeline(
    query: str,
    language: str,
    index,
    doc_lengths,
    embeddings: np.ndarray,
    hadith_ids: np.ndarray,
    model,
    eval_ids: set[int],
    texts_dict: dict[int, str],
    candidate_k: int = 500,
    rerank_k: int = 30,
    final_k: int = 30,
) -> dict[int, float]:

    bm25_scores = bm25(query, language, index, doc_lengths)

    candidates = [
        hid for hid in sorted(bm25_scores, key=bm25_scores.get, reverse=True)
        if hid in eval_ids
    ][:candidate_k]

    query_emb = model.encode([query if language == "EN" else f"query: {query}"])[0]
    query_emb = query_emb / np.linalg.norm(query_emb)

    scores = embeddings @ query_emb

    top_dense_idx = np.argsort(-scores)[:candidate_k]
    dense_candidates = hadith_ids[top_dense_idx].tolist()

    dense_candidates = [hid for hid in dense_candidates if hid in eval_ids]

    bm25_ranked = {hid: i + 1 for i, hid in enumerate(candidates)}
    dense_ranked = {hid: i + 1 for i, hid in enumerate(dense_candidates)}

    fused = rrf_fusion([bm25_ranked, dense_ranked], k=60)

    top_candidates = list(fused.keys())[:rerank_k]
    hadith_texts = {
        hid: texts_dict[hid]
        for hid in top_candidates
        if hid in texts_dict
    }

    return cross_encoder_rerank(
        query=query,
        candidate_ids=top_candidates,
        hadith_texts=hadith_texts,
        top_k=final_k
    )
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

if __name__ == "__main__":
    from scripts.loading import get_english_inverted_index, get_arabic_inverted_index, get_document_lengths
    query = input("Enter Query: ")
    language = input("Enter Language: ").upper()
    if language == "EN":
        inverted_index = get_english_inverted_index()
    elif language == "AR":
        inverted_index = get_arabic_inverted_index()
    else:
        raise ValueError("Invalid language. Use 'EN' or 'AR'.")
    document_lengths = get_document_lengths()
    bm25_hadiths = bm25(query, language, inverted_index, document_lengths)
    print("Before Query Expansion:\n")
    print_top_10_hadiths(bm25_hadiths)
    k = 5
    top_hadiths = []
    
    for hadith_id in list(bm25_hadiths.keys())[:k]:
        hadith_data = get_hadith(hadith_id)
        col = "Preprocessed_English" if language == "EN" else "Preprocessed_Arabic"
        top_hadiths.append(hadith_data[col])
    custom_weights = query_expansion(query=query, top_hadiths=top_hadiths, language=language, inverted_index=inverted_index, document_lengths=document_lengths, top_n=k)
    expanded_bm25 = bm25(query=query, language=language, inverted_index=inverted_index, document_lengths=document_lengths, custom_weights=custom_weights)
    print("\n\nAfter Query Expansion:\n")
    print_top_10_hadiths(expanded_bm25)
