from functools import lru_cache
from scripts.search import get_arabic_inverted_index, get_english_inverted_index, get_document_lengths
from scripts.preprocess import get_mle, get_english_lemmatizer

@lru_cache()
def get_english_index():
    return get_english_inverted_index()

@lru_cache()
def get_arabic_index():
    return get_arabic_inverted_index()

@lru_cache()
def get_doc_lengths():
    return get_document_lengths()

@lru_cache()
def get_mle_model():
    return get_mle()

@lru_cache()
def get_lemmatizer():
    return get_english_lemmatizer()