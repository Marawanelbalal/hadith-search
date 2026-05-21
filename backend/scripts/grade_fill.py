import os
import re
import sqlite3
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hadiths.db')
MAX_WORKERS = 12
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def infer_grade_from_book(book: str) -> str | None:
    if not book:
        return None
    b = book.lower()
    if "sahih al-bukhari" in b or "sahih bukhari" in b:
        return "Sahih (Al-Bukhari)"
    if "sahih muslim" in b:
        return "Sahih (Muslim)"
    return None

def scrape_grade(url: str) -> str | None:
    if not url:
        return None
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for node in soup.select("td.arabic_grade.arabic"):
            text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
            if text and text != "حكم" and len(text) > 3:
                return text
    except Exception as e:
        print(f"Failed {url}: {e}")
    return None

def process_row(row) -> tuple:
    rowid, book, url, _ = row
    grade = infer_grade_from_book(book)
    if grade:
        return rowid, grade, "book"
    grade = scrape_grade(url)
    if grade:
        return rowid, grade, "scraped"
    return rowid, "Unknown", "unknown"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")

    rows = conn.execute("""
        SELECT rowid, Book, Reference, Grade FROM hadiths
        WHERE Grade IS NULL OR TRIM(Grade) = 'Unknown'
    """).fetchall()

    print(f"Missing grades: {len(rows)}")

    # Test single URL before full run
    if rows:
        test = scrape_grade("https://sunnah.com/abudawud:57")
        print(f"Test scrape result: {test}")
        if not test:
            print("WARNING: Scraping not working, check connectivity or site structure")
            return

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_row, row): row for row in rows}
        for fut in as_completed(futures):
            rowid, grade, source = fut.result()
            results.append((rowid, grade, source))
            print(f"rowid={rowid} -> {grade} [{source}]")

    conn.executemany(
        "UPDATE hadiths SET Grade = ? WHERE rowid = ?",
        [(grade, rowid) for rowid, grade, _ in results]
    )
    conn.commit()
    conn.close()

    print(f"\nDone. Total: {len(results)}")
    print(f"Book-inferred: {sum(1 for *_, s in results if s == 'book')}")
    print(f"Scraped:       {sum(1 for *_, s in results if s == 'scraped')}")
    print(f"Unknown:       {sum(1 for *_, s in results if s == 'unknown')}")

if __name__ == "__main__":
    main()