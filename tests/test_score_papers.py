import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel_path: str):
    p = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


score_papers = load_module("score_papers", "scripts/score_papers.py")


def test_llm_override_score_applies():
    papers = [{
        "title": "Agent memory study",
        "abstract": "A practical agent framework",
        "categories": ["cs.AI"],
        "keywords": [],
        "source": "arXiv",
        "url": "https://arxiv.org/abs/2604.00001",
        "code_url": "",
        "benchmark_url": "",
    }]
    overrides = {
        "https://arxiv.org/abs/2604.00001": {
            "score": 88.8,
            "reason": "强工程价值",
            "matched_topics": ["ai-agent"]
        }
    }
    scored = score_papers.score_papers(papers, llm_overrides=overrides)
    assert scored[0]["score"] == 88.8
    assert scored[0]["decision"] == "重点学习"
    assert scored[0]["matched_topics"] == ["ai-agent"]
