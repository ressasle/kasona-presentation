import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(url, key)
    
    columns = ['investment_thesis_de', 'strategic_vision_de', 'bull-case_de', 'rivalry_de', 'leadership-governance_de']
    select_str = "ticker_eod, " + ", ".join(columns)
    res = supabase.table('company_presentation').select(select_str).execute()
    print(f"Total rows in DB: {len(res.data)}")
    for row in res.data:
        for col in columns:
            val = row.get(col)
            if not val or len(str(val)) < 50:
                print(f"Found candidate: {row['ticker_eod']} (Missing: {col}, Length: {len(str(val)) if val else 0})")
                return
    print("No candidates found with missing German strategic content.")

if __name__ == "__main__":
    main()
