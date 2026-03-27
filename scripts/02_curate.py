#!/usr/bin/env python3
"""Step 02: 选题筛选 & 打分 - Curate and score collected news."""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_episode_dir, get_pipeline_config
from utils.logger import setup_logger

logger = setup_logger("02_curate")

# Simple relevance scoring based on keyword matches
SCORE_KEYWORDS = {
    "GPT": 3.0,
    "OpenAI": 3.0,
    "Anthropic": 3.0,
    "Google": 2.5,
    "大模型": 2.5,
    "LLM": 2.5,
    "深度学习": 2.0,
    "transformer": 2.0,
    "机器学习": 2.0,
    "AI": 1.5,
    "neural": 1.5,
    "diffusion": 1.5,
    "model": 1.0,
    "算法": 1.0,
}

HIGH_PRIORITY_SOURCES = {"TechCrunch AI", "The Verge AI", "MIT Technology Review AI"}


def score_item(item: dict) -> float:
    """Score a news item for relevance and importance."""
    text = f"{item['title']} {item.get('summary', '')}".lower()
    score = 0.0

    # Keyword-based scoring
    for keyword, weight in SCORE_KEYWORDS.items():
        if keyword.lower() in text:
            score += weight

    # Source priority boost
    if item.get("source") in HIGH_PRIORITY_SOURCES:
        score *= 1.3

    if item.get("priority") == "high":
        score *= 1.2

    # Normalize to 0-1 range
    return min(score / 10.0, 1.0)


def deduplicate_by_similarity(items: list[dict]) -> list[dict]:
    """Remove very similar items based on title overlap."""
    unique = []
    seen_titles = []

    for item in items:
        title_words = set(item["title"].lower().split())
        is_dup = False

        for seen in seen_titles:
            overlap = len(title_words & seen) / max(len(title_words | seen), 1)
            if overlap > 0.6:
                is_dup = True
                break

        if not is_dup:
            unique.append(item)
            seen_titles.append(title_words)

    return unique


def curate(episode: str) -> Path:
    """Main curation function."""
    config = get_pipeline_config()
    ep_dir = get_episode_dir(episode)

    # Load collected items
    collected_path = ep_dir / "collected.json"
    if not collected_path.exists():
        raise FileNotFoundError(f"No collected data found: {collected_path}")

    with open(collected_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    logger.info(f"Loaded {len(items)} items for curation")

    # Score each item
    for item in items:
        item["relevance_score"] = score_item(item)

    # Sort by score
    items.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Deduplicate
    items = deduplicate_by_similarity(items)

    # Select top N
    max_stories = config.get("pipeline", {}).get("max_stories", 8)
    min_score = config.get("pipeline", {}).get("steps", {}).get("curate", {}).get("min_score", 0.3)
    selected = [i for i in items[:max_stories * 2] if i["relevance_score"] >= min_score][:max_stories]

    # Save curated items
    output = {
        "episode": episode,
        "curated_at": datetime.now().isoformat(),
        "total_candidates": len(items),
        "selected_count": len(selected),
        "items": selected,
    }

    output_path = ep_dir / "curated.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"Selected {len(selected)} stories -> {output_path}")
    for i, item in enumerate(selected, 1):
        logger.info(f"  {i}. [{item['relevance_score']:.2f}] {item['title']}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Step 02: Curate and score news")
    parser.add_argument("--episode", required=True, help="Episode number")
    args = parser.parse_args()

    output = curate(args.episode)
    print(f"✅ Curation complete: {output}")


if __name__ == "__main__":
    main()
