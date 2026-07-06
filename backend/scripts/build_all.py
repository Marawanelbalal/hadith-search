import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scripts import data_creation

DATA_DIR = os.path.join(SCRIPTS_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")
MANIFEST_PATH = os.path.join(DATA_DIR, "build_manifest.json")


def _has_columns(required_columns):
    if not os.path.isfile(DB_PATH):
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("PRAGMA table_info(hadiths)")
        cols = {row[1] for row in cur.fetchall()}
        conn.close()
        return set(required_columns).issubset(cols)
    except Exception:
        return False


def _has_preprocessed_data():
    required_columns = [
        "Preprocessed_English",
        "Preprocessed_Arabic",
        "Preprocessed_English_Isnad",
        "Preprocessed_Arabic_Isnad",
        "Preprocessed_English_Matn",
        "Preprocessed_Arabic_Matn",
    ]
    if not _has_columns(required_columns):
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("""
            SELECT COUNT(*)
            FROM hadiths
            WHERE COALESCE(NULLIF(TRIM(Preprocessed_English_Matn), ''), '') != ''
               OR COALESCE(NULLIF(TRIM(Preprocessed_Arabic_Matn), ''), '') != ''
        """).fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def _row_count():
    if not os.path.isfile(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return None


def _output_exists(step):
    if step.get("always_run"):
        return False
    if "check" in step:
        return step["check"]()
    markers = step.get("markers", [])
    return bool(markers) and all(os.path.isfile(marker) for marker in markers)


def _prompt_overwrite(name):
    while True:
        choice = input(f"\n[{name}] Output data already exists. [Y]es to rebuild, [N]o to skip, [Q]uit: ").strip().lower()
        if choice == "y":
            return True
        if choice == "n":
            return False
        if choice == "q":
            print("Exiting.")
            sys.exit(0)


def _make_steps(skip_embeddings):
    steps = [
        {
            "name": "Creating SQLite database from LK Hadith Corpus",
            "module": "scripts.data_creation",
            "markers": [DB_PATH],
        },
        {
            "name": "Profiling loaded corpus",
            "module": "scripts.profile",
            "always_run": True,
        },
        {
            "name": "Preprocessing full text, isnad, and matn",
            "module": "scripts.preprocess",
            "check": _has_preprocessed_data,
        },
        {
            "name": "Building matn-focused inverted indices",
            "module": "scripts.build_inverted_index",
            "markers": [
                os.path.join(DATA_DIR, "english_inverted_index.pkl"),
                os.path.join(DATA_DIR, "arabic_inverted_index.pkl"),
                os.path.join(DATA_DIR, "document_lengths.pkl"),
            ],
        },
    ]

    if not skip_embeddings:
        steps.extend([
            {
                "name": "Generating dense embeddings",
                "module": "scripts.build_embeddings",
                "markers": [
                    os.path.join(DATA_DIR, "english_embeddings.npy"),
                    os.path.join(DATA_DIR, "arabic_embeddings.npy"),
                    os.path.join(DATA_DIR, "hadith_ids.npy"),
                ],
            },
            {
                "name": "Pooling candidate qrels",
                "module": "scripts.pooling",
                "markers": [os.path.join(DATA_DIR, "qrels_ungraded.json")],
            },
        ])

    return steps


def run_step(step, force):
    name = step["name"]
    print(f"\n{'=' * 72}")
    print(f"Step: {name}")
    print(f"{'=' * 72}")

    if _output_exists(step) and not force:
        if not _prompt_overwrite(name):
            print(f"Skipping {name}")
            return {"name": name, "status": "skipped", "elapsed_seconds": 0}

    start = time.perf_counter()
    try:
        module = __import__(step["module"], fromlist=["run"])
        module.run()
        elapsed = time.perf_counter() - start
        print(f"\n{name} completed successfully in {elapsed:.2f}s")
        return {"name": name, "status": "completed", "elapsed_seconds": round(elapsed, 3)}
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"\n{name} failed after {elapsed:.2f}s with error: {e}")
        raise


def write_manifest(step_results, skip_embeddings):
    source_path = data_creation.resolve_lk_source()
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "LK-Hadith-Corpus",
        "source_repo": data_creation.LK_REPO_URL,
        "source_path": str(source_path),
        "source_commit": data_creation.get_source_commit(source_path),
        "row_count": _row_count(),
        "db_path": DB_PATH,
        "skip_embeddings": skip_embeddings,
        "canonical_corpus": "bilingual_matn",
        "drop_policy": "drop rows missing English_Matn or Arabic_Matn after deterministic reconstruction",
        "dropped_rows_file": os.path.join(DATA_DIR, "dropped_lk_rows.json"),
        "embedding_model": "intfloat/multilingual-e5-large",
        "sparse_index_fields": {
            "EN": "Preprocessed_English_Matn",
            "AR": "Preprocessed_Arabic_Matn",
        },
        "dense_embedding_fields": {
            "EN": "Chapter_Title_English + English_Matn",
            "AR": "Chapter_Title_Arabic + Arabic_Matn",
        },
        "steps": step_results,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nBuild manifest written to {MANIFEST_PATH}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the LK-native hadith search data pipeline.")
    parser.add_argument("--force", action="store_true", help="Rebuild existing outputs without interactive prompts.")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip dense embeddings and pooling. Useful for local/dev runs without GPU.",
    )
    args = parser.parse_args(argv)

    step_results = []
    try:
        for step in _make_steps(args.skip_embeddings):
            step_results.append(run_step(step, args.force))
        write_manifest(step_results, args.skip_embeddings)
    except Exception:
        if step_results:
            write_manifest(step_results, args.skip_embeddings)
        sys.exit(1)

    print(f"\n{'=' * 72}")
    print("All build steps completed successfully.")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
