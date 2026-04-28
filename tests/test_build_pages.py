import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel_path: str):
    p = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build_pages = load_module("build_pages", "scripts/build_pages.py")


def test_parse_front_matter_basic():
    text = """---
title: demo
stage: 上升
tags: [agent, memory]
---
# Body
"""
    meta, body = build_pages.parse_front_matter(text)
    assert meta["title"] == "demo"
    assert meta["stage"] == "上升"
    assert meta["tags"] == ["agent", "memory"]
    assert body.strip().startswith("# Body")


def test_markdown_to_simple_html_external_link_attrs():
    md = "- [arXiv](https://arxiv.org/abs/1234.5678)"
    html = build_pages.markdown_to_simple_html(md)
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
