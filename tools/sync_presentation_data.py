#!/usr/bin/env python3
"""
sync_presentation_data.py — Data Populator Skill (Company Structural Analysis).

Fetches company structural data from EODHD and synchronizes it with 
the `public.company_presentation` table in Supabase.
"""

import os
import sys
import argparse
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

EODHD_API_KEY = os.environ.get("EODHD_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not all([EODHD_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Missing environment variables.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_eodhd_fundamentals(ticker):
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={EODHD_API_KEY}&fmt=json"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}

def sync_presentation(ticker):
    print(f"[*] Syncing Structural Presentation for {ticker}...")
    
    fundamentals = get_eodhd_fundamentals(ticker)
    if not fundamentals:
        print(f"❌ Could not fetch data for {ticker}")
        return

    gen = fundamentals.get("General", {})
    company_name = gen.get("Name", ticker)
    description = gen.get("Description", "")
    sector = gen.get("Sector", "")
    industry = gen.get("Industry", "")
    
    # Heuristic mapping for structural analysis
    investment_thesis = f"Structural leader in {sector}. Dominant position in {industry}."
    strategic_vision = f"Scaling global footprint in {sector} while maintaining technological edge."
    competitive_landscape = f"Primary focus on {industry}. High-barrier to entry with significant R&D spend."
    growth_roadmap = f"Expansion into emerging markets and digitalization of {industry} services."

    data = {
        "ticker_eod": ticker,
        "company_name": company_name,
        "description": description,
        "investment_thesis": investment_thesis,
        "strategic_vision": strategic_vision,
        "competitive_landscape": competitive_landscape,
        "growth_roadmap": growth_roadmap,
        "status": "to_review",
        "updated_at": "now()"
    }

    try:
        supabase.table("company_presentation").upsert(data, on_conflict="ticker_eod").execute()
        print(f"[OK] Successfully synchronized {ticker} presentation data.")
    except Exception as e:
        print(f"[ERR] Sync failed for {ticker}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    args = parser.parse_args()
    sync_presentation(args.ticker)

if __name__ == "__main__":
    main()
