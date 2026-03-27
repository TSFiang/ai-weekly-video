# 🎬 AI Weekly Video Pipeline

每周AI资讯视频自动化制作流程。从新闻采集到视频发布，一键完成。

## 架构

```
采集 → 筛选 → 脚本 → 配音 → 画面 → 字幕 → 合成 → 分发
```

## 功能特性

- 📡 **自动采集** — RSS + 网页 API 多源抓取 AI 新闻
- 🎯 **智能筛选** — 关键词打分 + 相似度去重，自动选出最佳选题
- ✍️ **脚本生成** — LLM 自动生成视频脚本，支持模板降级
- 🎙️ **AI 配音** — edge-tts 免费高质量中文语音合成
- 🎨 **画面生成** — Pillow 自动生成 1920×1080 标题卡、故事卡、片尾卡
- 📝 **字幕生成** — whisper 语音识别 / 文本估算两种模式
- 🎬 **视频合成** — ffmpeg 自动拼装为 MP4
- 📤 **多平台发布** — B站、YouTube、抖音一键发布（需配置凭据）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装系统依赖
sudo apt install ffmpeg espeak-ng  # Linux
# brew install ffmpeg espeak-ng    # macOS

# 3. 配置
cp config/pipeline.yaml.example config/pipeline.yaml
# 编辑 config/pipeline.yaml 填入 API keys

# 4. 运行完整流程
python3 run_pipeline.py

# 5. 或分步运行
python3 scripts/01_collect.py --episode 001
python3 scripts/02_curate.py --episode 001
python3 scripts/03_script.py --episode 001
python3 scripts/04_tts.py --episode 001
python3 scripts/05_visuals.py --episode 001
python3 scripts/06_subtitles.py --episode 001
python3 scripts/07_compose.py --episode 001
python3 scripts/08_publish.py --episode 001
```

## 目录结构

```
ai-weekly-video/
├── config/
│   ├── sources.yaml        # 信息源配置
│   ├── pipeline.yaml       # 流水线配置
│   └── platforms.yaml      # 发布平台配置
├── scripts/
│   ├── 01_collect.py       # 信息采集
│   ├── 02_curate.py        # 选题筛选 & 打分
│   ├── 03_script.py        # 脚本生成
│   ├── 04_tts.py           # AI配音
│   ├── 05_visuals.py       # 画面生成
│   ├── 06_subtitles.py     # 字幕生成
│   ├── 07_compose.py       # 视频合成
│   ├── 08_publish.py       # 多平台发布
│   └── utils/              # 工具函数
├── templates/
│   ├── script_template.md  # 脚本模板
│   ├── thumbnail.html      # 缩略图模板
│   └── description.md      # 平台描述模板
├── assets/
│   ├── images/             # 生成的图片素材
│   ├── audio/              # TTS音频
│   ├── video/              # 录屏/素材视频
│   └── subtitles/          # SRT字幕文件
├── data/
│   ├── raw/                # 原始采集数据
│   └── processed/          # 处理后的数据
├── output/                 # 最终视频输出
├── logs/                   # 运行日志
├── tests/                  # 单元测试
├── run_pipeline.py         # 主入口
└── requirements.txt        # Python 依赖
```

## 每周时间线

| 天 | 步骤 | 耗时 | 人工介入 |
|----|------|------|----------|
| 周一 | 自动采集 + 选题 | 自动 | 审核定稿 |
| 周二 | 脚本生成 + 润色 | 30min | 重点修改 |
| 周三 | 配音 + 画面 + 字幕 | 自动 | 检查质量 |
| 周四 | 视频合成 + 审片 | 30min | 最终确认 |
| 周五 | 发布 | 15min | 一键发布 |

## 免费工具栈

| 用途 | 工具 | 说明 |
|------|------|------|
| 配音 | edge-tts | 微软免费TTS，质量高 |
| 画面 | Python + Pillow | 数据可视化、文字卡 |
| 字幕 | faster-whisper | 本地语音识别，零成本 |
| 合成 | ffmpeg | 视频处理 |
| 采集 | feedparser + httpx | RSS + 网页抓取 |
| 脚本 | LLM API | OpenAI / DeepSeek / 本地模型 |

## 测试

```bash
python3 -m pytest tests/ -v
```

## License

MIT
