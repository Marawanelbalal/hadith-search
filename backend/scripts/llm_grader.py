import os
import re
import json
import time
import sqlite3
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "5"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

SYSTEM_PROMPT_EN = (
    "You are an expert in Islamic Hadith science and jurisprudence. "
    "Your task is to assess the relevance of a Hadith to a search query. "
    "Respond with ONLY a single digit: 0 (irrelevant), 1 (partially relevant), or 2 (highly relevant). "
    "Do not include any explanation or additional text."
)

SYSTEM_PROMPT_AR = (
    "أنت خبير في علم الحديث والفقه الإسلامي. "
    "مهمتك تقييم مدى صلة الحديث بموضوع البحث. "
    "أجب برقم واحد فقط: 0 (غير ذ صلة)، 1 (ذ صلة جزئية)، أو 2 (ذ صلة قوية). "
    "لا تضمّن أي تفسير أو نص إضافي."
)

GRADE_PROMPT_EN = """\
Query: {query}
Hadith: {hadith_text}

Grade (0, 1, or 2):"""

GRADE_PROMPT_AR = """\
السؤال: {query}
الحديث: {hadith_text}

التقييم (0، 1، أو 2):"""


def build_messages(query, hadith_text, language):
    if language == "AR":
        system = SYSTEM_PROMPT_AR
        user = GRADE_PROMPT_AR.format(query=query, hadith_text=hadith_text)
    else:
        system = SYSTEM_PROMPT_EN
        user = GRADE_PROMPT_EN.format(query=query, hadith_text=hadith_text)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_grade(text):
    match = re.search(r"[012]", text.strip())
    if match:
        return int(match.group())
    return None


def call_llm(messages):
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 5,
    }

    url = LLM_API_BASE.rstrip("/") + "/chat/completions"

    for attempt in range(LLM_MAX_RETRIES):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=LLM_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content
        except requests.exceptions.RequestException as e:
            if attempt < LLM_MAX_RETRIES - 1:
                wait = 2 ** attempt
                print(f"    Retry {attempt+1}/{LLM_MAX_RETRIES} after {wait}s: {e}")
                time.sleep(wait)
            else:
                raise
    return None


def grade_document(query, hadith_text, language):
    messages = build_messages(query, hadith_text, language)
    content = call_llm(messages)
    if content is None:
        return None
    grade = parse_grade(content)
    return grade


def grade_query_pool(query_id, query_text, language, pooled_ids, hadith_texts, max_workers=None):
    workers = max_workers or LLM_MAX_WORKERS
    grades = {}
    tasks = {}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for hid in pooled_ids:
            text = hadith_texts.get(str(hid)) or hadith_texts.get(int(hid))
            if text is None:
                continue
            future = pool.submit(grade_document, query_text, text, language)
            tasks[future] = hid

        for future in as_completed(tasks):
            hid = tasks[future]
            try:
                grade = future.result()
                if grade is not None:
                    grades[str(hid)] = grade
            except Exception as e:
                print(f"    Error grading hadith {hid}: {e}")

    return grades


def load_hadith_texts(language, hadith_ids):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    col = "Arabic_Text" if language == "AR" else "English_Text"
    placeholders = ",".join("?" * len(hadith_ids))
    cursor.execute(
        f"SELECT id, {col} FROM hadiths WHERE id IN ({placeholders})",
        hadith_ids,
    )
    texts = {str(row[0]): row[1] for row in cursor.fetchall() if row[1]}
    conn.close()
    return texts


def save_checkpoint(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def grade_all(queries_path, output_path, pool_fn=None, pool_depth=100, resume=True):
    with open(queries_path, encoding="utf-8") as f:
        queries = json.load(f)

    existing = {}
    if resume and os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"Resuming: {len(existing)}/{len(queries)} queries already graded")

    results = dict(existing)

    for i, (qid, qtext) in enumerate(queries.items()):
        if qid in existing and existing[qid]:
            print(f"  [{i+1}/{len(queries)}] {qid} — skipped (already graded)")
            continue

        language = "AR" if qid.startswith("AR") else "EN"
        print(f"  [{i+1}/{len(queries)}] {qid} — pooling + grading ({language})...")

        if pool_fn is not None:
            pooled_ids = pool_fn(qtext, language, pool_depth)
        else:
            pooled_ids = []

        if not pooled_ids:
            print(f"    No pooled candidates, skipping")
            continue

        hadith_texts = load_hadith_texts(language, pooled_ids)
        print(f"    Pool: {len(pooled_ids)} docs, {len(hadith_texts)} with text")

        grades = grade_query_pool(qid, qtext, language, pooled_ids, hadith_texts)
        results[qid] = grades
        print(f"    Graded: {len(grades)}/{len(hadith_texts)} docs")

        save_checkpoint(output_path, results)

    total_graded = sum(len(v) for v in results.values())
    print(f"\nDone. {len(results)} queries, {total_graded} total grades")
    print(f"Saved to: {output_path}")
    return results


if __name__ == "__main__":
    import argparse
    from scripts.search import (
        bm25_with_expansion,
        cosine_similarity_search,
        bm25,
        tf_idf,
    )
    from scripts.loading import (
        get_english_inverted_index,
        get_arabic_inverted_index,
        get_document_lengths,
        get_english_embeddings,
        get_arabic_embeddings,
        get_hadith_ids,
        get_model,
    )
    from scripts.preprocess import normalize_arabic_text
    from camel_tools.utils.dediac import dediac_ar

    parser = argparse.ArgumentParser(description="LLM grading pipeline for training queries")
    parser.add_argument("--queries", default=os.path.join(DATA_DIR, "training_queries.json"),
                        help="Path to queries JSON")
    parser.add_argument("--output", default=os.path.join(DATA_DIR, "training_qrels_graded.json"),
                        help="Path to output graded qrels JSON")
    parser.add_argument("--pool-depth", type=int, default=100,
                        help="Pooling depth per retrieval system")
    parser.add_argument("--no-resume", action="store_true",
                        help="Start fresh, ignore existing graded file")
    parser.add_argument("--validate", action="store_true",
                        help="Run validation mode on human eval queries instead")
    args = parser.parse_args()

    if args.validate:
        queries_path = os.path.join(DATA_DIR, "queries.json")
        output_path = os.path.join(DATA_DIR, "llm_eval_grades.json")
        pool_path = os.path.join(DATA_DIR, "qrels_ungraded.json")
        print("=== LLM Validation Mode ===")
        print(f"Queries: {queries_path}")
        print(f"Pooled candidates: {pool_path}")
        print(f"Output: {output_path}")
        print(f"LLM endpoint: {LLM_API_BASE}")
        print(f"LLM model: {LLM_MODEL}")
        print()

        with open(pool_path, encoding="utf-8") as f:
            pooled_data = json.load(f)
        with open(queries_path, encoding="utf-8") as f:
            queries = json.load(f)

        existing = {}
        if not args.no_resume and os.path.exists(output_path):
            with open(output_path, encoding="utf-8") as f:
                existing = json.load(f)

        results = dict(existing)

        for i, (qid, qtext) in enumerate(queries.items()):
            if qid in existing and existing[qid]:
                print(f"  [{i+1}/{len(queries)}] {qid} — skipped")
                continue

            language = "AR" if qid.startswith("AR") else "EN"
            pooled_ids = pooled_data.get(qid, [])

            if not pooled_ids:
                print(f"  [{i+1}/{len(queries)}] {qid} — no pooled candidates")
                continue

            hadith_texts = load_hadith_texts(language, pooled_ids)
            print(f"  [{i+1}/{len(queries)}] {qid} — grading {len(hadith_texts)} docs ({language})")

            grades = grade_query_pool(qid, qtext, language, pooled_ids, hadith_texts)
            results[qid] = grades
            print(f"    Graded: {len(grades)} docs")

            save_checkpoint(output_path, results)

        print(f"\nValidation grading done. {len(results)} queries graded.")
        print(f"Run llm_validation.py to compute agreement metrics.")
    else:
        print("=== LLM Grading Pipeline ===")
        print(f"Queries: {args.queries}")
        print(f"Output: {args.output}")
        print(f"Pool depth: {args.pool_depth}")
        print(f"LLM endpoint: {LLM_API_BASE}")
        print(f"LLM model: {LLM_MODEL}")
        print(f"Max workers: {LLM_MAX_WORKERS}")
        print()

        print("Loading retrieval resources...")
        en_index = get_english_inverted_index()
        ar_index = get_arabic_inverted_index()
        doc_lengths = get_document_lengths()
        en_embeddings = get_english_embeddings()
        ar_embeddings = get_arabic_embeddings()
        hadith_ids = get_hadith_ids()
        model = get_model()
        print("Resources loaded.")

        def pool_fn(query, language, per_algo_size):
            index = en_index if language == "EN" else ar_index
            embeddings = en_embeddings if language == "EN" else ar_embeddings

            bm25_scores = bm25(query, language, index, doc_lengths)
            bm25_top = list(bm25_scores.keys())[:per_algo_size]

            tfidf_scores = tf_idf(query, language, index, doc_lengths)
            tfidf_top = list(tfidf_scores.keys())[:per_algo_size]

            if language == "AR":
                e5_query = f"query: {normalize_arabic_text(dediac_ar(query))}"
            else:
                e5_query = f"query: {query}"
            query_emb = model.encode([e5_query])[0]
            cosine_scores = cosine_similarity_search(query_emb, embeddings, hadith_ids, top_k=per_algo_size)
            cosine_top = list(cosine_scores.keys())[:per_algo_size]

            bm25_rocchio = bm25_with_expansion(query, language, index, doc_lengths, get_hadith)
            rocchio_top = list(bm25_rocchio.keys())[:per_algo_size]

            combined = set(bm25_top) | set(tfidf_top) | set(cosine_top) | set(rocchio_top)
            return list(combined)

        from scripts.search import get_hadith

        grade_all(
            queries_path=args.queries,
            output_path=args.output,
            pool_fn=pool_fn,
            pool_depth=args.pool_depth,
            resume=not args.no_resume,
        )
