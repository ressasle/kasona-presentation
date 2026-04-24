#!/usr/bin/env python3
"""Upload SFT.LSE presentation artifacts to Supabase and insert database record."""
import os
import json
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Administrator\Documents\kasonaops\presentation\.env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nayggiozebvwqnpjzvvn.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ticker = "SFT.LSE"
company_name = "Software Circle plc"

# Upload PDF
pdf_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\SFT_presentation.pdf")
storage_path_pdf = f"{ticker}/SFT_presentation.pdf"
with open(pdf_path, "rb") as f:
    supabase.storage.from_("earnings-reports-pdf").upload(
        path=storage_path_pdf, file=f,
        file_options={"upsert": "true", "content-type": "application/pdf"}
    )
pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{storage_path_pdf}"
print(f"[OK] PDF uploaded: {pdf_url}")

# Upload Audio
audio_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\SFT_briefing.mp3")
storage_path_audio = f"{ticker}/SFT_briefing.mp3"
with open(audio_path, "rb") as f:
    supabase.storage.from_("final-podcasts").upload(
        path=storage_path_audio, file=f,
        file_options={"upsert": "true", "content-type": "audio/mpeg"}
    )
audio_url = f"{SUPABASE_URL}/storage/v1/object/public/final-podcasts/{storage_path_audio}"
print(f"[OK] Audio uploaded: {audio_url}")

# Read markdown content
md_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\references\SFT_presentation.md")
markdown_content = md_path.read_text(encoding="utf-8")

# Update company_presentation
data = {
    "ticker_eod": ticker,
    "company_name": company_name,
    "description": "UK-based serial acquirer of vertical market software (VMS) businesses, focusing on mission-critical SME solutions.",
    "investment_thesis": "Serial acquirer model targeting high-quality SaaS businesses with low churn and stable cash flows. Transitioned from legacy print (Grafenia) to pure-play software growth.",
    "strategic_vision": "Expanding the 'Software Circle' lifecycle to become the leading UK-listed VMS consolidator, utilizing a decentralized operating model for operational excellence.",
    "competitive_landscape": "Fragmented VMS market; competes with regional software consolidators and private equity for acquisitions. Moat derived from deep niche expertise and founder-friendly reputation.",
    "growth_roadmap": "Accelerated M&A pipeline targeting Northern Europe and UK, deepening feature sets (CareDocs, Arc Technology), and optimizing capital allocation via DBS-inspired system.",
    "markdown_content": markdown_content,
    "pdf_url": pdf_url,
    "audio_url": audio_url,
    "status": "uploaded",
    "review_status": "approved",
    "uploaded": True,
    "audio_tts": "en-US-ChristopherNeural (edge-tts)",
    "n8n-info": "Manual Research Synthesis (Workflow QTfs16hVROvSIjlA timed out but served as baseline)"
}

response = supabase.table("company_presentation").upsert(data, on_conflict="ticker_eod").execute()
record_id = response.data[0]["id"] if response.data else "unknown"
print(f"[OK] Database record updated: {record_id}")
print(f"\n=== FINAL LINKS ===")
print(f"PDF:   {pdf_url}")
print(f"Audio: {audio_url}")
print(f"Record ID: {record_id}")
