
import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load env
env_path = "c:/Users/Administrator/Documents/kasonaops/presentation/.env"
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Watchlist tickers
sa_tickers = [
    "ADDT-B.ST", "ARENIT.ST", "ASKER.ST", "ASPO.HE", "BERG-B.ST", "BNZL.LSE",
    "BOREO.HE", "BRK-B.US", "BRO.US", "CSU.TO", "DHR.US", "HLMA.LSE",
    "IMCD.AS", "INDT.ST", "LAGR-B.ST", "LIFCO-B.ST", "MMGR-B.ST", "QXO.US",
    "ROKO-B.ST", "ROP.US", "SFT.LSE", "VIT-B.ST"
]

pep_tickers = [
    "1SXP.DE", "BANB.SW", "DESN.SW", "HIMS.US", "LLY.US", "MEDP.US",
    "NOVO-B.CO", "PPGN.SW", "ROVI.MC", "STVN.US", "WST.US", "YPSN.SW", "ZEAL.CO"
]

all_watchlist_tickers = sa_tickers + pep_tickers

# Get data from DB
res = supabase.table("company_presentation").select("ticker_eod, markdown_content, pdf_url, audio_url").execute()
db_data = {r["ticker_eod"]: r for r in res.data}

results = []
for ticker in all_watchlist_tickers:
    if ticker not in db_data:
        results.append({"ticker": ticker, "status": "Missing from Table"})
    else:
        row = db_data[ticker]
        missing_fields = []
        if not row.get("markdown_content"): missing_fields.append("markdown_content")
        if not row.get("pdf_url"): missing_fields.append("pdf_url")
        if not row.get("audio_url"): missing_fields.append("audio_url")
        
        if missing_fields:
            results.append({"ticker": ticker, "status": "In Table, missing: " + ", ".join(missing_fields)})

print(json.dumps(results, indent=2))
