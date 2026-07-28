#!/usr/bin/env python3
"""
前沿理论雷达 - 历史日期真实数据补全

按日期逐天从 arXiv API 抓取真实论文，替换占位数据。
使用 curl 调用 arXiv API（urllib 在本机有 TLS 超时问题）。
每次调用间隔 5 秒，遵守 arXiv API 速率限制。
"""

import json
import os
import sys
import subprocess
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")
DAILY_DIR = os.path.join(PROJECT_ROOT, "daily")

ARXIV_CATEGORIES = [
    "cs.AI", "cs.CL", "cs.LG", "cs.SE", "cs.IR",
    "cs.MA", "cs.RO", "cs.CV", "cs.DC", "cs.DB", "cs.CR",
    "stat.ML"
]

HIGH_PRIORITY_KEYWORDS = [
    "agent", "agentic", "world model", "context engineering",
    "memory", "coding agent", "evaluation", "benchmark",
    "RAG", "retrieval augmented", "multimodal", "inference",
    "tool use", "function calling", "planning"
]


def find_dates_to_backfill():
    """找出需要补全真实数据的日期：日报文件中含'占位'标记的"""
    target_dates = []
    daily_dir = os.path.join(DAILY_DIR, "2026")
    if not os.path.isdir(daily_dir):
        return target_dates

    for fname in sorted(os.listdir(daily_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(daily_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        # Check if this is a placeholder daily
        if "补全占位" in content or "backfill_placeholder" in content or "此日期论文数据待重跑" in content:
            date_str = fname.replace(".md", "")
            target_dates.append(date_str)

    return target_dates


def curl_arxiv_date(target_date_str, max_results=50):
    """用 curl 调用 arXiv API 按日期查询"""
    d = datetime.strptime(target_date_str, "%Y-%m-%d")
    date_start = d.strftime("%Y%m%d") + "0000"
    date_end = d.strftime("%Y%m%d") + "2359"

    cat_query = " OR ".join([f"cat:{cat}" for cat in ARXIV_CATEGORIES[:6]])
    date_filter = f"submittedDate:[{date_start} TO {date_end}]"
    search_query = f"({cat_query}) AND {date_filter}"

    # Build URL with proper encoding via curl -G
    cmd = [
        "curl", "-s", "--max-time", "45",
        "-G", "https://export.arxiv.org/api/query",
        "--data-urlencode", f"search_query={search_query}",
        "--data-urlencode", f"start=0",
        "--data-urlencode", f"max_results={max_results}",
        "--data-urlencode", "sortBy=submittedDate",
        "--data-urlencode", "sortOrder=descending",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        data = result.stdout

        if not data or "Rate exceeded" in data:
            print(f"    [warn] arXiv API rate limited or empty for {target_date_str}")
            return []

        root = ET.fromstring(data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        papers = []

        for entry in entries:
            paper = parse_entry(entry, ns)
            if paper:
                papers.append(paper)

        print(f"    [fetch] {len(papers)} papers from arXiv for {target_date_str}")
        return papers

    except subprocess.TimeoutExpired:
        print(f"    [error] curl timed out for {target_date_str}")
        return []
    except ET.ParseError as e:
        print(f"    [error] XML parse failed: {e}")
        return []
    except Exception as e:
        print(f"    [error] {e}")
        return []


def parse_entry(entry, ns):
    """解析 arXiv entry"""
    ns_atom = {"atom": "http://www.w3.org/2005/Atom"}

    title_el = entry.find("atom:title", ns_atom)
    title = title_el.text.strip().replace("\n", " ") if title_el is not None else ""
    title = " ".join(title.split())

    summary_el = entry.find("atom:summary", ns_atom)
    abstract = summary_el.text.strip().replace("\n", " ") if summary_el is not None else ""
    abstract = " ".join(abstract.split())

    id_el = entry.find("atom:id", ns_atom)
    url = id_el.text.strip() if id_el is not None else ""

    published_el = entry.find("atom:published", ns_atom)
    published = published_el.text.strip()[:10] if published_el is not None else ""

    updated_el = entry.find("atom:updated", ns_atom)
    updated = updated_el.text.strip()[:10] if updated_el is not None else ""

    authors = []
    for author in entry.findall("atom:author", ns_atom):
        name_el = author.find("atom:name", ns_atom)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    categories = []
    for cat in entry.findall("atom:category", ns_atom):
        term = cat.get("term", "")
        if term:
            categories.append(term)

    pdf_url = ""
    for link in entry.findall("atom:link", ns_atom):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break

    abs_lower = abstract.lower()
    keywords = [kw for kw in HIGH_PRIORITY_KEYWORDS if kw.lower() in abs_lower]

    return {
        "title": title,
        "authors": authors[:5],
        "published": published,
        "updated": updated,
        "source": "arxiv",
        "url": url,
        "pdf_url": pdf_url,
        "openreview_url": "",
        "paperswithcode_url": f"https://paperswithcode.com/search?q={urllib.parse.quote(title[:80])}",
        "code_url": "",
        "benchmark_url": "",
        "project_url": "",
        "abstract": abstract[:600],
        "categories": categories,
        "keywords": keywords,
        "score": 0,
        "decision": "pending",
        "links": [],
    }


def save_papers(papers, target_date):
    year = target_date[:4]
    output_dir = os.path.join(PAPERS_DIR, year)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{target_date}-papers.json")

    data = {
        "date": target_date,
        "source_status": "ok" if papers else "no_papers_found",
        "papers": papers if papers else [{
            "title": f"[无新论文] {target_date} arXiv 无新提交",
            "authors": [], "published": target_date, "updated": target_date,
            "source": "arxiv", "url": "", "pdf_url": "",
            "openreview_url": "", "paperswithcode_url": "",
            "code_url": "", "benchmark_url": "", "project_url": "",
            "abstract": f"{target_date} 日 arXiv 在目标分类中无新论文提交。",
            "categories": [], "keywords": [], "score": 0,
            "decision": "pending", "links": [],
        }],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"    [save] {len(data['papers'])} papers → {output_path}")


def run_pipeline_step(script_name, target_date):
    script_path = os.path.join(PROJECT_ROOT, "scripts", script_name)
    if not os.path.exists(script_path):
        print(f"    [skip] {script_name} not found")
        return False
    try:
        result = subprocess.run(
            ["python3", script_path, target_date],
            capture_output=True, text=True, timeout=120,
            cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            print(f"    [warn] {script_name} exit={result.returncode}")
            if result.stderr:
                print(f"    [stderr] {result.stderr[:200]}")
        else:
            print(f"    [ok] {script_name}")
        return result.returncode == 0
    except Exception as e:
        print(f"    [error] {script_name}: {e}")
        return False


def backfill_one_day(target_date):
    print(f"\n{'='*60}")
    print(f"  补全真实数据: {target_date}")
    print(f"{'='*60}")

    # Fetch real papers
    papers = curl_arxiv_date(target_date)

    if not papers:
        # Retry once after longer wait
        print(f"    [retry] waiting 15s before retry...")
        time.sleep(15)
        papers = curl_arxiv_date(target_date)

    save_papers(papers, target_date)

    # Run pipeline
    run_pipeline_step("score_papers.py", target_date)
    run_pipeline_step("generate_daily.py", target_date)

    # Verify daily is no longer placeholder
    year = target_date[:4]
    daily_path = os.path.join(DAILY_DIR, year, f"{target_date}.md")
    if os.path.exists(daily_path):
        with open(daily_path, "r", encoding="utf-8") as f:
            content = f.read()
        is_placeholder = "补全占位" in content or "此日期论文数据待重跑" in content
        size = os.path.getsize(daily_path)
        status = "❌ 仍是占位" if is_placeholder else "✅ 真实数据"
        print(f"    {status} 日报: {size} bytes")
        return not is_placeholder
    else:
        print(f"    ❌ 日报未生成!")
        return False


def main():
    dates = find_dates_to_backfill()

    if not dates:
        print("没有需要补全真实数据的日期！")
        return

    print(f"发现 {len(dates)} 个需要替换占位数据的日期:")
    for d in dates:
        print(f"  - {d}")

    success = 0
    failed = []

    for i, target_date in enumerate(dates):
        ok = backfill_one_day(target_date)
        if ok:
            success += 1
        else:
            failed.append(target_date)

        # arXiv rate limit: wait 5s between requests
        if i < len(dates) - 1:
            print(f"    [rate-limit] waiting 5s...")
            time.sleep(5)

    # Rebuild index and pages
    print(f"\n{'='*60}")
    print(f"  重建索引和 Pages")
    print(f"{'='*60}")
    run_pipeline_step("update_index.py", dates[-1] if dates else "")
    run_pipeline_step("build_pages.py", dates[-1] if dates else "")

    print(f"\n{'='*60}")
    print(f"  补全完成: {success}/{len(dates)} 成功")
    if failed:
        print(f"  失败日期: {', '.join(failed)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
