#!/usr/bin/env python3
"""Configuration loader for the AI Weekly Video Pipeline."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_sources_config() -> Dict[str, Any]:
    """Load sources configuration."""
    path = CONFIG_DIR / "sources.yaml"
    if not path.exists():
        path = CONFIG_DIR / "sources.yaml.example"
    return load_yaml(path)


def get_pipeline_config() -> Dict[str, Any]:
    """Load pipeline configuration."""
    path = CONFIG_DIR / "pipeline.yaml"
    if not path.exists():
        path = CONFIG_DIR / "pipeline.yaml.example"
    return load_yaml(path)


def get_platforms_config() -> Dict[str, Any]:
    """Load platforms configuration."""
    path = CONFIG_DIR / "platforms.yaml"
    if not path.exists():
        path = CONFIG_DIR / "platforms.yaml.example"
    return load_yaml(path)


def get_episode_dir(episode: str) -> Path:
    """Get the data directory for a specific episode."""
    ep_dir = BASE_DIR / "data" / "processed" / f"episode_{episode}"
    ep_dir.mkdir(parents=True, exist_ok=True)
    return ep_dir


def get_output_dir() -> Path:
    """Get the output directory, creating it if needed."""
    out_dir = BASE_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir
