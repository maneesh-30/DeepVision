import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.calculator import calculate_nutrition

def test_calculator():
    # Provide an ingredient that exists in the seeded DB
    standardized_ingredients = [
        {"name": "wheat flour", "quantity": 100}, # 100g of wheat flour
        {"name": "sugar", "quantity": 50}         # 50g of sugar
    ]
    
    # Wheat flour (per 100g): Energy 341, Protein 11.8, Carbs 69.4, Sugar 1
    # Sugar (per 100g): Energy 400, Protein 0, Carbs 99.9, Sugar 99.9
    
    # Expected total for 150g raw:
    # Energy: 341 + (400 * 0.5) = 341 + 200 = 541 kcal
    # Protein: 11.8 + 0 = 11.8 g
    # Carbs: 69.4 + (99.9 * 0.5) = 69.4 + 49.95 = 119.35 g
    
    # calculate_nutrition normalizes to per 100g
    # 541 / 1.5 = 360.66 kcal / 100g
    
    final_yield_weight = 0 # Use raw weight (150g)
    serving_size_g = 30
    
    try:
        result = calculate_nutrition(standardized_ingredients, final_yield_weight, serving_size_g)
        
        # Check normalization (should be roughly 360.66)
        energy_100g = result["per_100g"]["energy"]
        assert 360 < energy_100g < 361, f"Expected ~360.66, got {energy_100g}"
        
        # Check allergens (wheat flour has gluten)
        assert "gluten" in result["allergens"], "Expected 'gluten' in allergens"
        
        print("test_calculator passed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calculator()
