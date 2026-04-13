import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hadiths.db')

def sample_hadiths(total_sample: int = 500) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM hadiths", conn)
    conn.close()
    df['group'] = df['Book'] + ' || ' + df['Chapter_Title_English'].fillna('Unknown')
    group_counts = df['group'].value_counts()
    group_proportions = group_counts / len(df)
    group_sample_sizes = (group_proportions * total_sample).round().astype(int)

    group_sample_sizes = group_sample_sizes.clip(lower=1)

    while group_sample_sizes.sum() > total_sample:
        group_sample_sizes.iloc[group_sample_sizes.argmax()] -= 1

    while group_sample_sizes.sum() < total_sample:
        group_sample_sizes.iloc[group_sample_sizes.argmin()] += 1

    sampled = []
    for group, size in group_sample_sizes.items():
        group_df = df[df['group'] == group]
        size = min(size, len(group_df))
        sampled.append(group_df.sample(n=size, random_state=42))

    result = pd.concat(sampled).reset_index(drop=True)
    result = result.drop(columns=['group'])
    return result

def main():
    sample = sample_hadiths(2000)

    print(f"Total sampled: {len(sample)}")
    print("\nDistribution by book:")
    print(sample['Book'].value_counts())
    print(f"\nUnique chapters represented: {sample['Chapter_Title_English'].nunique()}")
    print("\nChapters per book:")
    for book in sample['Book'].unique():
        chapters = sample[sample['Book'] == book]['Chapter_Title_English'].unique()
        print(f"\n{book} ({len(chapters)} chapters):")
        for chapter in sorted(chapters):
            print(f"  - {chapter}")
    conn = sqlite3.connect(DB_PATH)
    sample.to_sql("evaluation_hadiths", conn, if_exists="replace", index=False)
    conn.close()

    print("\nSaved to evaluation_hadiths table.")

if __name__ == "__main__":
    main()