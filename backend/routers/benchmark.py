from fastapi import APIRouter, Depends
import json
import os
from scripts.loading import get_hadiths_df

router = APIRouter(prefix="/benchmark", tags=["benchmark"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
QUERIES_PATH = os.path.join(DATA_DIR, "queries.json")
QRELS_RESULTS_PATH = os.path.join(DATA_DIR, "qrels_results.json")
STATS_RESULTS_PATH = os.path.join(DATA_DIR, "stats_results.json")


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/results")
def benchmark_results():
    return load_json(QRELS_RESULTS_PATH)


@router.get("/stats")
def benchmark_stats():
    path = STATS_RESULTS_PATH
    if not os.path.exists(path):
        return {"error": "No stats results found. Run evaluation first."}
    return load_json(path)


@router.get("/qrels")
def benchmark_qrels(hadiths_df=Depends(get_hadiths_df)):
    queries_data = load_json(QUERIES_PATH)

    enhanced = {}
    for qid, query_text in queries_data.items():
        enhanced[qid] = {
            "query": query_text,
            "grades": {}
        }

    return {
        "description": (
            "Generated from a stratified sample of 2000 hadiths across books and chapters. "
            "Results reflect only those 2000 hadiths for fair comparison, "
            "covering all currently available algorithms."
        ),
        "qrels": enhanced,
    }