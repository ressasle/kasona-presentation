import os
import re
from dotenv import load_dotenv
from supabase import create_client

def format_as_numbered_list(text):
    if not text:
        return text
    
    # Let's standardize the newlines first
    text = re.sub(r'\r\n', '\n', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    formatted_lines = []
    i = 0
    count = 1
    
    while i < len(lines):
        line = lines[i]
        
        # Strip leading dashes and spaces
        line = re.sub(r'^\-\s*', '', line)
        
        # Check if line is a heading/number
        # matches: "heading: xxx", "1: xxx", "heading1: xxx"
        heading_match = re.match(r'^(?:heading(?:\s*\d+)?|\d+)\s*:\s*(.*)', line, re.IGNORECASE)
        if heading_match:
            heading_text = heading_match.group(1).strip()
            
            # Look ahead for rationale/point
            if i + 1 < len(lines):
                next_line = re.sub(r'^\-\s*', '', lines[i+1])
                rationale_match = re.match(r'^(?:rationale|point(?:\s*\d+)?)\s*:\s*(.*)', next_line, re.IGNORECASE)
                if rationale_match:
                    rationale_text = rationale_match.group(1).strip()
                    formatted_lines.append(f"{count}. {heading_text}: {rationale_text}")
                    count += 1
                    i += 2
                    continue
            
            # If no rationale found on next line, just output heading if there's no rationale match
            formatted_lines.append(f"{count}. {heading_text}")
            count += 1
            i += 1
            continue
            
        # Maybe the format is already "1. Heading: Rationale" or similar
        # "1. Dominant Market Position: Rationale: Alibaba maintains..."
        # We can clean up redundant "Rationale:" inside
        already_numbered = re.match(r'^\d+\.\s*(.*?):\s*Rationale:\s*(.*)', line, re.IGNORECASE)
        if already_numbered:
            formatted_lines.append(f"{count}. {already_numbered.group(1).strip()}: {already_numbered.group(2).strip()}")
            count += 1
            i += 1
            continue
            
        # "1. Dominant Market Position: Alibaba maintains..."
        already_numbered_simple = re.match(r'^\d+\.\s*(.*)', line)
        if already_numbered_simple:
            # Check if it has a colon separating heading and rationale
            content = already_numbered_simple.group(1)
            # Remove redundant "Rationale:" if present
            content = re.sub(r'Rationale:\s*', '', content, flags=re.IGNORECASE)
            formatted_lines.append(f"{count}. {content}")
            count += 1
            i += 1
            continue
            
        # Catch-all: Just prepend the number if it doesn't have one and doesn't match above
        # But wait, maybe the rationale was attached to the same line without a newline?
        # e.g., "heading: XYZ rationale: ABC"
        inline_match = re.match(r'^(?:heading(?:\s*\d+)?|\d+)\s*:\s*(.*?)\s+(?:rationale|point(?:\s*\d+)?)\s*:\s*(.*)', line, re.IGNORECASE)
        if inline_match:
            formatted_lines.append(f"{count}. {inline_match.group(1).strip()}: {inline_match.group(2).strip()}")
            count += 1
            i += 1
            continue
            
        # Final fallback, just line
        # Remove redundant "Rationale:" if present
        line = re.sub(r'Rationale:\s*', '', line, flags=re.IGNORECASE)
        formatted_lines.append(f"{count}. {line}")
        count += 1
        i += 1

    final_text = "\n".join(formatted_lines)
    return final_text

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
            cleaned_bull = format_as_numbered_list(bull)
            if cleaned_bull != str(bull).strip():
                needs_update = True
                new_data["bull-case"] = cleaned_bull
                
        if bear:
            cleaned_bear = format_as_numbered_list(bear)
            if cleaned_bear != str(bear).strip():
                needs_update = True
                new_data["bear-case"] = cleaned_bear
                
        if needs_update:
            updates.append((ticker, new_data, row))
            
    print(f"Found {len(updates)} rows to update.")
    
    for ticker, new_data, old_row in updates:
        # print(f"Updating {ticker}...")
        supabase.table("company_presentation").update(new_data).eq("ticker_eod", ticker).execute()
        
    print("Updates complete. Verifying sample...")
    
    res = supabase.table("company_presentation").select("ticker_eod", "bull-case", "bear-case").limit(5).execute()
    for row in res.data:
        print(f"\n[{row['ticker_eod']}]")
        print("BULL-CASE:")
        print(row.get('bull-case', ''))
        print("BEAR-CASE:")
        print(row.get('bear-case', ''))

if __name__ == "__main__":
    main()
