#!/usr/bin/env python3
"""
AI Weekly Video Pipeline - Main Entry Point

Usage:
    python run_pipeline.py                  # Run full pipeline
    python run_pipeline.py --episode 001    # Run for specific episode
    python run_pipeline.py --step collect   # Run single step
"""

import argparse
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from scripts.utils import get_pipeline_config
from scripts.utils.logger import setup_logger

logger = setup_logger("pipeline")

# Pipeline steps in order
PIPELINE_STEPS = [
    ("collect", "scripts.01_collect", "collect"),
    ("curate", "scripts.02_curate", "curate"),
    ("script", "scripts.03_script", "generate_script"),
    ("tts", "scripts.04_tts", "generate_tts"),
    ("visuals", "scripts.05_visuals", "generate_visuals"),
    ("subtitles", "scripts.06_subtitles", "generate_subtitles"),
    ("compose", "scripts.07_compose", "compose_video"),
    ("publish", "scripts.08_publish", "publish"),
]


def get_next_episode() -> str:
    """Auto-detect next episode number."""
    data_dir = BASE_DIR / "data" / "processed"
    if not data_dir.exists():
        return "001"

    existing = sorted(data_dir.glob("episode_*"))
    if not existing:
        return "001"

    last = existing[-1].name.replace("episode_", "")
    try:
        return f"{int(last) + 1:03d}"
    except ValueError:
        return "001"


def run_step(step_name: str, episode: str) -> dict:
    """Run a single pipeline step."""
    step_info = next((s for s in PIPELINE_STEPS if s[0] == step_name), None)
    if not step_info:
        return {"status": "error", "message": f"Unknown step: {step_name}"}

    _, module_name, func_name = step_info

    start = time.time()
    try:
        import importlib
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        result = func(episode)
        elapsed = time.time() - start

        return {
            "status": "success",
            "step": step_name,
            "result": str(result),
            "elapsed_seconds": round(elapsed, 2),
        }
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Step {step_name} failed: {e}")
        logger.error(traceback.format_exc())

        return {
            "status": "error",
            "step": step_name,
            "error": str(e),
            "elapsed_seconds": round(elapsed, 2),
        }


def run_pipeline(episode: str, start_from: str = None) -> list[dict]:
    """Run the full pipeline or from a specific step."""
    config = get_pipeline_config()
    steps_config = config.get("pipeline", {}).get("steps", {})

    results = []
    skip = start_from is not None

    for step_name, _, _ in PIPELINE_STEPS:
        if skip:
            if step_name == start_from:
                skip = False
            else:
                continue

        # Check if step is enabled
        step_cfg = steps_config.get(step_name, {})
        if not step_cfg.get("enabled", True):
            logger.info(f"Skipping {step_name} (disabled in config)")
            results.append({"status": "skipped", "step": step_name})
            continue

        logger.info(f"{'='*60}")
        logger.info(f"Running step: {step_name}")
        logger.info(f"{'='*60}")

        result = run_step(step_name, episode)
        results.append(result)

        if result["status"] == "error":
            logger.error(f"Pipeline stopped at {step_name}: {result['error']}")
            break

    return results


def print_summary(results: list[dict], episode: str):
    """Print a summary of the pipeline run."""
    print(f"\n{'='*60}")
    print(f"  AI Weekly Video Pipeline - Episode {episode}")
    print(f"{'='*60}")

    total_time = 0
    for r in results:
        status = r["status"]
        step = r.get("step", "?")
        elapsed = r.get("elapsed_seconds", 0)
        total_time += elapsed

        icon = {"success": "✅", "error": "❌", "skipped": "⏭️"}.get(status, "❓")
        print(f"  {icon} {step:12s} {status:8s} ({elapsed:.1f}s)")

    print(f"{'='*60}")
    print(f"  Total time: {total_time:.1f}s")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="AI Weekly Video Pipeline")
    parser.add_argument("--episode", default=None, help="Episode number (auto-detect if omitted)")
    parser.add_argument("--step", default=None, help="Run single step only")
    parser.add_argument("--start-from", default=None, help="Start from specific step")
    args = parser.parse_args()

    episode = args.episode or get_next_episode()
    logger.info(f"Episode: {episode}")

    if args.step:
        result = run_step(args.step, episode)
        print(f"\n{'✅' if result['status'] == 'success' else '❌'} {args.step}: {result['status']}")
    else:
        results = run_pipeline(episode, args.start_from)
        print_summary(results, episode)


if __name__ == "__main__":
    main()
