import hashlib
import secrets
import json
import os
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from database import get_db, init_annotation_tables, now_iso

router = APIRouter(prefix="/auth", tags=["auth"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
QUERIES_PATH = os.path.join(DATA_DIR, "queries.json")

QUERIES_PER_ANNOTATOR = 2
ANNOTATORS_PER_QUERY = 3


class SignupRequest(BaseModel):
    username: str
    password: str


class SigninRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    key, _ = hash_password(password, salt)
    return secrets.compare_digest(key, stored_hash)


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def load_queries() -> dict:
    with open(QUERIES_PATH, encoding="utf-8") as f:
        return json.load(f)


def auto_assign_queries(annotator_id: int, conn) -> list[str]:
    cursor = conn.cursor()
    cursor.execute("SELECT query_id, COUNT(*) as cnt FROM assignments GROUP BY query_id")
    counts = {row["query_id"]: row["cnt"] for row in cursor.fetchall()}

    all_queries = load_queries()
    all_query_ids = list(all_queries.keys())
    sorted_queries = sorted(all_query_ids, key=lambda q: (counts.get(q, 0), q))

    assigned = []
    for qid in sorted_queries:
        if counts.get(qid, 0) < ANNOTATORS_PER_QUERY:
            cursor.execute(
                "INSERT INTO assignments (annotator_id, query_id, assigned_at) VALUES (?, ?, ?)",
                (annotator_id, qid, now_iso()),
            )
            assigned.append(qid)
        if len(assigned) >= QUERIES_PER_ANNOTATOR:
            break

    return assigned


def get_current_annotator(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT s.annotator_id, a.username FROM sessions s JOIN annotators a ON s.annotator_id = a.id WHERE s.token = ?",
        (token,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"id": row["annotator_id"], "username": row["username"]}


def get_annotator_assignments(annotator_id: int, conn) -> list[str]:
    cursor = conn.cursor()
    cursor.execute("SELECT query_id FROM assignments WHERE annotator_id = ?", (annotator_id,))
    return [row["query_id"] for row in cursor.fetchall()]


@router.post("/signup")
def signup(req: SignupRequest):
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    init_annotation_tables()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM annotators WHERE username = ?", (req.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Username already taken")

    pw_hash, pw_salt = hash_password(req.password)
    cursor.execute(
        "INSERT INTO annotators (username, password_hash, password_salt, created_at) VALUES (?, ?, ?, ?)",
        (req.username, pw_hash, pw_salt, now_iso()),
    )
    annotator_id = cursor.lastrowid

    assigned = auto_assign_queries(annotator_id, conn)

    token = generate_token()
    cursor.execute(
        "INSERT INTO sessions (token, annotator_id, created_at) VALUES (?, ?, ?)",
        (token, annotator_id, now_iso()),
    )

    conn.commit()

    all_queries = load_queries()
    assigned_details = [
        {"query_id": qid, "query": all_queries.get(qid, "")}
        for qid in assigned
    ]

    conn.close()

    return {
        "token": token,
        "annotator": {"id": annotator_id, "username": req.username},
        "assignments": assigned_details,
    }


@router.post("/signin")
def signin(req: SigninRequest):
    init_annotation_tables()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, password_hash, password_salt FROM annotators WHERE username = ?", (req.username,))
    row = cursor.fetchone()

    if not row or not verify_password(req.password, row["password_hash"], row["password_salt"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = generate_token()
    cursor.execute(
        "INSERT INTO sessions (token, annotator_id, created_at) VALUES (?, ?, ?)",
        (token, row["id"], now_iso()),
    )
    conn.commit()

    assigned_ids = get_annotator_assignments(row["id"], conn)
    all_queries = load_queries()
    assigned_details = [
        {"query_id": qid, "query": all_queries.get(qid, "")}
        for qid in assigned_ids
    ]

    conn.close()

    return {
        "token": token,
        "annotator": {"id": row["id"], "username": row["username"]},
        "assignments": assigned_details,
    }


@router.post("/signout")
def signout(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

    return {"success": True}


@router.get("/me")
def me(annotator: dict = Depends(get_current_annotator)):
    conn = get_db()
    assigned_ids = get_annotator_assignments(annotator["id"], conn)
    all_queries = load_queries()
    assigned_details = [
        {"query_id": qid, "query": all_queries.get(qid, "")}
        for qid in assigned_ids
    ]
    conn.close()

    return {
        "annotator": annotator,
        "assignments": assigned_details,
    }
