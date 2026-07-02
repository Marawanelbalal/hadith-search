import os
import pickle
import numpy as np
import pandas as pd
from functools import lru_cache
from transformers import AutoModelForSequenceClassification, AutoTokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

EN_II_PATH  = os.path.join(DATA_DIR, "english_inverted_index.pkl")
AR_II_PATH  = os.path.join(DATA_DIR, "arabic_inverted_index.pkl")
DOC_LEN_PATH = os.path.join(DATA_DIR, "document_lengths.pkl")
EN_EMB_PATH  = os.path.join(DATA_DIR, "english_embeddings.npy")
AR_EMB_PATH  = os.path.join(DATA_DIR, "arabic_embeddings.npy")
HADITH_IDS_PATH = os.path.join(DATA_DIR, "hadith_ids.npy")

@lru_cache()
def get_english_inverted_index():
    with open(EN_II_PATH, "rb") as f:
        return pickle.load(f)

@lru_cache()
def get_arabic_inverted_index():
    with open(AR_II_PATH, "rb") as f:
        return pickle.load(f)

@lru_cache()
def get_document_lengths():
    with open(DOC_LEN_PATH, "rb") as f:
        return pickle.load(f)

def _normalize(embeddings: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / (norms + eps)

@lru_cache()
def get_english_embeddings():
    return _normalize(np.load(EN_EMB_PATH))

@lru_cache()
def get_arabic_embeddings():
    return _normalize(np.load(AR_EMB_PATH))

@lru_cache()
def get_hadith_ids() -> np.ndarray:
    return np.load(HADITH_IDS_PATH)

@lru_cache()
def get_hadiths_df() -> pd.DataFrame:
    db_path = os.path.join(DATA_DIR, "hadiths.db")
    conn = __import__("sqlite3").connect(db_path)
    df = pd.read_sql("SELECT * FROM hadiths", conn)
    conn.close()
    return df.set_index("id")

@lru_cache()
def get_mle():
    from camel_tools.disambig.mle import MLEDisambiguator
    return MLEDisambiguator.pretrained("calima-msa-r13")

@lru_cache()
def get_english_lemmatizer():
    from nltk.stem import WordNetLemmatizer
    return WordNetLemmatizer()

@lru_cache()
def get_model():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("intfloat/multilingual-e5-large")

    adapter_path = os.getenv("FINETUNED_ADAPTER_PATH", "")
    if adapter_path and os.path.exists(adapter_path):
        from peft import PeftModel
        model[0].auto_model = PeftModel.from_pretrained(
            model[0].auto_model, adapter_path,
        )
        model[0].auto_model = model[0].auto_model.merge_and_unload()

    return model