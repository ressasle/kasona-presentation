#!/usr/bin/env python3
"""
generate_presentation_audio.py — Institutional Bilingual Briefing Engine (V4)

Features:
- Bilingual Support (EN, DE)
- Institutional Header/Intro/Pillars/Outro structure.
- High-fidelity narration with section parsing.
- Optimized for professional investment briefings.

Usage:
    python3 generate_presentation_audio.py --script presentation.md --output briefing.mp3 --lang en
"""
import asyncio
import argparse
import os
import re
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("edge-tts not installed. Run: pip install edge-tts")
    sys.exit(1)

# ── Voice Configuration ───────────────────────────────────────────────────────
VOICES = {
    "en": "en-US-ChristopherNeural",
    "de": "de-DE-ConradNeural",  # High-quality German male voice
}

# ── Institutional Templates ────────────────────────────────────────────────────
TEMPLATES: dict[str, dict[str, str | dict[str, str]]] = {
    "en": {
        "headlines_start": "This company presentation and strategic review of {company_name} shows the long-term thesis and core pillars of the business. The essential points first:",
        "intro_greeting": "Hello Kasona Investor. Welcome to today's strategic update. We have deep-dive developments across the 4 pillars that merit your attention.",
        "pillar_announcement": "Section {num}. {title}.",
        "outro": "That was a Kasona Production. Check out our full offering on Kasona.ai. We filter the relevant developments using our process and artificial intelligence. This does not constitute buy or sell recommendations. Until next time!",
        "transitions": {
            "1": "History and Evolution",
            "2": "Porter's Five Forces Analysis",
            "3": "Leadership and Governance Audit",
            "4": "Risk and Success Factors",
        }
    },
    "de": {
        "headlines_start": "Diese Unternehmenspräsentation und strategische Analyse von {company_name} zeigt die langfristige Thesis und die Kernpfeiler des Unternehmens. Das Wichtigste vorab:",
        "intro_greeting": "Hallo Kasona-Investor. Willkommen zum heutigen strategischen Update. Wir haben tiefgreifende Entwicklungen in den 4 Säulen, die Ihre Aufmerksamkeit verdienen.",
        "pillar_announcement": "Abschnitt {num}. {title}.",
        "outro": "Das war eine Kasona-Produktion. Besuchen Sie unser vollständiges Angebot auf Kasona.ai. Wir filtern die relevanten Marktimpulse durch unseren KI-gestützten Analyse-Prozess präzise für Sie heraus. Dies stellt keine Kauf- oder Verkaufsempfehlungen dar. Bis zum nächsten Mal!",
        "transitions": {
            "1": "Historie und Evolution",
            "2": "Porter's Five Forces Analyse",
            "3": "Leadership und Governance Audit",
            "4": "Risiko- und Erfolgsfaktoren",
        }
    }
}

SKIP_SUBSECTIONS = {"Financial Highlights", "Financial Highlight", "Finanzielle Highlights"}

# ── Text Cleaning ─────────────────────────────────────────────────────────────
def clean_for_speech(text: str) -> str:
    """Strip all markdown syntax leaving clean, natural language."""
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)           # images
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # links → anchor text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)          # bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)              # italic
    text = re.sub(r'`(.+?)`', r'\1', text)                # code
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.M)    # headings
    text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.M) # bullets
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.M)    # numbered list
    text = text.replace('&amp;', 'and').replace('&', 'and')
    text = text.replace('%', ' percent' if 'en' else ' Prozent')
    return text.strip()

# ── Narration Builder ─────────────────────────────────────────────────────────
def build_narration(script_path: str, lang: str = "en") -> str:
    """Assemble a high-quality institutional podcast script."""
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    tpl = TEMPLATES.get(lang, TEMPLATES["en"])
    stem = Path(script_path).stem
    company_name = stem.replace("_presentation", "").replace("_de", "").replace("_", " ").title()

    # 1. Section Parsing
    lines = [L.strip() for L in content.split("\n") if L.strip() and L.strip() != "---"]
    
    # Extract Headlines (first 3 bullet points of section 1)
    headlines = []
    found_sec1 = False
    for line in lines:
        if line.startswith("## 1."): found_sec1 = True
        if found_sec1 and line.startswith("*"):
            headlines.append(clean_for_speech(line))
            if len(headlines) >= 3: break
    
    headline_text = " ".join(headlines)

    # 2. Intro Assembly
    full_script: list[str] = [
        str(tpl.get("headlines_start", "")).format(company_name=company_name), 
        headline_text,
        str(tpl.get("intro_greeting", "")).replace("Institutional Portfolio", f"{company_name} Strategic Update")
    ]

    # 3. Deep Dive
    current_section_num: str | None = None
    section_body: list[str] = []
    in_table: bool = False

    def flush():
        if not section_body: return
        trans = tpl.get("transitions", {})
        title = trans.get(current_section_num, "") if isinstance(trans, dict) else ""
        announcement_tpl = str(tpl.get("pillar_announcement", "Section {num}. {title}."))
        announcement = announcement_tpl.format(num=current_section_num, title=title)
        body_text = " ".join(section_body)
        full_script.append(f"\n{announcement}\n{body_text}")

    for line in lines:
        if line.startswith("|"):
            in_table = True
            continue
        elif in_table:
            in_table = False
            continue

        if line.startswith("## "):
            flush()
            section_body = []
            m = re.match(r'^##\s+(\d+)\.', line)
            current_section_num = m.group(1) if m else None
            continue

        if line.startswith("### "):
            sub = clean_for_speech(line)
            if not any(s in sub for s in SKIP_SUBSECTIONS):
                section_body.append(f"{sub}:")
            continue

        cleaned = clean_for_speech(line)
        if cleaned:
            if cleaned[-1] not in ".!?:": cleaned += "."
            section_body.append(cleaned)

    flush()

    # 4. Outro
    full_script.append("\n" + str(tpl.get("outro", "")))

    return "\n\n".join(full_script)

# ── TTS Engine ────────────────────────────────────────────────────────────────
async def generate_audio_file(text: str, output_path: str, voice: str):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="-5%")
    await communicate.save(output_path)
    print(f"[OK] Audio generated: {output_path}")

# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--lang",   default="en", choices=["en", "de"])
    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f"Script not found: {args.script}")
        sys.exit(1)

    voice = VOICES.get(args.lang, VOICES["en"])
    text  = build_narration(args.script, args.lang)

    if not text.strip():
        print("No narration text extracted.")
        sys.exit(1)

    asyncio.run(generate_audio_file(text, args.output, voice))

if __name__ == "__main__":
    main()
