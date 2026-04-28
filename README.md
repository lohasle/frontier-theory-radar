# 前沿理论驱动技术雷达日报

> 面向资深架构师与 AI 研究员的论文价值发现系统。

**核心目标：从论文出发，快速判断即时价值、趋势价值和长尾价值，沉淀可复用研究资产。**

## 项目定位

这个项目不是普通论文摘要站，也不是热点搬运器。
它关注的是：在海量论文中，哪些值得今天就读、哪些值得纳入趋势观察、哪些值得作为长尾资产保存、哪些应该明确忽略。

## 价值类型说明

- **即时价值（immediate）**：今天就值得读、值得试、值得转成 Prompt / Skill / Checklist / 最小实验。
- **趋势价值（trend）**：需要与多篇论文、开源项目、Benchmark、工程实践共同观察 7-30 天。
- **长尾价值（long_tail）**：现在不火，但提出了好问题、好评测、好反证、好抽象，值得保存。
- **暂时忽略（ignore）**：新意弱、证据弱、相关性弱、难迁移或缺少资产价值。

## 常见研究路径（不是强制模板）

项目仍保留“论文 → 理论 → 工程实践 → 趋势 → 启发 → 行动”作为**常见研究路径**，但不再把它作为所有论文的强制结构。
真实流程先做**价值路由**，再决定是否进入更深研究链路。

## 页面说明

- **首页**：论文价值发现工作台
- **日报**：每日候选论文、价值分布、今日重点与长尾保存
- **日报详情页**：某天的完整价值判断报告
- **论文库**：所有被筛选、评分、判断过的论文
- **论文详情页**：长期论文研究档案
- **趋势雷达**：只收纳确实有趋势价值的方向
- **长尾库**：保存现在不火但未来可能有价值的论文
- **启发**：Prompt / Skill / Checklist / 架构模式 / 评测方法 / 工程机会
- **数据源**：固定数据源与接入状态
- **关于**：方法论与使用说明

## 数据结构说明

- `docs/data/latest.json`：首页汇总、今日重点、价值分布
- `docs/data/daily-index.json`：日报列表
- `docs/data/paper-index.json`：论文库索引
- `docs/data/trend-index.json`：趋势雷达索引
- `docs/data/insight-index.json`：启发索引
- `docs/data/long-tail-index.json`：长尾库索引
- `docs/data/daily-details/<date>.json`：单日详细价值报告
- `docs/data/paper-details/<paper-id>.json`：单篇论文研究档案

## Mermaid 图表说明

GitHub Pages 使用固定 Mermaid 模板展示：
- 论文价值发现图
- 研究证据图
- 行动路由图

目标是稳定、可读、可复用，不追求每天自由生成复杂图。

## 固定数据源

- 理论源头：arXiv、OpenReview、Hugging Face Daily Papers、Papers with Code
- 工程验证源：GitHub Search / Trending、大厂 Engineering Blog、CNCF / InfoQ / Thoughtworks Radar、Hacker News / Reddit / X

## 本地运行

```bash
./run_daily.sh [YYYY-MM-DD]
# 或分步运行
python3 scripts/fetch_papers.py
python3 scripts/score_papers.py 2026-04-28
python3 scripts/generate_daily.py 2026-04-28
python3 scripts/update_index.py 2026-04-28
python3 scripts/build_pages.py
```

## GitHub Pages

- 仓库设置：Settings → Pages → Source 选择 **GitHub Actions**
- 页面地址：`https://lohasle.github.io/frontier-theory-radar/index.html`

## 最近 7 篇日报索引

- [2026-04-29 · Long-Context Aware Upcycling: A New Frontier for Hybrid LLM Scaling](daily-detail.html?date=2026-04-29) · 即时价值 · 重点学习
- [2026-04-28 · Long-Context Aware Upcycling: A New Frontier for Hybrid LLM Scaling](daily-detail.html?date=2026-04-28) · 即时价值 · 重点学习

## 当前重点趋势索引

- [Agentic World Modeling](trend-detail.html?id=agentic-world-modeling) · 上升 · 关联论文 3
- [Coding Agent](trend-detail.html?id=coding-agent) · 主流化 · 关联论文 6
- [Context Engineering](trend-detail.html?id=context-engineering) · 上升 · 关联论文 3

## 启发沉淀说明

启发页用于沉淀跨论文可复用资产，包括：
- Prompt 模板
- Skill 草案
- Checklist
- 架构模式
- 评测方法
- 学习与复盘决策
