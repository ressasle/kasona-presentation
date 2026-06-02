import os
import subprocess
from supabase import create_client
from dotenv import load_dotenv

def remediate_portfolio():
    # Load .env relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.dirname(script_dir)
    env_path = os.path.join(res_dir, ".env")
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    res = supabase.table("company_presentation").select("ticker_eod").execute()
    tickers = [r['ticker_eod'] for r in res.data]
    
    print(f"[*] Starting full portfolio remediation for {len(tickers)} assets...")
    
    for ticker in tickers:
        print(f"\n{'-'*30}\n[*] Remediating {ticker}...")
        try:
            # We run the remediate_all_pillars.py for each ticker
            # Use absolute path for python tool
            remediate_script = os.path.join(script_dir, "remediate_all_pillars.py")
            subprocess.run(["python", remediate_script, ticker], check=True)
        except Exception as e:
            print(f"[ERR] Failed to remediate {ticker}: {e}")

if __name__ == "__main__":
    remediate_portfolio()
