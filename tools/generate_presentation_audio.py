#!/usr/bin/env python3
"""
generate_presentation_audio.py — Company Presentation Briefing TTS

Generates an MP3 audio file from a company presentation script.
Uses `edge-tts` for high-quality neural voices.

Usage:
    python3 generate_presentation_audio.py --script apple_script.md --output apple_briefing.mp3
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
    print("❌ edge-tts not installed. Run: pip install edge-tts")
    sys.exit(1)

VOICES = {
    "christopher": "en-US-ChristopherNeural",
    "jenny": "en-US-JennyNeural",
}

DEFAULT_VOICE = "en-US-ChristopherNeural"
DEFAULT_RATE = "+0%"

def clean_markdown_for_speech(text: str) -> str:
    """Strip markdown formatting for natural speech synthesis."""
    # Remove images entirely ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Handle links: keep just the text [link text](url)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    # Remove basic formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Remove headers and structural symbols
    text = text.replace("#", "")
    text = text.replace("- ", "") # Bullet points
    return text.strip()

def extract_tts_text(script_path: str) -> str:
    """Extract and clean text from the [SUBSKILL] section for TTS."""
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Target the subskill section specifically
    subskill_match = re.search(r'## \[SUBSKILL\] Neural Audio Briefing Script(.*?)$', content, re.DOTALL | re.IGNORECASE)
    if not subskill_match:
        # Fallback to general cleaning if subskill block not found
        lines = content.split("\n")
        section_text = "\n".join([l for l in lines if not l.strip().startswith("#") and "|" not in l])
    else:
        section_text = subskill_match.group(1)

    spoken_lines = []
    lines = section_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "---": continue
        
        # Strip internal labels like **Intro**:, Intro:, Outro:
        cleaned = re.sub(r'^\**[A-Za-z\s]+[\*]*:\s*', '', stripped)
        
        # Standard markdown cleaning
        cleaned = clean_markdown_for_speech(cleaned)
        
        if cleaned:
            spoken_lines.append(cleaned)
            
    return "\n".join(spoken_lines).strip()

async def generate_audio_file(text: str, output_path: str, voice: str, rate: str):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)
    print(f"[OK] Audio generated: {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--rate", default=DEFAULT_RATE)
    args = parser.parse_args()
    
    if not os.path.exists(args.script):
        print(f"❌ Script not found: {args.script}")
        sys.exit(1)
        
    voice = VOICES.get(args.voice.lower(), args.voice)
    text = extract_tts_text(args.script)
    if not text:
        print("❌ No text to speak.")
        sys.exit(1)
        
    asyncio.run(generate_audio_file(text, args.output, voice, args.rate))

if __name__ == "__main__":
    main()
