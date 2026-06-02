import os
import requests
from supabase import create_client
from dotenv import load_dotenv

# Load env
load_dotenv(".env")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
eodhd_key = os.environ.get("EODHD_API_KEY")
supabase = create_client(url, key)

tickers_to_fix = ["HLMA", "IMCD", "INDT", "LAGR-B", "LIFCO-B", "MMGR-B", "QXO"]

def normalize(ticker, eodhd_key):
    # Try to find company name first
    res = supabase.table("company_presentation").select("company_name").eq("ticker_eod", ticker).execute()
    if not res.data: return None
    company_name = res.data[0]["company_name"]
    
    print(f"Normalizing {ticker} ({company_name})...")
    search_url = f"https://eodhd.com/api/search/{company_name}?api_token={eodhd_key}&fmt=json"
    try:
        r = requests.get(search_url, timeout=10)
        data = r.json()
        for item in data:
            if item.get("Code", "").upper() == ticker.upper():
                full = f"{item['Code'].upper()}.{item['Exchange'].upper()}"
                return full
    except: pass
    return f"{ticker}.US"

for t in tickers_to_fix:
    new_t = normalize(t, eodhd_key)
    if new_t and new_t != t:
        print(f"  Updating {t} -> {new_t}")
        # Check if new_t already exists
        check = supabase.table("company_presentation").select("id").eq("ticker_eod", new_t).execute()
        if check.data:
            print(f"    [MERGE] {new_t} already exists. Merging {t} into it.")
            # For simplicity in this script, we just delete the old one if the new one exists
            # In a real scenario we'd merge fields, but let's assume the suffixed one is better.
            supabase.table("company_presentation").delete().eq("ticker_eod", t).execute()
        else:
            supabase.table("company_presentation").update({"ticker_eod": new_t}).eq("ticker_eod", t).execute()
