import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def update_ticker_pillars(ticker, pillars):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("[ERROR] Supabase credentials missing.")
        return

    supabase = create_client(url, key)
    
    try:
        res = supabase.table("company_presentation").update(pillars).eq("ticker_eod", ticker).execute()
        print(f"[SUCCESS] Updated pillars for {ticker}")
        return res
    except Exception as e:
        print(f"[ERROR] Failed to update {ticker}: {e}")

if __name__ == "__main__":
    # Example usage for manual remediation
    ticker = "ROP.US"
    pillars = {
        "bull-case": "1. Multi-Industry Dominance: Roper operates a diversified portfolio of hyper-niche VMS and medical businesses with high market share and recurring revenue.\n2. Asset-Light Compounder: Exceptional free cash flow conversion and low CapEx requirements allow for continuous disciplined bolt-on acquisitions.\n3. Defensive Moat: Its mission-critical software solutions are integrated into healthcare, water, and legal workflows with high switching costs.",
        "bear-case": "1. Acquisition Multiple Inflation: As private equity competition increases, Roper may face pressure to pay higher multiples for quality assets, potentially diluting ROIC.\n2. Organic Growth Limits: The niche nature of their subsidiaries sometimes limits total addressable market (TAM) expansion, making the company reliant on continuous M&A.\n3. Integration & Decentralization Risk: Managing a vast decentralized network requires robust oversight to prevent operational slippage across business units.",
        "rivalry": "Low: Most subsidiaries operate in niche silos where there are few direct institutional competitors.",
        "supplier-power": "Low: Diverse supply base with no single critical vendor dependency.",
        "buyer-power": "Low: High switching costs for mission-critical VMS platforms.",
        "threat-of-entry": "Low: Significant intellectual property and customer integration barriers.",
        "substitutes": "Low: Specific vertical solutions lack close substitutes."
    }
    update_ticker_pillars(ticker, pillars)
