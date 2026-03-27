# ⚙️ 配置说明

所有配置文件位于 `config/` 目录，使用 YAML 格式。

## sources.yaml — 信息源配置

控制从哪些渠道采集 AI 新闻。

### RSS 源

```yaml
sources:
  rss:
    - name: "TechCrunch AI"        # 源名称
      url: "https://..."            # RSS 地址
      enabled: true                 # 是否启用
      priority: high                # 优先级: high / medium / low
```

### 网页 API 源

```yaml
sources:
  web:
    - name: "Hacker News AI"
      url: "https://hn.algolia.com/api/v1/search?query=AI&tags=story"
      type: "json_api"              # 目前支持 json_api
      enabled: true
      priority: medium
```

### 关键词过滤

```yaml
keywords:           # 标题/摘要包含任一关键词即入选
  - "AI"
  - "GPT"
  - "大模型"

exclude_keywords:   # 包含任一即排除
  - "广告"
  - "sponsor"
```

## pipeline.yaml — 流水线配置

### 全局设置

```yaml
pipeline:
  project_name: "AI Weekly"
  language: "zh-CN"             # 语言
  video_duration_target: 600    # 目标视频时长（秒）
  max_stories: 8                # 每期最多故事数
```

### 步骤控制

```yaml
steps:
  collect:
    enabled: true
    timeout: 300
    max_items_per_source: 50
  curate:
    enabled: true
    min_score: 0.6              # 最低入选分数（0-1）
  script:
    enabled: true
    model: "gpt-4o-mini"
    temperature: 0.7
  tts:
    enabled: true
    voice: "zh-CN-XiaoxiaoNeural"  # edge-tts 语音名
    rate: "+10%"                    # 语速
  visuals:
    enabled: true
    style: "modern"             # modern / minimal / neon
  subtitles:
    enabled: true
    language: "zh"
  compose:
    enabled: true
    resolution: "1920x1080"
    fps: 30
  publish:
    enabled: false              # 默认关闭，需手动开启
```

### LLM 配置

```yaml
llm:
  api_base: "https://api.openai.com/v1"  # OpenAI 兼容 API
  api_key: "${OPENAI_API_KEY}"            # 引用环境变量
  model: "gpt-4o-mini"
```

支持的提供商：
| 提供商 | api_base | model |
|--------|----------|-------|
| OpenAI | `https://api.openai.com/v1` | gpt-4o-mini |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| Ollama | `http://localhost:11434/v1` | llama3 |
| 本地 vLLM | `http://localhost:8000/v1` | 自定义 |

### TTS 语音列表

常用 edge-tts 中文语音：

| 语音名 | 性别 | 风格 |
|--------|------|------|
| zh-CN-XiaoxiaoNeural | 女 | 自然、温暖 |
| zh-CN-YunxiNeural | 男 | 年轻、活力 |
| zh-CN-YunjianNeural | 男 | 成熟、专业 |
| zh-CN-XiaoyiNeural | 女 | 活泼 |
| zh-CN-YunyangNeural | 男 | 新闻播报 |

查看全部语音：
```bash
edge-tts --list-voices | grep zh-CN
```

### 视频合成

```yaml
video:
  resolution: "1920x1080"
  fps: 30
  background_color: "#0a0a0a"
  font: "Noto Sans SC"
  font_size: 24
  transition_duration: 0.5

output:
  format: "mp4"
  codec: "libx264"
  audio_codec: "aac"
  bitrate: "8M"
```

## platforms.yaml — 发布平台配置

### B站

```yaml
bilibili:
  enabled: true
  credentials:
    access_token: "${BILIBILI_ACCESS_TOKEN}"
  upload:
    tid: 188          # 分区 ID（188=科技）
    copyright: 1      # 1=自制
    tags: "AI,人工智能,科技"
```

### YouTube

```yaml
youtube:
  enabled: true
  credentials:
    client_id: "${YOUTUBE_CLIENT_ID}"
    client_secret: "${YOUTUBE_CLIENT_SECRET}"
    refresh_token: "${YOUTUBE_REFRESH_TOKEN}"
  upload:
    category_id: "28"  # Science & Technology
    privacy: "public"
```

### 发布计划

```yaml
schedule:
  day: "friday"   # 发布日
  time: "18:00"   # 发布时间
```
