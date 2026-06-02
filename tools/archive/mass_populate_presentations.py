"""
mass_populate_presentations.py — Batch Orchestrator for Kasona Research
========================================================================
Scales the new-company-presentation.py pipeline across multiple tickers.
Processes in batches to manage API limits and provides resume capability.
"""

import os
import sys
import time
import json
import argparse
from typing import List, Dict

# Import the core pipeline components from the main script
# Ensure the path is correct for importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib
pipeline_mod = importlib.import_module("new-company-presentation")

# Watchlist for Portfolio ID: 991001-SA
WATCHLIST = [
    {"name": "Addtech", "ticker": "ADDT-B.ST"},
    {"name": "Arenite Group", "ticker": "ARENIT"},
    {"name": "Asker Healthcare Group", "ticker": "ASKER"},
    {"name": "Aspo Oyj", "ticker": "ASPO.HE"},
    {"name": "Bergman & Beving", "ticker": "BERG-B.ST"},
    {"name": "Berkshire Hathaway", "ticker": "BRK-B.US"},
    {"name": "Boreo Oyj", "ticker": "BOREO.HE"},
    {"name": "Brown & Brown Inc.", "ticker": "BRO.US"},
    {"name": "Bunzl plc", "ticker": "BNZL.LSE"},
    {"name": "Constellation Software", "ticker": "CSU.TO"},
    {"name": "Danaher Corp", "ticker": "DHR.US"},
    {"name": "Halma plc", "ticker": "HLMA.LSE"},
    {"name": "IMCD N.V.", "ticker": "IMCD.AS"},
    {"name": "Indutrade", "ticker": "INDT.ST"},
    {"name": "Lagercrantz Group", "ticker": "LAGR-B.ST"},
    {"name": "Lifco", "ticker": "LIFCO-B.ST"},
    {"name": "Momentum Group", "ticker": "MMGR-B.ST"},
    {"name": "QXO Inc", "ticker": "QXO.US"},
    {"name": "Röko AB", "ticker": "ROKO-B.ST"},
    {"name": "Roper Technologies", "ticker": "ROP.US"},
    {"name": "Software Circle", "ticker": "SFT.LSE"},
    {"name": "Vitec Software Group", "ticker": "VIT-B.ST"}
]

STATE_FILE = "mass_population_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"completed": [], "failed": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Mass Populate Company Presentations")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of tickers to process in this run")
    parser.add_argument("--delay", type=int, default=30, help="Delay in seconds between companies")
    parser.add_argument("--force", action="store_true", help="Re-process completed tickers")
    args = parser.parse_args()

    state = load_state()
    
    # Load config from environment
    config = {
        "apify_key":      os.environ.get("APIFY_API_KEY", ""),
        "gemini_key":     os.environ.get("GOOGLE_GEMINI_API_KEY", ""),
        "openrouter_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "openai_key":     os.environ.get("OPENAI_API_KEY", ""),
        "supabase_url":   os.environ.get("SUPABASE_URL", ""),
        "supabase_key":   os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        "eodhd_key":      os.environ.get("EODHD_API_KEY", ""),
    }

    # Initialize Supabase
    supabase_client = pipeline_mod.create_client(config["supabase_url"], config["supabase_key"])

    to_process = []
    for item in WATCHLIST:
        if args.force or (item["ticker"] not in state["completed"] and item["ticker"] not in state["failed"]):
            to_process.append(item)

    print(f"\n[ORCHESTRATOR] Found {len(to_process)} tickers pending.")
    batch = to_process[:args.batch_size]
    print(f"[ORCHESTRATOR] Starting batch of {len(batch)}...\n")

    for i, item in enumerate(batch):
        ticker = item["ticker"]
        name = item["name"]
        
        print(f"\n{'='*80}")
        print(f" PROCESSING {i+1}/{len(batch)}: {name} ({ticker})")
        print(f"{'='*80}\n")

        try:
            # Run the pipeline
            results = pipeline_mod.run_pipeline(name, ticker, config)
            
            # Sync to Supabase
            pipeline_mod.sync_to_supabase(ticker, results, supabase_client)
            pipeline_mod.push_to_master_index(ticker, results, supabase_client)
            
            state["completed"].append(ticker)
            print(f"\n[SUCCESS] Completed {ticker}")
            
        except Exception as e:
            print(f"\n[ERROR] Failed to process {ticker}: {e}")
            state["failed"].append(ticker)
        
        save_state(state)
        
        if i < len(batch) - 1:
            print(f"\n[WAIT] Sleeping for {args.delay}s to manage rate limits...")
            time.sleep(args.delay)

    print(f"\n[DONE] Batch complete. Current state: {len(state['completed'])} total successes.")

if __name__ == "__main__":
    main()
