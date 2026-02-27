import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.external_api import search_ingredient_nutrition
from engines.calculator import calculate_nutrition

def test_external_api():
    # Test direct lookup
    print("Testing direct Open Food Facts API lookup for 'quinoa'...")
    data = search_ingredient_nutrition("quinoa")
    assert data is not None, "Failed to fetch quinoa"
    assert data["name"] == "quinoa", "Name mismatch"
    print(f"Success! Data mapped: {data}")
    
    # Test integrated flow
    print("\nTesting Calculator Integration (should lookup and insert into DB)...")
    standardized = [
        {"name": "quinoa", "quantity": 100},
        {"name": "chia seeds", "quantity": 50}
    ]
    
    calc_result = calculate_nutrition(standardized, 150, 30)
    print("\nSuccess! Integrated Calculation Result:")
    print(f"Per 100g Energy: {calc_result['per_100g']['energy']} kcal")
    print(f"Allergens found: {calc_result['allergens']}")

if __name__ == "__main__":
    test_external_api()
