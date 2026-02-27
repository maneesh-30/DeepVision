import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# We will support Groq (llama-3) or Gemini (gemini-1.5-flash) style APIs.
# The original guide specified Groq, which uses OpenAI-compatible endpoints.
LLM_API_KEY = os.getenv("LLM_API_KEY")

def retry_parse(raw_text):
    return parse_ingredients(raw_text, retries=1)

def parse_ingredients(raw_text, retries=0):
    if not LLM_API_KEY:
        raise ValueError("LLM API key missing. Please check your .env configuration.")

    prompt = f"""
You are a precise food ingredient parser.
Extract: ingredient name, numeric quantity, unit.
Return ONLY a valid JSON array. No extra text, no markdown.
Convert fractions to decimals. Default unit to 'g' if missing.
Remove adjectives and prep methods from ingredient names.

Input:
{raw_text}
"""
    try:
        # Check if it's a Gemini key or Groq key
        if LLM_API_KEY.startswith("gsk_"):
            # It's a Groq key
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": "llama-3.1-8b-instant", # Updated reliable Groq model
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0
                }
            )
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
        else:
            # Assume it's a Gemini key using the Google Generative AI REST endpoint
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={LLM_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts":[{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0
                    }
                }
            )
            response.raise_for_status()
            result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        # Strip markdown code fences if LLM adds them
        result = result.strip().strip("```json").strip("```").strip()
        
        parsed_data = json.loads(result)
        
        # Validate that the structure is basically correct
        if not isinstance(parsed_data, list):
            raise ValueError("LLM did not return a list")
            
        for item in parsed_data:
            if "name" not in item or "quantity" not in item or "unit" not in item:
                raise ValueError("LLM response missing required keys")
            if float(item["quantity"]) <= 0:
                raise ValueError(f"Invalid quantity for {item['name']}. Must be greater than 0.")
                
        return parsed_data

    except json.JSONDecodeError:
        if retries == 0:
            return retry_parse(raw_text)
        else:
            raise ValueError("Could not parse ingredient list. Please check input format.")
    except Exception as e:
        # Add response text to error if available for debugging
        error_details = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_details += f" | Details: {e.response.text}"
        raise ValueError(f"Error communicating with LLM logic: {error_details}")

def standardize_units(parsed_list):
    unit_map = {
        "kg": 1000, 
        "mg": 0.001, 
        "l": 1000,
        "tbsp": 15, 
        "tsp": 5, 
        "cup": 200,
        "piece": 50, 
        "whole": 50,
        "ml": 1,
        "g": 1
    }
    
    standardized = []
    for item in parsed_list:
        unit = item.get("unit", "g").lower()
        
        try:
            qty = float(item["quantity"])
        except (ValueError, TypeError):
            continue
            
        name = str(item.get("name", "")).lower().strip()
        if not name:
            continue
            
        if unit in unit_map:
            qty = qty * unit_map[unit]
            
        standardized.append({
            "name": name,
            "quantity": qty
        })
        
    return standardized
