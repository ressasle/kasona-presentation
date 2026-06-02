import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(url, key)
    
    res = supabase.table('company_presentation').select('ticker_eod').execute()
    tickers = [r['ticker_eod'] for r in res.data]
    print(f"Tickers in DB: {tickers}")

if __name__ == "__main__":
    main()
