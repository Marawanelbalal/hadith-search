from math import log2
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
    if k < len(retrieved):
        retrieved = retrieved[:k]
    return precision(set(retrieved),relevant)

def recall_at_k(retrieved : list[int], relevant : set[int], k : int = 10) -> float:
    if k < len(retrieved):
        retrieved = retrieved[:k]
    return recall(set(retrieved),relevant)

def fbeta_score_at_k(retrieved : list[int], relevant : set[int], beta : float = 1.0, k : int = 10) -> float:
    if k < len(retrieved):
        retrieved = retrieved[:k]
    P = precision(set(retrieved),relevant)
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
    if k < len(retrieved):
        retrieved = retrieved[:k]
    return jaccard_similarity(set(retrieved),relevant)

def dcg(retrieved : list[int], relevant : graded_relevant_list) -> float:
    dcg_score = 0
    for i in range(len(retrieved)):
        if retrieved[i] in relevant:
            grade = relevant[retrieved[i]]
            dg = grade / log2(i + 2)
            dcg_score += dg
    return dcg_score

def dcg_at_k(retrieved : list[int], relevant : graded_relevant_list, k : int = 10) -> float:
    if k < len(retrieved):
        retrieved = retrieved[:k]
    return dcg(retrieved, relevant)

def ideal_dcg(relevant : graded_relevant_list) -> float:
    sorted_relevant = sorted(relevant, key=relevant.get, reverse=True)
    return dcg(sorted_relevant,relevant)

def normalized_dcg(retrieved : list[int], relevant : graded_relevant_list) -> float:
    dcg_score = dcg(retrieved,relevant)
    idcg_score = ideal_dcg(relevant)
    return dcg_score/idcg_score if idcg_score != 0 else 0

def normalized_dcg_at_k(retrieved : list[int], relevant : graded_relevant_list, k : int = 10) -> float:
    dcg_score = dcg_at_k(retrieved,relevant,k)
    idcg_score = ideal_dcg(relevant)
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
    queries: list[str],
    retrieved_per_query: list[list[int]],
    relevant_per_query: list[graded_relevant_list],
    k: int = 10
) -> pd.DataFrame:
    relevant_set_per_query = [set(graded_list.keys()) for graded_list in relevant_per_query]
    
    rows = []
    for query, retrieved, relevant, relevant_set in zip(queries, retrieved_per_query, relevant_per_query, relevant_set_per_query):
        retrieved_set = set(retrieved)
        rows.append({
            "query":        query,
            "AP":           average_precision(retrieved, relevant_set),
            "RR":           reciprocal_rank(retrieved, relevant_set),
            f"P@{k}":       precision_at_k(retrieved, relevant_set, k),
            f"R@{k}":       recall_at_k(retrieved, relevant_set, k),
            f"F1@{k}":      f1_score_at_k(retrieved, relevant_set, k),
            f"nDCG@{k}":    normalized_dcg_at_k(retrieved, relevant, k),
        })
    df = pd.DataFrame(rows).set_index("query")
    df.loc["MEAN"] = df.mean()
    return df






if __name__ == "__main__":
    import json
    import os
    import sqlite3
    from scripts.search import ranked_boolean_retrieval, tf_idf, bm25, bm25_with_expansion, bm25_tfidf_hybrid, hybrid_with_expansion
    
    def get_filtered_ranked_ids(results: dict[int, float], eval_ids: set[int]) -> dict[int, float]:
        filtered_dict = {doc_id: score for doc_id, score in results.items() if doc_id in eval_ids}
        return [docid for docid, _ in sorted(filtered_dict.items(), key=lambda x: x[1], reverse=True)]
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    DB_PATH = os.path.join(DATA_DIR, "hadiths.db")
    conn = sqlite3.connect(DB_PATH)
    eval_ids = set(pd.read_sql("SELECT ID FROM evaluation_hadiths", conn)["id"])
    conn.close()    

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    QRELS_PATH = os.path.join(BASE_DIR, "qrels.json")

    with open(QRELS_PATH, encoding="utf-8") as f:
        qrels = json.load(f)


    query_ids     = list(qrels.keys())
    queries       = [v["query"] for v in qrels.values()]
    relevant_list = [
        {int(k): v for k, v in entry["grades"].items()}  #JSON keys are strings by default so this casting is essential
        for entry in qrels.values()
    ]

    languages = ["AR" if qid.startswith("AR") else "EN" for qid in query_ids]

    systems = {
        "Boolean": lambda q, lang: get_filtered_ranked_ids(ranked_boolean_retrieval(q, lang), eval_ids),
        "TF-IDF":  lambda q, lang: get_filtered_ranked_ids(tf_idf(q, lang), eval_ids),
        "BM25":    lambda q, lang: get_filtered_ranked_ids(bm25(q, lang), eval_ids),
        "BM25+ROCCHIO": lambda q,lang: get_filtered_ranked_ids(bm25_with_expansion(q, lang), eval_ids),
        "BM25_TF_IDF": lambda q,lang: get_filtered_ranked_ids(bm25_tfidf_hybrid(q, lang), eval_ids),
        "BM25_TF_IDF+ROCCHIO": lambda q,lang: get_filtered_ranked_ids(hybrid_with_expansion(q, lang), eval_ids),
    }

    k = 20

    for system_name, search_fn in systems.items():
        retrieved_per_query = [
            search_fn(query, lang)
            for query, lang in zip(queries, languages)
        ]
        sample_retrieved = retrieved_per_query[0]
        sample_relevant = relevant_list[0]
        
        df = evaluate_system(query_ids, retrieved_per_query, relevant_list, k)
        print(f"\n{'='*20} {system_name} {'='*20}")
        print(df.to_string())