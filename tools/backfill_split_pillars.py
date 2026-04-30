"""
backfill_split_pillars.py — Retroactive Column Splitter
========================================================
The old pipeline wrote History + Core Assets + Porter's + Risk/Success factors
ALL into the `history-evolution` column. This script:

1. Reads all rows where `core-assets-capabilities` IS NULL
2. Uses Gemini to generate FRESH dedicated content for:
   - core-assets-capabilities (EN)
   - core-assets-capabilities_de (DE)
   - success-failure-factors (EN)
   - success-failure-factors_de (DE)
3. Optionally re-generates a CLEAN history-evolution that only contains history

Usage:
  # Backfill ALL companies with missing pillars:
  python tools/backfill_split_pillars.py

  # Backfill a specific ticker:
  python tools/backfill_split_pillars.py --ticker BERG-B.ST

  # Dry run (preview what would be updated):
  python tools/backfill_split_pillars.py --dry-run

  # Also rewrite history-evolution to remove mixed content:
  python tools/backfill_split_pillars.py --rewrite-history
"""

import os
import sys
import time
import json
import argparse
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv

# ── stdout UTF-8 fix ──
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Load .env ──
_tools_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_tools_dir)
_env_path = os.path.join(_root_dir, ".env")
load_dotenv(_env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.environ.get("GOOGLE_GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    print(f"[FATAL] Missing env vars. URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_KEY)}, GEMINI={bool(GEMINI_API_KEY)}")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# ── Gemini Models ──
GEMINI_MODEL = "models/gemini-2.0-flash"

# ── Prompts ──
CORE_ASSETS_EN_PROMPT = """You are a Senior Equity Research Analyst. Analyze the core competencies and strategic assets of {company}.

Structure (ENGLISH):
1. Intellectual Property & Patents: Key patents, trade secrets, proprietary technology.
2. Physical Infrastructure: Manufacturing, distribution, logistics networks.
3. Data & Digital Assets: Proprietary data, platforms, digital ecosystems.
4. Operational Strengths: Process excellence, supply chain, cost advantages.
5. Human Capital: Key talent pools, R&D capabilities, organizational culture.

Tone: Institutional, analytical. No marketing language. Start directly without introduction."""

CORE_ASSETS_DE_PROMPT = """Du bist ein Senior Corporate Analyst. Erstelle eine detaillierte deutschsprachige Analyse der Kernkompetenzen und strategischen Assets von {company}.

Struktur (DEUTSCH):
1. Geistiges Eigentum & Patente: Schlüsselpatente, proprietäre Technologie.
2. Physische Infrastruktur: Fertigung, Distribution, Logistiknetzwerke.
3. Daten & Digitale Assets: Proprietäre Daten, Plattformen, digitale Ökosysteme.
4. Operative Stärken: Prozessexzellenz, Lieferkette, Kostenvorteile.
5. Humankapital: Schlüsseltalente, F&E-Kapazitäten, Organisationskultur.

Schreibe ausschließlich auf DEUTSCH. Keine Einleitungsfloskeln."""

SUCCESS_FAILURE_EN_PROMPT = """You are a Senior Investment Analyst. Analyze the critical success and failure factors of {company} as investment KPIs.

Structure (ENGLISH):
1. Critical Success Drivers: What must go right for the investment thesis to work?
2. Key Risk Variables: What could derail the business model?
3. Investment KPIs to Watch: Specific metrics investors should monitor.
4. Historical Pattern Recognition: Past instances where similar factors played out.

Tone: Institutional, data-driven. Start directly without introduction."""

SUCCESS_FAILURE_DE_PROMPT = """Du bist ein Senior Investment Analyst. Analysiere die kritischen Erfolgs- und Misserfolgsfaktoren von {company} als Investitions-KPIs.

Struktur (DEUTSCH):
1. Kritische Erfolgstreiber: Was muss richtig laufen, damit die Investmentthese funktioniert?
2. Zentrale Risikovariablen: Was könnte das Geschäftsmodell gefährden?
3. Investitions-KPIs: Spezifische Kennzahlen, die Investoren überwachen sollten.
4. Historische Mustererkennung: Vergangene Fälle, in denen ähnliche Faktoren relevant waren.

Schreibe ausschließlich auf DEUTSCH. Keine Einleitungsfloskeln."""

CLEAN_HISTORY_EN_PROMPT = """You are a Global Equity Research Director. Rewrite the following company history to contain ONLY the history and strategic evolution — remove any sections about Core Assets, Porter's Five Forces, Risk/Success Factors, or Investment KPIs.

Structure (ENGLISH):
1. Founding & Origin Story: The genesis, founding vision, and early years.
2. Strategic Pivots & M&A: Key transformational moments, acquisitions, divestitures.
3. Growth Phases: Major expansion periods, market entries, geographic diversification.
4. Modern Era: Current strategic positioning and evolution trajectory.

Original content to clean:
{content}

Output ONLY the cleaned history. Start directly without introduction."""

CLEAN_HISTORY_DE_PROMPT = """Du bist ein Senior Corporate Historian. Bereinige die folgende Firmenhistorie, sodass NUR die Geschichte und strategische Evolution enthalten ist — entferne alle Abschnitte über Kernkompetenzen, Porter's Five Forces, Risiko-/Erfolgsfaktoren oder Investitions-KPIs.

Struktur (DEUTSCH):
1. Gründungsjahre & Vision: Die Anfänge und der Geist der Gründer.
2. Formative Phasen: Krisen, Durchbrüche und kulturelle Prägung.
3. Die moderne Ära: Transformation zum heutigen Unternehmen.
4. Heritage-Zusammenfassung: Was macht den "Kern" des Unternehmens heute aus?

Originalinhalt zum Bereinigen:
{content}

Gib NUR die bereinigte Firmenhistorie aus. Keine Einleitungsfloskeln."""


def generate_with_retry(prompt: str, max_retries: int = 10) -> str:
    """Generate content with retry logic for rate limits."""
    model = genai.GenerativeModel(model_name=GEMINI_MODEL)
    wait = 30
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            err = str(exc)
            if "429" in err or "quota" in err.lower():
                print(f"      [429] Rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
                wait = min(wait + 30, 180)
                continue
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return f"[AI_ERROR] {exc}"
    return "[AI_ERROR] Failed after all retries."


def backfill_ticker(row: dict, rewrite_history: bool = False, dry_run: bool = False) -> dict:
    """Generate and backfill missing pillars for one company."""
    ticker = row["ticker_eod"]
    company = row.get("company_name") or ticker
    
    print(f"\n{'='*60}")
    print(f"  [{ticker}] {company}")
    print(f"{'='*60}")
    
    update_payload = {}
    
    # Check what's missing
    has_core_assets = row.get("core-assets-capabilities") and len(str(row["core-assets-capabilities"]).strip()) > 20
    has_core_assets_de = row.get("core-assets-capabilities_de") and len(str(row["core-assets-capabilities_de"]).strip()) > 20
    has_success = row.get("success-failure-factors") and len(str(row["success-failure-factors"]).strip()) > 20
    has_success_de = row.get("success-failure-factors_de") and len(str(row["success-failure-factors_de"]).strip()) > 20
    
    # Generate Core Assets EN
    if not has_core_assets:
        print(f"  [GEN] Core Assets & Capabilities (EN)...")
        if not dry_run:
            result = generate_with_retry(CORE_ASSETS_EN_PROMPT.format(company=company))
            if not result.startswith("[AI_ERROR]"):
                update_payload["core-assets-capabilities"] = result
                print(f"  [OK] Core Assets EN: {len(result)} chars")
            else:
                print(f"  [FAIL] {result}")
        else:
            print(f"  [DRY] Would generate Core Assets EN")
    else:
        print(f"  [SKIP] Core Assets EN already exists ({len(str(row['core-assets-capabilities']))} chars)")
    
    # Generate Core Assets DE
    if not has_core_assets_de:
        print(f"  [GEN] Core Assets & Capabilities (DE)...")
        if not dry_run:
            result = generate_with_retry(CORE_ASSETS_DE_PROMPT.format(company=company))
            if not result.startswith("[AI_ERROR]"):
                update_payload["core-assets-capabilities_de"] = result
                print(f"  [OK] Core Assets DE: {len(result)} chars")
            else:
                print(f"  [FAIL] {result}")
        else:
            print(f"  [DRY] Would generate Core Assets DE")
    else:
        print(f"  [SKIP] Core Assets DE already exists")
    
    # Generate Success/Failure EN
    if not has_success:
        print(f"  [GEN] Success/Failure Factors (EN)...")
        if not dry_run:
            result = generate_with_retry(SUCCESS_FAILURE_EN_PROMPT.format(company=company))
            if not result.startswith("[AI_ERROR]"):
                update_payload["success-failure-factors"] = result
                print(f"  [OK] Success/Failure EN: {len(result)} chars")
            else:
                print(f"  [FAIL] {result}")
        else:
            print(f"  [DRY] Would generate Success/Failure EN")
    else:
        print(f"  [SKIP] Success/Failure EN already exists ({len(str(row['success-failure-factors']))} chars)")
    
    # Generate Success/Failure DE
    if not has_success_de:
        print(f"  [GEN] Success/Failure Factors (DE)...")
        if not dry_run:
            result = generate_with_retry(SUCCESS_FAILURE_DE_PROMPT.format(company=company))
            if not result.startswith("[AI_ERROR]"):
                update_payload["success-failure-factors_de"] = result
                print(f"  [OK] Success/Failure DE: {len(result)} chars")
            else:
                print(f"  [FAIL] {result}")
        else:
            print(f"  [DRY] Would generate Success/Failure DE")
    else:
        print(f"  [SKIP] Success/Failure DE already exists")
    
    # Optionally rewrite history to remove mixed content
    if rewrite_history:
        history_en = row.get("history-evolution") or ""
        history_de = row.get("history-evolution_de") or ""
        
        if history_en and len(history_en) > 200:
            # Check if history contains mixed content (heuristic: look for Porter's / Risk / Core Assets headings)
            mixed_markers = ["porter", "five forces", "core assets", "kernkompetenzen", "risk", "risiko", "erfolgsfaktoren", "success", "failure"]
            is_mixed = any(m in history_en.lower() for m in mixed_markers)
            
            if is_mixed:
                print(f"  [REWRITE] History EN contains mixed content — cleaning...")
                if not dry_run:
                    clean = generate_with_retry(CLEAN_HISTORY_EN_PROMPT.format(content=history_en[:6000]))
                    if not clean.startswith("[AI_ERROR]"):
                        update_payload["history-evolution"] = clean
                        print(f"  [OK] Clean History EN: {len(clean)} chars (was {len(history_en)})")
                else:
                    print(f"  [DRY] Would clean History EN ({len(history_en)} chars)")
            else:
                print(f"  [SKIP] History EN looks clean already")
        
        if history_de and len(history_de) > 200:
            mixed_markers_de = ["porter", "five forces", "kernkompetenzen", "risiko", "erfolgsfaktoren", "infrastruktur", "wettbewerb"]
            is_mixed_de = any(m in history_de.lower() for m in mixed_markers_de)
            
            if is_mixed_de:
                print(f"  [REWRITE] History DE contains mixed content — cleaning...")
                if not dry_run:
                    clean_de = generate_with_retry(CLEAN_HISTORY_DE_PROMPT.format(content=history_de[:6000]))
                    if not clean_de.startswith("[AI_ERROR]"):
                        update_payload["history-evolution_de"] = clean_de
                        print(f"  [OK] Clean History DE: {len(clean_de)} chars (was {len(history_de)})")
                else:
                    print(f"  [DRY] Would clean History DE ({len(history_de)} chars)")
            else:
                print(f"  [SKIP] History DE looks clean already")
    
    return update_payload


def main():
    parser = argparse.ArgumentParser(description="Backfill core-assets and success-failure columns")
    parser.add_argument("--ticker", type=str, help="Process only this ticker (e.g. BERG-B.ST)")
    parser.add_argument("--dry-run", action="store_true", help="Preview what would be updated without making changes")
    parser.add_argument("--rewrite-history", action="store_true", help="Also clean mixed content out of history-evolution")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tickers to process (0 = all)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Kasona Pillar Backfill — Retroactive Column Splitter")
    print("=" * 60)
    if args.dry_run:
        print("  MODE: DRY RUN (no changes will be made)")
    if args.rewrite_history:
        print("  MODE: Will also rewrite mixed history-evolution content")
    print()
    
    # Fetch all rows
    select_cols = "ticker_eod,company_name,history-evolution,history-evolution_de,core-assets-capabilities,core-assets-capabilities_de,success-failure-factors,success-failure-factors_de"
    
    query = supabase.table("company_presentation").select(select_cols)
    
    if args.ticker:
        query = query.eq("ticker_eod", args.ticker)
    
    res = query.execute()
    rows = res.data if res.data else []
    
    if not rows:
        print("[INFO] No rows found.")
        return
    
    # Filter to rows that need work
    targets = []
    for row in rows:
        needs_core = not (row.get("core-assets-capabilities") and len(str(row["core-assets-capabilities"]).strip()) > 20)
        needs_success = not (row.get("success-failure-factors") and len(str(row["success-failure-factors"]).strip()) > 20)
        
        if needs_core or needs_success:
            targets.append(row)
        elif args.rewrite_history:
            # Even if pillars exist, check if history needs cleaning
            targets.append(row)
    
    print(f"[INFO] Found {len(targets)} tickers requiring backfill (out of {len(rows)} total).\n")
    
    if args.limit > 0:
        targets = targets[:args.limit]
        print(f"[INFO] Limited to {args.limit} tickers.\n")
    
    stats = {"updated": 0, "skipped": 0, "failed": 0}
    
    for i, row in enumerate(targets, 1):
        ticker = row["ticker_eod"]
        print(f"\n[{i}/{len(targets)}] Processing {ticker}...")
        
        try:
            payload = backfill_ticker(row, rewrite_history=args.rewrite_history, dry_run=args.dry_run)
            
            if payload and not args.dry_run:
                print(f"  [SAVE] Writing {len(payload)} columns to Supabase...")
                try:
                    res = supabase.table("company_presentation").update(payload).eq("ticker_eod", ticker).execute()
                    if hasattr(res, 'data') and res.data:
                        print(f"  [OK] ✅ {ticker} updated successfully.")
                        stats["updated"] += 1
                    else:
                        print(f"  [WARN] Supabase returned no data for {ticker}.")
                        stats["failed"] += 1
                except Exception as e:
                    print(f"  [ERR] Supabase update failed: {e}")
                    stats["failed"] += 1
            elif payload and args.dry_run:
                print(f"  [DRY] Would update columns: {list(payload.keys())}")
                stats["updated"] += 1
            else:
                print(f"  [SKIP] Nothing to update for {ticker}.")
                stats["skipped"] += 1
            
            # Cooldown between tickers
            if i < len(targets):
                cooldown = 15
                print(f"  [COOL] Waiting {cooldown}s...")
                time.sleep(cooldown)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  [FATAL] Error processing {ticker}: {e}")
            stats["failed"] += 1
            continue
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  BACKFILL COMPLETE")
    print(f"  Updated: {stats['updated']} | Skipped: {stats['skipped']} | Failed: {stats['failed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
