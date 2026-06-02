#!/usr/bin/env python3
import os
import json
import time
import requests
import argparse
import google.generativeai as genai
from supabase import create_client
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True, help="Ticker in SYMBOL.EXCHANGE format")
    parser.add_argument("--name", help="Company Name")
    parser.add_argument("--chart", help="Path to local chart image to inject")
    args = parser.parse_args()
    
    ticker = args.ticker
    
    # Load .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    EODHD_API_KEY = os.getenv("EODHD_API_KEY")
    GEMINI_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-3-flash-preview") # Production model
    
    print(f"[*] Fetching fundamentals for {ticker}...")
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={EODHD_API_KEY}&fmt=json"
    resp = requests.get(url)
    funda = resp.json() if resp.status_code == 200 else {}
    gen = funda.get("General", {})
    
    company_name = args.name or gen.get("Name", ticker)
    description = gen.get("Description", "")
    
    def synthesize(field_name, prompt_context, length="short"):
        print(f"[*] Synthesizing {field_name}...")
        time.sleep(10) # Aggressive rate limit mitigation
        limit = "max 3 sentences" if length == "short" else "comprehensive institutional grade (300-500 words)"
        prompt = f"Company: {company_name}\nDescription: {description}\n\nTask: Provide a professional, high-fidelity institutional {field_name} in English. {limit}.\nContext: {prompt_context}"
        try:
            r = model.generate_content(prompt)
            return r.text.strip()
        except Exception as e:
            print(f"  [ERR] {field_name} failed: {e}")
            return ""

    print("[*] Checking existing record for partial population...")
    existing = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    existing_data = existing.data[0] if existing.data else {}

    def get_or_synthesize(field_name, prompt_context, column_name, length="short"):
        val = existing_data.get(column_name) or ""
        if val and len(val) > 20: # Assume already populated
            print(f"[*] {field_name} already exists, skipping...")
            return val
        res = synthesize(field_name, prompt_context, length)
        return res if res else val

    # Strategic Pillars
    investment_thesis = get_or_synthesize("Investment Thesis", "Long-term value creation perspective.", "investment_thesis")
    strategic_vision = get_or_synthesize("Strategic Vision", "Future market positioning and tech edge.", "strategic_vision")
    competitive_landscape = get_or_synthesize("Competitive Landscape", "Key rivals and moats.", "competitive_landscape")
    growth_roadmap = get_or_synthesize("Growth Roadmap", "Revenue drivers and M&A/Expansion.", "growth_roadmap")
    history_evolution = get_or_synthesize("Company History & Evolution", "Key milestones from founding to current leader.", "history-evolution", length="medium")
    leadership = get_or_synthesize("Leadership & Governance Audit", "Executive core and governance quality.", "leadership-governance", length="medium")
    risk_factors = get_or_synthesize("Risk & Success Factors", "Critical dependencies and tailwinds.", "risk-success-factors", length="medium")
    bull_case = get_or_synthesize("Investment Bull Case", "Key catalysts for upside performance.", "bull-case")
    bear_case = get_or_synthesize("Investment Bear Case", "Key risks and potential downside scenarios.", "bear-case")
    
    # Porter's Five Forces
    rivalry = get_or_synthesize("Porter's Force: Rivalry among existing competitors", "Intensity of competition.", "rivalry")
    supplier_power = get_or_synthesize("Porter's Force: Bargaining power of suppliers", "Dependency on critical components.", "supplier-power")
    buyer_power = get_or_synthesize("Porter's Force: Bargaining power of buyers", "Customer concentration vs price power.", "buyer-power")
    threat_of_entry = get_or_synthesize("Porter's Force: Threat of new entrants", "Barriers to entry.", "threat-of-entry")
    substitutes = get_or_synthesize("Porter's Force: Threat of substitute products", "Technological displacement risks.", "substitutes")

    payload = {
        "company_name": company_name,
        "description": description,
        "investment_thesis": investment_thesis,
        "strategic_vision": strategic_vision,
        "competitive_landscape": competitive_landscape,
        "growth_roadmap": growth_roadmap,
        "history-evolution": history_evolution,
        "leadership-governance": leadership,
        "risk-success-factors": risk_factors,
        "bull-case": bull_case,
        "bear-case": bear_case,
        "rivalry": rivalry,
        "supplier-power": supplier_power,
        "buyer-power": buyer_power,
        "threat-of-entry": threat_of_entry,
        "substitutes": substitutes,
        "status": "to_review"
    }
    
    print("[*] Updating Supabase...")
    existing = supabase.table("company_presentation").select("id").eq("ticker_eod", ticker).execute()
    if existing.data:
        record_id = existing.data[0]["id"]
        supabase.table("company_presentation").update({**payload}).eq("id", record_id).execute()
        print(f"[*] Updated existing record ID: {record_id}")
    else:
        supabase.table("company_presentation").insert({**payload, "ticker_eod": ticker}).execute()
        print("[*] Inserted new record")
    
    print("[SUCCESS] Research data populated. Now generating artifacts...")
    
    # Trigger generic artifact generation (needs to be created)
    # For now, I'll update generate_presentation_pdf.py to handle the chart if passed
    
    # Inject chart into markdown if provided
    if args.chart:
        print(f"[*] Chart injection requested: {args.chart}")
        # Logic to append to markdown_content would go here or handled in the generator
    
    # Execute generation command for this ticker
    os.system(f"python tools/generate_ticker_artifacts.py --ticker {ticker} --chart {args.chart if args.chart else ''}")

if __name__ == "__main__":
    main()
