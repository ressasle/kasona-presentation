import os
import sys
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
EODHD_API_KEY = os.environ.get("EODHD_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, EODHD_API_KEY]):
    print("Error: Missing environment variables.")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS = ["UBER.US"]

def main():
    for ticker in TICKERS:
        print(f"Processing {ticker}...")
        try:
            url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={EODHD_API_KEY}&fmt=json"
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            general = data.get("General", {})
            company_name = general.get("Name", "")
            description = general.get("Description", "")
            officers_dict = general.get("Officers", {})
            
            # Serialize Officers into a list
            officers_list = list(officers_dict.values()) if officers_dict else []
            
            row = {
                "ticker_eod": ticker,
                "company_name": company_name,
                "description": description,
                "officers": officers_list,
                "status": "to_review"
            }
            
            res = supabase.table("company_presentation").upsert(row).execute()
            if hasattr(res, 'data') and res.data:
                print(f"  [OK] Upserted {ticker} successfully.")
            else:
                print(f"  [WARN] Upsert might have failed for {ticker}. Response: {res}")
                
        except Exception as e:
            print(f"  [ERR] Failed to process {ticker}: {e}")

if __name__ == "__main__":
    main()
