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
    "AI.PA", "BCHN.SW", "BTC-USD.CC", "COIN.US", "ETH-USD.CC", 
    "HOOD.US", "MA.US", "SOL-USD.CC", "SPGI.US", "SREN.SW", "TT.US"
]

def check_all():
    while True:
        res = supabase.table("company_presentation").select("ticker_eod, status, pdf_url, html_url, audio_url").in_("ticker_eod", tickers).execute()
        data_by_ticker = {r["ticker_eod"]: r for r in res.data}
        
        all_done = True
        for t in tickers:
            row = data_by_ticker.get(t)
            if not row or row.get("status") != "uploaded":
                all_done = False
                break
                
        if all_done:
            print("================ FINAL URLS ================")
            for t in tickers:
                row = data_by_ticker.get(t)
                print(f"[{t}]")
                print(f"PDF: {row['pdf_url']}")
                print(f"HTML: {row['html_url']}")
                print(f"Audio: {row['audio_url']}")
                print("---")
            break
        
        time.sleep(10)

if __name__ == "__main__":
    check_all()
