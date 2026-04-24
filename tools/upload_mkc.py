#!/usr/bin/env python3
"""Upload MKC.US presentation artifacts to Supabase and update database record with institutional metadata."""
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

ticker = "MKC.US"
company_name = "McCormick & Company"

# 1. Load Research Data
json_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\McCormick_&_Company_data.json")
with open(json_path, 'r', encoding='utf-8') as f:
    research_data = json.load(f)

# 2. Upload PDF
pdf_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\mccormick_presentation.pdf")
storage_path_pdf = f"{ticker}/mccormick_presentation.pdf"
print(f"Uploading PDF: {pdf_path}...")
with open(pdf_path, "rb") as f:
    supabase.storage.from_("earnings-reports-pdf").upload(
        path=storage_path_pdf, file=f,
        file_options={"upsert": "true", "content-type": "application/pdf"}
    )
pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{storage_path_pdf}"
print(f"[OK] PDF uploaded: {pdf_url}")

# 3. Upload Audio
audio_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\mccormick_briefing.mp3")
storage_path_audio = f"{ticker}/mccormick_briefing.mp3"
print(f"Uploading Audio: {audio_path}...")
with open(audio_path, "rb") as f:
    supabase.storage.from_("final-podcasts").upload(
        path=storage_path_audio, file=f,
        file_options={"upsert": "true", "content-type": "audio/mpeg"}
    )
audio_url = f"{SUPABASE_URL}/storage/v1/object/public/final-podcasts/{storage_path_audio}"
print(f"[OK] Audio uploaded: {audio_url}")

# 4. Read markdown content
md_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\drafts\mccormick_presentation.md")
markdown_content = md_path.read_text(encoding="utf-8")

# 5. Update company_presentation
print("Updating database record with institutional metadata...")
data = {
    "ticker_eod": ticker,
    "company_name": company_name,
    "description": "Global leader in flavor, manufacturing, marketing, and distributing spices, seasoning mixes, condiments, and other flavorful products.",
    "investment_thesis": "Global flavor leader with ~20% market share, strong pricing power, and an 'indispensable' B2B role in the food industry.",
    "strategic_vision": "Transformation from a spice merchant into a high-tech platform for taste innovation via strategic M&A and AI-driven flavor development.",
    "competitive_landscape": "Commands a dominant 'Moat of Trust' and vertical integration that private labels cannot replicate; key partner for global FMCG players.",
    "growth_roadmap": "Focus on de-leveraging while scaling high-growth condenser categories (Cholula/Frank's) and expanding B2B technical flavor solutions.",
    "markdown_content": markdown_content,
    "pdf_url": pdf_url,
    "audio_url": audio_url,
    "status": "uploaded",
    "review_status": "approved",
    "uploaded": True,
    "audio_tts": "en-US-ChristopherNeural (edge-tts)",
    # New Institutional Columns
    "ai_agent_firmenhistorie": research_data.get("ai_agent_firmenhistorie"),
    "linkedin_profiles": research_data.get("linkedin_profiles"),
    "l4_report": research_data.get("l4_report"),
    "youtube_ceo_interview": research_data.get("youtube_ceo_interview"),
    "youtube_podcast": research_data.get("youtube_podcast")
}

response = supabase.table("company_presentation").upsert(data, on_conflict="ticker_eod").execute()
record_id = response.data[0]["id"] if response.data else "unknown"
print(f"[OK] Database record updated: {record_id}")

print(f"\n=== FINAL LINKS ===")
print(f"PDF:   {pdf_url}")
print(f"Audio: {audio_url}")
print(f"Record ID: {record_id}")
