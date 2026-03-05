import sqlite3
import os
import pandas as pd
hadith_data = load_dataset("meeAtif/hadith_datasets", split='train')
df = pd.DataFrame(hadith_data)
current_file_path = os.path.join(os.path.dirname(__file__), 'hadiths.db')
connection = sqlite3.connect(f"{current_file_path}../data/hadiths.db")
cursor = connection.cursor()
hadiths = cursor.execute("SELECT * FROM HADITHS")
print(hadiths)
connection.close()