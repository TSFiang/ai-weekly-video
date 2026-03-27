# 🤝 贡献指南

感谢你对 AI Weekly Video Pipeline 的关注！

## 如何贡献

### 报告问题

1. 在 GitHub Issues 中搜索是否已有相同问题
2. 创建新 Issue，包含：
   - 问题描述
   - 复现步骤
   - 环境信息（OS、Python 版本）
   - 错误日志

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 编写代码 + 测试
4. 确保测试通过：`python3 -m pytest tests/ -v`
5. 提交：`git commit -m "feat: 描述你的改动"`
6. 推送：`git push origin feature/your-feature`
7. 创建 Pull Request

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

| 前缀 | 用途 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | Bug 修复 |
| `docs:` | 文档更新 |
| `style:` | 代码格式（不影响逻辑） |
| `refactor:` | 重构 |
| `test:` | 测试相关 |
| `chore:` | 构建/工具变更 |

### 代码规范

- Python 3.10+，使用类型注解
- 函数必须有 docstring
- 使用项目 logger，不要 `print()`
- 配置从 YAML 读取，不要硬编码
- 新功能必须附带测试

### 测试要求

```bash
# 所有测试必须通过
python3 -m pytest tests/ -v

# 建议覆盖率
python3 -m pytest tests/ --cov=scripts --cov-report=term-missing
```

### 添加新的信息源

1. 在 `config/sources.yaml` 中添加源配置
2. 如需新采集逻辑，在 `scripts/01_collect.py` 中实现
3. 添加对应的单元测试

### 添加新的发布平台

1. 在 `scripts/08_publish.py` 中实现发布函数
2. 在 `config/platforms.yaml` 中添加配置模板
3. 在 `PLATFORM_PUBLISHERS` 中注册
4. 添加测试

## 开发者

项目由社区共同维护。感谢所有贡献者！
