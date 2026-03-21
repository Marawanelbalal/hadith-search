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

    print("\n=== Missing Values ===")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "No missing values")

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
        print(df['Grade'].value_counts(dropna=False))

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