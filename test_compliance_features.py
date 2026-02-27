import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.compliance_features import validate_health_claims, suggest_sodium_fix

def test_sodium():
    print("--- Testing Sodium Fix ---")
    ingredients = [{"name": "salt", "quantity": 4}]
    # 4g salt (38758mg per 100g -> ~387.58mg per 1g -> 1550.32mg total)
    # per 100g in 88g yield = 1550.32 / 88 * 100 = 1761.7mg per 100g
    per_100g_sodium = 1761.7
    fix = suggest_sodium_fix(ingredients, per_100g_sodium, 88)
    print("Contributors:", fix["contributors"])
    print("Fixes:", fix["fixes"])
    print("New Sodium:", fix["new_sodium_per_100g"], "Fixed:", fix["is_fully_fixed"])
    assert fix["is_fully_fixed"]
    print("Sodium fix calculation passed.\n")

def test_health_claims():
    print("--- Testing Health Claims ---")
    per_100g = {
        "fat": 2.5,
        "sat_fat": 1.0,
        "sodium": 110,
        "energy": 35,
        "protein": 11,
        "added_sugar": 0,
        "sugar": 4.5,
        "trans_fat": 0.1
    }
    claims = validate_health_claims(per_100g)
    qualified = [c["claim"] for c in claims["qualified"]]
    print("Qualified claims:", qualified)
    assert "Low Fat" in qualified
    assert "High Protein" in qualified
    assert "Low Sodium" in qualified
    assert "Low Calorie" in qualified
    print("Claims validation passed.")

if __name__ == "__main__":
    test_sodium()
    test_health_claims()
