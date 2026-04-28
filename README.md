# 📡 前沿理论驱动技术雷达日报

> 论文 → 理论 → 工程实践 → 趋势 → 启发 → 行动

**从前沿论文出发，提取理论假设，沿理论搜索工程实践，判断趋势阶段，蒸馏启发，最终形成可执行的行动建议和可复用的技术判断系统。**

[![Deploy Pages](https://github.com/lohasle/frontier-theory-radar/actions/workflows/pages.yml/badge.svg)](https://github.com/lohasle/frontier-theory-radar/actions/workflows/pages.yml)

---

## 研究范式

这不是普通技术新闻聚合器，也不是 GitHub Trending 搬运器。

```
论文 → 理论 → 工程实践 → 趋势 → 启发 → 行动
```

1. **论文**：从最新高价值论文中发现理论源头
2. **理论**：提取论文中的新假设、新方法、新范式
3. **工程实践**：沿理论搜索 GitHub 项目、Benchmark、大厂工程博客
4. **趋势**：判断理论处于萌芽、上升、主流化、过热还是噪声阶段
5. **启发**：蒸馏出对系统设计、AI Agent、研发流程的启发
6. **行动**：给出明确的 30 分钟学习任务、2 小时实践任务、1 周研究任务

## 固定数据源

### 理论源头

| 数据源 | 用途 | 状态 |
|--------|------|------|
| [arXiv](https://arxiv.org) | 理论发现（主源） | ✅ 已接入 |
| [OpenReview](https://openreview.net) | 会议论文跟踪 | ⏳ 待接入 |
| [Hugging Face Daily Papers](https://huggingface.co/papers) | 社区关注度辅助 | ⏳ 待接入 |
| [Papers with Code](https://paperswithcode.com) | 代码/Benchmark 验证 | ⏳ 待接入 |

### 工程验证源

| 数据源 | 用途 | 状态 |
|--------|------|------|
| GitHub Search | 工程实践验证 | ⏳ 待接入 |
| GitHub Trending | 社区热度参考 | ⏳ 待接入 |
| 大厂 Engineering Blog | 生产实践验证 | ⏳ 待接入 |
| CNCF / InfoQ / Thoughtworks | 技术趋势参考 | ⏳ 待接入 |
| Hacker News / Reddit / X | 弱信号和反证 | ⏳ 待接入 |

### 数据源使用规则

- arXiv / OpenReview 负责理论源头
- Hugging Face 负责辅助排序
- Papers with Code / GitHub 负责工程证据
- 工程博客负责生产实践验证
- 社区讨论只作为弱信号和反证，不作为主判断依据
- **不允许用单一来源直接下结论**
- 如果数据不足，必须明确写"不确定"或"待验证"

## 每日流程

```bash
./run_daily.sh [YYYY-MM-DD]
```

一键运行完整流程：

1. 拉取最新代码
2. 从 arXiv 抓取论文元数据
3. 基于规则评分排序
4. 选择深挖论文，生成结构化日报
5. 更新索引（README、趋势、启发、JSON）
6. 构建 GitHub Pages 数据
7. git commit & push

## 目录结构

```
frontier-theory-radar/
├── README.md                    # 项目说明
├── config/
│   ├── sources.yml              # 固定数据源配置
│   ├── topics.yml               # 重点研究方向
│   └── scoring.yml              # 评分模型配置
├── daily/
│   └── 2026/
│       └── 2026-04-28.md        # 每日日报
├── papers/
│   └── 2026/
│       └── 2026-04-28-papers.json  # 论文元数据
├── trends/
│   ├── index.md                 # 趋势索引
│   ├── agentic-world-modeling.md
│   ├── context-engineering.md
│   └── coding-agent.md
├── insights/
│   ├── index.md                 # 启发索引
│   ├── patterns.md              # 系统设计模式
│   ├── learning-decisions.md    # 学习决策记录
│   └── engineering-opportunities.md  # 工程机会
├── prompts/
│   ├── daily-radar-prompt.md    # 日报生成提示词
│   ├── paper-analysis-prompt.md # 论文分析提示词
│   └── engineering-validation-prompt.md  # 工程验证提示词
├── templates/
│   ├── daily-template.md        # 日报模板
│   ├── paper-card-template.md   # 论文卡片模板
│   └── trend-template.md        # 趋势模板
├── scripts/
│   ├── fetch_papers.py          # 论文抓取
│   ├── score_papers.py          # 论文评分
│   ├── generate_daily.py        # 日报生成
│   ├── update_index.py          # 索引更新
│   └── build_pages.py           # Pages 数据构建
├── docs/                        # GitHub Pages
│   ├── index.html               # 首页
│   ├── daily.html               # 日报列表
│   ├── papers.html              # 论文库
│   ├── trends.html              # 趋势雷达
│   ├── insights.html            # 启发
│   ├── sources.html             # 数据源
│   ├── about.html               # 关于
│   ├── assets/
│   │   ├── style.css            # 样式
│   │   └── app.js               # 交互逻辑
│   └── data/
│       ├── latest.json          # 最新数据汇总
│       ├── daily-index.json     # 日报索引
│       ├── paper-index.json     # 论文索引
│       ├── trend-index.json     # 趋势索引
│       ├── insight-index.json   # 启发索引
│       └── source-index.json    # 数据源索引
├── .github/
│   └── workflows/
│       └── pages.yml            # GitHub Actions
└── run_daily.sh                 # 一键运行脚本
```

## 本地运行

### 前置条件

- Python 3.8+
- Git

### 运行方式

```bash
# 克隆仓库
git clone https://github.com/lohasle/frontier-theory-radar.git
cd frontier-theory-radar

# 一键运行
./run_daily.sh

# 或分步运行
python3 scripts/fetch_papers.py
python3 scripts/score_papers.py
python3 scripts/generate_daily.py
python3 scripts/update_index.py
python3 scripts/build_pages.py
```

### Hermes 推理增强（无自建 LLM API）

项目支持由 Hermes 任务直接产出推理结果并回填：

- `papers/YYYY/YYYY-MM-DD-llm-scores.json`：覆盖/增强评分（score + reason）
- `papers/YYYY/YYYY-MM-DD-analysis.json`：填充“核心理论提取 / 启发 / 行动建议”

`scripts/score_papers.py` 和 `scripts/generate_daily.py` 会自动读取这两个文件（若存在）。

已创建 Hermes 定时任务：`frontier-theory-radar-daily`（every 24h）。

### 本地预览 GitHub Pages

```bash
# 使用 Python 内置 HTTP 服务器
cd docs
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

## GitHub Pages 访问

### 配置方法

1. 进入仓库 Settings → Pages
2. Source 选择 **GitHub Actions**
3. Push 到 main 分支后自动发布

### 访问地址

```
https://lohasle.github.io/frontier-theory-radar/
```

## 重点研究方向

1. AI Agent / Agentic Workflow
2. Coding Agent / 软件工程自动化
3. Context Engineering / Memory / Skill Learning
4. RAG / Long Context / Knowledge System
5. Multimodal Agent / World Model
6. LLM Evaluation / Benchmark / Auto-Eval
7. Inference / Serving / AI Infra
8. AI on Kubernetes / Platform Engineering
9. Data Engineering / CDC / Lakehouse / Real-time System
10. Security / Reliability / AI Governance

## 如何新增研究方向

1. 编辑 `config/topics.yml`，添加新的 topic 条目
2. 在 `trends/` 下创建对应的趋势页面
3. 更新 `scripts/score_papers.py` 中的关键词映射
4. 运行 `./run_daily.sh` 验证

## 如何调整评分模型

1. 编辑 `config/scoring.yml`，调整权重和阈值
2. 修改 `scripts/score_papers.py` 中的 `compute_score()` 函数
3. 运行 `python3 scripts/score_papers.py` 重新评分

## 评分体系

### 判断标准

| 分数 | 判断 | 说明 |
|------|------|------|
| 80+ | 🟢 重点学习 | 值得精读论文、本地复现、纳入技术雷达 |
| 65-79 | 🔵 轻量试点 | 值得花 2 小时了解和实践 |
| 50-64 | 🟡 持续观察 | 保持关注，等待更多证据 |
| <50 | ⚪ 暂时忽略 | 当前不值得投入时间 |

### 评分维度

- **理论新意** (15%) — 新假设、新方法、新范式
- **问题重要性** (15%) — 是否解决核心问题
- **工程影响力** (15%) — 对系统架构的潜在影响
- **工程外溢价值** (10%) — 能否映射到真实系统
- **证据强度** (10%) — 实验、代码、复现
- **来源质量** (5%) — 来源可信度
- **可复现性** (10%) — 代码和数据集
- **架构师相关性** (10%) — 与主线方向相关
- **长期复利** (10%) — 6-12 月后仍有价值

负向评分：炒作风险、证据不足惩罚、弱相关惩罚

## 质量标准

- ✅ 每天生成一篇日报，不允许空白
- ✅ 论文标题必须是可点击超链接
- ✅ 所有链接真实可访问，不编造
- ✅ 不确定的内容标注"待验证"
- ✅ 不提交密钥、cookie、token
- ✅ 抓取失败时生成失败说明和占位内容

## 最近日报

| 日期 | 深挖论文 | 结论 | 方向 |
|------|----------|------|------|
| 2026-04-28 | [Agentic World Modeling](https://arxiv.org/abs/2604.22748) | 🟢 重点学习 | AI Agent / World Model |

> ⚠️ 以上为初始化样例数据。

## 当前重点趋势

| 趋势 | 阶段 | 说明 |
|------|------|------|
| [Agentic World Modeling](trends/agentic-world-modeling.md) | 📈 上升 | Agent 从工具调用到预测-规划-执行 |
| [Context Engineering](trends/context-engineering.md) | 📈 上升 | 上下文管理是 Agent 的基础能力 |
| [Coding Agent](trends/coding-agent.md) | ✅ 主流化 | AI 编程助手已成为标配工具 |

## 启发沉淀

- [系统设计模式](insights/patterns.md) — 从论文中蒸馏的架构模式
- [学习决策记录](insights/learning-decisions.md) — 对技术方向的学习决策
- [工程机会](insights/engineering-opportunities.md) — 从理论中发现的实践机会

## License

MIT

---

> 本项目的核心不是追热点，而是从前沿论文出发，提取理论假设，沿理论搜索工程实践，判断趋势阶段，蒸馏启发，最终形成可执行的行动建议和可复用的技术判断系统。
