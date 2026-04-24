import os
import sys
import json
import time
import requests
from google import genai
from google.genai import types
from supabase import create_client, Client
from dotenv import load_dotenv

# ---- stdout encoding fix for Windows ----
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("[DEBUG] Script starting...", flush=True)

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    print(f"Error: Missing environment variables. (URL: {bool(SUPABASE_URL)}, KEY: {bool(SUPABASE_KEY)}, GEMINI: {bool(GEMINI_API_KEY)})")
    exit(1)

print("[DEBUG] Environment loaded. Initializing clients...", flush=True)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

PILLARS = {
    "description": "Comprehensive company overview and business model.",
    "history-evolution": "Detailed history of the company, key milestones, and evolution.",
    "leadership-governance": "Analysis of the leadership team, founders, and corporate governance.",
    "risk-success-factors": "Key success drivers and critical risk factors for the business.",
    "strategic_vision": "The company's long-term strategic vision and ambition.",
    "growth_roadmap": "Future growth initiatives, market expansion, and product roadmap.",
    "investment_thesis": "The overarching institutional investment thesis.",
    "bull-case": "Detailed investment thesis for the bull scenario.",
    "bear-case": "Detailed investment thesis for the bear scenario.",
    "rivalry": "Analysis of competitive rivalry (Porter's 5 Forces).",
    "supplier-power": "Analysis of supplier power (Porter's 5 Forces).",
    "buyer-power": "Analysis of buyer power (Porter's 5 Forces).",
    "threat-of-entry": "Analysis of the threat of new entry (Porter's 5 Forces).",
    "substitutes": "Analysis of the threat of substitutes (Porter's 5 Forces).",
    "ai_agent_firmenhistorie": "Deep evolutionary history, strategic pivot points, and institutional heritage analysis."
}

def synthesize_batch(ticker, company_name, missing_pillars, context):
    """
    Synthesizes multiple missing pillars in a single Gemini request.
    """
    if not missing_pillars:
        return {}

    pillar_descriptions = "\n".join([f"- {p}: {PILLARS[p]}" for p in missing_pillars])
    
    prompt = f"""
    You are an institutional equity researcher. Provide a high-fidelity analysis for the following missing pillars for {company_name} ({ticker}).
    
    Context:
    {context}
    
    Missing Pillars to Analyze:
    {pillar_descriptions}
    
    Requirements:
    - Return analysis in JSON format where keys matching the missing pillars.
    - For Bull/Bear: Provide 3 clear, numbered points with a heading and brief rationale.
    - For Porter's Five Forces: Qualitative assessment (High/Medium/Low) + 2-3 sentence institutional rationale.
    
    Output Format:
    {{
        "{missing_pillars[0]}": "Analysis text...",
        ...
    }}
    JSON only, no markdown blocks.
    """
    
    models_to_try = [
        "models/gemini-3.1-flash-lite-preview",
        "models/gemini-2.5-flash-native-audio-latest",
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-lite",
        "models/gemini-flash-latest"
    ]
    
    for model_name in models_to_try:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"    [*] Trying model: {model_name}...", flush=True)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json',
                    )
                )
                res_text = response.text.strip()
                
                # Robust JSON extraction
                if "{" in res_text:
                    res_text = res_text[res_text.find("{"):res_text.rfind("}")+1]
                
                data = json.loads(res_text)
                
                # [FIX] Filter keys to prevent Supabase schema errors
                valid_data = {k: v for k, v in data.items() if k in PILLARS}
                if len(valid_data) < len(data):
                    print(f"      [WARN] Filtered out invalid keys: {set(data.keys()) - set(valid_data.keys())}")
                
                return valid_data
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "quota" in err_msg.lower():
                    wait_time = 60 * (attempt + 1)
                    print(f"    [429] Model {model_name} rate limit hit. Waiting {wait_time}s...", flush=True)
                    time.sleep(wait_time)
                elif "404" in err_msg or "not found" in err_msg.lower():
                    print(f"    [404] Model {model_name} not available. Skipping to next model...", flush=True)
                    break
                else:
                    print(f"    [ERR] Gemini ({model_name}) failed: {e}", flush=True)
                    break
    
    return {}

def remediate_ticker(row):
    ticker = row['ticker_eod']
    company_name = row['company_name']
    description = row.get('description') or ''
    thesis = row.get('investment_thesis') or ''
    
    print(f"\n>>> Remediating {ticker} ({company_name})", flush=True)
    
    missing = []
    for pillar in PILLARS.keys():
        val = row.get(pillar, "")
        if not val or len(str(val).strip()) < 10:
            missing.append(pillar)
    
    if not missing:
        print(f"  [OK] No missing structural pillars for {ticker}.", flush=True)
    else:
        print(f"  [MISSING] {len(missing)} pillars: {', '.join(missing)}", flush=True)
        context = f"Company Description: {description[:1000]}\nInvestment Thesis: {thesis[:500]}"
        print(f"  [*] Synthesizing {len(missing)} pillars...", flush=True)
        try:
            synthesis_batch = synthesize_batch(ticker, company_name, missing, context)
        except Exception as se:
            print(f"  [ERR] Synthesis critical failure: {se}", flush=True)
            synthesis_batch = {}
        
        if synthesis_batch:
            print(f"  [SAVE] Persisting {len(synthesis_batch)} pillars to Supabase...", flush=True)
            try:
                res = supabase.table("company_presentation").update(synthesis_batch).eq("ticker_eod", ticker).execute()
                if hasattr(res, 'data') and res.data:
                    print(f"  [OK] Saved successfully.", flush=True)
                else:
                    print(f"  [WARN] Supabase update returned no data. Check permissions.", flush=True)
            except Exception as e:
                print(f"  [ERR] Supabase update failed: {e}", flush=True)
        else:
            print(f"  [FAIL] Synthesis returned no data for {ticker}.", flush=True)

    # Trigger artifact regeneration regardless (to ensure quality)
    print(f"  [GEN] Regenerating artifacts for {ticker}...", flush=True)
    os.system(f"python tools/generate_ticker_artifacts.py --ticker {ticker}")

def main():
    target_ticker = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("Starting Institutional Pillar Remediation Sweep (Batched Mode)...", flush=True)
    
    # Query for all incomplete records
    res = supabase.table("company_presentation").select("*").execute()
    rows = res.data if res.data else []
    
    if not rows:
        print("No records found in company_presentation table.")
        return

    targets = []
    for row in rows:
        if not row: continue
        if target_ticker and row['ticker_eod'] != target_ticker:
            continue
            
        needs_work = False
        for pillar in PILLARS.keys():
            val = row.get(pillar, "")
            if not val or len(str(val).strip()) < 10:
                needs_work = True
                break
        if needs_work:
            targets.append(row)
            
    print(f"Found {len(targets)} tickers requiring remediation.", flush=True)
    
    for row in targets:
        try:
            remediate_ticker(row)
            # Global cooldown between tickers to respect token buckets
            print("  [COOL] Waiting 30s before next ticker...", flush=True)
            time.sleep(30)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Fatal error processing {row['ticker_eod']}: {e}", flush=True)
            continue

if __name__ == "__main__":
    main()
