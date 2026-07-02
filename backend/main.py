import sqlite3
import os
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, ".", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

os.makedirs(DATA_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading indices and models at startup...")
    from scripts.loading import (
        get_english_inverted_index,
        get_arabic_inverted_index,
        get_document_lengths,
        get_english_embeddings,
        get_arabic_embeddings,
        get_hadith_ids,
        get_hadiths_df,
        get_model,
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
    print("  - English embeddings... ", end="", flush=True)
    get_english_embeddings()
    print("done")
    print("  - Arabic embeddings... ", end="", flush=True)
    get_arabic_embeddings()
    print("done")
    print("  - Hadith IDs... ", end="", flush=True)
    get_hadith_ids()
    print("done")
    print("  - Hadiths DataFrame... ", end="", flush=True)
    get_hadiths_df()
    print("done")
    print("  - Sentence Transformer model (intfloat/multilingual-e5-large)... ", end="", flush=True)
    get_model()
    print("done")
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

app.include_router(search_router)
app.include_router(benchmark_router)
app.include_router(annotation_router)

@app.get("/hadith/{hadith_id}")
def get_hadith(hadith_id: int):
    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths WHERE id = ?", connection, params=(hadith_id,))
    if df.empty:
        return {"error": "not found"}
    return df.iloc[0].to_dict()