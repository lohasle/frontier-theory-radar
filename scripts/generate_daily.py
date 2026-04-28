#!/usr/bin/env python3
"""论文价值发现系统 - 日报生成脚本"""
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(PROJECT_ROOT, "papers")
DAILY_DIR = os.path.join(PROJECT_ROOT, "daily")

VALUE_LABELS = {
    "immediate": "即时价值",
    "trend": "趋势价值",
    "long_tail": "长尾价值",
    "ignore": "暂时忽略",
}


def load_papers(target_date):
    year = target_date[:4]
    papers_path = os.path.join(PAPERS_DIR, year, f"{target_date}-papers.json")
    if not os.path.exists(papers_path):
        return []
    return json.loads(Path(papers_path).read_text(encoding="utf-8")).get("papers", [])


def load_analysis(target_date):
    year = target_date[:4]
    p = Path(PAPERS_DIR) / year / f"{target_date}-analysis.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def paper_link(label, url):
    return f"[{label}]({url})" if url and url.startswith("http") else (url or "暂无")


def paper_links_line(paper):
    chunks = []
    for label, key in [("arXiv", "url"), ("PDF", "pdf_url"), ("OpenReview", "openreview_url"), ("Code", "code_url"), ("Benchmark", "benchmark_url"), ("Papers with Code", "paperswithcode_url")]:
        chunks.append(f"- **{label}：** {paper_link(label, paper.get(key, ''))}")
    return "\n".join(chunks)


def build_paper_table(papers):
    rows = []
    for p in papers[:5]:
        rows.append(
            f"| [{p.get('title','未知')}]({p.get('url','#')}) | {' / '.join(p.get('matched_topics',[])[:2]) or '未分类'} | {VALUE_LABELS.get(p.get('value_type'),'待定')} | {p.get('score',0):.1f} | {p.get('decision','待定')} | {'是' if p.get('code_url') else '否'} | {'是' if p.get('benchmark_url') else '否'} | {'是' if p.get('score',0) >= 70 else '否'} |"
        )
    return "\n".join(rows)


def choose_long_tail(papers):
    tails = [p for p in papers if p.get('value_type') == 'long_tail']
    return tails[:3] if tails else [p for p in papers if p.get('decision') in ('持续观察', '轻量试点')][:3]


def choose_ignore_reasons(papers):
    ignored = [p for p in papers if p.get('value_type') == 'ignore' or p.get('decision') == '暂时忽略']
    reasons = [f"- [{p.get('title')}]({p.get('url')})：新意弱 / 证据弱 / 当前相关性有限。" for p in ignored[:3]]
    return "\n".join(reasons) or '- 当前样本中暂无明确噪声论文，但仍需保留忽略标准。'


def generate_daily_report(papers, target_date):
    analysis = load_analysis(target_date)
    deep = papers[0] if papers else {
        'title': '[占位] 今日无可用论文数据', 'url': '', 'source': 'placeholder', 'authors': [], 'published': target_date,
        'score': 0, 'decision': '暂时忽略', 'value_type': 'ignore', 'abstract': '今日论文抓取失败或无新论文。', 'links': []
    }
    value_type = deep.get('value_type', 'ignore')
    value_label = VALUE_LABELS.get(value_type, '待定')
    stage = {'trend':'上升','immediate':'萌芽','long_tail':'长尾观察','ignore':'噪声'}.get(value_type, '萌芽')
    long_tail = choose_long_tail(papers)
    candidate_table = build_paper_table(papers)
    summary = analysis.get('summary_markdown') or (
        f"- **今天最值得看什么：** [{deep.get('title')}]({deep.get('url')})。\n"
        f"- **为什么值得看：** {deep.get('llm_reason') or '它同时具备问题重要性、工程可验证性和研究资产转化价值。'}\n"
        f"- **它属于什么价值类型：** {value_label}。\n"
        f"- **今天该做什么：** 先读摘要与方法，随后验证是否能沉淀为 Prompt / Skill / Checklist。\n"
        f"- **最大不确定性：** {analysis.get('uncertainty') or '是否存在可核验代码、benchmark 与多源趋势证据。'}"
    )
    deep_dive_section = analysis.get('deep_dive_markdown') or (
        f"- **一句话本质：** {deep.get('llm_reason') or '提出了值得快速判断是否可转化为工程资产的新方法。'}\n"
        f"- **底层问题：** {analysis.get('core_problem') or '如何在有限注意力下快速分辨哪些论文值得今天就投入。'}\n"
        f"- **新命题 / 新方法 / 新证据：** {analysis.get('new_claim_or_method') or '通过新的方法路径或评测视角提升价值密度。'}\n"
        f"- **研究位置：** {analysis.get('research_position') or '源头论文 / 改进论文之间，仍需后续核验。'}\n"
        f"- **工程可验证性：** {'有明确代码入口，可安排最小实验。' if deep.get('code_url') else '暂缺代码，但可从提示词、评测或架构思路侧做最小验证。'}\n"
        f"- **趋势关联：** {('值得纳入趋势雷达继续观察。' if value_type == 'trend' else '更偏即时试验或长尾保存。')}\n"
        f"- **长尾价值：** {analysis.get('long_tail_value') or '即使短期不火，也可能沉淀为未来可复用的研究资产。'}\n"
        f"- **启发：** {analysis.get('one_line_insight') or '先做价值路由，再决定是否投入深读与工程搜索。'}\n"
        f"- **行动建议：** {analysis.get('today_action') or '今天完成摘要精读 + 最小验证计划。'}"
    )
    insights = analysis.get('insights_markdown') or dedent('''### 系统设计启发
- 先做价值路由，而不是默认每篇都深挖到同样层级。

### Agent 工程启发
- 让 Agent 先判断“今天值不值得试”，再决定是否展开复杂研究链路。

### 研发流程启发
- 论文筛选要能输出 Prompt / Skill / Checklist，而不是只停留在摘要解释。

### 评测方法启发
- 把“是否值得继续投入”本身也当作一个评测对象。

### 平台工程启发
- 长尾库让团队能低成本保留未来资产，不被短期热度绑架。

### 个人学习启发
- 优先读能形成研究资产的论文，而不是单纯追热度。''')

    if value_type == 'immediate':
        action_block = dedent('''- **30 分钟学习任务：** 读摘要、方法、实验设定，记下 3 个可验证假设。
- **2 小时实践任务：** 做最小实验、Prompt 试验或评测脚本草图。
- **1 周研究任务：** 沉淀为 Prompt / Skill / Checklist / 模板，并跟踪复现结果。''')
    elif value_type == 'trend':
        action_block = dedent('''- **纳入趋势雷达：** 记录为需要连续观察的方向。
- **设置观察问题：** 它是否会出现代码、benchmark、工程博客或多篇跟进论文？
- **连续观察周期：** 7-30 天滚动复盘一次。''')
    elif value_type == 'long_tail':
        action_block = dedent('''- **加入长尾库：** 先保存，不急于投入大量精力。
- **设置未来触发条件：** 开源实现、benchmark 收录、被高质量论文引用、成本下降。
- **沉淀资产：** 先提炼成 Prompt / Skill / Checklist / 模板草稿。''')
    else:
        action_block = dedent('''- **保留最小索引：** 记录标题、来源、分数与忽略理由。
- **忽略理由：** 当前证据弱、相关性低或难以转化为研究资产。
- **后续策略：** 除非出现强外部信号，否则不继续投入。''')

    long_tail_md = []
    for p in long_tail:
        revisit = (datetime.fromisoformat(target_date) + timedelta(days=21)).date().isoformat()
        long_tail_md.append(
            f"### [{p.get('title')}]({p.get('url')})\n"
            f"- **为什么现在不火也值得保存：** {p.get('llm_reason') or '具备方法抽象、评测启发或反证价值。'}\n"
            f"- **未来触发条件：** 出现开源实现 / 被高质量论文引用 / 进入 benchmark。\n"
            f"- **可能应用场景：** Prompt 设计、Agent workflow、评测治理、系统设计。\n"
            f"- **可沉淀资产：** Prompt / Skill / Checklist / 架构模式 / 评测方法。\n"
            f"- **建议复盘时间：** {revisit}"
        )
    long_tail_section = "\n\n".join(long_tail_md) if long_tail_md else '暂无长尾保存候选。'
    refs = paper_links_line(deep)
    now = datetime.now().isoformat()
    report = f'''---
date: {target_date}
title: 论文价值发现日报 - {target_date}
decision: {deep.get('decision','待定')}
value_type: {value_type}
stage: {stage}
deep_dive_title: {deep.get('title','')}
deep_dive_url: {deep.get('url','')}
daily_action: {analysis.get('today_action') or '完成摘要精读与最小实验设计'}
max_uncertainty: {analysis.get('uncertainty') or '缺少多源工程证据'}
---

# 论文价值发现日报 - {target_date}

> 从论文出发，快速判断即时价值、趋势价值和长尾价值，沉淀可复用研究资产。
> ⚠️ **注意：这是初始化样例，后续运行会替换为真实数据。**

## 1. 标题区
- **今日最值得关注论文：** [{deep.get('title')}]({deep.get('url')})
- **价值类型：** {value_label}
- **今日建议动作：** {analysis.get('today_action') or '完成摘要精读与最小实验设计'}
- **分数：** {deep.get('score',0)}
- **趋势阶段：** {stage}

## 2. 先说结论
{summary}

## 3. 今日候选论文表

| 论文标题 | 方向 | 价值类型 | 分数 | 判断 | 是否有代码 | 是否有 Benchmark | 是否值得深挖 |
|---|---|---|---:|---|---|---|---|
{candidate_table}

## 4. 今日深挖论文

{deep_dive_section}

## 5. 今日长尾保存

{long_tail_section}

## 6. 今日忽略理由

{choose_ignore_reasons(papers)}

## 7. 启发

{insights}

## 8. 行动建议

{action_block}

## 9. 引用与延伸阅读

{refs}

## 10. 最终结论
- **结论：** {deep.get('decision','待定')}
- **价值类型：** {value_label}
- **原因：** {deep.get('llm_reason') or '同时具备较高相关性、可验证性或长尾资产价值。'}
- **最大不确定性：** {analysis.get('uncertainty') or '是否有后续工程证据与多源跟进。'}
- **下一步动作：** {analysis.get('next_action') or '更新趋势页、长尾库与论文详情档案。'}

> 生成时间：{now}
> 数据来源：arXiv API + 固定源配置
> 状态：{'Hermes 推理增强' if analysis else '初始化样例/规则生成'}
'''
    return report, deep


def save_daily_report(report, target_date):
    output_dir = os.path.join(DAILY_DIR, target_date[:4])
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{target_date}.md")
    Path(output_path).write_text(report, encoding='utf-8')
    print(f"[generate] 日报已保存到: {output_path}")
    return output_path


def main():
    print('=' * 60)
    print('论文价值发现系统 - 日报生成')
    print('=' * 60)
    target_date = date.today().isoformat()
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    papers = load_papers(target_date)
    print(f"[generate] 加载 {len(papers)} 篇论文")
    report, deep_dive = generate_daily_report(papers, target_date)
    output_path = save_daily_report(report, target_date)
    print(f"[generate] 深挖论文: {deep_dive.get('title', 'N/A')}")
    print(f"[generate] 完成！日报已保存到: {output_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
