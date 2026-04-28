#!/usr/bin/env python3
"""
前沿理论驱动技术雷达 - 索引更新脚本

更新：
- docs/data/*.json
- trends/index.md
- insights/index.md

保证首页能展示最新日报。
"""

import json
import os
import sys
import glob
from datetime import date, datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY_DIR = os.path.join(PROJECT_ROOT, "daily")
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")
TRENDS_DIR = os.path.join(PROJECT_ROOT, "trends")
INSIGHTS_DIR = os.path.join(PROJECT_ROOT, "insights")
DOCS_DATA_DIR = os.path.join(PROJECT_ROOT, "docs", "data")
GITHUB_BLOB_BASE = "https://github.com/lohasle/frontier-theory-radar/blob/main"


def load_daily_reports(max_count=30):
    """加载最近的日报列表"""
    reports = []

    # 搜索所有日报文件
    pattern = os.path.join(DAILY_DIR, "*", "*.md")
    files = sorted(glob.glob(pattern), reverse=True)

    for filepath in files[:max_count]:
        filename = os.path.basename(filepath)
        date_str = filename.replace(".md", "")

        # 从 Markdown 中提取基本信息
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取深挖论文标题
        deep_dive_title = ""
        deep_dive_url = ""
        for line in content.split("\n"):
            if line.startswith("**论文：**") or line.startswith("**论文:**"):
                # 提取 markdown 链接
                import re
                match = re.search(r"\[(.*?)\]\((.*?)\)", line)
                if match:
                    deep_dive_title = match.group(1)
                    deep_dive_url = match.group(2)
                else:
                    deep_dive_title = line.split("**", 2)[-1].strip()
                break

        # 提取结论
        decision = ""
        for line in content.split("\n"):
            if "**结论：**" in line or "**结论:**" in line:
                decision = line.split("**")[-1].strip()
                break

        # 提取方向
        topics = ""
        for line in content.split("\n"):
            if "方向" in line and "|" in line and "未知" not in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) > 3 and parts[2]:
                    topics = parts[2]
                    break

        # 提取一句话启发
        inspiration = ""
        for line in content.split("\n"):
            if "启发" in line.lower() and len(line.strip()) > 10:
                inspiration = line.strip()[:100]
                break

        reports.append({
            "date": date_str,
            "deep_dive_title": deep_dive_title or "待分析",
            "deep_dive_url": deep_dive_url,
            "decision": decision or "待定",
            "topics": topics or "综合",
            "inspiration": inspiration or "待分析",
            "path": f"{GITHUB_BLOB_BASE}/daily/{date_str[:4]}/{date_str}.md"
        })

    return reports


def make_cn_brief(title, topics, abstract=""):
    """生成中文一句话概述"""
    topic_map = {
        "ai-agent": "AI Agent",
        "coding-agent": "Coding Agent",
        "context-engineering": "上下文工程",
        "rag-knowledge": "RAG/知识系统",
        "multimodal-agent": "多模态 Agent",
        "llm-evaluation": "LLM 评测",
        "inference-serving": "推理与服务",
        "ai-k8s-platform": "AI 平台工程",
        "data-engineering": "数据工程",
        "security-governance": "安全与治理",
    }
    t = topics[0] if isinstance(topics, list) and topics else ""
    domain = topic_map.get(t, "前沿研究")
    if abstract:
        brief = " ".join(abstract.strip().split())
        return f"{domain}：{brief[:80]}{'…' if len(brief) > 80 else ''}"
    return f"{domain}：该论文提出新方法，建议结合工程证据进一步验证。"


def load_paper_index():
    """加载论文索引"""
    papers = []

    pattern = os.path.join(PAPERS_DIR, "*", "*.json")
    files = sorted(glob.glob(pattern), reverse=True)

    seen_titles = set()

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for p in data.get("papers", []):
            title_key = p.get("title", "")[:80]
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                papers.append({
                    "title": p.get("title", ""),
                    "url": p.get("url", ""),
                    "source": p.get("source", ""),
                    "published": p.get("published", ""),
                    "score": p.get("score", 0),
                    "decision": p.get("decision", ""),
                    "has_code": bool(p.get("code_url")),
                    "has_benchmark": bool(p.get("benchmark_url")),
                    "topics": p.get("matched_topics", []),
                    "tags": p.get("keywords", [])[:5],
                    "brief_cn": make_cn_brief(
                        p.get("title", ""),
                        p.get("matched_topics", []),
                        p.get("abstract", "")
                    ),
                    "links": p.get("links", []),
                    "pdf_url": p.get("pdf_url", ""),
                    "openreview_url": p.get("openreview_url", ""),
                    "paperswithcode_url": p.get("paperswithcode_url", ""),
                    "code_url": p.get("code_url", ""),
                    "benchmark_url": p.get("benchmark_url", ""),
                })

    return papers


def load_trends():
    """加载趋势数据"""
    trends = []
    pattern = os.path.join(TRENDS_DIR, "*.md")

    for filepath in sorted(glob.glob(pattern)):
        filename = os.path.basename(filepath)
        if filename == "index.md":
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取标题
        title = ""
        stage = "萌芽"
        for line in content.split("\n"):
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            if "当前阶段" in line:
                import re
                stage_match = re.search(r"当前阶段[：:]\s*(\S+)", line)
                if stage_match:
                    stage = stage_match.group(1)
                else:
                    # 从 blockquote 提取
                    stage_match = re.search(r"(萌芽|上升|主流化|过热|噪声)", line)
                    if stage_match:
                        stage = stage_match.group(1)

        slug = filename.replace(".md", "")
        trends.append({
            "title": title or slug,
            "slug": slug,
            "stage": stage,
            "path": f"{GITHUB_BLOB_BASE}/trends/{filename}"
        })

    return trends


def update_latest_json(daily_reports, papers):
    """更新 latest.json"""
    latest = {
        "updated_at": datetime.now().isoformat(),
        "latest_daily": daily_reports[0] if daily_reports else None,
        "paper_count": len(papers),
        "daily_count": len(daily_reports)
    }

    # 补充首页需要的额外信息
    if daily_reports:
        latest["recent_dailies"] = daily_reports[:7]

    # 高分论文
    top_papers = sorted(papers, key=lambda x: x.get("score", 0), reverse=True)[:10]
    latest["top_papers"] = top_papers

    save_json("latest.json", latest)


def update_daily_index_json(daily_reports):
    """更新 daily-index.json"""
    save_json("daily-index.json", {
        "updated_at": datetime.now().isoformat(),
        "total": len(daily_reports),
        "reports": daily_reports
    })


def update_paper_index_json(papers):
    """更新 paper-index.json"""
    save_json("paper-index.json", {
        "updated_at": datetime.now().isoformat(),
        "total": len(papers),
        "papers": papers
    })


def update_trend_index_json(trends):
    """更新 trend-index.json"""
    save_json("trend-index.json", {
        "updated_at": datetime.now().isoformat(),
        "total": len(trends),
        "trends": trends
    })


def update_insight_index_json():
    """更新 insight-index.json"""
    insights = []
    pattern = os.path.join(INSIGHTS_DIR, "*.md")

    for filepath in sorted(glob.glob(pattern)):
        filename = os.path.basename(filepath)
        if filename == "index.md":
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        title = ""
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        slug = filename.replace(".md", "")
        insights.append({
            "title": title or slug,
            "slug": slug,
            "path": f"{GITHUB_BLOB_BASE}/insights/{filename}"
        })

    save_json("insight-index.json", {
        "updated_at": datetime.now().isoformat(),
        "total": len(insights),
        "insights": insights
    })


def update_source_index_json():
    """更新 source-index.json"""
    sources = {
        "theory_sources": [
            {"name": "arXiv", "type": "theory_primary", "status": "active",
             "url": "https://arxiv.org", "frequency": "daily"},
            {"name": "OpenReview", "type": "theory_primary", "status": "pending",
             "url": "https://openreview.net", "frequency": "daily"},
            {"name": "Hugging Face Daily Papers", "type": "theory_auxiliary", "status": "pending",
             "url": "https://huggingface.co/papers", "frequency": "daily"},
            {"name": "Papers with Code", "type": "theory_auxiliary", "status": "pending",
             "url": "https://paperswithcode.com", "frequency": "daily"},
        ],
        "engineering_sources": [
            {"name": "GitHub Search", "type": "engineering_primary", "status": "pending",
             "url": "https://github.com/search", "frequency": "daily"},
            {"name": "GitHub Trending", "type": "engineering_primary", "status": "pending",
             "url": "https://github.com/trending", "frequency": "daily"},
            {"name": "GitHub Topics", "type": "engineering_primary", "status": "pending",
             "url": "https://github.com/topics", "frequency": "weekly"},
            {"name": "大厂 Engineering Blog", "type": "engineering_verification", "status": "pending",
             "url": "#", "frequency": "weekly"},
            {"name": "CNCF", "type": "engineering_verification", "status": "pending",
             "url": "https://www.cncf.io", "frequency": "weekly"},
            {"name": "Thoughtworks Radar", "type": "engineering_verification", "status": "pending",
             "url": "https://www.thoughtworks.com/radar", "frequency": "quarterly"},
            {"name": "InfoQ", "type": "engineering_verification", "status": "pending",
             "url": "https://www.infoq.com", "frequency": "weekly"},
        ],
        "community_sources": [
            {"name": "Hacker News", "type": "community_weak_signal", "status": "pending",
             "url": "https://news.ycombinator.com", "frequency": "daily"},
            {"name": "Reddit", "type": "community_weak_signal", "status": "pending",
             "url": "https://reddit.com/r/MachineLearning", "frequency": "daily"},
            {"name": "X (Twitter)", "type": "community_weak_signal", "status": "pending",
             "url": "https://x.com", "frequency": "daily"},
        ]
    }

    save_json("source-index.json", {
        "updated_at": datetime.now().isoformat(),
        **sources
    })


def save_json(filename, data):
    """保存 JSON 到 docs/data/"""
    os.makedirs(DOCS_DATA_DIR, exist_ok=True)
    path = os.path.join(DOCS_DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[index] 已更新: {path}")


def update_trends_index_md(trends):
    """更新 trends/index.md"""
    lines = ["# 趋势雷达索引\n"]
    lines.append("> 从前沿论文出发，跟踪长期技术演化\n")

    for t in trends:
        lines.append(f"- [{t['title']}]({t['path']}) — 阶段：{t['stage']}")

    content = "\n".join(lines)
    path = os.path.join(TRENDS_DIR, "index.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[index] 已更新: {path}")


def update_insights_index_md():
    """更新 insights/index.md"""
    lines = ["# 启发索引\n"]
    lines.append("> 从论文和工程实践中蒸馏的启发\n")

    pattern = os.path.join(INSIGHTS_DIR, "*.md")
    for filepath in sorted(glob.glob(pattern)):
        filename = os.path.basename(filepath)
        if filename == "index.md":
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        title = ""
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        lines.append(f"- [{title or filename}](./{filename})")

    content = "\n".join(lines)
    path = os.path.join(INSIGHTS_DIR, "index.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[index] 已更新: {path}")


def main():
    print("=" * 60)
    print("前沿理论驱动技术雷达 - 索引更新")
    print("=" * 60)

    target_date = date.today().isoformat()
    if len(sys.argv) > 1:
        target_date = sys.argv[1]

    print(f"[index] 目标日期: {target_date}")

    # 加载数据
    daily_reports = load_daily_reports()
    papers = load_paper_index()
    trends = load_trends()

    print(f"[index] 加载 {len(daily_reports)} 篇日报")
    print(f"[index] 加载 {len(papers)} 篇论文")
    print(f"[index] 加载 {len(trends)} 个趋势")

    # 更新 JSON
    update_latest_json(daily_reports, papers)
    update_daily_index_json(daily_reports)
    update_paper_index_json(papers)
    update_trend_index_json(trends)
    update_insight_index_json()
    update_source_index_json()

    # 更新 Markdown 索引
    update_trends_index_md(trends)
    update_insights_index_md()

    print("[index] 索引更新完成！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
