"""
Company Analysis Workflow - Kasona Institutional Pipeline
Real Apify scrapers: YouTube (search + transcripts) + LinkedIn people search
"""

import os
import sys
import json
import time
import requests
import argparse
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
from supabase import create_client, Client

# ---- stdout encoding fix for Windows ----
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# ---------------------------------------------------------------------------
# Verified Apify actor IDs (username~actor-name format)
# ---------------------------------------------------------------------------
APIFY_YT_ACTOR     = "streamers~youtube-scraper"          # search + subtitles in one
APIFY_LI_ACTOR     = "anchor~linkedin-profile-emailer"    # LinkedIn people search (no-cookie)
APIFY_BASE         = "https://api.apify.com/v2"


class CompanyAnalyzer:
    """Orchestrates the full Kasona institutional research pipeline."""

    def __init__(self, config: Dict[str, Any]):
        self.config      = config
        self.apify_key   = config.get("apify_api_key") or ""
        gemini_key       = config.get("google_gemini_api_key") or ""

        if gemini_key:
            self.genai_client = genai.Client(api_key=gemini_key)
            self.model_name = "gemini-2.0-flash"
        else:
            self.genai_client = None

        self.eodhd_key = config.get("eodhd_api_key") or ""

        # Supabase config
        self.supabase_url = config.get("supabase_url")
        self.supabase_key = config.get("supabase_service_key")
        self.supabase: Client = None
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                print(f"  [+] Supabase client initialized.")
            except Exception as e:
                print(f"  [!] Supabase init error: {e}")

    # ------------------------------------------------------------------
    # AI helper with exponential back-off on 429
    # ------------------------------------------------------------------
    def _ask_ai(self, system_prompt: str, user_prompt: str, *, max_retries: int = 5, response_mime_type: str = "text/plain") -> str:
        if not self.genai_client:
            return "No research model initialized."

        full_prompt = f"{system_prompt}\n\nUSER INPUT: {user_prompt}"
        wait = 20
        current_model = self.model_name
        
        for attempt in range(max_retries):
            try:
                response = self.genai_client.models.generate_content(
                    model=current_model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type=response_mime_type,
                    )
                )
                return response.text.strip()
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower():
                    print(f"  [!] Gemini {current_model} quota – waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                    if attempt >= 2 and current_model == "gemini-2.0-flash":
                        print("  [!] Switching to gemini-flash-latest fallback...")
                        current_model = "gemini-flash-latest"
                    time.sleep(wait)
                    wait = min(wait * 2, 120)
                else:
                    print(f"  [!] Gemini error: {e}")
                    return f"[AI_ERROR] {e}"
        return "[AI_ERROR] Gemini quota exceeded after all retries."

    # ------------------------------------------------------------------
    # Apify: run actor and wait for results
    # ------------------------------------------------------------------
    def _apify_run_and_wait(
        self,
        actor_id: str,
        run_input: Dict,
        timeout: int = 180,
        memory_mb: int = 512,
    ) -> List[Dict]:
        if not self.apify_key:
            print("  [!] No Apify API key configured.")
            return []

        headers = {"Content-Type": "application/json"}
        start_url = (
            f"{APIFY_BASE}/acts/{actor_id}/runs"
            f"?token={self.apify_key}&memory={memory_mb}"
        )
        try:
            resp = requests.post(start_url, json=run_input, headers=headers, timeout=30)
            resp.raise_for_status()
            run_id = resp.json()["data"]["id"]
            print(f"  [+] Apify run started (actor={actor_id}): {run_id}")
        except Exception as e:
            print(f"  [!] Apify launch error: {e}")
            return []

        deadline = time.time() + timeout
        poll_interval = 10
        while time.time() < deadline:
            time.sleep(poll_interval)
            poll_interval = min(poll_interval + 5, 30)
            try:
                s = requests.get(
                    f"{APIFY_BASE}/actor-runs/{run_id}?token={self.apify_key}",
                    timeout=20,
                ).json()["data"]
                status = s.get("status", "")
                print(f"  ... Apify status: {status}")
                if status == "SUCCEEDED":
                    dataset_id = s["defaultDatasetId"]
                    items = requests.get(
                        f"{APIFY_BASE}/datasets/{dataset_id}/items"
                        f"?token={self.apify_key}&clean=true&format=json",
                        timeout=60,
                    ).json()
                    return items if isinstance(items, list) else []
                elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    print(f"  [!] Apify run ended with status: {status}")
                    return []
            except Exception as e:
                print(f"  [!] Polling error: {e}")

        print("  [!] Apify polling timeout.")
        return []

    # ------------------------------------------------------------------
    # YouTube: search + subtitles in a single actor call
    # ------------------------------------------------------------------
    def scrape_youtube(self, company_name: str) -> Dict[str, Any]:
        """
        Uses streamers/youtube-scraper to search for videos AND download subtitles.
        Returns: { ceo_interviews: [...], podcasts: [...] }
        Each item: { title, url, duration, views, channel, publishedAt, transcript }
        """

        def _search(query: str, label: str) -> List[Dict]:
            print(f"  [YT] Searching: '{query}'")
            items = self._apify_run_and_wait(
                APIFY_YT_ACTOR,
                {
                    "searchQueries": [query],     # correct field name
                    "maxResultsShorts": 0,
                    "maxResults": 5,
                    "downloadSubtitles": True,    # request subtitles/transcripts
                    "subtitlesLanguage": "en",
                    "subtitlesFormat": "plaintext",
                },
                timeout=180,
            )
            enriched = []
            for v in items[:5]:
                vid_id = v.get("id") or v.get("videoId") or ""
                url = v.get("url") or (f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "")
                raw_transcript = v.get("subtitles") or v.get("transcript") or v.get("captions") or ""
                if isinstance(raw_transcript, list):
                    texts = []
                    for seg in raw_transcript:
                        if isinstance(seg, dict):
                            texts.append(seg.get("plaintext") or seg.get("text") or "")
                        else:
                            texts.append(str(seg))
                    raw_transcript = " ".join(texts)
                enriched.append({
                    "title":       v.get("title", ""),
                    "url":         url,
                    "duration":    v.get("duration", ""),
                    "views":       v.get("viewCount") or v.get("views", ""),
                    "channel":     v.get("channelName") or v.get("channel", ""),
                    "publishedAt": v.get("publishedAt") or v.get("date", ""),
                    "transcript":  str(raw_transcript)[:8000],  # cap
                    "label":       label,
                })
            return enriched

        ceo_results    = _search(f"{company_name} CEO interview investor 2024", "ceo_interview")
        podcast_results = _search(f"{company_name} acquired podcast OR company analysis 2024", "podcast")

        return {
            "ceo_interviews": ceo_results,
            "podcasts":       podcast_results,
        }

    # ------------------------------------------------------------------
    # LinkedIn: people search via Apify
    # ------------------------------------------------------------------
    def scrape_linkedin_profiles(self, company_name: str) -> List[Dict]:
        """
        Search for C-suite executives at company_name via Google Search Scraper.
        Returns list of { name, title, company, url, location, summary }.
        """
        print(f"  [LI] Finding LinkedIn executives for '{company_name}' via Google Search...")

        items = self._apify_run_and_wait(
            "apify~google-search-scraper",
            {
                "queries": f"site:linkedin.com/in/ \"{company_name}\" CEO\nsite:linkedin.com/in/ \"{company_name}\" CFO",
                "maxPagesPerQuery": 1,
                "resultsPerPage": 5,
                "customData": {"useApifyProxy": True},
            },
            timeout=180,
        )

        profiles = []
        seen = set()
        for page in items:
            organic = page.get("organicResults", [])
            for res in organic:
                url = res.get("url", "")
                if "linkedin.com/in/" not in url:
                    continue
                title = res.get("title", "")
                name = title.split("-")[0].split("|")[0].strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                profiles.append({
                    "name":     name,
                    "title":    res.get("description") or title,
                    "company":  company_name,
                    "url":      url,
                    "location": "",
                    "summary":  res.get("description", "")[:500],
                })

        print(f"  [LI] Found {len(profiles)} executive profile(s).")
        return profiles

    # ------------------------------------------------------------------
    # AI analysis
    # ------------------------------------------------------------------
    def analyze_leadership(self, company_name: str) -> str:
        prompt = (
            f"Rolle & Autoritaet: Senior Leadership & Governance Auditor (Kasona Division)."
            f" Mission: Seziere C-Suite, Board, Aktionaearsstruktur und Risiken von {company_name}."
            f" Struktur: Executive Leadership | Board of Directors | Aktionaersstruktur | Risiko-Check."
            f" Erstelle einen praezisen, faktenbasierten Audit-Report."
        )
        return self._ask_ai(prompt, company_name)

    def analyze_company_history(self, company_name: str) -> str:
        prompt = (
            f"Role: Global Equity Research Director.\n"
            f"Mission: Document the deep history and strategic transformation of {company_name}.\n"
            f"Structure:\n"
            f"1. Founding & Original Mission\n"
            f"2. Strategic Pivot Points (M&A, Divestments)\n"
            f"3. Cultural DNA & Governance Heritage\n"
            f"4. Evolution of Core Assets.\n"
            f"Strictly facts, NO filler words. Write in English."
        )
        return self._ask_ai(prompt, company_name)

    def analyze_porter_five_forces(self, company_name: str) -> Dict[str, str]:
        prompt = (
            f"Role: Strategic Industry Analyst.\n"
            f"Mission: Conduct a Porter's Five Forces analysis for {company_name}.\n"
            f"For each force, provide a detailed analysis (3-4 sentences).\n"
            f"Return the result in JSON format with these exact keys:\n"
            f"'rivalry', 'supplier-power', 'buyer-power', 'threat-of-entry', 'substitutes'.\n"
            f"Ensure the response is ONLY the JSON object. Write in English."
        )
        res_raw = self._ask_ai(prompt, company_name, response_mime_type="application/json")
        try:
            # Basic cleanup if AI adds markdown
            if "{" in res_raw:
                res_raw = res_raw[res_raw.find("{"):res_raw.rfind("}")+1]
            return json.loads(res_raw)
        except:
            print(f"  [!] Failed to parse Porter analysis: {res_raw[:100]}...")
            return {k: "" for k in ["rivalry", "supplier-power", "buyer-power", "threat-of-entry", "substitutes"]}

    def analyze_investment_thesis(self, company_name: str) -> Dict[str, str]:
        prompt = (
            f"Role: Investment Committee Lead.\n"
            f"Mission: Synthesize the Bull Case and Bear Case for {company_name}.\n"
            f"Structure:\n"
            f"- Bull Case: What are the key drivers for outperformance?\n"
            f"- Bear Case: What are the primary risks or structural headwinds?\n"
            f"Return the result in JSON format with keys 'bull-case' and 'bear-case'.\n"
            f"Ensure the response is ONLY the JSON object. Write in English."
        )
        res_raw = self._ask_ai(prompt, company_name, response_mime_type="application/json")
        try:
            if "{" in res_raw:
                res_raw = res_raw[res_raw.find("{"):res_raw.rfind("}")+1]
            return json.loads(res_raw)
        except:
            print(f"  [!] Failed to parse Investment Thesis: {res_raw[:100]}...")
            return {"bull-case": "", "bear-case": ""}

    def analyze_risk_success_factors(self, company_name: str) -> str:
        prompt = (
            f"Role: Risk Management Director.\n"
            f"Mission: Identify the critical success factors and primary risks for {company_name}.\n"
            f"Fokus: What matters most for the next 12-24 months?\n"
            f"Strictly facts and strategic judgment. Write in English."
        )
        return self._ask_ai(prompt, company_name)

    def generate_l4_report(self, company_name: str, results: Dict) -> str:
        yt = results.get("youtube_data", {})
        ceo_titles   = [v.get("title", "") for v in yt.get("ceo_interviews", [])[:3]]
        pod_titles   = [v.get("title", "") for v in yt.get("podcasts", [])[:3]]
        ceo_excerpt  = ""
        if yt.get("ceo_interviews"):
            ceo_excerpt = yt["ceo_interviews"][0].get("transcript", "")[:2000]

        context = (
            f"Leadership Analysis:\n{results.get('leadership', '')[:3000]}\n\n"
            f"Company History:\n{results.get('history-evolution', '')[:3000]}\n\n"
            f"YouTube CEO Interviews Found: {ceo_titles}\n"
            f"YouTube Podcasts Found: {pod_titles}\n"
            f"CEO Interview Transcript Excerpt:\n{ceo_excerpt}"
        )
        prompt = (
            f"Rolle: Investment Committee Lead (Kasona)."
            f" Fasse die gesamte Analyse fuer {company_name} ultra-dicht zusammen."
            f" Fokus: Moats, Risikokapital-Abgrenzung, langfristige Werttreiber."
            f" Keine Fuelwoerter. Nur harte Daten und strategisches Urteil."
        )
        return self._ask_ai(f"Analyst Context:\n{context}", prompt)

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------
    def run_workflow(self, company_name: str) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print(f"  Kasona Institutional Pipeline: {company_name}")
        print(f"{'='*60}\n")
        results: Dict[str, Any] = {}

        # 1 – Research History
        print("\n[1/5] Company History & Evolution...")
        history = self.analyze_company_history(company_name)
        results["ai_agent_firmenhistorie"] = history 
        results["history-evolution"]       = history
        print("  [DONE]")

        # 2.05 - Fundamental Data (EODHD)
        if self.eodhd_key and self.config.get("ticker_eod"):
            print("\n[2/5] Fetching EODHD Fundamentals...")
            ticker = self.config["ticker_eod"]
            url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={self.eodhd_key}&fmt=json"
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    funda = resp.json()
                    gen = funda.get("General", {})
                    results["company_name"] = gen.get("Name", "")
                    results["description"]  = gen.get("Description", "")
                    # Placeholder mapping for legacy structural fields if missing
                    results["investment_thesis"]    = f"Platform consolidator in {gen.get('Industry', 'Industrial Sector')}. Strategic focus on {gen.get('Sector', 'Industrial')} vertical."
                    results["strategic_vision"]     = f"Leading the transformation of {gen.get('Industry', 'Industry')} through high-velocity M&A."
                    results["competitive_landscape"] = f"Highly fragmented {gen.get('Industry', 'Market')} with significant consolidation opportunity."
                    results["growth_roadmap"]       = "Targeting $10B+ revenue through disciplined M&A and tech-enabled integration."
                    print(f"  [OK] Fundamental data fetched for {results.get('company_name')}")
                else:
                    print(f"  [!] EODHD Error {resp.status_code}")
            except Exception as e:
                print(f"  [!] EODHD Fetch Exception: {e}")

        # 2.1 - Strategic Analytics
        print("\n[2.5/5] Strategic & Investment Analytics...")
        results["leadership-governance"] = self.analyze_leadership(company_name)
        results["risk-success-factors"]  = self.analyze_risk_success_factors(company_name)
        
        thesis = self.analyze_investment_thesis(company_name)
        results["bull-case"] = thesis.get("bull-case", "")
        results["bear-case"] = thesis.get("bear-case", "")
        
        five_forces = self.analyze_porter_five_forces(company_name)
        for k in ["rivalry", "supplier-power", "buyer-power", "threat-of-entry", "substitutes"]:
            results[k] = five_forces.get(k, "")
        print("  [DONE]")

        # 3 – Real YouTube scrape
        print("\n[3/5] YouTube Research (Apify - real scrape + transcripts)...")
        yt_data = self.scrape_youtube(company_name)
        results["youtube_data"] = yt_data

        ceo_vids = yt_data.get("ceo_interviews", [])
        pod_vids = yt_data.get("podcasts", [])
        results["youtube_ceo_interview"] = ceo_vids[0]["url"] if ceo_vids else ""
        results["youtube_podcast"]       = pod_vids[0]["url"] if pod_vids else ""
        print(f"  CEO Interviews found:  {len(ceo_vids)}")
        print(f"  Podcasts found:        {len(pod_vids)}")

        # 4 – Real LinkedIn scrape
        print("\n[4/5] LinkedIn Executive Profiles (Apify - real scrape)...")
        results["linkedin_profiles"] = self.scrape_linkedin_profiles(company_name)

        # 5 – AI L4 Report (uses YouTube context)
        print("\n[5/5] Generating Institutional L4 Report...")
        results["l4_report"] = self.generate_l4_report(company_name, results)
        print("  [DONE]")

        print("\n[SUCCESS] Workflow completed.\n")
        return results

    def sync_to_supabase(self, ticker_eod: str, data: Dict[str, Any]) -> bool:
        """Updates the public.company_presentation table with synthesized data."""
        if not self.supabase:
            print("  [!] Supabase client not initialized. Cannot sync.")
            return False

        print(f"\n[SYNC] Updating Supabase for ticker: {ticker_eod}...")
        
        raw_metadata = {
            "youtube_raw": data.get("youtube_data", {}),
            "linkedin_raw": data.get("linkedin_profiles", []),
            "apify_meta": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "status": "raw_persistence_active"
            }
        }

        payload = {
            "ai_agent_firmenhistorie": data.get("history-evolution", ""),
            "history-evolution":       data.get("history-evolution", ""),
            "leadership-governance":   data.get("leadership-governance", ""),
            "risk-success-factors":    data.get("risk-success-factors", ""),
            "bull-case":               data.get("bull-case", ""),
            "bear-case":               data.get("bear-case", ""),
            "rivalry":                 data.get("rivalry", ""),
            "supplier-power":          data.get("supplier-power", ""),
            "buyer-power":             data.get("buyer-power", ""),
            "threat-of-entry":         data.get("threat-of-entry", ""),
            "substitutes":             data.get("substitutes", ""),
            "linkedin_profiles":        data.get("linkedin_profiles", []),
            "l4_report":               data.get("l4_report", ""),
            "youtube_ceo_interview":   data.get("youtube_ceo_interview", ""),
            "youtube_podcast":         data.get("youtube_podcast", ""),
            "company_name":            data.get("company_name", ""),
            "description":             data.get("description", ""),
            "investment_thesis":       data.get("investment_thesis", ""),
            "strategic_vision":        data.get("strategic_vision", ""),
            "competitive_landscape":   data.get("competitive_landscape", ""),
            "growth_roadmap":          data.get("growth_roadmap", ""),
            "n8n-info":                json.dumps(raw_metadata),
            "status":                  "to_review"
        }
        
        try:
            res = self.supabase.table("company_presentation") \
                .update(payload) \
                .eq("ticker_eod", ticker_eod) \
                .execute()
            
            if len(res.data) > 0:
                print(f"  [SUCCESS] Supabase updated for {ticker_eod}.")
                # Pre-flight check for structural pillars
                print(f"  [ZNCR] Triggering Zero-Null pre-flight check for {ticker_eod}...")
                import subprocess
                subprocess.run(["python", "tools/remediate_all_pillars.py", ticker_eod], check=True)
                return True
            else:
                print(f"  [WARNING] No record found in Supabase for ticker_eod='{ticker_eod}'.")
                return False
        except Exception as e:
            print(f"  [!] Supabase update or ZNCR check error: {e}")
            return False


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Kasona Company Analyzer")
    parser.add_argument("--company", required=True, help="Company name to analyse")
    parser.add_argument("--ticker-eod", help="Ticker EOD format (e.g. AAPL.US)")
    parser.add_argument("--supabase-sync", action="store_true", help="Update Supabase directly")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()

    config = {
        "apify_api_key":          os.environ.get("APIFY_API_KEY"),
        "google_gemini_api_key":  os.environ.get("GOOGLE_GEMINI_API_KEY"),
        "supabase_url":           os.environ.get("SUPABASE_URL"),
        "supabase_service_key":   os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
        "eodhd_api_key":          os.environ.get("EODHD_API_KEY"),
        "ticker_eod":             args.ticker_eod
    }

    print(f"  Apify key:    {'LOADED' if config['apify_api_key'] else 'MISSING'}")
    print(f"  Gemini key:   {'LOADED' if config['google_gemini_api_key'] else 'MISSING'}")
    print(f"  Supabase key: {'LOADED' if config['supabase_service_key'] else 'MISSING'}")

    analyzer = CompanyAnalyzer(config)
    results  = analyzer.run_workflow(args.company)

    # Save to JSON
    os.makedirs(args.output_dir, exist_ok=True)
    slug          = args.company.replace(" ", "_").replace("&", "and")
    json_filename = os.path.join(args.output_dir, f"{slug}_data.json")
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] JSON: {json_filename}")

    # Sync to Supabase if requested
    if args.supabase_sync:
        ticker = args.ticker_eod
        if not ticker:
            print("  [!] Error: --supabase-sync requires --ticker-eod")
            sys.exit(1)
        analyzer.sync_to_supabase(ticker, results)


if __name__ == "__main__":
    main()
