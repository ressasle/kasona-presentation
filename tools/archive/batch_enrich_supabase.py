import os
import requests
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment
load_dotenv(r"C:\Users\Administrator\Documents\kasonaops\presentation\.env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
EODHD_KEY = os.environ.get("EODHD_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, EODHD_KEY]):
    print("Error: Missing SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, or EODHD_API_KEY in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

AI_ERROR_MARKER = "[AI_ERROR] Gemini quota exceeded after all retries."

def get_eodhd_fundamentals(ticker):
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={EODHD_KEY}&fmt=json"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return None

def resolve_ticker(ticker):
    """Attempt to resolve a raw ticker to an EODHD ticker if needed."""
    if "." in ticker or "-" in ticker and len(ticker.split("-")) > 1 and len(ticker.split("-")[1]) > 1:
        # Likely already has suffix (e.g. AAPL.US or MMGR-B.ST)
        return ticker
    
    print(f"Resolving ticker: {ticker}")
    url = f"https://eodhd.com/api/search/{ticker}?api_token={EODHD_KEY}&fmt=json"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        if data:
            # Sort by relevance or just take the first one that matches the code
            for match in data:
                if match['Code'] == ticker:
                    return f"{match['Code']}.{match['Exchange']}"
            return f"{data[0]['Code']}.{data[0]['Exchange']}"
    return ticker

def enrich():
    # 1. Fetch missing core metadata in company_presentation
    print("Fetching tickers from company_presentation with missing data...")
    res = supabase.table("company_presentation").select("ticker_eod").is_("company_name", "null").execute()
    tickers = [row['ticker_eod'] for row in res.data]
    print(f"Found {len(tickers)} tickers to process.")

    for raw_ticker in tickers:
        print(f"\nProcessing {raw_ticker}...")
        
        # Fundamental data
        fundamentals = get_eodhd_fundamentals(raw_ticker)
        if not fundamentals:
            # Try resolving if it failed
            resolved = resolve_ticker(raw_ticker)
            if resolved != raw_ticker:
                print(f"Retrying with resolved ticker: {resolved}")
                fundamentals = get_eodhd_fundamentals(resolved)
        
        if not fundamentals:
            print(f"Failed to get data for {raw_ticker}")
            continue

        general = fundamentals.get("General") or {}
        highlights = fundamentals.get("Highlights") or {}
        address = general.get("AddressData") or {}
        
        company_name = general.get("Name")
        description = general.get("Description")
        officers = general.get("Officers")
        website = general.get("WebURL")
        industry = general.get("Industry")
        phone = general.get("Phone")
        hq_location = f"{address.get('City', '')}, {address.get('Country', '')}".strip(", ")

        # Update company_presentation
        pres_data = {
            "company_name": company_name,
            "description": description,
            "officers": officers,
            "investment_thesis": AI_ERROR_MARKER,
            "strategic_vision": AI_ERROR_MARKER,
            "competitive_landscape": AI_ERROR_MARKER,
            "growth_roadmap": AI_ERROR_MARKER,
            "bull-case": AI_ERROR_MARKER,
            "bear-case": AI_ERROR_MARKER,
            "leadership-governance": AI_ERROR_MARKER,
            "risk-success-factors": AI_ERROR_MARKER,
            "history-evolution": AI_ERROR_MARKER
        }
        
        # Clean nulls in pres_data (don't overwrite with null if we have something)
        pres_data = {k: v for k, v in pres_data.items() if v is not None}

        supabase.table("company_presentation").update(pres_data).eq("ticker_eod", raw_ticker).execute()
        print(f"[OK] Updated company_presentation for {raw_ticker}")

        # Upsert into companies
        comp_data = {
            "company_name": company_name,
            "website": website,
            "industry": industry,
            "hq_location": hq_location,
            "phone": phone
        }
        # We don't have a direct ticker join for 'companies' usually, it's by name or id.
        # But looking at the schema, it's a separate entity. 
        # For now, let's just ensure company_presentation is solid.
        
        # Update quarterly_earnings if ticker matches
        earnings_res = supabase.table("quarterly_earnings").select("id").eq("ticker_eod", raw_ticker).execute()
        if earnings_res.data:
            earn_update = {
                "markdown_content_de": str(AI_ERROR_MARKER),
                "executive_summary_de": str(AI_ERROR_MARKER)
            }
            
            eps_val = highlights.get("DilutedEpsTTM")
            rev_val = highlights.get("RevenueTTM")
            
            # If we want exact quarter data:
            earnings_history = fundamentals.get("Earnings", {}).get("History", {})
            if earnings_history and isinstance(earnings_history, dict):
                latest_q = list(earnings_history.values())[0]
                eps_val = latest_q.get("epsActual")
                earn_update["eps_estimate"] = latest_q.get("epsEstimate")
            
            financials_history = fundamentals.get("Financials", {}).get("Income_Statement", {}).get("quarterly", {})
            if financials_history and isinstance(financials_history, dict):
                latest_f = list(financials_history.values())[0]
                rev_val = latest_f.get("totalRevenue")

            if eps_val is not None:
                earn_update["eps_actual"] = float(eps_val) if str(eps_val).replace('.','',1).isdigit() else None
            if rev_val is not None:
                earn_update["revenue_actual"] = float(rev_val) if str(rev_val).replace('.','',1).isdigit() else None
            
            # Remove any keys with None value to avoid overwriting existing data with nulls
            earn_update = {k: v for k, v in earn_update.items() if v is not None}

            supabase.table("quarterly_earnings").update(earn_update).eq("ticker_eod", raw_ticker).execute()
            print(f"[OK] Updated quarterly_earnings for {raw_ticker}")

if __name__ == "__main__":
    enrich()
