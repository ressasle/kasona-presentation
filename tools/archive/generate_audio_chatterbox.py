"""
Earnings Briefing TTS Audio Generator — Chatterbox Edition.
Generates WAV audio from the English earnings TTS script using Resemble AI's Chatterbox.

⚡ Chatterbox requires a CUDA GPU (NVIDIA).
   - Turbo: 350M params, ~2GB VRAM, fastest
   - Original: 500M params, ~4GB VRAM, more expressive
   - Multilingual: 500M params, ~4GB VRAM, 23 languages

Fallback: If no GPU available, uses edge-tts (CPU, free, cloud-based).

Usage:
    # GPU mode (Chatterbox):
    pip install chatterbox-tts
    python generate_audio_chatterbox.py

    # CPU fallback (edge-tts):
    pip install edge-tts
    python generate_audio_chatterbox.py --fallback-edge-tts

    # With voice cloning (provide a 10s reference clip):
    python generate_audio_chatterbox.py --reference my_voice.wav

    # Use Turbo model (faster, paralinguistic tags):
    python generate_audio_chatterbox.py --model turbo
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path


# ── Text Extractor ───────────────────────────────────────────────────────────

def extract_tts_text(script_path: str) -> str:
    """Read TTS script markdown and extract spoken text."""
    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    spoken_lines = []
    in_frontmatter = False
    frontmatter_closed = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # YAML frontmatter (only at file start)
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter and not frontmatter_closed:
            if stripped == "---":
                frontmatter_closed = True
            continue

        if stripped == "---":
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            continue
        if not stripped:
            spoken_lines.append("")
            continue

        spoken_lines.append(stripped)

    text = "\n".join(spoken_lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return text.strip()


# ── Chatterbox TTS Generator ────────────────────────────────────────────────

def generate_with_chatterbox(
    text: str,
    output_path: str,
    model_type: str = "original",
    reference_audio: str = None,
    exaggeration: float = 0.3,
    cfg_weight: float = 0.5,
):
    """
    Generate audio using Resemble AI's Chatterbox TTS.

    Args:
        text: Text to synthesize.
        output_path: Output WAV file path.
        model_type: "turbo" (350M, fast), "original" (500M), or "multilingual" (500M, 23 langs).
        reference_audio: Optional path to a 10s reference WAV for voice cloning.
        exaggeration: Expressiveness (0.0-1.0). Higher = more dramatic. Default 0.3 for CIO briefing.
        cfg_weight: Classifier-free guidance (0.0-1.0). Lower = slower pacing. Default 0.5.
    """
    import torch
    import torchaudio as ta

    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cpu":
        print("⚠️  No CUDA GPU detected. Chatterbox works best on GPU.")
        print("   Attempting CPU mode (will be slow)...")
        print("   Consider using --fallback-edge-tts for fast CPU generation.\n")

    if model_type == "turbo":
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        print(f"🚀  Loading Chatterbox Turbo (350M) on {device}...")
        model = ChatterboxTurboTTS.from_pretrained(device=device)
    else:
        from chatterbox.tts import ChatterboxTTS
        print(f"🎙️  Loading Chatterbox Original (500M) on {device}...")
        model = ChatterboxTTS.from_pretrained(device=device)

    print(f"📝  Text length: {len(text)} characters (~{len(text.split())} words)")
    print(f"⏱️  Estimated duration: ~{len(text.split()) // 150} minutes")
    print(f"🎛️  Exaggeration: {exaggeration} | CFG Weight: {cfg_weight}")
    if reference_audio:
        print(f"🎤  Voice cloning from: {Path(reference_audio).name}")
    print(f"💾  Output: {output_path}\n")

    # Chatterbox handles long texts by chunking internally
    # For best quality, we split on paragraph breaks and concatenate
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    all_wavs = []
    for i, paragraph in enumerate(paragraphs):
        if not paragraph or paragraph == "...":
            # Insert 0.5s silence for pause markers
            silence = torch.zeros(1, int(model.sr * 0.5))
            all_wavs.append(silence)
            continue

        print(f"  ▸ Generating paragraph {i+1}/{len(paragraphs)} ({len(paragraph)} chars)")

        kwargs = {}
        if reference_audio:
            kwargs["audio_prompt_path"] = reference_audio

        if model_type != "turbo":
            kwargs["exaggeration"] = exaggeration
            kwargs["cfg_weight"] = cfg_weight

        wav = model.generate(paragraph, **kwargs)
        all_wavs.append(wav)

        # Add short silence between paragraphs
        silence = torch.zeros(1, int(model.sr * 0.3))
        all_wavs.append(silence)

    # Concatenate all audio chunks
    final_wav = torch.cat(all_wavs, dim=1)

    # Save
    ta.save(output_path, final_wav, model.sr)

    file_size = os.path.getsize(output_path)
    duration_s = final_wav.shape[1] / model.sr
    print(f"\n✅  Audio generated successfully!")
    print(f"📦  File size: {file_size / 1024 / 1024:.1f} MB")
    print(f"⏱️  Duration: {int(duration_s // 60)}:{int(duration_s % 60):02d}")

    return os.path.abspath(output_path)


# ── Edge-TTS Fallback (CPU) ─────────────────────────────────────────────────

async def generate_with_edge_tts(
    text: str,
    output_path: str,
    voice: str = "en-US-ChristopherNeural",
    rate: str = "+0%",
):
    """Fallback: Generate MP3 using edge-tts (no GPU needed)."""
    import edge_tts

    print(f"🎙️  Generating with edge-tts (CPU fallback)")
    print(f"🗣️  Voice: {voice}")
    print(f"📝  Text length: {len(text)} characters (~{len(text.split())} words)")
    print(f"💾  Output: {output_path}\n")

    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)

    file_size = os.path.getsize(output_path)
    print(f"✅  Audio generated successfully!")
    print(f"📦  File size: {file_size / 1024 / 1024:.1f} MB")

    return os.path.abspath(output_path)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate TTS audio from earnings briefing (Chatterbox or edge-tts)"
    )
    parser.add_argument(
        "--script",
        default=os.path.join(os.path.dirname(__file__), "beiersdorf_q4_fy2025_tts_script_EN.md"),
        help="Path to the English TTS script",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (WAV for Chatterbox, MP3 for edge-tts)",
    )
    parser.add_argument(
        "--model",
        choices=["turbo", "original"],
        default="original",
        help="Chatterbox model variant (default: original)",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="Reference audio WAV (~10s) for voice cloning",
    )
    parser.add_argument(
        "--exaggeration",
        type=float,
        default=0.3,
        help="Expressiveness (0.0-1.0). Lower = more measured/CIO style (default: 0.3)",
    )
    parser.add_argument(
        "--cfg-weight",
        type=float,
        default=0.5,
        help="CFG weight (0.0-1.0). Lower = slower pacing (default: 0.5)",
    )
    parser.add_argument(
        "--fallback-edge-tts",
        action="store_true",
        help="Use edge-tts instead of Chatterbox (no GPU needed)",
    )
    parser.add_argument(
        "--edge-voice",
        default="en-US-ChristopherNeural",
        help="Edge-TTS voice for fallback (default: ChristopherNeural)",
    )

    args = parser.parse_args()

    # Read script
    if not os.path.exists(args.script):
        print(f"❌ Script not found: {args.script}")
        sys.exit(1)

    print(f"📖  Reading script: {Path(args.script).name}")
    text = extract_tts_text(args.script)

    if not text:
        print("❌ No spoken text found in the script.")
        sys.exit(1)

    # Determine output path
    script_dir = os.path.dirname(args.script)
    if args.fallback_edge_tts:
        default_output = os.path.join(script_dir, "beiersdorf_q4_fy2025_briefing_EN.mp3")
    else:
        default_output = os.path.join(script_dir, "beiersdorf_q4_fy2025_briefing_EN.wav")

    output_path = args.output or default_output

    # Generate
    if args.fallback_edge_tts:
        asyncio.run(
            generate_with_edge_tts(
                text=text,
                output_path=output_path,
                voice=args.edge_voice,
            )
        )
    else:
        try:
            generate_with_chatterbox(
                text=text,
                output_path=output_path,
                model_type=args.model,
                reference_audio=args.reference,
                exaggeration=args.exaggeration,
                cfg_weight=args.cfg_weight,
            )
        except ImportError:
            print("❌ chatterbox-tts not installed. Run: pip install chatterbox-tts")
            print("   Or use --fallback-edge-tts for CPU generation.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Chatterbox error: {e}")
            print("   Falling back to edge-tts...")
            output_path = output_path.replace(".wav", ".mp3")
            asyncio.run(
                generate_with_edge_tts(
                    text=text,
                    output_path=output_path,
                    voice=args.edge_voice,
                )
            )

    print(f"\n🎧  Play with: open '{output_path}'")


if __name__ == "__main__":
    main()
