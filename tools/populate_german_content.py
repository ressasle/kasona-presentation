import os
import sys
import json
import time
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

class GermanContentPopulator:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.genai_client = genai.Client(api_key=self.gemini_key)
        self.model_name = "gemini-2.0-flash"

        # New Format Persona
        self.persona = """
        Role: Senior Strategic Analyst & Governance Auditor.
        Mission: Provide a purely fact-based, value-neutral analysis of a target company.
        Operating Protocol: Strict evidence-based logic. Avoid promotional adjectives (e.g., 'leading', 'innovative', 'unique') unless backed by specific market share data or KPIs.
        Language Rules: Use precise financial terminology and preserve institutional tone.
        """

    def _ask_ai(self, prompt: str, max_retries: int = 5) -> str:
        wait = 15
        current_model = self.model_name
        for attempt in range(max_retries):
            try:
                response = self.genai_client.models.generate_content(
                    model=current_model,
                    contents=f"{self.persona}\n\n{prompt}",
                    config=types.GenerateContentConfig(
                        temperature=0.1,  # Low temperature for fact-based neutrality
                    )
                )
                return response.text.strip()
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"  [!] Rate limit hit for {current_model} (attempt {attempt+1}/{max_retries}).", flush=True)
                    if attempt >= 1 and current_model == "gemini-2.0-flash":
                        print("  [!] Switching to gemini-flash-latest fallback...", flush=True)
                        current_model = "gemini-flash-latest"
                    
                    time.sleep(wait)
                    wait = min(wait * 2, 60)
                else:
                    print(f"  [!] AI error: {e}")
                    return ""
        return ""

    def synthesize_missing_pillar(self, ticker: str, pillar_name: str, base_description: str) -> str:
        if not base_description or len(base_description) < 50:
            return ""
            
        print(f"  [~] Synthesizing missing pillar: {pillar_name} for {ticker}...", flush=True)
        prompt = f"""
        Company: {ticker}
        Base Description: {base_description}
        
        Task: Based on the description and your knowledge of {ticker}, generate a professional 3-4 paragraph {pillar_name} in English.
        The content must be institutional quality, data-driven, and strategic.
        
        Requirements:
        - Purely fact-based and value-neutral.
        - Zero process transparency (no mentions of AI or models).
        - Direct analysis, no headers.
        """
        return self._ask_ai(prompt)

    def translate_column(self, text: str, context: str = "general") -> str:
        if not text or len(text.strip()) < 10:
            return ""
        
        prompt = f"""
        Role: Professional Financial Translator (English to German).
        Context: Institutional Investor Presentation for {context}.
        Task: Translate the following English text into professional, sophisticated German.
        Requirements:
        - Use precise financial terminology (e.g., 'Moat' -> 'Burggraben', 'Leverage' -> 'Verschuldungsgrad', 'Cash Flow' -> 'Cashflow').
        - Maintain a serious, institutional tone.
        - Preserve all markdown formatting (bullet points, bolding).
        - 0% process transparency: Do not mention that this was translated or any AI role.
        
        TEXT TO TRANSLATE:
        {text}
        
        GERMAN TRANSLATION:
        """
        return self._ask_ai(prompt)

    def process_tickers(self, tickers: List[str]):
        for ticker in tickers:
            print(f"[*] Processing {ticker}...", flush=True)
            
            # 1. Update company_presentation
            res = self.supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
            if res.data:
                data = res.data[0]
                updates = {}
                base_desc = data.get("description") or data.get("history-evolution", "")
                
                # Comprehensive Mapping for "New Format" Compliance
                # Maps EN pillar to its DE counterpart
                mappings = {
                    "investment_thesis": "investment_thesis_de",
                    "strategic_vision": "strategic_vision_de",
                    "growth_roadmap": "growth_roadmap_de",
                    "history-evolution": "ai_agent_firmenhistorie_de",
                    "leadership-governance": "leadership-governance_de",
                    "risk-success-factors": "risk-success-factors_de",
                    "bull-case": "bull-case_de",
                    "bear-case": "bear-case_de",
                    "rivalry": "rivalry_de",
                    "supplier-power": "supplier-power_de",
                    "buyer-power": "buyer-power_de",
                    "threat-of-entry": "threat-of-entry_de",
                    "substitutes": "substitutes_de",
                    "core-assets-capabilities": "core-assets-capabilities_de",
                    "success-failure-factors": "success-failure-factors_de"
                }
                
                # Check for special case: executive summary (uses description)
                if not data.get("executive_summary_de"):
                    en_summary = data.get("description") or base_desc[:1000]
                    if en_summary:
                        print(f"  [+] Translating executive_summary_de...", flush=True)
                        updates["executive_summary_de"] = self.translate_column(en_summary, context=ticker)

                for en_col, de_col in mappings.items():
                    en_val = data.get(en_col)
                    de_val = data.get(de_col)
                    
                    # Ensure English pillar reaches minimum density
                    if not en_val or len(str(en_val)) < 50:
                        en_val = self.synthesize_missing_pillar(ticker, en_col.replace("-", " ").title(), base_desc)
                        if en_val:
                            updates[en_col] = en_val
                    
                    # Translate to German if missing or newly synthesized
                    if en_val and (not de_val or len(str(de_val)) < 50):
                        print(f"  [+] Translating {en_col} -> {de_col}...", flush=True)
                        translated = self.translate_column(en_val, context=ticker)
                        if translated:
                            updates[de_col] = translated
                
                if updates:
                    self.supabase.table("company_presentation").update(updates).eq("ticker_eod", ticker).execute()
                    print(f"  [DONE] Updated {len(updates)} columns for {ticker}", flush=True)
                else:
                    print(f"  [SKIP] No updates needed for {ticker}", flush=True)
            
            # 2. Update quarterly_earnings (most recent)
            res_qe = self.supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).order("fiscal_year", desc=True).order("quarter", desc=True).limit(1).execute()
            if res_qe.data:
                data_qe = res_qe.data[0]
                if not data_qe.get("executive_summary_de") and data_qe.get("executive_summary"):
                    print(f"  [+] Translating QE for {ticker}...", flush=True)
                    trans = self.translate_column(data_qe["executive_summary"], context=f"{ticker} Earnings")
                    if trans:
                        self.supabase.table("quarterly_earnings").update({"executive_summary_de": trans}).eq("id", data_qe["id"]).execute()

if __name__ == "__main__":
    target_ticker = sys.argv[1] if len(sys.argv) > 1 else None
    populator = GermanContentPopulator()
    
    query = populator.supabase.table("company_presentation").select("ticker_eod")
    if target_ticker:
        query = query.eq("ticker_eod", target_ticker)
    
    res = query.execute()
    tickers = [row["ticker_eod"] for row in res.data if row]
    
    if not tickers:
        if target_ticker:
            print(f"  [!] Ticker {target_ticker} not found in database.")
        else:
            print("  [!] No tickers found to process.")
        sys.exit(0)
        
    print(f"[*] Found {len(tickers)} tickers to process.", flush=True)
    populator.process_tickers(tickers)
