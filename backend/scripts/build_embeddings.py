import torch
import sys
from sentence_transformers import SentenceTransformer
import numpy as np
import sqlite3
import pandas as pd
import os

def run():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "..", "data", "hadiths.db")

    if not torch.cuda.is_available():
        print("CUDA is not available.")
        choice = input("Proceed with CPU (extremely slow)? [y/N]: ").strip().lower()
        if choice != 'y':
            print("Aborted.")
            return
        device = 'cpu'
        print("Using CPU (this will be very slow)")
    else:
        device = 'cuda'
        print(f"Using device: {device} ({torch.cuda.get_device_name(0)})")

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT id, English_Text, Arabic_Text FROM hadiths", conn)
    conn.close()

    print(f"Loaded {len(df)} hadiths")

    model = SentenceTransformer("intfloat/multilingual-e5-large", device=device)

    print("Generating English embeddings...")
    en_embeddings = model.encode(df["English_Text"].tolist(), batch_size=32, show_progress_bar=True)
    np.save(os.path.join(BASE_DIR, "..", "data", "english_embeddings.npy"), en_embeddings)
    print("English embeddings saved")

    print("Generating Arabic embeddings...")
    ar_embeddings = model.encode(df["Arabic_Text"].tolist(), batch_size=32, show_progress_bar=True)
    np.save(os.path.join(BASE_DIR, "..", "data", "arabic_embeddings.npy"), ar_embeddings)
    print("Arabic embeddings saved")

    np.save(os.path.join(BASE_DIR, "..", "data", "hadith_ids.npy"), df["id"].values)
    print("Done")

if __name__ == "__main__":
    run()