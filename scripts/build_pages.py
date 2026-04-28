#!/usr/bin/env python3
"""论文价值发现系统 - Pages 数据构建脚本"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY_DIR = os.path.join(PROJECT_ROOT, 'daily')
DOCS_DATA_DIR = os.path.join(PROJECT_ROOT, 'docs', 'data')

VALUE_LABELS = {'immediate':'即时价值','trend':'趋势价值','long_tail':'长尾价值','ignore':'暂时忽略'}

MERMAID_VALUE_DISCOVERY = '''flowchart TD
P[论文] --> V[价值判断]
V --> I[即时价值]
V --> T[趋势价值]
V --> L[长尾价值]
V --> N[暂时忽略]
I --> A[立即学习 / 试点]
T --> R[纳入趋势雷达 / 持续观察]
L --> S[沉淀启发 / 加入长尾库]
N --> X[保留最小索引]'''

MERMAID_EVIDENCE = '''flowchart TD
P[论文] --> Q[底层问题]
P --> M[新命题 / 新方法]
P --> G[研究位置]
P --> E[工程可验证性]
P --> C[趋势关联]
P --> L[长尾价值]'''

MERMAID_ACTIONS = '''flowchart TD
V[价值类型] --> I[即时价值]
V --> T[趋势价值]
V --> L[长尾价值]
V --> N[暂时忽略]
I --> I1[30分钟学习]
I --> I2[2小时实践]
I --> I3[1周研究]
T --> T1[纳入趋势雷达]
T --> T2[设置观察问题]
T --> T3[周期复盘]
L --> L1[加入长尾库]
L --> L2[标注触发条件]
L --> L3[沉淀 Prompt / Skill / Checklist]
N --> N1[记录忽略理由]
N --> N2[保留最小索引]'''


def parse_front_matter(text):
    if not text.startswith('---\n'):
        return {}, text
    end = text.find('\n---\n', 4)
    if end == -1:
        return {}, text
    meta = {}
    for raw in text[4:end].splitlines():
        raw = raw.strip()
        if not raw or raw.startswith('#') or ':' not in raw:
            continue
        k, v = raw.split(':', 1)
        v = v.strip().strip('"').strip("'")
        if v.startswith('[') and v.endswith(']'):
            meta[k.strip()] = [x.strip().strip('"').strip("'") for x in v[1:-1].split(',') if x.strip()]
        else:
            meta[k.strip()] = v
    return meta, text[end+5:]


def markdown_to_simple_html(md_text):
    html_lines = []
    in_list = False
    in_table = False

    def render_inline(text):
        text = re.sub(r'\]\(\./([a-z0-9-]+)\.md\)', r'](trend-detail.html?id=\1)', text)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        return text

    for line in md_text.split('\n'):
        if line.strip() == '---':
            if in_list:
                html_lines.append('</ul>'); in_list = False
            if in_table:
                html_lines.append('</tbody></table></div>'); in_table = False
            continue
        if line.startswith('# '):
            if in_list:
                html_lines.append('</ul>'); in_list = False
            if in_table:
                html_lines.append('</tbody></table></div>'); in_table = False
            html_lines.append(f'<h2>{render_inline(line[2:])}</h2>')
        elif line.startswith('## '):
            if in_list:
                html_lines.append('</ul>'); in_list = False
            if in_table:
                html_lines.append('</tbody></table></div>'); in_table = False
            html_lines.append(f'<h3>{render_inline(line[3:])}</h3>')
        elif line.startswith('### '):
            if in_list:
                html_lines.append('</ul>'); in_list = False
            if in_table:
                html_lines.append('</tbody></table></div>'); in_table = False
            html_lines.append(f'<h4>{render_inline(line[4:])}</h4>')
        elif line.startswith('- '):
            if in_table:
                html_lines.append('</tbody></table></div>'); in_table = False
            if not in_list:
                html_lines.append('<ul>'); in_list = True
            html_lines.append(f'<li>{render_inline(line[2:])}</li>')
        elif line.strip().startswith('|') and '---' not in line:
            if in_list:
                html_lines.append('</ul>'); in_list = False
            if not in_table:
                html_lines.append('<div class="table-wrapper"><table><tbody>'); in_table = True
            cells = [render_inline(c.strip()) for c in line.split('|')[1:-1]]
            html_lines.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
        elif line.strip().startswith('|') and set(line.replace('|', '').replace('-', '').strip()) == set():
            continue
        elif line.strip() == '':
            if in_list:
                html_lines.append('</ul>'); in_list = False
        else:
            if in_list:
                html_lines.append('</ul>'); in_list = False
            if in_table:
                html_lines.append('</tbody></table></div>'); in_table = False
            html_lines.append(f'<p>{render_inline(line)}</p>')
    if in_list:
        html_lines.append('</ul>')
    if in_table:
        html_lines.append('</tbody></table></div>')
    return '\n'.join(html_lines)


def save_json(rel_path, data):
    path = Path(DOCS_DATA_DIR) / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[build] 已生成: {path}')


def load_json(name, key):
    path = Path(DOCS_DATA_DIR) / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding='utf-8')).get(key, [])


def build_paper_details(papers, long_tail_items, trends):
    trend_map = {t['slug']: t for t in trends}
    long_tail_map = {i['id']: i for i in long_tail_items}
    aggregate = {'updated_at': datetime.now().isoformat(), 'papers': {}}
    by_id = {}
    for p in papers:
        related_trends = [slug for slug in p.get('related_trends', []) if slug in trend_map]
        detail = {
            'id': p['id'],
            'title': p['title'],
            'authors': p.get('authors', []),
            'source': p.get('source', ''),
            'published': p.get('published', ''),
            'url': p.get('url', ''),
            'pdf_url': p.get('pdf_url', ''),
            'code_url': p.get('code_url', ''),
            'benchmark_url': p.get('benchmark_url', ''),
            'paperswithcode_url': p.get('paperswithcode_url', ''),
            'openreview_url': p.get('openreview_url', ''),
            'first_seen_date': p.get('first_seen_date', ''),
            'first_deep_dive_daily': p.get('first_deep_dive_daily', ''),
            'value_type': p.get('value_type', 'ignore'),
            'value_type_label': p.get('value_type_label', '待定'),
            'value_scores': {
                'novelty': p.get('score_breakdown', {}).get('novelty', 0),
                'relevance': p.get('score_breakdown', {}).get('relevance', 0),
                'evidence': p.get('score_breakdown', {}).get('evidence_strength', 0),
                'engineering_testability': p.get('score_breakdown', {}).get('engineering_testability', 0),
                'trend_signal': p.get('score_breakdown', {}).get('trend_signal', 0),
                'long_tail_potential': p.get('score_breakdown', {}).get('long_tail_potential', 0),
                'actionability': p.get('score_breakdown', {}).get('actionability', 0),
                'noise_risk': p.get('score_breakdown', {}).get('noise_risk', 0)
            },
            'score': p.get('score', 0),
            'decision': p.get('decision', '待定'),
            'one_line_judgement': p.get('one_line_judgement', ''),
            'one_line_essence': p.get('llm_reason') or p.get('brief_cn', ''),
            'core_problem': '如何把论文信号转成能指导架构、Agent、评测与平台实践的研究资产。',
            'new_claim_or_method': (p.get('llm_reason') or p.get('brief_cn', ''))[:180],
            'research_position': 'benchmark' if 'benchmark' in (p.get('title','') + p.get('abstract','')).lower() else ('long_tail_insight' if p.get('value_type') == 'long_tail' else 'source_paper'),
            'engineering_testability': {
                'has_code': bool(p.get('code_url')),
                'has_benchmark': bool(p.get('benchmark_url')),
                'can_reproduce': bool(p.get('code_url') or p.get('benchmark_url')),
                'minimum_experiment': '摘要精读 + Prompt 试验 / 评测脚本 / 最小 PoC',
                'engineering_scenarios': ['AI Agent', 'Context Engineering', '评测治理']
            },
            'trend_relation': {
                'status': p.get('trend_status', 'noise'),
                'related_trends': related_trends,
                'evidence': ['论文主题匹配固定研究方向'],
                'uncertainties': ['是否会出现更多开源实现与生产案例']
            },
            'long_tail': {
                'why_save': long_tail_map.get(p['id'], {}).get('why_save', p.get('long_tail_summary', '当前未列入长尾主清单。')),
                'future_trigger': [long_tail_map.get(p['id'], {}).get('future_trigger', p.get('future_trigger', ''))],
                'possible_use_cases': ['Prompt 设计', 'Skill 草案', '评测方法', '架构模式'],
                'reusable_assets': ['Prompt', 'Skill', 'Checklist', '模板'],
                'revisit_condition': '出现开源实现 / 高质量引用 / benchmark 收录 / 与当前场景交集增强',
                'revisit_date': long_tail_map.get(p['id'], {}).get('revisit_date', '')
            },
            'insights': {
                'system_design': ['先判断价值类型，再决定系统性投入。'],
                'agent_engineering': ['为 Agent 建立论文价值路由器。'],
                'dev_process': ['论文输出应沉淀为可执行资产。'],
                'evaluation': ['同时看方法与证据质量。'],
                'platform_engineering': ['长尾资产库可降低重复检索成本。'],
                'personal_learning': ['优先读能转化为未来复利的论文。']
            },
            'actions': {
                'immediate_actions': ['今天读摘要与方法', '今天试最小实验', '一周内沉淀为 Skill / Checklist'] if p.get('value_type') == 'immediate' else [],
                'trend_actions': ['纳入趋势雷达', '观察代码 / benchmark / 工程博客', '7-30 天复盘'] if p.get('value_type') == 'trend' else [],
                'long_tail_actions': ['加入长尾库', '标注未来触发条件', '先沉淀 Prompt / Skill 草案'] if p.get('value_type') == 'long_tail' else [],
                'ignore_reason': '新意弱、证据弱、相关性有限，当前不建议投入。' if p.get('value_type') == 'ignore' else ''
            },
            'references': p.get('links', []),
            'detail_path': p.get('detail_path', ''),
            'daily_path': f"daily-detail.html?date={p.get('first_deep_dive_daily','')}" if p.get('first_deep_dive_daily') else '',
            'trend_paths': [f"trend-detail.html?id={slug}" for slug in related_trends],
            'long_tail_path': 'long-tail.html',
            'mermaid': {'value_discovery': MERMAID_VALUE_DISCOVERY, 'evidence': MERMAID_EVIDENCE, 'actions': MERMAID_ACTIONS}
        }
        save_json(f'paper-details/{p["id"]}.json', detail)
        aggregate['papers'][p['id']] = detail
        by_id[p['id']] = detail
    save_json('paper-details.json', aggregate)
    return by_id


def build_daily_details(papers_by_id):
    aggregate = {'updated_at': datetime.now().isoformat(), 'dailies': {}}
    for filepath in sorted(glob.glob(os.path.join(DAILY_DIR, '*', '*.md')), reverse=True):
        date_str = Path(filepath).stem
        raw = Path(filepath).read_text(encoding='utf-8')
        meta, body = parse_front_matter(raw)
        deep_title = meta.get('deep_dive_title', '')
        deep = next((p for p in papers_by_id.values() if p.get('title') == deep_title), None)
        candidates = [p for p in papers_by_id.values() if p.get('first_seen_date') == date_str][:5] or list(papers_by_id.values())[:5]
        long_tail_items = [p for p in candidates if p.get('value_type') == 'long_tail'][:3]
        ignored = [p for p in candidates if p.get('value_type') == 'ignore'][:3]
        detail = {
            'date': date_str,
            'title': meta.get('title') or f'论文价值发现日报 - {date_str}',
            'deep_dive_id': deep.get('id') if deep else '',
            'deep_dive_title': deep_title,
            'value_type': meta.get('value_type', deep.get('value_type') if deep else 'ignore'),
            'value_type_label': VALUE_LABELS.get(meta.get('value_type', deep.get('value_type') if deep else 'ignore'), '待定'),
            'decision': meta.get('decision', deep.get('decision') if deep else '待定'),
            'daily_action': meta.get('daily_action', '完成摘要精读与最小实验设计'),
            'score': deep.get('score', 0) if deep else 0,
            'trend_stage': deep.get('trend_relation', {}).get('status', '待定') if deep else '待定',
            'one_line_judgement': deep.get('one_line_judgement', '待补充价值判断') if deep else '待补充价值判断',
            'max_uncertainty': meta.get('max_uncertainty', '缺少多源工程证据'),
            'conclusion_lines': [
                f"今天最值得看的是《{deep_title}》。" if deep_title else '今天最值得看的论文待补充。',
                f"它属于{VALUE_LABELS.get(meta.get('value_type', ''), '待定')}，因为同时具备较高的相关性与研究资产价值。",
                f"今天建议动作：{meta.get('daily_action', '完成摘要精读与最小实验设计')}。",
                f"最大不确定性：{meta.get('max_uncertainty', '缺少多源工程证据')}。"
            ],
            'candidate_papers': [
                {
                    'id': p['id'],
                    'title': p['title'],
                    'detail_path': p['detail_path'],
                    'direction': ' / '.join(p.get('matched_topics', [])[:2]) or '未分类',
                    'value_type': p['value_type'],
                    'value_type_label': p['value_type_label'],
                    'score': p['score'],
                    'decision': p['decision'],
                    'has_code': bool(p.get('code_url')),
                    'has_benchmark': bool(p.get('benchmark_url')),
                    'worth_deep_dive': p['score'] >= 70
                } for p in candidates
            ],
            'deep_dive': deep,
            'long_tail_saved': [
                {
                    'id': p['id'],
                    'title': p['title'],
                    'detail_path': p['detail_path'],
                    'why_save': p.get('long_tail', {}).get('why_save', ''),
                    'future_trigger': (p.get('long_tail', {}).get('future_trigger') or ['待观察'])[0],
                    'possible_use_cases': ['Prompt 设计', 'Skill 草案', '评测方法', '架构模式'],
                    'reusable_assets': ['Prompt', 'Skill', 'Checklist', '评测方法'],
                    'revisit_date': (datetime.fromisoformat(date_str) + timedelta(days=21)).date().isoformat()
                } for p in long_tail_items
            ],
            'ignore_reasons': [f"{p['title']}：新意弱、证据弱或当前相关性有限。" for p in ignored] or ['暂无明确忽略样本，但忽略标准仍需保留。'],
            'insights': {
                'system_design': ['先做价值路由，再决定是否深入工程推导。'],
                'agent_engineering': ['让 Agent 先判断“今天值不值得试”。'],
                'dev_process': ['论文筛选应产出 Prompt / Skill / Checklist。'],
                'evaluation': ['把“是否值得投入”也纳入评测流程。'],
                'platform_engineering': ['长尾库是低成本知识保留层。'],
                'personal_learning': ['优先读可沉淀资产的论文。']
            },
            'actions': {
                'immediate_actions': ['30 分钟学习', '2 小时实践', '1 周研究'] if meta.get('value_type') == 'immediate' else [],
                'trend_actions': ['纳入趋势雷达', '设置观察问题', '周期复盘'] if meta.get('value_type') == 'trend' else [],
                'long_tail_actions': ['加入长尾库', '设置触发条件', '沉淀 Prompt / Skill / Checklist'] if meta.get('value_type') == 'long_tail' else [],
                'ignore_reason': '仅保留最小索引。' if meta.get('value_type') == 'ignore' else ''
            },
            'references': deep.get('references', []) if deep else [],
            'mermaid': {'value_discovery': MERMAID_VALUE_DISCOVERY, 'evidence': MERMAID_EVIDENCE, 'actions': MERMAID_ACTIONS},
            'raw_markdown_html': markdown_to_simple_html(body)
        }
        save_json(f'daily-details/{date_str}.json', detail)
        aggregate['dailies'][date_str] = detail
    save_json('daily-details.json', aggregate)


def build_trend_details(trends, papers_by_id):
    aggregate = {'updated_at': datetime.now().isoformat(), 'trends': {}}
    paper_list = list(papers_by_id.values())
    for trend in trends:
        slug = trend['slug']
        related_papers = [p for p in paper_list if slug in (p.get('trend_relation', {}).get('related_trends') or [])]
        detail = {
            'slug': slug,
            'title': trend['title'],
            'stage': trend.get('stage', '待定'),
            'updated_at': trend.get('updated_at', ''),
            'key_insight': trend.get('key_insight', ''),
            'paper_count': trend.get('paper_count', 0),
            'practice_count': trend.get('practice_count', 0),
            'path': trend.get('path', f'trend-detail.html?id={slug}'),
            'markdown_path': trend.get('markdown_path', f'trends/{slug}.md'),
            'related_papers': [
                {
                    'id': p['id'],
                    'title': p['title'],
                    'detail_path': p.get('detail_path', ''),
                    'value_type': p.get('value_type', ''),
                    'value_type_label': p.get('value_type_label', ''),
                    'score': p.get('score', 0),
                    'decision': p.get('decision', ''),
                    'one_line_judgement': p.get('one_line_judgement', ''),
                    'source': p.get('source', ''),
                    'published': p.get('published', ''),
                    'brief_cn': p.get('brief_cn', ''),
                    'code_url': p.get('code_url', ''),
                    'benchmark_url': p.get('benchmark_url', ''),
                    'paperswithcode_url': p.get('paperswithcode_url', ''),
                    'url': p.get('url', ''),
                    'pdf_url': p.get('pdf_url', ''),
                }
                for p in sorted(related_papers, key=lambda item: item.get('score', 0), reverse=True)
            ],
            'value_distribution': {
                'immediate': sum(1 for p in related_papers if p.get('value_type') == 'immediate'),
                'trend': sum(1 for p in related_papers if p.get('value_type') == 'trend'),
                'long_tail': sum(1 for p in related_papers if p.get('value_type') == 'long_tail'),
                'ignore': sum(1 for p in related_papers if p.get('value_type') == 'ignore'),
            },
            'top_paper': next(({
                'id': p['id'],
                'title': p['title'],
                'detail_path': p.get('detail_path', ''),
                'score': p.get('score', 0),
                'decision': p.get('decision', ''),
                'value_type': p.get('value_type', ''),
                'value_type_label': p.get('value_type_label', ''),
                'one_line_judgement': p.get('one_line_judgement', ''),
            } for p in sorted(related_papers, key=lambda item: item.get('score', 0), reverse=True)), None),
            'mermaid': {
                'value_discovery': MERMAID_VALUE_DISCOVERY,
                'evidence': MERMAID_EVIDENCE,
                'actions': MERMAID_ACTIONS,
            },
        }
        markdown_path = Path(PROJECT_ROOT) / 'trends' / f'{slug}.md'
        if markdown_path.exists():
            raw = markdown_path.read_text(encoding='utf-8')
            meta, body = parse_front_matter(raw)
            detail['priority_topics'] = meta.get('priority_topics', [])
            detail['raw_markdown_html'] = markdown_to_simple_html(body)
        else:
            detail['priority_topics'] = []
            detail['raw_markdown_html'] = '<p>暂无趋势详情。</p>'
        save_json(f'trend-details/{slug}.json', detail)
        aggregate['trends'][slug] = detail
    save_json('trend-details.json', aggregate)


def main():
    papers = load_json('paper-index.json', 'papers')
    long_tail_items = load_json('long-tail-index.json', 'items')
    trends = load_json('trend-index.json', 'trends')
    papers_by_id = build_paper_details(papers, long_tail_items, trends)
    build_daily_details(papers_by_id)
    build_trend_details(trends, papers_by_id)
    print('[build] Pages 数据构建完成！')
    return 0


if __name__ == '__main__':
    sys.exit(main())
