
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

# Watchlist tickers from fix_missing_artifacts_sa_pep.py
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

# Get tickers from DB
res = supabase.table("company_presentation").select("ticker_eod").execute()
db_tickers = [r["ticker_eod"] for r in res.data]

missing = [t for t in all_watchlist_tickers if t not in db_tickers]

print(json.dumps({
    "missing": missing,
    "total_watchlist": len(all_watchlist_tickers),
    "total_db": len(db_tickers)
}, indent=2))
