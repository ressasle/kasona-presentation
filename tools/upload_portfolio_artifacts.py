#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def upload_file(supabase, file_path, bucket, folder):
    file_name = file_path.name
    storage_path = f"{folder}/{file_name}"
    
    with open(file_path, "rb") as f:
        opts = {"upsert": "true"}
        if file_path.suffix.lower() == ".pdf":
            opts["content-type"] = "application/pdf"
        elif file_path.suffix.lower() == ".mp3":
            opts["content-type"] = "audio/mpeg"
        
        supabase.storage.from_(bucket).upload(path=storage_path, file=f, file_options=opts)
    
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--portfolio", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--type", default="Portfolio Briefing")
    args = parser.parse_args()

    if not SUPABASE_KEY:
        print("Missing SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    pdf_path = Path(args.pdf)
    audio_path = Path(args.audio)
    script_path = Path(args.script)
    
    # Upload PDF
    pdf_url = upload_file(supabase, pdf_path, "earnings-reports-pdf", args.portfolio)
    print(f"[OK] PDF Uploaded: {pdf_url}")
    
    # Upload Audio (to final-podcasts)
    audio_url = upload_file(supabase, audio_path, "final-podcasts", args.portfolio)
    print(f"[OK] Audio Uploaded: {audio_url}")
    
    # Read Script
    with open(script_path, "r", encoding="utf-8") as f:
        script_content = f.read()
    
    # Insert record into kasona_podcast_runs
    data = {
        "portfolio_id": args.portfolio,
        "investor_name": args.name,
        "produktart": args.type,
        "podcast_script": script_content,
        "audio_path": f"reports/{audio_path.name}", # Relative path as per example
        "final_audio_path": audio_url,
        "char_count": len(script_content),
        "version": 1,
        "qa_status": "delivered"
    }
    
    # Check if a record for today already exists to update it, or insert new
    try:
        supabase.table("kasona_podcast_runs").insert(data).execute()
        print("[OK] Database record created.")
    except Exception as e:
        print(f"[ERR] Database Error: {e}")

if __name__ == "__main__":
    main()
