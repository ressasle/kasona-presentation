import os
import subprocess
import time
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0, help="Starting index")
    parser.add_argument("--count", type=int, default=5, help="Number of tickers to process")
    args = parser.parse_args()

    tickers = [
        "1SXP.DE", "ADDT-B.ST", "ARENIT.ST", "ASKER.ST", "ASPO.HE", "BANB.SW", "BERG-B.ST", 
        "BNZL.LSE", "BOREO.HE", "BRK-B.US", "BRO.US", "CSU.TO", "DESN.SW", "DHR.US", 
        "HIMS.US", "HLMA.LSE", "IMCD.AS", "INDT.ST", "LAGR-B.ST", "LIFCO-B.ST", "LLY.US", 
        "MEDP.US", "MMGR-B.ST", "NOVO-B.CO", "PPGN.SW", "QXO.US", "ROKO-B.ST", "ROP.US", 
        "ROVI.MC", "SFT.LSE", "STVN.US", "VIT-B.ST", "WST.US", "YPSN.SW", "ZEAL.CO"
    ]
    
    batch = tickers[args.start : args.start + args.count]
    
    print(f"Starting batch German artifact generation for {len(batch)} tickers (Index {args.start} to {args.start + args.count - 1})...")
    
    success_count = 0
    fail_count = 0
    
    for i, ticker in enumerate(batch):
        print(f"\n[{i+1}/{len(batch)}] Generating artifacts for {ticker}...")
        
        cmd = [
            "python", "tools/generate_german_artifacts.py",
            "--ticker", ticker
        ]
        
        try:
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                print(f"[SUCCESS] {ticker} artifacts generated and uploaded.")
                success_count += 1
            else:
                print(f"[ERROR] Failed for {ticker}. Check logs.")
                print("STDOUT:", process.stdout[-500:])
                print("STDERR:", process.stderr[-500:])
                fail_count += 1
                
        except Exception as e:
            print(f"[ERROR] Exception running {ticker}: {e}")
            fail_count += 1
            
        time.sleep(2)
        
    print("\n" + "="*40)
    print(f"BATCH PROCESSING COMPLETE (Start: {args.start})")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print("="*40)

if __name__ == "__main__":
    main()
