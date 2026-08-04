import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)

if response.status_code == 200:
    models = response.json().get("models", [])
    print("Available embedding models:")
    for m in models:
        if "embed" in m.get("supportedGenerationMethods", []):
            print(f"- {m['name']} (methods: {m.get('supportedGenerationMethods')})")
            
    print("\nAll models:")
    for m in models:
        print(f"- {m['name']}")
else:
    print(f"Failed to fetch models: {response.status_code} - {response.text}")
