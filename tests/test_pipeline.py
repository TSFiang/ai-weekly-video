#!/usr/bin/env python3
"""Tests for AI Weekly Video Pipeline."""

import json
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))
sys.path.insert(0, str(PROJECT_DIR))


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directories
    for d in ["config", "scripts/utils", "templates", "assets/images",
              "assets/audio", "assets/subtitles", "data/raw", "data/processed",
              "output", "logs", "tests"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # Create config files
    sources_config = {
        "sources": {
            "rss": [{"name": "Test RSS", "url": "http://example.com/feed", "enabled": True}],
            "web": [],
            "keywords": ["AI"],
            "exclude_keywords": ["spam"],
        }
    }
    (tmp_path / "config/sources.yaml").write_text(
        "sources:\n  rss:\n    - name: Test RSS\n      url: http://example.com/feed\n      enabled: true\n"
    )

    pipeline_config = {
        "pipeline": {
            "project_name": "AI Weekly",
            "language": "zh-CN",
            "max_stories": 5,
            "steps": {
                "collect": {"enabled": True},
                "curate": {"enabled": True, "min_score": 0.3},
                "script": {"enabled": True},
                "tts": {"enabled": True},
                "visuals": {"enabled": True, "style": "modern"},
                "subtitles": {"enabled": True},
                "compose": {"enabled": True},
                "publish": {"enabled": False},
            },
            "tts": {"engine": "edge-tts", "voice": "zh-CN-XiaoxiaoNeural"},
            "video": {"resolution": "1920x1080", "fps": 30},
            "output": {"format": "mp4", "codec": "libx264"},
        }
    }
    (tmp_path / "config/pipeline.yaml").write_text(
        "pipeline:\n  max_stories: 5\n  steps:\n    curate:\n      min_score: 0.3\n"
        "    visuals:\n      style: modern\n    tts:\n      voice: zh-CN-XiaoxiaoNeural\n"
        "  video:\n    resolution: 1920x1080\n    fps: 30\n  output:\n    codec: libx264\n"
    )

    platforms_config = {"platforms": {"bilibili": {"enabled": False}}}
    (tmp_path / "config/platforms.yaml").write_text(
        "platforms:\n  bilibili:\n    enabled: false\n"
    )

    # Copy scripts
    import shutil
    scripts_src = PROJECT_DIR / "scripts"
    scripts_dst = tmp_path / "scripts"
    for f in scripts_src.glob("*.py"):
        shutil.copy2(f, scripts_dst / f.name)
    for f in (scripts_src / "utils").glob("*.py"):
        shutil.copy2(f, scripts_dst / "utils" / f.name)

    # Copy templates
    for f in (PROJECT_DIR / "templates").glob("*"):
        shutil.copy2(f, tmp_path / "templates" / f.name)

    return tmp_path


# ============ Config Tests ============

class TestConfig:
    def test_load_sources_config(self, temp_project):
        """Test loading sources config."""
        from utils import load_yaml
        config = load_yaml(temp_project / "config/sources.yaml")
        assert "sources" in config
        assert len(config["sources"]["rss"]) >= 1

    def test_load_pipeline_config(self, temp_project):
        """Test loading pipeline config."""
        from utils import load_yaml
        config = load_yaml(temp_project / "config/pipeline.yaml")
        assert "pipeline" in config

    def test_get_episode_dir_creates_dir(self, temp_project):
        """Test episode directory creation."""
        from utils import get_episode_dir
        ep_dir = get_episode_dir("001")
        assert ep_dir.exists()
        assert "episode_001" in str(ep_dir)


# ============ Step 01: Collect Tests ============

class TestCollect:
    def test_filter_keywords(self):
        """Test keyword filtering."""
        from importlib import import_module
        module = import_module("scripts.01_collect")

        items = [
            {"title": "AI breakthrough", "summary": "New model", "url": "1"},
            {"title": "Spam ad", "summary": "Buy now", "url": "2"},
            {"title": "GPT-5 released", "summary": "Amazing", "url": "3"},
        ]
        config = {
            "sources": {},
            "keywords": ["AI", "GPT"],
            "exclude_keywords": ["spam"],
        }

        filtered = module.filter_keywords(items, config)
        assert len(filtered) == 2
        assert all("spam" not in i["title"].lower() for i in filtered)

    def test_collect_rss_handles_error(self):
        """Test RSS collection error handling."""
        from importlib import import_module
        module = import_module("scripts.01_collect")

        source = {"name": "Bad Feed", "url": "http://invalid.example.com/feed"}
        items = module.collect_rss(source)
        assert items == []  # Should not crash

    def test_collect_deduplication(self, temp_project):
        """Test URL deduplication in collect."""
        os.chdir(temp_project)
        from importlib import import_module
        module = import_module("scripts.01_collect")

        # Mock the source config
        mock_config = {
            "sources": {"rss": [], "web": []},
            "keywords": [],
            "exclude_keywords": [],
        }

        with patch.object(module, "get_sources_config", return_value=mock_config):
            result = module.collect("999")
            assert result.exists()


# ============ Step 02: Curate Tests ============

class TestCurate:
    def test_score_item(self):
        """Test item scoring."""
        from importlib import import_module
        module = import_module("scripts.02_curate")

        high_score_item = {"title": "GPT-5 by OpenAI released", "summary": "New AI model", "source": "TechCrunch AI"}
        low_score_item = {"title": "Random news", "summary": "Nothing about AI", "source": "Unknown"}

        high = module.score_item(high_score_item)
        low = module.score_item(low_score_item)

        assert high > low
        assert 0 <= high <= 1.0

    def test_deduplication(self):
        """Test title similarity deduplication."""
        from importlib import import_module
        module = import_module("scripts.02_curate")

        items = [
            {"title": "OpenAI releases GPT-5", "url": "1"},
            {"title": "OpenAI releases GPT-5 model", "url": "2"},  # Very similar
            {"title": "Google announces Gemini", "url": "3"},
        ]

        unique = module.deduplicate_by_similarity(items)
        assert len(unique) == 2

    def test_curate_full(self, temp_project):
        """Test full curation pipeline."""
        os.chdir(temp_project)
        from importlib import import_module
        import scripts.utils as utils_mod
        module = import_module("scripts.02_curate")

        # Create test data at the correct temp path
        ep_dir = temp_project / "data" / "processed" / "episode_001"
        ep_dir.mkdir(parents=True, exist_ok=True)

        test_data = {
            "episode": "001",
            "items": [
                {"title": "GPT-5 released by OpenAI", "summary": "Big AI news", "url": "1", "source": "TechCrunch AI", "priority": "high"},
                {"title": "Google Gemini update", "summary": "AI model", "url": "2", "source": "The Verge AI", "priority": "high"},
                {"title": "Spam ad", "summary": "Buy stuff", "url": "3", "source": "Unknown", "priority": "low"},
            ]
        }
        (ep_dir / "collected.json").write_text(json.dumps(test_data))

        # Patch BASE_DIR and config
        with patch.object(utils_mod, "BASE_DIR", temp_project), \
             patch.object(module, "get_pipeline_config", return_value={
                 "pipeline": {"max_stories": 5, "steps": {"curate": {"min_score": 0.1}}}
             }), \
             patch.object(module, "get_episode_dir", lambda ep: temp_project / "data" / "processed" / f"episode_{ep}"):
            result = module.curate("001")
            assert result.exists()

            with open(result) as f:
                curated = json.load(f)
            assert curated["selected_count"] >= 1


# ============ Step 03: Script Tests ============

class TestScript:
    def test_generate_script_template(self):
        """Test template-based script generation."""
        from importlib import import_module
        module = import_module("scripts.03_script")

        stories = [
            {"title": "AI News 1", "summary": "Something happened", "source": "Test"},
            {"title": "AI News 2", "summary": "Something else", "source": "Test"},
        ]

        script = module.generate_script_template(stories)
        assert "AI News 1" in script
        assert "AI News 2" in script
        assert "AI Weekly" in script

    def test_script_generation_full(self, temp_project):
        """Test full script generation."""
        os.chdir(temp_project)
        from importlib import import_module
        import scripts.utils as utils_mod
        module = import_module("scripts.03_script")

        ep_dir = temp_project / "data" / "processed" / "episode_001"
        ep_dir.mkdir(parents=True, exist_ok=True)

        test_data = {
            "episode": "001",
            "items": [
                {"title": "Test Story", "summary": "Test summary", "source": "Test", "url": "1"},
            ]
        }
        (ep_dir / "curated.json").write_text(json.dumps(test_data))

        with patch.object(module, "get_pipeline_config", return_value={}), \
             patch.object(module, "get_episode_dir", lambda ep: temp_project / "data" / "processed" / f"episode_{ep}"):
            result = module.generate_script("001")
            assert result.exists()
            content = result.read_text()
            assert "Test Story" in content


# ============ Step 04: TTS Tests ============

class TestTTS:
    def test_extract_text_from_script(self):
        """Test text extraction from script."""
        from importlib import import_module
        module = import_module("scripts.04_tts")

        script_content = """# Title
Hello world
---
Some **bold** text here
### Subtitle
More content
"""
        from io import StringIO
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(script_content)
            f.flush()
            segments = module.extract_text_from_script(Path(f.name))

        assert len(segments) > 0
        all_text = " ".join(s["text"] for s in segments)
        assert "Hello world" in all_text
        assert "bold" in all_text


# ============ Step 05: Visuals Tests ============

class TestVisuals:
    def test_create_title_card(self):
        """Test title card generation."""
        from importlib import import_module
        module = import_module("scripts.05_visuals")

        colors = module.COLOR_SCHEMES["modern"]
        img = module.create_title_card("001", colors)
        assert img.size == (1920, 1080)
        assert img.mode == "RGB"

    def test_create_story_card(self):
        """Test story card generation."""
        from importlib import import_module
        module = import_module("scripts.05_visuals")

        colors = module.COLOR_SCHEMES["modern"]
        img = module.create_story_card("Test Title", 1, colors)
        assert img.size == (1920, 1080)

    def test_create_outro_card(self):
        """Test outro card generation."""
        from importlib import import_module
        module = import_module("scripts.05_visuals")

        colors = module.COLOR_SCHEMES["modern"]
        img = module.create_outro_card(colors)
        assert img.size == (1920, 1080)

    def test_color_schemes(self):
        """Test all color schemes."""
        from importlib import import_module
        module = import_module("scripts.05_visuals")

        for scheme_name in ["modern", "minimal", "neon"]:
            colors = module.COLOR_SCHEMES[scheme_name]
            img = module.create_title_card("001", colors)
            assert img.size == (1920, 1080)

    def test_visuals_full(self, temp_project):
        """Test full visual generation."""
        os.chdir(temp_project)
        from importlib import import_module
        import scripts.utils as utils_mod
        module = import_module("scripts.05_visuals")

        ep_dir = temp_project / "data" / "processed" / "episode_001"
        ep_dir.mkdir(parents=True, exist_ok=True)

        test_data = {
            "episode": "001",
            "items": [
                {"title": "Test Story 1", "url": "1"},
                {"title": "Test Story 2", "url": "2"},
            ]
        }
        (ep_dir / "curated.json").write_text(json.dumps(test_data))

        with patch.object(module, "get_pipeline_config", return_value={
                 "pipeline": {"steps": {"visuals": {"style": "modern"}}}
             }), \
             patch.object(module, "get_episode_dir", lambda ep: temp_project / "data" / "processed" / f"episode_{ep}"), \
             patch.object(module, "BASE_DIR", temp_project):
            result = module.generate_visuals("001")
            assert result.exists()

            with open(result) as f:
                manifest = json.load(f)
            assert len(manifest["visuals"]) == 4  # title + 2 stories + outro


# ============ Step 06: Subtitles Tests ============

class TestSubtitles:
    def test_format_timestamp(self):
        """Test SRT timestamp formatting."""
        from importlib import import_module
        module = import_module("scripts.06_subtitles")

        assert module.format_timestamp(0) == "00:00:00,000"
        assert module.format_timestamp(65.5) == "00:01:05,500"
        assert module.format_timestamp(3661.123) == "01:01:01,123"

    def test_estimate_duration(self):
        """Test duration estimation."""
        from importlib import import_module
        module = import_module("scripts.06_subtitles")

        short = module.estimate_duration("短")
        long = module.estimate_duration("这是一段比较长的中文文本内容用来测试")
        assert long > short

    def test_srt_generation(self, temp_project):
        """Test SRT file generation."""
        from importlib import import_module
        module = import_module("scripts.06_subtitles")

        ep_dir = temp_project / "data" / "processed" / "episode_001"
        ep_dir.mkdir(parents=True, exist_ok=True)

        script = "# Test\n\nHello world this is a test.\n\nMore content here.\n"
        (ep_dir / "script.md").write_text(script)

        srt_path = temp_project / "assets" / "subtitles" / "ep001.srt"
        srt_path.parent.mkdir(parents=True, exist_ok=True)

        subs = module.generate_srt_from_script(ep_dir / "script.md", srt_path)
        assert len(subs) > 0
        assert srt_path.exists()

        content = srt_path.read_text()
        assert "-->" in content


# ============ Step 07: Compose Tests ============

class TestCompose:
    def test_build_placeholder_command(self):
        """Test placeholder video command generation."""
        from importlib import import_module
        module = import_module("scripts.07_compose")

        cmd = module.build_placeholder_command("001", Path("/tmp/test.mp4"), {})
        assert "ffmpeg" in cmd
        assert "libx264" in cmd


# ============ Step 08: Publish Tests ============

class TestPublish:
    def test_generate_description(self):
        """Test description generation."""
        from importlib import import_module
        module = import_module("scripts.08_publish")

        stories = [{"title": "Story 1"}, {"title": "Story 2"}]

        bilibili_desc = module.generate_description("001", stories, "bilibili")
        assert "第001期" in bilibili_desc
        assert "Story 1" in bilibili_desc

        youtube_desc = module.generate_description("001", stories, "youtube")
        assert "Episode #001" in youtube_desc


# ============ Pipeline Integration Tests ============

class TestPipeline:
    def test_next_episode_detection(self, temp_project):
        """Test auto-detection of next episode."""
        os.chdir(temp_project)

        # Create existing episodes
        (temp_project / "data" / "processed" / "episode_001").mkdir(parents=True)
        (temp_project / "data" / "processed" / "episode_005").mkdir(parents=True)

        # Patch PROJECT_DIR
        import importlib
        module = importlib.import_module("run_pipeline")
        with patch.object(module, "BASE_DIR", temp_project):
            ep = module.get_next_episode()
            assert ep == "006"

    def test_run_step_unknown(self):
        """Test running unknown step."""
        from run_pipeline import run_step
        result = run_step("nonexistent", "001")
        assert result["status"] == "error"

    def test_config_has_all_steps(self):
        """Verify all pipeline steps are defined."""
        from run_pipeline import PIPELINE_STEPS
        step_names = [s[0] for s in PIPELINE_STEPS]
        assert step_names == ["collect", "curate", "script", "tts", "visuals", "subtitles", "compose", "publish"]


# ============ Utility Tests ============

class TestUtils:
    def test_logger_setup(self):
        """Test logger initialization."""
        from scripts.utils.logger import setup_logger
        logger = setup_logger("test_logger")
        assert logger.name == "test_logger"
        assert len(logger.handlers) >= 1

    def test_load_yaml_nonexistent(self):
        """Test loading non-existent YAML."""
        from utils import load_yaml
        with pytest.raises(FileNotFoundError):
            load_yaml(Path("/nonexistent/file.yaml"))
