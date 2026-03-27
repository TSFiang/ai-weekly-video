# 📋 更新日志

所有重要的项目变更都会记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-03-27

### Added
- 完整的 8 步视频制作流水线
  - `01_collect` — RSS + 网页 API 多源新闻采集
  - `02_curate` — 关键词打分 + 相似度去重筛选
  - `03_script` — LLM 脚本生成（支持模板降级）
  - `04_tts` — edge-tts 配音（支持 espeak-ng 降级）
  - `05_visuals` — Pillow 自动生成 1920×1080 画面卡
  - `06_subtitles` — SRT 字幕生成（whisper + 文本估算）
  - `07_compose` — ffmpeg 视频合成
  - `08_publish` — 多平台发布框架（B站/YouTube/抖音）
- 三种画面风格：modern / minimal / neon
- YAML 配置系统（sources / pipeline / platforms）
- 日志系统（控制台 + 文件）
- 27 个单元测试，全部通过
- 命令行入口 `run_pipeline.py`
  - `--episode` 指定期数
  - `--step` 运行单步
  - `--start-from` 从某步开始
- 示例数据（Episode 001）
- 完整文档（README / INSTALL / CONFIG / DEVELOPMENT）

### Dependencies
- PyYAML >= 6.0
- httpx >= 0.25.0
- feedparser >= 6.0
- Pillow >= 10.0
- edge-tts >= 6.1.0
- pytest >= 7.0

### System Requirements
- Python 3.10+
- ffmpeg 4.0+
- 中文字体（Noto Sans CJK / PingFang）
