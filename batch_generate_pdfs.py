import os
import subprocess
from pathlib import Path

def main():
    md_files = [f for f in os.listdir('.') if f.endswith('_presentation.md')]
    
    for md_file in md_files:
        # Extract ticker from filename: ROP_US_presentation.md -> ROP.US
        ticker_part = md_file.replace('_presentation.md', '')
        # Handle cases like BERG_B_ST -> BERG-B.ST or similar if needed
        # But let's assume simple replacement for now, 
        # or use the original tickers if we had them.
        # Actually, it's safer to just run the script.
        
        # Mapping back to ticker format (robust)
        ticker = ticker_part.replace('_', '.')
        
        # Explicit corrections for known tricky symbols
        corrections = {
            'ADDT.B.ST': 'ADDT-B.ST',
            'BERG.B.ST': 'BERG-B.ST',
            'LAGR.B.ST': 'LAGR-B.ST',
            'BRK.B.US': 'BRK-B.US',
            'PRIVATE.STRIPE': 'PRIVATE.STRIPE'
        }
        if ticker in corrections:
            ticker = corrections[ticker]
        
        # Heuristic: if it ends with .ST or .HE and had a _B_ it likely needs a dash
        if (ticker.endswith('.ST') or ticker.endswith('.HE')) and '.B.' in ticker:
            ticker = ticker.replace('.B.', '-B.')
        
        print(f"Generating PDF for {ticker} using {md_file}...")
        
        cmd = [
            "python", "tools/generate_presentation_pdf.py",
            md_file,
            "--ticker", ticker
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Successfully generated PDF for {ticker}")
            else:
                print(f"Failed for {ticker}: {result.stderr}")
        except Exception as e:
            print(f"Error for {ticker}: {e}")

if __name__ == "__main__":
    main()
