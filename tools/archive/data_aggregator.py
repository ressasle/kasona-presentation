#!/usr/bin/env python3
"""
data_aggregator.py — Gathers data for Kasona Company Presentation

Fetches:
- Financial fundamentals (EODHD)
- Executive and Board data (EODHD)
- Recent news and sentiment (EODHD)
- Qualitative context (Web Search)

Outputs a structured JSON and a draft Markdown narrative.
"""

import os
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()
EODHD_API_KEY = os.getenv("EODHD_API_KEY")

class DataAggregator:
    def __init__(self, ticker):
        self.ticker = ticker
        self.data = {
            "fundamentals": {},
            "sentiment": {},
            "qualitative": {},
        }

    def fetch_fundamentals(self):
        """Fetch general company fundamentals from EODHD."""
        print(f"[*] Fetching fundamentals for {self.ticker}...")
        url = f"https://eodhistoricaldata.com/api/fundamentals/{self.ticker}?api_token={EODHD_API_KEY}&fmt=json"
        response = requests.get(url)
        if response.status_code == 200:
            self.data["fundamentals"] = response.json()
            print("[OK] Fundamentals fetched.")
        else:
            print(f"[ERR] Failed to fetch fundamentals: {response.status_code}")

    def fetch_sentiment(self):
        """Fetch recent sentiment for the ticker."""
        print(f"[*] Fetching sentiment for {self.ticker}...")
        url = f"https://eodhistoricaldata.com/api/sentiments?s={self.ticker}&api_token={EODHD_API_KEY}&fmt=json"
        response = requests.get(url)
        if response.status_code == 200:
            self.data["sentiment"] = response.json()
            print("[OK] Sentiment fetched.")
        else:
            print(f"[ERR] Failed to fetch sentiment: {response.status_code}")

    def save_data(self, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)
        print(f"[OK] Raw data saved to {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--output", default="data.json")
    args = parser.parse_args()
    
    agg = DataAggregator(args.ticker)
    agg.fetch_fundamentals()
    agg.fetch_sentiment()
    agg.save_data(args.output)

if __name__ == "__main__":
    main()
