import os
import json
import requests
from supabase import create_client
from dotenv import load_dotenv

# Load env
env_path = "c:/Users/Administrator/Documents/kasonaops/presentation/.env"
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
eodhd_token = os.getenv("EODHD_API_TOKEN") or os.getenv("EODHD_API_KEY")

supabase = create_client(supabase_url, supabase_key)

# Get the tickers we are interested in
portfolio_ids = ['991001-SA', '991001-PEP', '991001-SA-EN', '991001-PEP-EN']
res = supabase.table("kasona_portfolio_assets").select("*").in_("portfolio_id", portfolio_ids).execute()
assets = res.data

# Get company presentations
res_cp = supabase.table("company_presentation").select("ticker_eod, company_name, description, officers").in_("ticker_eod", [a['ticker_eod'] for a in assets]).execute()
cp_map = {r['ticker_eod']: r for r in res_cp.data}

def is_empty(val):
    return val is None or str(val).strip() == "" or val == {} or val == []

filled_summary = []
missing_summary = []

unique_tickers = list(set([a['ticker_eod'] for a in assets if a['ticker_eod']]))

for ticker in unique_tickers:
    # Check if we need to fetch EODHD
    asset_rows = [a for a in assets if a['ticker_eod'] == ticker]
    cp_row = cp_map.get(ticker, {})
    
    needs_fetch = False
    for a in asset_rows:
        for col in ['stock_name', 'exchange', 'country', 'sector', 'industry', 'description', 'currency', 'isin', 'website_url', 'logo_url', 'fiscal_year_end', 'officers']:
            if is_empty(a.get(col)):
                needs_fetch = True
                break
    
    for col in ['company_name', 'description', 'officers']:
        if is_empty(cp_row.get(col)):
            needs_fetch = True
            break
            
    if not needs_fetch:
        continue
        
    # Fetch from EODHD
    print(f"Fetching {ticker} from EODHD...")
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={eodhd_token}&fmt=json"
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Failed to fetch {ticker}")
        continue
        
    data = resp.json()
    gen = data.get("General", {})
    
    # EODHD values
    e_officers = gen.get("Officers", {})
    if e_officers:
        # Convert EODHD officers format to list of dicts if it's a dict
        if isinstance(e_officers, dict):
            e_officers = list(e_officers.values())
            
    e_isin = gen.get("ISIN")
    e_logo = gen.get("LogoURL")
    if e_logo and e_logo.startswith("/"):
        e_logo = "https://eodhd.com" + e_logo
    e_sector = gen.get("Sector")
    e_industry = gen.get("Industry")
    e_desc = gen.get("Description")
    e_currency = gen.get("CurrencyCode")
    e_web = gen.get("WebURL")
    e_country = gen.get("CountryName")
    e_exchange = gen.get("Exchange")
    e_name = gen.get("Name")
    e_fye = gen.get("FiscalYearEnd")
    
    # Update kasona_portfolio_assets
    filled_cols_asset = []
    missing_cols_asset = []
    
    # We update all rows for this ticker
    for a in asset_rows:
        updates = {}
        if is_empty(a.get('officers')) and not is_empty(e_officers): updates['officers'] = e_officers
        if is_empty(a.get('isin')) and not is_empty(e_isin): updates['isin'] = e_isin
        if is_empty(a.get('logo_url')) and not is_empty(e_logo): updates['logo_url'] = e_logo
        if is_empty(a.get('sector')) and not is_empty(e_sector): updates['sector'] = e_sector
        if is_empty(a.get('industry')) and not is_empty(e_industry): updates['industry'] = e_industry
        if is_empty(a.get('description')) and not is_empty(e_desc): updates['description'] = e_desc
        if is_empty(a.get('currency')) and not is_empty(e_currency): updates['currency'] = e_currency
        if is_empty(a.get('website_url')) and not is_empty(e_web): updates['website_url'] = e_web
        if is_empty(a.get('fiscal_year_end')) and not is_empty(e_fye): updates['fiscal_year_end'] = e_fye
        
        if updates:
            supabase.table("kasona_portfolio_assets").update(updates).eq("id", a["id"]).execute()
            filled_cols_asset.extend(updates.keys())
            
        # Re-check what is still missing
        for col in ['stock_name', 'exchange', 'country', 'sector', 'industry', 'description', 'currency', 'isin', 'website_url', 'logo_url', 'fiscal_year_end', 'officers']:
            if is_empty(a.get(col)) and col not in updates:
                missing_cols_asset.append(col)
                
    # Update company_presentation
    filled_cols_cp = []
    missing_cols_cp = []
    if cp_row:
        updates_cp = {}
        if is_empty(cp_row.get('company_name')) and not is_empty(e_name): updates_cp['company_name'] = e_name
        if is_empty(cp_row.get('description')) and not is_empty(e_desc): updates_cp['description'] = e_desc
        if is_empty(cp_row.get('officers')) and not is_empty(e_officers): updates_cp['officers'] = e_officers
        
        if updates_cp:
            supabase.table("company_presentation").update(updates_cp).eq("ticker_eod", ticker).execute()
            filled_cols_cp.extend(updates_cp.keys())
            
        for col in ['company_name', 'description', 'officers']:
            if is_empty(cp_row.get(col)) and col not in updates_cp:
                missing_cols_cp.append(col)
                
    filled_cols = list(set(filled_cols_asset + filled_cols_cp))
    missing_cols = list(set(missing_cols_asset + missing_cols_cp))
    
    if filled_cols:
        filled_summary.append(f"{ticker}: Filled {', '.join(filled_cols)}")
    if missing_cols:
        missing_summary.append(f"{ticker}: Still missing {', '.join(missing_cols)}")

print("=== FILLED ===")
for f in filled_summary: print(f)
print("\n=== STILL MISSING ===")
for m in missing_summary: print(m)
