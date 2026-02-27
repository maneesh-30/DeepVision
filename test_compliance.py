import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.compliance import apply_compliance

def test_compliance():
    # Mock calculation engine output
    calculated_data = {
        "per_100g": {
            "energy": 360.66,
            "protein": 11.85,
            "carbs": 119.35,
            "sugar": 50.45,
            "added_sugar": 49.95,
            "fat": 1.75,
            "sat_fat": 0.35,
            "trans_fat": 0.05,
            "sodium": 2.5
        },
        "per_serving": {
            "energy": 108.2,
            "protein": 3.55,
            "carbs": 35.8,
            "sugar": 15.13,
            "added_sugar": 14.98,
            "fat": 0.52,
            "sat_fat": 0.105,
            "trans_fat": 0.015,
            "sodium": 0.75
        },
        "allergens": ["gluten", "milk"],
        "veg_type": "veg",
        "ingredients": [
            {"name": "wheat flour", "quantity": 100},
            {"name": "sugar", "quantity": 50}
        ],
        "serving_size_g": 30,
        "show_disclaimer": True
    }
    
    result = apply_compliance(calculated_data)
    
    # Check rounding
    assert result["per_100g"]["energy"] == 361, "Energy rounding failed"
    assert result["per_100g"]["protein"] == 11.8, f"Protein rounding failed, got {result['per_100g']['protein']}"
    
    # Check trans fat threshold (should be '0' string since per_serving is < 0.2)
    assert result["per_100g"]["trans_fat"] == "0", "Trans fat threshold rule failed"
    assert result["per_serving"]["trans_fat"] == "0", "Trans fat serving formula failed"
    
    # Check allergens
    assert result["allergen_statement"] == "Contains: Gluten, Milk", f"Allergen statement failed {result['allergen_statement']}"
    
    print("test_compliance passed successfully!")

if __name__ == "__main__":
    test_compliance()
