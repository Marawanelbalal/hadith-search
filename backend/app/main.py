import sqlite3
import os
import pandas as pd
from fastapi import FastAPI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI()

@app.get("/hadith/{hadith_id}")
def get_hadith(hadith_id: int):
    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths WHERE id = ?", connection, params=(hadith_id,))
    if df.empty:
        return {"error": "not found"}
    return df.iloc[0].to_dict()