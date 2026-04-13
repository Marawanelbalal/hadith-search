import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hadiths.db')
QRELS_PATH = os.path.join(os.path.dirname(__file__), 'qrels.json')

with open(QRELS_PATH, 'r', encoding='utf-8') as f:
    qrels = json.load(f)

conn = sqlite3.connect(DB_PATH)

for query_id, data in qrels.items():
    print(f"\n{'='*80}")
    print(f"Query ID: {query_id}")
    print(f"Query: {data['query']}")
    print(f"Relevant hadiths: {len(data['relevant_ids'])}")
    print('='*80)

    for doc_id in data['relevant_ids']:
        row = conn.execute(
            "SELECT id, Book, Chapter_Title_English, English_Text, Arabic_Text FROM hadiths WHERE id = ?",
            (doc_id,)
        ).fetchone()

        if not row:
            print(f"\n  [!] ID {doc_id} was NOT FOUND IN DATABASE")
            continue

        hadith_id, book, chapter, english, arabic = row
        print(f"\n  Hadith ID: {hadith_id}")
        print(f"  Book: {book}")
        print(f"  Chapter: {chapter}")
        print(f"  English: {english if english else 'N/A'}...")
        print(f"  {'-'*60}")

    input("\nPress Enter to continue to next query...")

conn.close()