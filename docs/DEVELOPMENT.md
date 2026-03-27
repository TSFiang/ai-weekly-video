# 🔧 开发指南

## 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/TSFiang/ai-weekly-video.git
cd ai-weekly-video

# 安装依赖（含开发依赖）
pip install -r requirements.txt

# 运行测试
python3 -m pytest tests/ -v
```

## 流水线架构

### 8 步流水线

```
01_collect → 02_curate → 03_script → 04_tts
                                      ↓
         08_publish ← 07_compose ← 06_subtitles
                                     ↑
                             05_visuals
```

每个步骤是一个独立 Python 脚本，可以：
- 单独运行：`python3 scripts/01_collect.py --episode 001`
- 作为流水线的一部分：`python3 run_pipeline.py`
- 从某步开始：`python3 run_pipeline.py --start-from script`

### 数据流

```
01_collect  →  data/processed/episode_XXX/collected.json
02_curate   →  data/processed/episode_XXX/curated.json
03_script   →  data/processed/episode_XXX/script.md
04_tts      →  assets/audio/epXXX_segNN.mp3
05_visuals  →  assets/images/epXXX_title.png, epXXX_storyNN.png
06_subtitles→  assets/subtitles/epXXX.srt
07_compose  →  output/ai_weekly_epXXX.mp4
08_publish  →  data/processed/episode_XXX/publish_meta.json
```

## 添加新步骤

1. 在 `scripts/` 下创建 `09_xxx.py`
2. 实现函数，接受 `episode: str` 参数，返回 `Path`
3. 在 `run_pipeline.py` 的 `PIPELINE_STEPS` 中注册
4. 在 `config/pipeline.yaml` 中添加配置项
5. 添加对应的单元测试

## 添加新信息源

编辑 `config/sources.yaml`：

```yaml
sources:
  rss:
    - name: "My New Source"
      url: "https://example.com/feed"
      enabled: true
      priority: medium
```

### 自定义抓取逻辑

对于非 RSS/JSON API 的源，在 `scripts/01_collect.py` 中添加新的采集函数：

```python
def collect_custom(source: dict) -> list[dict]:
    """自定义采集逻辑"""
    items = []
    # ... 你的抓取逻辑
    return items
```

然后在 `collect()` 函数中调用它。

## 添加新发布平台

1. 在 `scripts/08_publish.py` 中添加发布函数：

```python
def publish_to_platform(video_path: Path, meta: dict, config: dict) -> dict:
    """发布到新平台"""
    # ... 实现上传逻辑
    return {"platform": "platform_name", "status": "success"}
```

2. 注册到 `PLATFORM_PUBLISHERS` 字典
3. 在 `config/platforms.yaml` 中添加配置

## 画面样式定制

编辑 `scripts/05_visuals.py` 中的 `COLOR_SCHEMES`：

```python
COLOR_SCHEMES = {
    "my_style": {
        "bg": (10, 10, 10),
        "primary": (0, 200, 255),
        "secondary": (255, 100, 50),
        "text": (255, 255, 255),
        "accent": (100, 255, 100),
    },
}
```

然后在 `pipeline.yaml` 中设置 `visuals.style: my_style`。

## 测试

```bash
# 运行全部测试
python3 -m pytest tests/ -v

# 运行单个测试类
python3 -m pytest tests/test_pipeline.py::TestVisuals -v

# 带覆盖率
python3 -m pytest tests/ --cov=scripts --cov-report=term-missing
```

## 代码规范

- Python 3.10+ 类型注解
- 函数文档字符串
- 日志使用 `utils.logger`
- 配置通过 `utils` 模块加载，不要硬编码
