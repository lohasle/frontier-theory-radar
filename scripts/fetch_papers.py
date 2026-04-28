#!/usr/bin/env python3
"""
前沿理论驱动技术雷达 - 论文抓取脚本

从固定数据源抓取论文元数据。
当前实现：arXiv API
后续扩展：OpenReview, HuggingFace, Papers with Code

输出：papers/YYYY/YYYY-MM-DD-papers.json
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, date
import time
import re

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")

# arXiv API 配置
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# 重点分类
ARXIV_CATEGORIES = [
    "cs.AI", "cs.CL", "cs.LG", "cs.SE", "cs.IR",
    "cs.MA", "cs.RO", "cs.CV", "cs.DC", "cs.DB", "cs.CR",
    "stat.ML"
]

# 高优先级关键词
HIGH_PRIORITY_KEYWORDS = [
    "agent", "agentic", "world model", "context engineering",
    "memory", "coding agent", "evaluation", "benchmark",
    "RAG", "retrieval augmented", "multimodal", "inference",
    "tool use", "function calling", "planning"
]


def load_config():
    """加载配置"""
    # 简单配置加载，避免引入 yaml 依赖
    return {
        "max_results_per_category": 10,
        "categories": ARXIV_CATEGORIES,
    }


def fetch_arxiv_papers(categories, max_results=10):
    """从 arXiv API 抓取论文"""
    papers = []

    # 构建查询 - 按多个分类搜索
    # 使用批量查询减少 API 调用
    cat_query = " OR ".join([f"cat:{cat}" for cat in categories[:5]])

    params = {
        "search_query": cat_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

    try:
        print(f"[fetch] 请求 arXiv API: {url[:120]}...")
        req = urllib.request.Request(url, headers={"User-Agent": "FrontierTheoryRadar/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode("utf-8")

        root = ET.fromstring(data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            try:
                paper = parse_arxiv_entry(entry, ns)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"[warn] 解析论文条目失败: {e}")
                continue

        print(f"[fetch] 从 arXiv 获取 {len(papers)} 篇论文")

    except Exception as e:
        print(f"[error] arXiv API 请求失败: {e}")

    return papers


def parse_arxiv_entry(entry, ns):
    """解析 arXiv API 返回的单篇论文"""
    title_elem = entry.find("atom:title", ns)
    if title_elem is None:
        return None

    title = title_elem.text.strip().replace("\n", " ").replace("\r", "")
    title = re.sub(r"\s+", " ", title)

    # 基本信息
    paper_id = entry.find("atom:id", ns).text
    published = entry.find("atom:published", ns).text[:10] if entry.find("atom:published", ns) is not None else ""
    updated = entry.find("atom:updated", ns).text[:10] if entry.find("atom:updated", ns) is not None else ""

    # 摘要
    summary_elem = entry.find("atom:summary", ns)
    abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""
    abstract = re.sub(r"\s+", " ", abstract)

    # 作者
    authors = []
    for author in entry.findall("atom:author", ns):
        name = author.find("atom:name", ns)
        if name is not None:
            authors.append(name.text.strip())

    # 分类
    categories = []
    for cat in entry.findall("atom:category", ns):
        term = cat.get("term", "")
        if term:
            categories.append(term)

    # 链接
    pdf_url = ""
    for link in entry.findall("atom:link", ns):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break

    if not pdf_url:
        pdf_url = paper_id.replace("abs", "pdf")

    links = [
        {"label": "arXiv", "url": paper_id},
        {"label": "PDF", "url": pdf_url},
    ]

    return {
        "title": title,
        "authors": authors[:5],  # 最多保留 5 位作者
        "published": published,
        "updated": updated,
        "source": "arXiv",
        "url": paper_id,
        "pdf_url": pdf_url,
        "openreview_url": "",
        "paperswithcode_url": "",
        "code_url": "",
        "benchmark_url": "",
        "project_url": "",
        "abstract": abstract[:500] if abstract else "",
        "categories": categories,
        "keywords": extract_keywords(title, abstract),
        "score": 0,
        "decision": "pending",
        "links": links
    }


def extract_keywords(title, abstract):
    """从标题和摘要中提取关键词"""
    text = (title + " " + abstract).lower()
    found = []
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw.lower() in text:
            found.append(kw)
    return found


def fetch_openreview_papers():
    """从 OpenReview 抓取论文（待实现）"""
    # TODO: 实现 OpenReview API 调用
    print("[fetch] OpenReview 抓取待实现，跳过")
    return []


def fetch_huggingface_papers():
    """从 Hugging Face Daily Papers 抓取（待实现）"""
    # TODO: 实现 HuggingFace Papers API 调用
    print("[fetch] HuggingFace Papers 抓取待实现，跳过")
    return []


def fetch_paperswithcode_papers():
    """从 Papers with Code 抓取（待实现）"""
    # TODO: 实现 Papers with Code API 调用
    print("[fetch] Papers with Code 抓取待实现，跳过")
    return []


def merge_and_deduplicate(papers_list):
    """合并多个来源的论文并去重"""
    seen_titles = set()
    merged = []
    for papers in papers_list:
        for p in papers:
            title_key = p["title"].lower().strip()[:80]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                merged.append(p)
    return merged


def save_papers(papers, target_date=None):
    """保存论文数据到 JSON"""
    if target_date is None:
        target_date = date.today().isoformat()

    year = target_date[:4]
    output_dir = os.path.join(PAPERS_DIR, year)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{target_date}-papers.json")

    output = {
        "date": target_date,
        "total": len(papers),
        "generated_at": datetime.now().isoformat(),
        "papers": papers
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[fetch] 保存 {len(papers)} 篇论文到 {output_path}")
    return output_path


def main():
    print("=" * 60)
    print("前沿理论驱动技术雷达 - 论文抓取")
    print("=" * 60)

    target_date = date.today().isoformat()
    if len(sys.argv) > 1:
        target_date = sys.argv[1]

    print(f"[fetch] 目标日期: {target_date}")

    config = load_config()

    # 从各数据源抓取
    all_papers = []

    # arXiv（已实现）
    arxiv_papers = fetch_arxiv_papers(config["categories"], config["max_results_per_category"])
    all_papers.append(arxiv_papers)

    # OpenReview（待实现）
    openreview_papers = fetch_openreview_papers()
    all_papers.append(openreview_papers)

    # HuggingFace（待实现）
    hf_papers = fetch_huggingface_papers()
    all_papers.append(hf_papers)

    # Papers with Code（待实现）
    pwc_papers = fetch_paperswithcode_papers()
    all_papers.append(pwc_papers)

    # 合并去重
    papers = merge_and_deduplicate(all_papers)

    if not papers:
        print("[warn] 未获取到任何论文，生成空占位数据")
        papers = [{
            "title": "[占位] 今日论文抓取失败或无新论文",
            "authors": [],
            "published": target_date,
            "updated": target_date,
            "source": "placeholder",
            "url": "",
            "pdf_url": "",
            "openreview_url": "",
            "paperswithcode_url": "",
            "code_url": "",
            "benchmark_url": "",
            "project_url": "",
            "abstract": "论文抓取失败或无新论文。请检查网络连接和 API 状态。后续运行会替换为真实数据。",
            "categories": [],
            "keywords": [],
            "score": 0,
            "decision": "pending",
            "links": []
        }]

    # 保存
    output_path = save_papers(papers, target_date)
    print(f"[fetch] 完成！论文数据已保存到: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
