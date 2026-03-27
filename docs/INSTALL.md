# 📦 安装指南

## 系统要求

- Python 3.10+
- ffmpeg 4.0+
- 操作系统：Linux / macOS / Windows (WSL)

## 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 依赖说明

| 包 | 用途 | 必需 |
|----|------|------|
| PyYAML | 配置文件解析 | ✅ |
| httpx | HTTP 请求 | ✅ |
| feedparser | RSS 解析 | ✅ |
| Pillow | 图片生成 | ✅ |
| edge-tts | 语音合成 | ✅ |
| faster-whisper | 语音识别（字幕） | 可选 |
| pytest | 测试 | 开发 |

## 2. 安装系统依赖

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install ffmpeg espeak-ng fonts-noto-cjk
```

### macOS

```bash
brew install ffmpeg espeak-ng
# 中文字体 macOS 自带 PingFang
```

### Windows (WSL)

```bash
sudo apt update
sudo apt install ffmpeg espeak-ng fonts-noto-cjk
```

### 字体

需要支持中文的字体才能正确渲染画面卡：

- Linux: `fonts-noto-cjk`（推荐 Noto Sans CJK）
- macOS: 系统自带 PingFang
- Windows: 微软雅黑

## 3. 配置 API Keys（可选）

### LLM 脚本生成

```bash
export OPENAI_API_KEY="sk-xxx"
# 或 DeepSeek
export OPENAI_API_KEY="sk-xxx"  # 同时修改 pipeline.yaml 中的 api_base
```

### B站发布

在 `config/platforms.yaml` 中填入 B站 access token。

### YouTube 发布

在 `config/platforms.yaml` 中填入 OAuth 凭据。

## 4. 验证安装

```bash
# 运行测试
python3 -m pytest tests/ -v

# 运行单步测试
python3 run_pipeline.py --step collect --episode 001
```

## 常见问题

### Q: ffmpeg 找不到

```bash
# 检查是否安装
ffmpeg -version

# 如果没有，安装它
sudo apt install ffmpeg  # Linux
brew install ffmpeg       # macOS
```

### Q: 中文显示乱码

安装中文字体：
```bash
sudo apt install fonts-noto-cjk  # Ubuntu/Debian
```

### Q: edge-tts 安装失败

```bash
pip install --upgrade edge-tts
# 或用 espeak-ng 作为降级方案
```

### Q: 更换 LLM 提供商

编辑 `config/pipeline.yaml`：

```yaml
llm:
  api_base: "https://api.deepseek.com/v1"  # DeepSeek
  # api_base: "http://localhost:11434/v1"  # Ollama 本地模型
  model: "deepseek-chat"
```
