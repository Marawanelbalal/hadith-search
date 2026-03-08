from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from nltk.corpus import stopwords
import pyarabic.araby as araby
import qalsadi.lemmatizer

import re

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


def remove_stopwords_english(tokens):
  stop_words = set(stopwords.words('english'))
  tokens_without_stopwords = [word for word in tokens if word not in stop_words]
  return tokens_without_stopwords

def preprocess_english(text,lemmatizer):
  text = re.sub(r'[^\w\s]',"",text.lower())
  tokens = word_tokenize(text)
  lemmatized_tokens = lemmatize_english(tokens,lemmatizer)
  final_tokens = remove_stopwords_english(lemmatized_tokens)
  return " ".join(final_tokens)

# Arabic pipeline

def normalize_arabic(text):
    text = araby.strip_diacritics(text)
    text = araby.strip_tatweel(text)
    text = araby.normalize_hamza(text, method="tasheel")
    return text

def lemmatize_arabic(text,lemmatizer):
    lemmas_with_pos = lemmatizer.lemmatize_text(text, return_pos=True)
    return lemmas_with_pos

def remove_stopwords_arabic(lemmas_with_pos):
    lemmas_with_pos = [(word,pos) for word,pos in lemmas_with_pos if pos != 'stopword']
    lemmas = [word for word,_ in lemmas_with_pos]
    return lemmas

def preprocess_arabic(text,lemmatizer):
    text = normalize_arabic(text)
    text_lemmas_with_pos = lemmatize_arabic(text,lemmatizer)
    final_tokens = remove_stopwords_arabic(text_lemmas_with_pos)
    return " ".join(final_tokens)

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
    arabicLemmatizer = qalsadi.lemmatizer.Lemmatizer()
    englishLemmatizer = WordNetLemmatizer()

    for row in df.itertuples():
        cursor.execute("""
            UPDATE hadiths 
            SET Preprocessed_English = ?, Preprocessed_Arabic = ?
            WHERE id = ?
        """, (preprocess_english(row.English_Text,englishLemmatizer), 
            preprocess_arabic(row.Arabic_Text,arabicLemmatizer), 
            row.id))
    print("Preprocessing Successful, current state of DB:")
    df = pd.read_sql("SELECT * FROM HADITHS LIMIT 300;", connection)
    for index,row in df.iterrows():
        print(f"Hadith: {index}\n")
        print(f"English Text: {row['English_Text']}\n")
        print(f"Arabic Text: {row['Arabic_Text']}\n")
        print(f"English Text After Preprocessing: {row['preprocessed_english']}\n")
        print(f"Arabic Text After Preprocessing: {row['preprocessed_arabic']}\n")
        print("\n\n")
    print(df)
    connection.commit()
    connection.close()
    end = time.perf_counter()
    print(f"Total Time Taken: {end-start}s")