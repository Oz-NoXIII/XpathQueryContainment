from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery
from view.tpq_visualizer import TreePatternQueryVisualizer


DEFAULT_XPATH = "self[(lab = a)&?child[(lab = b)]]"
DEFAULT_XML = """<a><b /><c /></a>"""


class TPQXmlHomomorphismPage:
	"""Page dédiée au homomorphisme entre un TPQ et un arbre de données XML."""

	def __init__(self, xpath_expression: str | None = None, xml_text: str | None = None):
		self.xpath_expression = xpath_expression or DEFAULT_XPATH
		self.xml_text = xml_text or DEFAULT_XML
		self._theme_assets = TreePatternQueryVisualizer(TreePatternQuery(QueryNode("a")))

	def _theme_switch_html(self) -> str:
		return self._theme_assets._theme_switch_html()

	def _theme_switch_script(self) -> str:
		return self._theme_assets._theme_switch_script()

	def to_html(self, title: str = "Homomorphisme TPQ ↔ arbre XML") -> str:
		template = Template(
			"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>$title</title>
  <style>
    :root { color-scheme: light dark; --bg:#f4f7fb; --text:#102a43; --header-bg:#fff; --border:#d9e2ec; --hint:#486581; --panel-bg:#fff; --panel-alt-bg:#f0f4f8; --shadow:rgba(16,42,67,.08); --primary:#1f4e79; --primary-hover:#163d5d; --success:#2f855a; --danger:#c44536; --danger-hover:#9e372b; --node-fill:#f7fbff; --json-bg:#f0f4f8; }
    @media (prefers-color-scheme: dark) { :root:not([data-theme='light']) { --bg:#0f1720; --text:#e6edf5; --header-bg:#111b26; --border:#2a3a4a; --hint:#9ab1c9; --panel-bg:#111b26; --panel-alt-bg:#172534; --shadow:rgba(0,0,0,.45); --primary:#2c5f8f; --primary-hover:#3a75ad; --success:#3ea76a; --danger:#d65f4c; --danger-hover:#e07c67; --node-fill:#173047; --json-bg:#172534; } }
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
    .ghost { background:transparent; color:var(--text); border:1px solid var(--border); }
    .ghost:hover { background:var(--panel-alt-bg); }
    main { flex:1; display:grid; grid-template-columns: 420px 1fr; gap:14px; padding:14px; min-height:0; }
    .panel { background:var(--panel-bg); border:1px solid var(--border); border-radius:14px; box-shadow:0 6px 20px var(--shadow); min-height:0; }
    .panel header { background:transparent; box-shadow:none; border-bottom:1px solid var(--border); padding:12px 12px 10px; gap:10px; }
    .panel h2 { margin:0; font-size:16px; }
    .panel-body { padding:12px; display:grid; gap:12px; }
    .field { display:grid; gap:6px; }
    .field label { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--hint); }
    .field textarea { width:100%; min-height:180px; resize:vertical; border:1px solid var(--border); border-radius:10px; background:var(--json-bg); color:var(--text); padding:10px 12px; font:inherit; font-family:Consolas, 'Courier New', monospace; }
    .status { margin:0; font-size:13px; color:var(--hint); white-space:pre-wrap; line-height:1.45; }
    .status.is-error { color:#e07c67; }
    .status.is-success { color:#4ab97a; }
    .result-stage { position:relative; }
    .result-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:12px; position:relative; z-index:1; }
    .result-card { border:1px solid var(--border); border-radius:12px; background:var(--panel-alt-bg); overflow:hidden; min-width:0; }
    .result-card.full { grid-column:1 / -1; }
    .result-card h3 { margin:0; padding:10px 12px; font-size:14px; border-bottom:1px solid var(--border); }
    .result-card .card-body { padding:12px; overflow:auto; }
    .svg-slot { min-height:220px; display:flex; align-items:center; justify-content:center; position:relative; }
    .svg-slot svg { max-width:100%; height:auto; }
    .mapping-list { margin:0; padding-left:18px; line-height:1.5; font-size:13px; }
    .badge { display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:4px 10px; font-size:12px; font-weight:bold; }
    .badge.is-success { background:rgba(62,167,106,.16); color:var(--success); }
    .badge.is-error { background:rgba(214,95,76,.18); color:#e07c67; }
    .homomorphism-overlay { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible; z-index:3; }
    .homomorphism-overlay .homomorphism-arrow { fill:none; stroke-width:3; stroke-linecap:round; stroke-linejoin:round; }
    .homomorphism-overlay .homomorphism-arrow.is-committed { stroke:var(--success); opacity:.92; }
    .homomorphism-overlay .homomorphism-label { fill:var(--hint); font-size:11px; font-family:Arial, Helvetica, sans-serif; }
    @media (max-width: 1200px) { main { grid-template-columns: 1fr; } .result-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <div class="header-top">
      <div class="header-copy">
        <h1>$title</h1>
        <p class="hint">Cette page vérifie un homomorphisme entre un <strong>TPQ</strong> construit depuis une requête XPath et un arbre de données <strong>XML</strong> (réduit ici à un arbre de nœuds étiquetés). Utilisez d'abord <strong>Transformer la requête</strong>, puis <strong>Vérifier l'homomorphisme</strong>.</p>
      </div>
      $theme_switch
    </div>
    <div class="toolbar">
      <button type="button" id="transform">Transformer la requête</button>
      <button type="button" id="check-homomorphism">Vérifier l'homomorphisme</button>
      <button type="button" id="load-sample" class="ghost">Charger un exemple</button>
      <button type="button" id="reset" class="ghost">Réinitialiser</button>
    </div>
  </header>
  <main>
    <section class="panel">
      <header>
        <h2>Entrées</h2>
      </header>
      <div class="panel-body">
        <div class="field">
          <label for="xpath-input">Requête XPath</label>
          <textarea id="xpath-input" spellcheck="false"></textarea>
        </div>
        <div class="field">
          <label for="xml-input">Arbre XML</label>
          <textarea id="xml-input" spellcheck="false"></textarea>
        </div>
        <p id="status" class="status">Transformez d'abord la requête XPath pour afficher le TPQ correspondant.</p>
      </div>
    </section>
    <section class="panel">
      <header>
        <h2>Résultats</h2>
      </header>
      <div class="panel-body">
        <div id="summary"><span class="badge is-success">Prêt</span></div>
        <div class="result-stage">
          <div class="result-grid">
            <article class="result-card">
              <h3>TPQ</h3>
              <div class="card-body svg-slot" id="tpq-preview">Aucun rendu.</div>
            </article>
            <article class="result-card">
              <h3>Arbre XML</h3>
              <div class="card-body svg-slot" id="xml-preview">Aucun rendu.</div>
            </article>
            <article class="result-card full">
              <h3>Homomorphisme</h3>
              <div class="card-body">
                <div id="result-message">Aucun test effectué pour le moment.</div>
                <ol id="mapping" class="mapping-list"></ol>
              </div>
            </article>
          </div>
          <svg id="homomorphism-overlay" class="homomorphism-overlay" aria-hidden="true"></svg>
        </div>
      </div>
    </section>
  </main>
  <script>
$theme_script
    const initialXPath = $xpath_expression;
    const initialXml = $xml_text;
    const xpathInput = document.getElementById('xpath-input');
    const xmlInput = document.getElementById('xml-input');
    const statusBox = document.getElementById('status');
    const summaryBox = document.getElementById('summary');
    const tpqPreview = document.getElementById('tpq-preview');
    const xmlPreview = document.getElementById('xml-preview');
    const resultMessage = document.getElementById('result-message');
    const mappingList = document.getElementById('mapping');
    const homomorphismOverlay = document.getElementById('homomorphism-overlay');
    let lastTpqSvg = '';
    const homomorphismState = { active: false, mapping: [] };
    const canvasState = {
      tpq: { container: tpqPreview, svg: null, nodes: new Map(), edges: [], dragged: null },
      xml: { container: xmlPreview, svg: null, nodes: new Map(), edges: [], dragged: null }
    };

    function setStatus(message, kind) {
      statusBox.textContent = message;
      statusBox.className = ('status ' + (kind || '')).trim();
    }

    function renderSvg(slot, svg, canvasName) {
      slot.innerHTML = svg || '<em>Aucun rendu.</em>';
      if (canvasName && svg) {
        hydrateCanvas(canvasName);
      } else if (canvasName) {
        const state = canvasState[canvasName];
        if (state) {
          state.svg = null;
          state.nodes = new Map();
          state.edges = [];
          state.dragged = null;
        }
      }
      if (homomorphismState.active) {
        renderHomomorphismOverlay();
      }
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, function(ch) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
      });
    }

    function getNodeIndex(nodeId) {
      const parts = String(nodeId || '').split('_');
      return parts.length ? parts[parts.length - 1] : null;
    }

    function getCanvasNode(canvasName, nodeId) {
      const state = canvasState[canvasName];
      if (!state) return null;
      // Try direct id lookup first (server may have rendered data-node-id)
      if (state.nodeIdMap && nodeId && state.nodeIdMap[nodeId]) {
        return state.nodeIdMap[nodeId];
      }
      // Fallback: numeric index (e.g. 'node_0' -> '0')
      const nodeIndex = getNodeIndex(nodeId);
      return nodeIndex !== null ? state.nodes.get(nodeIndex) || null : null;
    }

    function getOverlayPoint(canvasName, nodeId, side) {
      if (!homomorphismOverlay) {
        return null;
      }
      const node = getCanvasNode(canvasName, nodeId);
      if (!node) {
        return null;
      }
      const rect = node.circle.getBoundingClientRect();
      const overlayRect = homomorphismOverlay.getBoundingClientRect();
      const radius = Math.max(rect.width, rect.height) / 2;
      const direction = side === 'source' ? 1 : -1;
      return {
        x: rect.left - overlayRect.left + rect.width / 2 + direction * radius * 0.85,
        y: rect.top - overlayRect.top + rect.height / 2
      };
    }

    function updateCanvasEdges(canvasName) {
      const state = canvasState[canvasName];
      if (!state || !state.svg) {
        return;
      }
      state.edges.forEach(function(line) {
        const source = state.nodes.get(line.dataset.sourceIndex);
        const target = state.nodes.get(line.dataset.targetIndex);
        if (!source || !target) {
          return;
        }
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
      if (!state) {
        return;
      }
      const node = state.nodes.get(String(nodeIndex));
      if (!node || node.root) {
        return;
      }
      node.circle.setAttribute('cx', String(x));
      node.circle.setAttribute('cy', String(y));
      if (node.text) {
        node.text.setAttribute('x', String(x));
        node.text.setAttribute('y', String(y));
      }
      if (node.badge) {
        // badges are rendered as <ellipse> — update both center coordinates so badge follows node
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
      if (homomorphismState.active) {
        renderHomomorphismOverlay();
      }
    }

    function hydrateCanvas(canvasName) {
      const state = canvasState[canvasName];
      if (!state || !state.container) {
        return;
      }
      state.svg = state.container.querySelector('svg');
      state.nodes = new Map();
      state.edges = [];
      state.dragged = null;
      if (!state.svg) {
        return;
      }

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
        // prefer explicit node id if provided by the server-side renderer
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
          if (!handle) {
            return;
          }
          const index = handle.dataset.nodeIndex;
          const node = state.nodes.get(index);
          if (!node || node.root) {
            return;
          }
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
          if (!state.dragged) {
            return;
          }
          const rect = state.svg.getBoundingClientRect();
          moveCanvasNode(canvasName, state.dragged.index, event.clientX - rect.left - state.dragged.offsetX, event.clientY - rect.top - state.dragged.offsetY);
        });
        state.svg.addEventListener('pointerup', function() {
          state.dragged = null;
        });
        state.svg.addEventListener('pointerleave', function() {
          state.dragged = null;
        });
      }

      updateCanvasEdges(canvasName);
    }

    function renderHomomorphismOverlay() {
      if (!homomorphismOverlay) {
        return;
      }
      const rect = homomorphismOverlay.getBoundingClientRect();
      homomorphismOverlay.setAttribute('viewBox', '0 0 ' + Math.max(1, rect.width) + ' ' + Math.max(1, rect.height));
      homomorphismOverlay.innerHTML = '';
      if (!homomorphismState.active) {
        return;
      }

      const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
      const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
      marker.setAttribute('id', 'homomorphism-arrowhead');
      marker.setAttribute('viewBox', '0 0 10 10');
      marker.setAttribute('refX', '8.5');
      marker.setAttribute('refY', '5');
      marker.setAttribute('markerWidth', '7');
      marker.setAttribute('markerHeight', '7');
      marker.setAttribute('orient', 'auto-start-reverse');
      const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      arrow.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
      arrow.setAttribute('fill', 'currentColor');
      marker.appendChild(arrow);
      defs.appendChild(marker);
      homomorphismOverlay.appendChild(defs);

      homomorphismState.mapping.forEach(function(item) {
        // item.source_id / item.target_id are full ids (e.g. 'source_0' / 'target_0')
        // pass canvas names ('tpq' / 'xml') to getOverlayPoint so it looks up nodes
        const sourcePoint = getOverlayPoint('tpq', item.source_id, 'source');
        const targetPoint = getOverlayPoint('xml', item.target_id, 'target');
        if (!sourcePoint || !targetPoint) {
          return;
        }

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const midX = (sourcePoint.x + targetPoint.x) / 2;
        const curve = Math.max(32, Math.abs(targetPoint.x - sourcePoint.x) * 0.25);
        const control1X = midX + curve;
        const control2X = midX - curve;
        path.setAttribute('d', 'M ' + sourcePoint.x + ' ' + sourcePoint.y + ' C ' + control1X + ' ' + sourcePoint.y + ', ' + control2X + ' ' + targetPoint.y + ', ' + targetPoint.x + ' ' + targetPoint.y);
        path.setAttribute('class', 'homomorphism-arrow is-committed');
        path.setAttribute('marker-end', 'url(#homomorphism-arrowhead)');
        homomorphismOverlay.appendChild(path);

        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('class', 'homomorphism-label');
        label.setAttribute('x', String((sourcePoint.x + targetPoint.x) / 2));
        label.setAttribute('y', String((sourcePoint.y + targetPoint.y) / 2 - 6));
        label.setAttribute('text-anchor', 'middle');
        label.textContent = item.source_label + ' → ' + item.target_label;
        homomorphismOverlay.appendChild(label);
      });
    }

    async function transformQuery() {
      const xpath = xpathInput.value.trim();
      if (!xpath) {
        setStatus('La requête XPath ne peut pas être vide.', 'is-error');
        return;
      }
      try {
        const response = await fetch('/tpq-xml/transform', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ xpath: xpath })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data && data.message ? data.message : 'Erreur serveur');
        }
        lastTpqSvg = data.svg || '';
        renderSvg(tpqPreview, lastTpqSvg, 'tpq');
        renderSvg(xmlPreview, '', 'xml');
        homomorphismState.active = false;
        homomorphismState.mapping = [];
        renderHomomorphismOverlay();
        setStatus('La requête a été transformée en TPQ.', 'is-success');
        summaryBox.innerHTML = '<span class="badge is-success">TPQ prêt</span>';
      } catch (error) {
        setStatus('Erreur : ' + error.message, 'is-error');
      }
    }

    async function checkHomomorphism() {
      const xpath = xpathInput.value.trim();
      const xml = xmlInput.value.trim();
      if (!xpath || !xml) {
        setStatus('La requête XPath et le document XML doivent être renseignés.', 'is-error');
        return;
      }
      setStatus('Analyse de l’homomorphisme en cours…', 'is-success');
      try {
        const response = await fetch('/tpq-xml/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ xpath: xpath, xml: xml })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data && data.message ? data.message : 'Erreur serveur');
        }
        renderSvg(tpqPreview, data.tpq && data.tpq.svg ? data.tpq.svg : lastTpqSvg, 'tpq');
        renderSvg(xmlPreview, data.xml_tree && data.xml_tree.svg ? data.xml_tree.svg : '', 'xml');
        homomorphismState.active = true;
        homomorphismState.mapping = data.mapping || [];
        renderHomomorphismOverlay();
        resultMessage.innerHTML = data.exists
          ? '<span class="badge is-success">Homomorphisme trouvé</span> ' + escapeHtml(data.message)
          : '<span class="badge is-error">Aucun homomorphisme</span> ' + escapeHtml(data.message);
        mappingList.innerHTML = '';
        (data.mapping || []).forEach(function(item) {
          const li = document.createElement('li');
          li.textContent = item.source_label + ' → ' + item.target_label;
          mappingList.appendChild(li);
        });
        summaryBox.innerHTML = data.exists ? '<span class="badge is-success">Résultat : vrai</span>' : '<span class="badge is-error">Résultat : faux</span>';
        setStatus(data.message, data.exists ? 'is-success' : 'is-error');
      } catch (error) {
        setStatus('Erreur : ' + error.message, 'is-error');
      }
    }

    function loadSample() {
      xpathInput.value = initialXPath;
      xmlInput.value = initialXml;
      setStatus('Exemple chargé.', 'is-success');
    }

    function resetPage() {
      xpathInput.value = initialXPath;
      xmlInput.value = initialXml;
      lastTpqSvg = '';
      homomorphismState.active = false;
      homomorphismState.mapping = [];
      renderHomomorphismOverlay();
      tpqPreview.innerHTML = 'Aucun rendu.';
      xmlPreview.innerHTML = 'Aucun rendu.';
      canvasState.tpq.svg = null;
      canvasState.tpq.nodes = new Map();
      canvasState.tpq.edges = [];
      canvasState.xml.svg = null;
      canvasState.xml.nodes = new Map();
      canvasState.xml.edges = [];
      resultMessage.textContent = 'Aucun test effectué pour le moment.';
      mappingList.innerHTML = '';
      summaryBox.innerHTML = '<span class="badge is-success">Prêt</span>';
      setStatus("Transformez d'abord la requête XPath pour afficher le TPQ correspondant.");
    }

    xpathInput.value = initialXPath;
    xmlInput.value = initialXml;
    document.getElementById('transform').addEventListener('click', transformQuery);
    document.getElementById('check-homomorphism').addEventListener('click', checkHomomorphism);
    document.getElementById('load-sample').addEventListener('click', loadSample);
    document.getElementById('reset').addEventListener('click', resetPage);
    window.addEventListener('resize', renderHomomorphismOverlay);
  </script>
</body>
</html>"""
		)

		return template.substitute(
			title=escape(title),
			theme_switch=self._theme_switch_html(),
			theme_script=self._theme_switch_script(),
			xpath_expression=json.dumps(self.xpath_expression, ensure_ascii=False),
			xml_text=json.dumps(self.xml_text, ensure_ascii=False),
		)

	def save_html(self, path: str | Path):
		output_path = Path(path)
		output_path.write_text(self.to_html(), encoding="utf-8")
		return output_path














