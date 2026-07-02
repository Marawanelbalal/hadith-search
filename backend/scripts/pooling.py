import os
import json
import sqlite3
import numpy as np

SCRIPTS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(SCRIPTS_DIR, '..', 'data')
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

from scripts.search import (
    bm25_with_expansion,
    cosine_similarity_search,
    final_search_pipeline,
    get_hadith
)
from scripts.preprocess import normalize_arabic_text
from camel_tools.utils.dediac import dediac_ar

from scripts.loading import (
    get_english_inverted_index,
    get_arabic_inverted_index,
    get_document_lengths,
    get_english_embeddings,
    get_arabic_embeddings,
    get_hadith_ids,
    get_model
)

print("Loading indices and embeddings...")
en_index = get_english_inverted_index()
ar_index = get_arabic_inverted_index()
doc_lengths = get_document_lengths()
en_embeddings = get_english_embeddings()
ar_embeddings = get_arabic_embeddings()
hadith_ids = get_hadith_ids()
model = get_model()

print("Loading hadiths into memory...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT id, English_Text, Arabic_Text FROM hadiths")
hadith_rows = cursor.fetchall()
conn.close()

hadith_texts_en = {row[0]: row[1] for row in hadith_rows if row[1]}
hadith_texts_ar = {row[0]: row[2] for row in hadith_rows if row[2]}
all_hadith_ids = set(hadith_ids)

def pool_query(query: str, language: str, per_algo_size : int = 100) -> list[int]:
    index = en_index if language == "EN" else ar_index
    embeddings = en_embeddings if language == "EN" else ar_embeddings
    texts_dict = hadith_texts_en if language == "EN" else hadith_texts_ar

    bm25_scores = bm25_with_expansion(query, language, index, doc_lengths, get_hadith)
    bm25_top = list(bm25_scores.keys())[:per_algo_size]

    if language == "AR":
        e5_query = f"query: {normalize_arabic_text(dediac_ar(query))}"
    else:
        e5_query = f"query: {query}"
    query_emb = model.encode([e5_query])[0]
    cosine_scores = cosine_similarity_search(query_emb, embeddings, hadith_ids, top_k=50)
    cosine_top = list(cosine_scores.keys())[:per_algo_size]

    pipeline_scores = final_search_pipeline(
        query=query,
        language=language,
        index=index,
        doc_lengths=doc_lengths,
        embeddings=embeddings,
        hadith_ids=hadith_ids,
        model=model,
        eval_ids=all_hadith_ids,
        texts_dict=texts_dict,
        candidate_k=1000,
        rerank_k=per_algo_size,
        final_k=per_algo_size
    )
    pipeline_top = list(pipeline_scores.keys())[:per_algo_size]

    combined = set(bm25_top) | set(cosine_top) | set(pipeline_top)
    return list(combined)

if __name__ == "__main__":
    print("Loading queries.json...")
    with open(os.path.join(DATA_DIR, "queries.json"), encoding="utf-8") as f:
        queries = json.load(f)

    qrels_ungraded = {}
    distributions = {}

    print("\nPooling queries...")
    for qid, query_text in queries.items():
        language = qid[:2]

        print(f"  Processing {qid}...")
        pooled_ids = pool_query(query_text, language)

        qrels_ungraded[qid] = pooled_ids
        distributions[qid] = len(pooled_ids)
        print(f"    -> {len(pooled_ids)} hadiths pooled")

    print("\n" + "=" * 50)
    print("DISTRIBUTIONS")
    print("=" * 50)
    for qid, count in distributions.items():
        print(f"{qid}: {count} hadiths")

    output_path = os.path.join(DATA_DIR, "qrels_ungraded.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(qrels_ungraded, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")