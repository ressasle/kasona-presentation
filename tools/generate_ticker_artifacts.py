import os
import json
import subprocess
import argparse
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

def format_json_to_md(data):
    """Recursively convert a JSON object/list into Markdown bullets/sections."""
    if isinstance(data, str):
        try:
            # Try to parse if it looks like JSON
            if data.strip().startswith(('{', '[')):
                data = json.loads(data)
            else:
                return data
        except:
            return data
            
    md = ""
    if isinstance(data, dict):
        for k, v in data.items():
            key_clean = k.replace("_", " ").title()
            if isinstance(v, (dict, list)):
                md += f"\n**{key_clean}**:\n" + format_json_to_md(v)
            else:
                md += f"- **{key_clean}**: {v}\n"
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                md += "\n" + format_json_to_md(item)
            else:
                md += f"- {item}\n"
    return md

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--chart", help="Path to local chart image")
    args = parser.parse_args()
    
    ticker = args.ticker
    chart_path = args.chart
    
    # Load .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    print(f"[*] Fetching data for {ticker}...")
    res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    
    if not res.data:
        print(f"[ERR] No data found for {ticker}")
        return
    
    data = res.data[0]
    company_name = data.get('company_name', ticker)
    
    # 1. Validation: Enforce Zero-Null Policy
    mandatory_pillars = [
        'description', 'history-evolution', 'strategic_vision', 'growth_roadmap',
        'rivalry', 'supplier-power', 'buyer-power', 'threat-of-entry', 'substitutes',
        'leadership-governance', 'risk-success-factors', 'investment_thesis',
        'bull-case', 'bear-case', 'ai_agent_firmenhistorie',
        'core-assets-capabilities', 'success-failure-factors'
    ]
    
    missing_pillars = []
    for p in mandatory_pillars:
        val = data.get(p, "")
        if not val or "No data available" in str(val) or len(str(val)) < 20:
            missing_pillars.append(p)
            
    if missing_pillars:
        print(f"\n[CRITICAL] Zero-Null Policy Violation for {ticker}!")
        print(f"Missing Columns: {', '.join(missing_pillars)}")
        print(f"[*] Triggering automatic remediation...")
        subprocess.run(["python", "tools/remediate_all_pillars.py", ticker], check=True)
        # Re-fetch data after remediation
        res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
        data = res.data[0]

    # 2. Draft the Markdown
    md_content = f"""# Institutional Presentation: {company_name}
    
## 1. Company Overview
{data.get('description')}

## 2. History and Strategic Evolution
{data.get('history-evolution')}

### 2.1 Deep Institutional Heritage
{format_json_to_md(data.get('ai_agent_firmenhistorie'))}

### 2.2 Core Assets & Capabilities
{data.get('core-assets-capabilities')}

### 2.3 Success & Failure Factors
{data.get('success-failure-factors')}
"""

    if chart_path and os.path.exists(chart_path):
        md_content += f"\n![Regional Revenue Breakdown]({Path(chart_path).as_posix()})\n"

    md_content += f"""
## 3. Strategic Vision & Growth Roadmap
### Vision
{data.get('strategic_vision')}

### Roadmap
{data.get('growth_roadmap')}

## 4. Porter's Five Forces Analysis
### Competitive Rivalry
{data.get('rivalry')}

### Supplier Power
{data.get('supplier-power')}

### Buyer Power
{data.get('buyer-power')}

### Threat of New Entry
{data.get('threat-of-entry')}

### Threat of Substitutes
{data.get('substitutes')}

## 5. Leadership and Governance Audit
{data.get('leadership-governance')}

## 6. Risk and Success Factors
{data.get('risk-success-factors')}

## 7. Investment Thesis
### Professional Summary
{data.get('investment_thesis')}

### Bull Case (Upside Catalysts)
{data.get('bull-case')}

### Bear Case (Downside Risks)
{data.get('bear-case')}

## 8. Institutional Resources & External Validation
"""
    # Append Links if they exist
    links = []
    if data.get('youtube_ceo_interview'):
        links.append(f"- **Latest CEO Interview**: [Watch here]({data.get('youtube_ceo_interview')})")
    if data.get('youtube_podcast'):
        links.append(f"- **Strategic Deep Dive (Podcast)**: [Watch here]({data.get('youtube_podcast')})")
    if data.get('linkedin_profiles'):
        profiles = data.get('linkedin_profiles')
        if isinstance(profiles, str) and profiles.startswith('['):
            try: profiles = json.loads(profiles)
            except: pass
            
        if isinstance(profiles, list):
            md_content += "- **Executive Performance Context (LinkedIn)**:\n"
            for p in profiles:
                if isinstance(p, dict):
                    name = p.get('name', 'Profile')
                    url = p.get('url', '#')
                    title = p.get('title', '').split('·')[0].strip()
                    md_content += f"    - [{name}]({url}) - {title}\n"
        else:
            md_content += f"- **Executive Performance Context**: [LinkedIn Profiles]({profiles})\n"
            
    if data.get('l4_report'):
        md_content += f"\n### Institutional Benchmark Analysis\n{data.get('l4_report')}\n"
        
    if links:
        md_content += "\n".join(links) + "\n"
    else:
        md_content += "No external institutional links currently mapped.\n"

    safe_ticker = ticker.replace(".", "_").lower()
    md_file = Path(f"references/{safe_ticker}_presentation.md")
    os.makedirs("references", exist_ok=True)
    md_file.write_text(md_content, encoding="utf-8")
    print(f"[OK] Markdown drafted: {md_file}")

    # 2. Generate PDF
    print("[*] Generating PDF...")
    os.makedirs("output", exist_ok=True)
    pdf_cmd = [
        "python", "tools/generate_presentation_pdf.py", 
        str(md_file), 
        "--ticker", ticker,
        "--output-dir", "output"
    ]
    subprocess.run(pdf_cmd, check=True)
    pdf_path = Path(f"output/{safe_ticker}_presentation.pdf")
    
    # 3. Generate Audio
    print("[*] Generating Audio...")
    audio_path = Path(f"output/{safe_ticker}_briefing.mp3")
    audio_cmd = [
        "python", "tools/generate_presentation_audio.py",
        "--script", str(md_file),
        "--output", str(audio_path),
        "--lang", "en"
    ]
    subprocess.run(audio_cmd, check=True)
    
    # 4. Upload to Supabase Storage
    print("[*] Uploading artifacts...")
    # 4. Upload to Supabase Storage
    print("[*] Uploading artifacts...")
    try:
        from tools.supabase_presentation_manager import upload_file
    except ImportError:
        try:
            from supabase_presentation_manager import upload_file
        except ImportError:
            import sys
            sys.path.append(str(Path(__file__).parent))
            from supabase_presentation_manager import upload_file
            
    pdf_url = upload_file(pdf_path, "earnings-reports-presentations", ticker)
    audio_url = upload_file(audio_path, "earnings-presentation-podcasts", ticker)
    
    # 5. Update Supabase Record
    print("[*] Updating database URLs...")
    update_data = {
        "pdf_url": pdf_url,
        "audio_url": audio_url,
        "markdown_content": md_content,
        "status": "uploaded"
    }
    supabase.table("company_presentation").update(update_data).eq("ticker_eod", ticker).execute()
    
    print(f"\n{'='*40}")
    print(f"[SUCCESS] Artifacts Generated for {ticker}!")
    print(f"PDF URL: {pdf_url}")
    print(f"Audio URL: {audio_url}")
    print(f"{'='*40}")

if __name__ == "__main__":
    main()
