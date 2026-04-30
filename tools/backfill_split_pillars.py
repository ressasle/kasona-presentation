"""
backfill_split_pillars.py — Retroactive Column Splitter
========================================================
The old pipeline wrote History + Core Assets + Porter's + Risk/Success factors
ALL into the `history-evolution` column. This script:

1. Reads all rows where `core-assets-capabilities` IS NULL
2. Uses OpenRouter (Gemini Flash) to generate FRESH dedicated content for:
   - core-assets-capabilities (EN)
   - core-assets-capabilities_de (DE)
   - success-failure-factors (EN)
   - success-failure-factors_de (DE)
3. Optionally re-generates a CLEAN history-evolution that only contains history

Usage:
  # Backfill ALL companies with missing pillars:
  python3 tools/backfill_split_pillars.py

  # Backfill a specific ticker:
  python3 tools/backfill_split_pillars.py --ticker BERG-B.ST

  # Dry run (preview what would be updated):
  python3 tools/backfill_split_pillars.py --dry-run

  # Also rewrite history-evolution to remove mixed content:
  python3 tools/backfill_split_pillars.py --rewrite-history
"""

import os
import sys
import time
import json
import argparse
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

# ── stdout UTF-8 fix ──
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Load .env (try multiple locations) ──
_tools_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_tools_dir)

_env_candidates = [
    os.path.join(_root_dir, ".env"),
    os.path.join(_root_dir, "..", "1.3_podcast-production", ".env"),
    os.path.join(_root_dir, "..", "..", "1.3_podcast-production", ".env"),
]
for _env in _env_candidates:
    if os.path.exists(_env):
        print(f"  [ENV] Loading: {_env}")
        load_dotenv(_env)

_research_env = os.path.join(_root_dir, "..", "research-meeting-skill", "config", ".env")
if os.path.exists(_research_env):
    load_dotenv(_research_env, override=False)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY]):
    print(f"[FATAL] Missing env vars. URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_KEY)}, OPENROUTER={bool(OPENROUTER_API_KEY)}")
    sys.exit(1)

print(f"  [OK] Supabase: {SUPABASE_URL[:35]}...")
print(f"  [OK] OpenRouter key loaded.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── OpenRouter Models (reliable first) ──
OPENROUTER_MODELS = [
    "openai/gpt-4.1-mini",
    "anthropic/claude-3.5-haiku",
]

# ── Prompts ──
CORE_ASSETS_EN = """You are a Senior Equity Research Analyst. Analyze the core competencies and strategic assets of {company}.

Structure (ENGLISH):
1. Intellectual Property & Patents: Key patents, trade secrets, proprietary technology.
2. Physical Infrastructure: Manufacturing, distribution, logistics networks.
3. Data & Digital Assets: Proprietary data, platforms, digital ecosystems.
4. Operational Strengths: Process excellence, supply chain, cost advantages.
5. Human Capital: Key talent pools, R&D capabilities, organizational culture.

Tone: Institutional, analytical. No marketing language. Start directly without introduction."""

CORE_ASSETS_DE = """Du bist ein Senior Corporate Analyst. Erstelle eine detaillierte deutschsprachige Analyse der Kernkompetenzen und strategischen Assets von {company}.

Struktur (DEUTSCH):
1. Geistiges Eigentum & Patente: Schluesselpatente, proprietaere Technologie.
2. Physische Infrastruktur: Fertigung, Distribution, Logistiknetzwerke.
3. Daten & Digitale Assets: Proprietaere Daten, Plattformen, digitale Oekosysteme.
4. Operative Staerken: Prozessexzellenz, Lieferkette, Kostenvorteile.
5. Humankapital: Schluesseltalente, F&E-Kapazitaeten, Organisationskultur.

Schreibe ausschliesslich auf DEUTSCH. Keine Einleitungsfloskeln."""

SUCCESS_FAILURE_EN = """You are a Senior Investment Analyst. Analyze the critical success and failure factors of {company} as investment KPIs.

Structure (ENGLISH):
1. Critical Success Drivers: What must go right for the investment thesis to work?
2. Key Risk Variables: What could derail the business model?
3. Investment KPIs to Watch: Specific metrics investors should monitor.
4. Historical Pattern Recognition: Past instances where similar factors played out.

Tone: Institutional, data-driven. Start directly without introduction."""

SUCCESS_FAILURE_DE = """Du bist ein Senior Investment Analyst. Analysiere die kritischen Erfolgs- und Misserfolgsfaktoren von {company} als Investitions-KPIs.

Struktur (DEUTSCH):
1. Kritische Erfolgstreiber: Was muss richtig laufen, damit die Investmentthese funktioniert?
2. Zentrale Risikovariablen: Was koennte das Geschaeftsmodell gefaehrden?
3. Investitions-KPIs: Spezifische Kennzahlen, die Investoren ueberwachen sollten.
4. Historische Mustererkennung: Vergangene Faelle, in denen aehnliche Faktoren relevant waren.

Schreibe ausschliesslich auf DEUTSCH. Keine Einleitungsfloskeln."""

CLEAN_HISTORY_EN = """You are a Global Equity Research Director. Rewrite the following company history to contain ONLY the history and strategic evolution. Remove any sections about Core Assets, Porter's Five Forces, Risk/Success Factors, or Investment KPIs.

Structure:
1. Founding & Origin Story
2. Strategic Pivots & M&A
3. Growth Phases
4. Modern Era

Original content to clean:
{content}

Output ONLY the cleaned history. Start directly."""

CLEAN_HISTORY_DE = """Du bist ein Senior Corporate Historian. Bereinige die folgende Firmenhistorie, sodass NUR die Geschichte und strategische Evolution enthalten ist. Entferne alle Abschnitte ueber Kernkompetenzen, Porter's Five Forces, Risiko-/Erfolgsfaktoren oder Investitions-KPIs.

Originalinhalt zum Bereinigen:
{content}

Gib NUR die bereinigte Firmenhistorie aus. Keine Einleitungsfloskeln."""


def generate(prompt, max_retries=3):
    """Generate content via OpenRouter with model fallback."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kasona.ai",
        "X-Title": "Kasona Pillar Backfill"
    }
    for model in OPENROUTER_MODELS:
        wait = 10
        for attempt in range(max_retries):
            try:
                r = requests.post(url, headers=headers, json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                }, timeout=120)
                if r.status_code == 429:
                    print(f"      [429] {model} — waiting {wait}s ({attempt+1}/{max_retries})")
                    time.sleep(wait)
                    wait = min(wait + 15, 60)
                    continue
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                if "404" in str(e):
                    break
                print(f"      [ERR] {model}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    break
        print(f"      [FALLBACK] next model...")
    return "[AI_ERROR] All models exhausted."


def backfill_ticker(row, rewrite_history=False, dry_run=False):
    ticker = row["ticker_eod"]
    company = row.get("company_name") or ticker
    print(f"\n{'='*60}\n  [{ticker}] {company}\n{'='*60}")

    payload = {}
    checks = {
        "core-assets-capabilities": (CORE_ASSETS_EN, "Core Assets EN"),
        "core-assets-capabilities_de": (CORE_ASSETS_DE, "Core Assets DE"),
        "success-failure-factors": (SUCCESS_FAILURE_EN, "Success/Failure EN"),
        "success-failure-factors_de": (SUCCESS_FAILURE_DE, "Success/Failure DE"),
    }

    for col, (prompt_tpl, label) in checks.items():
        existing = row.get(col)
        if existing and len(str(existing).strip()) > 20:
            print(f"  [SKIP] {label} already exists ({len(str(existing))} chars)")
            continue
        print(f"  [GEN] {label}...")
        if dry_run:
            print(f"  [DRY] Would generate {label}")
            continue
        result = generate(prompt_tpl.format(company=company))
        if not result.startswith("[AI_ERROR]"):
            payload[col] = result
            print(f"  [OK] {label}: {len(result)} chars")
        else:
            print(f"  [FAIL] {result}")

    if rewrite_history:
        for col, prompt_tpl, lang_label in [
            ("history-evolution", CLEAN_HISTORY_EN, "History EN"),
            ("history-evolution_de", CLEAN_HISTORY_DE, "History DE"),
        ]:
            content = row.get(col) or ""
            if len(content) < 200:
                continue
            markers = ["porter", "five forces", "core assets", "kernkompetenzen", "risiko", "erfolgsfaktoren", "success factors"]
            if not any(m in content.lower() for m in markers):
                print(f"  [SKIP] {lang_label} looks clean")
                continue
            print(f"  [REWRITE] {lang_label} — mixed content detected")
            if dry_run:
                print(f"  [DRY] Would clean {lang_label}")
                continue
            clean = generate(prompt_tpl.format(content=content[:6000]))
            if not clean.startswith("[AI_ERROR]"):
                payload[col] = clean
                print(f"  [OK] {lang_label}: {len(clean)} chars (was {len(content)})")

    return payload


def main():
    parser = argparse.ArgumentParser(description="Backfill core-assets and success-failure columns")
    parser.add_argument("--ticker", type=str, help="Process only this ticker")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--rewrite-history", action="store_true", help="Clean mixed content from history-evolution")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tickers (0 = all)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Kasona Pillar Backfill (OpenRouter)")
    print("=" * 60)
    if args.dry_run:
        print("  MODE: DRY RUN")
    if args.rewrite_history:
        print("  MODE: REWRITE HISTORY")
    print()

    select_cols = "ticker_eod,company_name,history-evolution,history-evolution_de,core-assets-capabilities,core-assets-capabilities_de,success-failure-factors,success-failure-factors_de"
    query = supabase.table("company_presentation").select(select_cols)
    if args.ticker:
        query = query.eq("ticker_eod", args.ticker)

    rows = (query.execute().data or [])
    if not rows:
        print("[INFO] No rows found.")
        return

    targets = []
    for row in rows:
        needs_core = not (row.get("core-assets-capabilities") and len(str(row["core-assets-capabilities"]).strip()) > 20)
        needs_success = not (row.get("success-failure-factors") and len(str(row["success-failure-factors"]).strip()) > 20)
        if needs_core or needs_success or args.rewrite_history:
            targets.append(row)

    print(f"[INFO] {len(targets)} tickers to process (of {len(rows)} total).\n")
    if args.limit > 0:
        targets = targets[:args.limit]

    stats = {"updated": 0, "skipped": 0, "failed": 0}

    for i, row in enumerate(targets, 1):
        ticker = row["ticker_eod"]
        print(f"\n[{i}/{len(targets)}] {ticker}")
        try:
            p = backfill_ticker(row, rewrite_history=args.rewrite_history, dry_run=args.dry_run)
            if p and not args.dry_run:
                print(f"  [SAVE] Writing {len(p)} columns...")
                try:
                    res = supabase.table("company_presentation").update(p).eq("ticker_eod", ticker).execute()
                    if res.data:
                        print(f"  [OK] {ticker} updated.")
                        stats["updated"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    print(f"  [ERR] {e}")
                    stats["failed"] += 1
            elif p and args.dry_run:
                print(f"  [DRY] Would update: {list(p.keys())}")
                stats["updated"] += 1
            else:
                stats["skipped"] += 1
            if i < len(targets):
                time.sleep(5)
        except Exception as e:
            import traceback
            traceback.print_exc()
            stats["failed"] += 1

    print(f"\n{'='*60}")
    print(f"  DONE — Updated: {stats['updated']} | Skipped: {stats['skipped']} | Failed: {stats['failed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
