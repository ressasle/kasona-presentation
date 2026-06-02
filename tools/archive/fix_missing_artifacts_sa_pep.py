#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_missing_artifacts_sa_pep.py
================================
Fixes all missing markdown_content and pdf_url in company_presentation
for portfolios 991001-SA and 991001-PEP.

Runs: generate_ticker_artifacts.py for each incomplete ticker.
"""

import os
import sys
import time
import subprocess
from supabase import create_client
from dotenv import load_dotenv

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("[ERROR] Missing Supabase credentials!")
    sys.exit(1)

supabase = create_client(url, key)

# All tickers in 991001-SA and 991001-PEP (public stocks only)
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

ALL_TICKERS = SA_TICKERS + PEP_TICKERS


def get_missing_tickers():
    """Query company_presentation to find tickers with missing markdown or PDF."""
    print("\n[*] Checking company_presentation for missing artifacts...")

    res = supabase.table("company_presentation") \
        .select("ticker_eod, markdown_content_de, pdf_url_de, audio_url_de") \
        .in_("ticker_eod", ALL_TICKERS) \
        .execute()

    existing = {row["ticker_eod"]: row for row in res.data}

    missing_markdown = []
    missing_pdf = []
    missing_audio = []
    all_incomplete = set()

    for ticker in ALL_TICKERS:
        row = existing.get(ticker)
        if not row:
            print(f"  [WARN] {ticker} -- NOT FOUND in company_presentation")
            all_incomplete.add(ticker)
            continue

        md = row.get("markdown_content_de") or ""
        pdf = row.get("pdf_url_de") or ""
        audio = row.get("audio_url_de") or ""

        needs_work = False
        if len(str(md).strip()) < 20:
            missing_markdown.append(ticker)
            needs_work = True
        if len(str(pdf).strip()) < 5:
            missing_pdf.append(ticker)
            needs_work = True
        if len(str(audio).strip()) < 5:
            missing_audio.append(ticker)
            needs_work = True

        if needs_work:
            all_incomplete.add(ticker)

    print(f"\n[SUMMARY]")
    print(f"   Missing markdown : {len(missing_markdown)} tickers")
    print(f"   Missing PDF      : {len(missing_pdf)} tickers")
    print(f"   Missing audio    : {len(missing_audio)} tickers")
    print(f"   Total to fix     : {len(all_incomplete)} tickers")

    if missing_markdown:
        print(f"\n   No markdown : {', '.join(sorted(missing_markdown))}")
    if missing_pdf:
        print(f"   No PDF      : {', '.join(sorted(missing_pdf))}")
    if missing_audio:
        print(f"   No audio    : {', '.join(sorted(missing_audio))}")

    return sorted(all_incomplete)


def run_artifact_generation(ticker):
    """Run generate_ticker_artifacts.py for a single ticker."""
    print(f"\n{'='*60}")
    print(f"  [RUN] Generating artifacts for: {ticker}")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        "tools/generate_ticker_artifacts.py",
        "--ticker", ticker
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"  [OK] SUCCESS: {ticker}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] FAILED: {ticker} -- {e}")
        return False


def main():
    print("=" * 60)
    print("  KASONA -- Missing Artifact Fixer (SA + PEP Portfolios)")
    print("=" * 60)

    targets = get_missing_tickers()

    if not targets:
        print("\n[OK] All tickers have complete artifacts. Nothing to do!")
        return

    print(f"\n[TARGET] Will process {len(targets)} tickers: {', '.join(targets)}")
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    succeeded = []
    failed = []

    for i, ticker in enumerate(targets):
        print(f"\n[{i+1}/{len(targets)}] Processing {ticker}...")
        ok = run_artifact_generation(ticker)

        if ok:
            succeeded.append(ticker)
        else:
            failed.append(ticker)

        # Rate limit delay between tickers (except last)
        if i < len(targets) - 1:
            print(f"  [WAIT] 10s before next ticker...")
            time.sleep(10)

    # Final report
    print(f"\n{'='*60}")
    print(f"  DONE! Results:")
    print(f"  Succeeded : {len(succeeded)} -- {', '.join(succeeded)}")
    if failed:
        print(f"  Failed    : {len(failed)} -- {', '.join(failed)}")
    print(f"{'='*60}")

    # Final DB check
    print("\n[*] Final DB verification...")
    res = supabase.table("company_presentation") \
        .select("ticker_eod, markdown_content_de, pdf_url_de, audio_url_de") \
        .in_("ticker_eod", ALL_TICKERS) \
        .execute()

    still_incomplete = []
    for row in res.data:
        md = row.get("markdown_content_de") or ""
        pdf = row.get("pdf_url_de") or ""
        if len(str(md).strip()) < 20 or len(str(pdf).strip()) < 5:
            still_incomplete.append(row["ticker_eod"])

    if still_incomplete:
        print(f"  [WARN] Still incomplete: {', '.join(still_incomplete)}")
    else:
        print("  [OK] All tickers now have complete artifacts!")


if __name__ == "__main__":
    main()
