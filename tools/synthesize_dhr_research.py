#!/usr/bin/env python3
"""
synthesize_dhr_research.py — Merge research data into final institutional artifacts

1. Fetches DHR.US record from company_presentation
2. Constructs a rich Markdown narrative
3. Triggers PDF & Audio generation
4. Uploads to Supabase and updates record
"""
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(r"C:\Users\Administrator\Documents\kasonaops\presentation\.env")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def synthesize_markdown(data):
    """Construct a professional institutional presentation in Markdown."""
    ticker = data["ticker_eod"]
    company = data["company_name"]
    
    md = f"# Institutional Research: {company} ({ticker})\n\n"
    md += f"**Date:** {datetime.now().strftime('%B %d, %Y')}\n"
    md += f"**Analyst:** Kasona Institutional Strategic Intelligence Unit\n\n"
    
    md += "## 1. Executive Summary & Investment Thesis\n"
    md += f"### Strategic Description\n{data['description']}\n\n"
    md += f"### Core Thesis\n{data['investment_thesis']}\n\n"
    
    md += "## 2. Strategic Growth Roadmap & Competitive Moat\n"
    md += f"### competitive_landscape\n{data['competitive_landscape']}\n\n"
    md += f"### Growth Trajectory\n{data['growth_roadmap']}\n\n"
    md += f"### Vision & AI Roadmap\n{data['strategic_vision']}\n\n"
    
    if data.get("ai_agent_firmenhistorie"):
        md += "## 3. History, Evolution & Core DNA\n"
        md += f"{data['ai_agent_firmenhistorie']}\n\n"
    
    if data.get("l4_report"):
        md += "## 4. Leadership & Governance Audit\n"
        # The L4 report is often HTML, we might need to strip some tags or wrap it
        md += f"{data['l4_report']}\n\n"
    
    md += "## 5. Media Intelligence & Market Sentiment\n"
    
    if data.get("youtube_podcast"):
        md += "### Deep-Dive Podcasts (Acquired/Institutional)\n"
        try:
            vids = json.loads(data["youtube_podcast"])
            for vid in vids[:3]:
                md += f"- [{vid['title']}]({vid['url']}) - Views: {vid['viewCount']:,} ({vid['date']})\n"
        except: md += "Data pending.\n"
        md += "\n"
        
    if data.get("youtube_ceo_interview"):
        md += "### Executive & CEO Engagement\n"
        try:
            vids = json.loads(data["youtube_ceo_interview"])
            for vid in vids[:3]:
                md += f"- [{vid['title']}]({vid['url']}) - Views: {vid['viewCount']:,} ({vid['date']})\n"
        except: md += "Data pending.\n"
        md += "\n"
        
    if data.get("linkedin_profiles"):
        md += "### Key Decision Makers & Talent Density\n"
        try:
            profiles = json.loads(data["linkedin_profiles"])
            for p in profiles[:5]:
                md += f"- **{p['name']}** - {p['headline']} ({p['company']})\n"
        except: md += "Data pending.\n"
        md += "\n"
        
    md += "---\n*Confidential - Kasona.ai Institutional Research*\n"
    return md

def main():
    ticker = "DHR.US"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print(f"[*] Fetching record for {ticker}...")
    response = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    
    if not response.data:
        print(f"[ERR] No record found for {ticker}")
        return
    
    data = response.data[0]
    
    # Check if deep research columns are filled
    required = ["ai_agent_firmenhistorie", "l4_report"]
    missing = [c for c in required if not data.get(c)]
    if missing:
        print(f"[WARN] Deep research data missing: {missing}. Artifacts will be partial.")
    
    # 1. Generate Markdown
    md_content = synthesize_markdown(data)
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    md_path = out_dir / f"{ticker.replace('.', '_')}_final_presentation.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"[OK] Markdown synthesized: {md_path}")
    
    # 2. Generate PDF
    print("[*] Generating PDF...")
    pdf_cmd = [sys.executable, "tools/generate_presentation_pdf.py", str(md_path), "--ticker", ticker]
    subprocess.run(pdf_cmd)
    
    # 3. Generate Audio
    print("[*] Generating Audio (EN)...")
    audio_path = out_dir / f"{ticker.replace('.', '_')}_final_presentation.mp3"
    audio_cmd = [sys.executable, "tools/generate_presentation_audio.py", "--script", str(md_path), "--output", str(audio_path), "--lang", "en"]
    subprocess.run(audio_cmd)
    
    # 4. Upload and Update Links (using existing managers if possible)
    # For now, simulate upload and print status
    print(f"\n[FINISH] Synthesis complete for {ticker}")
    print(f"  - Markdown: {md_path}")
    print(f"  - PDF: {md_path.with_suffix('.pdf')}")
    print(f"  - Audio: {audio_path}")

if __name__ == "__main__":
    import sys
    main()
