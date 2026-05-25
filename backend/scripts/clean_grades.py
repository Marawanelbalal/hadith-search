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

def fill_grades(conn):
    rows = conn.execute("""
        SELECT rowid, Book, Reference, Grade FROM hadiths
        WHERE Grade IS NULL OR TRIM(Grade) = '' OR TRIM(Grade) = 'Unknown'
    """).fetchall()

    print(f"Missing grades: {len(rows)}")
    if not rows:
        print("Nothing to fill.")
        return

    test = scrape_grade("https://sunnah.com/abudawud:57")
    print(f"Test scrape result: {test}")
    if not test:
        print("WARNING: Scraping not working, book-inferred grades will still be filled.")

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

    print(f"\nFill complete. Total: {len(results)}")
    print(f"Book-inferred: {sum(1 for *_, s in results if s == 'book')}")
    print(f"Scraped:       {sum(1 for *_, s in results if s == 'scraped')}")
    print(f"Unknown:       {sum(1 for *_, s in results if s == 'unknown')}")

# --- Normalize grades ---

def normalize_grade(grade: str) -> str:
    if not grade or grade.strip() == "Unknown":
        return "Unknown"

    g = grade.lower()

    def first_pos(terms):
        positions = [g.find(t) for t in terms if g.find(t) != -1]
        return min(positions) if positions else float('inf')

    scores = {
        "Maudu (Fabricated)": first_pos(["maudu", "mawdu", "fabricat", "موضوع"]),
        "Da'if (Weak)":        first_pos(["da'if", "da\u2019if", "daif", "da if",
                                           "da`if", "da,if", "ضعيف", "shadh",
                                           "munkar", "منكر", "شاذ", "maqtu", "مقطوع", "1819"]),
        "Hasan":               first_pos(["hasan", "حسن"]),
        "Sahih":               first_pos(["sahih", "صحيح", "sah,"]),
    }

    scores = {k: v for k, v in scores.items() if v != float('inf')}
    return min(scores, key=lambda k: scores[k]) if scores else "Unknown"

def normalize_grades(conn):
    try:
        conn.execute("ALTER TABLE hadiths ADD COLUMN Normalized_Grade TEXT")
        conn.commit()
        print("Added Normalized_Grade column")
    except sqlite3.OperationalError:
        print("Normalized_Grade column already exists, overwriting...")

    rows = conn.execute("SELECT rowid, Grade FROM hadiths").fetchall()
    normalized = [(normalize_grade(grade), rowid) for rowid, grade in rows]

    conn.executemany(
        "UPDATE hadiths SET Normalized_Grade = ? WHERE rowid = ?",
        normalized
    )
    conn.commit()

    dist = conn.execute("""
        SELECT Normalized_Grade, COUNT(*) as count
        FROM hadiths
        GROUP BY Normalized_Grade
        ORDER BY count DESC
    """).fetchall()

    print("\nNormalized Grade Distribution:")
    for grade, count in dist:
        print(f"{count:6d} | {grade}")


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")

    print("=== Step 1: Filling missing grades ===")
    fill_grades(conn)

    print("\n=== Step 2: Normalizing grades ===")
    normalize_grades(conn)

    conn.close()

if __name__ == "__main__":
    run()