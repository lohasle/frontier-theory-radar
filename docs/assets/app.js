/**
 * Frontier Theory Radar — GitHub Pages App
 * Vanilla JS for data loading, rendering, and interactivity
 */

const DATA_BASE = './data';

// ===== Data Loading =====
async function loadJSON(filename) {
  try {
    const resp = await fetch(`${DATA_BASE}/${filename}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (e) {
    console.error(`Failed to load ${filename}:`, e);
    return null;
  }
}

// ===== Utilities =====
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch {
    return dateStr;
  }
}

function decisionBadgeClass(decision) {
  if (!decision) return 'badge-ignore';
  const d = decision.toLowerCase();
  if (d.includes('重点')) return 'badge-focus';
  if (d.includes('轻量') || d.includes('试点')) return 'badge-trial';
  if (d.includes('观察')) return 'badge-watch';
  if (d.includes('忽略')) return 'badge-ignore';
  return 'badge-ignore';
}

function stageBadgeClass(stage) {
  if (!stage) return 'badge-ignore';
  if (stage.includes('萌芽')) return 'badge-emerging';
  if (stage.includes('上升')) return 'badge-rising';
  if (stage.includes('主流')) return 'badge-mainstream';
  if (stage.includes('过热') || stage.includes('噪声')) return 'badge-overheated';
  return 'badge-ignore';
}

function renderBadge(text, cls) {
  return `<span class="badge ${cls}">${escapeHtml(text)}</span>`;
}

function cleanInspiration(text) {
  if (!text) return '';
  return text
    .replace(/^>\s*研究范式：.*$/m, '')
    .replace(/论文\s*→\s*理论\s*→\s*工程实践\s*→\s*趋势\s*→\s*启发\s*→\s*行动/g, '')
    .trim();
}

function renderPaperLinks(links) {
  if (!links || !links.length) return '<span style="color:var(--text-muted);font-size:12px">暂无</span>';
  const linkMap = {
    'arXiv': 'arxiv', 'PDF': 'pdf', 'Code': 'code',
    'Benchmark': 'benchmark', 'Papers with Code': 'pwc', 'OpenReview': 'openreview'
  };
  return links.map(l => {
    const cls = linkMap[l.label] || 'arxiv';
    const url = l.url || '#';
    if (!l.url) return `<span class="paper-link ${cls} disabled">${escapeHtml(l.label)}</span>`;
    return `<a class="paper-link ${cls}" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(l.label)}</a>`;
  }).join('');
}

function showLoading(containerId) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>加载数据中...</p></div>';
}

function showError(containerId, msg) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="error-state"><p>⚠️ ${escapeHtml(msg || '数据加载失败，请稍后刷新重试。')}</p></div>`;
}

function showEmpty(containerId, msg) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="empty-state"><p>${escapeHtml(msg || '暂无数据')}</p></div>`;
}

// ===== Navigation Active State =====
function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.navbar-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (path.endsWith(href) || (href === 'index.html' && (path.endsWith('/') || path.endsWith('index.html')))) {
      a.classList.add('active');
    }
  });
}

// ===== Mobile Menu Toggle =====
function initMobileMenu() {
  const toggle = document.querySelector('.navbar-toggle');
  const links = document.querySelector('.navbar-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
    });
  }
}

// ===== Index Page Rendering =====
async function renderIndexPage() {
  const latest = await loadJSON('latest.json');
  if (!latest) {
    showError('hero-data', '数据加载失败');
    showError('daily-list', '');
    return;
  }

  // Core judgment card
  const dd = latest.latest_daily;
  const coreEl = document.getElementById('core-judgment');
  if (coreEl && dd) {
    const dec = dd.decision || '待定';
    const decClass = decisionBadgeClass(dec);
    coreEl.innerHTML = `
      <div class="card">
        <div class="section-header">
          <h2 class="section-title">今日核心判断</h2>
          ${renderBadge(dec, decClass)}
        </div>
        <div class="card-meta">日期：${formatDate(dd.date)}</div>
        <div class="card-title"><a href="${escapeHtml(dd.deep_dive_url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(dd.deep_dive_title || '待分析')}</a></div>
        <div class="card-desc" style="margin-top:8px">
          <p>最大不确定性：${escapeHtml(dd.max_uncertainty || '待分析')}</p>
          <p>下一步动作：${escapeHtml(dd.next_action || '运行完整流程')}</p>
        </div>
      </div>`;
  }

  // Research chain
  const chainEl = document.getElementById('chain-vis');
  if (chainEl) {
    const steps = [
      { icon: '1', label: '论文', desc: '前沿论文发现' },
      { icon: '2', label: '理论', desc: '核心理论提取' },
      { icon: '3', label: '工程', desc: '实践验证搜索' },
      { icon: '4', label: '趋势', desc: '阶段判断' },
      { icon: '5', label: '启发', desc: '蒸馏洞察' },
      { icon: '6', label: '行动', desc: '执行建议' },
    ];
    chainEl.innerHTML = steps.map((s, i) => {
      const arrow = i < steps.length - 1 ? '<span class="chain-arrow">→</span>' : '';
      return `<div class="chain-step"><div class="chain-step-icon">${s.icon}</div><div class="chain-step-label">${s.label}</div><div class="chain-step-desc">${s.desc}</div></div>${arrow}`;
    }).join('');
  }

  // Radar overview
  const radarEl = document.getElementById('radar-overview');
  if (radarEl) {
    const trends = await loadJSON('trend-index.json');
    if (trends && trends.trends) {
      const stages = {
        '萌芽': { icon: '🌱', items: [] },
        '上升': { icon: '📈', items: [] },
        '主流化': { icon: '✅', items: [] },
        '过热': { icon: '🔥', items: [] },
      };
      trends.trends.forEach(t => {
        const s = t.stage || '萌芽';
        if (stages[s]) stages[s].items.push(t);
        else stages['萌芽'].items.push(t);
      });
      radarEl.innerHTML = Object.entries(stages).map(([stage, data]) => `
        <div class="radar-quadrant">
          <h3>${data.icon} ${stage}</h3>
          ${data.items.length ? data.items.map(t => `
            <div class="radar-item">
              <span class="radar-item-name">${escapeHtml(t.title)}</span>
              <span class="radar-item-meta">${formatDate(t.updated_at || '')}</span>
            </div>
          `).join('') : '<p style="color:var(--text-muted);font-size:13px">暂无</p>'}
        </div>
      `).join('');
    }
  }

  // Recent 7 dailies
  const dailyListEl = document.getElementById('daily-list');
  if (dailyListEl && latest.recent_dailies) {
    const dailies = latest.recent_dailies.slice(0, 7);
    if (dailies.length === 0) {
      showEmpty('daily-list', '暂无日报');
    } else {
      dailyListEl.innerHTML = dailies.map(d => {
        const dec = d.decision || '待定';
        return `
          <div class="card daily-card">
            <div class="daily-card-date">${formatDate(d.date)}</div>
            <div class="daily-card-paper"><a href="${escapeHtml(d.deep_dive_url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(d.deep_dive_title || '待分析')}</a></div>
            <div class="badge-group">${renderBadge(dec, decisionBadgeClass(dec))}${d.topics ? renderBadge(d.topics, 'badge-trial') : ''}</div>
            <div class="daily-card-insight">${escapeHtml(cleanInspiration(d.inspiration || '') || '—')}</div>
            <div class="daily-card-footer">
              <span></span>
              <a href="${escapeHtml(d.path || '#')}" class="btn btn-sm btn-outline" style="color:var(--primary-lighter);border-color:var(--border)">查看日报</a>
            </div>
          </div>`;
      }).join('');
    }
  }
}

// ===== Daily Page Rendering =====
async function renderDailyPage() {
  showLoading('daily-content');
  const data = await loadJSON('daily-index.json');
  if (!data || !data.reports || data.reports.length === 0) {
    showError('daily-content', '暂无日报数据');
    return;
  }

  const container = document.getElementById('daily-content');
  container.innerHTML = data.reports.map(d => {
    const dec = d.decision || '待定';
    return `
      <div class="card daily-card" data-decision="${escapeHtml(dec)}" data-direction="${escapeHtml(d.topics || '')}">
        <div class="daily-card-date">${formatDate(d.date)}</div>
        <div class="daily-card-paper"><a href="${escapeHtml(d.deep_dive_url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(d.deep_dive_title || '待分析')}</a></div>
        <div class="badge-group">${renderBadge(dec, decisionBadgeClass(dec))}${d.topics ? renderBadge(d.topics, 'badge-trial') : ''}</div>
        <div class="daily-card-insight">${escapeHtml(d.inspiration || '')}</div>
        <div class="daily-card-footer">
          <span class="card-meta">${formatDate(d.date)}</span>
          <a href="${escapeHtml(d.path || '#')}" class="btn btn-sm btn-outline" style="color:var(--primary-lighter);border-color:var(--border)">查看日报</a>
        </div>
      </div>`;
  }).join('');

  initFilters('daily-content', '.daily-card');
}

// ===== Papers Page Rendering =====
async function renderPapersPage() {
  showLoading('papers-content');
  const data = await loadJSON('paper-index.json');
  if (!data || !data.papers || data.papers.length === 0) {
    showError('papers-content', '暂无论文数据');
    return;
  }

  const container = document.getElementById('papers-content');
  const header = `<div class="table-wrapper"><table>
    <thead><tr>
      <th>论文</th><th>一句话概述</th><th>领域标签</th><th>日期</th><th>来源</th><th style="text-align:right">分数</th><th>判断</th><th>代码</th><th>Benchmark</th><th>链接</th>
    </tr></thead><tbody>`;

  const rows = data.papers.map(p => {
    const dec = p.decision || '待定';
    const topics = Array.isArray(p.topics) ? p.topics : [];
    const tags = Array.isArray(p.tags) ? p.tags : [];
    const topicBadges = (topics.length ? topics : ['未分类'])
      .slice(0, 3)
      .map(t => `<span class="topic-chip">${escapeHtml(t)}</span>`)
      .join('');
    const keywordBadges = tags.slice(0, 2).map(t => `<span class="topic-chip topic-chip-light">${escapeHtml(t)}</span>`).join('');
    const hasCode = p.has_code || p.code_url ? '✅' : '—';
    const hasBench = p.has_benchmark || p.benchmark_url ? '✅' : '—';
    return `<tr data-decision="${escapeHtml(dec)}" data-source="${escapeHtml(p.source || '')}" data-score="${p.score || 0}">
      <td><a href="${escapeHtml(p.url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(p.title || '未知')}</a></td>
      <td class="paper-brief">${escapeHtml(p.brief_cn || '暂无概述')}</td>
      <td><div class="topic-chip-group">${topicBadges}${keywordBadges}</div></td>
      <td>${formatDate(p.published)}</td>
      <td>${escapeHtml(p.source || '')}</td>
      <td class="num">${p.score || 0}</td>
      <td>${renderBadge(dec, decisionBadgeClass(dec))}</td>
      <td>${hasCode}</td>
      <td>${hasBench}</td>
      <td>${renderPaperLinks(p.links)}</td>
    </tr>`;
  }).join('');

  container.innerHTML = header + rows + '</tbody></table></div>';
  initFilters('papers-content', 'tbody tr');
}

// ===== Trends Page Rendering =====
async function renderTrendsPage() {
  showLoading('trends-content');
  const data = await loadJSON('trend-index.json');
  if (!data || !data.trends || data.trends.length === 0) {
    showError('trends-content', '暂无趋势数据');
    return;
  }

  const stages = { '萌芽': [], '上升': [], '主流化': [], '过热': [], '噪声': [] };
  data.trends.forEach(t => {
    const s = t.stage || '萌芽';
    if (stages[s]) stages[s].push(t);
    else stages['萌芽'].push(t);
  });

  const container = document.getElementById('trends-content');
  const icons = { '萌芽': 'M1', '上升': 'R2', '主流化': 'S3', '过热': 'H4', '噪声': 'N5' };

  container.innerHTML = Object.entries(stages).map(([stage, items]) => `
    <div class="section">
      <h2 class="section-title">${icons[stage] || '📊'} ${stage}</h2>
      <div class="grid grid-3">
        ${items.map(t => `
          <div class="card">
            <div class="card-title">${escapeHtml(t.title)}</div>
            <div class="badge-group">${renderBadge(t.stage || '萌芽', stageBadgeClass(t.stage))}</div>
            <div class="card-meta" style="margin-top:8px">最近更新：${formatDate(t.updated_at || '')}</div>
            <a href="${escapeHtml(t.path || '#')}" class="btn btn-sm btn-outline" style="margin-top:8px;color:var(--primary-lighter);border-color:var(--border)">查看详情</a>
          </div>
        `).join('') || '<p style="color:var(--text-muted)">暂无</p>'}
      </div>
    </div>
  `).join('');
}

// ===== Insights Page Rendering =====
async function renderInsightsPage() {
  showLoading('insights-content');
  const data = await loadJSON('insight-index.json');
  if (!data || !data.insights || data.insights.length === 0) {
    showError('insights-content', '暂无启发数据');
    return;
  }

  const container = document.getElementById('insights-content');
  container.innerHTML = data.insights.map(i => `
    <div class="card" style="margin-bottom:12px">
      <div class="card-title"><a href="${escapeHtml(i.path || '#')}">${escapeHtml(i.title)}</a></div>
      <div class="card-meta">${escapeHtml(i.slug || '')}</div>
    </div>
  `).join('');
}

// ===== Sources Page Rendering =====
async function renderSourcesPage() {
  showLoading('sources-content');
  const data = await loadJSON('source-index.json');
  if (!data) {
    showError('sources-content', '数据源信息加载失败');
    return;
  }

  const container = document.getElementById('sources-content');
  const groups = [
    { key: 'theory_sources', title: '📚 理论源头', desc: '负责理论发现' },
    { key: 'engineering_sources', title: '🔧 工程验证源', desc: '负责工程证据验证' },
    { key: 'community_sources', title: '💬 社区信号', desc: '弱信号和反证' },
  ];

  container.innerHTML = groups.map(g => {
    const items = data[g.key] || [];
    return `
      <div class="source-group">
        <h3>${g.title} <span style="font-weight:400;font-size:13px;color:var(--text-muted)">${g.desc}</span></h3>
        ${items.map(s => `
          <div class="source-item">
            <div>
              <div class="source-name">${escapeHtml(s.name)}</div>
              <div style="font-size:12px;color:var(--text-muted)">频率：${escapeHtml(s.frequency || '未知')}</div>
            </div>
            <div>
              <span class="source-status ${s.status === 'active' ? 'active' : 'pending'}">${s.status === 'active' ? '已接入' : '待接入'}</span>
            </div>
          </div>
        `).join('')}
      </div>`;
  }).join('');
}

// ===== Filter Logic =====
function initFilters(containerId, itemSelector) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const filterBar = container.closest('.container')?.querySelector('.filter-bar');
  if (!filterBar) return;

  const selects = filterBar.querySelectorAll('select');
  selects.forEach(sel => {
    sel.addEventListener('change', () => applyFilters(containerId, itemSelector));
  });
}

function applyFilters(containerId, itemSelector) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const items = container.querySelectorAll(itemSelector);

  const filterBar = container.closest('.container')?.querySelector('.filter-bar');
  if (!filterBar) return;

  const decisionFilter = filterBar.querySelector('[data-filter="decision"]')?.value || '';
  const sourceFilter = filterBar.querySelector('[data-filter="source"]')?.value || '';

  items.forEach(item => {
    let show = true;
    if (decisionFilter && !item.dataset.decision?.includes(decisionFilter)) show = false;
    if (sourceFilter && item.dataset.source !== sourceFilter) show = false;
    item.style.display = show ? '' : 'none';
  });
}

// ===== Init =====
document.addEventListener('DOMContentLoaded', () => {
  setActiveNav();
  initMobileMenu();

  const page = document.body.dataset.page;
  switch (page) {
    case 'index': renderIndexPage(); break;
    case 'daily': renderDailyPage(); break;
    case 'papers': renderPapersPage(); break;
    case 'trends': renderTrendsPage(); break;
    case 'insights': renderInsightsPage(); break;
    case 'sources': renderSourcesPage(); break;
  }
});
