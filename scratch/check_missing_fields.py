import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def check_missing_fields():
    response = supabase.table("company_presentation").select("ticker, pdf_url, audio_url, markdown_content").execute()
    data = response.data
    
    missing_pdf = []
    missing_audio = []
    missing_markdown = []
    
    for row in data:
        ticker = row['ticker']
        if not row.get('pdf_url'):
            missing_pdf.append(ticker)
        if not row.get('audio_url'):
            missing_audio.append(ticker)
        if not row.get('markdown_content'):
            missing_markdown.append(ticker)
            
    print(f"Total Companies: {len(data)}")
    print(f"Missing PDF ({len(missing_pdf)}): {missing_pdf}")
    print(f"Missing Audio ({len(missing_audio)}): {missing_audio}")
    print(f"Missing Markdown ({len(missing_markdown)}): {missing_markdown}")

if __name__ == "__main__":
    check_missing_fields()
