import torch
import sys
from sentence_transformers import SentenceTransformer
import numpy as np
import sqlite3
import pandas as pd
import os

if not torch.cuda.is_available():
    print("ERROR: CUDA not available. This script requires a GPU.")
    print("To run on CPU, change device='cuda' to device='cpu' in line 18.")
    print("NOTE: Running on CPU is extremely slow and not recommended.")
    sys.exit(1)

device = 'cuda'
print(f"Using device: {device} ({torch.cuda.get_device_name(0)})")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "hadiths.db")

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