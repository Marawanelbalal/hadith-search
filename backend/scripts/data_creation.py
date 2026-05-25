import sqlite3
import os
import pandas as pd
from datasets import load_dataset

def run():
    hadith_data = load_dataset("meeAtif/hadith_datasets", split='train')
    df = pd.DataFrame(hadith_data)
    DB_DIR = os.path.join(os.path.dirname(__file__),'..','data','hadiths.db')
    connection = sqlite3.connect(DB_DIR)
    df.to_sql("HADITHS",connection,if_exists="replace", index = True, index_label = 'id')
    print(pd.read_sql("SELECT COUNT(*) FROM HADITHS", connection))
    connection.close()

if __name__ == "__main__":
    run()