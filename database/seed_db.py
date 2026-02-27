import sqlite3
import os

def seed_db():
    db_path = os.path.join(os.path.dirname(__file__), 'nutrition.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop the table if it exists so we can run this script multiple times safely
    cursor.execute('DROP TABLE IF EXISTS ingredients')

    # Create the ingredients table with FSSAI-compliant structure
    cursor.execute('''
    CREATE TABLE ingredients (
        name          TEXT PRIMARY KEY NOT NULL,
        energy        REAL NOT NULL DEFAULT 0,
        protein       REAL NOT NULL DEFAULT 0,
        carbs         REAL NOT NULL DEFAULT 0,
        sugar         REAL NOT NULL DEFAULT 0,
        added_sugar   REAL NOT NULL DEFAULT 0,
        fat           REAL NOT NULL DEFAULT 0,
        sat_fat       REAL NOT NULL DEFAULT 0,
        trans_fat     REAL NOT NULL DEFAULT 0,
        sodium        REAL NOT NULL DEFAULT 0,
        allergen      TEXT NOT NULL DEFAULT 'none',
        veg_type      TEXT NOT NULL DEFAULT 'veg',
        source        TEXT NOT NULL DEFAULT 'IFCT 2017'
    )
    ''')

    # Create an index for quick lookups by ingredient name
    cursor.execute('CREATE INDEX idx_ingredient_name ON ingredients(name)')

    # IFCT 2017 seed data (per 100g)
    ingredients = [
        ('rice', 346, 6.8, 78.2, 0, 0, 0.5, 0.2, 0, 4, 'none', 'veg', 'IFCT 2017'),
        ('wheat flour', 341, 11.8, 69.4, 1, 0, 1.7, 0.3, 0, 2, 'gluten', 'veg', 'IFCT 2017'),
        ('maida', 348, 10.3, 74.2, 1.5, 0, 0.9, 0.1, 0, 2, 'gluten', 'veg', 'IFCT 2017'),
        ('besan', 347, 22.5, 57.9, 10.9, 0, 5.6, 0.5, 0, 37, 'none', 'veg', 'IFCT 2017'),
        ('gram flour', 347, 22.5, 57.9, 10.9, 0, 5.6, 0.5, 0, 37, 'none', 'veg', 'IFCT 2017'), # duplicate for easier lookup
        ('sugar', 400, 0, 99.9, 99.9, 99.9, 0, 0, 0, 0, 'none', 'veg', 'IFCT 2017'),
        ('jaggery', 383, 0.4, 98.0, 97, 97, 0.1, 0, 0, 30, 'none', 'veg', 'IFCT 2017'),
        ('honey', 304, 0.3, 82.1, 82.1, 82.1, 0, 0, 0, 4, 'none', 'veg', 'IFCT 2017'),
        ('milk', 61, 3.2, 4.4, 4.4, 0, 3.4, 2.2, 0.1, 44, 'milk', 'veg', 'IFCT 2017'),
        ('curd', 60, 3.1, 4.0, 4.0, 0, 3.3, 2.1, 0, 50, 'milk', 'veg', 'IFCT 2017'),
        ('dahi', 60, 3.1, 4.0, 4.0, 0, 3.3, 2.1, 0, 50, 'milk', 'veg', 'IFCT 2017'),
        ('paneer', 265, 18.3, 1.2, 0, 0, 20.8, 13.2, 0.4, 28, 'milk', 'veg', 'IFCT 2017'),
        ('butter', 729, 0.6, 0.1, 0, 0, 81, 51.4, 3.0, 11, 'milk', 'veg', 'IFCT 2017'),
        ('ghee', 900, 0, 0, 0, 0, 99.9, 62, 0.5, 0, 'milk', 'veg', 'IFCT 2017'),
        ('sunflower oil', 884, 0, 0, 0, 0, 100, 10, 0.1, 0, 'none', 'veg', 'IFCT 2017'),
        ('coconut oil', 862, 0, 0, 0, 0, 100, 86.5, 0.2, 0, 'none', 'veg', 'IFCT 2017'),
        ('egg', 173, 13.3, 0.7, 0.4, 0, 13.2, 3.8, 0, 124, 'egg', 'non-veg', 'IFCT 2017'),
        ('chicken', 109, 18.6, 0, 0, 0, 3.6, 1.0, 0, 70, 'none', 'non-veg', 'IFCT 2017'),
        ('salt', 0, 0, 0, 0, 0, 0, 0, 0, 38758, 'none', 'veg', 'IFCT 2017'),
        ('onion', 40, 1.2, 9.0, 4.2, 0, 0.1, 0, 0, 4, 'none', 'veg', 'IFCT 2017'),
        ('tomato', 18, 0.9, 3.9, 2.6, 0, 0.2, 0, 0, 5, 'none', 'veg', 'IFCT 2017'),
        ('potato', 77, 2.0, 17.0, 0.8, 0, 0.1, 0, 0, 6, 'none', 'veg', 'IFCT 2017'),
        ('spinach', 23, 2.0, 3.6, 0.4, 0, 0.4, 0.1, 0, 79, 'none', 'veg', 'IFCT 2017'),
        ('vanilla extract', 288, 0.1, 12.6, 12.6, 0, 0.1, 0, 0, 9, 'none', 'veg', 'IFCT 2017'),
        ('chickpeas', 360, 17.1, 60.5, 10.7, 0, 5.3, 0.5, 0, 24, 'none', 'veg', 'IFCT 2017'),
        ('red lentils', 340, 25.1, 59.0, 2, 0, 0.9, 0.1, 0, 8, 'none', 'veg', 'IFCT 2017'),
        ('peanuts', 567, 25.8, 16.1, 4, 0, 49.2, 6.8, 0, 18, 'peanuts', 'veg', 'IFCT 2017'),
        ('cashew', 553, 18.2, 30.2, 5.9, 0, 43.9, 7.8, 0.2, 12, 'tree-nuts', 'veg', 'IFCT 2017'),
        ('almond', 579, 21.2, 21.7, 3.9, 0, 49.9, 3.8, 0.1, 1, 'tree-nuts', 'veg', 'IFCT 2017'),
        ('cumin', 375, 17.8, 44.2, 2.3, 0, 22.3, 1.5, 0, 168, 'none', 'veg', 'IFCT 2017'),
        ('turmeric', 354, 7.8, 64.9, 3.2, 0, 9.9, 3.1, 0, 38, 'none', 'veg', 'IFCT 2017'),
        ('coriander', 298, 12.4, 54.9, 0, 0, 17.8, 0.9, 0, 35, 'none', 'veg', 'IFCT 2017'),
        ('chilli', 314, 15.0, 49.7, 0, 0, 12.4, 1.8, 0, 30, 'none', 'veg', 'IFCT 2017'),
        ('black pepper', 251, 10.4, 64.0, 0.6, 0, 3.3, 1.4, 0, 20, 'none', 'veg', 'IFCT 2017')
    ]

    cursor.executemany('''
    INSERT INTO ingredients (
        name, energy, protein, carbs, sugar, added_sugar, fat, sat_fat, trans_fat, sodium, allergen, veg_type, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ingredients)

    conn.commit()
    conn.close()
    print(f"Database seeded successfully at {db_path} with {len(ingredients)} ingredients.")

if __name__ == '__main__':
    seed_db()
