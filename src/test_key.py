import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Llave leída: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")

if not api_key or "PEGAR" in api_key:
    print("❌ LA KEY NO ES VALIDA (Es el placeholder).")
else:
    genai.configure(api_key=api_key)
    try:
        print("Listando modelos disponibles...")
        with open("models.txt", "w") as f:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Escribir nombre limpio
                    name = m.name
                    if name.startswith("models/"):
                        name = name.replace("models/", "")
                    f.write(f"{name}\n")
                    print(f"- {name}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
