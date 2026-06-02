import os
from supabase import create_client
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

def check_files():
    # 1. Get tickers from DB
    res = supabase.table("company_presentation").select("ticker_eod").execute()
    db_tickers = sorted(list(set([r['ticker_eod'] for r in res.data if r['ticker_eod']])))
    
    # 2. Get files from root and output/
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(root_dir, "output")
    
    files = os.listdir(root_dir)
    if os.path.exists(output_dir):
        files += [f"output/{f}" for f in os.listdir(output_dir)]
    
    # Extract just the filename for matching, but keep the path for verification if needed
    # Actually, the logic below expects filenames. Let's keep it simple.
    presentation_files = []
    for f in os.listdir(root_dir):
        if f.endswith("_presentation.md") or f.endswith("_presentation.pdf"):
            presentation_files.append(f)
            
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
             if f.endswith("_presentation.md") or f.endswith("_presentation.pdf"):
                 presentation_files.append(f)
    
    print(f"Tickers in DB: {len(db_tickers)}")
    print(f"Presentation files found: {len(presentation_files)}")
    
    # Map db tickers to expected filenames (replacing . and - with _)
    db_to_filename = {}
    for t in db_tickers:
        # Standardize: replace both . and - with _
        base = t.replace(".", "_").replace("-", "_").upper()
        db_to_filename[t] = {
            "md": f"{base}_presentation.md",
            "pdf": f"{base}_presentation.pdf"
        }
    
    # Case-insensitive mapping of existing files
    lower_files = {f.lower(): f for f in presentation_files}
    actual_files_set = set(presentation_files)
    
    mismatches = []
    missing_files = []
    found_files = set()
    
    expected_files_set = set()
    for t, names in db_to_filename.items():
        for ext in ['md', 'pdf']:
            expected = names[ext]
            expected_files_set.add(expected)
            
            if expected in actual_files_set:
                found_files.add(expected)
            elif expected.lower() in lower_files:
                mismatches.append((expected, lower_files[expected.lower()]))
                found_files.add(lower_files[expected.lower()])
            else:
                missing_files.append((t, expected))
                
    extra_files = [f for f in presentation_files if f not in found_files]
    
    # Categorize extra files
    lowercase_extras = []
    dash_extras = []
    localized_extras = []
    other_extras = []
    
    for f in extra_files:
        if f != f.upper() and any(c.islower() for c in f):
            lowercase_extras.append(f)
        elif "-" in f:
            dash_extras.append(f)
        elif "_de_presentation" in f:
            localized_extras.append(f)
        else:
            other_extras.append(f)

    print("\n--- CASE MISMATCHES (Expected vs Actual) ---")
    if not mismatches:
        print("None")
    for expected, actual in sorted(mismatches):
        print(f"EX: {expected} | AC: {actual}")
        
    print("\n--- MISSING FILES (Expected but not found) ---")
    if not missing_files:
        print("None")
    for t, m in sorted(missing_files):
        print(f"{m} (Ticker: {t})")
        
    print("\n--- EXTRA FILES: LOWERCASE ---")
    for f in sorted(lowercase_extras):
        print(f)

    print("\n--- EXTRA FILES: CONTAINS DASHES ---")
    for f in sorted(dash_extras):
        print(f)

    print("\n--- EXTRA FILES: LOCALIZED (DE) ---")
    for f in sorted(localized_extras):
        print(f)

    print("\n--- EXTRA FILES: OTHERS (Potential Duplicates or Old Suffixes) ---")
    for f in sorted(other_extras):
        print(f)

if __name__ == "__main__":
    check_files()
