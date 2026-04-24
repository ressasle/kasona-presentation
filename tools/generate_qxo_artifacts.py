import os
import json
import subprocess
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

def main():
    # Load .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    ticker = "QXO.US"
    print(f"[*] Fetching data for {ticker}...")
    res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    
    if not res.data:
        print(f"[ERR] No data found for {ticker}")
        return
    
    data = res.data[0]
    
    # 1. Draft the Markdown
    md_content = f"""# Institutional Presentation: QXO Inc.

## 1. Company Overview
{data.get('description', 'No description available.')}

## 2. History and Evolution
{data.get('history-evolution', 'No data available.')}

## 3. Strategic Vision & Growth Roadmap
### Vision
{data.get('strategic_vision', 'No data available.')}

### Roadmap
{data.get('growth_roadmap', 'No data available.')}

## 4. Porter's Five Forces Analysis
### Rivalry
{data.get('rivalry', 'No data available.')}

### Supplier Power
{data.get('supplier-power', 'No data available.')}

### Buyer Power
{data.get('buyer-power', 'No data available.')}

### Threat of Entry
{data.get('threat-of-entry', 'No data available.')}

### Substitutes
{data.get('substitutes', 'No data available.')}

### Competitive Landscape
{data.get('competitive_landscape', 'No data available.')}

## 5. Leadership and Governance Audit
{data.get('leadership-governance', 'No data available.')}

### Key Executive Profiles (LinkedIn Summary)
"""
    
    linkedin_data = data.get('linkedin_profiles', [])
    if isinstance(linkedin_data, str):
        try:
            linkedin_data = json.loads(linkedin_data)
        except:
            linkedin_data = []
            
    for profile in linkedin_data[:5]:
        name = profile.get('name', 'N/A')
        title = profile.get('title', 'N/A')
        url = profile.get('url', '#')
        md_content += f"- **{name}**: {title} ([Profile]({url}))\n"

    md_content += f"""
## 6. Risk and Success Factors
{data.get('risk-success-factors', 'No data available.')}

## 7. Investment Thesis
### Professional Summary
{data.get('investment_thesis', 'No data available.')}

### Bull Case
{data.get('bull-case', 'No data available.')}

### Bear Case
{data.get('bear-case', 'No data available.')}

## 8. L4 Strategic Report
{data.get('l4_report', 'No data available.')}
"""

    md_path = Path("references/qxo_presentation.md")
    md_path.write_text(md_content, encoding="utf-8")
    print(f"[OK] Markdown drafted: {md_path}")

    # 2. Generate PDF
    print("[*] Generating PDF...")
    pdf_cmd = [
        "python", "tools/generate_presentation_pdf.py", 
        str(md_path), 
        "--ticker", ticker,
        "--output-dir", "output"
    ]
    subprocess.run(pdf_cmd, check=True)
    pdf_path = Path("output/qxo_presentation.pdf")
    
    # 3. Generate Audio
    print("[*] Generating Audio...")
    audio_path = Path("output/qxo_briefing.mp3")
    audio_cmd = [
        "python", "tools/generate_presentation_audio.py",
        "--script", str(md_path),
        "--output", str(audio_path),
        "--lang", "en"
    ]
    subprocess.run(audio_cmd, check=True)
    
    # 4. Upload to Supabase Storage
    print("[*] Uploading artifacts...")
    try:
        from tools.supabase_presentation_manager import upload_file
    except ImportError:
        from supabase_presentation_manager import upload_file
    
    pdf_url = upload_file(pdf_path, "earnings-reports-presentations", ticker)
    audio_url = upload_file(audio_path, "earnings-presentation-podcasts", ticker)
    
    # 5. Update Supabase Record
    print("[*] Updating database URLs...")
    update_data = {
        "pdf_url": pdf_url,
        "audio_url": audio_url,
        "status": "to_review"
    }
    supabase.table("company_presentation").update(update_data).eq("ticker_eod", ticker).execute()
    
    print(f"\n{'='*40}")
    print(f"[SUCCESS] QXO Artifacts Generated and Linked!")
    print(f"PDF URL: {pdf_url}")
    print(f"Audio URL: {audio_url}")
    print(f"{'='*40}")

if __name__ == "__main__":
    main()
