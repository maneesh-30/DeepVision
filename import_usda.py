import os
import requests
import zipfile
import pandas as pd
import sqlite3
import urllib.request
import time

url = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_csv_2025-12-18.zip"
zip_path = "usda_data.zip"

print(f"Downloading USDA zip file from {url}...")
start_time = time.time()
try:
    urllib.request.urlretrieve(url, zip_path)
except Exception as e:
    # Try another known recent one if 2025-12-18 fails
    print(f"Failed to download: {e}")
    print("Trying alternative Foundation Foods subset...")
    url = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2025-12-18.zip"
    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e2:
        print(f"Failed to download alternative: {e2}")
        exit(1)

print(f"Downloaded in {time.time() - start_time:.2f} seconds. Unzipping...")
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall("usda_data")

# Find the csv files
folder = "usda_data"
food_csv = None
nutrient_csv = None
for root, dirs, files in os.walk(folder):
    for f in files:
        if f == "food.csv": food_csv = os.path.join(root, f)
        if f == "food_nutrient.csv": nutrient_csv = os.path.join(root, f)

if not food_csv or not nutrient_csv:
    print("Could not find food.csv or food_nutrient.csv in the extracted files.")
    exit(1)

print(f"Loading {food_csv}...")
df_food = pd.read_csv(food_csv, usecols=['fdc_id', 'description'], low_memory=False)

print(f"Loading {nutrient_csv}...")
# Nutrients:
# 1008: Energy (kcal)
# 1003: Protein (g)
# 1004: Fat (g)
# 1005: Carbs (g)
# 1093: Sodium (mg)
# 2000: Total Sugars (g)
# 1235: Added Sugars (g)
# 1258: Saturated Fat (g)
# 1257: Trans Fat (g)
relevant_nutrients = [1008, 1003, 1004, 1005, 1093, 2000, 1235, 1258, 1257]

# Read in chunks to avoid blowing up memory if the branded dataset is huge
print("Reading nutrient data in chunks...")
chunk_list = []
for chunk in pd.read_csv(nutrient_csv, usecols=['fdc_id', 'nutrient_id', 'amount'], chunksize=1000000, low_memory=False):
    filtered_chunk = chunk[chunk['nutrient_id'].isin(relevant_nutrients)]
    chunk_list.append(filtered_chunk)

df_nutr = pd.concat(chunk_list)

print("Pivoting data...")
df_pivot = df_nutr.pivot_table(index='fdc_id', columns='nutrient_id', values='amount', aggfunc='first').fillna(0)
df_pivot.reset_index(inplace=True)

print("Merging with foods...")
df_final = pd.merge(df_food, df_pivot, on='fdc_id', how='inner')

rename_map = {
    1008: 'energy',
    1003: 'protein',
    1005: 'carbs',
    2000: 'sugar',
    1235: 'added_sugar',
    1004: 'fat',
    1258: 'sat_fat',
    1257: 'trans_fat',
    1093: 'sodium'
}
df_final.rename(columns=rename_map, inplace=True)

# Add missing columns with 0
for col in rename_map.values():
    if col not in df_final.columns:
        df_final[col] = 0.0

# Process fields
df_final['name'] = df_final['description'].astype(str).str.lower().str.strip()
df_final['allergen'] = 'none' # Need NLP or advanced parse for real allergens, default 'none'
df_final['veg_type'] = 'veg' # Default 'veg'
df_final['source'] = 'USDA'

df_insert = df_final[['name', 'energy', 'protein', 'carbs', 'sugar', 'added_sugar', 'fat', 'sat_fat', 'trans_fat', 'sodium', 'allergen', 'veg_type', 'source']]

# Drop duplicates if multiple foods have exact same name
df_insert = df_insert.drop_duplicates(subset=['name'], keep='first')
df_insert = df_insert.dropna(subset=['name'])

print(f"Preparing to insert {len(df_insert)} ingredients into SQLite...")

# Insert into database
db_path = os.path.join(os.path.dirname(__file__), 'database', 'nutrition.db')
conn = sqlite3.connect(db_path)

# Insert ignoring duplicates (which might exist from IFCT 2017)
# We can use pd.to_sql via a temp table
df_insert.to_sql('usda_temp', conn, if_exists='replace', index=False)

cursor = conn.cursor()
cursor.execute('''
    INSERT OR IGNORE INTO ingredients (name, energy, protein, carbs, sugar, added_sugar, fat, sat_fat, trans_fat, sodium, allergen, veg_type, source)
    SELECT name, energy, protein, carbs, sugar, added_sugar, fat, sat_fat, trans_fat, sodium, allergen, veg_type, source FROM usda_temp
''')

conn.commit()
cursor.execute('DROP TABLE usda_temp')
conn.close()

print("USDA database imported successfully!")

# cleanup zip and extracted files
try:
    import shutil
    shutil.rmtree("usda_data")
    os.remove("usda_data.zip")
    print("Cleaned up downloaded files.")
except:
    pass
