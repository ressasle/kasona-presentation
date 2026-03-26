import os
import argparse
import re
from gtts import gTTS
from pathlib import Path

def clean_markdown_for_speech(text: str) -> str:
    # 1. Strip bold and italic
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # 2. Strip inline code
    text = re.sub(r'`(.*?)`', r'\1', text)
    # 3. Strip hyperlinks: [label](url) -> label
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 4. Remove excessive symbols
    text = text.replace("#", "")
    text = text.replace("|", " ")
    return text.strip()

def extract_tts_text(script_path: str) -> str:
    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    spoken_lines = []
    in_frontmatter = False
    frontmatter_closed = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter and not frontmatter_closed:
            if stripped == "---":
                frontmatter_closed = True
            continue
        if stripped == "---" or stripped.startswith("#") or stripped.startswith(">"):
            continue
        if not stripped:
            if spoken_lines and spoken_lines[-1] != "":
                spoken_lines.append("")
            continue
        cleaned = clean_markdown_for_speech(stripped)
        if cleaned:
            spoken_lines.append(cleaned)
    return "\n".join(spoken_lines).strip()

def main():
    parser = argparse.ArgumentParser(description="Generate audio via gTTS")
    parser.add_argument("--script", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    print(f"[*] Extracting text from: {args.script}")
    text = extract_tts_text(args.script)
    
    if not text:
        print("❌ No text found.")
        return

    print(f"[*] Generating audio (gTTS): {args.output}")
    tts = gTTS(text=text, lang='en')
    tts.save(args.output)
    print(f"[OK] Audio saved: {args.output}")

if __name__ == "__main__":
    main()
