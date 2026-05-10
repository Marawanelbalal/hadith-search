from fastapi import APIRouter, Depends
import json
import os
from scripts.loading import get_hadiths_df

router = APIRouter(prefix="/benchmark", tags=["benchmark"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
QRELS_PATH = os.path.join(DATA_DIR, "qrels.json")
QRELS_RESULTS_PATH = os.path.join(DATA_DIR, "qrels_results.json")


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/results")
def benchmark_results():
    return load_json(QRELS_RESULTS_PATH)


@router.get("/qrels")
def benchmark_qrels(hadiths_df=Depends(get_hadiths_df)):
    qrels = load_json(QRELS_PATH)

    enhanced = {}
    for qid, entry in qrels.items():
        enhanced[qid] = {
            "query": entry["query"],
            "grades": {
                hid: {
                    "grade": grade,
                    "hadith": hadiths_df.loc[int(hid)].to_dict()
                    if int(hid) in hadiths_df.index
                    else {"error": "not found"},
                }
                for hid, grade in entry["grades"].items()
            },
        }

    return {
        "description": (
            "Generated from a stratified sample of 2000 hadiths across books and chapters. "
            "Results reflect only those 2000 hadiths for fair comparison, "
            "covering all currently available algorithms."
        ),
        "qrels": enhanced,
    }