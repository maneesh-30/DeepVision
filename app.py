import os
import sqlite3
import uuid
import json
from datetime import timedelta
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from db_init import init_db

from engines.parser import parse_ingredients, standardize_units
from engines.calculator import calculate_nutrition
from engines.compliance import apply_compliance
from engines.compliance_features import validate_health_claims, suggest_sodium_fix
from engines.label_generator import generate_pdf
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Security & Sessions
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    app.secret_key = os.urandom(24)
    print("WARNING: SECRET_KEY not set in environment. Using a random key. Sessions will not persist across restarts.")

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# DB Initialization
with app.app_context():
    init_db()

# Login Manager Setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to generate and save labels."
login_manager.login_message_category = "alert"
login_manager.init_app(app)

def get_db_connection():
    conn = sqlite3.connect('nutrition.db')
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_row:
        return User(id=user_row['id'], name=user_row['name'], email=user_row['email'])
    return None

@login_manager.unauthorized_handler
def unauthorized():
    flash("Please log in to generate and save labels.", "alert")
    if request.path == '/generate':
        return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('landing.html', current_user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            flash('Email already registered', 'alert')
            conn.close()
            return redirect(url_for('signup'))
        
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        conn.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)', (name, email, password_hash))
        conn.commit()
        conn.close()
        
        flash('Successful registration', 'alert')
        return redirect(url_for('login'))
        
    return render_template('signup.html', current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if not user_row:
            flash('Email not found', 'alert')
            return redirect(url_for('login'))
            
        if not check_password_hash(user_row['password_hash'], password):
            flash('Wrong password', 'alert')
            return redirect(url_for('login'))
            
        user = User(id=user_row['id'], name=user_row['name'], email=user_row['email'])
        login_user(user, remember=True)
        return redirect(url_for('dashboard'))
        
    return render_template('login.html', current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', current_user=current_user)

@app.route('/generate', methods=['POST', 'GET'])
@login_required
def generate():
    if request.method == 'GET':
        return redirect(url_for('dashboard'))
        
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

        # 5. Generate PDF with uuid4
        pdf_dir = os.path.join(app.root_path, 'static', 'labels')
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filename = f"label_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        generate_pdf(compliant_data, pdf_path)
        
        compliant_data["pdf_url"] = f"/static/labels/{pdf_filename}"
        
        # 6. Calculate Compliance Score
        compliance_score = 100
        
        # Subtract 20 if sodium > 600mg per 100g
        if float(calc_data['per_100g'].get('sodium', 0)) > 600:
            compliance_score -= 20
            
        # Subtract 10 if trans fat > 0.2g per serving
        if float(calc_data['per_serving'].get('trans_fat', 0)) > 0.2:
            compliance_score -= 10
            
        # Subtract 10 if any mandatory nutrient value is missing or zero.
        mandatory = ['energy', 'protein', 'carbs', 'sugar', 'fat', 'sat_fat', 'trans_fat', 'sodium']
        missing_or_zero = False
        for n in mandatory:
            val = float(calc_data['per_100g'].get(n, 0))
            if val == 0:
                missing_or_zero = True
                break
        
        if missing_or_zero:
            compliance_score -= 10
            
        # Subtract 10 if FSSAI license number was not provided
        if not fssai_license.strip():
            compliance_score -= 10
            
        compliance_score = max(0, compliance_score)
        
        # 7. Save to History
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO label_history (user_id, product_name, compliance_score, pdf_filename, nutrition_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (current_user.id, product_name, compliance_score, pdf_filename, json.dumps(compliant_data)))
        conn.commit()
        conn.close()

        # Provide JSON or HTML Preview
        if request.headers.get('Accept') == 'application/json':
            return jsonify(compliant_data)
        return render_template('result.html', data=compliant_data, current_user=current_user)

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    total_count = conn.execute('SELECT COUNT(*) FROM label_history WHERE user_id = ?', (current_user.id,)).fetchone()[0]
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    
    records = conn.execute('''
        SELECT * FROM label_history 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (current_user.id, per_page, offset)).fetchall()
    conn.close()
    
    return render_template('history.html', records=records, page=page, total_pages=total_pages, current_user=current_user)

@app.route('/download/<int:id>')
@login_required
def download(id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM label_history WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not record or record['user_id'] != current_user.id:
        abort(403)
        
    return send_from_directory(os.path.join(app.root_path, 'static', 'labels'), record['pdf_filename'], as_attachment=True)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM label_history WHERE id = ?', (id,)).fetchone()
    
    if not record or record['user_id'] != current_user.id:
        conn.close()
        abort(403)
        
    conn.execute('DELETE FROM label_history WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    # Clean up PDF file
    try:
        os.remove(os.path.join(app.root_path, 'static', 'labels', record['pdf_filename']))
    except:
        pass
        
    flash("Menu item deleted from history.", "alert")
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
