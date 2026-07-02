from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from database import get_db, init_annotation_tables, now_iso
from routers.auth import get_current_annotator
import sqlite3
import json
import os

router = APIRouter(prefix="/annotation", tags=["annotation"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

QUERIES_PATH = os.path.join(DATA_DIR, "queries.json")
QRELS_UNGRADED_PATH = os.path.join(DATA_DIR, "qrels_ungraded.json")


def load_json(path: str):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_hadith_texts(hadith_ids: list[int]) -> dict[int, dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    results = {}
    for hid in hadith_ids:
        cursor.execute(
            'SELECT Arabic_Text, English_Text, Book, Normalized_Grade, Reference, "In-book reference" FROM hadiths WHERE id = ?',
            (hid,),
        )
        row = cursor.fetchone()
        if row:
            results[hid] = {
                "arabic_hadith": row[0] or "",
                "english_hadith": row[1] or "",
                "book": row[2] or "",
                "normalized_grade": row[3] or "",
                "reference": row[4] or "",
                "in_book_reference": row[5] or "",
            }
        else:
            results[hid] = {
                "arabic_hadith": "",
                "english_hadith": "",
                "book": "",
                "normalized_grade": "",
                "reference": "",
                "in_book_reference": "",
            }
    conn.close()
    return results


def verify_assignment(annotator_id: int, query_id: str, conn) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM assignments WHERE annotator_id = ? AND query_id = ?",
        (annotator_id, query_id),
    )
    return cursor.fetchone() is not None


def get_annotator_labels(annotator_id: int, query_id: str, conn) -> dict[str, int]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT hadith_id, label FROM annotations WHERE annotator_id = ? AND query_id = ?",
        (annotator_id, query_id),
    )
    return {str(row["hadith_id"]): row["label"] for row in cursor.fetchall()}


def get_progress(annotator_id: int, query_id: str, conn) -> int:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT current_index FROM annotation_progress WHERE annotator_id = ? AND query_id = ?",
        (annotator_id, query_id),
    )
    row = cursor.fetchone()
    return row["current_index"] if row else 0


def set_progress(annotator_id: int, query_id: str, index: int, conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO annotation_progress (annotator_id, query_id, current_index) VALUES (?, ?, ?) "
        "ON CONFLICT(annotator_id, query_id) DO UPDATE SET current_index = ?",
        (annotator_id, query_id, index, index),
    )


class LabelPayload(BaseModel):
    hadith_id: int
    index: int
    label: int


@router.get("/queries")
def get_queries(annotator: dict = Depends(get_current_annotator)):
    init_annotation_tables()
    conn = get_db()

    cursor = conn.cursor()
    cursor.execute(
        "SELECT query_id FROM assignments WHERE annotator_id = ?",
        (annotator["id"],),
    )
    assigned_ids = [row["query_id"] for row in cursor.fetchall()]

    queries_data = load_json(QUERIES_PATH)
    qrels_ungraded = load_json(QRELS_UNGRADED_PATH)

    queries = []
    for qid in assigned_ids:
        pooled = qrels_ungraded.get(qid, [])
        total = len(pooled)
        labels = get_annotator_labels(annotator["id"], qid, conn)
        graded = len(labels)
        current_index = get_progress(annotator["id"], qid, conn)

        if current_index >= total:
            current_index = total - 1 if total else 0

        queries.append({
            "query_id": qid,
            "query": queries_data.get(qid, ""),
            "total": total,
            "graded": graded,
            "current_index": current_index,
        })

    conn.close()
    return {"queries": queries}


@router.get("/{query_id}/current")
def get_current_state(query_id: str, annotator: dict = Depends(get_current_annotator)):
    init_annotation_tables()
    conn = get_db()

    if not verify_assignment(annotator["id"], query_id, conn):
        conn.close()
        raise HTTPException(status_code=403, detail="You are not assigned to this query")

    queries_data = load_json(QUERIES_PATH)
    if query_id not in queries_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Query not found")

    query_text = queries_data[query_id]
    pooled_ids = load_json(QRELS_UNGRADED_PATH).get(query_id, [])
    labels = get_annotator_labels(annotator["id"], query_id, conn)
    current_index = get_progress(annotator["id"], query_id, conn)

    if current_index >= len(pooled_ids):
        current_index = len(pooled_ids) - 1 if pooled_ids else 0

    conn.close()

    hadith_texts = get_hadith_texts(pooled_ids)
    pooled_hadiths = [
        {"hadith_id": hid, **hadith_texts.get(hid, {"arabic_hadith": "", "english_hadith": ""})}
        for hid in pooled_ids
    ]

    return {
        "query_id": query_id,
        "query": query_text,
        "current_index": current_index,
        "total": len(pooled_ids),
        "pooled_hadiths": pooled_hadiths,
        "labels": labels,
    }


@router.post("/{query_id}/label")
def save_label(query_id: str, payload: LabelPayload, annotator: dict = Depends(get_current_annotator)):
    init_annotation_tables()
    conn = get_db()

    if not verify_assignment(annotator["id"], query_id, conn):
        conn.close()
        raise HTTPException(status_code=403, detail="You are not assigned to this query")

    queries_data = load_json(QUERIES_PATH)
    if query_id not in queries_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Query not found")

    qrels_ungraded = load_json(QRELS_UNGRADED_PATH)
    pooled = qrels_ungraded.get(query_id, [])

    if payload.label not in (0, 1, 2):
        conn.close()
        raise HTTPException(status_code=400, detail="Label must be 0, 1, or 2")

    ts = now_iso()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO annotations (annotator_id, query_id, hadith_id, label, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(annotator_id, query_id, hadith_id) DO UPDATE SET label = ?, updated_at = ?",
        (annotator["id"], query_id, payload.hadith_id, payload.label, ts, ts, payload.label, ts),
    )

    next_index = payload.index + 1
    if next_index < len(pooled):
        set_progress(annotator["id"], query_id, next_index, conn)
    else:
        set_progress(annotator["id"], query_id, payload.index, conn)

    conn.commit()
    conn.close()

    return {"success": True, "current_index": next_index}


@router.post("/{query_id}/navigate")
def navigate(query_id: str, index: int, annotator: dict = Depends(get_current_annotator)):
    init_annotation_tables()
    conn = get_db()

    if not verify_assignment(annotator["id"], query_id, conn):
        conn.close()
        raise HTTPException(status_code=403, detail="You are not assigned to this query")

    queries_data = load_json(QUERIES_PATH)
    if query_id not in queries_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Query not found")

    pooled = load_json(QRELS_UNGRADED_PATH).get(query_id, [])
    if index < 0 or index >= len(pooled):
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid index")

    set_progress(annotator["id"], query_id, index, conn)
    conn.commit()
    conn.close()

    return {"success": True, "current_index": index}


@router.get("/stats/agreement")
def get_agreement_stats(annotator: dict = Depends(get_current_annotator)):
    init_annotation_tables()
    conn = get_db()

    queries_data = load_json(QUERIES_PATH)
    qrels_ungraded = load_json(QRELS_UNGRADED_PATH)

    cursor = conn.cursor()

    per_query = []
    all_kappas = []
    all_spearmans = []

    for qid in queries_data:
        pooled_ids = qrels_ungraded.get(qid, [])
        if not pooled_ids:
            continue

        cursor.execute(
            "SELECT annotator_id FROM assignments WHERE query_id = ?",
            (qid,),
        )
        annotator_ids = [row["annotator_id"] for row in cursor.fetchall()]

        if len(annotator_ids) < 2:
            per_query.append({
                "query_id": qid,
                "query": queries_data[qid],
                "annotators": len(annotator_ids),
                "kappa": None,
                "agreement": None,
            })
            continue

        all_labels = {}
        for aid in annotator_ids:
            cursor.execute(
                "SELECT hadith_id, label FROM annotations WHERE annotator_id = ? AND query_id = ?",
                (aid, qid),
            )
            all_labels[aid] = {row["hadith_id"]: row["label"] for row in cursor.fetchall()}

        common_ids = set(pooled_ids)
        for aid in annotator_ids:
            common_ids = common_ids & set(all_labels[aid].keys())

        common_ids = sorted(common_ids)
        if len(common_ids) < 2:
            per_query.append({
                "query_id": qid,
                "query": queries_data[qid],
                "annotators": len(annotator_ids),
                "common_labeled": len(common_ids),
                "kappa": None,
                "agreement": None,
            })
            continue

        import numpy as np
        label_matrix = np.array([[all_labels[aid][hid] for hid in common_ids] for aid in annotator_ids])

        from itertools import combinations
        from sklearn.metrics import cohen_kappa_score
        from scipy.stats import spearmanr

        pair_kappas = []
        pair_spearmans = []
        for i, j in combinations(range(len(annotator_ids)), 2):
            k = cohen_kappa_score(label_matrix[i], label_matrix[j])
            if k is not None and not np.isnan(k):
                pair_kappas.append(k)
            rho, _ = spearmanr(label_matrix[i], label_matrix[j])
            if rho is not None and not np.isnan(rho):
                pair_spearmans.append(rho)

        avg_kappa = sum(pair_kappas) / len(pair_kappas) if pair_kappas else None
        avg_spearman = sum(pair_spearmans) / len(pair_spearmans) if pair_spearmans else None

        raw_agree = sum(1 for hid in common_ids
                        if len(set(all_labels[aid][hid] for aid in annotator_ids)) == 1) / len(common_ids)

        if avg_kappa is not None:
            all_kappas.append(avg_kappa)
        if avg_spearman is not None:
            all_spearmans.append(avg_spearman)

        per_query.append({
            "query_id": qid,
            "query": queries_data[qid],
            "annotators": len(annotator_ids),
            "common_labeled": len(common_ids),
            "kappa": round(avg_kappa, 4) if avg_kappa is not None else None,
            "spearman": round(avg_spearman, 4) if avg_spearman is not None else None,
            "raw_agreement": round(raw_agree, 4),
        })

    overall = {
        "mean_kappa": round(sum(all_kappas) / len(all_kappas), 4) if all_kappas else None,
        "mean_spearman": round(sum(all_spearmans) / len(all_spearmans), 4) if all_spearmans else None,
        "queries_with_agreement": len(all_kappas),
        "total_queries": len(queries_data),
    }

    conn.close()
    return {"per_query": per_query, "overall": overall}
