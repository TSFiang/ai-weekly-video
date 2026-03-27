#!/usr/bin/env python3
"""Step 07: 视频合成 - Compose final video from assets."""

import json
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_episode_dir, get_pipeline_config, BASE_DIR, get_output_dir
from utils.logger import setup_logger

logger = setup_logger("07_compose")


def get_duration(audio_path: Path) -> float:
    """Get audio duration using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0  # Default fallback


def build_ffmpeg_command(episode: str, ep_dir: Path, config: dict) -> list[str]:
    """Build the ffmpeg command for video composition."""
    video_config = config.get("pipeline", {}).get("video", {})
    output_config = config.get("pipeline", {}).get("output", {})

    resolution = video_config.get("resolution", "1920x1080")
    fps = video_config.get("fps", 30)
    codec = output_config.get("codec", "libx264")
    audio_codec = output_config.get("audio_codec", "aac")
    bitrate = output_config.get("bitrate", "8M")

    images_dir = BASE_DIR / "assets" / "images"
    audio_dir = BASE_DIR / "assets" / "audio"
    output_dir = get_output_dir()
    output_path = output_dir / f"ai_weekly_ep{episode}.mp4"

    # Load manifests
    visuals_path = ep_dir / "visuals_manifest.json"
    audio_manifest_path = ep_dir / "audio_manifest.json"

    visuals = []
    audio_segments = []

    if visuals_path.exists():
        with open(visuals_path, "r") as f:
            visuals = json.load(f).get("visuals", [])

    if audio_manifest_path.exists():
        with open(audio_manifest_path, "r") as f:
            audio_segments = json.load(f).get("segments", [])

    if not visuals:
        # Create a simple black video as fallback
        logger.warning("No visuals found, creating placeholder video")
        return build_placeholder_command(episode, output_path, config)

    # Build input files and filter complex
    ffmpeg_args = []       # flat list of ffmpeg args (inputs + options)
    input_idx = 0          # running count of -i inputs
    filter_parts = []
    duration_per_image = 5.0  # seconds per image

    # Add audio input if available
    has_audio = any(seg.get("file") for seg in audio_segments)
    audio_stream_idx = -1

    if has_audio:
        # Concatenate audio segments via concat demuxer
        audio_list = ep_dir / "audio_list.txt"
        with open(audio_list, "w") as f:
            for seg in audio_segments:
                if seg.get("file") and Path(seg["file"]).exists():
                    f.write(f"file '{seg['file']}'\n")
        ffmpeg_args.extend(["-f", "concat", "-safe", "0", "-i", str(audio_list)])
        audio_stream_idx = input_idx
        input_idx += 1

    # Add image inputs — each image is one -i
    image_start_idx = input_idx
    valid_visuals = []
    for vis in visuals:
        img_path = Path(vis["file"])
        if img_path.exists():
            ffmpeg_args.extend(["-loop", "1", "-t", str(duration_per_image), "-i", str(img_path)])
            valid_visuals.append(img_path)
            input_idx += 1

    if not valid_visuals:
        logger.warning("No valid visual images, creating placeholder video")
        return build_placeholder_command(episode, output_path, config)

    # Build filter to concatenate images
    num_images = len(valid_visuals)
    if num_images > 1:
        concat_inputs = "".join(f"[{image_start_idx + i}:v]" for i in range(num_images))
        filter_parts.append(
            f"{concat_inputs}concat=n={num_images}:v=1:a=0[vout]"
        )
        map_video = "[vout]"
    else:
        map_video = f"{image_start_idx}:v"

    cmd = ["ffmpeg", "-y"]
    cmd.extend(ffmpeg_args)

    if filter_parts:
        cmd.extend(["-filter_complex", ";".join(filter_parts)])

    # Map video
    cmd.extend(["-map", map_video])

    # Map audio if available
    if has_audio and audio_stream_idx >= 0:
        cmd.extend(["-map", f"{audio_stream_idx}:a"])

    # Output settings
    cmd.extend([
        "-c:v", codec,
        "-b:v", bitrate,
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
    ])

    if has_audio:
        cmd.extend(["-c:a", audio_codec, "-b:a", "192k"])

    cmd.extend(["-shortest", str(output_path)])

    return cmd


def build_placeholder_command(episode: str, output_path: Path, config: dict) -> list[str]:
    """Build a simple placeholder video."""
    return [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=10:r=30",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "10",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]


def compose_video(episode: str) -> Path:
    """Main video composition function."""
    config = get_pipeline_config()
    ep_dir = get_episode_dir(episode)

    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        logger.error("ffmpeg not found! Please install ffmpeg.")
        raise SystemExit("ffmpeg is required but not installed")

    # Build and run ffmpeg command
    cmd = build_ffmpeg_command(episode, ep_dir, config)
    logger.info(f"Running ffmpeg: {' '.join(cmd[:10])}...")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            logger.error(f"ffmpeg failed: {result.stderr[:500]}")
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out after 600s")
        raise

    output_path = get_output_dir() / f"ai_weekly_ep{episode}.mp4"

    # Save composition metadata
    meta = {
        "episode": episode,
        "composed_at": datetime.now().isoformat(),
        "output_path": str(output_path),
        "output_exists": output_path.exists(),
        "output_size": output_path.stat().st_size if output_path.exists() else 0,
        "ffmpeg_command": cmd[:5],
    }
    meta_path = ep_dir / "composition_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info(f"Video composed: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Step 07: Compose video")
    parser.add_argument("--episode", required=True, help="Episode number")
    args = parser.parse_args()

    output = compose_video(args.episode)
    print(f"✅ Video composition complete: {output}")


if __name__ == "__main__":
    main()
