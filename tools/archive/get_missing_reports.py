import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        return
        
    supabase = create_client(url, key)
    
    # Query for all companies where l4_report is NULL
    res = supabase.table('company_presentation').select('ticker_eod, company_name').is_('l4_report', 'null').execute()
    
    missing = res.data
    print(f"Total companies with missing l4_report: {len(missing)}")
    
    for i, item in enumerate(missing[:20]):  # Print first 20
        print(f"{i+1}. {item['ticker_eod']} - {item['company_name']}")
        
    if len(missing) > 20:
        print("...")

if __name__ == "__main__":
    main()
