import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

def main():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(url, key)
    
    res = supabase.table('company_presentation').select('ticker_eod, company_name, markdown_content').execute()
    
    for row in res.data:
        ticker = row['ticker_eod']
        name = row['company_name']
        content = row['markdown_content']
        
        if not content:
            print(f"Skipping {ticker}: No markdown content")
            continue
            
        # Clean ticker for filename
        clean_ticker = ticker.replace('.', '_').replace('-', '_')
        filename = f"{clean_ticker}_presentation.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Exported {filename}")

if __name__ == "__main__":
    main()
