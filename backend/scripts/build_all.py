import os
import time
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")

STEPS = [
    {
        "name": "Creating Database from HuggingFace dataset",
        "module": "scripts.data_creation",
        "markers": [DB_PATH],
    },
    {
        "name": "Preprocessing English and Arabic text",
        "module": "scripts.preprocess",
        "markers": [],
        "check": lambda: _has_preprocessed_columns(),
    },
    {
        "name": "Cleaning and Normalizing Grades",
        "module": "scripts.clean_grades",
        "markers": [],
        "check": lambda: _has_normalized_grades(),
    },
    {
        "name": "Building Inverted Indices and Document Lengths",
        "module": "scripts.build_inverted_index",
        "markers": [
            os.path.join(DATA_DIR, "english_inverted_index.pkl"),
            os.path.join(DATA_DIR, "arabic_inverted_index.pkl"),
            os.path.join(DATA_DIR, "document_lengths.pkl"),
        ],
    },
    {
        "name": "Generating Dense Embeddings",
        "module": "scripts.build_embeddings",
        "markers": [
            os.path.join(DATA_DIR, "english_embeddings.npy"),
            os.path.join(DATA_DIR, "arabic_embeddings.npy"),
            os.path.join(DATA_DIR, "hadith_ids.npy"),
        ],
    },
]


def _has_preprocessed_columns():
    if not os.path.isfile(DB_PATH):
        return False
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("PRAGMA table_info(hadiths)")
        cols = {row[1] for row in cur.fetchall()}
        conn.close()
        return "preprocessed_english" in cols or "Preprocessed_English" in cols
    except Exception:
        return False


def _has_normalized_grades():
    if not os.path.isfile(DB_PATH):
        return False
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("PRAGMA table_info(hadiths)")
        cols = {row[1] for row in cur.fetchall()}
        conn.close()
        return "normalized_grade" in cols or "Normalized_Grade" in cols
    except Exception:
        return False


def _output_exists(step):
    if step["markers"]:
        return any(os.path.isfile(m) for m in step["markers"])
    if "check" in step:
        return step["check"]()
    return False


def _prompt_overwrite(name):
    while True:
        choice = input(f"\n[{name}] Output data already exists. [Y]es to rebuild and overwrite, [N]o to skip, [Q]uit: ").strip().lower()
        if choice == 'y':
            return True
        if choice == 'n':
            return False
        if choice == 'q':
            print("Exiting.")
            sys.exit(0)


def run_step(step):
    name = step["name"]
    print(f"\n{'='*60}")
    print(f"Step: {name}")
    print(f"{'='*60}")

    if _output_exists(step):
        if not _prompt_overwrite(name):
            print(f"→ Skipping {name}")
            return

    start = time.perf_counter()
    try:
        module = __import__(step["module"], fromlist=["run"])
        module.run()
        elapsed = time.perf_counter() - start
        print(f"\n✓ {name} completed successfully in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n✗ {name} failed after {elapsed:.2f}s with error: {e}")
        sys.exit(1)


def main():
    for step in STEPS:
        run_step(step)
    print(f"\n{'='*60}")
    print("All build steps completed successfully.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
