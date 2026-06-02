import os
from dotenv import load_dotenv
from supabase import create_client

def main():
    load_dotenv(".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    print("Fetching company_presentation records...")
    res = supabase.table("company_presentation").select("ticker_eod", "bull-case", "bear-case").execute()
    data = res.data
    
    print("\nSAMPLE OF CLEANED RESULTS:\n" + "="*50)
    for row in data[:5]:
        ticker = row.get("ticker_eod")
        bull = str(row.get("bull-case", ""))
        bear = str(row.get("bear-case", ""))
        
        print(f"\n[{ticker}]")
        print("BULL-CASE:")
        print(bull[:200] + "..." if len(bull) > 200 else bull)
        print("\nBEAR-CASE:")
        print(bear[:200] + "..." if len(bear) > 200 else bear)
        print("-" * 50)
        
if __name__ == "__main__":
    main()
