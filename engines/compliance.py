def apply_compliance(calculated_data):
    per_100g = calculated_data["per_100g"]
    per_serving = calculated_data["per_serving"]
    allergens = calculated_data["allergens"]
    veg_type = calculated_data["veg_type"]
    ingredients = calculated_data["ingredients"]

    display = {}
    display_serving = {}

    # Standard rounding rules
    # Energy, Sodium -> nearest whole number
    # Macros -> 1 decimal place
    display["energy"]      = round(per_100g["energy"])
    display["protein"]     = round(per_100g["protein"], 1)
    display["carbs"]       = round(per_100g["carbs"], 1)
    display["sugar"]       = round(per_100g["sugar"], 1)
    display["added_sugar"] = round(per_100g["added_sugar"], 1)
    display["fat"]         = round(per_100g["fat"], 1)
    display["sodium"]      = round(per_100g["sodium"])

    # Trans fat threshold logic per serving
    display["trans_fat"] = "0" if per_serving["trans_fat"] < 0.2 else str(round(per_100g["trans_fat"], 1))

    # Sat fat threshold logic per serving
    display["sat_fat"] = "0" if per_serving["sat_fat"] < 0.1 else str(round(per_100g["sat_fat"], 1))

    # Per serving Values (same rounding rules)
    display_serving["energy"]      = round(per_serving["energy"])
    display_serving["protein"]     = round(per_serving["protein"], 1)
    display_serving["carbs"]       = round(per_serving["carbs"], 1)
    display_serving["sugar"]       = round(per_serving["sugar"], 1)
    display_serving["added_sugar"] = round(per_serving["added_sugar"], 1)
    display_serving["fat"]         = round(per_serving["fat"], 1)
    display_serving["sodium"]      = round(per_serving["sodium"])

    display_serving["sat_fat"]     = "0" if per_serving["sat_fat"] < 0.1 else str(round(per_serving["sat_fat"], 1))
    display_serving["trans_fat"]   = "0" if per_serving["trans_fat"] < 0.2 else str(round(per_serving["trans_fat"], 1))

    # Sodium warning (exceeds 600mg per 100g)
    sodium_warning = per_100g["sodium"] > 600

    # Allergen statement format
    if allergens:
        all_sorted = sorted([a.strip().title() for a in allergens if a and a != 'none'])
        allergen_statement = "Contains: " + ", ".join(all_sorted) if all_sorted else "No known allergens"
    else:
        allergen_statement = "No known allergens"

    # Assemble compliant structured payload for frontend and PDF builder
    return {
        "per_100g": display,
        "per_serving": display_serving,
        "sodium_warning": sodium_warning,
        "allergen_statement": allergen_statement,
        "veg_type": veg_type,
        "show_added_sugar": per_100g["added_sugar"] > 0,
        "ingredients": ingredients,
        "serving_size_g": calculated_data["serving_size_g"],
        "show_disclaimer": calculated_data["show_disclaimer"]
    }
