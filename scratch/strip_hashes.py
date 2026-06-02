import os
import re
from dotenv import load_dotenv
from supabase import create_client

def clean_content(text):
    if not isinstance(text, str) or not text:
        return text
    
    # Remove markdown headers at the start of lines (e.g., ## , ### )
    cleaned = re.sub(r'(?m)^#+\s*', '', text)
    # Also remove any lingering double hashes that might not be at the start of a line just in case
    cleaned = cleaned.replace('##', '')
    # Optionally remove bold markers if it's meant to be pure prose
    cleaned = cleaned.replace('**', '')
    
    return cleaned.strip()

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
        res = supabase.table("company_presentation").select("*").range(offset, offset + limit - 1).execute()
        data = res.data
        if not data:
            break
        all_data.extend(data)
        if len(data) < limit:
            break
        offset += limit
        
    print(f"Total rows fetched: {len(all_data)}")
    
    # Columns that typically contain prose that might have markdown hashes
    text_columns = [
        "description", "history-evolution", "leadership-governance", 
        "risk-success-factors", "strategic_vision", "growth_roadmap", 
        "investment_thesis", "bull-case", "bear-case", "rivalry", 
        "supplier-power", "buyer-power", "threat-of-entry", "substitutes", 
        "ai_agent_firmenhistorie"
    ]
    
    updates = []
    for row in all_data:
        ticker = row.get("ticker_eod")
        needs_update = False
        new_data = {}
        
        for col in text_columns:
            val = row.get(col)
            if val:
                cleaned_val = clean_content(val)
                if cleaned_val != str(val).strip():
                    needs_update = True
                    new_data[col] = cleaned_val
                    
        if needs_update:
            updates.append((ticker, new_data))
            
    print(f"Found {len(updates)} rows to update.")
    
    for ticker, new_data in updates:
        supabase.table("company_presentation").update(new_data).eq("ticker_eod", ticker).execute()
        
    print("Updates complete.")

if __name__ == "__main__":
    main()
