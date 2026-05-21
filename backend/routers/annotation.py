from fastapi import APIRouter, HTTPException
import json
import os
import sqlite3
from pydantic import BaseModel

router = APIRouter(prefix="/annotation", tags=["annotation"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

QUERIES_PATH = os.path.join(DATA_DIR, "queries.json")
QRELS_UNGRADED_PATH = os.path.join(DATA_DIR, "qrels_ungraded.json")
QRELS_GRADED_PATH = os.path.join(DATA_DIR, "qrels_graded.json")


def get_hadith_texts(hadith_ids: list[int]) -> dict[int, dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    results = {}
    for hid in hadith_ids:
        cursor.execute("SELECT Arabic_Text, English_Text FROM hadiths WHERE id = ?", (hid,))
        row = cursor.fetchone()
        if row:
            results[hid] = {
                "arabic_hadith": row[0] or "",
                "english_hadith": row[1] or ""
            }
        else:
            results[hid] = {
                "arabic_hadith": "",
                "english_hadith": ""
            }
    conn.close()
    return results


def load_json(path: str):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class LabelPayload(BaseModel):
    hadith_id: int
    index: int
    label: int


@router.get("/queries")
def get_queries():
    queries_data = load_json(QUERIES_PATH)
    qrels_ungraded = load_json(QRELS_UNGRADED_PATH)
    qrels_graded = load_json(QRELS_GRADED_PATH)

    queries = []
    for qid, query_text in queries_data.items():
        ungraded_hadiths = qrels_ungraded.get(qid, [])
        total = len(ungraded_hadiths)

        graded_grades = qrels_graded.get(qid, {}).get("grades", {})
        graded = len(graded_grades)

        current_index = qrels_graded.get(qid, {}).get("current_index", 0)

        queries.append({
            "query_id": qid,
            "query": query_text,
            "total": total,
            "graded": graded,
            "current_index": current_index
        })

    return {"queries": queries}


@router.get("/{query_id}/current")
def get_current_state(query_id: str):
    queries_data = load_json(QUERIES_PATH)
    qrels_ungraded = load_json(QRELS_UNGRADED_PATH)
    qrels_graded = load_json(QRELS_GRADED_PATH)

    if query_id not in queries_data:
        raise HTTPException(status_code=404, detail="Query not found")

    query_text = queries_data[query_id]
    pooled_ids = qrels_ungraded.get(query_id, [])
    graded_data = qrels_graded.get(query_id, {"grades": {}})
    grades = graded_data.get("grades", {})
    current_index = graded_data.get("current_index", 0)

    if current_index >= len(pooled_ids):
        current_index = len(pooled_ids) - 1 if pooled_ids else 0

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
        "labels": grades
    }


@router.post("/{query_id}/label")
def save_label(query_id: str, payload: LabelPayload):
    queries_data = load_json(QUERIES_PATH)
    qrels_ungraded = load_json(QRELS_UNGRADED_PATH)
    qrels_graded = load_json(QRELS_GRADED_PATH)

    if query_id not in queries_data:
        raise HTTPException(status_code=404, detail="Query not found")

    if query_id not in qrels_graded:
        qrels_graded[query_id] = {
            "query": queries_data[query_id],
            "grades": {},
            "current_index": 0
        }

    qrels_graded[query_id]["grades"][str(payload.hadith_id)] = payload.label

    next_index = payload.index + 1
    if next_index < len(qrels_ungraded.get(query_id, [])):
        qrels_graded[query_id]["current_index"] = next_index

    save_json(QRELS_GRADED_PATH, qrels_graded)

    return {"success": True, "current_index": next_index}


@router.post("/{query_id}/navigate")
def navigate(query_id: str, index: int):
    queries_data = load_json(QUERIES_PATH)
    qrels_ungraded = load_json(QRELS_UNGRADED_PATH)
    qrels_graded = load_json(QRELS_GRADED_PATH)

    if query_id not in queries_data:
        raise HTTPException(status_code=404, detail="Query not found")

    pooled = qrels_ungraded.get(query_id, [])
    if index < 0 or index >= len(pooled):
        raise HTTPException(status_code=400, detail="Invalid index")

    if query_id not in qrels_graded:
        qrels_graded[query_id] = {
            "query": queries_data[query_id],
            "grades": {},
            "current_index": 0
        }

    qrels_graded[query_id]["current_index"] = index
    save_json(QRELS_GRADED_PATH, qrels_graded)

    return {"success": True, "current_index": index}