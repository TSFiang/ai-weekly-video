#!/usr/bin/env python3
"""Step 01: 信息采集 - Collect AI news from various sources."""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

import feedparser
import httpx

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_sources_config, get_episode_dir, BASE_DIR
from utils.logger import setup_logger

logger = setup_logger("01_collect")


def collect_rss(source: dict) -> list[dict]:
    """Collect articles from an RSS feed."""
    items = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:50]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500],
                "published": entry.get("published", ""),
                "source": source["name"],
                "priority": source.get("priority", "medium"),
            })
        logger.info(f"RSS [{source['name']}]: {len(items)} items")
    except Exception as e:
        logger.error(f"RSS [{source['name']}] failed: {e}")
    return items


def collect_web(source: dict) -> list[dict]:
    """Collect articles from a web API (JSON)."""
    items = []
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(source["url"])
            resp.raise_for_status()
            data = resp.json()

        if source.get("type") == "json_api":
            for hit in data.get("hits", [])[:30]:
                items.append({
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "summary": hit.get("title", ""),
                    "published": hit.get("created_at", ""),
                    "source": source["name"],
                    "priority": source.get("priority", "medium"),
                })
        logger.info(f"Web [{source['name']}]: {len(items)} items")
    except Exception as e:
        logger.error(f"Web [{source['name']}] failed: {e}")
    return items


def filter_keywords(items: list[dict], config: dict) -> list[dict]:
    """Filter items by keywords."""
    keywords = [kw.lower() for kw in config.get("keywords", [])]
    exclude = [kw.lower() for kw in config.get("exclude_keywords", [])]

    filtered = []
    for item in items:
        text = f"{item['title']} {item['summary']}".lower()

        # Check exclude first
        if any(ex in text for ex in exclude):
            continue

        # Must match at least one keyword
        if not keywords or any(kw in text for kw in keywords):
            filtered.append(item)

    return filtered


def collect(episode: str) -> Path:
    """Main collection function."""
    config = get_sources_config()
    items = []

    # RSS sources
    for source in config.get("sources", {}).get("rss", []):
        if source.get("enabled", True):
            items.extend(collect_rss(source))

    # Web sources
    for source in config.get("sources", {}).get("web", []):
        if source.get("enabled", True):
            items.extend(collect_web(source))

    # Filter by keywords
    items = filter_keywords(items, config)

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for item in items:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique.append(item)

    # Save
    ep_dir = get_episode_dir(episode)
    output_path = ep_dir / "collected.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "episode": episode,
            "collected_at": datetime.now().isoformat(),
            "total_items": len(unique),
            "items": unique,
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"Collected {len(unique)} unique items -> {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Step 01: Collect AI news")
    parser.add_argument("--episode", required=True, help="Episode number (e.g., 001)")
    args = parser.parse_args()

    output = collect(args.episode)
    print(f"✅ Collection complete: {output}")


if __name__ == "__main__":
    main()
