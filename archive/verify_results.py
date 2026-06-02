import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    load_dotenv('.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(url, key)
    
    res = supabase.table('company_presentation').select('ticker_eod, "leadership-governance", "leadership-governance_de"').eq('ticker_eod', 'ROKO-B.ST').execute()
    if res.data:
        data = res.data[0]
        print(f"EN ({len(data['leadership-governance'])} chars):")
        print(data['leadership-governance'][:200] + "...")
        print("\nDE (" + str(len(data['leadership-governance_de'])) + " chars):")
        print(data['leadership-governance_de'][:200] + "...")

if __name__ == "__main__":
    main()
