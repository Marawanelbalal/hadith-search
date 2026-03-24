import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hadiths.db')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'evaluation_corpus.csv')

def export_evaluation_corpus():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT 
            id,
            Book,
            Chapter_Title_English,
            English_Text,
            Arabic_Text,
            Grade,
            Normalized_Grade,
            Reference
        FROM evaluation_hadiths
        ORDER BY Book, Chapter_Number
    """, conn)
    conn.close()

    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"Exported {len(df)} hadiths to {OUTPUT_PATH}")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    export_evaluation_corpus()