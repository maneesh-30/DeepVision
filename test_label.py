import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.label_generator import generate_pdf

def test_label_generator():
    label_data = {
        "product_name": "Test Cookies",
        "servings_per_pack": 5,
        "serving_size_g": 30,
        "per_100g_display": {
            "energy": 361,
            "protein": 11.8,
            "carbs": 119.4,
            "sugar": 50.5,
            "added_sugar": 50.0,
            "fat": 1.8,
            "sat_fat": 0.4,
            "trans_fat": "0",
            "sodium": 3
        },
        "per_serving_display": {
            "energy": 108,
            "protein": 3.5,
            "carbs": 35.8,
            "sugar": 15.1,
            "added_sugar": 15.0,
            "fat": 0.5,
            "sat_fat": "0",
            "trans_fat": "0",
            "sodium": 1
        },
        "ingredients": [
            {"name": "wheat flour", "quantity": 100},
            {"name": "sugar", "quantity": 50}
        ],
        "allergen_statement": "Contains: Gluten",
        "veg_type": "veg",
        "fssai_license": "12345678901234",
        "show_disclaimer": True
    }
    
    output_path = "test_label.pdf"
    
    try:
        generated_path = generate_pdf(label_data, output_path)
        assert os.path.exists(generated_path), "PDF file was not created"
        print(f"test_label_generator passed, PDF created at {generated_path}")
        
        # Clean up
        os.remove(generated_path)
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_label_generator()
