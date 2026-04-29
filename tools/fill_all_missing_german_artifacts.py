import os
import sys
import time
import subprocess
from supabase import create_client
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Missing Supabase credentials!")
    sys.exit(1)

supabase = create_client(url, key)

def main():
    print("Checking for missing German artifacts (markdown_content_de IS NULL OR length < 20)...")
    res = supabase.table("company_presentation").select("ticker_eod, markdown_content_de, pdf_url_de, audio_url_de").execute()
    
    targets = []
    if res.data:
        for row in res.data:
            # We check if markdown, pdf, or audio is missing. Since user asked to fill all gaps.
            md_miss = not row.get("markdown_content_de") or len(str(row.get("markdown_content_de"))) < 20
            pdf_miss = not row.get("pdf_url_de") or len(str(row.get("pdf_url_de"))) < 5
            audio_miss = not row.get("audio_url_de") or len(str(row.get("audio_url_de"))) < 5
            
            if md_miss or pdf_miss or audio_miss:
                targets.append(row["ticker_eod"])

    print(f"Found {len(targets)} tickers requiring German artifact generation.")
    
    for i, ticker in enumerate(targets):
        print(f"\n[{i+1}/{len(targets)}] Generating German Artifacts for {ticker}...")
        try:
            cmd = ["python", "tools/generate_german_artifacts.py", "--ticker", ticker]
            subprocess.run(cmd, check=True)
            print(f"  [SUCCESS] {ticker} generated.")
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Failed to generate for {ticker}: {e}")
        
        # Slight cooling down to prevent rate limits
        time.sleep(2)

if __name__ == "__main__":
    main()
