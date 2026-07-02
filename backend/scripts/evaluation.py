from math import log2
import time
import pandas as pd

graded_relevant_list = dict[int : int]

def precision(retrieved : set[int], relevant : set[int]) -> float:
    ret = len(retrieved)
    return len(retrieved & relevant) / ret if ret != 0 else 0

def recall(retrieved : set[int], relevant : set[int]) -> float:
    rel = len(relevant)
    return len(retrieved & relevant) / rel if rel != 0 else 0

def fbeta_score(retrieved : set[int], relevant : set[int], beta : float = 1.0) -> float:
    P = precision(retrieved,relevant)
    R = recall(retrieved,relevant)
    numerator = (beta**2 + 1) * P * R
    denominator = (beta**2 * P) + R
    return numerator/denominator if denominator != 0 else 0
    
def f1_score(retrieved : set[int], relevant : set[int]) -> float:
    return fbeta_score(retrieved,relevant,1)

def precision_at_k(retrieved : list[int], relevant : set[int], k : int = 10) -> float:
    retrieved = retrieved[:k]
    return len(set(retrieved) & relevant) / k if k != 0 else 0

def recall_at_k(retrieved : list[int], relevant : set[int], k : int = 10) -> float:
    retrieved = retrieved[:k]
    return recall(set(retrieved),relevant)

def fbeta_score_at_k(retrieved : list[int], relevant : set[int], beta : float = 1.0, k : int = 10) -> float:
    retrieved = retrieved[:k]
    P = len(set(retrieved) & relevant) / k if k != 0 else 0
    R = recall(set(retrieved),relevant)
    numerator = (beta**2 + 1) * P * R
    denominator = (beta**2 * P) + R
    return numerator/denominator if denominator != 0 else 0

def f1_score_at_k(retrieved : list[int], relevant : set[int], k):
    return fbeta_score_at_k(retrieved,relevant,1,k)

def average_precision(retrieved : list[int], relevant : set[int]) -> float:
    relevant_num = 0
    ap = 0
    for i in range(len(retrieved)):
        if retrieved[i] in relevant:
            relevant_num += 1
            ap += relevant_num/(i+1)
    return ap / len(relevant) if len(relevant) != 0 else 0

def average_precision_at_k(retrieved : list[int], relevant : set[int],k : int = 10) -> float:
    if k < len(retrieved):
        retrieved = retrieved[:k]
    return average_precision(retrieved,relevant)

def MAP(retrieved : list[list], relevant: list[list]) -> float:
    """
    Retrieved and relevant should be of the same size which is the number of queries.
    Retrieved and relevant should each be a list of lists containing
    all retrieved lists for each query and all relevant lists for each query respectively.
    """
    ap_sum = 0
    for i in range(len(retrieved)):
        ap_sum += average_precision(retrieved[i],relevant[i])
    return ap_sum / len(retrieved) if len(retrieved) != 0 else 0


def jaccard_similarity(retrieved : set[int], relevant : set[int]) -> float:
    I = len(retrieved & relevant)
    U = len(retrieved | relevant)
    return I / U if U != 0 else 0

def jaccard_similarity_at_k(retrieved : list[int], relevant : set[int], k : int = 10) -> float:
    retrieved = retrieved[:k]
    return jaccard_similarity(set(retrieved),relevant)

def dcg(retrieved : list[int], relevant : graded_relevant_list) -> float:
    dcg_score = 0
    for i in range(len(retrieved)):
        if retrieved[i] in relevant:
            grade = relevant[retrieved[i]]
            dg = (2**grade - 1) / log2(i + 2)
            dcg_score += dg
    return dcg_score

def dcg_at_k(retrieved : list[int], relevant : graded_relevant_list, k : int = 10) -> float:
    retrieved = retrieved[:k]
    return dcg(retrieved, relevant)

def ideal_dcg(relevant : graded_relevant_list, k : int | None = None) -> float:
    sorted_relevant = sorted(relevant, key=relevant.get, reverse=True)
    if k is not None:
        sorted_relevant = sorted_relevant[:k]
    return dcg(sorted_relevant,relevant)

def normalized_dcg(retrieved : list[int], relevant : graded_relevant_list) -> float:
    dcg_score = dcg(retrieved,relevant)
    idcg_score = ideal_dcg(relevant)
    return dcg_score/idcg_score if idcg_score != 0 else 0

def normalized_dcg_at_k(retrieved : list[int], relevant : graded_relevant_list, k : int = 10) -> float:
    dcg_score = dcg_at_k(retrieved,relevant,k)
    idcg_score = ideal_dcg(relevant,k)
    return dcg_score/idcg_score if idcg_score != 0 else 0

def reciprocal_rank(retrieved : list[int], relevant : set[int]) -> float:
    for i,DocId in enumerate(retrieved):
        if DocId in relevant:
            return 1/(i+1)
    return 0.0

def mean_reciprocal_rank(retrieved : list[list[int]],
                         relevant : list[set[int]]) -> float:
    return sum(reciprocal_rank(ret,rel) for ret,rel in zip(retrieved,relevant)) / len(retrieved) if len(retrieved) != 0 else 0
    
def evaluate_query(retrieved : list[int], 
                   relevant : graded_relevant_list) -> pd.DataFrame:
    retrieved_set = set(retrieved)
    relevant_set = set(relevant.keys())
    return pd.DataFrame([
        {
            "Precision": precision(retrieved_set,relevant_set),
            "Recall": recall(retrieved_set,relevant_set),
            "F1_Score": f1_score(retrieved_set,relevant_set),
            "AP": average_precision(retrieved,relevant_set),
            "IoU": jaccard_similarity(retrieved_set,relevant_set),
            "NDCG": normalized_dcg(retrieved,relevant)
        }
    ])

def evaluate_query_at_k(retrieved : list[int], 
                        relevant : graded_relevant_list,
                        k) -> pd.DataFrame:
    relevant_set = set(relevant.keys())
    return pd.DataFrame([
        {
            f"Precision@{k}": precision_at_k(retrieved,relevant_set,k),
            f"Recall@{k}": recall_at_k(retrieved,relevant_set,k),
            f"F1_Score@{k}": f1_score_at_k(retrieved,relevant_set,k),
            f"IoU@{k}": jaccard_similarity_at_k(retrieved,relevant_set,k),
            f"nDCG@{k}": normalized_dcg_at_k(retrieved,relevant,k)
        }
    ])


def evaluate_system(
    query_ids: list[str],
    retrieved_per_query: list[list[int]],
    relevant_per_query: list[graded_relevant_list],
    k: int = 10,
) -> pd.DataFrame:
    """Compute per-query IR metrics and return a DataFrame with a MEAN row."""
    rows = []
    for qid, retrieved, relevant in zip(query_ids, retrieved_per_query, relevant_per_query):
        relevant_set = set(relevant.keys())
        rows.append({
            "query":     qid,
            "AP":        average_precision(retrieved, relevant_set),
            "RR":        reciprocal_rank(retrieved, relevant_set),
            f"P@{k}":    precision_at_k(retrieved, relevant_set, k),
            f"R@{k}":    recall_at_k(retrieved, relevant_set, k),
            f"F1@{k}":   f1_score_at_k(retrieved, relevant_set, k),
            f"nDCG@{k}": normalized_dcg_at_k(retrieved, relevant, k),
        })
    df = pd.DataFrame(rows).set_index("query")
    df.loc["MEAN"] = df.mean()
    return df


def _filter_and_rank(
    scores: dict[int, float], eval_ids: set[int]
) -> list[tuple[int, float]]:
    """Keep only eval-pool documents and return them sorted by descending score."""
    return sorted(
        ((doc_id, score) for doc_id, score in scores.items() if doc_id in eval_ids),
        key=lambda x: x[1],
        reverse=True,
    )



if __name__ == "__main__":
    import json
    import os
    import sqlite3
    import numpy as np
    from scripts.search import (
        ranked_term_overlap,
        tf_idf, bm25, bm25_with_expansion, bm25_tfidf_hybrid, hybrid_with_expansion,
        semantic_reranker, cross_encoder_rerank, semantic_search_e5, bm25_semantic_rrf,
        get_hadith, final_search_pipeline
    )
    from scripts.loading import (
        get_english_inverted_index, get_arabic_inverted_index,
        get_document_lengths,
        get_english_embeddings, get_arabic_embeddings,
        get_hadith_ids,
        get_model
    )


    BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR   = os.path.join(BASE_DIR, "..", "data")
    DB_PATH    = os.path.join(DATA_DIR, "hadiths.db")
    QUERIES_PATH = os.path.join(DATA_DIR, "queries.json")
    QRELS_GRADED_PATH = os.path.join(DATA_DIR, "qrels_graded.json")
    RESULTS_PATH = os.path.join(DATA_DIR, "qrels_results.json")

    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries_data = json.load(f)

    with open(QRELS_GRADED_PATH, encoding="utf-8") as f:
        qrels_graded = json.load(f)

    query_ids     = list(queries_data.keys())
    queries       = list(queries_data.values())
    relevant_list = [
        {int(k): v for k, v in qrels_graded.get(qid, {}).get("grades", {}).items()}
        for qid in query_ids
    ]
    languages = ["AR" if qid.startswith("AR") else "EN" for qid in query_ids]


    with sqlite3.connect(DB_PATH) as conn:
        eval_ids    = set(pd.read_sql("SELECT id FROM evaluation_hadiths", conn)["id"])
        hadiths_df  = pd.read_sql("SELECT id, English_Text, Arabic_Text FROM hadiths", conn).set_index("id")

    en_texts_dict = hadiths_df["English_Text"].to_dict()
    ar_texts_dict = hadiths_df["Arabic_Text"].to_dict()

    print("Loading indexes and models...")
    en_index          = get_english_inverted_index()
    ar_index          = get_arabic_inverted_index()
    doc_lengths       = get_document_lengths()
    en_embeddings     = get_english_embeddings()
    ar_embeddings     = get_arabic_embeddings()
    hadith_ids        = get_hadith_ids()
    sentence_model = get_model()
    eval_mask       = np.array([hid in eval_ids for hid in hadith_ids])
    eval_hadith_ids = hadith_ids[eval_mask]
    en_eval_embeddings = en_embeddings[eval_mask]
    ar_eval_embeddings = ar_embeddings[eval_mask]

    def simulated_2k_pipeline(
        query: str, language: str, model_type: str
    ) -> dict[int, float]:

        index = en_index if language == "EN" else ar_index
        bm25_scores = bm25(query, language, index, doc_lengths)

        eval_pool = eval_ids  # assume set[int]

        # Top BM25 candidates (already ranked properly)
        print(f"Candidates Before: {len(bm25_scores)}")
        candidates = [
            doc_id for doc_id in sorted(
                bm25_scores.keys(),
                key=bm25_scores.get,
                reverse=True
            )
            if doc_id in eval_pool
        ]
        print(f"Candidates After: {len(candidates)}")
        embeddings = en_eval_embeddings if language == "EN" else ar_eval_embeddings
        model = sentence_model

        if model_type == "bi-encoder":
            return semantic_reranker(
                query=query,
                language=language,
                candidate_ids=candidates[:500],
                model=model,
                embeddings=embeddings,
                hadith_ids=eval_hadith_ids,
                top_k=500
            )

        elif model_type == "rrf":

            fused = bm25_semantic_rrf(
                query=query,
                language=language,
                index=_index(language),
                judged_ids=eval_ids,
                doc_lengths=doc_lengths,
                corpus_embeddings_normed = embeddings,
                hadith_ids=eval_hadith_ids,
                model=model,
            )

            return dict(list(fused.items()))

        elif model_type == "cross-encoder":
            candidates = candidates[:100]
            texts = en_texts_dict if language == "EN" else ar_texts_dict
            hadith_texts = {
                hid: texts[hid]
                for hid in candidates
                if hid in texts
            }
            return cross_encoder_rerank(
                query=query,
                language=language,
                candidate_ids=candidates,
                hadith_texts=hadith_texts
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    def _index(lang: str):
        return en_index if lang == "EN" else ar_index
    

    print(f"hadith_ids:       {hadith_ids.shape}")
    print(f"en_embeddings:    {en_embeddings.shape}")
    print(f"ar_embeddings:    {ar_embeddings.shape}")
    print(f"eval pool size:   {eval_mask.sum()}")

    PIPELINES = {
    "BM25": lambda q, lang: bm25(q, lang, _index(lang), doc_lengths),

    "TF_IDF": lambda q, lang: tf_idf(q, lang, _index(lang), doc_lengths),

    "Term Overlap": lambda q, lang: ranked_term_overlap(q, lang, _index(lang)),

    "BM25_ROCCHIO": lambda q, lang: bm25_with_expansion(
        q, lang, _index(lang), doc_lengths, get_hadith
    ),

    "BM25_TF_IDF": lambda q, lang: bm25_tfidf_hybrid(
        q, lang, _index(lang), doc_lengths
    ),

    "BM25_TF_IDF_ROCCHIO": lambda q, lang: hybrid_with_expansion(
        q, lang, _index(lang), doc_lengths, get_hadith
    ),
    }
    DENSE = {
    "COSINE_SIMILARITY": lambda q, lang: semantic_search_e5(
        query=q,
        language=lang,
        model=sentence_model,
        corpus_embeddings_normed= en_eval_embeddings if lang == "EN" else ar_eval_embeddings,
        hadith_ids=eval_hadith_ids,
        top_k=20,
    ),
    }
    HYBRIDS = {
    "BM25_SEMANTIC_RERANK": lambda q, lang: simulated_2k_pipeline(
        q, lang, "bi-encoder"
    ),

    "BM25_RRF": lambda q, lang: simulated_2k_pipeline(
        q, lang, "rrf"
    ),

    "BM25_CROSS_ENCODER": lambda q, lang: simulated_2k_pipeline(
        q, lang, "cross-encoder"
    ),
    "FINAL_PIPELINE": lambda q, lang: final_search_pipeline(
    query=q,
    language=lang,
    index=_index(lang),
    doc_lengths=doc_lengths,
    embeddings=en_eval_embeddings if lang == "EN" else ar_eval_embeddings,
    hadith_ids=eval_hadith_ids,
    model=sentence_model,
    eval_ids=eval_ids,
    texts_dict=en_texts_dict if lang == "EN" else ar_texts_dict
    )
    }
    SYSTEMS = {**PIPELINES,**DENSE,**HYBRIDS}


    k = 20
    all_results: dict[str, dict] = {}

    for system_name, search_fn in SYSTEMS.items():
        print(f"\nEvaluating [{system_name}]...")
        if system_name == "BM25_CROSS_ENCODER":
            time.sleep(60) #avoid jina api free tier rate limits during testing
        ranked_per_query: list[list[tuple[int, float]]] = [
            _filter_and_rank(search_fn(query, lang), eval_ids)
            for query, lang in zip(queries, languages)
        ]

        retrieved_ids = [[doc_id for doc_id, _ in ranked] for ranked in ranked_per_query]
        df = evaluate_system(query_ids, retrieved_ids, relevant_list, k)
        print(df.to_string())

        system_block = {}

        for qid, query_text in zip(query_ids, queries):
            row = df.loc[qid]

            system_block[qid] = {
                "Query Text": query_text,
                "Metrics": {
                    "AP": float(row["AP"]),
                    "RR": float(row["RR"]),
                    "P@20": float(row["P@20"]),
                    "R@20": float(row["R@20"]),
                    "F1@20": float(row["F1@20"]),
                    f"nDCG@{k}": float(row[f"nDCG@{k}"]),
                },
            }
        mean_row = df.loc["MEAN"]

        system_block["MEAN"] = {
            "Metrics": {
                "AP": float(mean_row["AP"]),
                "RR": float(mean_row["RR"]),
                "P@20": float(mean_row["P@20"]),
                "R@20": float(mean_row["R@20"]),
                "F1@20": float(mean_row["F1@20"]),
                f"nDCG@{k}": float(mean_row[f"nDCG@{k}"]),
            }
        }

        all_results[system_name] = system_block

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved → {RESULTS_PATH}")


