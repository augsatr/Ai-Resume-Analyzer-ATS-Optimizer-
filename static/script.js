let currentData = null;

// Upload
const uploadCard = document.getElementById('uploadCard');
const resumeInput = document.getElementById('resumeInput');
uploadCard.addEventListener('click', () => resumeInput.click());
uploadCard.addEventListener('dragover', (e) => { e.preventDefault(); uploadCard.classList.add('dragover'); });
uploadCard.addEventListener('dragleave', () => uploadCard.classList.remove('dragover'));
uploadCard.addEventListener('drop', (e) => { e.preventDefault(); uploadCard.classList.remove('dragover'); if (e.dataTransfer.files.length) resumeInput.files = e.dataTransfer.files; handleFile(); });
resumeInput.addEventListener('change', handleFile);

function handleFile() {
  const file = resumeInput.files[0];
  const fn = document.getElementById('fileName');
  const btn = document.getElementById('analyzeBtn');
  if (file) {
    fn.innerHTML = '<span>&#128196;</span> ' + file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
    fn.style.display = 'flex';
    uploadCard.classList.add('has-file');
    btn.disabled = false;
  } else {
    fn.style.display = 'none';
    uploadCard.classList.remove('has-file');
    btn.disabled = true;
  }
}

// Analyze
async function analyze() {
  const file = resumeInput.files[0];
  if (!file) return;

  const btn = document.getElementById('analyzeBtn');
  const loading = document.getElementById('loading');
  const loadingText = document.getElementById('loadingText');
  const results = document.getElementById('results');

  btn.disabled = true;
  btn.innerHTML = '<span>&#8987;</span> Analyzing...';
  loading.classList.add('active');
  results.classList.remove('active');
  results.innerHTML = '';

  const steps = ['Parsing resume...', 'Extracting text and sections...', 'Analyzing keywords...', 'Calculating ATS score...', 'Generating insights...'];
  let stepIdx = 0;
  const stepInterval = setInterval(() => {
    if (stepIdx < steps.length) loadingText.textContent = steps[stepIdx++];
    else clearInterval(stepInterval);
  }, 800);

  const formData = new FormData();
  formData.append('resume', file);
  formData.append('job_description', document.getElementById('jobDesc').value.trim());

  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    const data = await res.json();
    clearInterval(stepInterval);
    loadingText.textContent = 'Analysis complete!';

    if (data.error) {
      results.innerHTML = '<div class="feedback-item error" style="padding:20px;border-radius:12px;"><span class="fb-icon">&#10060;</span>' + escapeHtml(data.error) + '</div>';
      results.classList.add('active');
      btn.disabled = false;
      btn.innerHTML = '<span>&#9889;</span> Analyze Resume';
      loading.classList.remove('active');
      return;
    }

    currentData = data;
    setTimeout(() => {
      renderResults(data);
      results.classList.add('active');
      loading.classList.remove('active');
      btn.disabled = false;
      btn.innerHTML = '<span>&#9889;</span> Analyze Resume';
    }, 300);
  } catch (err) {
    clearInterval(stepInterval);
    results.innerHTML = '<div class="feedback-item error" style="padding:20px;border-radius:12px;"><span class="fb-icon">&#10060;</span>Network error: ' + escapeHtml(err.message) + '</div>';
    results.classList.add('active');
    loading.classList.remove('active');
    btn.disabled = false;
    btn.innerHTML = '<span>&#9889;</span> Analyze Resume';
  }
}

// Render
function renderResults(data) {
  const el = document.getElementById('results');
  if (data.ats_score) {
    el.innerHTML = renderScoreOverview(data.ats_score) +
      renderFeedbackSummary(data.ats_score) +
      renderFeedback(data.ats_score) +
      renderTabs(data);
    initTabs();
    drawRadarChart(data.ats_score);
  } else {
    el.innerHTML = renderNoJD(data);
  }
}

function renderScoreOverview(ats) {
  const score = ats.total_score;
  const cls = score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low';
  let verdict, vClass;
  if (score >= 80) { verdict = 'Excellent'; vClass = 'verdict-excellent'; }
  else if (score >= 65) { verdict = 'Good'; vClass = 'verdict-good'; }
  else if (score >= 45) { verdict = 'Fair'; vClass = 'verdict-fair'; }
  else { verdict = 'Needs Work'; vClass = 'verdict-poor'; }

  const catLabels = {
    keyword_match: 'Keywords', formatting: 'Format', contact_info: 'Contact',
    sections: 'Sections', quantified: 'Impact', action_verbs: 'Verbs',
    education: 'Education', experience: 'Experience', length: 'Length', skills_depth: 'Skills'
  };
  let miniBars = Object.entries(ats.category_scores).map(([k, v]) => {
    const label = catLabels[k] || k;
    return '<div class="category-mini-item"><span class="mini-label">' + label + '</span><span class="mini-score" style="color:' + (v >= 70 ? 'var(--success)' : v >= 40 ? 'var(--warning)' : 'var(--error)') + '">' + v + '%</span></div>';
  }).join('');

  return '<div class="score-overview">' +
    '<div class="score-circle">' +
      '<div class="score-number ' + cls + '">' + score + '</div>' +
      '<div class="score-label">ATS Score</div>' +
      '<div class="score-verdict ' + vClass + '">' + verdict + '</div>' +
      '<div class="category-mini-grid">' + miniBars + '</div>' +
    '</div>' +
    '<div class="radar-container"><canvas id="radarChart"></canvas></div>' +
  '</div>';
}

function renderFeedbackSummary(ats) {
  const counts = { success: 0, warning: 0, error: 0, info: 0 };
  ats.feedback.forEach(f => { if (counts[f.type] !== undefined) counts[f.type]++; });
  return '<div class="feedback-summary">' +
    (counts.success ? '<span class="feedback-stat success">&#10003; ' + counts.success + ' Success</span>' : '') +
    (counts.warning ? '<span class="feedback-stat warning">&#9888; ' + counts.warning + ' Warnings</span>' : '') +
    (counts.error ? '<span class="feedback-stat error">&#10060; ' + counts.error + ' Issues</span>' : '') +
  '</div>';
}

function renderFeedback(ats) {
  const icons = { success: '&#10003;', warning: '&#9888;', error: '&#10060;', info: '&#9432;' };
  let html = '<div class="feedback-section"><h3>&#128220; Detailed Feedback</h3><ul class="feedback-list">';
  ats.feedback.forEach(f => {
    html += '<li class="feedback-item ' + f.type + '"><span class="fb-icon">' + icons[f.type] + '</span>' + escapeHtml(f.message) + '</li>';
  });
  html += '</ul></div>';
  return html;
}

function renderTabs(data) {
  const tabConfig = [
    { id: 'keywords', label: 'Keywords' },
    { id: 'skills', label: 'Skills Gap' },
    { id: 'improver', label: 'Bullet Improver' },
    { id: 'resume', label: 'Resume Text' },
  ];
  let tabs = '<div class="tabs">';
  tabConfig.forEach((t, i) => {
    tabs += '<button class="tab-btn' + (i === 0 ? ' active' : '') + '" data-tab="' + t.id + '">' + t.label + '</button>';
  });
  tabs += '</div>';

  const renderers = {
    keywords: () => renderKeywordsTab(data),
    skills: () => renderSkillsGapTab(data),
    improver: () => renderImproverTab(),
    resume: () => renderResumeTab(data),
  };

  let contents = '';
  tabConfig.forEach(t => {
    contents += '<div class="tab-content' + (t.id === 'keywords' ? ' active' : '') + '" id="tab-' + t.id + '">' + renderers[t.id]() + '</div>';
  });

  return tabs + contents;
}

function renderKeywordsTab(data) {
  const kw = data.keyword_match;
  if (!kw) return '<p style="color:var(--text-muted);padding:20px;">No keyword data available. Paste a job description and re-analyze.</p>';

  const isDual = kw.matched.length > 0 || kw.missing.length > 0;
  if (!isDual) return '<p style="color:var(--text-muted);padding:20px;">No keywords extracted. Try a more detailed job description.</p>';

  let html = '<div class="keyword-viz">';

  html += '<div class="keyword-panel">';
  html += '<h3>Matched Keywords <span style="color:var(--success);font-weight:400;">(' + kw.matched_count + ')</span></h3>';
  html += '<p class="subtitle">These keywords from the JD appear in your resume &#10003;</p>';
  html += '<div class="keyword-tags">';
  if (kw.matched.length) kw.matched.forEach(k => html += '<span class="keyword-tag matched">' + escapeHtml(k) + '</span>');
  else html += '<span style="color:var(--text-muted);font-size:0.85rem;">No matches found</span>';
  html += '</div></div>';

  html += '<div class="keyword-panel">';
  html += '<h3>Missing Keywords <span style="color:var(--error);font-weight:400;">(' + kw.missing.length + ')</span></h3>';
  html += '<p class="subtitle">Add these to your resume to improve your match rate</p>';
  html += '<div class="keyword-tags">';
  kw.missing.forEach(k => html += '<span class="keyword-tag missing">' + escapeHtml(k) + '</span>');
  html += '</div></div></div>';

  html += '<div style="padding:14px 18px;background:var(--surface);border-radius:var(--radius-sm);margin-bottom:16px;">';
  html += '<p style="font-size:0.88rem;"><strong>Match Rate:</strong> ' + kw.match_rate + '% &mdash; ' +
    kw.matched_count + ' of ' + kw.total_jd_keywords + ' JD keywords found in resume.</p>';
  html += '</div>';

  // Category breakdown
  if (kw.matched_categorized) {
    html += '<div style="margin-top:16px;"><h3 style="font-size:0.95rem;margin-bottom:12px;">Category Breakdown</h3><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;">';
    const allCats = new Set([...Object.keys(kw.matched_categorized || {}), ...Object.keys(kw.missing_categorized || {})]);
    allCats.forEach(cat => {
      const matched = (kw.matched_categorized && kw.matched_categorized[cat]) || [];
      const missing = (kw.missing_categorized && kw.missing_categorized[cat]) || [];
      if (matched.length + missing.length === 0) return;
      const pct = matched.length / (matched.length + missing.length) * 100;
      const barCls = pct >= 60 ? 'high' : pct >= 30 ? 'medium' : 'low';
      html += '<div class="skills-gap-card"><h4>' + cat.replace(/_/g, ' ') + '</h4>';
      html += '<div class="skills-gap-bar"><div class="skills-gap-fill ' + barCls + '" style="width:' + pct + '%"></div></div>';
      html += '<div class="skills-gap-stats"><span class="matched">+' + matched.length + ' matched</span><span class="missing">-' + missing.length + ' missing</span></div>';
      html += '</div>';
    });
    html += '</div></div>';
  }

  return html;
}

function renderSkillsGapTab(data) {
  if (!data.skills_gap) return '<p style="color:var(--text-muted);padding:20px;">Paste a job description and re-analyze to see skills gap analysis.</p>';

  let html = '<div class="skills-gap-section"><h3>&#128200; Skills Gap Analysis</h3><p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:14px;">How your skills stack up against what the job description requires, broken down by category.</p>';
  html += '<div class="skills-gap-grid">';

  for (const [cat, gap] of Object.entries(data.skills_gap)) {
    if (gap.matched_count + gap.missing_count === 0) continue;
    const barCls = gap.match_rate >= 60 ? 'high' : gap.match_rate >= 30 ? 'medium' : 'low';
    html += '<div class="skills-gap-card">';
    html += '<h4>' + cat.replace(/_/g, ' ') + '</h4>';
    html += '<div class="skills-gap-bar"><div class="skills-gap-fill ' + barCls + '" style="width:' + gap.match_rate + '%"></div></div>';
    html += '<div class="skills-gap-stats"><span class="matched">&#10003; ' + gap.matched_count + ' matched</span><span class="missing">&#10060; ' + gap.missing_count + ' missing</span></div>';
    if (gap.missing.length > 0) {
      html += '<div style="margin-top:6px;font-size:0.78rem;color:var(--text-muted);">Missing: ';
      html += gap.missing.slice(0, 5).map(k => '<span class="keyword-tag missing" style="font-size:0.72rem;padding:2px 8px;margin:2px;">' + escapeHtml(k) + '</span>').join('');
      html += '</div>';
    }
    html += '</div>';
  }

  html += '</div></div>';
  return html;
}

function renderImproverTab() {
  return '<div class="bullet-improver">' +
    '<h3>&#9997; AI Bullet Point Improver</h3>' +
    '<p class="subtitle">Paste a bullet point from your resume to get an AI-enhanced version with STAR context and actionable suggestions.</p>' +
    '<div class="bullet-input-group">' +
      '<input type="text" id="bulletInput" placeholder="e.g. Was responsible for managing a team of 5 developers" autocomplete="off">' +
      '<button onclick="improveBullet()">Improve</button>' +
    '</div>' +
    '<div id="bulletResult"></div>' +
    '<div class="batch-improve">' +
      '<h4>Improve All Bullet Points</h4>' +
      '<p style="color:var(--text-muted);font-size:0.82rem;margin-bottom:10px;">Extracted ' + (currentData && currentData.ats_score ? 'from your resume' : '') + '</p>' +
      '<button class="btn btn-sm" onclick="improveAllBullets()">Improve All Bullets</button>' +
      '<div id="batchResult" class="batch-list" style="margin-top:12px;"></div>' +
    '</div>' +
  '</div>';
}

function renderResumeTab(data) {
  let html = '';
  if (data.contact) {
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;">';
    const c = data.contact;
    html += '<span class="contact-badge ' + (c.emails.length ? 'found' : 'missing') + '">&#9993; ' + (c.emails.length ? c.emails[0] : 'No email') + '</span>';
    html += '<span class="contact-badge ' + (c.phones.length ? 'found' : 'missing') + '">&#9742; ' + (c.phones.length ? c.phones[0] : 'No phone') + '</span>';
    html += '<span class="contact-badge ' + (c.linkedin.length ? 'found' : 'missing') + '">&#128279; ' + (c.linkedin.length ? 'LinkedIn' : 'No LinkedIn') + '</span>';
    html += '</div>';
  }

  if (data.resume_text) {
    let text = escapeHtml(data.resume_text);
    if (data.keyword_match) {
      data.keyword_match.matched.forEach(k => {
        const re = new RegExp('\\b' + escapeRegex(k) + '\\b', 'gi');
        text = text.replace(re, '<span class="highlight-matched">$&</span>');
      });
    }
    html += '<h3 style="font-size:0.95rem;margin-bottom:10px;">Resume Text <span style="color:var(--text-muted);font-weight:400;font-size:0.82rem;">(matched keywords highlighted in green)</span></h3>';
    html += '<div class="text-preview">' + text + '</div>';
  }
  return html;
}

function renderNoJD(data) {
  let html = '<div style="background:var(--surface);border-radius:var(--radius);padding:28px;text-align:center;">';
  html += '<div style="font-size:2.5rem;margin-bottom:10px;">&#128200;</div>';
  html += '<h3 style="margin-bottom:8px;">Resume Parsed Successfully</h3>';
  html += '<p style="color:var(--text-muted);margin-bottom:16px;">' + (data.stats ? data.stats.word_count + ' words extracted. ' : '') + 'Paste a job description above and re-analyze to get ATS scoring, keyword matching, and skills gap analysis.</p>';

  if (data.contact) {
    html += '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:16px;">';
    const c = data.contact;
    html += '<span class="contact-badge ' + (c.emails.length ? 'found' : 'missing') + '">&#9993; ' + (c.emails.length ? c.emails[0] : 'No email') + '</span>';
    html += '<span class="contact-badge ' + (c.phones.length ? 'found' : 'missing') + '">&#9742; ' + (c.phones.length ? c.phones[0] : 'No phone') + '</span>';
    html += '<span class="contact-badge ' + (c.linkedin.length ? 'found' : 'missing') + '">&#128279; ' + (c.linkedin.length ? 'LinkedIn' : 'No LinkedIn') + '</span>';
    html += '</div>';
  }

  if (data.resume_text) {
    html += '<details style="text-align:left;"><summary style="cursor:pointer;color:var(--primary);font-size:0.9rem;font-weight:600;padding:8px 0;">View Extracted Resume Text</summary>';
    html += '<div class="text-preview" style="margin-top:10px;">' + escapeHtml(data.resume_text) + '</div></details>';
  }

  html += '</div>';
  return html;
}

// Radar Chart
function drawRadarChart(ats) {
  const canvas = document.getElementById('radarChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.parentElement.clientWidth || 300;
  const H = 240;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = W * dpr;
  canvas.height = H * dpr;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(dpr, dpr);

  const cx = W / 2;
  const cy = H / 2 + 5;
  const r = Math.min(W, H) / 2.7;

  const labels = ats.radar_labels || [];
  const values = ats.radar_values || [];
  const count = labels.length;
  const angleStep = (Math.PI * 2) / count;
  const startAngle = -Math.PI / 2;

  ctx.clearRect(0, 0, W, H);

  // Grid
  for (let level = 1; level <= 3; level++) {
    const radius = (r / 3) * level;
    ctx.beginPath();
    for (let i = 0; i <= count; i++) {
      const angle = startAngle + i * angleStep;
      const x = cx + radius * Math.cos(angle);
      const y = cy + radius * Math.sin(angle);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.strokeStyle = 'rgba(148,163,184,0.15)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Axes
  for (let i = 0; i < count; i++) {
    const angle = startAngle + i * angleStep;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + r * Math.cos(angle), cy + r * Math.sin(angle));
    ctx.strokeStyle = 'rgba(148,163,184,0.12)';
    ctx.stroke();
  }

  // Data fill
  ctx.beginPath();
  for (let i = 0; i <= count; i++) {
    const idx = i % count;
    const val = Math.min(values[idx] || 0, 100) / 100;
    const angle = startAngle + idx * angleStep;
    const x = cx + r * val * Math.cos(angle);
    const y = cy + r * val * Math.sin(angle);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(99,102,241,0.25)';
  ctx.fill();
  ctx.strokeStyle = '#6366f1';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Data points
  for (let i = 0; i < count; i++) {
    const val = Math.min(values[i] || 0, 100) / 100;
    const angle = startAngle + i * angleStep;
    const x = cx + r * val * Math.cos(angle);
    const y = cy + r * val * Math.sin(angle);
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#6366f1';
    ctx.fill();
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  // Labels
  ctx.font = '10px -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  for (let i = 0; i < count; i++) {
    const angle = startAngle + i * angleStep;
    const labelR = r + 22;
    const x = cx + labelR * Math.cos(angle);
    const y = cy + labelR * Math.sin(angle);
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(labels[i], x, y);
  }

  // Center score
  ctx.font = 'bold 16px -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const sc = ats.total_score;
  ctx.fillStyle = sc >= 70 ? '#10b981' : sc >= 40 ? '#f59e0b' : '#ef4444';
  ctx.fillText(Math.round(sc) + '%', cx, cy - 4);
  ctx.font = '9px -apple-system, sans-serif';
  ctx.fillStyle = '#94a3b8';
  ctx.fillText('OVERALL', cx, cy + 14);
}

// Tabs
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      const tab = document.getElementById('tab-' + btn.dataset.tab);
      if (tab) tab.classList.add('active');
    });
  });
}

// Bullet improver single
async function improveBullet() {
  const input = document.getElementById('bulletInput');
  const div = document.getElementById('bulletResult');
  const text = input.value.trim();
  if (!text) return;

  div.innerHTML = '<p style="color:var(--text-muted);font-size:0.88rem;">Improving...</p>';

  try {
    const res = await fetch('/api/improve-single-bullet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bullet: text })
    });
    const data = await res.json();
    if (data.error) { div.innerHTML = '<p style="color:var(--error);">' + data.error + '</p>'; return; }

    const r = data.result;
    let html = '<div class="bullet-result">';
    html += '<div class="original"><strong>Original:</strong> ' + escapeHtml(r.original) + '</div>';
    html += '<div class="improved"><strong>Improved:</strong> ' + escapeHtml(r.improved) + '</div>';
    if (r.changes && r.changes.length) {
      html += '<ul class="changes">';
      r.changes.forEach(c => html += '<li>' + escapeHtml(c) + '</li>');
      html += '</ul>';
    }
    if (r.star_context) {
      html += '<div class="star-context"><strong>STAR Context:</strong>\n' + escapeHtml(r.star_context) + '</div>';
    }
    html += '</div>';
    div.innerHTML = html;
  } catch (err) {
    div.innerHTML = '<p style="color:var(--error);">Error: ' + err.message + '</p>';
  }
}

// Batch improve
async function improveAllBullets() {
  const div = document.getElementById('batchResult');
  const text = currentData ? currentData.resume_text : '';
  if (!text) { div.innerHTML = '<p style="color:var(--text-muted);">No resume text available. Upload a resume first.</p>'; return; }

  const lines = text.split('\n').filter(l => l.trim().match(/^[\s]*[•\-*\d+.]/)).map(l => l.trim());
  if (!lines.length) {
    const words = text.split(/[.!?\n]/).filter(s => s.trim().length > 20).slice(0, 10);
    if (!words.length) { div.innerHTML = '<p style="color:var(--text-muted);">Could not extract bullet points. Paste one manually above.</p>'; return; }
    div.innerHTML = '<p style="color:var(--text-muted);">Improving ' + words.length + ' extracted phrases...</p>';
    const results = [];
    for (const w of words) {
      try {
        const res = await fetch('/api/improve-single-bullet', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bullet: w.trim() })
        });
        const data = await res.json();
        if (data.result) results.push(data.result);
      } catch (e) {}
    }
    renderBatchResults(results, div);
    return;
  }

  div.innerHTML = '<p style="color:var(--text-muted);">Improving ' + lines.length + ' bullet points...</p>';
  try {
    const res = await fetch('/api/improve-all-bullets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bullets: lines })
    });
    const data = await res.json();
    if (data.results) renderBatchResults(data.results, div);
    else div.innerHTML = '<p style="color:var(--error);">Error processing bullets.</p>';
  } catch (err) {
    div.innerHTML = '<p style="color:var(--error);">Error: ' + err.message + '</p>';
  }
}

function renderBatchResults(results, div) {
  if (!results.length) { div.innerHTML = '<p style="color:var(--text-muted);">No results returned.</p>'; return; }
  let html = '';
  results.forEach((r, i) => {
    html += '<div class="batch-item">';
    html += '<div class="batch-original">#' + (i + 1) + ': ' + escapeHtml(r.original.length > 80 ? r.original.slice(0, 80) + '...' : r.original) + '</div>';
    html += '<div class="batch-improved">&#9654; ' + escapeHtml(r.improved.length > 100 ? r.improved.slice(0, 100) + '...' : r.improved) + '</div>';
    html += '</div>';
  });
  div.innerHTML = html;
}

// Utils
function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Auto-resize radar on window resize
window.addEventListener('resize', () => {
  if (currentData && currentData.ats_score) drawRadarChart(currentData.ats_score);
});
