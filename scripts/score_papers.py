#!/usr/bin/env python3
"""论文价值发现系统 - 论文评分脚本"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")

TOPIC_KEYWORDS = {
    "ai-agent": ["agent", "agentic", "multi-agent", "planning", "tool use", "function calling"],
    "coding-agent": ["coding agent", "code generation", "program synthesis", "software engineering", "code review", "debugging"],
    "context-engineering": ["context engineering", "long context", "context window", "memory", "prompt", "in-context learning"],
    "rag-knowledge": ["rag", "retrieval", "knowledge", "search", "knowledge graph", "retrieval-augmented"],
    "multimodal-agent": ["multimodal", "world model", "vision-language", "embodied", "robotics", "simulation"],
    "llm-evaluation": ["evaluation", "benchmark", "rubric", "judge", "leaderboard", "agreement", "auto-eval"],
    "inference-serving": ["inference", "serving", "latency", "throughput", "quantization", "speculative decoding", "distillation"],
    "ai-k8s-platform": ["kubernetes", "platform engineering", "scheduling", "gpu", "infra"],
    "data-engineering": ["data pipeline", "streaming", "cdc", "lakehouse", "real-time", "state management"],
    "security-governance": ["security", "governance", "privacy", "reliability", "guardrail", "audit", "risk"],
}

HIGH_VALUE_KEYWORDS = {
    "novelty": ["novel", "new", "first", "foundation", "frontier", "upcycling", "generalization", "emergent", "hypothesis"],
    "evidence": ["experiment", "evaluation", "ablation", "agreement", "benchmark", "validation", "proof", "empirical"],
    "actionability": ["framework", "workflow", "pipeline", "practical", "deployment", "production", "tool", "system"],
    "long_tail": ["negative", "failure", "blind spot", "rubric", "taxonomy", "survey", "counterexample", "case-specific"],
    "trend": ["scaling", "agentic", "world model", "long-context", "coding", "evaluation", "memory", "benchmark"],
}

IGNORE_PATTERNS = ["sentiment", "e-commerce reviews", "indonesian", "medical image segmentation"]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "paper"


def clamp(v, lo=0, hi=10):
    return max(lo, min(hi, round(v, 2)))


def match_topics(text: str):
    matched = []
    for topic_id, kws in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in kws):
            matched.append(topic_id)
    return matched


def compute_score(paper):
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    text = f"{title} {abstract}".lower()
    matched_topics = match_topics(text)

    novelty = 4.8 + sum(0.6 for kw in HIGH_VALUE_KEYWORDS["novelty"] if kw in text)
    problem_importance = 4.5 + len(matched_topics) * 0.65
    relevance = 3.8 + len(matched_topics) * 1.2
    evidence_strength = 4.5 + sum(0.45 for kw in HIGH_VALUE_KEYWORDS["evidence"] if kw in text)
    engineering_testability = 3.5 + sum(0.55 for kw in HIGH_VALUE_KEYWORDS["actionability"] if kw in text)
    trend_signal = 3.5 + sum(0.55 for kw in HIGH_VALUE_KEYWORDS["trend"] if kw in text)
    long_tail_potential = 3.5 + sum(0.65 for kw in HIGH_VALUE_KEYWORDS["long_tail"] if kw in text)
    asset_convertibility = 4.0 + (1.4 if any(k in text for k in ["rubric", "checklist", "workflow", "framework", "prompt"]) else 0) + (0.8 if matched_topics else 0)
    actionability = 3.8 + (1.2 if any(k in text for k in ["practical", "system", "workflow", "code generation", "context", "evaluation"]) else 0) + (1.5 if paper.get("code_url") else 0)

    if paper.get("code_url"):
        evidence_strength += 1.4
        engineering_testability += 2.0
        actionability += 0.8
    if paper.get("benchmark_url"):
        evidence_strength += 1.3
        trend_signal += 0.8
    if paper.get("paperswithcode_url"):
        engineering_testability += 1.2
    if paper.get("openreview_url"):
        evidence_strength += 0.6
    if "survey" in text:
        long_tail_potential += 1.2
        actionability -= 0.6
    if "benchmark" in text:
        trend_signal += 1.4
        asset_convertibility += 0.8
    if any(pat in text for pat in IGNORE_PATTERNS):
        relevance -= 2.8

    noise_risk = 1.2 + (1.2 if not matched_topics else 0) + (1.0 if "exploratory" in text else 0)
    weak_evidence_penalty = 2.0 + (2.0 if not paper.get("code_url") else 0) + (1.0 if "evaluation" not in text and "experiment" not in text else 0)
    low_relevance_penalty = max(0, 5 - len(matched_topics) * 1.4)
    engineering_cost_penalty = 2.5 + (1.5 if "pretrain" in text or "from scratch" in text else 0)
    reproducibility_risk = 2.0 + (2.0 if not paper.get("code_url") else 0) + (1.0 if not paper.get("benchmark_url") else 0)

    scores = {
        "novelty": clamp(novelty),
        "problem_importance": clamp(problem_importance),
        "relevance": clamp(relevance),
        "evidence_strength": clamp(evidence_strength),
        "engineering_testability": clamp(engineering_testability),
        "trend_signal": clamp(trend_signal),
        "long_tail_potential": clamp(long_tail_potential),
        "asset_convertibility": clamp(asset_convertibility),
        "actionability": clamp(actionability),
        "noise_risk": clamp(noise_risk),
        "weak_evidence_penalty": clamp(weak_evidence_penalty),
        "low_relevance_penalty": clamp(low_relevance_penalty),
        "engineering_cost_penalty": clamp(engineering_cost_penalty),
        "reproducibility_risk": clamp(reproducibility_risk),
    }
    return scores, matched_topics


def calculate_total_score(scores):
    positive_weights = {
        "novelty": 14, "problem_importance": 12, "relevance": 13,
        "evidence_strength": 10, "engineering_testability": 12,
        "trend_signal": 10, "long_tail_potential": 10,
        "asset_convertibility": 10, "actionability": 9,
    }
    negative_weights = {
        "noise_risk": 8, "weak_evidence_penalty": 6, "low_relevance_penalty": 6,
        "engineering_cost_penalty": 5, "reproducibility_risk": 5,
    }
    total = sum(scores.get(k, 0) * w / 10 for k, w in positive_weights.items())
    total -= sum(scores.get(k, 0) * w / 10 for k, w in negative_weights.items())
    return round(max(0, min(100, total)), 1)


def get_decision(score):
    if score >= 80:
        return "重点学习"
    if score >= 65:
        return "轻量试点"
    if score >= 50:
        return "持续观察"
    return "暂时忽略"


def classify_value_type(scores, total):
    if total < 50 or (scores["novelty"] < 4.5 and scores["long_tail_potential"] < 5):
        return "ignore"
    if scores["relevance"] >= 7 and scores["engineering_testability"] >= 6.2 and scores["actionability"] >= 6.2:
        return "immediate"
    if scores["trend_signal"] >= 7.2 and scores["evidence_strength"] >= 5.2:
        return "trend"
    if scores["long_tail_potential"] >= 6.4 or scores["asset_convertibility"] >= 7:
        return "long_tail"
    if total >= 72:
        return "immediate"
    if total >= 58:
        return "trend"
    return "long_tail"


def trend_status_from_value_type(value_type, scores):
    if value_type == "ignore":
        return "noise"
    if value_type == "long_tail":
        return "long_tail_watch"
    if value_type == "trend":
        return "rising" if scores.get("evidence_strength", 0) >= 6 else "emerging"
    return "emerging"


def load_llm_overrides(target_date):
    year = target_date[:4]
    llm_path = Path(PAPERS_DIR) / year / f"{target_date}-llm-scores.json"
    if not llm_path.exists():
        return {}
    try:
        data = json.loads(llm_path.read_text(encoding="utf-8"))
        return data.get("by_url", {})
    except Exception as e:
        print(f"[score] 读取 LLM 增强评分失败: {e}")
        return {}


def score_papers(papers, llm_overrides=None):
    llm_overrides = llm_overrides or {}
    scored = []
    for paper in papers:
        scores, topics = compute_score(paper)
        total = calculate_total_score(scores)
        decision = get_decision(total)
        value_type = classify_value_type(scores, total)

        llm_hit = llm_overrides.get(paper.get("url", ""))
        if llm_hit and isinstance(llm_hit, dict):
            llm_score = llm_hit.get("score")
            if isinstance(llm_score, (int, float)):
                total = round(max(0, min(100, float(llm_score))), 1)
                decision = get_decision(total)
                value_type = classify_value_type(scores, total)
            if llm_hit.get("value_type"):
                value_type = llm_hit["value_type"]
            if isinstance(llm_hit.get("matched_topics"), list) and llm_hit.get("matched_topics"):
                topics = llm_hit["matched_topics"]
            if llm_hit.get("reason"):
                paper["llm_reason"] = llm_hit["reason"]

        paper["id"] = paper.get("id") or slugify(paper.get("title", ""))
        paper["score"] = total
        paper["decision"] = decision
        paper["value_type"] = value_type
        paper["matched_topics"] = topics
        paper["score_breakdown"] = scores
        paper["trend_status"] = trend_status_from_value_type(value_type, scores)
        scored.append(paper)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def main():
    print("=" * 60)
    print("论文价值发现系统 - 论文评分")
    print("=" * 60)
    target_date = date.today().isoformat()
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    year = target_date[:4]
    papers_path = os.path.join(PAPERS_DIR, year, f"{target_date}-papers.json")
    if not os.path.exists(papers_path):
        print(f"[error] 论文文件不存在: {papers_path}")
        return 1
    data = json.loads(Path(papers_path).read_text(encoding="utf-8"))
    papers = data.get("papers", [])
    print(f"[score] 加载 {len(papers)} 篇论文")
    llm_overrides = load_llm_overrides(target_date)
    if llm_overrides:
        print(f"[score] 检测到 LLM 增强评分: {len(llm_overrides)} 条")
    scored_papers = score_papers(papers, llm_overrides=llm_overrides)
    for i, p in enumerate(scored_papers[:10], start=1):
        print(f"  #{i} [{p['score']:5.1f}] {p['value_type']:10s} | {p['title'][:60]}")
    data["papers"] = scored_papers
    data["scored_at"] = date.today().isoformat()
    Path(papers_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[score] 评分完成，结果已保存到: {papers_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
