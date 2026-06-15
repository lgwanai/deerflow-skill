# DeerFlow Skill

将 DeerFlow 智能体能力嵌入 Claude Code，无需服务器即可在本地进程内运行深度研究、多步推理、并行子代理等复杂任务。

基于 [deer-flow](https://github.com/bytedance/deer-flow) 内核，持续同步上游更新（last sync: 2026.07.01，同步 130+ 个 commits）。

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

### 配置说明

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

# 子代理配置（可选）
subagents:
  max_concurrent: 3      # 最大并行子代理数
  timeout_seconds: 900   # 子代理超时时间（秒）
```

---

## 功能特性

- **网页搜索**：通过 Tavily 实时搜索互联网
- **内容抓取**：通过 Jina AI 提取网页正文
- **多步推理**：复杂问题的深度思考链路
- **规划模式**：TodoList 结构化的任务分解和追踪
- **子代理委托**：持久化事件循环驱动的并行子任务执行
- **循环检测**：可配置的重复调用检测，支持每种工具单独设定阈值
- **安全终止处理**：Provider 安全过滤时自动抑制截断的 tool_calls（OpenAI/Anthropic/Gemini）
- **MCP 会话池**：有状态 MCP 服务器会话复用，修复跨任务 cancel-scope 错误
- **子代理状态契约**：结构化 subagent_status 字段，替代字符串解析
- **Brave/SearXNG/Browserless**：新增 3 个社区搜索/抓取工具
- **StepFun 模型**：适配 step-3.7-flash/step-3.5-flash 推理模型
- **MiMo 推理支持**：解析小米 MiMo 模型的 reasoning_content
- **Memory JSON 解析**：解析包装的 memory update JSON 响应
- **工具输出预算**：大型工具输出自动截断/持久化，防止上下文爆炸
- **事件循环优化**：Uploads/Memory 扫描异步化，不阻塞主线程
- **Async/Sync 桥接**：`tools/sync.py` 自动为 async 工具生成同步包装器
- **沙箱安全**：路径穿越防护，禁止越权访问文件系统；幂等状态合并
- **输出隔离**：日志到 stderr，AI 内容到 stdout，文件输出零污染

---

## 内置技能 (19 个)

Agent 启动时自动加载 `skills/public/` 下的技能模块，按需调用。

### 多媒体生成
| 技能 | 说明 | 依赖 |
|------|------|------|
| image-generation | AI 图片生成 | MINIMAX_API_KEY |
| video-generation | AI 视频生成 | MINIMAX_API_KEY |
| music-generation | AI 音乐生成 | MINIMAX_API_KEY |
| podcast-generation | AI 播客生成 | MINIMAX_API_KEY |

### 数据分析
| 技能 | 说明 |
|------|------|
| data-analysis | Python 数据分析（需 sandbox） |
| chart-visualization | 24 种图表生成（柱/饼/雷达/桑基/词云...）|
| ppt-generation | PPT 幻灯片生成 |

### 深度研究
| 技能 | 说明 |
|------|------|
| deep-research | 多步深度调研 |
| consulting-analysis | 专业咨询分析报告 |
| github-deep-research | GitHub 仓库深度分析 |
| systematic-literature-review | 学术论文系统综述 + arxiv |
| academic-paper-review | 学术论文审阅 |

### 设计与开发
| 技能 | 说明 |
|------|------|
| frontend-design | 前端 UI 设计 |
| web-design-guidelines | Web 界面设计规范 |
| code-documentation | 代码文档生成 |

### 其他
| 技能 | 说明 |
|------|------|
| bootstrap | 初始化 Agent SOUL |
| newsletter-generation | 新闻简报生成 |
| find-skills | 技能发现与安装 |
| surprise-me | 随机技能推荐 |

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
│   ├── community/        # Tavily, Jina, Brave, SearXNG, Browserless 等
│   ├── subagents/        # 子代理执行器 + Token 收集
│   ├── runtime/          # Checkpointer、运行时、用户上下文
│   ├── models/           # LLM 提供者适配 (DeepSeek, StepFun, MiniMax...)
│   ├── sandbox/          # 本地沙箱（含路径穿越防护）
│   ├── skills/           # Skill 管理 + 存储 + 工具策略
│   └── mcp/              # MCP 协议客户端
├── skills/               # 内置技能定义（19 个）
│   └── public/           # 多媒体生成 / 数据分析 / 深度研究 / 设计
├── lib/                  # 辅助工具
├── tests/                # 测试套件（95 个用例）
└── dist/                 # 打包输出
```

## 打包

```bash
./scripts/package.sh
# 输出: dist/deerflow-skill-YYYYMMDD.zip (~390KB)
```

## 开发

```bash
# 运行测试
python -m pytest tests/ -q

# 测试结果: 95 passed
```

## License

MIT
