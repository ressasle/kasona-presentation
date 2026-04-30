"""
new-company-presentation.py — Kasona Institutional Research Pipeline v2
=======================================================================
Full Python replica of the n8n workflow:

  n8n Node Map → Python Phase Map
  ──────────────────────────────────────────────────────────────────────
  Formular (Test)                       → CLI argparse
  Youtube Acquired Podcast  (APIFY)      → scrape_youtube_acquired_podcast()
  Youtube Ceo Interview    (APIFY)      → scrape_youtube_ceo_interview()
  Filter: Videos < 2 Years / <6 Months → _filter_videos_by_age()
  AI Agent: Leadership (Gemini 3 Flash) → run_leadership_audit()
  AI Agent: Historie (English/German) (Gemini 3 Flash) → run_history_analysis()
  Clean data (GPT-4.1-nano)             → extract_executive_names()
  Code in JavaScript                    → parse_names_to_list()
  LinkedIn Profile Scraper (APIFY)      → scrape_linkedin_profiles()
  L4_Report Generator HTML              → generate_l4_html_report()
  Supabase (implicit)                   → sync_to_supabase()

Usage
─────
  python tools/new-company-presentation.py --company "Danaher" --ticker-eod DHR.US
  python tools/new-company-presentation.py --company "Lifco" --ticker-eod LIFCO-B --supabase-sync

.env keys required
──────────────────
  APIFY_API_KEY
  GOOGLE_GEMINI_API_KEY        (for leadership audit via Gemini 2.5 Pro)
  OPENROUTER_API_KEY           (for history analysis via Perplexity sonar)
  OPENAI_API_KEY               (for name extractor via GPT-4.1-nano)
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  EODHD_API_KEY
"""

from __future__ import annotations

import os
import sys
import time
import json
import argparse
import requests
import datetime
from typing import Any
from pathlib import Path
import google.generativeai as genai

from dotenv import load_dotenv
from supabase import create_client, Client

# ── stdout UTF-8 fix (Windows) ─────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Load .env ──────────────────────────────────────────────────────────
print("  [DEBUG] Loading .env...", flush=True)
_tools_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_tools_dir)
_env_path = os.path.join(_root_dir, ".env")
print(f"  [DEBUG] Env path: {_env_path}", flush=True)
load_dotenv(_env_path)
print(f"  [DEBUG] .env loaded. APIFY_API_TOKEN present: {bool(os.environ.get('APIFY_API_TOKEN'))}", flush=True)
print(f"  [DEBUG] SUPABASE_URL present: {bool(os.environ.get('SUPABASE_URL'))}", flush=True)

# ── Apify actor IDs (n8n node → actor ID) ─────────────────────────────
APIFY_BASE            = "https://api.apify.com/v2"
APIFY_YT_ACTOR        = "streamers~youtube-scraper"            # Youtube Aquired Podcast + Ceo Interview node
APIFY_LI_ACTOR        = "apimaestro~linkedin-profile-detail"   # LinkedIn Profile Scraper node

# ── Master Index Constants ───────────────────────────────────────────
SKILL_ID = "company_presentation"
DEFAULT_REPORT_TYPE = "Deep Dive Presentation"

# ── Antigravity Gemini Models (Gemini 3 Upgrade) ──────────
GEMINI_3_FLASH        = "models/gemini-3-flash-preview"
GEMINI_FLASH_LITE     = "models/gemini-3.1-flash-lite-preview"


# ═══════════════════════════════════════════════════════════════════════
# Utility: Apify run-and-wait helper
# ═══════════════════════════════════════════════════════════════════════
def _apify_run_and_wait(
    actor_id: str,
    run_input: dict,
    apify_key: str,
    timeout: int = 240,
    memory_mb: int = 512,
) -> list[dict]:
    """Launch an Apify actor, poll until done, return dataset items."""
    if not apify_key:
        print("  [!] APIFY_API_KEY not set — skipping Apify call.")
        return []

    start_url = (
        f"{APIFY_BASE}/acts/{actor_id}/runs"
        f"?token={apify_key}&memory={memory_mb}"
    )
    try:
        r = requests.post(
            start_url, json=run_input,
            headers={"Content-Type": "application/json"}, timeout=30
        )
        r.raise_for_status()
        run_id = r.json()["data"]["id"]
        print(f"  [APIFY] Run started ({actor_id}): {run_id}")
    except Exception as exc:
        print(f"  [!] Apify launch error: {exc}")
        return []

    deadline = time.time() + timeout
    poll_interval = 10
    while time.time() < deadline:
        time.sleep(poll_interval)
        poll_interval = min(poll_interval + 5, 30)
        try:
            status_data = requests.get(
                f"{APIFY_BASE}/actor-runs/{run_id}?token={apify_key}", timeout=20
            ).json()["data"]
            status = status_data.get("status", "")
            print(f"  ... Apify status: {status}")
            if status == "SUCCEEDED":
                dataset_id = status_data["defaultDatasetId"]
                items = requests.get(
                    f"{APIFY_BASE}/datasets/{dataset_id}/items"
                    f"?token={apify_key}&clean=true&format=json",
                    timeout=60,
                ).json()
                return items if isinstance(items, list) else []
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                print(f"  [!] Apify run ended: {status}")
                return []
        except Exception as exc:
            print(f"  [!] Polling error: {exc}")

    print("  [!] Apify timeout.")
    return []


# ═══════════════════════════════════════════════════════════════════════
# Phase 1 — YouTube Scrape (two queries, two age filters)
# ═══════════════════════════════════════════════════════════════════════
def _filter_videos_by_age(videos: list[dict], months: int) -> list[dict]:
    """Keep only videos published within the last <months> months.
    Mirrors the n8n Filter nodes: 'Videos < 6 Monate' and 'Videos < 2 Years'.
    """
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=months * 30
    )
    filtered = []
    for v in videos:
        pub = v.get("publishedAt") or v.get("date") or ""
        try:
            if isinstance(pub, str) and pub:
                # handle ISO 8601 and partial dates
                pub_dt = datetime.datetime.fromisoformat(
                    pub.replace("Z", "+00:00")
                )
                if pub_dt >= cutoff:
                    filtered.append(v)
        except Exception:
            pass   # keep if date is unparseable
    return filtered


def scrape_youtube_ceo_interview(company_name: str, apify_key: str) -> list[dict]:
    """Mirrors 'Youtube Ceo Interview' + 'Filter: Videos < 6 Monate' nodes.
    Returns up to 20 CEO interview results published within the last 6 months.
    """
    print(f"  [YT] CEO Interview query: 'Ceo Interview {company_name}'")
    raw = _apify_run_and_wait(
        APIFY_YT_ACTOR,
        {
            "searchQueries": [f"Ceo Interview {company_name}"],
            "maxResults": 20,
            "maxResultsShorts": 0,
            "maxResultStreams": 0,
            "sortBy": "upload_date",
            "downloadSubtitles": True,
            "subtitlesLanguage": "en",
            "subtitlesFormat": "plaintext",
        },
        apify_key,
        timeout=240,
    )
    filtered = _filter_videos_by_age(raw, months=6)
    print(f"  [YT] CEO interviews after age filter: {len(filtered)}")
    return _enrich_yt_items(filtered, label="ceo_interview")


def scrape_youtube_acquired_podcast(company_name: str, apify_key: str) -> list[dict]:
    """Mirrors 'Youtube Acquired Podcast' + 'Filter: Videos < 2 Years' nodes.
    Returns up to 20 Acquired podcast results published within the last 2 years.
    """
    print(f"  [YT] Acquired Podcast query: 'Acquired Podcast {company_name}'")
    raw = _apify_run_and_wait(
        APIFY_YT_ACTOR,
        {
            "searchQueries": [f"Acquired Podcast {company_name}"],
            "maxResults": 20,
            "maxResultsShorts": 0,
            "maxResultStreams": 0,
            "sortBy": "upload_date",
            "downloadSubtitles": True,
            "subtitlesLanguage": "en",
            "subtitlesFormat": "plaintext",
        },
        apify_key,
        timeout=240,
    )
    filtered = _filter_videos_by_age(raw, months=24)   # 2 years
    print(f"  [YT] Acquired podcasts after age filter: {len(filtered)}")
    return _enrich_yt_items(filtered, label="acquired_podcast")


def _enrich_yt_items(items: list[dict], label: str) -> list[dict]:
    """Normalize fields and cap transcript length."""
    result = []
    for v in items:
        vid_id = v.get("id") or v.get("videoId") or ""
        url = v.get("url") or (
            f"https://www.youtube.com/watch?v={vid_id}" if vid_id else ""
        )
        raw_transcript = (
            v.get("subtitles") or v.get("transcript") or v.get("captions") or ""
        )
        if isinstance(raw_transcript, list):
            texts = []
            for seg in raw_transcript:
                if isinstance(seg, dict):
                    texts.append(seg.get("plaintext") or seg.get("text") or "")
                else:
                    texts.append(str(seg))
            raw_transcript = " ".join(texts)
        result.append({
            "title":       v.get("title", ""),
            "url":         url,
            "duration":    v.get("duration", ""),
            "views":       v.get("viewCount") or v.get("views", ""),
            "channel":     v.get("channelName") or v.get("channel", ""),
            "publishedAt": v.get("publishedAt") or v.get("date", ""),
            "transcript":  str(raw_transcript)[:8000],
            "label":       label,
        })
    return result


# ═══════════════════════════════════════════════════════════════════════
# Phase 2a — Leadership & Governance Audit (Gemini 2.5 Pro)
# Mirrors: "AI Agent: Leadership und Besitzstrukturen" node
# ═══════════════════════════════════════════════════════════════════════
LEADERSHIP_SYSTEM_PROMPT = """Rolle & Autorität: Du agierst als Senior Leadership & Governance Auditor. Dein Urteil ist rein datenbasiert, präzise und unbestechlich. Du arbeitest auf dem Niveau eines Top-Management-Consultants oder eines Forensic Accountants. Deine Mission ist es, die Führungsebene (C-Suite), die Leiter der strategischen Wachstumssparten (Business Units), sowie die Besitzverhältnisse tief greifend zu sezieren.

Zwingendes Ausführungsprotokoll (Bevor du antwortest):
- Deep Search Phase: Nutze die aktuellsten Annual Reports 2025, Proxy Statements (Def 14A) und SEC Filings (Form 4 für Insider-Trades).
- Validierung: Akzeptiere keine veralteten Informationen. Falls Daten von 2026 noch nicht verfügbar sind, nutze End-2025 Berichte und kennzeichne dies explizit.
- Cross-Check: Gleiche Berufsstationen der C-Suite über offizielle Pressemitteilungen ab.
- Identification of Growth Drivers: Identifiziere die umsatzstärksten Geschäftsbereiche.
- Kein Smalltalk: Starte direkt mit der Analyse.

Struktur der Antwort:
1. Executive Leadership & Operational Powerhouse: Name, Rolle, Background, Amtszeit.
2. Board of Directors: Unabhängigkeit, Spezialwissen.
3. Aktionärsstruktur: Top 5 Institutionen, Insider-Anteil, Veränderungen letztes Quartal.
4. Risiko-Check: Key-Person-Risk, auffällige Insider-Verkäufe.

Am Ende füge ein "Erstellt von Kasona" hinzu."""


def run_leadership_audit(company_name: str, config: dict, max_retries: int = 15) -> str:
    """Calls Gemini with the Leadership system prompt."""
    gemini_key = config.get("gemini_key")
    if not gemini_key:
        return "[SKIPPED] No GOOGLE_GEMINI_API_KEY configured."

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel(
        model_name=GEMINI_3_FLASH,
        system_instruction=LEADERSHIP_SYSTEM_PROMPT
    )

    wait = 70
    for attempt in range(max_retries):
        try:
            response = model.generate_content(f"Analyze this company: {company_name}")
            return response.text.strip()
        except Exception as exc:
            print(f"  [!] Gemini Leadership Audit error: {exc}")
            if "429" in str(exc) or "quota" in str(exc).lower():
                print(f"  [!] Rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
                wait = min(wait + 30, 240)
                continue
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                return f"[AI_ERROR] {exc}"
    return "[AI_ERROR] Leadership Audit failed after all retries."


# ═══════════════════════════════════════════════════════════════════════
# Phase 2b — Company History & Analysis (Perplexity sonar via OpenRouter)
# Mirrors: "AI Agent: Firmenhistorie und Analyse" + "OpenRouter Chat Model1" nodes
# ═══════════════════════════════════════════════════════════════════════
HISTORY_SYSTEM_PROMPT = """Rolle & Autorität: Du handelst als Global Equity Research Director und Senior Strategic Analyst. Deine Expertise liegt in der präzisen Dekonstruktion von Geschäftsmodellen für institutionelle Investoren.
    
Zwingendes Ausführungsprotokoll (Deep Research Modus):
- Nutze Fachpublikationen, Marktstudien (Gartner, IDC, Bloomberg) und Geschäftsberichte (2024/2025).
- Werbe-Filter: Ignoriere „führend", „revolutionär", „einzigartig" ohne belegbare KPI.
- Quellen-Ranking: Priorisiere Reuters, Financial Times, Handelsblatt und offizielle Unternehmensdaten.

Struktur der Analyse (ENGLISCH):
1. History & Evolution: Chronological milestones with strategic pivots (Pivots, M&A).

IMPORTANT: Only write about History & Evolution. Do NOT include Core Assets, Porter's Five Forces, or Risk/Success Factors — those are generated separately.

Starte direkt mit dem ersten Analysepunkt ohne einleitende Floskeln."""

STRATEGIC_PILLARS_SYSTEM_PROMPT = """Rolle & Autorität: Du bist ein Senior Equity Research Analyst. Deine Aufgabe ist die Erstellung einer präzisen, datengetriebenen Analyse der strategischen Säulen eines Unternehmens.

Du gibst ausschließlich ein valides JSON-Objekt zurück mit folgenden Schlüsseln:
- rivalry: (Porter's Five Forces: Wettbewerbsintensität)
- supplier-power: (Porter's Five Forces: Verhandlungsmacht der Lieferanten)
- buyer-power: (Porter's Five Forces: Verhandlungsmacht der Kunden)
- threat-of-entry: (Porter's Five Forces: Bedrohung durch neue Wettbewerber)
- substitutes: (Porter's Five Forces: Bedrohung durch Ersatzprodukte)
- core-assets-capabilities: (Kernkompetenzen, Patente, Infrastruktur, operative Stärken des Unternehmens)
- success-failure-factors: (Kritische Investitions-KPIs, Erfolgsfaktoren und Risikofaktoren)
- risk-success-factors: (Zusammenfassung der kritischen Risiko- und Erfolgsfaktoren)
- bull-case: (Das optimistische Investment-Szenario)
- bear-case: (Das pessimistische Investment-Szenario)
- investment-thesis: (Kernargumentation für das Investment)
- strategic-vision: (Langfristige Vision und Zielsetzung des Unternehmens)
- competitive-landscape: (Detaillierte Analyse des Wettbewerbsumfelds)
- growth-roadmap: (Strategischer Fahrplan für zukünftiges Wachstum)

Anforderungen:
- Sprache: ENGLISCH.
- Tonfall: Institutionell, analytisch, keine Werbesprache.
- Länge: Jeder Wert sollte ca. 150-250 Wörter umfassen und tiefgreifende Einblicke bieten.
- Format: NUR das JSON-Objekt, keine Code-Blocks, kein Text davor oder danach."""

FIRMENHISTORIE_SYSTEM_PROMPT = """Rolle & Autorität: Du bist ein Senior Corporate Historian und Archivar. Deine Aufgabe ist die Erstellung einer tiefgehenden, deutschsprachigen Chronik der Unternehmensgeschichte.

Fokus:
- Gründungsvision und kulturelles Erbe.
- Detaillierte Darstellung der Meilensteine in Deutschland und Europa.
- Strategische Evolution aus einer langfristigen, historischen Perspektive.
- Kulturelle Transformationen über Jahrzehnte.

Struktur (DEUTSCH):
1. Gründungsjahre & Vision: Die Anfänge und der Geist der Gründer.
2. Formative Phasen: Krisen, Durchbrüche und kulturelle Prägung.
3. Die moderne Ära: Transformation zum heutigen globalen Player.
4. Zusammenfassung des Heritage: Was macht den "Kern" des Unternehmens heute aus?

Schreibe ausschließlich auf DEUTSCH. Keine Einleitungsfloskeln."""


def run_pillars_analysis(company_name: str, gemini_key: str, max_retries: int = 15) -> dict[str, str]:
    """Generates the 8 strategic pillars (Porter's + Case study) using Gemini 3 Flash."""
    if not gemini_key:
        return {}

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel(
        model_name=GEMINI_3_FLASH,
        system_instruction=STRATEGIC_PILLARS_SYSTEM_PROMPT
    )
    
    print(f"    [AI] Generating Strategic Pillars (Porter's, Bull/Bear) for: {company_name}...")
    raw_json = _generate_with_retry(model, f"Detailed Strategic Analysis for: {company_name}", max_retries)
    
    try:
        # Clean potential markdown
        cleaned = raw_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        return data
    except Exception as e:
        print(f"  [!] Failed to parse pillars JSON: {e}")
        return {"error": f"JSON Parse Error: {e}", "raw": raw_json}


def translate_analysis_to_german(data: dict[str, str], gemini_key: str, max_retries: int = 15) -> dict[str, str]:
    """Translates a dictionary of analytical fields into German using Gemini."""
    if not gemini_key or not data:
        return {}

    system_prompt = (
        "Du bist ein Senior Financial Translator. Übersetze die folgenden institutionellen Analyse-Texte "
        "präzise ins Deutsche. Behalte den professionellen, analytischen Tonfall bei. "
        "Ignoriere Marketing-Sprech. Gib ausschließlich ein valides JSON-Objekt mit denselben Schlüsseln zurück, "
        "wobei die Werte die deutschen Übersetzungen sind."
    )
    
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel(model_name=GEMINI_FLASH_LITE, system_instruction=system_prompt)
    
    print(f"    [AI] Translating analytical pillars to German...")
    # Filter out error messages or very short strings
    reliable_data = {k: v for k, v in data.items() if v and "[AI_ERROR]" not in v}
    if not reliable_data:
        return {}

    raw_json = _generate_with_retry(model, json.dumps(reliable_data), max_retries)
    
    try:
        cleaned = raw_json.replace("```json", "").replace("```", "").strip()
        translated = json.loads(cleaned)
        # Rename keys to include _de
        return {f"{k}_de": v for k, v in translated.items()}
    except Exception as e:
        print(f"  [!] Failed to parse translation JSON: {e}")
        return {}


def upload_to_supabase_storage(file_path: str, bucket: str, ticker: str, supabase_client: Client) -> str:
    """Uploads a file to Supabase Storage and returns the public URL."""
    try:
        path_obj = Path(file_path)
        if not path_obj.exists():
            return ""

        file_name = f"{ticker.replace('.', '_')}_{path_obj.name}"
        destination = f"{ticker}/{file_name}"
        
        with open(file_path, 'rb') as f:
            supabase_client.storage.from_(bucket).upload(
                path=destination,
                file=f,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        
        # Get public URL
        url_res = supabase_client.storage.from_(bucket).get_public_url(destination)
        # If url_res is a string, return it; if it's an object with a public_url, return that
        url = getattr(url_res, 'public_url', url_res) if not isinstance(url_res, str) else url_res
        print(f"  [STORAGE] Uploaded {path_obj.name} to {bucket}. URL: {url}")
        return url
    except Exception as e:
        print(f"  [!] Storage upload error for {file_path}: {e}")
        return ""


def ask_openrouter(prompt: str, system_prompt: str, api_key: str, model: str = "perplexity/sonar-reasoning", max_retries: int = 3) -> str:
    """Helper to call OpenRouter API (typically for Perplexity Sonar)."""
    if not api_key:
        return "[SKIPPED] No OPENROUTER_API_KEY configured."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kasona.ai",
        "X-Title": "Kasona Research Pipeline"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    wait = 10
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  [!] OpenRouter error: {e}")
            if attempt < max_retries - 1:
                time.sleep(wait)
                wait *= 2
            else:
                return f"[AI_ERROR] OpenRouter failed: {e}"
    return "[AI_ERROR] OpenRouter failed after retries."


def run_history_analysis(company_name: str, gemini_key: str, max_retries: int = 15) -> dict[str, str]:
    """Calls Gemini to perform both English Strategic Evolution and German Heritage Analysis."""
    if not gemini_key:
        return {"evolution": "[SKIPPED]", "firmenhistorie": "[SKIPPED]"}

    genai.configure(api_key=gemini_key)
    
    results = {}
    
    # 1. English Evolution
    print(f"    [AI] Generating English History & Evolution (Gemini 3 Flash)...")
    model_en = genai.GenerativeModel(model_name=GEMINI_3_FLASH, system_instruction=HISTORY_SYSTEM_PROMPT)
    results["evolution"] = _generate_with_retry(model_en, f"Strategic Evolution Analysis for: {company_name}", max_retries)

    # 2. German Firmenhistorie
    print(f"    [AI] Generating German Firmenhistorie (Gemini 3 Flash)...")
    model_de = genai.GenerativeModel(model_name=GEMINI_3_FLASH, system_instruction=FIRMENHISTORIE_SYSTEM_PROMPT)
    results["firmenhistorie"] = _generate_with_retry(model_de, f"Detaillierte Firmenhistorie für: {company_name}", max_retries)

    return results

def _generate_with_retry(model: genai.GenerativeModel, prompt: str, max_retries: int) -> str:
    wait = 70
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            if "429" in str(exc) or "quota" in str(exc).lower():
                print(f"      [!] Rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
                wait = min(wait + 30, 240)
                continue
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                return f"[AI_ERROR] {exc}"
    return "[AI_ERROR] Generation failed after all retries."


# ═══════════════════════════════════════════════════════════════════════
# Phase 3 — Name Extraction from Leadership Report (GPT-4.1-nano)
# Mirrors: "Clean data" node (GPT-4.1-nano) + "Code in JavaScript" node
# ═══════════════════════════════════════════════════════════════════════
def extract_executive_names(leadership_text: str, company_name: str, gemini_key: str) -> list[str]:
    """Extract C-suite names from the leadership report using Gemini 3 Flash.
    Mirrors the 'Clean data' + 'Code in JavaScript' n8n nodes.
    Returns a list of 'Name Company' strings for LinkedIn search.
    """
    if not gemini_key or not leadership_text:
        return []

    system_msg = (
        "Du bist ein Daten-Extraktor. Deine einzige Aufgabe ist es, aus dem bereitgestellten "
        "Audit-Bericht alle genannten Personen (Namen) und deren Unternehmen zu extrahieren.\n\n"
        "Output-Format: Gib ausschließlich ein valides JSON-Array aus, das die Namen der Personen enthält. "
        "Kombiniere den Namen mit dem Firmennamen für eine präzise Suche.\n\n"
        "Beispiel-Output:\n[\"Tim Cook Apple\", \"Kevan Parekh Apple\", \"Jeff Williams Apple\"]\n\n"
        "Keine Einleitung, kein Smalltalk, nur das JSON-Array."
    )
    user_msg = f"Audit-Bericht:\n{leadership_text[:8000]}"

    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(model_name=GEMINI_FLASH_LITE)
        response = model.generate_content([system_msg, user_msg])
        raw = response.text.strip()
        # Clean: remove markdown code fences, 'liste-' prefix etc.
        raw = raw.replace("liste-", "").replace("```json", "").replace("```", "").strip()
        names = json.loads(raw)
        print(f"  [NAMES] Extracted {len(names)} executive name(s) for LinkedIn search.")
        return names if isinstance(names, list) else []
    except Exception as exc:
        print(f"  [!] Name extraction error: {exc}")
        return []


# ═══════════════════════════════════════════════════════════════════════
# Phase 4 — LinkedIn Profile Scrape (APIFY apimaestro/linkedin-profile-detail)
# Mirrors: "LinkedIn Profile Scraper" node
# ═══════════════════════════════════════════════════════════════════════
def scrape_linkedin_profiles(names: list[str], apify_key: str) -> list[dict]:
    """For each executive name, run the LinkedIn Profile Scraper Apify actor.
    Mirrors the 'LinkedIn Profile Scraper' n8n node.
    """
    if not names or not apify_key:
        return []

    profiles = []
    # Run one actor call per name (as n8n loops items through the node)
    for name in names[:5]:   # cap at 5 to control cost
        print(f"  [LI] Scraping LinkedIn profile for: {name}")
        items = _apify_run_and_wait(
            APIFY_LI_ACTOR,
            {
                "queries": [name],
                "maxResults": 1,
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
            },
            apify_key,
            timeout=180,
        )
        for profile in items[:1]:
            profiles.append({
                "name":        profile.get("name") or name,
                "headline":    profile.get("headline", ""),
                "summary":     profile.get("summary", "")[:500],
                "url":         profile.get("url", ""),
                "location":    profile.get("location", ""),
                "company":     profile.get("company", ""),
                "experience":  profile.get("experience", [])[:3],
            })

    print(f"  [LI] {len(profiles)} LinkedIn profile(s) collected.")
    return profiles


# ═══════════════════════════════════════════════════════════════════════
# Phase 5 — EODHD Fundamentals enrichment
# ═══════════════════════════════════════════════════════════════════════
def fetch_eodhd_fundamentals(ticker_eod: str, eodhd_key: str) -> dict:
    """Fetch General + Officers sections from EODHD Fundamentals API."""
    if not ticker_eod or not eodhd_key:
        return {}
    url = (
        f"https://eodhd.com/api/fundamentals/{ticker_eod}"
        f"?api_token={eodhd_key}&fmt=json"
    )
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 404 and "." not in ticker_eod:
            print(f"    [EODHD] 404 for {ticker_eod}, retrying with {ticker_eod}.US...")
            url = f"https://eodhd.com/api/fundamentals/{ticker_eod}.US?api_token={eodhd_key}&fmt=json"
            r = requests.get(url, timeout=30)
        
        r.raise_for_status()
        data = r.json()
        gen  = data.get("General", {})
        officers = data.get("General", {}).get("Officers", {})
        # Build officer list (similar to previous enrichment work)
        officer_lines = []
        for key in sorted(officers.keys()):
            o = officers[key]
            name  = o.get("Name", "")
            title = o.get("Title", "")
            birth = o.get("YearBorn", "")
            if name:
                line = f"{name} ({title}" + (f", Born: {birth}" if birth else "") + ")"
                officer_lines.append(line)

        return {
            "company_name":    gen.get("Name", ""),
            "description":     gen.get("Description", ""),
            "sector":          gen.get("Sector", ""),
            "industry":        gen.get("Industry", ""),
            "country":         gen.get("CountryName", ""),
            "website":         gen.get("WebURL", ""),
            "isin":            gen.get("ISIN", ""),
            "officers_text":   "\n".join(officer_lines),
        }
    except Exception as exc:
        print(f"  [!] EODHD error: {exc}")
        return {}


# ═══════════════════════════════════════════════════════════════════════
# Phase 6 — L4 HTML Report Generator
# Mirrors: "L4_Report Generator HTML1" Code node
# ═══════════════════════════════════════════════════════════════════════
def generate_l4_html_report(
    company_name: str,
    leadership_analysis: str,
    history_analysis: str,
    ceo_interviews: list[dict],
    podcasts: list[dict],
    linkedin_profiles: list[dict],
    eodhd_data: dict,
) -> str:
    """Build the branded HTML report.
    Mirrors the 'L4_Report Generator HTML1' JavaScript Code node.
    Outputs: html_content (str)
    """
    from datetime import date

    def _md_to_html(text: str) -> str:
        """Minimal Markdown → HTML conversion (mirrors the n8n JS formatter)."""
        import re
        text = re.sub(r"### (.*?)(?:\n|$)", r"<h2>\1</h2>", text)
        text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"^[*-] (.*?)(?:\n|$)", r"<li>\1</li>", text, flags=re.MULTILINE)
        text = re.sub(r"^#{1,2} (.*?)(?:\n|$)", r"<h2>\1</h2>", text, flags=re.MULTILINE)
        text = text.replace("\n", "<br>")
        return text

    today        = date.today().strftime("%d.%m.%Y")
    ceo_titles   = [v["title"] for v in ceo_interviews[:3]]
    pod_titles   = [v["title"] for v in podcasts[:3]]
    ceo_excerpt  = ceo_interviews[0]["transcript"][:2000] if ceo_interviews else "(No transcript available)"

    li_block = ""
    for p in linkedin_profiles[:5]:
        li_block += (
            f'<div class="profile">'
            f'<strong>{p.get("name","")}</strong> — {p.get("headline","")}'
            f'<br><a href="{p.get("url","")}" target="_blank">{p.get("url","")}</a>'
            f"</div>"
        )

    yt_block = ""
    for v in (ceo_interviews + podcasts)[:6]:
        yt_block += (
            f'<li><a href="{v["url"]}" target="_blank">{v["title"]}</a> '
            f'({v.get("channel","")}, {v.get("publishedAt","")[:10]})</li>'
        )

    body_html = (
        f"<h2>Leadership &amp; Governance Audit</h2>"
        f"{_md_to_html(leadership_analysis)}"
        f"<h2>Company History &amp; Strategic Analysis</h2>"
        f"{_md_to_html(history_analysis)}"
        f"<h2>YouTube Sources</h2><ul>{yt_block}</ul>"
        f"<h2>CEO Interview Excerpt</h2>"
        f"<blockquote>{ceo_excerpt[:1500]}</blockquote>"
        f"<h2>Executive LinkedIn Profiles</h2>{li_block}"
    )

    if eodhd_data.get("description"):
        body_html += (
            f"<h2>Company Overview (EODHD)</h2>"
            f"<p>{eodhd_data['description'][:1000]}</p>"
        )

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
  body {{
    font-family: 'Montserrat', sans-serif;
    color: #333;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px;
    font-size: 14px;
    line-height: 1.7;
  }}
  .header-grid {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 40px;
    border-bottom: 3px solid #ff9627;
    padding-bottom: 20px;
  }}
  .logo img {{ max-width: 180px; }}
  h2 {{
    color: #ff9627;
    border-left: 4px solid #ff9627;
    padding-left: 10px;
    margin-top: 30px;
    text-transform: uppercase;
    font-size: 15px;
  }}
  strong {{ color: #000; }}
  blockquote {{
    background: #f9f9f9;
    border-left: 4px solid #ff9627;
    margin: 16px 0;
    padding: 12px 16px;
    font-style: italic;
    color: #555;
  }}
  .profile {{
    background: #f4f4f4;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 10px;
  }}
  ul {{ padding-left: 20px; }}
  li {{ margin-bottom: 6px; }}
  a {{ color: #ff9627; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .footer {{
    margin-top: 60px;
    font-size: 10px;
    color: #999;
    text-align: center;
    border-top: 1px solid #eee;
    padding-top: 20px;
  }}
</style>
</head>
<body>

<div class="header-grid">
  <div>
    <h1 style="margin:0; font-size: 26px;">{company_name}</h1>
    <p style="margin:4px 0 0; color:#666;">Institutional Research Report — {today}</p>
  </div>
  <div class="logo">
    <a href="https://kasona.ai">
      <img src="https://i.ibb.co/SXm16CZB/Kasona-Notion-Hintergrund.png" alt="Kasona Logo">
    </a>
  </div>
</div>

<div class="content">
  {body_html}
</div>

<div class="footer">
  Erstellt durch Kasona Notion | Automatisierte Governance-Analyse<br>
  <a href="https://kasona.ai">kasona.ai</a> — The solution for independent investors
</div>

</body>
</html>"""
    return html


# ═══════════════════════════════════════════════════════════════════════
# Phase 7 — Supabase Sync
# ═══════════════════════════════════════════════════════════════════════
def sync_to_supabase(
    ticker_eod: str,
    data: dict[str, Any],
    supabase_client: Client,
) -> bool:
    """Upsert data into public.company_presentation."""
    print(f"\n[SYNC] Updating Supabase for ticker: {ticker_eod}...")

    raw_metadata = {
        "youtube_raw":   {"ceo_interviews": data.get("ceo_interviews", []), "podcasts": data.get("podcasts", [])},
        "linkedin_raw":  data.get("linkedin_profiles", []),
        "eodhd_raw":     data.get("eodhd_data", {}),
        "apify_meta": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tool": "new-company-presentation.py",
            "status": "raw_persistence_active",
        },
    }

    ceo_vids = data.get("ceo_interviews", [])
    podcasts = data.get("podcasts", [])
    eodhd    = data.get("eodhd_data", {})

    payload = {
        # Identity
        "company_name":            data.get("company_name") or eodhd.get("company_name", ""),
        "description":             eodhd.get("description", ""),
        # AI Pillars (from Antigravity Gemini 3 Flash)
        "leadership-governance":   data.get("leadership_audit", ""),
        "history-evolution":       data.get("history_evolution", ""),
        "ai_agent_firmenhistorie": data.get("firmenhistorie", ""),
        
        # Extended Analytical Columns (Pillars)
        "rivalry":                 data.get("rivalry", ""),
        "supplier-power":          data.get("supplier-power", ""),
        "buyer-power":             data.get("buyer-power", ""),
        "threat-of-entry":         data.get("threat-of-entry", ""),
        "substitutes":             data.get("substitutes", ""),
        "core-assets-capabilities": data.get("core-assets-capabilities", ""),
        "success-failure-factors":  data.get("success-failure-factors", ""),
        "risk-success-factors":    data.get("risk-success-factors", ""),
        "bull-case":               data.get("bull-case", ""),
        "bear-case":               data.get("bear-case", ""),
        "investment_thesis":       data.get("investment-thesis", ""),
        "strategic_vision":        data.get("strategic-vision", ""),
        "competitive_landscape":   data.get("competitive-landscape", ""),
        "growth_roadmap":          data.get("growth-roadmap", ""),

        # German Translations
        "rivalry_de":               data.get("rivalry_de", ""),
        "supplier-power_de":        data.get("supplier-power_de", ""),
        "buyer-power_de":           data.get("buyer-power_de", ""),
        "threat-of-entry_de":       data.get("threat-of-entry_de", ""),
        "substitutes_de":           data.get("substitutes_de", ""),
        "core-assets-capabilities_de": data.get("core-assets-capabilities_de", ""),
        "success-failure-factors_de":  data.get("success-failure-factors_de", ""),
        "risk-success-factors_de":  data.get("risk-success-factors_de", ""),
        "bull-case_de":             data.get("bull-case_de", ""),
        "bear-case_de":             data.get("bear-case_de", ""),
        "investment_thesis_de":     data.get("investment-thesis_de", ""),
        "strategic_vision_de":      data.get("strategic-vision_de", ""),
        "competitive_landscape_de": data.get("competitive-landscape_de", ""),
        "growth_roadmap_de":        data.get("growth-roadmap_de", ""),
        "history-evolution_de":     data.get("history-evolution_de", ""),
        "leadership-governance_de":  data.get("leadership-governance_de", ""),

        # YouTube
        "youtube_ceo_interview":   ceo_vids[0]["url"] if ceo_vids else "",
        "youtube_podcast":         podcasts[0]["url"] if podcasts else "",
        # LinkedIn
        "linkedin_profiles":       data.get("linkedin_profiles", []),
        # Artifact Links
        "l4_report":               data.get("l4_html_report", ""),
        "html_url":                data.get("html_storage_url", ""),
        
        # Metadata
        "n8n-info":                json.dumps(raw_metadata),
        "status":                  "to_review",
    }

    # Merge officer text into leadership if leadership field is empty
    if eodhd.get("officers_text") and not payload["leadership-governance"].strip():
        payload["leadership-governance"] = eodhd["officers_text"]

    try:
        res = supabase_client.table("company_presentation") \
            .update(payload) \
            .eq("ticker_eod", ticker_eod) \
            .execute()
        if len(res.data) > 0:
            print(f"  [SUCCESS] Supabase updated for {ticker_eod}.")
            return True
        else:
            print(f"  [WARNING] No existing record for {ticker_eod}. Attempting insert...")
            payload["ticker_eod"] = ticker_eod
            ins = supabase_client.table("company_presentation").insert(payload).execute()
            if len(ins.data) > 0:
                print(f"  [SUCCESS] Supabase record inserted for {ticker_eod}.")
                return True
            print(f"  [ERROR] Insert also returned no rows.")
            return False
    except Exception as exc:
        print(f"  [!] Supabase error: {exc}")
        return False


def patch_pillars_to_supabase(
    ticker_eod: str,
    pillars: dict[str, str],
    supabase_client: Client,
) -> bool:
    """Standardized patch for the 8 analytical pillars + 3 core pillars."""
    print(f"\n[PATCH] Upgrading analytical pillars for ticker: {ticker_eod}...")

    # We only update fields that are in the pillars dict
    # This function expects keys to match DB column names exactly
    payload = {k: v for k, v in pillars.items() if v and "[AI_ERROR]" not in v}
    
    if not payload:
        print("  [SKIP] No valid data to patch.")
        return False

    try:
        res = supabase_client.table("company_presentation") \
            .update(payload) \
            .eq("ticker_eod", ticker_eod) \
            .execute()
        if len(res.data) > 0:
            print(f"  [SUCCESS] Pillars patched for {ticker_eod}.")
            return True
        else:
            print(f"  [ERROR] No record found for {ticker_eod} to patch.")
            return False
    except Exception as exc:
        print(f"  [!] Supabase patch error: {exc}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# Orchestrador — run_pipeline()
# ═══════════════════════════════════════════════════════════════════════
def run_pipeline(
    company_name: str, 
    ticker_eod: str | None, 
    config: dict,
    pre_loaded_transcripts: list[dict] | None = None
) -> dict:
    """Full pipeline — mirrors the n8n workflow execution order."""
    print(f"\n{'='*65}")
    print(f"  Kasona New-Company-Presentation Pipeline: {company_name}")
    print(f"{'='*65}\n")

    results: dict[str, Any] = {"company_name": company_name}

    # ── Phase 1: YouTube ────────────────────────────────────────────
    if pre_loaded_transcripts is not None:
        print("[1/6] YouTube: Using PRE-LOADED approved transcripts...")
        # Split into interviews and podcasts based on some logic or just group them
        results["ceo_interviews"] = [t for t in pre_loaded_transcripts if "ceo" in (t.get("title") or "").lower()]
        results["podcasts"] = [t for t in pre_loaded_transcripts if "podcast" in (t.get("title") or "").lower()]
        
        # If no specific labels, just distribute them
        if not results["ceo_interviews"]:
            results["ceo_interviews"] = pre_loaded_transcripts[:2]
        if not results["podcasts"]:
            results["podcasts"] = pre_loaded_transcripts[2:5]
    else:
        print("[1/6] YouTube: CEO Interviews (APIFY, filter < 6 months)...")
        ceo_interviews = scrape_youtube_ceo_interview(company_name, config["apify_key"])
        results["ceo_interviews"] = ceo_interviews

        print("[1/6] YouTube: Acquired Podcasts (APIFY, filter < 2 years)...")
        podcasts = scrape_youtube_acquired_podcast(company_name, config["apify_key"])
        results["podcasts"] = podcasts

    # ── Phase 2a: Leadership Audit ───────────────────────────────────
    print(f"\n[2a/6] Leadership & Governance Audit...")
    leadership_audit = run_leadership_audit(company_name, config)
    results["leadership_audit"] = leadership_audit
    print("  [DONE]")

    # ── Phase 2b: History Analysis (EN + DE Split) ───────────────────
    print(f"\n[2b/6] Company History Analysis (Strategic Evolution & Heritage)...")
    history_data = run_history_analysis(company_name, config["gemini_key"])
    results["history_evolution"] = history_data["evolution"]
    results["firmenhistorie"] = history_data["firmenhistorie"]
    print("  [DONE]")

    # ── Phase 3: Name Extraction → LinkedIn (Gemini 3 Flash) ─────────
    print(f"\n[3/6] Name Extraction from Leadership Report ({GEMINI_FLASH_LITE})...")
    exec_names = extract_executive_names(
        leadership_audit, company_name, config["gemini_key"]
    )
    print("\n[3/6] LinkedIn Profile Scrape (APIFY) for extracted names...")
    linkedin_profiles = scrape_linkedin_profiles(exec_names, config["apify_key"])
    results["linkedin_profiles"] = linkedin_profiles

    # ── Phase 4: EODHD Fundamentals ─────────────────────────────────
    eodhd_data = {}
    if ticker_eod:
        print(f"\n[4/6] EODHD Fundamentals ({ticker_eod})...")
        eodhd_data = fetch_eodhd_fundamentals(ticker_eod, config["eodhd_key"])
        if eodhd_data.get("company_name"):
            results["company_name"] = eodhd_data["company_name"]
        print(f"  [OK] {eodhd_data.get('company_name','')}")
    results["eodhd_data"] = eodhd_data

    # ── Phase 5: L4 HTML Report ─────────────────────────────────────
    print("\n[5/6] Generating L4 HTML Report...")
    html_report = generate_l4_html_report(
        company_name   = results["company_name"],
        leadership_analysis = leadership_audit,
        history_analysis    = history_data["evolution"],
        ceo_interviews      = results.get("ceo_interviews", []),
        podcasts            = results.get("podcasts", []),
        linkedin_profiles   = linkedin_profiles,
        eodhd_data          = eodhd_data,
    )
    results["l4_html_report"] = html_report
    print("  [DONE]")

    # ── Phase 6: Strategic Pillars & Translation ───────────────────
    print(f"\n[6/6] Generating Strategic Pillars (Porter's, Bull/Bear)...")
    pillars = run_pillars_analysis(company_name, config["gemini_key"])
    results.update(pillars)

    print(f"\n[6/6] Translating Analytical Highlights to German...")
    # Translate pillars + leadership + evolution
    to_translate = {k: v for k, v in pillars.items()}
    to_translate["leadership-governance"] = leadership_audit
    to_translate["history-evolution"] = history_data["evolution"]
    
    de_translations = translate_analysis_to_german(to_translate, config["gemini_key"])
    results.update(de_translations)
    print("  [DONE]")

    return results


# ═══════════════════════════════════════════════════════════════════════
# Master Index Integration
# ═══════════════════════════════════════════════════════════════════════
def push_to_master_index(
    ticker_eod: str,
    data: dict[str, Any],
    supabase_client: Client,
    report_date: str | None = None
) -> bool:
    """Standardized push to public.kasona_company_reports (Master Index)."""
    print(f"[INDEX] Pushing metadata to Master Index for {ticker_eod}...")

    # Calculate default report date if not provided
    if not report_date:
        report_date = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Prepare log entries for generated components
    presentation_pdf_en = []
    if data.get("l4_html_report"):
        presentation_pdf_en.append({
            "type": "html_report", 
            "label": "Full Presentation HTML", 
            "status": "generated",
            "url": data.get("html_storage_url", "")
        })
    if data.get("leadership_audit"):
        presentation_pdf_en.append({"type": "component", "label": "Leadership & Governance Audit", "status": "generated"})
    if data.get("history_evolution"):
        presentation_pdf_en.append({"type": "component", "label": "Strategic Evolution Analysis", "status": "generated"})

    presentation_pdf_de = []
    if data.get("firmenhistorie"):
        presentation_pdf_de.append({"type": "component", "label": "Firmenhistorie & Heritage", "status": "generated"})
    if data.get("l4_html_report_de"): # If we ever generate a German HTML specifically
         presentation_pdf_de.append({
            "type": "html_report", 
            "label": "Full Presentation HTML (DE)", 
            "status": "generated",
            "url": data.get("html_storage_url_de", "")
        })

    presentation_audio_en = []
    if data.get("presentation_audio_en"):
        presentation_audio_en.append({"type": "presentation_audio", "label": "Presentation Audio (EN)", "url": data["presentation_audio_en"]})

    presentation_audio_de = []
    if data.get("presentation_audio_de"):
        presentation_audio_de.append({"type": "presentation_audio", "label": "Presentation Audio (DE)", "url": data["presentation_audio_de"]})

    payload = {
        "ticker_eod": ticker_eod,
        "company_name": data.get("company_name"),
        "report_date": report_date,
        "skill_id": SKILL_ID,
        "report_type": DEFAULT_REPORT_TYPE,
        "trigger_reason": "On-demand Request",
        "presentation_pdf_en": presentation_pdf_en,
        "presentation_pdf_de": presentation_pdf_de,
        "presentation_audio_en": presentation_audio_en,
        "presentation_audio_de": presentation_audio_de,
        "quarterly_analysis_pdf_en": [],
        "quarterly_analysis_pdf_de": [],
        "quarterly_analysis_audio_en": [],
        "quarterly_analysis_audio_de": [],
        "created_by": "n8n-automation",
        "review_status": "published",
        "html_report_url": data.get("html_storage_url", ""),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    try:
        res = supabase_client.table("kasona_company_reports").upsert(payload).execute()
        if len(res.data) > 0:
            print(f"  [SUCCESS] Master Index updated for {ticker_eod} ({report_date}).")
            return True
        return False
    except Exception as exc:
        print(f"  [!] Master Index error: {exc}")
        return False


def save_raw_transcripts_to_staging(
    ticker_eod: str,
    videos: list[dict],
    supabase_client: Client
):
    """Save raw YouTube transcripts to youtube_ceo_transcripts for HITL validation."""
    print(f"\n[STAGING] Saving {len(videos)} transcripts for validation...")
    for v in videos:
        payload = {
            "ticker_eod": ticker_eod,
            "video_url": v.get("url"),
            "title": v.get("title"),
            "transcript": v.get("transcript"),
            "qa_status": "pending"
        }
        try:
            # Simple insert (avoiding duplicates by URL if needed, but here we just append)
            supabase_client.table("youtube_ceo_transcripts").insert(payload).execute()
            print(f"  [OK] Staged: {v.get('title')[:40]}...")
        except Exception as exc:
            print(f"  [!] Staging error for {v.get('url')}: {exc}")


def check_staging_approval(ticker_eod: str, supabase_client: Client) -> list[dict]:
    """Check if any transcripts for this ticker are 'approved'."""
    try:
        res = supabase_client.table("youtube_ceo_transcripts") \
            .select("*") \
            .eq("ticker_eod", ticker_eod) \
            .eq("qa_status", "approved") \
            .execute()
        return res.data
    except Exception as exc:
        print(f"  [!] Approval check error: {exc}")
        return []


# ═══════════════════════════════════════════════════════════════════════
# CLI entrypoint
# ═══════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Kasona New-Company-Presentation Pipeline (n8n workflow replica)"
    )
    parser.add_argument("--company",       help="Company name (e.g. 'Danaher')")
    parser.add_argument("--ticker-eod",    default=None,  help="EODHD ticker (e.g. 'DHR.US')")
    parser.add_argument("--supabase-sync", action="store_true", help="Sync results to Supabase (SSOT + Master Index)")
    staged_transcripts = None
    parser.add_argument("--output-dir",    default="output", help="Directory for JSON + HTML output")
    parser.add_argument("--mode",          choices=["full", "extract", "staged"], default="full", 
                        help="Execution mode: 'full' (all at once), 'extract' (YouTube only), 'staged' (Run from approved transcripts)")
    parser.add_argument("--fill-blanks",   type=int, default=0, help="Batch mode: process N pending records from the bottom of the table")
    parser.add_argument("--patch-pillars", action="store_true", help="Audit all records and fill missing Porter/Strategic pillars")
    args = parser.parse_args()

    config = {
        "apify_key":      os.environ.get("APIFY_API_KEY") or os.environ.get("APIFY_API_TOKEN", ""),
        "gemini_key":     os.environ.get("GOOGLE_GEMINI_API_KEY", ""),
        "openrouter_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "openai_key":     os.environ.get("OPENAI_API_KEY", ""),
        "supabase_url":   os.environ.get("SUPABASE_URL", ""),
        "supabase_key":   os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        "eodhd_key":      os.environ.get("EODHD_API_KEY", ""),
    }

    print("  Key status:")
    for k, v in config.items():
        print(f"    {k:20s}: {'LOADED' if v else 'MISSING'}")

    # Supabase setup
    supabase_client = None
    if args.supabase_sync or args.patch_pillars or args.mode in ["extract", "staged"]:
        if not config["supabase_url"] or not config["supabase_key"]:
            print("  [!] Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
            sys.exit(1)
        supabase_client = create_client(config["supabase_url"], config["supabase_key"])

    # ── MODE: Batch Fill Blanks ──────────────────────────────────────
    if args.fill_blanks > 0:
        if not args.supabase_sync:
            print("  [!] --fill-blanks requires --supabase-sync")
            sys.exit(1)
        
        print(f"\n[BATCH] Looking for up to {args.fill_blanks} pending records from the bottom...")
        try:
            # Look for records with status 'pending' OR status is NULL OR l4_report is NULL
            res = supabase_client.table("company_presentation") \
                .select("id, ticker_eod, company_name") \
                .or_("status.eq.pending,status.is.null,l4_report.is.null") \
                .order("id", desc=True) \
                .limit(args.fill_blanks) \
                .execute()
            
            pending_records = res.data
            if not pending_records:
                print("  [OK] No pending records found.")
                return
            
            print(f"  [OK] Found {len(pending_records)} pending record(s).")
            
            for rec in pending_records:
                curr_ticker = rec.get("ticker_eod")
                curr_company = rec.get("company_name")
                
                if not curr_ticker or not curr_company:
                    print(f"  [SKIP] Record ID {rec['id']} missing ticker or company name.")
                    continue
                
                print(f"\n{'-'*40}")
                print(f"  PROCESSING: {curr_company} ({curr_ticker})")
                print(f"{'-'*40}")
                
                try:
                    # Run pipeline
                    results = run_pipeline(curr_company, curr_ticker, config)
                    
                    # Sync
                    if args.supabase_sync:
                        # Upload HTML
                        html_path = os.path.join(args.output_dir, f"{curr_company.replace(' ', '_')}_l4_report.html")
                        if os.path.exists(html_path):
                            html_url = upload_to_supabase_storage(html_path, "company-presentations", curr_ticker, supabase_client)
                            results["html_storage_url"] = html_url
                        
                        sync_to_supabase(curr_ticker, results, supabase_client)
                        push_to_master_index(curr_ticker, results, supabase_client)
                except Exception as e:
                    print(f"  [!] Pipeline failed for {curr_company}: {e}")
            
            print("\n[BATCH] Completed all processing.")
            return
        except Exception as exc:
            print(f"  [!] Batch query error: {exc}")
            sys.exit(1)

    # ── MODE: Patch Missing Pillars ─────────────────────────────────
    if args.patch_pillars:
        print(f"\n[PATCH] Auditing all records for missing analytical pillars...")
        try:
            # Query for all tickers and check presence of the 11 columns
            res = supabase_client.table("company_presentation") \
                .select("id, ticker_eod, company_name, ai_agent_firmenhistorie, \"history-evolution\", \"leadership-governance\", \"risk-success-factors\", \"bull-case\", \"bear-case\", rivalry, \"supplier-power\", \"buyer-power\", \"threat-of-entry\", substitutes, growth_roadmap, l4_report, investment_thesis, strategic_vision, competitive_landscape, investment_thesis_de, strategic_vision_de, competitive_landscape_de, growth_roadmap_de, \"leadership-governance_de\", \"history-evolution_de\"") \
                .execute()
            
            all_records = res.data
            count = 0
            for rec in all_records:
                ticker = rec.get("ticker_eod")
                company = rec.get("company_name")
                
                # Identify missing or error pillars
                is_missing = lambda val: not val or "[AI_ERROR]" in str(val)
                
                # Porter's + Extra Pillars (11 columns)
                strategic_keys = [
                    "rivalry", "supplier-power", "buyer-power", "threat-of-entry", "substitutes",
                    "risk-success-factors", "bull-case", "bear-case", 
                    "investment_thesis", "strategic_vision", "competitive_landscape"
                ]
                # Map DB columns to AI JSON keys (hyphen)
                db_to_ai = {
                    "investment_thesis": "investment-thesis",
                    "strategic_vision": "strategic-vision",
                    "competitive_landscape": "competitive-landscape",
                    "growth_roadmap": "growth-roadmap"
                }
                
                needs_strategic = any(is_missing(rec.get(k)) for k in strategic_keys)
                needs_roadmap = is_missing(rec.get("growth_roadmap"))
                
                # Translations
                translation_keys = [f"{k}_de" for k in strategic_keys] + ["growth_roadmap_de", "leadership-governance_de", "history-evolution_de"]
                needs_translation = any(is_missing(rec.get(k)) for k in translation_keys)

                # Core Pillars
                needs_history = is_missing(rec.get("history-evolution")) or is_missing(rec.get("ai_agent_firmenhistorie"))
                needs_leadership = is_missing(rec.get("leadership-governance"))
                needs_report = is_missing(rec.get("l4_report"))
                
                if not (needs_strategic or needs_history or needs_leadership or needs_roadmap or needs_report or needs_translation):
                    continue
                
                print(f"\n[PATCHING] {company} ({ticker})")
                patch_payload = {}
                
                # 1. Strategic Pillars (English)
                if needs_strategic:
                    print(f"    [AI] Regenerating missing English strategic pillars...")
                    pillars = run_pillars_analysis(company, config["gemini_key"])
                    if pillars and "error" not in pillars:
                        for k in strategic_keys:
                            ai_key = db_to_ai.get(k, k)
                            if is_missing(rec.get(k)) and pillars.get(ai_key):
                                patch_payload[k] = pillars[ai_key]
                
                # 2. History Pillars
                if needs_history:
                    print(f"    [AI] Regenerating missing history/evolution...")
                    h_data = run_history_analysis(company, config["gemini_key"])
                    if is_missing(rec.get("history-evolution")) and h_data.get("evolution"):
                        patch_payload["history-evolution"] = h_data["evolution"]
                    if is_missing(rec.get("ai_agent_firmenhistorie")) and h_data.get("firmenhistorie"):
                        patch_payload["ai_agent_firmenhistorie"] = h_data["firmenhistorie"]
                
                # 3. Leadership Pillar
                if needs_leadership:
                    print(f"    [AI] Regenerating missing leadership audit...")
                    l_audit = run_leadership_audit(company, config)
                    if l_audit and not is_missing(l_audit):
                        patch_payload["leadership-governance"] = l_audit

                # 4. Roadmap (if still missing)
                if needs_roadmap:
                    print(f"    [AI] Regenerating missing growth roadmap...")
                    roadmap_prompt = f"Provide a 1-sentence growth roadmap for {company}. Focus on M&A, R&D, or geographical expansion."
                    model = genai.GenerativeModel(GEMINI_3_FLASH)
                    try:
                        r_res = model.generate_content(roadmap_prompt).text.strip()
                        if r_res and not is_missing(r_res):
                            patch_payload["growth_roadmap"] = r_res
                    except: pass

                # ── German Translation Sync ──────────────────────────
                if patch_payload or needs_translation:
                    print(f"    [TRANS] Syncing German translations for analytical blocks...")
                    # Build list of fields to translate (English sources)
                    to_translate = {}
                    # If we just patched EN, use those. Otherwise, use existing DB values.
                    for k in strategic_keys:
                        en_val = patch_payload.get(k) or rec.get(k)
                        if en_val and not is_missing(en_val): to_translate[k] = en_val
                    
                    en_roadmap = patch_payload.get("growth_roadmap") or rec.get("growth_roadmap")
                    if en_roadmap and not is_missing(en_roadmap): to_translate["growth_roadmap"] = en_roadmap
                    
                    en_leadership = patch_payload.get("leadership-governance") or rec.get("leadership-governance")
                    if en_leadership and not is_missing(en_leadership): to_translate["leadership-governance"] = en_leadership
                    
                    en_history = patch_payload.get("history-evolution") or rec.get("history-evolution")
                    if en_history and not is_missing(en_history): to_translate["history-evolution"] = en_history

                    if to_translate:
                        de_data = translate_analysis_to_german(to_translate, config["gemini_key"])
                        # Only patch missing or newly translated German fields
                        for de_k, de_v in de_data.items():
                            orig_k = de_k.replace("_de", "")
                            # Map back to DB key (preserve hyphens)
                            if is_missing(rec.get(de_k)) or patch_payload.get(orig_k):
                                patch_payload[de_k] = de_v

                # 5. Full Report Regeneration
                if patch_payload or needs_report:
                    print(f"    [REPORT] Regenerating full report to incorporate patches...")
                    # Fetch EODHD if needed (for metadata)
                    eodhd_data = fetch_eodhd_fundamentals(ticker, config["eodhd_key"])
                    
                    # Pull existing approved transcripts to avoid data loss in the report
                    staged_transcripts = check_staging_approval(ticker, supabase_client)
                    # Convert DB format to generator format (video_url -> url)
                    for st in staged_transcripts:
                        st["url"] = st.get("video_url", "")
                        st["channel"] = "(Staged/Verified)"
                        st["publishedAt"] = "2024-01-01" # Default if missing
                    
                    ceo_vids = [t for t in staged_transcripts if "ceo" in t.get("title", "").lower() or "interview" in t.get("title", "").lower()]
                    pod_vids = [t for t in staged_transcripts if t not in ceo_vids]

                    # Generate HTML
                    html_report = generate_l4_html_report(
                        company_name = company,
                        leadership_analysis = patch_payload.get("leadership-governance", rec.get("leadership-governance")),
                        history_analysis = patch_payload.get("history-evolution", rec.get("history-evolution")),
                        ceo_interviews = ceo_vids,
                        podcasts = pod_vids,
                        linkedin_profiles = [], # LinkedIn profiles aren't currently staged in a separate table
                        eodhd_data = eodhd_data
                    )
                    
                    # Sync HTML to Storage
                    temp_html = f"temp_{ticker}_report.html"
                    with open(temp_html, "w", encoding="utf-8") as f:
                        f.write(html_report)
                    
                    if args.supabase_sync:
                        html_url = upload_to_supabase_storage(temp_html, "company-presentations", ticker, supabase_client)
                        patch_payload["l4_report"] = html_url
                        patch_payload["status"] = "uploaded"
                        
                        # Also update Master Index metadata
                        results_for_index = {
                            "company_name": company,
                            "l4_html_report": html_report,
                            "html_storage_url": html_url
                        }
                        push_to_master_index(ticker, results_for_index, supabase_client)
                    
                    if os.path.exists(temp_html):
                        os.remove(temp_html)
                
                if patch_payload:
                    if patch_pillars_to_supabase(ticker, patch_payload, supabase_client):
                        count += 1
                else:
                    print(f"    [SKIP] No patch data generated for {ticker}.")
            
            print(f"\n[PATCH] Completed remediation. {count} records updated.")
            return
        except Exception as exc:
            print(f"  [!] Patching error: {exc}")
            sys.exit(1)

    # ── Single Company Run ─────────────────────────────────────────
    if not args.company:
        print("  [!] --company required for non-batch mode")
        sys.exit(1)

    # ── MODE: Extraction Only ──────────────────────────────────────
    if args.mode == "extract":
        if not args.ticker_eod:
            print("  [!] --mode extract requires --ticker-eod")
            sys.exit(1)
        print(f"\n[MODE] Running RAW EXTRACTION for {args.company}...")
        ceo = scrape_youtube_ceo_interview(args.company, config["apify_key"])
        pod = scrape_youtube_acquired_podcast(args.company, config["apify_key"])
        save_raw_transcripts_to_staging(args.ticker_eod, ceo + pod, supabase_client)
        print("\n[DONE] Extraction complete. Please approve transcripts in DB to proceed with generation.")
        return

    # ── MODE: Staged Full (Checking approvals) ────────────────────
    if args.mode == "staged":
        print(f"\n[MODE] Checking for APPROVED transcripts for {args.ticker_eod}...")
        approvals = check_staging_approval(args.ticker_eod, supabase_client)
        if not approvals:
            print("  [!] No approved transcripts found. Run with --mode extract first or approve them in DB.")
            return
        print(f"  [OK] Found {len(approvals)} approved transcripts. Proceeding to report generation...")
        staged_transcripts = approvals

    # ── Full / Final Pipeline Run ──────────────────────────────────
    results = run_pipeline(args.company, args.ticker_eod, config, pre_loaded_transcripts=staged_transcripts)

    # Save outputs
    # ... (rest of local saving logic)
    os.makedirs(args.output_dir, exist_ok=True)
    slug = args.company.replace(" ", "_").replace("&", "and")

    json_path = os.path.join(args.output_dir, f"{slug}_new_presentation.json")
    with open(json_path, "w", encoding="utf-8") as f:
        save_data = {k: v for k, v in results.items() if k != "l4_html_report"}
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] JSON → {json_path}")

    html_path = os.path.join(args.output_dir, f"{slug}_l4_report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(results.get("l4_html_report", ""))
    print(f"[SAVED] HTML → {html_path}")

    # Supabase sync
    if args.supabase_sync:
        if not args.ticker_eod:
            print("  [!] --supabase-sync requires --ticker-eod")
            sys.exit(1)
            
        # Upload HTML
        if os.path.exists(html_path):
            html_url = upload_to_supabase_storage(html_path, "company-presentations", args.ticker_eod, supabase_client)
            results["html_storage_url"] = html_url

        sync_to_supabase(args.ticker_eod, results, supabase_client)
        push_to_master_index(args.ticker_eod, results, supabase_client)


if __name__ == "__main__":
    main()
