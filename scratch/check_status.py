import os
import time
from supabase import create_client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

tickers = [
    "AMD.US", "AMZN.US", "CRWD.US", "DDOG.US", "DSY.PA", 
    "GOOG.US", "NET.US", "NOW.US", "SHOP.US", "SNOW.US", 
    "TER.US", "TTD.US", "UBER.US"
]

def check_all():
    while True:
        res = supabase.table("company_presentation").select("ticker_eod, status, pdf_url, html_url, audio_url").in_("ticker_eod", tickers).execute()
        
        data_by_ticker = {r["ticker_eod"]: r for r in res.data}
        
        all_done = True
        print("\n--- Current Status ---")
        for t in tickers:
            row = data_by_ticker.get(t)
            if not row or row.get("status") != "uploaded":
                print(f"{t}: PENDING")
                all_done = False
            else:
                print(f"{t}: UPLOADED")
                
        if all_done:
            print("\n================ FINAL URLS ================")
            for t in tickers:
                row = data_by_ticker.get(t)
                print(f"\n[{t}]")
                print(f"PDF: {row['pdf_url']}")
                print(f"HTML: {row['html_url']}")
                print(f"Audio: {row['audio_url']}")
            break
        
        print("\nWaiting 60 seconds before next check...")
        time.sleep(60)

if __name__ == "__main__":
    check_all()
