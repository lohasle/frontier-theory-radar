# Coding Agent

> 当前阶段：主流化 | 最近更新：2026-04-28

---

## 核心问题

如何让 AI Agent 自主完成代码编写、调试、测试、Code Review、PR 提交等软件工程任务，同时保证代码质量、安全性和可维护性。

## 代表论文

- [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770)
- [AgentCoder: Multi-Agent-Based Code Generation](https://arxiv.org/abs/2312.13010)

## 工程实践

| 实践名称 | 类型 | 成熟度 | 价值 |
|----------|------|--------|------|
| [Claude Code](https://www.anthropic.com/claude) | 产品 | 生产可用 | 极高 |
| [Cursor](https://cursor.sh) | 产品 | 生产可用 | 极高 |
| [GitHub Copilot](https://github.com/features/copilot) | 产品 | 生产可用 | 高 |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | 开源框架 | 实验阶段 | 高 |
| [SWE-Agent](https://github.com/princeton-nlp/SWE-agent) | 研究工具 | 实验阶段 | 中 |

## 关键启发

1. **从代码补全到代码 Agent 是质变**
2. **Issue → Context → Patch → Verify → PR 是标准流程**
3. **沙盒执行是安全底线**
4. **PR 风险模拟是下一个竞争点**
5. **人机协作审查是最佳实践**

## 演化时间线

| 时间 | 事件 | 影响 |
|------|------|------|
| 2022 Q4 | GitHub Copilot 发布 | 概念验证 |
| 2023 Q3 | GPT-4 代码能力突破 | 能力突破 |
| 2023 Q4 | SWE-bench 发布 | 评测标准 |
| 2024 Q2 | Cursor 流行 | 产品化 |
| 2024 Q4 | Claude Code 发布 | Agent 突破 |
| 2026 Q1 | Coding Agent 成标配 | 主流化 |

## 相关趋势

- [Agentic World Modeling](./agentic-world-modeling.md) — Coding Agent 是最佳落地场景
- [Context Engineering](./context-engineering.md) — 需要精确的代码上下文

---

> 最近更新：2026-04-28
