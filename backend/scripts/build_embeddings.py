from sentence_transformers import SentenceTransformer
import numpy as np
import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "hadiths.db")

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT id, English_Text, Arabic_Text FROM hadiths", conn)
conn.close()

print(f"Loaded {len(df)} hadiths")

# English
en_model = SentenceTransformer("all-mpnet-base-v2")
en_embeddings = en_model.encode(df["English_Text"].tolist(), show_progress_bar=True)
np.save(os.path.join(BASE_DIR, "..", "data", "english_embeddings.npy"), en_embeddings)
print("English embeddings saved")

# Arabic
ar_model = SentenceTransformer("Omartificial-Intelligence-Space/Arabic-Triplet-Matryoshka-V2")
ar_embeddings = ar_model.encode(df["Arabic_Text"].tolist(), show_progress_bar=True)
np.save(os.path.join(BASE_DIR, "..", "data", "arabic_embeddings.npy"), ar_embeddings)
print("Arabic embeddings saved")

# Save the IDs in order so you can map embeddings back to hadiths
np.save(os.path.join(BASE_DIR, "..", "data", "hadith_ids.npy"), df["id"].values)
print("Done")