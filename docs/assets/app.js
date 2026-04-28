const DATA_BASE = './data';

const valueTypeLabels = { immediate: '即时价值', trend: '趋势价值', long_tail: '长尾价值', ignore: '暂时忽略' };
const trendStatusLabels = { emerging: '萌芽', rising: '上升', mainstream: '主流化', overheated: '过热', noise: '噪声', long_tail_watch: '长尾观察' };

function q(key) { return new URLSearchParams(window.location.search).get(key); }
function el(id) { return document.getElementById(id); }
function escapeHtml(v) { return String(v ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
function formatDate(dateStr) { return dateStr || '未知'; }

async function loadJSON(name) {
  try {
    const res = await fetch(`${DATA_BASE}/${name}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error(`loadJSON failed: ${name}`, error);
    return null;
  }
}

function setActiveNav() {
  const page = document.body.dataset.page;
  document.querySelectorAll('.navbar-links a').forEach(a => {
    if (a.dataset.page === page) a.classList.add('active');
  });
}

function initMobileMenu() {
  const btn = document.querySelector('.navbar-toggle');
  const menu = document.querySelector('.navbar-links');
  if (!btn || !menu) return;
  btn.addEventListener('click', () => menu.classList.toggle('open'));
}

function badgeClass(name = '') {
  if (['重点学习', '即时价值', 'immediate'].includes(name)) return 'badge-immediate';
  if (['轻量试点', '趋势价值', 'trend', 'rising'].includes(name)) return 'badge-trend';
  if (['持续观察', '长尾价值', 'long_tail', 'emerging', 'long_tail_watch'].includes(name)) return 'badge-long-tail';
  if (['主流化', 'mainstream'].includes(name)) return 'badge-mainstream';
  if (['过热', 'overheated'].includes(name)) return 'badge-overheated';
  return 'badge-ignore';
}

function renderBadge(text, klass) { return `<span class="badge ${klass}">${escapeHtml(text)}</span>`; }
function linkButton(label, url) { return url ? `<a class="paper-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>` : `<span class="paper-link disabled">${escapeHtml(label || '暂无')}</span>`; }
function maybeArray(v) { return Array.isArray(v) ? v : []; }

function renderPaperLinks(paper) {
  return `<div class="link-row">
    ${linkButton('arXiv', paper.url)}
    ${linkButton('PDF', paper.pdf_url)}
    ${linkButton('OpenReview', paper.openreview_url)}
    ${linkButton('Code', paper.code_url)}
    ${linkButton('Benchmark', paper.benchmark_url)}
    ${linkButton('Papers with Code', paper.paperswithcode_url)}
  </div>`;
}

function showState(id, html) { const node = el(id); if (node) node.innerHTML = html; }
function showLoading(id) { showState(id, `<div class="loading"><div class="loading-spinner"></div><div>正在加载...</div></div>`); }
function showError(id, msg) { showState(id, `<div class="error-state">${escapeHtml(msg)}</div>`); }
function showEmpty(id, msg) { showState(id, `<div class="empty-state">${escapeHtml(msg)}</div>`); }

function renderMermaidShell(code) {
  return `<div class="mermaid-shell"><div class="mermaid">${escapeHtml(code)}</div><pre class="mermaid-fallback">${escapeHtml(code)}</pre></div>`;
}

async function enhanceMermaid() {
  const shells = document.querySelectorAll('.mermaid-shell');
  if (!shells.length) return;
  if (!window.mermaid) {
    shells.forEach(shell => {
      const fallback = shell.querySelector('.mermaid-fallback');
      if (fallback) fallback.style.display = 'block';
      const node = shell.querySelector('.mermaid');
      if (node) node.style.display = 'none';
    });
    return;
  }
  try {
    window.mermaid.initialize({ startOnLoad: false, theme: 'base', securityLevel: 'loose', themeVariables: { primaryColor: '#ede9fe', primaryTextColor: '#1e1b4b', primaryBorderColor: '#c4b5fd', lineColor: '#7c3aed', secondaryColor: '#ecfeff', tertiaryColor: '#f8fafc' } });
    await window.mermaid.run({ nodes: document.querySelectorAll('.mermaid') });
    document.querySelectorAll('.mermaid-fallback').forEach(n => n.style.display = 'none');
  } catch (e) {
    console.error('Mermaid render failed', e);
    document.querySelectorAll('.mermaid-fallback').forEach(n => n.style.display = 'block');
  }
}

function renderDailySummaryCard(item) {
  return `<div class="card">
    <div class="card-meta">${escapeHtml(item.date || '')}</div>
    <div class="card-title"><a href="${escapeHtml(item.path || '#')}">${escapeHtml(item.deep_dive_title || '待分析')}</a></div>
    <div class="badge-group" style="margin-bottom:10px">
      ${renderBadge(item.value_type_label || valueTypeLabels[item.value_type] || '待定', badgeClass(item.value_type))}
      ${renderBadge(item.decision || '待定', badgeClass(item.decision))}
    </div>
    <div class="daily-card-insight">${escapeHtml(item.one_line_judgement || '待补充价值判断')}</div>
    <div class="muted">建议动作：${escapeHtml(item.daily_action || '待补充')}</div>
  </div>`;
}

async function renderIndexPage() {
  showLoading('index-root');
  const data = await loadJSON('latest.json');
  if (!data) return showError('index-root', '首页数据加载失败，请稍后重试。');
  const top = data.top_paper || {};
  const latest = data.latest_daily || {};
  const longTail = maybeArray(data.long_tail_highlights);
  const recent = maybeArray(data.recent_dailies);
  const trends = await loadJSON('trend-index.json');
  const trendCards = maybeArray(trends?.trends).slice(0, 4).map(t => `
    <div class="card">
      <div class="card-title">${escapeHtml(t.title)}</div>
      <div class="badge-group" style="margin-bottom:10px">${renderBadge(t.stage || '待定', badgeClass(t.stage || ''))}</div>
      <div class="muted">关联论文：${escapeHtml(t.paper_count || 0)} · 最近更新：${escapeHtml(t.updated_at || '')}</div>
      <p>${escapeHtml(t.key_insight || '待补充')}</p>
      <a class="btn btn-secondary btn-sm" href="${escapeHtml(t.path || '#')}">查看趋势详情</a>
    </div>
  `).join('');
  const root = `
    <section class="hero">
      <div class="hero-badge"><span class="dot"></span>论文价值发现工作台</div>
      <h1>${escapeHtml(data.site_title || '前沿理论驱动技术雷达日报')}</h1>
      <p>${escapeHtml(data.site_subtitle || '')}</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="${escapeHtml(latest.path || 'daily.html')}">今日日报</a>
        <a class="btn btn-secondary" href="papers.html">论文库</a>
        <a class="btn btn-secondary" href="long-tail.html">长尾库</a>
        <a class="btn btn-secondary" href="trends.html">趋势雷达</a>
      </div>
    </section>

    <section class="kpi-grid">
      <div class="kpi-card"><div class="kpi-number">${escapeHtml(data.value_distribution?.immediate ?? 0)}</div><div class="kpi-label">即时价值</div></div>
      <div class="kpi-card"><div class="kpi-number">${escapeHtml(data.value_distribution?.trend ?? 0)}</div><div class="kpi-label">趋势价值</div></div>
      <div class="kpi-card"><div class="kpi-number">${escapeHtml(data.value_distribution?.long_tail ?? 0)}</div><div class="kpi-label">长尾价值</div></div>
      <div class="kpi-card"><div class="kpi-number">${escapeHtml(data.value_distribution?.ignore ?? 0)}</div><div class="kpi-label">暂时忽略</div></div>
    </section>

    <section class="section columns-2">
      <div class="card">
        <div class="section-title"><span class="section-icon">🎯</span>今日核心判断</div>
        <div class="card-title" style="margin-top:14px"><a href="${escapeHtml(top.detail_path || '#')}">${escapeHtml(top.title || '待补充')}</a></div>
        <div class="badge-group" style="margin-bottom:10px">
          ${renderBadge(top.value_type_label || valueTypeLabels[top.value_type] || '待定', badgeClass(top.value_type || ''))}
          ${renderBadge(top.decision || '待定', badgeClass(top.decision || ''))}
        </div>
        <p>${escapeHtml(top.one_line_judgement || '待补充')}</p>
        <ul class="note-list">
          <li><strong>今日建议动作：</strong>${escapeHtml(latest.daily_action || '待补充')}</li>
          <li><strong>一句话判断：</strong>${escapeHtml(top.one_line_judgement || '待补充')}</li>
          <li><strong>最大不确定性：</strong>${escapeHtml(latest.max_uncertainty || '待补充')}</li>
        </ul>
      </div>
      <div class="card">
        <div class="section-title"><span class="section-icon">🧭</span>论文价值发现图</div>
        <div style="margin-top:14px">${renderMermaidShell(`flowchart TD
P[论文] --> V[价值判断]
V --> I[即时价值]
V --> T[趋势价值]
V --> L[长尾价值]
V --> N[暂时忽略]
I --> A[立即学习 / 试点]
T --> R[纳入趋势雷达 / 持续观察]
L --> S[沉淀启发 / 加入长尾库]
N --> X[保留最小索引]`)}</div>
      </div>
    </section>

    <section class="section">
      <div class="section-header"><h2 class="section-title"><span class="section-icon">📄</span>今日深挖论文</h2></div>
      <div class="card">
        <div class="card-title"><a href="${escapeHtml(top.detail_path || '#')}">${escapeHtml(top.title || '待补充')}</a></div>
        <div class="card-meta">${escapeHtml(formatDate(top.published))} · ${escapeHtml(top.source || '')} · 分数 ${escapeHtml(top.score || 0)}</div>
        <p>${escapeHtml(top.brief_cn || '')}</p>
        <div class="badge-group" style="margin-bottom:12px">${maybeArray(top.matched_topics).map(t => `<span class="topic-chip">${escapeHtml(t)}</span>`).join('')}</div>
        ${renderPaperLinks(top)}
      </div>
    </section>

    <section class="section">
      <div class="section-header"><h2 class="section-title"><span class="section-icon">🧳</span>今日长尾保存</h2></div>
      <div class="grid grid-3">${longTail.map(item => `
        <div class="card">
          <div class="card-title"><a href="${escapeHtml(item.detail_path || '#')}">${escapeHtml(item.title)}</a></div>
          <p><strong>为什么值得保存：</strong>${escapeHtml(item.why_save || '待补充')}</p>
          <p><strong>未来触发条件：</strong>${escapeHtml(item.future_trigger || '待补充')}</p>
          <p><strong>可沉淀资产：</strong>${escapeHtml(maybeArray(item.reusable_assets).join(' / ') || '待补充')}</p>
        </div>`).join('') || '<div class="card">暂无长尾论文</div>'}</div>
    </section>

    <section class="section">
      <div class="section-header"><h2 class="section-title"><span class="section-icon">📚</span>最近 7 篇日报</h2><a href="daily.html">查看全部</a></div>
      <div class="grid grid-3">${recent.map(renderDailySummaryCard).join('') || '<div class="card">暂无日报</div>'}</div>
    </section>

    <section class="section">
      <div class="section-header"><h2 class="section-title"><span class="section-icon">📈</span>趋势雷达概览</h2></div>
      <div class="grid grid-2">${trendCards || '<div class="card">暂无趋势数据</div>'}</div>
    </section>`;
  showState('index-root', root);
  await enhanceMermaid();
}

async function renderDailyPage() {
  showLoading('daily-root');
  const data = await loadJSON('daily-index.json');
  if (!data) return showError('daily-root', '日报索引加载失败。');
  const reports = maybeArray(data.reports);
  if (!reports.length) return showEmpty('daily-root', '暂无日报数据。');
  const html = `<div class="page-header"><h1>日报</h1><p>查看每日候选论文、价值类型分布、今日重点与长尾保存。</p></div>
    <div class="grid grid-3">${reports.map(renderDailySummaryCard).join('')}</div>`;
  showState('daily-root', html);
}

async function renderPapersPage() {
  showLoading('papers-root');
  const data = await loadJSON('paper-index.json');
  if (!data) return showError('papers-root', '论文索引加载失败。');
  const papers = maybeArray(data.papers);
  const html = `<div class="page-header"><h1>论文库</h1><p>沉淀所有被筛选、评分、判断过的论文。</p></div>
  <div class="table-wrapper"><table><thead><tr><th>论文标题</th><th>日期</th><th>来源</th><th>方向</th><th>价值类型</th><th>分数</th><th>判断</th><th>链接</th></tr></thead><tbody>
  ${papers.map(p => `<tr>
    <td><a href="${escapeHtml(p.detail_path || '#')}">${escapeHtml(p.title || '')}</a><div class="muted">${escapeHtml(p.brief_cn || '')}</div></td>
    <td>${escapeHtml(p.first_seen_date || '')}</td>
    <td>${escapeHtml(p.source || '')}</td>
    <td>${escapeHtml(maybeArray(p.matched_topics).join(' / ') || '未分类')}</td>
    <td>${renderBadge(p.value_type_label || '', badgeClass(p.value_type || ''))}</td>
    <td class="num">${escapeHtml(p.score || 0)}</td>
    <td>${renderBadge(p.decision || '待定', badgeClass(p.decision || ''))}</td>
    <td>${renderPaperLinks(p)}</td>
  </tr>`).join('')}
  </tbody></table></div>`;
  showState('papers-root', html);
}

async function renderTrendsPage() {
  showLoading('trends-root');
  const data = await loadJSON('trend-index.json');
  if (!data) return showError('trends-root', '趋势索引加载失败。');
  const trends = maybeArray(data.trends);
  const html = `<div class="page-header"><h1>趋势雷达</h1><p>只收纳确实有趋势价值的方向。</p></div>
    <div class="grid grid-2">${trends.map(t => `<div class="card"><div class="card-title">${escapeHtml(t.title)}</div><div class="badge-group" style="margin-bottom:10px">${renderBadge(t.stage || '待定', badgeClass(t.stage || ''))}</div><p>${escapeHtml(t.key_insight || '')}</p><div class="muted">关联论文 ${escapeHtml(t.paper_count || 0)} · 最近更新 ${escapeHtml(t.updated_at || '')}</div><div style="margin-top:12px"><a class="btn btn-secondary btn-sm" href="${escapeHtml(t.path || '#')}">查看 Markdown 详情</a></div></div>`).join('')}</div>`;
  showState('trends-root', html);
}

async function renderLongTailPage() {
  showLoading('long-tail-root');
  const data = await loadJSON('long-tail-index.json');
  if (!data) return showError('long-tail-root', '长尾库索引加载失败。');
  const items = maybeArray(data.items);
  const html = `<div class="page-header"><h1>长尾库</h1><p>保存现在不火、没有成熟工程实践，但未来可能有价值的论文、方法、评测、反证和工程启发。</p></div>
    <div class="callout" style="margin-bottom:16px"><strong>为什么需要长尾库：</strong>不是所有有价值论文都会立刻形成趋势。长尾库用于保存未来可能变重要的论文、方法、评测、反证和工程启发。</div>
    <div class="table-wrapper"><table><thead><tr><th>论文标题</th><th>方向</th><th>长尾价值类型</th><th>为什么保存</th><th>未来触发条件</th><th>可沉淀资产</th><th>复盘时间</th></tr></thead><tbody>
    ${items.map(item => `<tr><td><a href="${escapeHtml(item.detail_path || '#')}">${escapeHtml(item.title || '')}</a></td><td>${escapeHtml(item.direction || '')}</td><td>${escapeHtml(item.long_tail_type || '')}</td><td>${escapeHtml(item.why_save || '')}</td><td>${escapeHtml(item.future_trigger || '')}</td><td>${escapeHtml(maybeArray(item.reusable_assets).join(' / ') || '')}</td><td>${escapeHtml(item.revisit_date || '')}</td></tr>`).join('') || '<tr><td colspan="7">暂无长尾论文</td></tr>'}
    </tbody></table></div>`;
  showState('long-tail-root', html);
}

async function renderInsightsPage() {
  showLoading('insights-root');
  const data = await loadJSON('insight-index.json');
  const papers = await loadJSON('paper-index.json');
  if (!data) return showError('insights-root', '启发索引加载失败。');
  const html = `<div class="page-header"><h1>启发</h1><p>沉淀 Prompt、Skill、Checklist、架构模式、评测方法与工程机会。</p></div>
  <div class="grid grid-2">
    <div class="card"><div class="card-title">系统设计启发</div><ul class="note-list"><li>先做价值路由，再决定是否深挖。</li><li>长尾库是知识资产保留层。</li></ul></div>
    <div class="card"><div class="card-title">Agent 工程启发</div><ul class="note-list"><li>让 Agent 先判断今天值不值得试。</li><li>输出应沉淀为 Skill / Checklist。</li></ul></div>
    <div class="card"><div class="card-title">评测方法启发</div><ul class="note-list"><li>不仅评估方法效果，也评估是否值得投入。</li></ul></div>
    <div class="card"><div class="card-title">来源论文</div>${maybeArray(papers?.papers).slice(0,6).map(p => `<div class="item-row"><a href="${escapeHtml(p.detail_path || '#')}">${escapeHtml(p.title)}</a><div class="muted">${escapeHtml(p.one_line_judgement || '')}</div></div>`).join('')}</div>
  </div>`;
  showState('insights-root', html);
}

async function renderSourcesPage() {
  showLoading('sources-root');
  const data = await loadJSON('source-index.json');
  if (!data) return showError('sources-root', '数据源加载失败。');
  const group = (title, items) => `<section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">📦</span>${escapeHtml(title)}</h2></div><div class="list-stack">${maybeArray(items).map(item => `<div class="source-item card"><div><div class="card-title">${escapeHtml(item.name)}</div><div class="muted">用途：${escapeHtml(item.purpose)} · 更新频率：${escapeHtml(item.frequency)}</div></div><div class="badge-group">${renderBadge(item.status || '', badgeClass(item.status || ''))}</div></div>`).join('')}</div></section>`;
  showState('sources-root', `<div class="page-header"><h1>数据源</h1><p>固定数据源用于支持稳定的论文价值发现流程。</p></div>${group('理论源头', data.theory_sources)}${group('工程验证源', data.engineering_sources)}${group('社区弱信号', data.community_sources)}`);
}

async function renderAboutPage() {
  showState('about-root', `<div class="page-header"><h1>关于</h1><p>从论文出发，快速判断即时价值、趋势价值和长尾价值，沉淀可复用研究资产。</p></div>
  <div class="grid grid-2">
    <div class="card"><div class="card-title">为什么先看论文</div><p>因为真正的方向变化通常先在论文中露头，再逐步外溢到工程、产品与团队实践。</p></div>
    <div class="card"><div class="card-title">为什么不强制固定链路</div><p>“论文 → 理论 → 工程实践 → 趋势 → 启发 → 行动”仍然是常见研究路径，但不是所有论文都值得走完整链路。系统先做价值路由，再决定投入深度。</p></div>
    <div class="card"><div class="card-title">如何过滤噪声</div><p>明确标记暂时忽略，避免把注意力浪费在新意弱、证据弱、相关性弱的论文上。</p></div>
    <div class="card"><div class="card-title">GitHub 仓库</div><p><a href="https://github.com/lohasle/frontier-theory-radar" target="_blank" rel="noopener noreferrer">lohasle/frontier-theory-radar</a></p></div>
  </div>`);
}

async function renderDailyDetailPage() {
  const date = q('date');
  if (!date) return showError('daily-detail-root', '缺少 date 参数');
  showLoading('daily-detail-root');
  const detail = await loadJSON(`daily-details/${date}.json`);
  if (!detail) return showError('daily-detail-root', `未找到 ${date} 的日报详情`);
  const candidateRows = maybeArray(detail.candidate_papers).map(p => `<tr>
    <td><a href="${escapeHtml(p.detail_path || '#')}">${escapeHtml(p.title || '')}</a></td>
    <td>${escapeHtml(p.direction || '')}</td>
    <td>${renderBadge(p.value_type_label || '', badgeClass(p.value_type || ''))}</td>
    <td class="num">${escapeHtml(p.score || 0)}</td>
    <td>${renderBadge(p.decision || '', badgeClass(p.decision || ''))}</td>
    <td>${p.has_code ? '有' : '暂无'}</td>
    <td>${p.has_benchmark ? '有' : '暂无'}</td>
    <td>${p.worth_deep_dive ? '是' : '否'}</td>
  </tr>`).join('');
  const longTailCards = maybeArray(detail.long_tail_saved).map(item => `<div class="card"><div class="card-title"><a href="${escapeHtml(item.detail_path || '#')}">${escapeHtml(item.title || '')}</a></div><p><strong>为什么值得保存：</strong>${escapeHtml(item.why_save || '')}</p><p><strong>未来触发条件：</strong>${escapeHtml(item.future_trigger || '')}</p><p><strong>可能应用场景：</strong>${escapeHtml(maybeArray(item.possible_use_cases).join(' / '))}</p><p><strong>可沉淀资产：</strong>${escapeHtml(maybeArray(item.reusable_assets).join(' / '))}</p><p><strong>建议复盘时间：</strong>${escapeHtml(item.revisit_date || '')}</p></div>`).join('') || '<div class="card">暂无长尾保存论文</div>';
  const insights = detail.insights || {};
  const deep = detail.deep_dive || {};
  const html = `<div class="page-header"><h1>${escapeHtml(detail.title || '')}</h1><p>${escapeHtml(date)} · ${renderBadge(detail.value_type_label || '', badgeClass(detail.value_type || ''))} · ${renderBadge(detail.decision || '', badgeClass(detail.decision || ''))}</p></div>
  <div class="columns-2 section">
    <div class="card"><div class="card-title">标题区</div><ul class="note-list"><li><strong>今日最值得关注论文：</strong><a href="${escapeHtml(deep.detail_path || '#')}">${escapeHtml(detail.deep_dive_title || '')}</a></li><li><strong>今日建议动作：</strong>${escapeHtml(detail.daily_action || '')}</li><li><strong>分数：</strong>${escapeHtml(detail.score || 0)}</li><li><strong>趋势阶段：</strong>${escapeHtml(trendStatusLabels[detail.trend_stage] || detail.trend_stage || '待定')}</li></ul></div>
    <div class="card"><div class="card-title">先说结论</div><ul class="note-list">${maybeArray(detail.conclusion_lines).map(line => `<li>${escapeHtml(line)}</li>`).join('')}</ul></div>
  </div>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">🧭</span>价值发现图</h2></div>${renderMermaidShell(detail.mermaid?.value_discovery || '')}</section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">📋</span>今日候选论文表</h2></div><div class="table-wrapper"><table><thead><tr><th>论文标题</th><th>方向</th><th>价值类型</th><th>分数</th><th>判断</th><th>代码</th><th>Benchmark</th><th>值得深挖</th></tr></thead><tbody>${candidateRows || '<tr><td colspan="8">暂无候选论文</td></tr>'}</tbody></table></div></section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">🔍</span>今日深挖论文</h2></div><div class="card"><div class="card-title"><a href="${escapeHtml(deep.detail_path || '#')}">${escapeHtml(deep.title || detail.deep_dive_title || '')}</a></div><p><strong>一句话本质：</strong>${escapeHtml(deep.one_line_essence || deep.one_line_judgement || '')}</p><p><strong>底层问题：</strong>${escapeHtml(deep.core_problem || '')}</p><p><strong>新命题 / 新方法 / 新证据：</strong>${escapeHtml(deep.new_claim_or_method || '')}</p><p><strong>研究位置：</strong>${escapeHtml(deep.research_position || '')}</p><p><strong>工程可验证性：</strong>${deep.engineering_testability?.has_code ? '有代码，可做最小实验。' : '暂无代码，先从 Prompt / 评测 / 架构草图验证。'}</p><p><strong>趋势关联：</strong>${escapeHtml(trendStatusLabels[deep.trend_relation?.status] || deep.trend_relation?.status || '待定')}</p><p><strong>长尾价值：</strong>${escapeHtml(deep.long_tail?.why_save || '')}</p><p><strong>启发：</strong>${escapeHtml(maybeArray(insights.agent_engineering).join('；') || '')}</p><p><strong>行动建议：</strong>${escapeHtml(detail.daily_action || '')}</p>${renderPaperLinks(deep)}</div></section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">🧳</span>今日长尾保存</h2></div><div class="grid grid-3">${longTailCards}</div></section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">🚫</span>今日忽略理由</h2></div><div class="card"><ul class="note-list">${maybeArray(detail.ignore_reasons).map(x => `<li>${escapeHtml(x)}</li>`).join('')}</ul></div></section>
  <section class="section columns-2"><div class="card"><div class="card-title">启发</div><ul class="note-list"><li><strong>系统设计：</strong>${escapeHtml(maybeArray(insights.system_design).join('；'))}</li><li><strong>Agent 工程：</strong>${escapeHtml(maybeArray(insights.agent_engineering).join('；'))}</li><li><strong>研发流程：</strong>${escapeHtml(maybeArray(insights.dev_process).join('；'))}</li><li><strong>评测方法：</strong>${escapeHtml(maybeArray(insights.evaluation).join('；'))}</li><li><strong>平台工程：</strong>${escapeHtml(maybeArray(insights.platform_engineering).join('；'))}</li><li><strong>个人学习：</strong>${escapeHtml(maybeArray(insights.personal_learning).join('；'))}</li></ul></div><div class="card"><div class="card-title">行动建议</div><ul class="note-list">${maybeArray(detail.actions.immediate_actions).map(x => `<li>${escapeHtml(x)}</li>`).join('')}${maybeArray(detail.actions.trend_actions).map(x => `<li>${escapeHtml(x)}</li>`).join('')}${maybeArray(detail.actions.long_tail_actions).map(x => `<li>${escapeHtml(x)}</li>`).join('')}${detail.actions.ignore_reason ? `<li>${escapeHtml(detail.actions.ignore_reason)}</li>` : ''}</ul></div></section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">📚</span>引用与延伸阅读</h2></div><div class="card">${renderPaperLinks(deep)}<div style="margin-top:16px">${detail.raw_markdown_html || ''}</div></div></section>`;
  showState('daily-detail-root', html);
  await enhanceMermaid();
}

async function renderPaperDetailPage() {
  const id = q('id');
  if (!id) return showError('paper-detail-root', '缺少 id 参数');
  showLoading('paper-detail-root');
  const detail = await loadJSON(`paper-details/${id}.json`);
  if (!detail) return showError('paper-detail-root', `未找到论文 ${id}`);
  const scores = detail.value_scores || {};
  const html = `<div class="page-header"><h1>论文详情</h1><p>${renderBadge(detail.value_type_label || '', badgeClass(detail.value_type || ''))} · 分数 ${escapeHtml(detail.score || 0)}</p></div>
  <section class="section columns-2">
    <div class="card"><div class="card-title">论文元信息</div><ul class="note-list"><li><strong>标题：</strong>${escapeHtml(detail.title || '')}</li><li><strong>作者：</strong>${escapeHtml(maybeArray(detail.authors).join(', ') || '暂无')}</li><li><strong>发布时间：</strong>${escapeHtml(detail.published || '')}</li><li><strong>来源：</strong>${escapeHtml(detail.source || '')}</li><li><strong>首次收录日期：</strong>${escapeHtml(detail.first_seen_date || '')}</li><li><strong>首次深挖日报：</strong>${detail.daily_path ? `<a href="${escapeHtml(detail.daily_path)}">查看日报</a>` : '暂无'}</li></ul>${renderPaperLinks(detail)}</div>
    <div class="card"><div class="card-title">价值判断</div><ul class="note-list"><li><strong>价值类型：</strong>${escapeHtml(detail.value_type_label || '')}</li><li><strong>推荐动作：</strong>${escapeHtml(detail.one_line_judgement || '')}</li><li><strong>一句话判断：</strong>${escapeHtml(detail.one_line_judgement || '')}</li><li><strong>最大不确定性：</strong>${escapeHtml(maybeArray(detail.trend_relation?.uncertainties).join('；') || '待补充')}</li></ul></div>
  </section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">🧭</span>论文价值发现图</h2></div>${renderMermaidShell(detail.mermaid?.value_discovery || '')}</section>
  <section class="section grid grid-2">
    <div class="card"><div class="card-title">一句话本质</div><p>${escapeHtml(detail.one_line_essence || '')}</p></div>
    <div class="card"><div class="card-title">底层问题</div><p>${escapeHtml(detail.core_problem || '')}</p></div>
    <div class="card"><div class="card-title">新命题 / 新方法 / 新证据</div><p>${escapeHtml(detail.new_claim_or_method || '')}</p></div>
    <div class="card"><div class="card-title">研究位置</div><p>${escapeHtml(detail.research_position || '')}</p></div>
  </section>
  <section class="section columns-2">
    <div class="card"><div class="card-title">工程可验证性</div><ul class="note-list"><li>是否有代码：${detail.engineering_testability?.has_code ? '有' : '暂无'}</li><li>是否有 Benchmark：${detail.engineering_testability?.has_benchmark ? '有' : '暂无'}</li><li>是否可复现：${detail.engineering_testability?.can_reproduce ? '较可复现' : '风险较高'}</li><li>最小实验：${escapeHtml(detail.engineering_testability?.minimum_experiment || '')}</li><li>工程场景：${escapeHtml(maybeArray(detail.engineering_testability?.engineering_scenarios).join(' / ') || '')}</li></ul></div>
    <div class="card"><div class="card-title">趋势关联</div><ul class="note-list"><li>状态：${escapeHtml(trendStatusLabels[detail.trend_relation?.status] || detail.trend_relation?.status || '待定')}</li><li>关联趋势：${maybeArray(detail.trend_relation?.related_trends).map(slug => `<a href="trends/${escapeHtml(slug)}.md">${escapeHtml(slug)}</a>`).join(' / ') || '暂无'}</li><li>证据：${escapeHtml(maybeArray(detail.trend_relation?.evidence).join('；') || '暂无')}</li></ul></div>
  </section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">🧳</span>长尾价值</h2></div><div class="card"><ul class="note-list"><li><strong>为什么值得保存：</strong>${escapeHtml(detail.long_tail?.why_save || '')}</li><li><strong>未来触发条件：</strong>${escapeHtml(maybeArray(detail.long_tail?.future_trigger).join('；') || '')}</li><li><strong>可能应用场景：</strong>${escapeHtml(maybeArray(detail.long_tail?.possible_use_cases).join(' / ') || '')}</li><li><strong>可迁移资产：</strong>${escapeHtml(maybeArray(detail.long_tail?.reusable_assets).join(' / ') || '')}</li><li><strong>何时复盘：</strong>${escapeHtml(detail.long_tail?.revisit_date || detail.long_tail?.revisit_condition || '')}</li><li><strong>长尾库入口：</strong><a href="long-tail.html">查看长尾库</a></li></ul></div></section>
  <section class="section columns-2"><div class="card"><div class="card-title">启发</div><ul class="note-list"><li><strong>系统设计：</strong>${escapeHtml(maybeArray(detail.insights?.system_design).join('；'))}</li><li><strong>Agent 工程：</strong>${escapeHtml(maybeArray(detail.insights?.agent_engineering).join('；'))}</li><li><strong>研发流程：</strong>${escapeHtml(maybeArray(detail.insights?.dev_process).join('；'))}</li><li><strong>评测方法：</strong>${escapeHtml(maybeArray(detail.insights?.evaluation).join('；'))}</li><li><strong>平台工程：</strong>${escapeHtml(maybeArray(detail.insights?.platform_engineering).join('；'))}</li><li><strong>个人学习：</strong>${escapeHtml(maybeArray(detail.insights?.personal_learning).join('；'))}</li></ul></div><div class="card"><div class="card-title">行动建议</div><ul class="note-list">${maybeArray(detail.actions?.immediate_actions).map(x => `<li>${escapeHtml(x)}</li>`).join('')}${maybeArray(detail.actions?.trend_actions).map(x => `<li>${escapeHtml(x)}</li>`).join('')}${maybeArray(detail.actions?.long_tail_actions).map(x => `<li>${escapeHtml(x)}</li>`).join('')}${detail.actions?.ignore_reason ? `<li>${escapeHtml(detail.actions.ignore_reason)}</li>` : ''}</ul></div></section>
  <section class="section"><div class="section-header"><h2 class="section-title"><span class="section-icon">📊</span>评分拆解</h2></div><div class="table-wrapper"><table><tbody>${Object.entries(scores).map(([k,v]) => `<tr><td>${escapeHtml(k)}</td><td class="num">${escapeHtml(v)}</td></tr>`).join('')}</tbody></table></div></section>`;
  showState('paper-detail-root', html);
  await enhanceMermaid();
}

document.addEventListener('DOMContentLoaded', async () => {
  setActiveNav();
  initMobileMenu();
  const page = document.body.dataset.page;
  if (page === 'index') await renderIndexPage();
  if (page === 'daily') await renderDailyPage();
  if (page === 'papers') await renderPapersPage();
  if (page === 'trends') await renderTrendsPage();
  if (page === 'long-tail') await renderLongTailPage();
  if (page === 'insights') await renderInsightsPage();
  if (page === 'sources') await renderSourcesPage();
  if (page === 'about') await renderAboutPage();
  if (page === 'daily-detail') await renderDailyDetailPage();
  if (page === 'paper-detail') await renderPaperDetailPage();
});
