from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from database import get_db, now_iso

router = APIRouter(prefix="/kv-pairs", tags=["kv-pairs"])


class VerifyRequest(BaseModel):
    status: str  # "verified" or "rejected"


@router.get("")
def list_kv_pairs(
    status: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM kv_pairs"
    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if topic:
        conditions.append("topic LIKE ?")
        params.append(f"%{topic}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    count_query = query.replace("SELECT *", "SELECT COUNT(*)", 1)
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    query += " ORDER BY id LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()

    pairs = []
    for row in rows:
        pairs.append({
            "id": row["id"],
            "topic": row["topic"],
            "language": row["language"],
            "concept_en": row["concept_en"],
            "concept_ar": row["concept_ar"],
            "entity_en": row["entity_en"],
            "entity_ar": row["entity_ar"],
            "hadith_id": row["hadith_id"],
            "hadith_en": row["hadith_en"],
            "hadith_ar": row["hadith_ar"],
            "status": row["status"],
            "created_at": row["created_at"],
            "verified_at": row["verified_at"],
        })

    conn.close()
    return {"pairs": pairs, "total": total, "limit": limit, "offset": offset}


@router.get("/stats")
def kv_pairs_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM kv_pairs")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT status, COUNT(*) FROM kv_pairs GROUP BY status")
    by_status = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT topic, COUNT(*) FROM kv_pairs GROUP BY topic")
    by_topic = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return {
        "total": total,
        "by_status": by_status,
        "by_topic": by_topic,
    }


@router.post("/{pair_id}/verify")
def verify_kv_pair(pair_id: int, req: VerifyRequest):
    if req.status not in ("verified", "rejected"):
        return {"error": "status must be 'verified' or 'rejected'"}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE kv_pairs SET status = ?, verified_at = ? WHERE id = ?",
        (req.status, now_iso(), pair_id),
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        return {"error": "KV pair not found"}
    return {"id": pair_id, "status": req.status}


@router.post("/verify-batch")
def verify_batch(reqs: list[dict]):
    conn = get_db()
    cursor = conn.cursor()
    updated = 0
    for r in reqs:
        pair_id = r.get("id")
        status = r.get("status")
        if not pair_id or status not in ("verified", "rejected"):
            continue
        cursor.execute(
            "UPDATE kv_pairs SET status = ?, verified_at = ? WHERE id = ?",
            (status, now_iso(), pair_id),
        )
        updated += cursor.rowcount
    conn.commit()
    conn.close()
    return {"updated": updated}


@router.get("/export")
def export_verified():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, topic, language, concept_en, concept_ar,
               entity_en, entity_ar, hadith_id, hadith_en, hadith_ar
        FROM kv_pairs WHERE status = 'verified'
        ORDER BY id
    """)
    rows = cursor.fetchall()
    conn.close()

    pairs = []
    for row in rows:
        pairs.append({
            "id": row["id"],
            "topic": row["topic"],
            "language": row["language"],
            "concept_en": row["concept_en"],
            "concept_ar": row["concept_ar"],
            "entity_en": row["entity_en"],
            "entity_ar": row["entity_ar"],
            "hadith_id": row["hadith_id"],
            "hadith_en": row["hadith_en"],
            "hadith_ar": row["hadith_ar"],
        })

    return {"pairs": pairs, "count": len(pairs)}
