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

print("Preprocessing Successful, current state of DB:")

def profile_hadith_df(df):
    print("=== DataFrame Info ===")
    print(df.info())
    print("\n=== Summary Statistics ===")
    print(df.describe(include='all'))
    
    print("\n=== Missing Values ===")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "No missing values")
    
    print("\n=== Unique Values per Column ===")
    for col in df.columns:
        unique_count = df[col].nunique(dropna=False)
        print(f"{col}: {unique_count} unique values")
    
    # Specific profiling for 'Grade' since missing grades are important
    if 'Grade' in df.columns:
        print("\n=== Grade Distribution ===")
        grade_counts = df['Grade'].value_counts(dropna=False)
        print(grade_counts)
        if df['Grade'].isnull().any():
            print(f"\nMissing Grades: {df['Grade'].isnull().sum()} entries")

    # Optional: Check text length distributions
    for text_col in ['Arabic_Text', 'English_Text', 'Preprocessed_Arabic', 'Preprocessed_English']:
        if text_col in df.columns:
            lengths = df[text_col].astype(str).apply(len)
            print(f"\n{text_col} length stats:")
            print(lengths.describe())
    
    valid_grade_hadiths = pd.read_sql("SELECT * FROM HADITHS WHERE GRADE = ''",connection)
    for row in valid_grade_hadiths.itertuples():
        print(f"{row.English_Text}\nGrade: {row.Grade}")
    print(len(valid_grade_hadiths))


# Run profiling
profile_hadith_df(df)