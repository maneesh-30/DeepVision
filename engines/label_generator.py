from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import os

def generate_pdf(label_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle("Title", fontSize=14, fontName="Helvetica-Bold",
                                  alignment=1, spaceAfter=6)
    elements.append(Paragraph("NUTRITION INFORMATION", title_style))
    
    # Check servings per pack safely
    servings_per_pack = label_data.get('servings_per_pack', '1')
    serving_size_g = label_data.get('serving_size_g', 100)
    
    elements.append(Paragraph(
        f"Serving Size: {serving_size_g}g | Servings Per Pack: ~{servings_per_pack}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 4*mm))

    # Nutrition table data
    per_100g = label_data.get('per_100g_display', {})
    if not per_100g:
        # Fallback if the key name is slightly different
        per_100g = label_data.get('per_100g', {})
        
    per_serving = label_data.get('per_serving_display', {})
    if not per_serving:
        per_serving = label_data.get('per_serving', {})

    table_data = [
        ["Nutrient", "Per 100g", f"Per Serving ({serving_size_g}g)"],
        ["Energy", f"{per_100g.get('energy', 0)} kcal", f"{per_serving.get('energy', 0)} kcal"],
        ["Protein", f"{per_100g.get('protein', 0)} g", f"{per_serving.get('protein', 0)} g"],
        ["Carbohydrate", f"{per_100g.get('carbs', 0)} g", f"{per_serving.get('carbs', 0)} g"],
        ["  of which Total Sugars", f"{per_100g.get('sugar', 0)} g", f"{per_serving.get('sugar', 0)} g"],
        ["  of which Added Sugars", f"{per_100g.get('added_sugar', 0)} g", f"{per_serving.get('added_sugar', 0)} g"],
        ["Total Fat", f"{per_100g.get('fat', 0)} g", f"{per_serving.get('fat', 0)} g"],
        ["  of which Saturated Fat", f"{per_100g.get('sat_fat', 0)} g", f"{per_serving.get('sat_fat', 0)} g"],
        ["  of which Trans Fat", f"{per_100g.get('trans_fat', 0)} g", f"{per_serving.get('trans_fat', 0)} g"],
        ["Sodium", f"{per_100g.get('sodium', 0)} mg", f"{per_serving.get('sodium', 0)} mg"],
    ]

    t = Table(table_data, colWidths=[90*mm, 40*mm, 50*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#1B3A6B")),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#E8EEF6")]),
        ("FONTNAME",     (0,1), (0,-1), "Helvetica-Bold"),
        ("LEFTPADDING",  (0,3), (0,5), 16),  # Indent sub-rows
        ("LEFTPADDING",  (0,7), (0,8), 16),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4*mm))

    # Ingredient list
    ingredients_list = label_data.get("ingredients", [])
    total_q = sum(x.get('quantity', 0) for x in ingredients_list)
    if total_q == 0: total_q = 1  # prevent div by zero
    
    item_strings = []
    for i in ingredients_list:
        name = i.get('name', '').title()
        pct = round(i.get('quantity', 0) / total_q * 100)
        item_strings.append(f"{name} ({pct}%)")
        
    ingredient_text = "Ingredients: " + ", ".join(item_strings)
    
    ingredients_style = ParagraphStyle("Ingredients", fontSize=10, leading=14)
    elements.append(Paragraph(ingredient_text, ingredients_style))
    elements.append(Spacer(1, 2*mm))

    # Allergen statement
    elements.append(Paragraph(label_data.get("allergen_statement", "No known allergens"), ingredients_style))
    elements.append(Spacer(1, 2*mm))

    # Veg symbol + License
    veg_type = label_data.get("veg_type", "veg")
    veg_symbol_color = "🟢" if veg_type == "veg" else "🟤"
    veg_symbol_text = "VEGETARIAN" if veg_type == "veg" else "NON-VEGETARIAN"
    
    fssai_license = label_data.get('fssai_license', 'NOT PROVIDED')
    
    bottom_style = ParagraphStyle("Bottom", fontSize=10, fontName="Helvetica-Bold", leading=14)
    elements.append(Paragraph(
        f"{veg_symbol_color} {veg_symbol_text}          FSSAI Lic. No.: {fssai_license}",
        bottom_style
    ))

    # Disclaimer if raw weight used
    if label_data.get("show_disclaimer"):
        disclaimer_style = ParagraphStyle("Disclaimer", fontSize=7, textColor=colors.grey)
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph(
            "* Nutritional values are estimated based on raw ingredient weights. "
            "For certified accuracy, use lab-tested final product weight.",
            disclaimer_style
        ))

    doc.build(elements)
    return output_path
