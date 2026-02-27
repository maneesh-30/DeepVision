import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.parser import standardize_units

def test_standardize_units():
    sample_data = [
        {"name": "wheat flour", "quantity": "2", "unit": "kg"},
        {"name": "sugar", "quantity": "3", "unit": "tsp"},
        {"name": "milk", "quantity": "500", "unit": "ml"},
        {"name": "salt", "quantity": "10", "unit": "g"}
    ]
    
    result = standardize_units(sample_data)
    
    expected = [
        {"name": "wheat flour", "quantity": 2000.0},
        {"name": "sugar", "quantity": 15.0},
        {"name": "milk", "quantity": 500.0},
        {"name": "salt", "quantity": 10.0}
    ]
    
    assert result == expected, f"Expected {expected}, got {result}"
    print("test_standardize_units passed successfully!")

if __name__ == "__main__":
    test_standardize_units()
