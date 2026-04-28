#!/usr/bin/env python3
"""
前沿理论驱动技术雷达 - 日报生成脚本

基于当天论文和模板生成日报 Markdown。
如果无法调用 LLM，则生成结构化占位版。

输入：papers/YYYY/YYYY-MM-DD-papers.json
输出：daily/YYYY/YYYY-MM-DD.md
"""

import json
import os
import sys
from datetime import date, datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")
DAILY_DIR = os.path.join(PROJECT_ROOT, "daily")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")


def load_papers(target_date):
    """加载论文数据"""
    year = target_date[:4]
    papers_path = os.path.join(PAPERS_DIR, year, f"{target_date}-papers.json")

    if not os.path.exists(papers_path):
        print(f"[generate] 论文文件不存在: {papers_path}")
        return []

    with open(papers_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("papers", [])


def format_paper_table(papers, top_n=5):
    """格式化论文表格"""
    rows = []
    for p in papers[:top_n]:
        title = p.get("title", "未知")
        url = p.get("url", "#")
        source = p.get("source", "未知")
        topics = p.get("matched_topics", ["未分类"])
        topic_str = " / ".join(topics[:2]) if topics else "未分类"
        score = p.get("score", 0)
        decision = p.get("decision", "待定")

        rows.append(
            f"| [{title}]({url}) | {source} | {topic_str} | {score:.1f} | {decision} |"
        )

    return "\n".join(rows)


def format_engineering_rows():
    """格式化工程实践搜索占位行"""
    return (
        "| 待搜索 | GitHub 项目 | 理论验证 | 待确认 | 待评估 |\n"
        "| 待搜索 | 开源框架 | 理论验证 | 待确认 | 待评估 |\n"
        "| 待搜索 | Benchmark | 性能验证 | 待确认 | 待评估 |\n"
        "| 待搜索 | 大厂工程博客 | 生产实践 | 待确认 | 待评估 |\n"
        "| 待搜索 | 社区讨论 | 弱信号 | 待确认 | 待评估 |"
    )


def generate_daily_report(papers, target_date):
    """生成日报"""
    # 选择深挖论文（取评分最高的）
    deep_dive = papers[0] if papers else None

    if deep_dive is None:
        deep_dive = {
            "title": "[占位] 今日无可用论文数据",
            "url": "",
            "source": "placeholder",
            "authors": [],
            "published": target_date,
            "score": 0,
            "decision": "待定",
            "abstract": "今日论文抓取失败或无新论文。",
            "links": []
        }

    # 论文表格
    paper_table = format_paper_table(papers, 5)

    # 工程实践行
    eng_rows = format_engineering_rows()

    # 深挖论文信息
    dd_title = deep_dive.get("title", "")
    dd_url = deep_dive.get("url", "#")
    dd_authors = ", ".join(deep_dive.get("authors", [])[:3]) or "未知"
    dd_source = deep_dive.get("source", "")
    dd_published = deep_dive.get("published", "")
    dd_score = deep_dive.get("score", 0)
    dd_decision = deep_dive.get("decision", "待定")
    dd_abstract = deep_dive.get("abstract", "")[:200]

    # 格式化链接
    links_md = []
    for link in deep_dive.get("links", []):
        if link.get("url"):
            links_md.append(f"- [{link['label']}]({link['url']})")
    if not links_md:
        links_md.append("- 暂未发现可信链接")

    # 引用
    references = "\n".join(links_md)

    # 判断
    if dd_score >= 80:
        final_decision = "重点学习"
    elif dd_score >= 65:
        final_decision = "轻量试点"
    elif dd_score >= 50:
        final_decision = "持续观察"
    else:
        final_decision = "暂时忽略"

    now = datetime.now().isoformat()

    report = f"""# 前沿理论驱动技术雷达日报 - {target_date}

> 研究范式：论文 → 理论 → 工程实践 → 趋势 → 启发 → 行动
> ⚠️ **注意：这是初始化样例，后续运行会替换为真实数据。**

---

## 1. 今日最值得关注的前沿论文

| 论文 | 来源 | 方向 | 分数 | 判断 |
|------|------|------|-----:|------|
{paper_table}

---

## 2. 今日选择深挖的论文

**论文：** [{dd_title}]({dd_url})

**作者 / 机构：** {dd_authors}

**来源：** {dd_source}

**发布时间：** {dd_published}

**评分：** {dd_score}

**摘要：** {dd_abstract}

**选择理由：**
- 是否可能改变工程范式：待分析
- 是否有工程外溢价值：待分析
- 是否能映射到真实系统问题：待分析
- 是否适合架构师学习：待分析
- 是否可能产生工程机会：待分析

---

## 3. 核心理论提取

- **它解决的底层问题是什么？** 待分析（需要 LLM 或人工补充）
- **它挑战了什么旧假设？** 待分析
- **它提出了什么新假设？** 待分析
- **它的核心机制是什么？** 待分析
- **它带来的新能力是什么？** 待分析
- **它的限制条件是什么？** 待分析

---

## 4. 工程演绎推导

| 推导方向 | 可能变化 | 影响程度 | 可信度 | 说明 |
|----------|----------|----------|--------|------|
| 系统架构 | 待分析 | 中 | 待验证 | 需要进一步研究 |
| 开发流程 | 待分析 | 中 | 待验证 | 需要进一步研究 |
| AI Agent 设计 | 待分析 | 高 | 待验证 | 核心影响方向 |
| RAG / 上下文系统 | 待分析 | 中 | 待验证 | 需要进一步研究 |
| 数据流与状态管理 | 待分析 | 中 | 待验证 | 需要进一步研究 |
| 推理成本 | 待分析 | 低 | 待验证 | 需要进一步研究 |
| 部署与运维 | 待分析 | 低 | 待验证 | 需要进一步研究 |
| 评测与治理 | 待分析 | 中 | 待验证 | 需要进一步研究 |
| 团队协作方式 | 待分析 | 低 | 待验证 | 需要进一步研究 |

---

## 5. 沿理论搜索工程实践

| 实践名称 | 类型 | 与论文理论的关系 | 成熟度 | 价值判断 |
|----------|------|-----------------|--------|----------|
| 暂未发现可信链接 | GitHub 项目 | 待搜索 | 待确认 | 待评估 |

> 🔍 需要进一步搜索 GitHub、Papers with Code、工程博客等工程证据。

---

## 6. 工程状态判断

**判断：** C. 理论还没有明显工程实践，但存在潜在机会

**理由：** 初始化阶段，工程实践搜索尚未执行。后续运行将自动搜索并更新。

---

## 7. 潜在工程机会

- **为什么现在还没有成熟实践？** 待分析
- **是因为太新，还是因为难以落地？** 待分析
- **哪些场景最可能先落地？** 待分析
- **对个人或团队来说，能否做一个最小 Demo？** 待分析
- **是否适合沉淀为 Skill、Prompt、架构模板或工具？** 待分析

---

## 8. 启发

### 对系统设计的启发
待分析

### 对 AI Agent 工程化的启发
待分析

### 对团队研发流程的启发
待分析

### 对企业落地的启发
待分析

### 对个人学习路径的启发
待分析

### 对未来 6-12 个月技术趋势的启发
待分析

---

## 9. 行动建议

- **30 分钟学习任务：** 阅读论文摘要，理解核心问题
- **2 小时实践任务：** 搜索相关 GitHub 项目，了解工程实现
- **1 周研究任务：** 深读论文，尝试复现核心实验
- **是否值得精读论文：** 待确认
- **是否值得本地复现：** 待确认
- **是否值得纳入技术雷达：** 待确认
- **是否值得沉淀成 Prompt / Skill / Checklist / 模板：** 待确认

---

## 10. 引用与延伸阅读

{references}

---

## 11. 最终结论

- **结论：** {final_decision}
- **原因：** 初始化样例，基于初步评分规则自动生成
- **最大不确定性：** 核心理论提取和工程实践验证尚未完成
- **下一步动作：** 运行完整流程后更新

---

> 生成时间：{now}
> 数据来源：arXiv API
> 状态：初始化样例
"""

    return report, deep_dive


def save_daily_report(report, target_date):
    """保存日报"""
    year = target_date[:4]
    output_dir = os.path.join(DAILY_DIR, year)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{target_date}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[generate] 日报已保存到: {output_path}")
    return output_path


def main():
    print("=" * 60)
    print("前沿理论驱动技术雷达 - 日报生成")
    print("=" * 60)

    target_date = date.today().isoformat()
    if len(sys.argv) > 1:
        target_date = sys.argv[1]

    print(f"[generate] 目标日期: {target_date}")

    # 加载论文
    papers = load_papers(target_date)
    print(f"[generate] 加载 {len(papers)} 篇论文")

    # 生成日报
    report, deep_dive = generate_daily_report(papers, target_date)

    # 保存
    output_path = save_daily_report(report, target_date)

    # 输出深挖论文信息（供后续脚本使用）
    info = {
        "date": target_date,
        "output_path": output_path,
        "deep_dive": {
            "title": deep_dive.get("title", ""),
            "url": deep_dive.get("url", ""),
            "decision": deep_dive.get("decision", ""),
            "score": deep_dive.get("score", 0)
        }
    }
    print(f"[generate] 深挖论文: {deep_dive.get('title', 'N/A')}")
    print(f"[generate] 完成！日报已保存到: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
