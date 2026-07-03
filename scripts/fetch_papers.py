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
ARXIV_API_URL = "https://export.arxiv.org/api/query"

# arXiv RSS 后备端点（export.arxiv.org API 不稳定时使用）
ARXIV_RSS_URL = "https://rss.arxiv.org/rss/{cat}"
DC_NS = "http://purl.org/dc/elements/1.1/"
ARXIV_NS = "http://arxiv.org/schemas/atom"
NS = {"dc": DC_NS, "arxiv": ARXIV_NS}

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
    """从 arXiv API 抓取论文；API 失败时自动回退到 RSS 馈送"""
    papers = fetch_arxiv_api(categories, max_results)
    if papers:
        return papers

    print("[fetch] arXiv API 无结果，尝试 RSS 馈送后备...")
    rss_papers = fetch_arxiv_rss(categories, max_results)
    if rss_papers:
        print(f"[fetch] RSS 后备成功，获取 {len(rss_papers)} 篇论文")
    else:
        print("[fetch] RSS 后备也未获取到论文")
    return rss_papers


def fetch_arxiv_api(categories, max_results=10):
    """从 arXiv Query API 抓取论文（原始实现）"""
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

        print(f"[fetch] 从 arXiv API 获取 {len(papers)} 篇论文")

    except Exception as e:
        print(f"[error] arXiv API 请求失败: {e}")

    return papers


def fetch_arxiv_rss(categories, max_results=10):
    """从 arXiv RSS 馈送抓取论文（export.arxiv.org API 不可用时的后备）"""
    papers = []
    # RSS 按分类逐个抓取，取前几个高优先级分类
    for cat in categories[:4]:
        url = ARXIV_RSS_URL.format(cat=cat)
        try:
            print(f"[fetch] 请求 RSS: {cat}")
            req = urllib.request.Request(url, headers={"User-Agent": "FrontierTheoryRadar/1.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read().decode("utf-8")
        except Exception as e:
            print(f"[warn] RSS {cat} 请求失败: {e}")
            continue

        try:
            root = ET.fromstring(data)
        except Exception as e:
            print(f"[warn] RSS {cat} 解析失败: {e}")
            continue

        for item in root.findall(".//item"):
            paper = parse_arxiv_rss_item(item, cat)
            if paper:
                papers.append(paper)

    # 合并去重（按 arxiv id / 标题）
    seen = set()
    deduped = []
    for p in papers:
        key = (p.get("url") or p["title"].lower().strip()[:80])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    return deduped[:max_results] if max_results else deduped


def parse_arxiv_rss_item(item, default_cat):
    """解析单个 RSS item 为统一论文 dict"""
    title_elem = item.find("title")
    if title_elem is None or not title_elem.text:
        return None
    title = re.sub(r"\s+", " ", title_elem.text.strip())

    link_elem = item.find("link")
    url = link_elem.text.strip() if link_elem is not None and link_elem.text else ""

    # 解析 description: "arXiv:<id>v<n> Announce Type: new \nAbstract: ..."
    desc_elem = item.find("description")
    abstract = ""
    announce_type = ""
    arxiv_id = ""
    if desc_elem is not None and desc_elem.text:
        desc = desc_elem.text
        m_id = re.search(r"arXiv:(\d{4}\.\d{4,5})", desc)
        if m_id:
            arxiv_id = m_id.group(1)
        m_type = re.search(r"Announce Type:\s*(\w+)", desc)
        if m_type:
            announce_type = m_type.group(1).lower()
        m_abs = re.search(r"Abstract:\s*(.*)", desc, re.DOTALL)
        if m_abs:
            abstract = re.sub(r"\s+", " ", m_abs.group(1).strip())

    # 作者：多个 dc:creator 子元素
    authors = []
    for creator in item.findall(f"{{{DC_NS}}}creator"):
        if creator.text:
            authors.append(creator.text.strip())

    # 发布日期
    pub_elem = item.find("pubDate")
    published = ""
    if pub_elem is not None and pub_elem.text:
        try:
            published = datetime.strptime(pub_elem.text, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
        except Exception:
            published = pub_elem.text[:10]

    if not arxiv_id and url:
        m = re.search(r"(\d{4}\.\d{4,5})", url)
        if m:
            arxiv_id = m.group(1)

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else ""

    categories = [c.text.strip() for c in item.findall("category") if c.text]
    if not categories:
        categories = [default_cat]

    links = []
    if url:
        links.append({"label": "arXiv", "url": url})
    if pdf_url:
        links.append({"label": "PDF", "url": pdf_url})

    return {
        "title": title,
        "authors": authors[:5],
        "published": published,
        "updated": published,
        "source": "arXiv",
        "url": url,
        "pdf_url": pdf_url,
        "openreview_url": "",
        "paperswithcode_url": "",
        "code_url": "",
        "benchmark_url": "",
        "project_url": "",
        "abstract": abstract[:500] if abstract else "",
        "categories": categories,
        "keywords": extract_keywords(title, abstract),
        "announce_type": announce_type,
        "score": 0,
        "decision": "pending",
        "links": links
    }


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
