import os
import json
import pandas as pd
import sqlite3

SCRIPTS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(SCRIPTS_DIR, '..', 'data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'evaluation_corpus')
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")
os.makedirs(OUTPUT_DIR, exist_ok=True)
from scripts.search import (
        tf_idf,
        bm25,
        bm25_with_expansion,
        bm25_tfidf_hybrid,
        hybrid_with_expansion,
        rrf_fusion, cosine_similarity_search,get_hadith
    )

from scripts.loading import (
    get_english_inverted_index,
    get_arabic_inverted_index,
    get_document_lengths,
    get_english_embeddings,
    get_arabic_embeddings,
    get_hadith_ids,
    get_model
)
en_index = get_english_inverted_index()
ar_index = get_arabic_inverted_index()
doc_lengths = get_document_lengths()
en_embeddings = get_english_embeddings()
ar_embeddings = get_arabic_embeddings()
hadith_ids = get_hadith_ids()
model = get_model()

print("Loading Database into memory...")
conn = sqlite3.connect(DB_PATH)
hadiths_df = pd.read_sql("SELECT id, English_Text, Arabic_Text FROM hadiths", conn).set_index("id")
conn.close()
# Pool all systems per query (full 34k, no restriction)

def pool_query(query: str, language: str) -> set[int]:
    index = en_index if language == "EN" else ar_index
    embeddings = en_embeddings if language == "EN" else ar_embeddings
    model = model
    text_col = "English_Text" if language == "EN" else "Arabic_Text"
    pool = set()

    #TF-IDF
    tf_idf_scores = tf_idf(query, language, index, doc_lengths)
    tf_idf_candidates = list(tf_idf_scores.keys())
    pool.update(tf_idf_candidates[:100])

    # BM25
    bm25_scores = bm25(query, language, index, doc_lengths)
    bm25_candidates = list(bm25_scores.keys())
    pool.update(bm25_candidates[:100])

    # BM25 + Rocchio
    rocchio_scores = bm25_with_expansion(query, language, index, doc_lengths,get_hadith)
    pool.update(list(rocchio_scores.keys())[:100])

    # BM25 + TF-IDF
    bm25_tfidf_scores = bm25_tfidf_hybrid(query, language, index, doc_lengths)
    pool.update(list(bm25_tfidf_scores.keys())[:100])

    # BM25 + TF-IDF + Rocchio
    bm25_tfidf_rocchio_scores = hybrid_with_expansion(query, language, index, doc_lengths,get_hadith)
    pool.update(list(bm25_tfidf_rocchio_scores.keys())[:100])

    # Semantic (independent full corpus search)
    query_emb = model.encode([query])[0]
    semantic_scores = cosine_similarity_search(query_emb, embeddings, hadith_ids, top_k=100)
    pool.update(list(semantic_scores.keys())[:100])

    # BM25 + RRF
    bm25_ranked = {hid: rank + 1 for rank, hid in enumerate(bm25_candidates[:100])}
    semantic_ranked = {hid: rank + 1 for rank, hid in enumerate(list(semantic_scores.keys())[:100])}
    rrf_scores = rrf_fusion([bm25_ranked, semantic_ranked])
    pool.update(list(rrf_scores.keys())[:100])

    return pool


def build_evaluation_corpus(qrels: dict) -> pd.DataFrame:
    rows = []
    seen = {}  # (hadith_id, query_id) -> row index, to handle duplicates

    for qid, data in qrels.items():
        query = data["query"]
        language = qid[:2]
        already_judged = set(int(k) for k in data["grades"].keys())

        print(f"Pooling {qid}...")
        pool = pool_query(query, language)
        new_candidates = pool - already_judged

        print(f"  {len(pool)} pooled | {len(already_judged)} already judged | {len(new_candidates)} new")

        for hid in new_candidates:
            if hid not in hadiths_df.index:
                continue
            key = (hid, qid)
            if key in seen:
                continue  # exact duplicate, skip
            seen[key] = True

            row = hadiths_df.loc[hid]
            rows.append({
                "hadith_id": hid,
                "query_id": qid,
                "query": query,
                "arabic_text": row.get("Arabic_Text", ""),
                "english_text": row.get("English_Text", "")
            })

    df = pd.DataFrame(rows, columns=["hadith_id", "query_id", "query", "arabic_text", "english_text"])
    df = df.sort_values(["query_id", "hadith_id"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "qrels.json"), encoding="utf-8") as f:
        qrels = json.load(f)

    df = build_evaluation_corpus(qrels)

    print(f"\nSplitting and refining {len(df)} rows...")
    
    unique_qids = df['query_id'].unique()
    
    for qid in unique_qids:
        #Filter for the specific query ID
        subset = df[df['query_id'] == qid].copy()

        refined_subset = subset.drop(columns=['query', 'query_id'])
        query_output_path = os.path.join(OUTPUT_DIR, f"{qid}.csv")
        refined_subset.to_csv(query_output_path, index=False, encoding="utf-8-sig")
        
        print(f" - Generated {qid}.csv (Size reduced: {len(refined_subset)} rows)")

    print(f"\nRefinement complete. Files saved to: {OUTPUT_DIR}")