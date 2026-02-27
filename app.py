import os
from flask import Flask, render_template, request, send_file, jsonify
from engines.parser import parse_ingredients, standardize_units
from engines.calculator import calculate_nutrition
from engines.compliance import apply_compliance
from engines.compliance_features import validate_health_claims, suggest_sodium_fix
from engines.label_generator import generate_pdf
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Ensure PDF output directory exists
pdf_dir = os.path.join(app.root_path, 'static', 'pdfs')
os.makedirs(pdf_dir, exist_ok=True)

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # 1. Collect inputs
        product_name = request.form.get('product_name', 'Unnamed Product')
        raw_recipe = request.form.get('ingredients', '')
        serving_size_g = float(request.form.get('serving_size', 30))
        net_weight_g = float(request.form.get('net_weight', 100))
        fssai_license = request.form.get('fssai_license', '')
        
        use_raw_weight = request.form.get('use_raw_weight') == 'on'
        yield_weight_str = request.form.get('yield_weight', '0')
        final_yield_weight = 0 if use_raw_weight else float(yield_weight_str)

        if not raw_recipe.strip():
            return jsonify({"error": "Ingredients are required"}), 400

        # Calculate servings per pack
        servings_per_pack = max(1, round(net_weight_g / serving_size_g))

        # 2. Parse and Standardize
        parsed_json = parse_ingredients(raw_recipe)
        standardized_ingredients = standardize_units(parsed_json)

        # 3. Calculate Nutrition
        calc_data = calculate_nutrition(standardized_ingredients, final_yield_weight, serving_size_g)

        # 4. Apply Compliance (Rounding, formatting, allergens)
        compliant_data = apply_compliance(calc_data)
        
        health_claims = validate_health_claims(calc_data['per_100g'])
        
        sodium_fix = None
        if calc_data['per_100g']['sodium'] > 600:
            sodium_fix = suggest_sodium_fix(
                standardized_ingredients,
                calc_data['per_100g']['sodium'],
                final_yield_weight
            )
        
        # Merge form data with compliant data
        compliant_data.update({
            "product_name": product_name,
            "serving_size_g": serving_size_g,
            "servings_per_pack": servings_per_pack,
            "fssai_license": fssai_license,
            "health_claims": health_claims,
            "sodium_fix": sodium_fix
        })

        # 5. Generate PDF
        pdf_filename = f"nutrition_label_{product_name.replace(' ', '_').lower()}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        generate_pdf(compliant_data, pdf_path)
        
        compliant_data["pdf_url"] = f"/static/pdfs/{pdf_filename}"
        
        # Provide JSON or HTML Preview
        if request.headers.get('Accept') == 'application/json':
            return jsonify(compliant_data)
        return render_template('result.html', data=compliant_data)

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
