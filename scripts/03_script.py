#!/usr/bin/env python3
"""Step 03: 脚本生成 - Generate video script from curated news."""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_episode_dir, get_pipeline_config
from utils.logger import setup_logger

logger = setup_logger("03_script")


# Default script template
DEFAULT_SCRIPT_TEMPLATE = """# AI Weekly 第{episode}期

## 开场白
大家好，欢迎收看 AI Weekly 第{episode}期。我是你们的AI主播。
本周AI领域发生了不少值得关注的事情，让我们一起来看看。

## 新闻播报

{stories}

## 结尾
以上就是本周的AI资讯，如果你觉得有帮助，请点赞关注。
我们下期再见！
"""


# Story template
STORY_TEMPLATE = """### {index}. {title}

**导语**: {lead}

**正文**: {body}

**点评**: {commentary}

---
"""


def generate_script_with_llm(stories: list[dict], config: dict) -> str:
    """Generate script using LLM API. Falls back to template if no API key."""
    import os

    llm_config = config.get("pipeline", {}).get("llm", {})
    api_key = os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        logger.warning("No OPENAI_API_KEY found, using template-based generation")
        return generate_script_template(stories)

    try:
        import httpx

        stories_text = "\n".join(
            f"{i+1}. {s['title']} - {s.get('summary', '')[:200]}"
            for i, s in enumerate(stories)
        )

        prompt = f"""你是一个专业的AI资讯视频脚本撰写者。请根据以下本周AI新闻，撰写一份视频脚本。

新闻列表：
{stories_text}

要求：
1. 用中文撰写
2. 每个故事包含：导语(1-2句)、正文(3-5句)、点评(1句)
3. 语言生动、口语化
4. 总时长约10分钟的内容

请用JSON格式输出，结构为：
{{
  "intro": "开场白",
  "stories": [
    {{
      "title": "标题",
      "lead": "导语",
      "body": "正文",
      "commentary": "点评"
    }}
  ],
  "outro": "结尾"
}}"""

        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{llm_config.get('api_base', 'https://api.openai.com/v1')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": llm_config.get("model", "gpt-4o-mini"),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": llm_config.get("temperature", 0.7),
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        # Try to parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            script_data = json.loads(json_match.group())
            return format_llm_script(script_data, config)

    except Exception as e:
        logger.error(f"LLM script generation failed: {e}")

    return generate_script_template(stories)


def format_llm_script(script_data: dict, config: dict) -> str:
    """Format LLM-generated script data into final script."""
    parts = [f"# AI Weekly Script\n\n{script_data.get('intro', '')}\n"]

    for i, story in enumerate(script_data.get("stories", []), 1):
        parts.append(STORY_TEMPLATE.format(
            index=i,
            title=story.get("title", ""),
            lead=story.get("lead", ""),
            body=story.get("body", ""),
            commentary=story.get("commentary", ""),
        ))

    parts.append(f"\n{script_data.get('outro', '')}")
    return "\n".join(parts)


def generate_script_template(stories: list[dict]) -> str:
    """Generate script from template without LLM."""
    story_parts = []
    for i, story in enumerate(stories, 1):
        story_parts.append(STORY_TEMPLATE.format(
            index=i,
            title=story.get("title", "Untitled"),
            lead=f"本周{story.get('source', 'AI')}报道了一则重要消息。",
            body=story.get("summary", "暂无详细信息。"),
            commentary="这无疑是AI领域的一个重要进展，值得我们持续关注。",
        ))

    return DEFAULT_SCRIPT_TEMPLATE.format(
        episode="{episode}",
        stories="\n".join(story_parts),
    )


def generate_script(episode: str) -> Path:
    """Main script generation function."""
    config = get_pipeline_config()
    ep_dir = get_episode_dir(episode)

    # Load curated items
    curated_path = ep_dir / "curated.json"
    if not curated_path.exists():
        raise FileNotFoundError(f"No curated data found: {curated_path}")

    with open(curated_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stories = data["items"]
    logger.info(f"Generating script for {len(stories)} stories")

    # Generate script
    script = generate_script_with_llm(stories, config)
    script = script.replace("{episode}", episode)

    # Save script
    script_path = ep_dir / "script.md"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    # Also save as structured JSON for downstream
    script_data = {
        "episode": episode,
        "generated_at": datetime.now().isoformat(),
        "stories_count": len(stories),
        "script_path": str(script_path),
        "word_count": len(script),
    }
    meta_path = ep_dir / "script_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Script saved: {script_path} ({len(script)} chars)")
    return script_path


def main():
    parser = argparse.ArgumentParser(description="Step 03: Generate script")
    parser.add_argument("--episode", required=True, help="Episode number")
    args = parser.parse_args()

    output = generate_script(args.episode)
    print(f"✅ Script generation complete: {output}")


if __name__ == "__main__":
    main()
