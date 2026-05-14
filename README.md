# DeerFlow Skill

将 DeerFlow 智能体能力嵌入 Claude Code，无需服务器即可在本地进程内运行深度研究、多步推理、并行子代理等复杂任务。

基于 [deer-flow](https://github.com/bytedance/deer-flow) 内核，持续同步上游更新（last sync: 2026.05）。

---

## 能解决什么问题

当你需要 AI 完成「一次对话搞不定」的任务时，这个 Skill 提供企业级 AI Agent 能力：

| 场景 | 典型问题 | 对应模式 |
|------|---------|----------|
| **快速问答** | "Python 和 Go 的区别？" | `--flash` |
| **深度调研** | "调研 2026 年 AI 最新进展，并给出分析" | `--standard` |
| **复杂规划** | "制定一个月的 Python 学习计划" | `--pro` |
| **大规模分析** | "对比特斯拉和比亚迪的技术路线、市场策略、未来发展" | `--ultra` |
| **研究报告** | "研究 XX 行业趋势，输出 Markdown 报告" | `--flash` + 管道 |

**核心能力**：自主搜索网页 → 阅读文章 → 多步推理 → 并行分发子任务 → 生成引用报告

---

## 使用方法

### 在 Claude Code 中激活

```
/deer 研究量子计算的最新进展
/deer --flash 今天北京的天气
/deer --pro 制定一个 REST API 项目计划
/deer --ultra 对比三家竞品公司的技术栈
```

### 命令行使用

```bash
# 快速问答
./scripts/chat.sh --flash "Python 的 GIL 是什么"

# 深度调研
./scripts/chat.sh --pro "分析 2026 年 AI 行业趋势"

# 并行分析
./scripts/chat.sh --ultra "对比国内外新能源汽车技术路线"

# 生成报告文件（日志在终端，AI 内容进文件）
./scripts/chat.sh --flash "调研特斯拉和比亚迪" > tesla_vs_byd.md
```

### 模式说明

| 模式 | 思考 | 规划 | 子代理 | 适用场景 |
|------|------|------|--------|----------|
| `--flash` | ✗ | ✗ | ✗ | 一句话能说清的问题 |
| `--standard` | ✓ | ✗ | ✗ | 默认模式，平衡速度和质量 |
| `--pro` | ✓ | ✓ | ✗ | 需要结构化规划的复杂任务 |
| `--ultra` | ✓ | ✓ | ✓ | 大规模任务，并行分发子代理 |

---

## 快速开始

```bash
# 1. 复制配置模板
cp config.example.yaml config.yaml

# 2. 编辑 config.yaml，填入 API Keys

# 3. 安装依赖
pip install langchain langchain-anthropic langchain-openai tavily-python httpx pyyaml

# 4. 运行
./scripts/chat.sh --flash "你的第一个问题"
```

### 所需 API Keys

| Key | 用途 | 获取地址 |
|-----|------|----------|
| `DEEPSEEK_API_KEY` | 模型推理 | https://platform.deepseek.com |
| `TAVILY_API_KEY` | 网页搜索 | https://tavily.com |
| `JINA_API_KEY` | 网页内容抓取 | https://jina.ai/reader |

### 配置示例

```yaml
models:
  - name: deepseek-v4-flash
    use: langchain_anthropic:ChatAnthropic
    model: deepseek-v4-flash
    api_key: $DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/anthropic

tools:
  - name: web_search
    use: deerflow.community.tavily.tools:web_search_tool
    api_key: $TAVILY_API_KEY

  - name: web_fetch
    use: deerflow.community.jina_ai.tools:web_fetch_tool
    api_key: $JINA_API_KEY
```

---

## 功能特性

- **网页搜索**：通过 Tavily 实时搜索互联网
- **内容抓取**：通过 Jina AI 提取网页正文
- **多步推理**：复杂问题的深度思考链路
- **规划模式**：TodoList 结构化的任务分解和追踪
- **子代理委托**：持久化事件循环驱动的并行子任务执行
- **循环检测**：可配置的重复调用检测，支持每种工具单独设定阈值
- **Async/Sync 桥接**：`tools/sync.py` 自动为 async 工具生成同步包装器
- **Token 追踪**：子代理 Token 用量收集和汇总

---

## 项目结构

```
deerflow-skill/
├── SKILL.md              # Skill 定义
├── config.yaml           # 配置文件（gitignored）
├── config.example.yaml   # 配置模板
├── scripts/
│   ├── skill.py          # 主入口
│   ├── chat.sh           # Shell 包装
│   └── package.sh        # 打包脚本
├── deerflow/             # 嵌入的 deer-flow 核心
│   ├── client.py         # DeerFlowClient API
│   ├── agents/           # Agent 编排 + 中间件
│   ├── tools/            # 工具定义 + sync 包装器
│   ├── config/           # 20+ 配置模型
│   ├── community/        # Tavily, Jina, Firecrawl 等
│   ├── subagents/        # 子代理执行器 + Token 收集
│   ├── runtime/          # Checkpointer、运行时、用户上下文
│   └── ...
├── lib/                  # 辅助工具
├── tests/                # 测试套件
└── dist/                 # 打包输出
```

## 打包

```bash
./scripts/package.sh
# 输出: dist/deerflow-skill-YYYYMMDD.zip (~390KB)
```

## License

MIT
