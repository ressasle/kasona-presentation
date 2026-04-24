import os
import google.generativeai as genai
from dotenv import load_dotenv

_env_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
load_dotenv(_env_path)

api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
if not api_key:
    print("No API key found")
    exit(1)

genai.configure(api_key=api_key)

print("Listing all reachable models:")
try:
    for m in genai.list_models():
        print(f"Name: {m.name}, Supported Methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error: {e}")
