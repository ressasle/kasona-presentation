import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(url, key)
    
    res = supabase.table('company_presentation').select('markdown_content').eq('ticker_eod', 'ROP.US').execute()
    content = res.data[0]['markdown_content']
    
    with open('ROP_US_presentation_fresh.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Saved ROP_US_presentation_fresh.md in UTF-8")

if __name__ == "__main__":
    main()
