#!/usr/bin/env python3
"""Step 06: 字幕生成 - Generate SRT subtitles from audio using speech recognition."""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_episode_dir, get_pipeline_config, BASE_DIR
from utils.logger import setup_logger

logger = setup_logger("06_subtitles")


def extract_text_from_script(script_path: Path) -> list[dict]:
    """Extract text segments from script for subtitle timing."""
    text = script_path.read_text(encoding="utf-8")
    segments = []

    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line in ("---", "***", "==="):
            continue
        clean = line.replace("**", "").replace("*", "").strip()
        if clean and len(clean) > 3:
            segments.append({"text": clean})

    return segments


def estimate_duration(text: str, chars_per_second: float = 4.0) -> float:
    """Estimate speech duration based on text length."""
    return len(text) / chars_per_second


def generate_srt_from_script(script_path: Path, output_path: Path) -> list[dict]:
    """Generate SRT subtitles from script text with estimated timing."""
    segments = extract_text_from_script(script_path)
    subs = []
    current_time = 0.0

    for i, seg in enumerate(segments, 1):
        duration = estimate_duration(seg["text"])
        start = current_time
        end = current_time + duration

        start_ts = format_timestamp(start)
        end_ts = format_timestamp(end)

        subs.append({
            "index": i,
            "start": start_ts,
            "end": end_ts,
            "text": seg["text"],
        })

        current_time = end + 0.3  # Small gap between subtitles

    # Write SRT file
    with open(output_path, "w", encoding="utf-8") as f:
        for sub in subs:
            f.write(f"{sub['index']}\n")
            f.write(f"{sub['start']} --> {sub['end']}\n")
            f.write(f"{sub['text']}\n\n")

    return subs


def generate_srt_from_audio(audio_manifest: dict, output_path: Path, config: dict) -> list[dict]:
    """Generate SRT using faster-whisper if audio is available."""
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("base", device="cpu", compute_type="int8")
        subs = []
        idx = 1

        for seg_info in audio_manifest.get("segments", []):
            audio_file = seg_info.get("file")
            if not audio_file or not Path(audio_file).exists():
                continue

            segments_iter, info = model.transcribe(audio_file, language="zh")
            for segment in segments_iter:
                start_ts = format_timestamp(segment.start)
                end_ts = format_timestamp(segment.end)
                subs.append({
                    "index": idx,
                    "start": start_ts,
                    "end": end_ts,
                    "text": segment.text.strip(),
                })
                idx += 1

        # Write SRT
        with open(output_path, "w", encoding="utf-8") as f:
            for sub in subs:
                f.write(f"{sub['index']}\n")
                f.write(f"{sub['start']} --> {sub['end']}\n")
                f.write(f"{sub['text']}\n\n")

        return subs

    except ImportError:
        logger.warning("faster-whisper not available, using script-based subtitles")
        return None
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_subtitles(episode: str) -> Path:
    """Main subtitle generation function."""
    config = get_pipeline_config()
    ep_dir = get_episode_dir(episode)
    subs_dir = BASE_DIR / "assets" / "subtitles"
    subs_dir.mkdir(parents=True, exist_ok=True)

    srt_path = subs_dir / f"ep{episode}.srt"

    # Try whisper-based subtitles first
    audio_manifest_path = ep_dir / "audio_manifest.json"
    subs = None

    if audio_manifest_path.exists():
        with open(audio_manifest_path, "r", encoding="utf-8") as f:
            audio_manifest = json.load(f)
        subs = generate_srt_from_audio(audio_manifest, srt_path, config)

    # Fallback to script-based estimation
    if subs is None:
        script_path = ep_dir / "script.md"
        if not script_path.exists():
            raise FileNotFoundError(f"No script found: {script_path}")
        subs = generate_srt_from_script(script_path, srt_path)

    # Save metadata
    meta = {
        "episode": episode,
        "generated_at": datetime.now().isoformat(),
        "subtitle_count": len(subs),
        "method": "whisper" if audio_manifest_path.exists() else "script_estimation",
        "srt_path": str(srt_path),
    }
    meta_path = ep_dir / "subtitles_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info(f"Generated {len(subs)} subtitle entries -> {srt_path}")
    return srt_path


def main():
    parser = argparse.ArgumentParser(description="Step 06: Generate subtitles")
    parser.add_argument("--episode", required=True, help="Episode number")
    args = parser.parse_args()

    output = generate_subtitles(args.episode)
    print(f"✅ Subtitle generation complete: {output}")


if __name__ == "__main__":
    main()
