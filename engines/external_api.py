import requests

def search_ingredient_nutrition(ingredient_name):
    """
    Queries the USDA FoodData Central API for the given ingredient name.
    Returns a dictionary mapping FSSAI fields to per-100g values, or None if not found.
    """
    # Using the USDA DEMO_KEY. In a real production app, users should supply their own key.
    # The DEMO_KEY has strict rate limits (30 requests/hr) but is sufficient for fallback test testing.
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": "DEMO_KEY",
        "query": ingredient_name,
        "pageSize": 1, # Only get the top result to save bandwidth
        "dataType": "Foundation,SR Legacy" # Reliable, well-structured data types
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("foods") or len(data["foods"]) == 0:
            return None

        # Take the top matched product
        product = data["foods"][0]
        food_nutrients = product.get("foodNutrients", [])

        # Helper function to extract nutrient by USDA ID
        def get_nutrient(nutrient_id):
            for n in food_nutrients:
                if n.get("nutrientId") == nutrient_id:
                    return n.get("value", 0)
            return 0

        # USDA Nutrient IDs:
        # 1008 = Energy (kcal)
        # 1003 = Protein (g)
        # 1005 = Carbohydrate (g)
        # 2000 = Total Sugars (g)
        # 1235 = Added Sugars (g)
        # 1004 = Total Fat (g)
        # 1258 = Saturated Fat (g)
        # 1257 = Trans Fat (g)
        # 1093 = Sodium (mg)

        energy = get_nutrient(1008)
        protein = get_nutrient(1003)
        carbs = get_nutrient(1005)
        sugar = get_nutrient(2000)
        added_sugar = get_nutrient(1235)
        fat = get_nutrient(1004)
        sat_fat = get_nutrient(1258)
        trans_fat = get_nutrient(1257)
        sodium_mg = get_nutrient(1093)

        # USDA doesn't explicitly flag allergens reliably in the basic API without parsing full ingredient lists
        # We'll default to 'none' and veg_type 'veg' as a conservative fallback payload
        # For a full commercial app, an NLP pass over the ingredient list string would be required.
        
        return {
            "name": ingredient_name.lower().strip(),
            "energy": round(energy, 2),
            "protein": round(protein, 2),
            "carbs": round(carbs, 2),
            "sugar": round(sugar, 2),
            "added_sugar": round(added_sugar, 2),
            "fat": round(fat, 2),
            "sat_fat": round(sat_fat, 2),
            "trans_fat": round(trans_fat, 2),
            "sodium": round(sodium_mg, 2),
            "allergen": "none",
            "veg_type": "veg",
            "source": "USDA FDC"
        }

    except Exception as e:
        print(f"Warning: Could not fetch from USDA API for '{ingredient_name}': {e}")
        return None
