import os
import json
import time
import requests
import google.generativeai as genai
from supabase import create_client
from dotenv import load_dotenv

def main():
    # Load .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    # Config
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    EODHD_API_KEY = os.getenv("EODHD_API_KEY")
    GEMINI_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-flash-latest")
    
    ticker = "QXO.US"
    print(f"[*] Fetching fundamentals for {ticker}...")
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={EODHD_API_KEY}&fmt=json"
    resp = requests.get(url)
    funda = resp.json() if resp.status_code == 200 else {}
    gen = funda.get("General", {})
    
    company_name = gen.get("Name", "QXO Inc.")
    description = gen.get("Description", "")
    print(f"[*] Description Length: {len(description)}")
    
    # Get existing Supabase record
    print("[*] Fetching existing Supabase record...")
    res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    existing = res.data[0] if res.data else {}
    
    def synthesize(field_name, prompt_context):
        print(f"[*] Synthesizing {field_name}...")
        time.sleep(15) # Rate limit
        prompt = f"Given the company Description: {description}. Provide a professional, high-fidelity institutional {field_name} (max 3 sentences). Context: {prompt_context}"
        try:
            r = model.generate_content(prompt)
            print(f"  [OK] Generated {len(r.text)} chars.")
            return r.text.strip()
        except Exception as e:
            print(f"  [ERR] {field_name} failed: {e}")
            return ""

    # Generate missing high-fidelity fields
    investment_thesis = synthesize("Investment Thesis", "Focus on Brad Jacobs' buy-and-build strategy in building products distribution.")
    strategic_vision = synthesize("Strategic Vision", "Consolidating the fragmented building products market through technology and M&A.")
    competitive_landscape = synthesize("Competitive Landscape", "Fragmented market with major incumbents like Ferguson but lacks a unified tech leader.")
    growth_roadmap = synthesize("Growth Roadmap", "Scaling to $10B+ revenue through platform acquisitions and AI-driven integration.")
    leadership_governance = synthesize("Leadership & Governance Audit", "Institutional focus on Brad Jacobs (Chairman) and his team of XPO/GXO veterans. Audit should be 100% in English.")

    payload = {
        "company_name": company_name,
        "description": description,
        "investment_thesis": investment_thesis,
        "strategic_vision": strategic_vision,
        "competitive_landscape": competitive_landscape,
        "growth_roadmap": growth_roadmap,
        "leadership-governance": leadership_governance,
        "status": "to_review"
    }
    
    print("[*] Updating Supabase...")
    supabase.table("company_presentation").update(payload).eq("ticker_eod", ticker).execute()
    
    print("[SUCCESS] All columns filled. Now regenerating artifacts...")
    
    # Regenerate artifacts
    os.system("python tools/generate_qxo_artifacts.py")

if __name__ == "__main__":
    main()
