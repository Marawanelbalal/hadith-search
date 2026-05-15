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

if __name__ == "__main__":
    import os
    import sqlite3
    import pandas as pd
    import time
    start = time.perf_counter()

    DB_PATH = os.path.join(os.path.dirname(__file__),'..','data','hadiths.db')
    print(os.path.abspath(DB_PATH))
    connection = sqlite3.connect(DB_PATH)

    df = pd.read_sql("SELECT * FROM HADITHS;", connection)
    
    cursor = connection.cursor()

    try:
        cursor.execute("ALTER TABLE hadiths ADD COLUMN Preprocessed_English TEXT")
        cursor.execute("ALTER TABLE hadiths ADD COLUMN Preprocessed_Arabic TEXT")
        connection.commit()
    except sqlite3.OperationalError:
        pass  # in case of running the script more than once and the columns already exist
    connection.commit()
    try:
        for row in df.itertuples():
            cursor.execute("""
                UPDATE hadiths 
                SET Preprocessed_English = ?, Preprocessed_Arabic = ?
                WHERE id = ?
            """, (preprocess_english(row.English_Text), 
                preprocess_arabic(row.Arabic_Text), 
                row.id))
        print("Preprocessing Successful, current state of DB:")
        df = pd.read_sql("SELECT * FROM HADITHS LIMIT 20", connection)
        for index,row in df.iterrows():
            print(f"Hadith: {index}\n")
            print(f"English Text: {row['English_Text']}\n")
            print(f"Arabic Text: {row['Arabic_Text']}\n")
            print(f"English Text After Preprocessing: {row['Preprocessed_English']}\n")
            print(f"Arabic Text After Preprocessing: {row['Preprocessed_Arabic']}\n")
            print("\n\n")
        print(df.info())
        connection.commit()
        print("Successful")
    finally:
        connection.close()
    end = time.perf_counter()
    print(f"Total Time Taken: {end-start}s")