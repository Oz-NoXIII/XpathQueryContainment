from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery
from view.tpq_visualizer import TreePatternQueryVisualizer


DEFAULT_Q1 = "self[(lab=*) & ?ancestor[(lab=a)] & ?descendant[(lab=b)]]/descendant[(lab=c)]"
DEFAULT_Q2 = "self[(lab=*) & ?parent[(lab=a)] & ?descendant[(lab=b)]]/descendant[(lab=c)]"


class XPathContainmentPage:
	"""Interactive page for the XPath → TPQ containment workflow."""

	def __init__(self, q1_expression: str | None = None, q2_expression: str | None = None):
		self.q1_expression = q1_expression or DEFAULT_Q1
		self.q2_expression = q2_expression or DEFAULT_Q2
		self._theme_assets = TreePatternQueryVisualizer(TreePatternQuery(QueryNode("a")))

	def _theme_switch_html(self) -> str:
		return self._theme_assets._theme_switch_html()

	def _theme_switch_script(self) -> str:
		return self._theme_assets._theme_switch_script()

	def to_html(self, title: str = "Vérification d'inclusion XPath via homomorphismes") -> str:
		template = Template(
			"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>$title</title>
  <style>
    :root { color-scheme: light dark; --bg:#f4f7fb; --text:#102a43; --header-bg:#fff; --border:#d9e2ec; --hint:#486581; --panel-bg:#fff; --panel-alt-bg:#f0f4f8; --shadow:rgba(16,42,67,.08); --primary:#1f4e79; --primary-hover:#163d5d; --danger:#c44536; --danger-hover:#9e372b; --success:#2f855a; --warning:#b7791f; --node-fill:#f7fbff; --json-bg:#f0f4f8; }
    @media (prefers-color-scheme: dark) { :root:not([data-theme='light']) { --bg:#0f1720; --text:#e6edf5; --header-bg:#111b26; --border:#2a3a4a; --hint:#9ab1c9; --panel-bg:#111b26; --panel-alt-bg:#172534; --shadow:rgba(0,0,0,.45); --primary:#2c5f8f; --primary-hover:#3a75ad; --danger:#d65f4c; --danger-hover:#e07c67; --success:#3ea76a; --warning:#c9953d; --node-fill:#173047; --json-bg:#172534; } }
    :root[data-theme='light'] { color-scheme: light; }
    :root[data-theme='dark'] { color-scheme: dark; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Arial, Helvetica, sans-serif; background:var(--bg); color:var(--text); min-height:100vh; display:flex; flex-direction:column; }
    header { padding:16px 20px 12px; background:var(--header-bg); border-bottom:1px solid var(--border); box-shadow:0 2px 8px var(--shadow); display:flex; flex-direction:column; gap:12px; }
    .header-top { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap; }
    .header-copy { max-width:980px; }
    h1 { margin:0 0 6px; font-size:20px; }
    .hint { margin:0; font-size:13px; color:var(--hint); line-height:1.45; }
    .toolbar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
    button, .theme-option { appearance:none; border:none; border-radius:8px; padding:8px 12px; font-size:13px; cursor:pointer; color:white; background:var(--primary); transition:background .2s, transform .1s; }
    button:hover, .theme-option:hover { background:var(--primary-hover); }
    button:active { transform:translateY(1px); }
    .ghost { background:transparent; color:var(--text); border:1px solid var(--border); }
    .ghost:hover { background:var(--panel-alt-bg); }
    .danger { background:var(--danger); }
    .danger:hover { background:var(--danger-hover); }
    main { flex:1; display:grid; grid-template-columns: 420px 1fr; gap:14px; padding:14px; min-height:0; }
    .panel { background:var(--panel-bg); border:1px solid var(--border); border-radius:14px; box-shadow:0 6px 20px var(--shadow); min-height:0; }
    .panel header { background:transparent; box-shadow:none; border-bottom:1px solid var(--border); padding:12px 12px 10px; gap:10px; }
    .panel h2 { margin:0; font-size:16px; }
    .panel-body { padding:12px; display:grid; gap:12px; }
    .field { display:grid; gap:6px; }
    .field label { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--hint); }
    .field textarea { width:100%; min-height:190px; resize:vertical; border:1px solid var(--border); border-radius:10px; background:var(--json-bg); color:var(--text); padding:10px 12px; font:inherit; font-family:Consolas, 'Courier New', monospace; }
    .status { margin:0; font-size:13px; color:var(--hint); white-space:pre-wrap; line-height:1.45; }
    .status.is-error { color:#e07c67; }
    .status.is-success { color:#4ab97a; }
    .result-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:12px; }
    .result-card { border:1px solid var(--border); border-radius:12px; background:var(--panel-alt-bg); overflow:hidden; min-width:0; }
    .result-card.full { grid-column:1 / -1; }
    .result-card h3 { margin:0; padding:10px 12px; font-size:14px; border-bottom:1px solid var(--border); }
    .result-card .card-body { padding:12px; overflow:auto; }
    .svg-slot { min-height:220px; display:flex; align-items:center; justify-content:center; }
    .svg-slot svg { max-width:100%; height:auto; }
    .summary { display:grid; gap:8px; }
    .summary strong { color:var(--text); }
    .attempts { width:100%; border-collapse:collapse; font-size:13px; }
    .attempts th, .attempts td { border-bottom:1px solid var(--border); padding:8px 6px; text-align:left; vertical-align:top; }
    .attempts th { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--hint); }
    .attempts tbody tr:nth-child(odd) { background:rgba(127, 147, 166, .06); }
    .badge { display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:4px 10px; font-size:12px; font-weight:bold; }
    .badge.is-success { background:rgba(62,167,106,.16); color:var(--success); }
    .badge.is-error { background:rgba(214,95,76,.18); color:#e07c67; }
    .badge.is-warning { background:rgba(201,149,61,.18); color:var(--warning); }
    .section-note { color:var(--hint); font-size:12px; margin:0; line-height:1.5; }
        .progress { width:100%; background:var(--panel-alt-bg); border-radius:8px; overflow:hidden; height:12px; border:1px solid var(--border); }
        .progress-bar { height:100%; width:0%; background:linear-gradient(90deg,var(--primary),var(--primary-hover)); transition:width .12s linear; }
        .progress-overlay { position:fixed; inset:0; display:none; align-items:center; justify-content:center; background:rgba(0,0,0,.12); backdrop-filter:blur(2px); z-index:9999; }
        .progress-card { background:var(--panel-bg); border:1px solid var(--border); border-radius:12px; box-shadow:0 6px 16px var(--shadow); padding:14px 16px; min-width:240px; display:grid; gap:8px; }
        .progress-percent { font-size:18px; font-weight:bold; text-align:center; }
    @media (max-width: 1200px) { main { grid-template-columns: 1fr; } .result-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <div class="header-top">
      <div class="header-copy">
        <h1>$title</h1>
        <p class="hint">Saisissez deux requêtes XPath, transformez-les en <strong>TPQ</strong>, puis lancez la méthode d’homomorphisme décrite dans <code>PC.pdf</code> : booléanisation de <code>q1</code> et <code>q2</code>, boucle sur les combinaisons <code>L</code>, construction de l’arbre canonique <code>Tc</code> à partir de <code>q1</code>, et recherche d’un homomorphisme de <code>q2</code> vers <code>Tc</code>. Si aucun homomorphisme n’existe, <code>Tc</code> est affiché comme contre-exemple.</p>
      </div>
      $theme_switch
    </div>
    <div class="toolbar">
      <button type="button" id="transform">1. Transformer XPath → TPQ</button>
      <button type="button" id="booleanize">2. Booléaniser</button>
      <button type="button" id="check-forward">3. Vérifier q1 ⊆ q2</button>
      <button type="button" id="check-backward">4. Vérifier q2 ⊆ q1</button>
      <button type="button" id="load-sample" class="ghost">Charger un exemple</button>
      <button type="button" id="reset" class="ghost">Réinitialiser</button>
    </div>
  </header>
  <main>
    <section class="panel">
      <header>
        <h2>Entrées XPath</h2>
      </header>
      <div class="panel-body">
        <div class="field">
          <label for="q1-xpath">q1</label>
          <textarea id="q1-xpath" spellcheck="false"></textarea>
        </div>
        <div class="field">
          <label for="q2-xpath">q2</label>
          <textarea id="q2-xpath" spellcheck="false"></textarea>
        </div>
        <p id="status" class="status">Entrez deux requêtes XPath puis cliquez sur « Analyser l'inclusion ».</p>
      </div>
    </section>

    <section class="panel">
      <header>
        <h2>Déroulé de la vérification</h2>
      </header>
      <div class="panel-body" style="position:relative;">
        <div id="summary" class="summary">
          <span class="badge is-warning">En attente d'analyse</span>
          <p class="section-note">Les visualisations et la liste des combinaisons <code>L</code> apparaîtront ici.</p>
        </div>
        <div id="progress-overlay" class="progress-overlay" aria-live="polite">
          <div class="progress-card">
            <div class="progress-percent" id="progress-percent">0%</div>
            <div class="progress" aria-hidden="true"><div id="progress-bar" class="progress-bar"></div></div>
            <div id="progress-label" style="font-size:12px;color:var(--hint);text-align:center;">0 / 0</div>
          </div>
        </div>
        <div class="result-grid">
          <article class="result-card">
            <h3>q1 — TPQ brut</h3>
            <div class="card-body svg-slot" id="raw-q1">Aucun rendu.</div>
          </article>
          <article class="result-card">
            <h3>q2 — TPQ brut</h3>
            <div class="card-body svg-slot" id="raw-q2">Aucun rendu.</div>
          </article>
          <article class="result-card">
            <h3>q1 — booléanisé</h3>
            <div class="card-body svg-slot" id="bool-q1">Aucun rendu.</div>
          </article>
          <article class="result-card">
            <h3>q2 — booléanisé</h3>
            <div class="card-body svg-slot" id="bool-q2">Aucun rendu.</div>
          </article>
          <article class="result-card full">
            <h3>Combinaisons L et résultat de l’homomorphisme</h3>
            <div class="card-body">
              <!-- Collapsed by default: summary line that can be expanded to view the full table -->
              <details>
                <summary style="cursor:pointer;">Afficher les combinaisons L et résultats (cliquer pour dérouler)</summary>
                <div style="margin-top:8px;">
                  <table class="attempts">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>L</th>
                        <th>Résultat</th>
                      </tr>
                    </thead>
                    <tbody id="attempts-body">
                      <tr><td colspan="3">Aucune analyse effectuée.</td></tr>
                    </tbody>
                  </table>
                </div>
              </details>
            </div>
          </article>
          <article class="result-card full">
            <h3>Arbre canonique Tc / contre-exemple</h3>
            <div class="card-body svg-slot" id="counterexample-tree">Aucun contre-exemple pour le moment.</div>
          </article>
        </div>
      </div>
    </section>
  </main>
  <script>
$theme_script
    const initialExpressions = { q1: $q1_expression, q2: $q2_expression };
    const q1Input = document.getElementById('q1-xpath');
    const q2Input = document.getElementById('q2-xpath');
    const statusBox = document.getElementById('status');
    const summaryBox = document.getElementById('summary');
    const rawQ1Box = document.getElementById('raw-q1');
    const rawQ2Box = document.getElementById('raw-q2');
    const boolQ1Box = document.getElementById('bool-q1');
    const boolQ2Box = document.getElementById('bool-q2');
    const counterexampleBox = document.getElementById('counterexample-tree');
    const attemptsBody = document.getElementById('attempts-body');
    const state = { raw: null, bool: null };

    function setStatus(message, kind) {
      statusBox.textContent = message;
      statusBox.className = ('status ' + (kind || '')).trim();
    }

    // Minimal interactive hydration for TPQ SVGs (based on tpq-xml page)
    const canvasState = {};

    function renderSvg(slot, svg, canvasName) {
      if (!slot) return;
      slot.innerHTML = svg || '<em>Aucun rendu.</em>';
      if (canvasName && svg) {
        hydrateCanvas(canvasName);
      } else if (canvasName) {
        // reset state
        const state = canvasState[canvasName];
        if (state) {
          state.svg = null;
          state.nodes = new Map();
          state.edges = [];
          state.dragged = null;
        }
      }
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, function(ch) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
      });
    }

    // Progress polling utilities
    let _progressPollTimer = null;
    function showProgressBar() {
      const wrap = document.getElementById('progress-overlay');
      if (wrap) wrap.style.display = 'flex';
      const bar = document.getElementById('progress-bar');
      if (bar) bar.style.width = '0%';
      const label = document.getElementById('progress-label');
      if (label) label.textContent = 'En attente du premier point de progression...';
      const percent = document.getElementById('progress-percent');
      if (percent) percent.textContent = '0%';
    }

    function hideProgressBar() {
      const wrap = document.getElementById('progress-overlay');
      if (wrap) wrap.style.display = 'none';
    }

    function startProgressPolling(progressId, onDone) {
      stopProgressPolling();
      if (!progressId) return;
      _progressPollTimer = setInterval(async function() {
        try {
          const resp = await fetch('/containment/progress?progress_id=' + encodeURIComponent(progressId));
          if (!resp.ok) return;
          const data = await resp.json();
          const bar = document.getElementById('progress-bar');
          const label = document.getElementById('progress-label');
          if (data && data.total !== undefined && data.attempted !== undefined) {
            const pct = Math.min(100, Math.round((data.total > 0) ? (data.attempted / data.total) * 100 : 0));
            if (bar) bar.style.width = pct + '%';
            if (label) label.textContent = data.total > 0 ? (data.attempted + ' / ' + data.total) : (data.attempted + ' / …');
            const percent = document.getElementById('progress-percent');
            if (percent) percent.textContent = pct + '%';
          }
          if (data && data.done) {
            stopProgressPolling();
            if (typeof onDone === 'function') {
              onDone(data);
            }
          }
        } catch (e) {
          // ignore polling errors
        }
      }, 250);
    }

    function stopProgressPolling() {
      if (_progressPollTimer) {
        clearInterval(_progressPollTimer);
        _progressPollTimer = null;
      }
    }

    // Minimal SVG hydration to allow dragging nodes (adapted from tpq-xml page)
    function getNodeIndex(nodeId) {
      const parts = String(nodeId || '').split('_');
      return parts.length ? parts[parts.length - 1] : null;
    }

    function getCanvasNode(canvasName, nodeId) {
      const state = canvasState[canvasName];
      if (!state) return null;
      if (state.nodeIdMap && nodeId && state.nodeIdMap[nodeId]) {
        return state.nodeIdMap[nodeId];
      }
      const nodeIndex = getNodeIndex(nodeId);
      return nodeIndex !== null ? state.nodes.get(nodeIndex) || null : null;
    }

    function updateCanvasEdges(canvasName) {
      const state = canvasState[canvasName];
      if (!state || !state.svg) return;
      state.edges.forEach(function(line) {
        const source = state.nodes.get(line.dataset.sourceIndex);
        const target = state.nodes.get(line.dataset.targetIndex);
        if (!source || !target) return;
        const sx = parseFloat(source.circle.getAttribute('cx')) || 0;
        const sy = parseFloat(source.circle.getAttribute('cy')) || 0;
        const tx = parseFloat(target.circle.getAttribute('cx')) || 0;
        const ty = parseFloat(target.circle.getAttribute('cy')) || 0;
        const sr = parseFloat(source.circle.getAttribute('r')) || 24;
        const tr = parseFloat(target.circle.getAttribute('r')) || 24;
        const dx = tx - sx;
        const dy = ty - sy;
        const length = Math.hypot(dx, dy) || 1;
        const ux = dx / length;
        const uy = dy / length;
        const x1 = sx + ux * sr;
        const y1 = sy + uy * sr;
        const x2 = tx - ux * tr;
        const y2 = ty - uy * tr;
        if (line.dataset.edgeType === 'descendant') {
          const offset = line.dataset.offset === 'positive' ? 4 : -4;
          const ox = -uy * offset;
          const oy = ux * offset;
          line.setAttribute('x1', String(x1 + ox));
          line.setAttribute('y1', String(y1 + oy));
          line.setAttribute('x2', String(x2 + ox));
          line.setAttribute('y2', String(y2 + oy));
        } else {
          line.setAttribute('x1', String(x1));
          line.setAttribute('y1', String(y1));
          line.setAttribute('x2', String(x2));
          line.setAttribute('y2', String(y2));
        }
      });
    }

    function moveCanvasNode(canvasName, nodeIndex, x, y) {
      const state = canvasState[canvasName];
      if (!state) return;
      const node = state.nodes.get(String(nodeIndex));
      if (!node || node.root) return;
      node.circle.setAttribute('cx', String(x));
      node.circle.setAttribute('cy', String(y));
      if (node.text) {
        node.text.setAttribute('x', String(x));
        node.text.setAttribute('y', String(y));
      }
      if (node.badge) {
        const br = parseFloat(node.circle.getAttribute('r')) || 0;
        const bx = x + br * 0.65;
        const by = y - br * 0.65;
        node.badge.setAttribute('cx', String(bx));
        node.badge.setAttribute('cy', String(by));
      }
      if (node.badgeText) {
        const brt = parseFloat(node.circle.getAttribute('r')) || 0;
        node.badgeText.setAttribute('x', String(x + brt * 0.65));
        node.badgeText.setAttribute('y', String(y - brt * 0.65));
      }
      updateCanvasEdges(canvasName);
    }

    function hydrateCanvas(canvasName) {
      const container = document.getElementById(canvasName);
      if (!container) return;
      const state = canvasState[canvasName] = canvasState[canvasName] || { container: container, svg: null, nodes: new Map(), edges: [], dragged: null };
      state.container = container;
      state.svg = state.container.querySelector('svg');
      state.nodes = new Map();
      state.edges = [];
      state.dragged = null;
      if (!state.svg) return;

      state.svg.style.touchAction = 'none';
      state.nodeIdMap = {};
      state.svg.querySelectorAll('circle[data-node-index]').forEach(function(circle) {
        const index = circle.dataset.nodeIndex;
        const text = state.svg.querySelector('text[data-node-index="' + index + '"]');
        const badge = state.svg.querySelector('ellipse.node-badge[data-node-index="' + index + '"]');
        const badgeText = state.svg.querySelector('text.node-badge-text[data-node-index="' + index + '"]');
        const nodeObj = {
          circle: circle,
          text: text,
          badge: badge,
          badgeText: badgeText,
          root: circle.dataset.root === 'true'
        };
        state.nodes.set(index, nodeObj);
        const nodeId = circle.dataset.nodeId || ('node_' + index);
        circle.dataset.nodeId = nodeId;
        if (text) text.dataset.nodeId = nodeId;
        if (badge) badge.dataset.nodeId = nodeId;
        if (badgeText) badgeText.dataset.nodeId = nodeId;
        state.nodeIdMap[nodeId] = nodeObj;
        circle.style.cursor = circle.dataset.root === 'true' ? 'default' : 'grab';
      });
      state.svg.querySelectorAll('line[data-source-index]').forEach(function(line) {
        state.edges.push(line);
      });

      if (!state.svg.dataset.dragBound) {
        state.svg.dataset.dragBound = 'true';
        state.svg.addEventListener('pointerdown', function(event) {
          const handle = event.target.closest('[data-node-index]');
          if (!handle) return;
          const index = handle.dataset.nodeIndex;
          const node = state.nodes.get(index);
          if (!node || node.root) return;
          const rect = state.svg.getBoundingClientRect();
          const circleRect = node.circle.getBoundingClientRect();
          state.dragged = {
            index: index,
            offsetX: event.clientX - rect.left - (circleRect.left - rect.left + circleRect.width / 2),
            offsetY: event.clientY - rect.top - (circleRect.top - rect.top + circleRect.height / 2)
          };
          state.svg.setPointerCapture(event.pointerId);
          event.preventDefault();
        });
        state.svg.addEventListener('pointermove', function(event) {
          if (!state.dragged) return;
          const rect = state.svg.getBoundingClientRect();
          moveCanvasNode(canvasName, state.dragged.index, event.clientX - rect.left - state.dragged.offsetX, event.clientY - rect.top - state.dragged.offsetY);
        });
        state.svg.addEventListener('pointerup', function() { state.dragged = null; });
        state.svg.addEventListener('pointerleave', function() { state.dragged = null; });
      }

      updateCanvasEdges(canvasName);
    }

    function renderAttempts(attempts) {
      attemptsBody.innerHTML = '';
      if (!attempts || !attempts.length) {
        attemptsBody.innerHTML = '<tr><td colspan="3">Aucune combinaison L generee.</td></tr>';
        return;
      }
      attempts.forEach(function(attempt, index) {
        const row = document.createElement('tr');
        const status = attempt.exists ? '<span class="badge is-success">Homomorphisme trouvé</span>' : '<span class="badge is-error">Aucun homomorphisme</span>';
        // Make the L column collapsible (closed by default) with message and mapping details inside
        const detailsHtml = '<details>' +
          '<summary style="cursor:pointer;">' + escapeHtml(JSON.stringify(attempt.L)) + '</summary>' +
          '<div style="margin-top:8px;font-size:12px;color:var(--hint);">' +
            '<div><strong>Message:</strong> ' + escapeHtml(attempt.message || '') + '</div>' +
            '<pre style="margin-top:6px;white-space:pre-wrap;">' + escapeHtml(JSON.stringify(attempt.mapping || [], null, 2)) + '</pre>' +
          '</div>' +
        '</details>';
        row.innerHTML = '<td>' + (index + 1) + '</td><td>' + detailsHtml + '</td><td>' + status + '</td>';
        attemptsBody.appendChild(row);
      });
    }

    function renderConclusion(data, label) {
      summaryBox.innerHTML = '<span class="badge ' + (data.contained ? 'is-success' : 'is-error') + '">' + label + '</span><p class="section-note">' + escapeHtml(data.summary || '') + '</p>';
      renderAttempts(data.attempts || []);
      renderSvg(counterexampleBox, data.counterexample_tree || "<em>Aucun contre-exemple : inclusion verifiee.</em>", 'counterexample-tree');
      setStatus(data.summary || 'Analyse terminée.', data.contained ? 'is-success' : 'is-error');
    }

    function renderProgress(data) {
      const bar = document.getElementById('progress-bar');
      const label = document.getElementById('progress-label');
      const percent = document.getElementById('progress-percent');
      if (!data) return;
      if (data.total !== undefined && data.attempted !== undefined) {
        const pct = Math.min(100, Math.round((data.total > 0) ? (data.attempted / data.total) * 100 : 0));
        if (bar) bar.style.width = pct + '%';
        if (label) label.textContent = data.total > 0 ? (data.attempted + ' / ' + data.total) : (data.attempted + ' / …');
        if (percent) percent.textContent = pct + '%';
      }
    }

    async function transform() {
      const q1 = q1Input.value.trim();
      const q2 = q2Input.value.trim();
      if (!q1 || !q2) {
        setStatus('Les deux expressions XPath doivent être renseignées.', 'is-error');
        return;
      }
      setStatus('Transformation XPath -> TPQ en cours...', 'is-success');
      try {
        const response = await fetch('/containment/transform', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ q1: q1, q2: q2 })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data && data.message ? data.message : 'Erreur serveur');
        state.raw = data;
        state.bool = null;
        renderSvg(rawQ1Box, data.q1 && data.q1.svg ? data.q1.svg : '', 'raw-q1');
        renderSvg(rawQ2Box, data.q2 && data.q2.svg ? data.q2.svg : '', 'raw-q2');
        renderSvg(boolQ1Box, '<em>Booléanisez pour voir cette étape.</em>', 'bool-q1');
        renderSvg(boolQ2Box, '<em>Booléanisez pour voir cette étape.</em>', 'bool-q2');
        summaryBox.innerHTML = '<span class="badge is-success">TPQ prêts</span><p class="section-note">Les deux requêtes ont été transformées en TPQ.</p>';
        attemptsBody.innerHTML = '<tr><td colspan="3">Lancez la booléanisation puis la vérification.</td></tr>';
        counterexampleBox.innerHTML = '<em>Aucun contre-exemple pour le moment.</em>';
      } catch (error) {
        setStatus('Erreur : ' + error.message, 'is-error');
      }
    }

    async function booleanize() {
      if (!state.raw) {
        setStatus('Commencez par transformer les requêtes XPath.', 'is-error');
        return;
      }
      setStatus('Booléanisation en cours...', 'is-success');
      try {
        const response = await fetch('/containment/booleanize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ q1: state.raw.q1.payload, q2: state.raw.q2.payload })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data && data.message ? data.message : 'Erreur serveur');
        state.bool = data;
        renderSvg(boolQ1Box, data.q1 && data.q1.svg ? data.q1.svg : '', 'bool-q1');
        renderSvg(boolQ2Box, data.q2 && data.q2.svg ? data.q2.svg : '', 'bool-q2');
        summaryBox.innerHTML = '<span class="badge is-success">Booléanisation terminée</span><p class="section-note">Vous pouvez maintenant vérifier q1 ⊆ q2 ou q2 ⊆ q1.</p>';
      } catch (error) {
        setStatus('Erreur : ' + error.message, 'is-error');
      }
    }

    async function check(direction) {
      if (!state.bool) {
        setStatus('Commencez par booléaniser les TPQ.', 'is-error');
        return;
      }
      setStatus("Recherche de l homomorphisme en cours...", 'is-success');
      // create a progress id for server-side progress reporting
      const progressId = 'p-' + Math.random().toString(36).slice(2, 10);
      showProgressBar();
      startProgressPolling(progressId, function(progressData) {
        if (progressData && progressData.result) {
          hideProgressBar();
          renderConclusion(progressData.result, direction === 'forward' ? 'q1 ⊆ q2' : 'q2 ⊆ q1');
        } else {
          hideProgressBar();
          setStatus('Analyse terminée, mais le résultat final est indisponible.', 'is-error');
        }
      });
      try {
        const response = await fetch('/containment/check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source: state.bool.q1.payload,
            target: state.bool.q2.payload,
            direction: direction,
            progress_id: progressId,
            source_name: direction === 'forward' ? 'q1' : 'q2',
            target_name: direction === 'forward' ? 'q2' : 'q1'
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data && data.message ? data.message : 'Erreur serveur');
        if (data && data.progress_id) {
          renderProgress({ attempted: 0, total: 0, done: false });
          return;
        }
        stopProgressPolling();
        hideProgressBar();
        renderConclusion(data, direction === 'forward' ? 'q1 ⊆ q2' : 'q2 ⊆ q1');
      } catch (error) {
        stopProgressPolling();
        hideProgressBar();
        setStatus('Erreur : ' + error.message, 'is-error');
      }
    }

    function loadSample() {
      q1Input.value = initialExpressions.q1;
      q2Input.value = initialExpressions.q2;
      state.raw = null;
      state.bool = null;
      renderSvg(rawQ1Box, 'Aucun rendu.', 'raw-q1');
      renderSvg(rawQ2Box, 'Aucun rendu.', 'raw-q2');
      renderSvg(boolQ1Box, 'Aucun rendu.', 'bool-q1');
      renderSvg(boolQ2Box, 'Aucun rendu.', 'bool-q2');
      renderSvg(counterexampleBox, 'Aucun contre-exemple pour le moment.', 'counterexample-tree');
      attemptsBody.innerHTML = '<tr><td colspan="3">Aucune analyse effectuée.</td></tr>';
      summaryBox.innerHTML = '<span class="badge is-success">Prêt</span>';
      setStatus('Exemple chargé.', 'is-success');
    }

    function resetPage() {
      q1Input.value = initialExpressions.q1;
      q2Input.value = initialExpressions.q2;
      state.raw = null;
      state.bool = null;
      rawQ1Box.innerHTML = 'Aucun rendu.';
      rawQ2Box.innerHTML = 'Aucun rendu.';
      boolQ1Box.innerHTML = 'Aucun rendu.';
      boolQ2Box.innerHTML = 'Aucun rendu.';
      counterexampleBox.innerHTML = 'Aucun contre-exemple pour le moment.';
      attemptsBody.innerHTML = '<tr><td colspan="3">Aucune analyse effectuée.</td></tr>';
      summaryBox.innerHTML = '<span class="badge is-success">Prêt</span>';
      setStatus("1. Transformer les requetes, 2. Booleianiser, 3. Verifier dans un sens ou dans l autre.");
    }

    q1Input.value = initialExpressions.q1;
    q2Input.value = initialExpressions.q2;
    document.getElementById('transform').addEventListener('click', transform);
    document.getElementById('booleanize').addEventListener('click', booleanize);
    document.getElementById('check-forward').addEventListener('click', function() { check('forward'); });
    document.getElementById('check-backward').addEventListener('click', function() { check('backward'); });
    document.getElementById('load-sample').addEventListener('click', loadSample);
    document.getElementById('reset').addEventListener('click', resetPage);
  </script>
</body>
</html>"""
		)

		return template.substitute(
			title=escape(title),
			theme_switch=self._theme_switch_html(),
			theme_script=self._theme_switch_script(),
			q1_expression=json.dumps(self.q1_expression, ensure_ascii=False),
			q2_expression=json.dumps(self.q2_expression, ensure_ascii=False),
		)

	def save_html(self, path: str | Path):
		output_path = Path(path)
		output_path.write_text(self.to_html(), encoding="utf-8")
		return output_path






