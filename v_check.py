import os
from pathlib import Path

def check_word_count(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    words = text.split()
    return len(words)

def check_audio_duration(file_path):
    # Using file size estimation for simplicity since mutagen might not be available
    size = os.path.getsize(file_path)
    # edge-tts typically produces 24kbps-48kbps MP3s
    # A 4-minute 32kbps MP3 is about 1MB
    # Let's just output the size for now and I'll judge based on that
    return size

if __name__ == "__main__":
    p_md = Path("c:/Users/Administrator/Documents/kasonaops/presentation/output/BEI_presentation.md")
    p_mp3 = Path("c:/Users/Administrator/Documents/kasonaops/presentation/output/BEI_briefing.mp3")
    
    if p_md.exists():
        wc = check_word_count(p_md)
        print(f"Word Count (MD): {wc}")
    
    if p_mp3.exists():
        size = check_audio_duration(p_mp3)
        print(f"Audio File Size: {size} bytes (~{size/1024/1024:.2f} MB)")
