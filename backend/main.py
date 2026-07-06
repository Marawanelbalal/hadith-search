import sqlite3
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, ".", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

os.makedirs(DATA_DIR, exist_ok=True)

APP_MODE = os.environ.get("APP_MODE", "search")

CORS_ORIGINS_ENV = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://192.168.1.6:5173,http://192.168.1.5:5173")
if CORS_ORIGINS_ENV.strip() == "*":
    CORS_ALLOW_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
else:
    CORS_ALLOW_ORIGINS = [o.strip() for o in CORS_ORIGINS_ENV.split(",") if o.strip()]
    CORS_ALLOW_CREDENTIALS = True


def _resolve_static_dir() -> str | None:
    env = os.environ.get("STATIC_DIR")
    if env and os.path.isdir(env):
        return env
    candidates = [
        os.path.join(BASE_DIR, "..", "static"),
        os.path.join(BASE_DIR, "..", "frontend", "dist"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return os.path.abspath(c)
    return None


STATIC_DIR = _resolve_static_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from database import init_annotation_tables, init_kv_pairs_table
    init_annotation_tables()
    init_kv_pairs_table()

    if APP_MODE == "annotation":
        print("APP_MODE=annotation: skipping model/index preload")
        yield
        print("Shutting down...")
        return

    print("Loading indices and models at startup...")
    from scripts.loading import (
        get_english_inverted_index,
        get_arabic_inverted_index,
        get_document_lengths,
        get_hadith_ids,
        get_hadiths_df,
    )
    print("  - English inverted index... ", end="", flush=True)
    get_english_inverted_index()
    print("done")
    print("  - Arabic inverted index... ", end="", flush=True)
    get_arabic_inverted_index()
    print("done")
    print("  - Document lengths... ", end="", flush=True)
    get_document_lengths()
    print("done")
    print("  - Hadith IDs... ", end="", flush=True)
    get_hadith_ids()
    print("done")
    print("  - Hadiths DataFrame... ", end="", flush=True)
    get_hadiths_df()
    print("done")

    if APP_MODE == "search":
        print("APP_MODE=search: lazy-loading E5 model on first request")
    elif APP_MODE == "research":
        print("  - Sentence Transformer model (intfloat/multilingual-e5-large)... ", end="", flush=True)
        from scripts.loading import get_model
        get_model()
        print("done")
    else:
        print(f"APP_MODE={APP_MODE} (unknown): lazy-loading E5 model on first request")

    if STATIC_DIR:
        print(f"Serving frontend from: {STATIC_DIR}")
    else:
        print("No frontend build found (STATIC_DIR not configured)")

    print("Startup complete. All data loaded.")
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.annotation import router as annotation_router
from routers.auth import router as auth_router
from routers.kv_pairs import router as kv_pairs_router

app.include_router(annotation_router)
app.include_router(auth_router)
app.include_router(kv_pairs_router)

if APP_MODE != "annotation":
    from routers.search import router as search_router
    from routers.benchmark import router as benchmark_router
    app.include_router(search_router)
    app.include_router(benchmark_router)


@app.get("/hadith/{hadith_id}")
def get_hadith(hadith_id: int):
    import pandas as pd
    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths WHERE id = ?", connection, params=(hadith_id,))
    if df.empty:
        return {"error": "not found"}
    return df.iloc[0].to_dict()


if STATIC_DIR:
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
