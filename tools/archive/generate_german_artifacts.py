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
            if data.strip().startswith(('{', '[')):
                data = json.loads(data)
            else:
                return data
        except:
            return data
            
    md = ""
    if isinstance(data, dict):
        for k, v in data.items():
            key_clean = str(k).replace("_", " ").title()
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
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    print(f"[*] Fetching German data for {ticker}...")
    res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    
    if not res.data:
        print(f"[ERR] No data found for {ticker}")
        return
    
    data = res.data[0]
    company_name = data.get('company_name', ticker)
    
    # German fallback chains
    exec_summary = data.get('executive_summary_de') or data.get('description') or ""
    history = data.get('ai_agent_firmenhistorie_de') or data.get('history-evolution_de') or data.get('history-evolution') or ""
    vision = data.get('strategic_vision_de') or data.get('strategic_vision') or ""
    roadmap = data.get('growth_roadmap_de') or data.get('growth_roadmap') or ""
    rivalry = data.get('rivalry_de') or data.get('rivalry') or ""
    supplier = data.get('supplier-power_de') or data.get('supplier-power') or ""
    buyer = data.get('buyer-power_de') or data.get('buyer-power') or ""
    threat = data.get('threat-of-entry_de') or data.get('threat-of-entry') or ""
    subs = data.get('substitutes_de') or data.get('substitutes') or ""
    leadership = data.get('leadership-governance_de') or data.get('leadership-governance') or ""
    risks = data.get('risk-success-factors_de') or data.get('risk-success-factors') or ""
    thesis = data.get('investment_thesis_de') or data.get('investment_thesis') or ""
    bull = data.get('bull-case_de') or data.get('bull-case') or ""
    bear = data.get('bear-case_de') or data.get('bear-case') or ""
    core_assets = data.get('core-assets-capabilities_de') or data.get('core-assets-capabilities') or ""
    success_factors = data.get('success-failure-factors_de') or data.get('success-failure-factors') or ""

    # Draft the German Markdown
    md_content = f"""# Institutionelle Präsentation: {company_name}
    
## 1. Unternehmensübersicht
{exec_summary}

## 2. Historie und Strategische Entwicklung
{history}

### 2.1 Kernkompetenzen & Infrastruktur
{core_assets}

### 2.2 Faktoren für Erfolg & Misserfolg
{success_factors}

"""
    if chart_path and os.path.exists(chart_path):
        md_content += f"\n![Umsatzverteilung]({Path(chart_path).as_posix()})\n"

    md_content += f"""
## 3. Strategische Vision & Wachstumsplan
### Vision
{vision}

### Wachstumsplan
{roadmap}

## 4. Porter's Five Forces Analyse
### Wettbewerbsintensität
{rivalry}

### Verhandlungsmacht der Lieferanten
{supplier}

### Verhandlungsmacht der Abnehmer
{buyer}

### Bedrohung durch neue Anbieter
{threat}

### Bedrohung durch Ersatzprodukte
{subs}

## 5. Führung und Corporate Governance
{leadership}

## 6. Risiken und Erfolgsfaktoren
{risks}

## 7. Investment Thesis
### Professionelle Zusammenfassung
{thesis}

### Bull Case (Aufwärtspotenzial)
{bull}

### Bear Case (Abwärtsrisiken)
{bear}

## 8. Institutionelle Ressourcen & Externe Validierung
"""

    links = []
    if data.get('youtube_ceo_interview'):
        links.append(f"- **Neuestes CEO-Interview**: [Hier ansehen]({data.get('youtube_ceo_interview')})")
    if data.get('youtube_podcast'):
        links.append(f"- **Strategischer Deep Dive (Podcast)**: [Hier ansehen]({data.get('youtube_podcast')})")
    
    if links:
        md_content += "\n".join(links) + "\n"
    else:
        md_content += "Keine externen institutionellen Links zugeordnet.\n"

    safe_ticker = ticker.replace(".", "_").lower()
    md_file = Path(f"references/{safe_ticker}_de_presentation.md")
    os.makedirs("references", exist_ok=True)
    md_file.write_text(md_content, encoding="utf-8")
    print(f"[OK] German Markdown drafted: {md_file}")

    # 2. Generate PDF
    print("[*] Generating German PDF...")
    os.makedirs("output", exist_ok=True)
    pdf_cmd = [
        "python", "tools/generate_presentation_pdf.py", 
        str(md_file), 
        "--ticker", ticker,
        "--output-dir", "output"
    ]
    subprocess.run(pdf_cmd, check=True)
    pdf_path = Path(f"output/{safe_ticker}_de_presentation.pdf")
    
    # Rename the output from generate_presentation_pdf to match DE expected name
    base_pdf = Path(f"output/{safe_ticker}_presentation.pdf")
    if base_pdf.exists() and not pdf_path.exists():
        # The script outputs _presentation.pdf by default based on regex or similar, 
        # let's just make sure we capture the right one.
        # Actually our md_file ends in _de_presentation.md.
        # Check what the script outputs. Usually it matches the stem.
        generated_pdf = Path(f"output/{md_file.stem}.pdf")
        if generated_pdf.exists():
            pdf_path = generated_pdf
        
    
    # 3. Generate Audio
    print("[*] Generating German Audio...")
    audio_path = Path(f"output/{safe_ticker}_de_briefing.mp3")
    audio_cmd = [
        "python", "tools/generate_presentation_audio.py",
        "--script", str(md_file),
        "--output", str(audio_path),
        "--lang", "de"
    ]
    subprocess.run(audio_cmd, check=True)
    
    # 4. Upload to Supabase Storage
    print("[*] Uploading artifacts...")
    try:
        from tools.supabase_presentation_manager import upload_file
    except ImportError:
        try:
            from supabase_presentation_manager import upload_file
        except ImportError:
            sys.path.append(str(Path(__file__).parent))
            from supabase_presentation_manager import upload_file
            
    pdf_url = upload_file(pdf_path, "earnings-reports-presentations", f"{ticker}_DE")
    audio_url = upload_file(audio_path, "earnings-presentation-podcasts", f"{ticker}_DE")
    
    # 5. Update Supabase Record
    print("[*] Updating database URLs...")
    update_data = {
        "pdf_url_de": pdf_url,
        "audio_url_de": audio_url,
        "markdown_content_de": md_content,
        "status": "de_uploaded"
    }
    supabase.table("company_presentation").update(update_data).eq("ticker_eod", ticker).execute()
    
    print(f"\n{'='*40}")
    print(f"[SUCCESS] German Artifacts Generated for {ticker}!")
    print(f"DE PDF URL: {pdf_url}")
    print(f"DE Audio URL: {audio_url}")
    print(f"{'='*40}")

if __name__ == "__main__":
    main()
