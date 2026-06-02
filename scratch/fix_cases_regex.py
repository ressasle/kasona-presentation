import os
import re
from dotenv import load_dotenv
from supabase import create_client

def clean_prose(text):
    if not text:
        return text
        
    s = str(text)
    
    # Re-wrap in brackets to see if it was broken JSON and parse it
    # But since it's messy, regex is more robust.
    
    # 1. Clean up "heading": "..." style JSON
    # Matches `1":{"heading": "Something", "rationale": "Because..."}`
    # and variations.
    s = re.sub(r'\"?\d+\"?:\s*\{\s*\"heading\"?\s*:\s*\"([^\"]+)\"?,?\s*\"rationale\"?\s*:\s*\"([^\"]+)\"?,?\s*\}?', r'- \1: \2\n', s)
    
    # Matches `"heading1": "...", "point1": "..."`
    s = re.sub(r'\"?heading\d+\"?\s*:\s*\"([^\"]+)\"?,?\s*\"point\d+\"?\s*:\s*\"([^\"]+)\"?,?', r'- \1: \2\n', s)
    
    # 2. Clean up `"1. Market Dominance":"Shopify continues..."`
    # Matches `"1. Something": "Rationale..."`
    s = re.sub(r'\"?(\d+\.\s*.*?)\"?\s*:\s*\"(.*?)\"', r'- \1: \2\n', s)

    # Clean up random JSON brackets and quotes remaining at start/end or separating things
    s = s.replace('"},{"', '\n')
    s = s.replace('","', '\n')
    
    # Remove any remaining raw JSON keys like "1":{
    s = re.sub(r'\"?\d+\"?:\s*\{', '', s)
    
    # Strip random structural chars
    s = s.replace('"}', '')
    s = s.replace('{"', '')
    s = s.replace('"}', '')
    s = s.replace(',"', '\n')
    
    # Remove leading/trailing quotes/brackets from lines
    lines = s.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        line = line.strip('{},[]"')
        if line:
            if not line.startswith('-') and re.match(r'^\d+\.', line):
                pass
            elif not line.startswith('-') and len(line) > 10:
                line = '- ' + line
            cleaned_lines.append(line)
            
    # Rejoin
    final_text = "\n".join(cleaned_lines)
    
    # Remove duplicate newlines
    final_text = re.sub(r'\n+', '\n', final_text)
    return final_text.strip()

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
        
    updates = []
    for row in all_data:
        ticker = row.get("ticker_eod")
        bull = row.get("bull-case")
        bear = row.get("bear-case")
        
        needs_update = False
        new_data = {}
        
        if bull:
            cleaned_bull = clean_prose(bull)
            if cleaned_bull != str(bull).strip():
                needs_update = True
                new_data["bull-case"] = cleaned_bull
                
        if bear:
            cleaned_bear = clean_prose(bear)
            if cleaned_bear != str(bear).strip():
                needs_update = True
                new_data["bear-case"] = cleaned_bear
                
        if needs_update:
            updates.append((ticker, new_data, row))
            
    print(f"Found {len(updates)} rows to update.")
    
    for ticker, new_data, old_row in updates:
        print(f"Updating {ticker}...")
        for k, v in new_data.items():
            # print(f"  {k} BEFORE:\n{old_row[k]}")
            # print(f"  {k} AFTER :\n{v}\n")
            pass
            
        supabase.table("company_presentation").update(new_data).eq("ticker_eod", ticker).execute()
        
    print("Done!")

if __name__ == "__main__":
    main()
