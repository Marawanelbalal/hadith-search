import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hadiths.db')

def profile_db():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths", conn)
    conn.close()

    print("=== Basic Info ===")
    print(df.info())

    print("\n=== Missing Values (Nulls) ===")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "No missing nulls (but check empty strings below)")

    # ---------------------------------------------------------
    # NEW: Empty Text Detection (Raw and Preprocessed)
    # ---------------------------------------------------------
    print("\n=== Empty Text Detection ===")
    
    # Create boolean masks for empty strings or purely whitespace
    empty_ar_raw = df['Arabic_Text'].isna() | (df['Arabic_Text'].astype(str).str.strip() == '')
    empty_en_raw = df['English_Text'].isna() | (df['English_Text'].astype(str).str.strip() == '')
    
    print("--- Raw Text ---")
    print(f"Hadiths missing Arabic text: {empty_ar_raw.sum()}")
    print(f"Hadiths missing English text: {empty_en_raw.sum()}")
    print(f"Hadiths missing BOTH (Overlap): {(empty_ar_raw & empty_en_raw).sum()}")

    # Check the preprocessed columns in case the stopword filter completely emptied them
    if 'Preprocessed_Arabic' in df.columns and 'Preprocessed_English' in df.columns:
        empty_ar_prep = df['Preprocessed_Arabic'].isna() | (df['Preprocessed_Arabic'].astype(str).str.strip() == '')
        empty_en_prep = df['Preprocessed_English'].isna() | (df['Preprocessed_English'].astype(str).str.strip() == '')
        
        print("\n--- Preprocessed Text (Post-Cleaning) ---")
        print(f"Empty Preprocessed Arabic (due to raw empty OR heavy filtering): {empty_ar_prep.sum()}")
        print(f"Empty Preprocessed English (due to raw empty OR heavy filtering): {empty_en_prep.sum()}")
    # ---------------------------------------------------------

    print("\n=== Unique Values per Column ===")
    for col in df.columns:
        print(f"{col}: {df[col].nunique(dropna=False)} unique values")

    print("\n=== Text Length Stats ===")
    for col in ['Arabic_Text', 'English_Text', 'Preprocessed_Arabic', 'Preprocessed_English']:
        if col in df.columns:
            lengths = df[col].astype(str).apply(len)
            print(f"\n{col}:")
            print(lengths.describe())

    if 'Grade' in df.columns:
        print("\n=== Grade Distribution ===")
        print(df['Grade'].value_counts(dropna=False).head(10)) # Added .head(10) so it doesn't spam your terminal

    if 'Normalized_Grade' in df.columns:
        print("\n=== Normalized Grade Distribution ===")
        print(df['Normalized_Grade'].value_counts(dropna=False))

    print("\n=== Hadiths per Book ===")
    print(df['Book'].value_counts())

    print("\n=== Summary ===")
    print(f"Total hadiths: {len(df)}")
    if 'Grade' in df.columns:
        print(f"Missing grades: {df['Grade'].isnull().sum() + (df['Grade'] == '').sum()}")
    if 'Normalized_Grade' in df.columns:
        print(f"Unknown normalized grades: {(df['Normalized_Grade'] == 'Unknown').sum()}")

if __name__ == "__main__":
    profile_db()