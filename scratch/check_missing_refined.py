
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
# Using columns from the fix script: markdown_content_de, pdf_url_de, audio_url_de
res = supabase.table("company_presentation").select("ticker_eod, markdown_content_de, pdf_url_de, audio_url_de").execute()
db_data = {r["ticker_eod"]: r for r in res.data}

missing_from_table = []
missing_artifacts = []

for ticker in all_watchlist_tickers:
    if ticker not in db_data:
        missing_from_table.append(ticker)
    else:
        row = db_data[ticker]
        md = row.get("markdown_content_de") or ""
        pdf = row.get("pdf_url_de") or ""
        audio = row.get("audio_url_de") or ""
        
        needs_work = False
        missing_fields = []
        if len(str(md).strip()) < 20:
            missing_fields.append("markdown_content_de")
            needs_work = True
        if len(str(pdf).strip()) < 5:
            missing_fields.append("pdf_url_de")
            needs_work = True
        if len(str(audio).strip()) < 5:
            missing_fields.append("audio_url_de")
            needs_work = True
            
        if needs_work:
            missing_artifacts.append({"ticker": ticker, "missing": missing_fields})

print(json.dumps({
    "missing_from_table": missing_from_table,
    "missing_artifacts": missing_artifacts
}, indent=2))
