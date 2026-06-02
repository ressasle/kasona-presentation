import os
from dotenv import load_dotenv
from supabase import create_client

def check():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
    if not url or not key:
        print("Missing env")
        return
    supabase = create_client(url, key)
    tickers = ['ADDT-B.ST', 'BERG-B.ST', 'BOREO.HE', 'DHR.US', 'PRIVATE.STRIPE', 'QXO.US']
    r = supabase.table('company_presentation').select('ticker_eod, description, \"n8n-info\"').in_('ticker_eod', tickers).execute()
    for row in r.data:
        has_info = row.get('n8n-info') is not None
        has_desc = row.get('description') is not None
        print(f"{row['ticker_eod']}: info={has_info}, desc={has_desc}")

if __name__ == "__main__":
    check()
