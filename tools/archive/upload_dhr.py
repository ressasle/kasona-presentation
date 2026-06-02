#!/usr/bin/env python3
"""Upload DHR.US presentation artifacts to Supabase and insert database record."""
import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Administrator\Documents\kasonaops\presentation\.env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nayggiozebvwqnpjzvvn.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Upload PDF
pdf_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\DHR_US_final_presentation.pdf")
storage_path_pdf = "DHR.US/DHR_presentation.pdf"
with open(pdf_path, "rb") as f:
    supabase.storage.from_("earnings-reports-pdf").upload(
        path=storage_path_pdf, file=f,
        file_options={"upsert": "true", "content-type": "application/pdf"}
    )
pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{storage_path_pdf}"
print(f"[OK] PDF uploaded: {pdf_url}")

# Upload Audio
audio_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\DHR_US_final_presentation.mp3")
storage_path_audio = "DHR.US/DHR_presentation.mp3"
with open(audio_path, "rb") as f:
    supabase.storage.from_("final-podcasts").upload(
        path=storage_path_audio, file=f,
        file_options={"upsert": "true", "content-type": "audio/mpeg"}
    )
audio_url = f"{SUPABASE_URL}/storage/v1/object/public/final-podcasts/{storage_path_audio}"
print(f"[OK] Audio uploaded: {audio_url}")

# Read markdown content
md_path = Path(r"c:\Users\Administrator\Documents\kasonaops\presentation\output\DHR_US_final_presentation.md")
markdown_content = md_path.read_text(encoding="utf-8")

# Insert into company_presentation
data = {
    "ticker_eod": "DHR.US",
    "company_name": "Danaher Corporation",
    "description": "Global life sciences and diagnostics leader with 3 segments: Biotechnology (Cytiva), Life Sciences, and Diagnostics. Powered by the Danaher Business System (DBS).",
    "investment_thesis": "Pure-play life sciences/diagnostics compounder with proprietary DBS operating system driving M&A integration and margin expansion. 75% recurring revenue, FCF conversion >145%.",
    "strategic_vision": "Bioprocessing recovery cycle + Masimo acquisition expands AI-enabled diagnostics platform. Cell therapy market CAGR 12.4% through 2030.",
    "competitive_landscape": "Competes with Thermo Fisher (TMO), Agilent (A), Sartorius in Life Sciences; Roche, Abbott, Siemens in Diagnostics. Key moat: integrated consumables ecosystem + DBS.",
    "growth_roadmap": "High-single-digit bioprocessing growth in 2026, Masimo integration for AI monitoring, CGT manufacturing expansion, China recovery.",
    "markdown_content": markdown_content,
    "pdf_url": pdf_url,
    "audio_url": audio_url,
    "status": "uploaded",
    "review_status": "approved",
    "uploaded": True,
    "audio_tts": "en-US-ChristopherNeural (edge-tts)",
    "n8n-info": "NotebookLM_DeepResearch triggered (workflow ID: QTfs16hVROvSIjlA) - awaiting async completion"
}

response = supabase.table("company_presentation").upsert(data, on_conflict="ticker_eod").execute()
record_id = response.data[0]["id"] if response.data else "unknown"
print(f"[OK] Database record created: {record_id}")
print(f"\n=== FINAL LINKS ===")
print(f"PDF:   {pdf_url}")
print(f"Audio: {audio_url}")
print(f"Record ID: {record_id}")
