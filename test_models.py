import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("API Key no encontrada")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    response = requests.get(url)
    data = response.json()
    if 'models' in data:
        print("Modelos disponibles:")
        for m in data['models']:
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                print(f"- {m['name']}")
    else:
        print("Error o respuesta inesperada:")
        print(data)
