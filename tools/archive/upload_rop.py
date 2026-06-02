#!/usr/bin/env python3
"""Upload ROP.US presentation artifacts to Supabase and update database record."""
import os
import json
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Absolute path to .env
env_path = r"c:\Users\Administrator\Documents\kasonaops\presentation\.env"
load_dotenv(env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_KEY:
    print("❌ Missing SUPABASE_SERVICE_ROLE_KEY in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ticker = "ROP.US"
company_name = "Roper Technologies Inc"

# 1. Upload PDF
pdf_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\drafts\roper_technologies_presentation.pdf")
storage_path_pdf = f"{ticker}/roper_technologies_presentation.pdf"
print(f"Uploading PDF: {pdf_path}...")
with open(pdf_path, "rb") as f:
    supabase.storage.from_("earnings-reports-pdf").upload(
        path=storage_path_pdf, file=f,
        file_options={"upsert": "true", "content-type": "application/pdf"}
    )
pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{storage_path_pdf}"
print(f"[OK] PDF uploaded: {pdf_url}")

# 2. Upload Audio
audio_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\drafts\roper_technologies_briefing.mp3")
storage_path_audio = f"{ticker}/roper_technologies_briefing.mp3"
print(f"Uploading Audio: {audio_path}...")
with open(audio_path, "rb") as f:
    supabase.storage.from_("final-podcasts").upload(
        path=storage_path_audio, file=f,
        file_options={"upsert": "true", "content-type": "audio/mpeg"}
    )
audio_url = f"{SUPABASE_URL}/storage/v1/object/public/final-podcasts/{storage_path_audio}"
print(f"[OK] Audio uploaded: {audio_url}")

# 3. Read markdown content
md_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\drafts\roper_technologies_presentation.md")
markdown_content = md_path.read_text(encoding="utf-8")

# 4. Update company_presentation
print("Updating database record...")
data = {
    "ticker_eod": ticker,
    "company_name": company_name,
    "description": "Diversified technology company that designs and develops vertical software and technology-enabled products for niche markets.",
    "investment_thesis": "Compounder model with 100%+ FCF conversion, dominant niche market positions, and a disciplined 'asset-light' acquisition strategy.",
    "strategic_vision": "Strategic pivot from industrial manufacturing to high-margin vertical software, creating recurring revenue streams and technical moats.",
    "competitive_landscape": "Dominates highly technical, mission-critical niches with high switching costs; avoids direct competition with mega-cap tech giants.",
    "growth_roadmap": "Continuing the compounding engine through disciplined M&A, AI integration across business units, and operational excellence.",
    "markdown_content": markdown_content,
    "pdf_url": pdf_url,
    "audio_url": audio_url,
    "status": "uploaded",
    "review_status": "approved",
    "uploaded": True,
    "audio_tts": "en-US-ChristopherNeural (edge-tts)"
}

response = supabase.table("company_presentation").upsert(data, on_conflict="ticker_eod").execute()
record_id = response.data[0]["id"] if response.data else "unknown"
print(f"[OK] Database record updated: {record_id}")

print(f"\n=== FINAL LINKS ===")
print(f"PDF:   {pdf_url}")
print(f"Audio: {audio_url}")
print(f"Record ID: {record_id}")
