import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def inspect_columns():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("[ERROR] Supabase credentials missing.")
        return

    supabase = create_client(url, key)
    
    try:
        # Fetch one row to see keys
        res = supabase.table("company_presentation").select("*").limit(1).execute()
        if res.data:
            print(f"Columns in public.company_presentation: {list(res.data[0].keys())}")
        else:
            print("No data found in table.")
    except Exception as e:
        print(f"[ERROR] Failed to inspect: {e}")

if __name__ == "__main__":
    inspect_columns()
