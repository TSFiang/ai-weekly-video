#!/usr/bin/env python3
"""Step 08: 多平台发布 - Publish video to multiple platforms."""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_episode_dir, get_platforms_config, get_pipeline_config, get_output_dir
from utils.logger import setup_logger

logger = setup_logger("08_publish")


def generate_description(episode: str, stories: list[dict], platform: str) -> str:
    """Generate platform-specific description."""
    stories_text = "\n".join(
        f"  {i+1}. {s.get('title', 'N/A')}"
        for i, s in enumerate(stories)
    )

    if platform == "bilibili":
        return (
            f"第{episode}期 AI 周刊 | {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"本期内容：\n{stories_text}\n\n"
            f"#AI #人工智能 #科技 #大模型"
        )
    elif platform == "youtube":
        return (
            f"AI Weekly Episode #{episode} | {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"Topics covered:\n{stories_text}\n\n"
            f"#AI #ArtificialIntelligence #Tech #MachineLearning"
        )
    else:
        return f"AI Weekly #{episode}\n\n{stories_text}"


def publish_to_bilibili(video_path: Path, meta: dict, platform_config: dict) -> dict:
    """Publish video to Bilibili (stub - requires real API integration)."""
    logger.info(f"[Bilibili] Would publish: {video_path}")
    return {
        "platform": "bilibili",
        "status": "stub",
        "message": "Bilibili upload requires API credentials. Configure in platforms.yaml.",
        "video_path": str(video_path),
    }


def publish_to_youtube(video_path: Path, meta: dict, platform_config: dict) -> dict:
    """Publish video to YouTube (stub - requires real API integration)."""
    logger.info(f"[YouTube] Would publish: {video_path}")
    return {
        "platform": "youtube",
        "status": "stub",
        "message": "YouTube upload requires OAuth credentials. Configure in platforms.yaml.",
        "video_path": str(video_path),
    }


def publish_to_douyin(video_path: Path, meta: dict, platform_config: dict) -> dict:
    """Publish video to Douyin (stub)."""
    logger.info(f"[Douyin] Would publish: {video_path}")
    return {
        "platform": "douyin",
        "status": "stub",
        "message": "Douyin upload not yet implemented.",
        "video_path": str(video_path),
    }


PLATFORM_PUBLISHERS = {
    "bilibili": publish_to_bilibili,
    "youtube": publish_to_youtube,
    "douyin": publish_to_douyin,
}


def publish(episode: str) -> Path:
    """Main publish function."""
    config = get_pipeline_config()
    platforms_config = get_platforms_config()
    ep_dir = get_episode_dir(episode)

    # Find video
    output_dir = get_output_dir()
    video_path = output_dir / f"ai_weekly_ep{episode}.mp4"
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Load stories for description
    curated_path = ep_dir / "curated.json"
    stories = []
    if curated_path.exists():
        with open(curated_path, "r", encoding="utf-8") as f:
            stories = json.load(f).get("items", [])

    results = []
    for platform_name, platform_config in platforms_config.get("platforms", {}).items():
        if not platform_config.get("enabled", False):
            logger.info(f"Skipping {platform_name} (disabled)")
            continue

        publisher = PLATFORM_PUBLISHERS.get(platform_name)
        if not publisher:
            logger.warning(f"No publisher for {platform_name}")
            continue

        # Generate description
        desc = generate_description(episode, stories, platform_name)

        meta = {
            "episode": episode,
            "title": f"AI Weekly 第{episode}期",
            "description": desc,
            "tags": platform_config.get("upload", {}).get("tags", ""),
        }

        result = publisher(video_path, meta, platform_config)
        results.append(result)

    # Save publish results
    publish_meta = {
        "episode": episode,
        "published_at": datetime.now().isoformat(),
        "video_path": str(video_path),
        "results": results,
    }
    meta_path = ep_dir / "publish_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(publish_meta, f, ensure_ascii=False, indent=2)

    logger.info(f"Publish results saved: {meta_path}")
    return meta_path


def main():
    parser = argparse.ArgumentParser(description="Step 08: Publish video")
    parser.add_argument("--episode", required=True, help="Episode number")
    args = parser.parse_args()

    output = publish(args.episode)
    print(f"✅ Publish step complete: {output}")


if __name__ == "__main__":
    main()
