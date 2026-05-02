import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models_to_test = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
for m in models_to_test:
    try:
        response = client.models.generate_content(
            model=m,
            contents="Di la palabra 'Hola' y nada mas.",
        )
        print(f"SUCCESS with {m}: {response.text.strip()}")
    except Exception as e:
        print(f"FAILED with {m}: {e}")
