import sqlite3
import os

def get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'nutrition.db')

def validate_health_claims(per_100g: dict) -> dict:
    """
    Validates the 13 FSSAI Health Claims against calculated per_100g values.
    Returns: { 'qualified': [...], 'disqualified': [...] }
    """
    qualified = []
    disqualified = []
    
    fat = per_100g.get('fat', 0)
    sat_fat = per_100g.get('sat_fat', 0)
    sodium = per_100g.get('sodium', 0)
    energy = per_100g.get('energy', 0)
    protein = per_100g.get('protein', 0)
    added_sugar = per_100g.get('added_sugar', 0)
    sugar = per_100g.get('sugar', 0)
    trans_fat = per_100g.get('trans_fat', 0)

    claims_registry = [
        {"claim": "Low Fat", "value": fat, "threshold": 3, "operator": "<", "unit": "g", "tip": "Reduce butter, oil or ghee"},
        {"claim": "Fat Free", "value": fat, "threshold": 0.5, "operator": "<", "unit": "g", "tip": "Remove all added fats"},
        {"claim": "Low Saturated Fat", "value": sat_fat, "threshold": 1.5, "operator": "<", "unit": "g", "tip": "Replace butter/ghee with sunflower oil"},
        {"claim": "Low Sodium", "value": sodium, "threshold": 120, "operator": "<", "unit": "mg", "tip": "Reduce or eliminate salt"},
        {"claim": "Very Low Sodium", "value": sodium, "threshold": 40, "operator": "<", "unit": "mg", "tip": "Remove all sodium-containing ingredients"},
        {"claim": "Sodium Free", "value": sodium, "threshold": 5, "operator": "<", "unit": "mg", "tip": "No salt or sodium additives allowed"},
        {"claim": "Low Calorie", "value": energy, "threshold": 40, "operator": "<", "unit": "kcal", "tip": "Significantly reduce fats and sugars"},
        {"claim": "High Protein", "value": protein, "threshold": 10, "operator": ">", "unit": "g", "tip": "Add whey powder, besan or soy protein isolate"},
        {"claim": "Source of Protein", "value": protein, "threshold": 5, "operator": ">", "unit": "g", "tip": "Add eggs, milk solids or legume flour"},
        {"claim": "No Added Sugar", "value": added_sugar, "threshold": 0, "operator": "==", "unit": "g", "tip": "Remove all sweeteners (sugar, jaggery, honey, syrups)"},
        {"claim": "Low Sugar", "value": sugar, "threshold": 5, "operator": "<", "unit": "g", "tip": "Reduce all sweeteners in recipe"},
        {"claim": "Sugar Free", "value": sugar, "threshold": 0.5, "operator": "<", "unit": "g", "tip": "Remove all sugars including natural fruit sugars"},
        {"claim": "Trans Fat Free", "value": trans_fat, "threshold": 0.2, "operator": "<", "unit": "g", "tip": "Remove vanaspati and hydrogenated oils"}
    ]
    
    for c in claims_registry:
        val = c["value"]
        thresh = c["threshold"]
        
        if c["operator"] == "==":
            qualifies = (val == thresh)
            gap = abs(val - thresh)
        elif c["operator"] == "<":
            qualifies = (val < thresh)
            gap = max(0, val - thresh)
        else: # ">"
            qualifies = (val > thresh)
            gap = max(0, thresh - val)
            
        if qualifies:
            qualified.append({
                "claim": c["claim"],
                "value": round(val, 2),
                "unit": c["unit"]
            })
        else:
            disqualified.append({
                "claim": c["claim"],
                "value": round(val, 2),
                "threshold": thresh,
                "gap": abs(round(gap, 2)),
                "unit": c["unit"],
                "tip": c["tip"]
            })
            
    return {
        "qualified": qualified,
        "disqualified": disqualified
    }

def suggest_sodium_fix(ingredients, per_100g_sodium, final_yield_weight, target_sodium=600):
    if per_100g_sodium <= target_sodium:
        return None
        
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    total_sodium_mg = (per_100g_sodium * final_yield_weight) / 100
    target_total_sodium = (target_sodium * final_yield_weight) / 100
    sodium_to_remove = total_sodium_mg - target_total_sodium
    
    contributors = []
    
    for item in ingredients:
        name = item["name"]
        qty = item["quantity"]
        
        # Query DB to get sodium for this exact ingredient name
        cursor.execute("SELECT sodium FROM ingredients WHERE name=?", (name,))
        row = cursor.fetchone()
        if row is None:
            # Fallback for LIKE query matches
            cursor.execute("SELECT sodium FROM ingredients WHERE name LIKE ? LIMIT 1", (f"%{name}%",))
            row = cursor.fetchone()
            
        if row and row[0] is not None:
            ing_sodium_per_100g = row[0]
            if ing_sodium_per_100g > 0:
                contribution_mg = (ing_sodium_per_100g * qty) / 100
                percentage = (contribution_mg / total_sodium_mg) * 100
                contributors.append({
                    "name": name,
                    "quantity": qty,
                    "sodium_per_100g": ing_sodium_per_100g,
                    "contribution_mg": contribution_mg,
                    "percentage": percentage
                })
                
    conn.close()
    
    # Sort descending by contribution
    contributors.sort(key=lambda x: x["contribution_mg"], reverse=True)
    
    fixes = []
    remaining_to_remove = sodium_to_remove
    
    for c in contributors:
        if remaining_to_remove <= 0.05: # practically 0
            break
            
        name = c["name"]
        current_amount = c["quantity"]
        current_cont = c["contribution_mg"]
        ing_sodium_per_100g = c["sodium_per_100g"]
        
        # We cap the reduction such that minimum amount is 0.1g
        min_allowed_contribution = (ing_sodium_per_100g * 0.1) / 100
        max_possible_removal = current_cont - min_allowed_contribution
        
        if max_possible_removal <= 0: # Can't remove any meaningful amount staying >= 0.1g
             new_qty = 0.1
             removed_from_this = max(0, current_cont - min_allowed_contribution)
        else:
            amount_to_remove_from_this = min(remaining_to_remove, max_possible_removal)
            new_contribution = current_cont - amount_to_remove_from_this
            new_qty = (new_contribution * 100) / ing_sodium_per_100g
            removed_from_this = amount_to_remove_from_this
            
        remaining_to_remove -= removed_from_this
        
        fixes.append({
            "name": name,
            "old_qty": round(current_amount, 2),
            "new_qty": round(new_qty, 2),
            "sodium_removed": round(removed_from_this, 2),
            "is_primary": "salt" in name.lower()
        })
        
    # Check if fixed
    new_total_sodium = total_sodium_mg - sum(f["sodium_removed"] for f in fixes)
    new_sodium_per_100g = (new_total_sodium / final_yield_weight) * 100 if final_yield_weight > 0 else 0
    is_fully_fixed = round(new_sodium_per_100g, 1) <= target_sodium
    
    return {
        "current_sodium_100g": round(per_100g_sodium, 1),
        "contributors": contributors,
        "fixes": fixes,
        "new_sodium_per_100g": round(new_sodium_per_100g, 1),
        "is_fully_fixed": is_fully_fixed,
        "target_sodium": target_sodium
    }
