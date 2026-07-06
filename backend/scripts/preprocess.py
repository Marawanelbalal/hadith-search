from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk import pos_tag
from nltk.corpus import stopwords
import pyarabic.araby as araby
import re
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.utils.dediac import dediac_ar
from camel_tools.utils.normalize import normalize_alef_ar, normalize_alef_maksura_ar, normalize_teh_marbuta_ar
from scripts.loading import get_mle,get_english_lemmatizer

def get_wordnet_pos(tag): #this is needed to convert nltk pos to wordnet pos
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

def lemmatize_english(tokens,lemmatizer):
  pos_tags = pos_tag(tokens)
  lemmatized_tokens = [lemmatizer.lemmatize(word, get_wordnet_pos(tag)) for word,tag in pos_tags]
  return lemmatized_tokens

_stop_words_en = None

def get_stop_words_english():
    global _stop_words_en
    if _stop_words_en is None:
        extra = {
            "say", "narrate", "told", "informed", "reported", "transmitted", "heard",
            "narration", "authority",
            "correct", "weak",
            "bin", "ibn", "abu", "abi", "hadith"
        }
        _stop_words_en = set(stopwords.words('english')) | extra
    return _stop_words_en

def remove_stopwords_english(tokens:list[str])->list[str]:
    stop_words = get_stop_words_english()
    return [word for word in tokens if word not in stop_words and len(word) >= 3]

def preprocess_english(text):
    lemmatizer = get_english_lemmatizer()
    text = re.sub(r"[^a-zA-Z\s]", "", text.lower())
    tokens = word_tokenize(text)
    lemmatized_tokens = lemmatize_english(tokens,lemmatizer)
    final_tokens = remove_stopwords_english(lemmatized_tokens)
    return " ".join(final_tokens)       


def has_text(value):
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"nan", "none", "null"}


# Arabic pipeline
def normalize_arabic_stopwords(stopwords: set) -> set:
    result = set()
    for word in stopwords:
        word = dediac_ar(word)
        word = normalize_alef_ar(word)
        word = normalize_alef_maksura_ar(word)
        word = araby.normalize_hamza(word, method="tasheel")
        result.add(word)
    return result

_stop_words_ar = None

def get_stop_words_arabic() -> set:
    global _stop_words_ar
    if _stop_words_ar is None:
        raw = {
            "قال", "حدث", "روى",
            "حديث", "ضعيف", "قوى",
            "صلى", "سلم",
            "بن", "ابن", "ابي", "ابو", "اخبر"
        }
        _stop_words_ar = normalize_arabic_stopwords(raw)
    return _stop_words_ar

def normalize_token(token):
    token = dediac_ar(token)
    token = normalize_alef_ar(token)
    token = normalize_alef_maksura_ar(token)
    token = araby.normalize_hamza(token, method="tasheel")
    return token

def normalize_passage(passage):
    tokens = passage.split()
    tokens = [normalize_token(t) for t in tokens]
    return " ".join(tokens)

def process_arabic_tokens(disambiguated_tokens, original_tokens):
    extra_stopwords = get_stop_words_arabic()
    stop_pos = {'prep', 'conj', 'part', 'punc'}
    #remove prepositions conjunctions particles and punctuations, keep pronouns for now
    final_tokens = []

    for i, word in enumerate(disambiguated_tokens):
        if not word.analyses:
            raw = dediac_ar(original_tokens[i])
            if raw and len(raw) >= 2 and raw not in extra_stopwords:
                final_tokens.append(normalize_token(raw))
            continue

        best_analysis = word.analyses[0]
        lemma = best_analysis.analysis['lex']
        pos = best_analysis.analysis['pos']
        clean_lemma = normalize_token(lemma)
        if pos not in stop_pos and clean_lemma not in extra_stopwords and len(clean_lemma) >= 2:
            final_tokens.append(clean_lemma)

    return final_tokens

def normalize_arabic_text(text):
    text = re.sub(r"[^\u0600-\u06FF\s]", " ", text)
    text = normalize_alef_ar(text)
    text = normalize_alef_maksura_ar(text)
    text = normalize_teh_marbuta_ar(text)
    text = araby.normalize_hamza(text, method="tasheel")
    text = araby.strip_tatweel(text)  # tatweel is safe to remove, as it's only for looks
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_arabic(text):
    text = normalize_arabic_text(text)
    tokens = simple_word_tokenize(text)
    if not tokens:
        return ""
    mle = get_mle()
    disambiguated = mle.disambiguate(tokens)
    processed = process_arabic_tokens(disambiguated, tokens)  # pass original tokens as fallback
    return " ".join(processed)

def run():
    import os
    import sqlite3
    import pandas as pd
    import time
    from concurrent.futures import ThreadPoolExecutor
    start = time.perf_counter()

    DB_PATH = os.path.join(os.path.dirname(__file__),'..','data','hadiths.db')
    print(os.path.abspath(DB_PATH))
    connection = sqlite3.connect(DB_PATH)

    df = pd.read_sql("SELECT * FROM HADITHS;", connection)

    cursor = connection.cursor()

    preprocessing_columns = [
        "Preprocessed_English",
        "Preprocessed_Arabic",
        "Preprocessed_English_Isnad",
        "Preprocessed_Arabic_Isnad",
        "Preprocessed_English_Matn",
        "Preprocessed_Arabic_Matn",
    ]
    for column in preprocessing_columns:
        try:
            cursor.execute(f"ALTER TABLE hadiths ADD COLUMN {column} TEXT")
            connection.commit()
        except sqlite3.OperationalError:
            pass
    connection.commit()

    try:
        def _text(row, column):
            value = getattr(row, column, "")
            return value if value else ""

        print("Preprocessing full English text...")
        english_t0 = time.perf_counter()
        english_results = [preprocess_english(_text(r, "English_Text")) if _text(r, "English_Text") else "" for r in df.itertuples()]
        print(f"  Done in {time.perf_counter() - english_t0:.2f}s")

        print("Preprocessing full Arabic text...")
        arabic_t0 = time.perf_counter()
        arabic_texts = df["Arabic_Text"].tolist()
        try:
            with ThreadPoolExecutor(max_workers=4) as ex:
                arabic_results = list(ex.map(lambda t: preprocess_arabic(t) if t else "", arabic_texts))
            print(f"  Done in {time.perf_counter() - arabic_t0:.2f}s (parallel)")
        except Exception:
            print("  ThreadPoolExecutor failed, falling back to sequential...")
            arabic_results = [preprocess_arabic(t) if t else "" for t in arabic_texts]
            print(f"  Done in {time.perf_counter() - arabic_t0:.2f}s (sequential)")

        print("Preprocessing English isnad text...")
        isnad_en_t0 = time.perf_counter()
        isnad_en_results = [preprocess_english(_text(r, "English_Isnad")) if _text(r, "English_Isnad") else "" for r in df.itertuples()]
        print(f"  Done in {time.perf_counter() - isnad_en_t0:.2f}s")

        print("Preprocessing Arabic isnad text...")
        isnad_ar_t0 = time.perf_counter()
        isnad_ar_texts = df["Arabic_Isnad"].tolist()
        try:
            with ThreadPoolExecutor(max_workers=4) as ex:
                isnad_ar_results = list(ex.map(lambda t: preprocess_arabic(t) if t else "", isnad_ar_texts))
            print(f"  Done in {time.perf_counter() - isnad_ar_t0:.2f}s (parallel)")
        except Exception:
            print("  ThreadPoolExecutor failed, falling back to sequential...")
            isnad_ar_results = [preprocess_arabic(t) if t else "" for t in isnad_ar_texts]
            print(f"  Done in {time.perf_counter() - isnad_ar_t0:.2f}s (sequential)")

        print("Preprocessing English matn text...")
        matn_en_t0 = time.perf_counter()
        matn_en_results = [preprocess_english(_text(r, "English_Matn")) if _text(r, "English_Matn") else "" for r in df.itertuples()]
        print(f"  Done in {time.perf_counter() - matn_en_t0:.2f}s")

        print("Preprocessing Arabic matn text...")
        matn_ar_t0 = time.perf_counter()
        matn_ar_texts = df["Arabic_Matn"].tolist()
        try:
            with ThreadPoolExecutor(max_workers=4) as ex:
                matn_ar_results = list(ex.map(lambda t: preprocess_arabic(t) if t else "", matn_ar_texts))
            print(f"  Done in {time.perf_counter() - matn_ar_t0:.2f}s (parallel)")
        except Exception:
            print("  ThreadPoolExecutor failed, falling back to sequential...")
            matn_ar_results = [preprocess_arabic(t) if t else "" for t in matn_ar_texts]
            print(f"  Done in {time.perf_counter() - matn_ar_t0:.2f}s (sequential)")

        empty_matn_en = [int(r.id) for r, value in zip(df.itertuples(), matn_en_results) if not has_text(value)]
        empty_matn_ar = [int(r.id) for r, value in zip(df.itertuples(), matn_ar_results) if not has_text(value)]
        if empty_matn_en or empty_matn_ar:
            details = []
            if empty_matn_en:
                details.append(f"English matn preprocessing produced empty strings for {len(empty_matn_en)} ids: {empty_matn_en[:20]}")
            if empty_matn_ar:
                details.append(f"Arabic matn preprocessing produced empty strings for {len(empty_matn_ar)} ids: {empty_matn_ar[:20]}")
            raise ValueError("; ".join(details))

        updates = [(en, ar, ien, iar, men, mar, r.id) for r, en, ar, ien, iar, men, mar in zip(
            df.itertuples(),
            english_results,
            arabic_results,
            isnad_en_results,
            isnad_ar_results,
            matn_en_results,
            matn_ar_results,
        )]
        cursor.executemany("""
            UPDATE hadiths
            SET Preprocessed_English = ?, Preprocessed_Arabic = ?,
                Preprocessed_English_Isnad = ?, Preprocessed_Arabic_Isnad = ?,
                Preprocessed_English_Matn = ?, Preprocessed_Arabic_Matn = ?
            WHERE id = ?
        """, updates)
        connection.commit()

        print(f"\nPreprocessing Successful. Total time: {time.perf_counter() - start:.2f}s")
    finally:
        connection.close()
    end = time.perf_counter()
    print(f"Total Time Taken: {end-start}s")

if __name__ == "__main__":
    run()
