#!/usr/bin/env python3
"""
前沿理论驱动技术雷达 - Pages 数据构建脚本

把 Markdown / JSON 数据转换成 docs 页面需要的数据索引。
保证 GitHub Pages 可以正常浏览。
"""

import json
import os
import sys
import glob
import re
from datetime import date, datetime


def parse_front_matter(text):
    """Parse YAML-like front matter without external deps."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_block = text[4:end]
    body = text[end + 5:]
    meta = {}
    for raw in fm_block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if v.startswith("[") and v.endswith("]"):
            items = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
            meta[k] = items
        else:
            meta[k] = v
    return meta, body

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY_DIR = os.path.join(PROJECT_ROOT, "daily")
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")
TRENDS_DIR = os.path.join(PROJECT_ROOT, "trends")
INSIGHTS_DIR = os.path.join(PROJECT_ROOT, "insights")
DOCS_DATA_DIR = os.path.join(PROJECT_ROOT, "docs", "data")


def parse_daily_markdown(filepath):
    """解析日报 Markdown 提取结构化数据"""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    front_matter, content = parse_front_matter(raw)

    result = {
        "has_content": True,
        "paper_table": [],
        "deep_dive": {},
        "references": [],
        "decision": front_matter.get("decision", ""),
        "stage": front_matter.get("stage", ""),
        "meta": front_matter,
    }

    lines = content.split("\n")

    # 提取论文表格
    in_paper_table = False
    for line in lines:
        if "## 1. 今日最值得关注的前沿论文" in line:
            in_paper_table = True
            continue
        if in_paper_table and line.startswith("## "):
            in_paper_table = False
        if in_paper_table and "|" in line and "[" in line:
            # 解析表格行
            match = re.search(r"\[(.*?)\]\((.*?)\).*?\|(.*?)\|(.*?)\|(.*?)\|(.*?)\|", line)
            if match:
                result["paper_table"].append({
                    "title": match.group(1),
                    "url": match.group(2),
                    "source": match.group(3).strip(),
                    "direction": match.group(4).strip(),
                    "score": match.group(5).strip(),
                    "decision": match.group(6).strip()
                })

    # 提取深挖论文
    for i, line in enumerate(lines):
        if line.startswith("**论文：**") or line.startswith("**论文:**"):
            match = re.search(r"\[(.*?)\]\((.*?)\)", line)
            if match:
                result["deep_dive"] = {
                    "title": match.group(1),
                    "url": match.group(2)
                }
            break

    # 提取结论
    for line in lines:
        if "**结论：**" in line or "**结论:**" in line:
            decision = line.split("**")[-1].strip()
            result["decision"] = decision
            break

    # 提取引用
    in_refs = False
    for line in lines:
        if "## 10. 引用与延伸阅读" in line:
            in_refs = True
            continue
        if in_refs and line.startswith("## "):
            in_refs = False
        if in_refs and line.strip().startswith("- ["):
            match = re.search(r"\[(.*?)\]\((.*?)\)", line)
            if match:
                result["references"].append({
                    "label": match.group(1),
                    "url": match.group(2)
                })

    return result


def build_daily_detail_data():
    """为每篇日报生成详情数据"""
    details = {}
    pattern = os.path.join(DAILY_DIR, "*", "*.md")

    for filepath in sorted(glob.glob(pattern), reverse=True):
        filename = os.path.basename(filepath)
        date_str = filename.replace(".md", "")

        parsed = parse_daily_markdown(filepath)
        details[date_str] = parsed

    return details


def build_trend_details():
    """构建趋势详情数据"""
    details = {}
    pattern = os.path.join(TRENDS_DIR, "*.md")

    for filepath in sorted(glob.glob(pattern)):
        filename = os.path.basename(filepath)
        if filename == "index.md":
            continue

        slug = filename.replace(".md", "")

        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        front_matter, content = parse_front_matter(raw)

        # 转换 Markdown 为简单 HTML（基础实现）
        html_content = markdown_to_simple_html(content)

        details[slug] = {
            "slug": slug,
            "meta": front_matter,
            "content": content,
            "html": html_content
        }

    return details


def markdown_to_simple_html(md_text):
    """简单的 Markdown 转 HTML"""
    lines = md_text.split("\n")
    html_lines = []

    for line in lines:
        if line.startswith("# "):
            html_lines.append(f"<h2>{line[2:]}</h2>")
        elif line.startswith("## "):
            html_lines.append(f"<h3>{line[3:]}</h3>")
        elif line.startswith("### "):
            html_lines.append(f"<h4>{line[4:]}</h4>")
        elif line.startswith("> "):
            html_lines.append(f"<blockquote>{line[2:]}</blockquote>")
        elif line.startswith("- "):
            # 处理链接
            text = line[2:]
            text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2" target="_blank">\1</a>', text)
            html_lines.append(f"<li>{text}</li>")
        elif line.startswith("| ") and "---" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            row = "".join(f"<td>{c}</td>" for c in cells)
            html_lines.append(f"<tr>{row}</tr>")
        elif line.strip() == "":
            html_lines.append("")
        else:
            # 处理链接和加粗
            text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2" target="_blank">\1</a>', line)
            text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
            html_lines.append(f"<p>{text}</p>")

    return "\n".join(html_lines)


def save_json(filename, data):
    """保存 JSON"""
    os.makedirs(DOCS_DATA_DIR, exist_ok=True)
    path = os.path.join(DOCS_DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[build] 已生成: {path}")


def main():
    print("=" * 60)
    print("前沿理论驱动技术雷达 - Pages 数据构建")
    print("=" * 60)

    # 构建日报详情数据
    daily_details = build_daily_detail_data()
    save_json("daily-details.json", {
        "updated_at": datetime.now().isoformat(),
        "dailies": daily_details
    })

    # 构建趋势详情数据
    trend_details = build_trend_details()
    save_json("trend-details.json", {
        "updated_at": datetime.now().isoformat(),
        "trends": trend_details
    })

    print("[build] Pages 数据构建完成！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
