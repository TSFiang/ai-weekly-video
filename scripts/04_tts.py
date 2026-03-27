#!/usr/bin/env python3
"""Step 04: AI配音 - Generate TTS audio from script."""

import json
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_episode_dir, get_pipeline_config, BASE_DIR
from utils.logger import setup_logger

logger = setup_logger("04_tts")


def extract_text_from_script(script_path: Path) -> list[dict]:
    """Extract speakable text segments from markdown script."""
    text = script_path.read_text(encoding="utf-8")
    segments = []
    current_segment = {"title": "intro", "text": ""}

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Skip markdown headers and formatting
        if line.startswith("#"):
            if current_segment["text"]:
                segments.append(current_segment)
            header_text = line.lstrip("#").strip()
            current_segment = {"title": header_text, "text": ""}
            continue

        # Skip bold markers and separators
        if line in ("---", "***", "==="):
            continue

        # Clean markdown formatting for speech
        clean_line = line.replace("**", "").replace("*", "").replace("###", "").strip()
        if clean_line:
            current_segment["text"] += clean_line + " "

    if current_segment["text"]:
        segments.append(current_segment)

    return segments


def generate_tts_edge(text: str, output_path: Path, config: dict) -> bool:
    """Generate TTS using edge-tts."""
    tts_config = config.get("pipeline", {}).get("tts", {})
    voice = tts_config.get("voice", "zh-CN-XiaoxiaoNeural")
    rate = tts_config.get("rate", "+10%")

    try:
        import edge_tts
        import asyncio

        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(str(output_path))

        asyncio.run(_generate())
        return True
    except ImportError:
        logger.warning("edge-tts not installed, using espeak-ng fallback")
        return generate_tts_espeak(text, output_path, config)
    except Exception as e:
        logger.error(f"edge-tts failed: {e}")
        return generate_tts_espeak(text, output_path, config)


def generate_tts_espeak(text: str, output_path: Path, config: dict) -> bool:
    """Fallback TTS using espeak-ng."""
    wav_path = output_path.with_suffix(".wav")
    try:
        cmd = [
            "espeak-ng",
            "-v", "zh",
            "-s", "160",
            "-w", str(wav_path),
            text,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)

        # Convert wav to mp3 if ffmpeg available
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(wav_path), str(output_path)],
                check=True, capture_output=True, timeout=30,
            )
            wav_path.unlink(missing_ok=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Just use wav directly
            if wav_path.exists():
                output_path_final = output_path.with_suffix(".wav")
                wav_path.rename(output_path_final)

        return True
    except Exception as e:
        logger.error(f"espeak-ng failed: {e}")
        return False


def generate_tts(episode: str) -> Path:
    """Main TTS generation function."""
    config = get_pipeline_config()
    ep_dir = get_episode_dir(episode)
    audio_dir = BASE_DIR / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Load script
    script_path = ep_dir / "script.md"
    if not script_path.exists():
        raise FileNotFoundError(f"No script found: {script_path}")

    # Extract text segments
    segments = extract_text_from_script(script_path)
    logger.info(f"Extracted {len(segments)} segments from script")

    # Generate audio for each segment
    audio_files = []
    for i, segment in enumerate(segments):
        if not segment["text"].strip():
            continue

        output_path = audio_dir / f"ep{episode}_seg{i:02d}.mp3"
        logger.info(f"Generating TTS for segment {i}: {segment['title'][:30]}...")

        success = generate_tts_edge(segment["text"], output_path, config)
        if success and output_path.exists():
            audio_files.append({
                "index": i,
                "title": segment["title"],
                "file": str(output_path),
                "text_preview": segment["text"][:100],
            })
        else:
            # Create a placeholder
            logger.warning(f"TTS failed for segment {i}, creating placeholder")
            audio_files.append({
                "index": i,
                "title": segment["title"],
                "file": None,
                "text_preview": segment["text"][:100],
            })

    # Save audio manifest
    manifest = {
        "episode": episode,
        "generated_at": datetime.now().isoformat(),
        "segments": audio_files,
    }
    manifest_path = ep_dir / "audio_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(f"Generated {len(audio_files)} audio segments -> {manifest_path}")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="Step 04: Generate TTS audio")
    parser.add_argument("--episode", required=True, help="Episode number")
    args = parser.parse_args()

    output = generate_tts(args.episode)
    print(f"✅ TTS generation complete: {output}")


if __name__ == "__main__":
    main()
