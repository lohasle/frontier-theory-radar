#!/usr/bin/env python3
"""
前沿理论雷达 - 历史日期补全脚本

逐天补全缺失的日报：
1. 按日期范围查询 arXiv API
2. 保存论文 JSON
3. 运行 score_papers → generate_daily → update_index → build_pages
"""

import json
import os
import sys
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")
DAILY_DIR = os.path.join(PROJECT_ROOT, "daily")
ARXIV_API_URL = "https://export.arxiv.org/api/query"

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

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def find_missing_dates(start, end):
    """找出 start~end 之间缺失日报的日期"""
    missing = []
    current = start
    while current <= end:
        date_str = current.isoformat()
        daily_path = os.path.join(DAILY_DIR, str(current.year), f"{date_str}.md")
        if not os.path.exists(daily_path):
            missing.append(date_str)
        current += timedelta(days=1)
    return missing


def fetch_arxiv_by_date(target_date_str, max_results=50):
    """按日期范围查询 arXiv API"""
    d = datetime.strptime(target_date_str, "%Y-%m-%d")
    # arXiv submittedDate format: YYYYMMDDHHMM
    date_start = d.strftime("%Y%m%d") + "0000"
    date_end = d.strftime("%Y%m%d") + "2359"

    cat_query = " OR ".join([f"cat:{cat}" for cat in ARXIV_CATEGORIES[:6]])
    date_filter = f"submittedDate:[{date_start} TO {date_end}]"
    search_query = f"({cat_query}) AND {date_filter}"

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
    papers = []

    try:
        print(f"  [fetch] arXiv API date query: {target_date_str}")
        req = urllib.request.Request(url, headers={"User-Agent": "FrontierTheoryRadar/1.0"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read().decode("utf-8")

        root = ET.fromstring(data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            try:
                paper = parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"  [warn] parse error: {e}")
                continue

        print(f"  [fetch] got {len(papers)} papers for {target_date_str}")

    except Exception as e:
        print(f"  [error] arXiv API failed: {e}")

    return papers


def parse_entry(entry, ns):
    """解析 arXiv API entry"""
    title_el = entry.find("atom:title", ns)
    title = title_el.text.strip().replace("\n", " ") if title_el is not None else ""
    title = " ".join(title.split())  # normalize whitespace

    summary_el = entry.find("atom:summary", ns)
    abstract = summary_el.text.strip().replace("\n", " ") if summary_el is not None else ""
    abstract = " ".join(abstract.split())

    id_el = entry.find("atom:id", ns)
    url = id_el.text.strip() if id_el is not None else ""

    published_el = entry.find("atom:published", ns)
    published = published_el.text.strip()[:10] if published_el is not None else ""

    updated_el = entry.find("atom:updated", ns)
    updated = updated_el.text.strip()[:10] if updated_el is not None else ""

    # Authors
    authors = []
    for author in entry.findall("atom:author", ns):
        name_el = author.find("atom:name", ns)
        if name_el is not None:
            authors.append(name_el.text.strip())

    # Categories
    categories = []
    for cat in entry.findall("atom:category", ns):
        term = cat.get("term", "")
        if term:
            categories.append(term)

    # Links
    pdf_url = ""
    for link in entry.findall("atom:link", ns):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break

    # DOI link (arxiv namespace)
    doi_el = entry.find("{http://arxiv.org/schemas/atom}doi", ns)
    doi = doi_el.text.strip() if doi_el is not None else ""

    # Keywords from abstract
    abs_lower = abstract.lower()
    keywords = [kw for kw in HIGH_PRIORITY_KEYWORDS if kw.lower() in abs_lower]

    # arxiv ID from URL
    arxiv_id = url.split("/abs/")[-1] if "/abs/" in url else url.split("/")[-1]

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
        "abstract": abstract[:500],
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
        "papers": papers,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  [save] {len(papers)} papers → {output_path}")
    return output_path


def run_pipeline_step(script_name, target_date):
    """运行流水线中的单个脚本"""
    script_path = os.path.join(PROJECT_ROOT, "scripts", script_name)
    if not os.path.exists(script_path):
        print(f"  [skip] {script_name} not found")
        return False

    try:
        result = subprocess.run(
            ["python3", script_path, target_date],
            capture_output=True, text=True, timeout=120,
            cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            print(f"  [warn] {script_name} exit={result.returncode}")
            if result.stderr:
                print(f"  [stderr] {result.stderr[:300]}")
        else:
            print(f"  [ok] {script_name}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  [warn] {script_name} timed out")
        return False
    except Exception as e:
        print(f"  [error] {script_name}: {e}")
        return False


def backfill_one_day(target_date):
    """补全单天"""
    print(f"\n{'='*60}")
    print(f"  补全日期: {target_date}")
    print(f"{'='*60}")

    # Step 1: Fetch papers by date
    papers = fetch_arxiv_by_date(target_date)

    if not papers:
        print(f"  [warn] 无论文数据，生成占位")
        papers = [{
            "title": f"[占位] {target_date} arXiv 无新论文或抓取失败",
            "authors": [],
            "published": target_date,
            "updated": target_date,
            "source": "placeholder",
            "url": "", "pdf_url": "", "openreview_url": "",
            "paperswithcode_url": "", "code_url": "", "benchmark_url": "", "project_url": "",
            "abstract": f"{target_date} 日 arXiv API 未返回论文数据，可能为周末/节假日或 API 限制。",
            "categories": [], "keywords": [], "score": 0, "decision": "pending", "links": [],
        }]

    # Step 2: Save papers JSON
    save_papers(papers, target_date)

    # Step 3: Run pipeline
    run_pipeline_step("score_papers.py", target_date)
    run_pipeline_step("generate_daily.py", target_date)
    run_pipeline_step("update_index.py", target_date)
    run_pipeline_step("build_pages.py", target_date)

    # Verify daily was created
    year = target_date[:4]
    daily_path = os.path.join(DAILY_DIR, year, f"{target_date}.md")
    if os.path.exists(daily_path):
        size = os.path.getsize(daily_path)
        print(f"  ✅ 日报已生成: {daily_path} ({size} bytes)")
        return True
    else:
        print(f"  ❌ 日报未生成!")
        return False


def main():
    # 自定义日期范围或自动检测
    if len(sys.argv) > 2:
        start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    elif len(sys.argv) > 1 and sys.argv[1] == "auto":
        start_date = date(2026, 4, 28)
        end_date = date(2026, 7, 24)
    else:
        print("用法: python3 backfill_missing_days.py [auto | START_DATE END_DATE]")
        sys.exit(1)

    missing = find_missing_dates(start_date, end_date)

    if not missing:
        print("没有缺失的日期！")
        return

    print(f"发现 {len(missing)} 个缺失日期:")
    for d in missing:
        print(f"  - {d}")

    success = 0
    failed = []

    for target_date in missing:
        ok = backfill_one_day(target_date)
        if ok:
            success += 1
        else:
            failed.append(target_date)

        # arXiv API rate limit: 3s between requests
        import time
        time.sleep(4)

    print(f"\n{'='*60}")
    print(f"  补全完成: {success}/{len(missing)} 成功")
    if failed:
        print(f"  失败日期: {', '.join(failed)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
