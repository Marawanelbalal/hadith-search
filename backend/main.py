import sqlite3
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, ".", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

os.makedirs(DATA_DIR, exist_ok=True)

APP_MODE = os.environ.get("APP_MODE", "search")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from database import init_annotation_tables
    init_annotation_tables()

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

    print("Startup complete. All data loaded.")
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://192.168.1.6:5173","http://192.168.1.5:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.search import router as search_router
from routers.benchmark import router as benchmark_router
from routers.annotation import router as annotation_router
from routers.auth import router as auth_router

app.include_router(search_router)
app.include_router(benchmark_router)
app.include_router(annotation_router)
app.include_router(auth_router)

@app.get("/hadith/{hadith_id}")
def get_hadith(hadith_id: int):
    import pandas as pd
    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths WHERE id = ?", connection, params=(hadith_id,))
    if df.empty:
        return {"error": "not found"}
    return df.iloc[0].to_dict()
