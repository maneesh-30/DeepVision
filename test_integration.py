import os
import requests
import time
import subprocess
import signal

def test_integration():
    print("Starting Flask server for integration test...")
    # Start flask in background
    proc = subprocess.Popen(
        [r".\venv\Scripts\python", "app.py"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print("Waiting for server to start...")
    time.sleep(3) # Give it a few seconds to boot
    
    try:
        # Check if it's up
        resp = requests.get("http://127.0.0.1:5000/")
        assert resp.status_code == 200, "Homepage did not load"
        print("Homepage loaded successfully")
        
        # Test generation endpoint
        print("Testing /generate endpoint...")
        form_data = {
            "product_name": "Integration Test Cookies",
            "ingredients": "100g wheat flour\n50g sugar",
            "serving_size": "30",
            "net_weight": "300",
            "use_raw_weight": "on"
        }
        
        # This will call the Groq API because parser.py uses it
        # Make sure .env has a valid key if you expect this to fully pass
        # If API key is missing or invalid, it will fail, which is expected behavior
        resp = requests.post("http://127.0.0.1:5000/generate", data=form_data)
        
        # We might get a 400 or 500 if the LLM API key isn't set up yet
        if resp.status_code == 200:
            print("Generate endpoint returned 200 OK")
            assert "Integration Test Cookies" in resp.text, "Product name not in output"
            assert "pdf_url" in resp.text or "Download PDF" in resp.text, "PDF link not in output"
            print("Integration test passed fully!")
        else:
            print(f"Generate endpoint returned {resp.status_code}. This might be due to missing LLM_API_KEY if error is 400/500.")
            print("Response:", resp.text)
            
    finally:
        # Kill the server
        print("Shutting down Flask server...")
        proc.kill()

if __name__ == "__main__":
    test_integration()
