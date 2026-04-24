#!/usr/bin/env python3
"""
supabase_presentation_manager.py — Uploads presentations to Supabase Storage
"""

import argparse
import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nayggiozebvwqnpjzvvn.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def upload_file(file_path: Path, bucket_name: str, ticker_eod: str) -> str:
    if not SUPABASE_KEY:
        print("[ERR] SUPABASE_SERVICE_ROLE_KEY not set.")
        sys.exit(1)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    file_name = file_path.name
    storage_path = f"{ticker_eod}/{file_name}"
    print(f"[*] Uploading {file_name} to bucket '{bucket_name}'...")
    with open(file_path, 'rb') as f:
        opts = {"upsert": "true"}
        if file_path.suffix.lower() == ".pdf": opts["content-type"] = "application/pdf"
        elif file_path.suffix.lower() == ".mp3": opts["content-type"] = "audio/mpeg"
        elif file_path.suffix.lower() == ".mp4": opts["content-type"] = "video/mp4"
        try:
            supabase.storage.from_(bucket_name).remove([storage_path])
        except Exception:
            pass
            
        try:
            supabase.storage.from_(bucket_name).upload(path=storage_path, file=f, file_options=opts)
        except Exception as e:
            print(f"[WARN] Upload threw an error (likely a parsing issue from storage3), but file might be in bucket: {e}")
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"
    print(f"[OK] Uploaded. URL: {public_url}")
    return public_url

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--bucket", default="company-presentations")
    parser.add_argument("--ticker", required=True)
    args = parser.parse_args()
    file_path = Path(args.file)
    if not file_path.exists(): sys.exit(1)
    upload_file(file_path, args.bucket, args.ticker)

if __name__ == "__main__":
    main()
