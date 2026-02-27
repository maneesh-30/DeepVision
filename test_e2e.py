import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.parser import standardize_units
from engines.calculator import calculate_nutrition
from engines.compliance import apply_compliance
from engines.label_generator import generate_pdf

def test_end_to_end():
    # Phase 2 logic mock (skip LLM for test stability)
    parsed_json = [
        {"name": "wheat flour", "quantity": "100", "unit": "g"},
        {"name": "sugar", "quantity": "50", "unit": "g"}
    ]
    standardized_ingredients = standardize_units(parsed_json)
    
    # Phase 3 logic
    final_yield_weight = 130 # e.g. some moisture lost
    serving_size_g = 30
    calc_data = calculate_nutrition(standardized_ingredients, final_yield_weight, serving_size_g)
    
    # Phase 4 logic
    compliant_data = apply_compliance(calc_data)
    
    # Merge required form data normally handled by app.py
    compliant_data.update({
        "product_name": "E2E Test Biscuits",
        "serving_size_g": serving_size_g,
        "servings_per_pack": 5, # 150g net weight / 30g
        "fssai_license": "99999999999999"
    })
    
    # Phase 5 logic
    pdf_path = os.path.join(os.path.dirname(__file__), "test_e2e_label.pdf")
    generate_pdf(compliant_data, pdf_path)
    
    assert os.path.exists(pdf_path), "E2E PDF was not created"
    print(f"E2E test passed successfully. PDF at {pdf_path}")
    
    # Cleanup
    os.remove(pdf_path)

if __name__ == "__main__":
    test_end_to_end()
