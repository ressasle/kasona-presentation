import os
import subprocess

TICKERS = [
    "AI.PA", "BCHN.SW", "BTC-USD.CC", "COIN.US", "D05.SI", "ETH-USD.CC", 
    "HOOD.US", "MA.US", "SOL-USD.CC", "SPGI.US", "SREN.SW", "TT.US"
]

def main():
    for ticker in TICKERS:
        print(f"Starting pipeline for {ticker}...")
        try:
            subprocess.run(["python", "tools/generate_ticker_artifacts.py", "--ticker", ticker], check=True)
            print(f"Finished pipeline for {ticker}.")
        except Exception as e:
            print(f"Error on {ticker}: {e}")

if __name__ == "__main__":
    main()
