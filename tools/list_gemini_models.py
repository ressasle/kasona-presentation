import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
os.environ["GOOGLE_API_KEY"] = api_key
genai.configure(api_key=api_key)

print("Available Models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
