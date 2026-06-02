import os
import json
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("Error: Missing environment variables.")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS_DATA = {
    "ISRG.US": r"C:\Users\Administrator\.gemini\antigravity\brain\597de06b-f91a-47c9-b1c7-1d6f6c739d73\.system_generated\steps\137\output.txt",
    "NVO.US": r"C:\Users\Administrator\.gemini\antigravity\brain\597de06b-f91a-47c9-b1c7-1d6f6c739d73\.system_generated\steps\138\output.txt",
    "ROG.SW": r"C:\Users\Administrator\.gemini\antigravity\brain\597de06b-f91a-47c9-b1c7-1d6f6c739d73\.system_generated\steps\139\output.txt",
    "ZTS.US": r"C:\Users\Administrator\.gemini\antigravity\brain\597de06b-f91a-47c9-b1c7-1d6f6c739d73\.system_generated\steps\140\output.txt"
}

def main():
    for ticker, filepath in TICKERS_DATA.items():
        print(f"Processing {ticker} from {filepath}...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
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
