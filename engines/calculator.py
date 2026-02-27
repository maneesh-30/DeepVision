import sqlite3
import os

def get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'nutrition.db')

def calculate_nutrition(standardized_ingredients, final_yield_weight, serving_size_g):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    nutrients = ["energy", "protein", "carbs", "sugar", "added_sugar",
                 "fat", "sat_fat", "trans_fat", "sodium"]
    totals = {n: 0 for n in nutrients}
    allergens = set()
    veg_type = "veg"
    ingredient_list = []
    
    total_raw_weight = sum(item["quantity"] for item in standardized_ingredients)

    for item in standardized_ingredients:
        name = item["name"]
        qty  = item["quantity"]

        cursor.execute("SELECT * FROM ingredients WHERE name=?", (name,))
        row = cursor.fetchone()

        if row is None:
            # Try a partial match (LIKE) before hitting the external API
            cursor.execute("SELECT * FROM ingredients WHERE name LIKE ? LIMIT 1", (f"%{name}%",))
            row = cursor.fetchone()

        if row is None:
            # Fallback to external API
            from engines.external_api import search_ingredient_nutrition
            ext_data = search_ingredient_nutrition(name)
            
            if ext_data:
                # Insert the fetched data into the DB to cache it for the future
                cursor.execute('''
                    INSERT INTO ingredients (
                        name, energy, protein, carbs, sugar, added_sugar, fat, sat_fat, trans_fat, sodium, allergen, veg_type, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ext_data['name'], ext_data['energy'], ext_data['protein'], ext_data['carbs'], ext_data['sugar'],
                    ext_data['added_sugar'], ext_data['fat'], ext_data['sat_fat'], ext_data['trans_fat'],
                    ext_data['sodium'], ext_data['allergen'], ext_data['veg_type'], ext_data['source']
                ))
                conn.commit()
                
                # Create a row tuple equivalent to what the DB fetch would return
                row = (
                    ext_data['name'], ext_data['energy'], ext_data['protein'], ext_data['carbs'], ext_data['sugar'],
                    ext_data['added_sugar'], ext_data['fat'], ext_data['sat_fat'], ext_data['trans_fat'],
                    ext_data['sodium'], ext_data['allergen'], ext_data['veg_type'], ext_data['source']
                )
            else:
                conn.close()
                raise ValueError(f"Ingredient '{name}' not found locally or via external database.")

        cols = ["name", "energy", "protein", "carbs", "sugar", "added_sugar",
                "fat", "sat_fat", "trans_fat", "sodium", "allergen", "veg_type", "source"]
        data = dict(zip(cols, row))

        for n in nutrients:
            totals[n] += (data[n] * qty) / 100

        if data["allergen"] and data["allergen"] != "none":
            allergens.update(data["allergen"].split(","))

        if data["veg_type"] == "non-veg":
            veg_type = "non-veg"

        ingredient_list.append({"name": name, "quantity": qty})

    conn.close()

    # Determine normalization weight
    normalization_weight = final_yield_weight if final_yield_weight > 0 else total_raw_weight
    show_disclaimer = final_yield_weight <= 0

    # FSSAI requires values normalized per 100g of final yield matching weight
    per_100g = {n: (totals[n] / normalization_weight) * 100 for n in nutrients}

    # Calculate per serving
    per_serving = {n: (per_100g[n] * serving_size_g) / 100 for n in nutrients}

    # Sort ingredients descending by weight
    ingredient_list.sort(key=lambda x: x["quantity"], reverse=True)

    return {
        "per_100g": per_100g,
        "per_serving": per_serving,
        "allergens": list(allergens),
        "veg_type": veg_type,
        "ingredients": ingredient_list,
        "serving_size_g": serving_size_g,
        "show_disclaimer": show_disclaimer,
        "total_yield_weight": normalization_weight
    }
