
import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("c:/Users/Administrator/Documents/kasonaops/presentation/.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

SA_TICKERS = [
    "ADDT-B.ST", "ARENIT.ST", "ASKER.ST", "ASPO.HE", "BERG-B.ST",
    "BNZL.LSE", "BOREO.HE", "BRK-B.US", "BRO.US", "CSU.TO",
    "DHR.US", "HLMA.LSE", "IMCD.AS", "INDT.ST", "LAGR-B.ST",
    "LIFCO-B.ST", "MMGR-B.ST", "QXO.US", "ROKO-B.ST", "ROP.US",
    "SFT.LSE", "VIT-B.ST"
]

PEP_TICKERS = [
    "1SXP.DE", "BANB.SW", "DESN.SW", "HIMS.US", "LLY.US",
    "MEDP.US", "NOVO-B.CO", "PPGN.SW", "ROVI.MC", "STVN.US",
    "WST.US", "YPSN.SW", "ZEAL.CO"
]

ALL_WATCHLIST = SA_TICKERS + PEP_TICKERS

res = supabase.table("company_presentation").select("ticker_eod").execute()
db_tickers = set([r['ticker_eod'] for r in res.data])

missing = [t for t in ALL_WATCHLIST if t not in db_tickers]
print(f"Missing tickers: {missing}")
