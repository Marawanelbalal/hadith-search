"""
Re-encode hadith embeddings with a fine-tuned model and run evaluation.

Usage:
    python -m scripts.finetune_eval --mode combined
    python -m scripts.finetune_eval --mode triplet --skip-encode

This script:
1. Loads the fine-tuned model (base E5 + LoRA adapter)
2. Re-encodes all hadith embeddings (EN + AR)
3. Saves new .npy files (overwrites existing)
4. Runs the evaluation pipeline
5. Saves results to data/finetuned_results.json
"""

import os
import sys
import json
import argparse
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")
OUTPUT_DIR = os.path.join(DATA_DIR, "finetuned")


def reencode_embeddings(adapter_path, batch_size=32):
    """Re-encode all hadith embeddings using the fine-tuned model."""
    import torch
    from transformers import AutoTokenizer, AutoModel
    from peft import PeftModel

    print(f"=== Re-encoding Embeddings ===")
    print(f"Adapter: {adapter_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT id, English_Text, Arabic_Text FROM hadiths", conn)
    conn.close()

    print(f"Loaded {len(df)} hadiths")

    model_name = "intfloat/multilingual-e5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    base_model = AutoModel.from_pretrained(model_name)
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model = model.merge_and_unload()
    model.to(device)
    model.eval()

    def encode_batch(texts):
        prefixed = [f"passage: {t}" for t in texts]
        batch = tokenizer(
            prefixed,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            outputs = model(**batch)
            mask = batch["attention_mask"].unsqueeze(-1).float()
            embeddings = (outputs.last_hidden_state * mask).sum(1)
            mask_sum = mask.sum(1).clamp(min=1e-9)
            embeddings = embeddings / mask_sum
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return embeddings.cpu().numpy()

    print("Encoding English embeddings...")
    en_texts = df["English_Text"].tolist()
    en_embeddings = []
    for i in range(0, len(en_texts), batch_size):
        batch = en_texts[i:i + batch_size]
        en_embeddings.append(encode_batch(batch))
        if (i // batch_size + 1) % 50 == 0:
            print(f"  {i + len(batch)}/{len(en_texts)}")
    en_embeddings = np.vstack(en_embeddings)
    en_path = os.path.join(DATA_DIR, "english_embeddings.npy")
    np.save(en_path, en_embeddings)
    print(f"Saved {en_embeddings.shape} -> {en_path}")

    print("Encoding Arabic embeddings...")
    ar_texts = df["Arabic_Text"].tolist()
    ar_embeddings = []
    for i in range(0, len(ar_texts), batch_size):
        batch = ar_texts[i:i + batch_size]
        ar_embeddings.append(encode_batch(batch))
        if (i // batch_size + 1) % 50 == 0:
            print(f"  {i + len(batch)}/{len(ar_texts)}")
    ar_embeddings = np.vstack(ar_embeddings)
    ar_path = os.path.join(DATA_DIR, "arabic_embeddings.npy")
    np.save(ar_path, ar_embeddings)
    print(f"Saved {ar_embeddings.shape} -> {ar_path}")

    ids_path = os.path.join(DATA_DIR, "hadith_ids.npy")
    np.save(ids_path, df["id"].values)
    print(f"Saved hadith IDs -> {ids_path}")

    print("Done re-encoding.\n")


def run_evaluation(mode, k=20):
    """Run the evaluation pipeline with the fine-tuned model."""
    from scripts.search import (
        ranked_term_overlap, tf_idf, bm25, bm25_with_expansion,
        bm25_tfidf_hybrid, hybrid_with_expansion,
        semantic_reranker, cross_encoder_rerank, semantic_search_e5,
        bm25_semantic_rrf, get_hadith, final_search_pipeline,
    )
    from scripts.loading import (
        get_english_inverted_index, get_arabic_inverted_index,
        get_document_lengths, get_english_embeddings,
        get_arabic_embeddings, get_hadith_ids, get_model,
    )
    from scripts.evaluation import evaluate_system, _filter_and_rank
    from scripts.stats_tests import run_analysis, generate_latex_table, filter_graded_queries

    print(f"=== Evaluation (fine-tuned: {mode}) ===\n")

    QUERIES_PATH = os.path.join(DATA_DIR, "queries.json")
    QRELS_GRADED_PATH = os.path.join(DATA_DIR, "qrels_graded.json")
    RESULTS_PATH = os.path.join(DATA_DIR, "finetuned_results.json")

    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries_data = json.load(f)
    with open(QRELS_GRADED_PATH, encoding="utf-8") as f:
        qrels_graded = json.load(f)

    query_ids = list(queries_data.keys())
    queries = list(queries_data.values())
    relevant_list = [
        {int(k): v for k, v in qrels_graded.get(qid, {}).get("grades", {}).items()}
        for qid in query_ids
    ]
    languages = ["AR" if qid.startswith("AR") else "EN" for qid in query_ids]

    with sqlite3.connect(DB_PATH) as conn:
        eval_ids = set(pd.read_sql("SELECT id FROM evaluation_hadiths", conn)["id"])
        hadiths_df = pd.read_sql(
            "SELECT id, English_Text, Arabic_Text FROM hadiths", conn
        ).set_index("id")

    en_texts_dict = hadiths_df["English_Text"].to_dict()
    ar_texts_dict = hadiths_df["Arabic_Text"].to_dict()

    print("Loading indexes and models...")
    en_index = get_english_inverted_index()
    ar_index = get_arabic_inverted_index()
    doc_lengths = get_document_lengths()
    en_embeddings = get_english_embeddings()
    ar_embeddings = get_arabic_embeddings()
    hadith_ids = get_hadith_ids()
    sentence_model = get_model()
    eval_mask = np.array([hid in eval_ids for hid in hadith_ids])
    eval_hadith_ids = hadith_ids[eval_mask]
    en_eval_embeddings = en_embeddings[eval_mask]
    ar_eval_embeddings = ar_embeddings[eval_mask]

    print(f"hadith_ids:       {hadith_ids.shape}")
    print(f"en_embeddings:    {en_embeddings.shape}")
    print(f"ar_embeddings:    {ar_embeddings.shape}")
    print(f"eval pool size:   {eval_mask.sum()}")

    def _index(lang):
        return en_index if lang == "EN" else ar_index

    def simulated_pipeline(query, language, model_type):
        index = en_index if language == "EN" else ar_index
        bm25_scores = bm25(query, language, index, doc_lengths)
        eval_pool = eval_ids

        candidates = [
            doc_id for doc_id in sorted(
                bm25_scores.keys(), key=bm25_scores.get, reverse=True
            )
            if doc_id in eval_pool
        ]
        embeddings = en_eval_embeddings if language == "EN" else ar_eval_embeddings
        model = sentence_model

        if model_type == "bi-encoder":
            return semantic_reranker(
                query=query, language=language, candidate_ids=candidates[:500],
                model=model, embeddings=embeddings,
                hadith_ids=eval_hadith_ids, top_k=500,
            )
        elif model_type == "rrf":
            fused = bm25_semantic_rrf(
                query=query, language=language, index=_index(language),
                judged_ids=eval_ids, doc_lengths=doc_lengths,
                corpus_embeddings_normed=embeddings,
                hadith_ids=eval_hadith_ids, model=model,
            )
            return dict(list(fused.items()))
        elif model_type == "cross-encoder":
            candidates = candidates[:100]
            texts = en_texts_dict if language == "EN" else ar_texts_dict
            hadith_texts = {hid: texts[hid] for hid in candidates if hid in texts}
            return cross_encoder_rerank(
                query=query, language=language, candidate_ids=candidates,
                hadith_texts=hadith_texts,
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    PIPELINES = {
        "BM25": lambda q, lang: bm25(q, lang, _index(lang), doc_lengths),
        "TF_IDF": lambda q, lang: tf_idf(q, lang, _index(lang), doc_lengths),
        "Term Overlap": lambda q, lang: ranked_term_overlap(q, lang, _index(lang)),
        "BM25_ROCCHIO": lambda q, lang: bm25_with_expansion(
            q, lang, _index(lang), doc_lengths, get_hadith),
        "BM25_TF_IDF": lambda q, lang: bm25_tfidf_hybrid(
            q, lang, _index(lang), doc_lengths),
        "BM25_TF_IDF_ROCCHIO": lambda q, lang: hybrid_with_expansion(
            q, lang, _index(lang), doc_lengths, get_hadith),
    }
    DENSE = {
        "COSINE_SIMILARITY": lambda q, lang: semantic_search_e5(
            query=q, language=lang, model=sentence_model,
            corpus_embeddings_normed=en_eval_embeddings if lang == "EN" else ar_eval_embeddings,
            hadith_ids=eval_hadith_ids, top_k=20,
        ),
    }
    HYBRIDS = {
        "BM25_SEMANTIC_RERANK": lambda q, lang: simulated_pipeline(q, lang, "bi-encoder"),
        "BM25_RRF": lambda q, lang: simulated_pipeline(q, lang, "rrf"),
        "BM25_CROSS_ENCODER": lambda q, lang: simulated_pipeline(q, lang, "cross-encoder"),
        "FINAL_PIPELINE": lambda q, lang: final_search_pipeline(
            query=q, language=lang, index=_index(lang), doc_lengths=doc_lengths,
            embeddings=en_eval_embeddings if lang == "EN" else ar_eval_embeddings,
            hadith_ids=eval_hadith_ids, model=sentence_model, eval_ids=eval_ids,
            texts_dict=en_texts_dict if lang == "EN" else ar_texts_dict,
        ),
    }
    SYSTEMS = {**PIPELINES, **DENSE, **HYBRIDS}

    all_results = {}
    for system_name, search_fn in SYSTEMS.items():
        print(f"\nEvaluating [{system_name}]...")
        if system_name == "BM25_CROSS_ENCODER":
            import time
            time.sleep(60)

        ranked_per_query = [
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

    graded_qids = {
        qid for qid, rel in zip(query_ids, relevant_list) if len(rel) > 0
    }
    filtered_results = filter_graded_queries(all_results, graded_qids)

    stats_output = run_analysis(filtered_results, baseline="BM25", k=k)
    latex_table = generate_latex_table(
        filtered_results, stats_output["pairwise_tests"],
        baseline="BM25", k=k,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_stamped = RESULTS_PATH.replace(".json", f"_{mode}_{timestamp}.json")
    stats_path = os.path.join(DATA_DIR, f"finetuned_stats_{mode}.json")
    stats_stamped = stats_path.replace(".json", f"_{timestamp}.json")
    latex_path = os.path.join(DATA_DIR, f"finetuned_results_table_{mode}.tex")
    latex_stamped = latex_path.replace(".tex", f"_{timestamp}.tex")

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    with open(results_stamped, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats_output, f, indent=2, ensure_ascii=False)
    with open(stats_stamped, "w", encoding="utf-8") as f:
        json.dump(stats_output, f, indent=2, ensure_ascii=False)

    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(latex_table)
    with open(latex_stamped, "w", encoding="utf-8") as f:
        f.write(latex_table)

    print(f"\nResults saved      -> {RESULTS_PATH}")
    print(f"Results archived   -> {results_stamped}")
    print(f"Stats saved        -> {stats_path}")
    print(f"Stats archived     -> {stats_stamped}")
    print(f"LaTeX table        -> {latex_path}")
    print(f"LaTeX archived     -> {latex_stamped}")

    print(f"\nBest systems per metric (graded queries only):")
    for metric, best_sys in stats_output["summary"]["best_systems"].items():
        mean_val = filtered_results[best_sys]["MEAN"]["Metrics"].get(metric, 0.0)
        print(f"  {metric:12s}: {best_sys} ({float(mean_val):.4f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate fine-tuned model on eval queries"
    )
    parser.add_argument(
        "--mode", choices=["triplet", "kv_pairs", "combined"],
        default="combined",
        help="Which fine-tuned adapter to use",
    )
    parser.add_argument(
        "--adapter-path", default=None,
        help="Custom adapter path (overrides --mode)",
    )
    parser.add_argument(
        "--skip-encode", action="store_true",
        help="Skip re-encoding embeddings (use existing .npy files)",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--k", type=int, default=20)
    args = parser.parse_args()

    adapter_path = args.adapter_path
    if adapter_path is None:
        adapter_path = os.path.join(OUTPUT_DIR, args.mode)

    if not os.path.exists(adapter_path):
        print(f"ERROR: Adapter not found at {adapter_path}")
        print("Run finetune.py first to train and save the adapter.")
        sys.exit(1)

    os.environ["FINETUNED_ADAPTER_PATH"] = adapter_path

    if not args.skip_encode:
        reencode_embeddings(adapter_path, args.batch_size)

    from scripts.loading import get_model, get_english_embeddings, get_arabic_embeddings

    get_model.cache_clear()
    get_english_embeddings.cache_clear()
    get_arabic_embeddings.cache_clear()

    run_evaluation(args.mode, args.k)
