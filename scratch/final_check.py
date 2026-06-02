
import os
from supabase import create_client
from dotenv import load_dotenv

# Load env
env_path = "c:/Users/Administrator/Documents/kasonaops/presentation/.env"
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

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

all_watchlist = set(sa_tickers + pep_tickers)

res = supabase.table("company_presentation").select("ticker_eod").execute()
db_tickers = set(r["ticker_eod"] for r in res.data)

missing = all_watchlist - db_tickers
print(f"Missing from table: {missing}")
