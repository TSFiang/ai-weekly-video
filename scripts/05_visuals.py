#!/usr/bin/env python3
"""Step 05: 画面生成 - Generate visual assets for video."""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_episode_dir, get_pipeline_config, BASE_DIR
from utils.logger import setup_logger

logger = setup_logger("05_visuals")

# Color schemes
COLOR_SCHEMES = {
    "modern": {
        "bg": (10, 10, 10),
        "primary": (0, 200, 255),
        "secondary": (255, 100, 50),
        "text": (255, 255, 255),
        "accent": (100, 255, 100),
    },
    "minimal": {
        "bg": (30, 30, 30),
        "primary": (220, 220, 220),
        "secondary": (100, 100, 100),
        "text": (255, 255, 255),
        "accent": (80, 80, 80),
    },
    "neon": {
        "bg": (5, 5, 20),
        "primary": (255, 0, 128),
        "secondary": (0, 255, 200),
        "text": (255, 255, 255),
        "accent": (255, 255, 0),
    },
}

RESOLUTION = (1920, 1080)


def get_font(size: int = 48) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default."""
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def create_title_card(episode: str, colors: dict) -> Image.Image:
    """Create an episode title card."""
    img = Image.new("RGB", RESOLUTION, colors["bg"])
    draw = ImageDraw.Draw(img)

    # Decorative lines
    for i in range(0, RESOLUTION[0], 40):
        alpha = int(30 + 20 * (i % 80 == 0))
        draw.line([(i, 0), (i, RESOLUTION[1])], fill=(*colors["primary"], alpha), width=1)

    # Episode title
    font_title = get_font(72)
    font_sub = get_font(36)

    title = f"AI Weekly"
    subtitle = f"第 {episode} 期"

    # Center text
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((RESOLUTION[0] - tw) // 2, 380), title, fill=colors["primary"], font=font_title)

    bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sw = bbox[2] - bbox[0]
    draw.text(((RESOLUTION[0] - sw) // 2, 480), subtitle, fill=colors["text"], font=font_sub)

    # Decorative bar
    bar_width = 200
    bar_x = (RESOLUTION[0] - bar_width) // 2
    draw.rectangle([bar_x, 550, bar_x + bar_width, 554], fill=colors["primary"])

    date_str = datetime.now().strftime("%Y.%m.%d")
    bbox = draw.textbbox((0, 0), date_str, font=font_sub)
    dw = bbox[2] - bbox[0]
    draw.text(((RESOLUTION[0] - dw) // 2, 580), date_str, fill=colors["secondary"], font=font_sub)

    return img


def create_story_card(title: str, index: int, colors: dict) -> Image.Image:
    """Create a card for each story."""
    img = Image.new("RGB", RESOLUTION, colors["bg"])
    draw = ImageDraw.Draw(img)

    # Index number
    font_big = get_font(120)
    font_title = get_font(48)

    num_str = f"{index:02d}"
    draw.text((80, 60), num_str, fill=colors["primary"], font=font_big)

    # Line under number
    draw.rectangle([80, 220, 300, 224], fill=colors["accent"])

    # Story title (wrap if too long)
    y = 280
    max_chars = 35
    words = title
    lines = []
    while words:
        lines.append(words[:max_chars])
        words = words[max_chars:]

    for line in lines[:4]:
        draw.text((80, y), line, fill=colors["text"], font=font_title)
        y += 65

    # Decorative elements
    draw.rectangle([RESOLUTION[0] - 100, 0, RESOLUTION[0], RESOLUTION[1]], fill=colors["primary"])

    return img


def create_outro_card(colors: dict) -> Image.Image:
    """Create an outro card."""
    img = Image.new("RGB", RESOLUTION, colors["bg"])
    draw = ImageDraw.Draw(img)

    font = get_font(48)
    text = "感谢收看"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((RESOLUTION[0] - tw) // 2, 400), text, fill=colors["primary"], font=font)

    font_sub = get_font(32)
    sub = "点赞 · 关注 · 下期再见"
    bbox = draw.textbbox((0, 0), sub, font=font_sub)
    sw = bbox[2] - bbox[0]
    draw.text(((RESOLUTION[0] - sw) // 2, 500), sub, fill=colors["text"], font=font_sub)

    return img


def generate_visuals(episode: str) -> Path:
    """Main visual generation function."""
    config = get_pipeline_config()
    ep_dir = get_episode_dir(episode)
    images_dir = BASE_DIR / "assets" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    style = config.get("pipeline", {}).get("steps", {}).get("visuals", {}).get("style", "modern")
    colors = COLOR_SCHEMES.get(style, COLOR_SCHEMES["modern"])

    # Load curated stories
    curated_path = ep_dir / "curated.json"
    stories = []
    if curated_path.exists():
        with open(curated_path, "r", encoding="utf-8") as f:
            stories = json.load(f).get("items", [])

    visuals = []

    # Title card
    title_img = create_title_card(episode, colors)
    title_path = images_dir / f"ep{episode}_title.png"
    title_img.save(title_path)
    visuals.append({"type": "title", "file": str(title_path)})
    logger.info(f"Created title card: {title_path}")

    # Story cards
    for i, story in enumerate(stories, 1):
        card = create_story_card(story.get("title", "Unknown"), i, colors)
        card_path = images_dir / f"ep{episode}_story{i:02d}.png"
        card.save(card_path)
        visuals.append({"type": "story", "index": i, "file": str(card_path)})
        logger.info(f"Created story card {i}: {card_path}")

    # Outro card
    outro = create_outro_card(colors)
    outro_path = images_dir / f"ep{episode}_outro.png"
    outro.save(outro_path)
    visuals.append({"type": "outro", "file": str(outro_path)})
    logger.info(f"Created outro card: {outro_path}")

    # Save manifest
    manifest = {
        "episode": episode,
        "generated_at": datetime.now().isoformat(),
        "style": style,
        "visuals": visuals,
    }
    manifest_path = ep_dir / "visuals_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(f"Generated {len(visuals)} visual assets -> {manifest_path}")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="Step 05: Generate visuals")
    parser.add_argument("--episode", required=True, help="Episode number")
    args = parser.parse_args()

    output = generate_visuals(args.episode)
    print(f"✅ Visual generation complete: {output}")


if __name__ == "__main__":
    main()
