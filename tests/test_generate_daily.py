import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel_path: str):
    p = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


generate_daily = load_module("generate_daily", "scripts/generate_daily.py")


def test_generate_daily_empty_papers_not_blank():
    report, deep_dive = generate_daily.generate_daily_report([], "2026-04-28")
    assert "前沿理论驱动技术雷达日报 - 2026-04-28" in report
    assert "## 1. 今日最值得关注的前沿论文" in report
    assert "## 11. 最终结论" in report
    assert deep_dive["title"].startswith("[占位]")
