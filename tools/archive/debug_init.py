import os
from supabase import create_client
from dotenv import load_dotenv

print("1. Loading .env...")
load_dotenv('.env')
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
print(f"2. Got URL: {url is not None}, Key: {key is not None}")

print("3. Creating client...")
try:
    s = create_client(url, key)
    print("4. Client created.")
    r = s.table("company_presentation").select("ticker_eod").limit(1).execute()
    print(f"5. Query SUCCESS: {r.data}")
except Exception as e:
    print(f"6. FAILED Supabase: {e}")

print("7. Importing Gemini...")
import google.generativeai as genai
print("8. Gemini imported.")

print("9. Configuring Gemini...")
g_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
genai.configure(api_key=g_key)
print("10. Gemini configured.")

print("11. Testing Generation...")
try:
    model = genai.GenerativeModel("gemini-3-flash-preview")
    resp = model.generate_content("Hello")
    print(f"12. Gemini SUCCESS: {resp.text}")
except Exception as e:
    print(f"13. FAILED Gemini: {e}")
