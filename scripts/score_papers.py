#!/usr/bin/env python3
"""
前沿理论驱动技术雷达 - 论文评分脚本

基于 config/scoring.yml 的规则对论文打分。
当前实现：关键词 + 分类规则打分。
后续扩展：LLM 辅助评分。

输入：papers/YYYY/YYYY-MM-DD-papers.json
输出：同文件（更新 score 和 decision 字段）
"""

import json
import os
import sys
from datetime import date

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")

# ============================================================
# 评分规则（对应 config/scoring.yml）
# ============================================================

# 高优先级关键词 -> topic 映射
TOPIC_KEYWORDS = {
    "ai-agent": ["agent", "agentic", "tool use", "function calling", "multi-agent",
                  "autonomous agent", "agent framework", "planning"],
    "coding-agent": ["coding agent", "code generation", "program synthesis",
                      "automated debugging", "code review", "software engineering ai"],
    "context-engineering": ["context engineering", "long context", "in-context learning",
                            "prompt engineering", "memory", "skill learning"],
    "rag-knowledge": ["rag", "retrieval augmented", "knowledge graph", "semantic search",
                      "document understanding"],
    "multimodal-agent": ["multimodal", "world model", "vision language", "embodied",
                         "robotics", "simulation"],
    "llm-evaluation": ["evaluation", "benchmark", "auto-eval", "llm judge", "alignment",
                       "safety evaluation"],
    "inference-serving": ["inference", "serving", "quantization", "distillation",
                          "speculative decoding", "optimization"],
    "ai-k8s-platform": ["kubernetes", "mlops", "platform engineering", "gpu scheduling"],
    "data-engineering": ["data engineering", "cdc", "lakehouse", "streaming", "real-time",
                         "data pipeline"],
    "security-governance": ["security", "governance", "red teaming", "adversarial",
                            "privacy", "reliability"]
}

# 高分关键词（theory_novelty 加分）
HIGH_NOVELTY_KEYWORDS = [
    "new paradigm", "novel", "first", "breakthrough", "foundation",
    "emergent", "zero-shot", "self-", "meta-", "auto-"
]

# 炒作风险关键词（hype_risk 加分）
HYPE_KEYWORDS = [
    "revolutionary", "game-changing", "unprecedented", "groundbreaking",
    "paradigm shift", "next generation"
]


def compute_score(paper):
    """基于规则的论文评分"""
    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()
    categories = paper.get("categories", [])
    keywords = paper.get("keywords", [])
    text = f"{title} {abstract}"

    scores = {}

    # theory_novelty: 理论新意 (0-10)
    novelty = 5  # 基础分
    for kw in HIGH_NOVELTY_KEYWORDS:
        if kw in text:
            novelty += 0.5
    novelty = min(novelty, 10)
    scores["theory_novelty"] = novelty

    # problem_importance: 问题重要性 (0-10)
    importance = 5
    matched_topics = []
    for topic_id, topic_kws in TOPIC_KEYWORDS.items():
        for kw in topic_kws:
            if kw in text:
                matched_topics.append(topic_id)
                importance += 0.3
                break
    importance = min(importance, 10)
    scores["problem_importance"] = importance

    # engineering_impact: 工程影响力 (0-10)
    eng_impact = 4
    eng_keywords = ["system", "architecture", "pipeline", "framework", "deployment",
                    "production", "scalab", "efficien"]
    for kw in eng_keywords:
        if kw in text:
            eng_impact += 0.4
    eng_impact = min(eng_impact, 10)
    scores["engineering_impact"] = eng_impact

    # engineering_potential: 工程外溢价值 (0-10)
    eng_potential = 4
    if any(kw in text for kw in ["agent", "tool", "automat", "workflow"]):
        eng_potential += 1.5
    if any(kw in text for kw in ["api", "sdk", "integration", "plugin"]):
        eng_potential += 1
    eng_potential = min(eng_potential, 10)
    scores["engineering_potential"] = eng_potential

    # evidence_strength: 证据强度 (0-10)
    evidence = 5
    if paper.get("code_url"):
        evidence += 2
    if paper.get("benchmark_url"):
        evidence += 2
    if any(kw in text for kw in ["experiment", "empirical", "ablation"]):
        evidence += 1
    evidence = min(evidence, 10)
    scores["evidence_strength"] = evidence

    # source_quality: 来源质量 (0-10)
    source_quality = 6  # arXiv 基础分
    if paper.get("source") == "OpenReview":
        source_quality = 8
    if any(kw in text for kw in ["google", "meta", "openai", "anthropic", "microsoft",
                                  "stanford", "mit", "berkeley", "cmu"]):
        source_quality += 1.5
    source_quality = min(source_quality, 10)
    scores["source_quality"] = source_quality

    # reproducibility: 可复现性 (0-10)
    reproducibility = 3
    if paper.get("code_url"):
        reproducibility += 3
    if paper.get("benchmark_url"):
        reproducibility += 2
    if any(kw in text for kw in ["open source", "code available", "github"]):
        reproducibility += 1.5
    reproducibility = min(reproducibility, 10)
    scores["reproducibility"] = reproducibility

    # personal_relevance: 对资深架构师的相关性 (0-10)
    relevance = 4
    if matched_topics:
        relevance += min(len(matched_topics) * 0.8, 3)
    relevance = min(relevance, 10)
    scores["personal_relevance"] = relevance

    # long_term_value: 长期学习复利 (0-10)
    long_term = 5
    if any(kw in text for kw in ["foundation", "general", "universal", "principle"]):
        long_term += 2
    if any(kw in text for kw in ["framework", "taxonomy", "survey"]):
        long_term += 1
    long_term = min(long_term, 10)
    scores["long_term_value"] = long_term

    # 负向评分
    # hype_risk (0-10)
    hype = 0
    for kw in HYPE_KEYWORDS:
        if kw in text:
            hype += 2
    hype = min(hype, 10)
    scores["hype_risk"] = hype

    # weak_evidence_penalty (0-10)
    weak_penalty = 3
    if not paper.get("code_url") and "code" not in text:
        weak_penalty += 2
    if not any(kw in text for kw in ["experiment", "result", "evaluation"]):
        weak_penalty += 2
    weak_penalty = min(weak_penalty, 10)
    scores["weak_evidence_penalty"] = weak_penalty

    # low_relevance_penalty (0-10)
    low_rel = 5
    if matched_topics:
        low_rel = max(0, 5 - len(matched_topics))
    scores["low_relevance_penalty"] = low_rel

    return scores, matched_topics


def calculate_total_score(scores):
    """计算总分"""
    # 正向权重
    positive_weights = {
        "theory_novelty": 15, "problem_importance": 15,
        "engineering_impact": 15, "engineering_potential": 10,
        "evidence_strength": 10, "source_quality": 5,
        "reproducibility": 10, "personal_relevance": 10,
        "long_term_value": 10
    }
    # 负向权重
    negative_weights = {
        "hype_risk": 10, "weak_evidence_penalty": 8,
        "low_relevance_penalty": 5
    }

    total = 0
    for key, weight in positive_weights.items():
        total += scores.get(key, 0) * weight / 10
    for key, weight in negative_weights.items():
        total -= scores.get(key, 0) * weight / 10

    return round(max(0, min(100, total)), 1)


def get_decision(score):
    """根据分数判断"""
    if score >= 80:
        return "重点学习"
    elif score >= 65:
        return "轻量试点"
    elif score >= 50:
        return "持续观察"
    else:
        return "暂时忽略"


def score_papers(papers):
    """对论文列表评分"""
    scored = []
    for paper in papers:
        scores, topics = compute_score(paper)
        total = calculate_total_score(scores)
        decision = get_decision(total)

        paper["score"] = total
        paper["decision"] = decision
        paper["matched_topics"] = topics
        paper["score_breakdown"] = scores

        scored.append(paper)

    # 按分数降序排序
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def main():
    print("=" * 60)
    print("前沿理论驱动技术雷达 - 论文评分")
    print("=" * 60)

    target_date = date.today().isoformat()
    if len(sys.argv) > 1:
        target_date = sys.argv[1]

    year = target_date[:4]
    papers_path = os.path.join(PAPERS_DIR, year, f"{target_date}-papers.json")

    if not os.path.exists(papers_path):
        print(f"[error] 论文文件不存在: {papers_path}")
        print("[hint] 请先运行 fetch_papers.py")
        return 1

    with open(papers_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    papers = data.get("papers", [])
    print(f"[score] 加载 {len(papers)} 篇论文")

    # 评分
    scored_papers = score_papers(papers)

    # 输出评分结果摘要
    for i, p in enumerate(scored_papers[:10]):
        print(f"  #{i+1} [{p['score']:5.1f}] {p['decision']:6s} | {p['title'][:60]}")

    # 更新文件
    data["papers"] = scored_papers
    data["scored_at"] = date.today().isoformat()

    with open(papers_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[score] 评分完成，结果已保存到: {papers_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
