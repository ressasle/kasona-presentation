import os
import json
import re
from dotenv import load_dotenv
from supabase import create_client

def format_json_to_prose(data):
    if isinstance(data, str):
        data = data.strip()
        # Try to parse as JSON if it looks like it
        if data.startswith('{') or data.startswith('['):
            try:
                # Sometimes there's a trailing quote if the string was weirdly formatted
                data = json.loads(data)
            except Exception:
                pass

    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, dict):
                heading = v.get('heading', '')
                rationale = v.get('rationale', '')
                if not heading and not rationale:
                    lines.append(f"{k}: {format_json_to_prose(v)}")
                else:
                    lines.append(f"{heading}: {rationale}")
            elif isinstance(v, list):
                lines.append(f"{k}: {format_json_to_prose(v)}")
            else:
                # Handle keys like "heading1", "point1" by just writing the value,
                # or formatting as "key: value"
                # If key looks like "heading1" and value is string
                if "heading" in k.lower() or "point" in k.lower():
                    lines.append(str(v))
                else:
                    lines.append(f"{k}: {v}")
        return "\n".join(lines)
    elif isinstance(data, list):
        lines = [format_json_to_prose(item) for item in data]
        return "\n".join(lines)
    else:
        # String
        s = str(data).strip()
        # strip brackets just in case
        chars_to_strip = " \n\r\t{[(\"']})"
        while True:
            prev = s
            s = s.strip(chars_to_strip)
            if s == prev:
                break
        return s

def clean_text(text):
    if not text:
        return text
    
    # Try multiple ways to parse the text as JSON, sometimes there's an extra quote
    s = str(text).strip()
    
    # Attempt to parse json
    try:
        if s.startswith('{') or s.startswith('['):
            parsed = json.loads(s)
            s = format_json_to_prose(parsed)
    except:
        pass
        
    # Extra cleanup for lingering leading/trailing quotes and brackets
    chars_to_strip = " \n\r\t{[(\"']})"
    while True:
        prev = s
        s = s.strip(chars_to_strip)
        if s == prev:
            break
            
    # also replace any lingering `":"` or similar with `: ` if it looks like broken json
    s = s.replace('":"', ': ')
    s = s.replace('": "', ': ')
    s = s.replace('","', '\n')
    
    return s.strip()

def main():
    load_dotenv(".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    print("Fetching company_presentation records...")
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = supabase.table("company_presentation").select("ticker_eod", "bull-case", "bear-case").range(offset, offset + limit - 1).execute()
        data = res.data
        if not data:
            break
        all_data.extend(data)
        if len(data) < limit:
            break
        offset += limit
        
    print(f"Total rows fetched: {len(all_data)}")
    
    updates = []
    for row in all_data:
        ticker = row.get("ticker_eod")
        bull = row.get("bull-case")
        bear = row.get("bear-case")
        
        needs_update = False
        new_data = {}
        
        if bull:
            # We want to re-evaluate based on the *original* raw data if possible,
            # but since we already stripped it in the previous run, some of them are malformed JSON now!
            # e.g., `1. Market Dominance":"Shopify continues...`
            # Let's fix those by manually turning them back to json or just cleaning them up.
            
            # If it starts with a number or something and contains ":"
            # We can just clean it
            cleaned_bull = clean_text(bull)
            if cleaned_bull != str(bull).strip():
                needs_update = True
                new_data["bull-case"] = cleaned_bull
                
        if bear:
            cleaned_bear = clean_text(bear)
            if cleaned_bear != str(bear).strip():
                needs_update = True
                new_data["bear-case"] = cleaned_bear
                
        if needs_update:
            updates.append((ticker, new_data, row))
            
    print(f"Found {len(updates)} rows to update.")
    
    for ticker, new_data, old_row in updates:
        print(f"Updating {ticker}...")
        for k, v in new_data.items():
            print(f"  {k} BEFORE: {old_row[k]}")
            print(f"  {k} AFTER : {v}\n")
            
        supabase.table("company_presentation").update(new_data).eq("ticker_eod", ticker).execute()
        
    print("Done!")

if __name__ == "__main__":
    main()
