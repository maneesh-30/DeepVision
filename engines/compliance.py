# ─── Allergen Keyword Mapping (FSSAI 8 Major Allergen Categories) ───
ALLERGEN_KEYWORDS = {
    "Gluten": [
        "wheat", "barley", "rye", "oats",
        "maida", "atta", "semolina", "sooji",
        "breadcrumb", "gluten"
    ],
    "Milk": [
        "milk", "dairy", "cream", "butter",
        "cheese", "ghee", "whey", "lactose",
        "curd", "yogurt", "casein", "paneer",
        "milk solids", "skimmed milk",
        "whole milk", "milk powder"
    ],
    "Nut": [
        "cashew", "almond", "walnut", "pistachio",
        "peanut", "groundnut", "hazelnut", "pecan",
        "macadamia", "pine nut", "brazil nut",
        "chestnut", "nut", "kaju", "badam"
    ],
    "Egg": [
        "egg", "albumin", "mayonnaise",
        "lecithin", "anda"
    ],
    "Soy": [
        "soy", "soya", "tofu", "tempeh",
        "edamame", "miso"
    ],
    "Fish": [
        "fish", "cod", "salmon", "tuna",
        "sardine", "anchovy", "mackerel",
        "hilsa", "rohu", "katla"
    ],
    "Shellfish": [
        "shrimp", "prawn", "crab", "lobster",
        "shellfish", "oyster", "mussel",
        "scallop", "jhinga"
    ],
    "Sesame": [
        "sesame", "til", "tahini",
        "gingelly", "sesame oil"
    ]
}


def detect_allergens(ingredient_name):
    """Detect allergens using case-insensitive substring matching."""
    detected = []
    name_lower = ingredient_name.lower()
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in name_lower:
                detected.append(allergen)
                break
    return detected


def apply_compliance(calculated_data):
    per_100g = calculated_data["per_100g"]
    per_serving = calculated_data["per_serving"]
    db_allergens = calculated_data["allergens"]
    veg_type = calculated_data["veg_type"]
    ingredients = calculated_data["ingredients"]

    # Collect all allergens from DB + keyword detection, deduplicated with preserved order
    all_allergens = list(db_allergens)
    for item in ingredients:
        all_allergens.extend(detect_allergens(item["name"]))

    # Remove duplicates while preserving order
    seen = set()
    allergens = []
    for a in all_allergens:
        a_clean = a.strip().title()
        if a_clean and a_clean != 'None' and a_clean not in seen:
            seen.add(a_clean)
            allergens.append(a_clean)

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

    # Allergen statement format (allergens list is already deduplicated and clean)
    if allergens:
        allergen_statement = "Contains: " + ", ".join(sorted(allergens))
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
