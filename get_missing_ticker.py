import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        print("Missing env")
        return
    
    supabase = create_client(url, key)
    
    # Get portfolio assets
    # Trying to find assets that might be in a "99-SA" portfolio or equivalent
    # We'll just get all tickers from kasona_portfolio_assets first
    res_assets = supabase.table('kasona_portfolio_assets').select('ticker').execute()
    portfolio_tickers = set(r['ticker'] for r in res_assets.data if r.get('ticker'))
    
    # Get existing presentations
    res_pres = supabase.table('company_presentation').select('ticker_eod').execute()
    existing_tickers = set(r['ticker_eod'] for r in res_pres.data if r.get('ticker_eod'))
    
    missing = portfolio_tickers - existing_tickers
    
    print(f"Total Portfolio Tickers: {len(portfolio_tickers)}")
    print(f"Existing in Presentation: {len(existing_tickers)}")
    print(f"Missing Tickers: {list(missing)[:10]}")
    
    if missing:
        # Choose the first one
        target = sorted(list(missing))[0]
        print(f"TARGET_TICKER:{target}")
    else:
        print("NO_MISSING_TICKERS")

if __name__ == "__main__":
    main()
