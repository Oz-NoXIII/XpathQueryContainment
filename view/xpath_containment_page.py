from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery
from view.tpq_visualizer import TreePatternQueryVisualizer


DEFAULT_Q1 = "(self[(lab = *)&?descendant[(lab = c)]&?ancestor[(lab = a)&?child[(lab = b)&?child[(lab = c)]]&?descendant[(lab = e)]]]/child[(lab = d)])"
DEFAULT_Q2 = "(self[(lab = *)&?descendant[(lab = c)]&?ancestor[(lab = a)&?child[(lab = b)&?child[(lab = c)]]&?descendant[(lab = e)]]]/child[(lab = d)])"


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
      <div class="panel-body">
        <div id="summary" class="summary">
          <span class="badge is-warning">En attente d'analyse</span>
          <p class="section-note">Les visualisations et la liste des combinaisons <code>L</code> apparaîtront ici.</p>
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
              <table class="attempts">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>L</th>
                    <th>Résultat</th>
                    <th>Détails</th>
                  </tr>
                </thead>
                <tbody id="attempts-body">
                  <tr><td colspan="4">Aucune analyse effectuée.</td></tr>
                </tbody>
              </table>
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

    function renderSvg(slot, svg) {
      if (!slot) return;
      slot.innerHTML = svg || '<em>Aucun rendu.</em>';
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, function(ch) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
      });
    }

    function renderAttempts(attempts) {
      attemptsBody.innerHTML = '';
      if (!attempts || !attempts.length) {
        attemptsBody.innerHTML = '<tr><td colspan="4">Aucune combinaison L n’a été générée.</td></tr>';
        return;
      }
      attempts.forEach(function(attempt, index) {
        const row = document.createElement('tr');
        const status = attempt.exists ? '<span class="badge is-success">Homomorphisme trouvé</span>' : '<span class="badge is-error">Aucun homomorphisme</span>';
        row.innerHTML = '<td>' + (index + 1) + '</td><td><code>' + escapeHtml(JSON.stringify(attempt.L)) + '</code></td><td>' + status + '</td><td><details><summary>Afficher Tc</summary><div class="svg-slot">' + (attempt.canonical_tree_svg || '<em>Aucun rendu.</em>') + '</div><p>' + escapeHtml(attempt.message || '') + '</p></details></td>';
        attemptsBody.appendChild(row);
      });
    }

    function renderConclusion(data, label) {
      summaryBox.innerHTML = '<span class="badge ' + (data.contained ? 'is-success' : 'is-error') + '">' + label + '</span><p class="section-note">' + escapeHtml(data.summary || '') + '</p>';
      renderAttempts(data.attempts || []);
      renderSvg(counterexampleBox, data.counterexample_tree || '<em>Aucun contre-exemple : l’inclusion semble vérifiée.</em>');
      setStatus(data.summary || 'Analyse terminée.', data.contained ? 'is-success' : 'is-error');
    }

    async function transform() {
      const q1 = q1Input.value.trim();
      const q2 = q2Input.value.trim();
      if (!q1 || !q2) {
        setStatus('Les deux expressions XPath doivent être renseignées.', 'is-error');
        return;
      }
      setStatus('Transformation XPath → TPQ en cours…', 'is-success');
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
        renderSvg(rawQ1Box, data.q1 && data.q1.svg ? data.q1.svg : '');
        renderSvg(rawQ2Box, data.q2 && data.q2.svg ? data.q2.svg : '');
        renderSvg(boolQ1Box, '<em>Booléanisez pour voir cette étape.</em>');
        renderSvg(boolQ2Box, '<em>Booléanisez pour voir cette étape.</em>');
        summaryBox.innerHTML = '<span class="badge is-success">TPQ prêts</span><p class="section-note">Les deux requêtes ont été transformées en TPQ.</p>';
        attemptsBody.innerHTML = '<tr><td colspan="4">Lancez la booléanisation puis la vérification.</td></tr>';
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
      setStatus('Booléanisation en cours…', 'is-success');
      try {
        const response = await fetch('/containment/booleanize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ q1: state.raw.q1.payload, q2: state.raw.q2.payload })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data && data.message ? data.message : 'Erreur serveur');
        state.bool = data;
        renderSvg(boolQ1Box, data.q1 && data.q1.svg ? data.q1.svg : '');
        renderSvg(boolQ2Box, data.q2 && data.q2.svg ? data.q2.svg : '');
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
      setStatus('Recherche de l’homomorphisme en cours…', 'is-success');
      try {
        const response = await fetch('/containment/check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source: state.bool.q1.payload,
            target: state.bool.q2.payload,
            direction: direction,
            source_name: direction === 'forward' ? 'q1' : 'q2',
            target_name: direction === 'forward' ? 'q2' : 'q1'
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data && data.message ? data.message : 'Erreur serveur');
        renderConclusion(data, direction === 'forward' ? 'q1 ⊆ q2' : 'q2 ⊆ q1');
      } catch (error) {
        setStatus('Erreur : ' + error.message, 'is-error');
      }
    }

    function loadSample() {
      q1Input.value = "self[(lab = a)/child[(lab = b)]]";
      q2Input.value = "self[(lab = a)/child[(lab = b)]]";
      state.raw = null;
      state.bool = null;
      renderSvg(rawQ1Box, 'Aucun rendu.');
      renderSvg(rawQ2Box, 'Aucun rendu.');
      renderSvg(boolQ1Box, 'Aucun rendu.');
      renderSvg(boolQ2Box, 'Aucun rendu.');
      renderSvg(counterexampleBox, 'Aucun contre-exemple pour le moment.');
      attemptsBody.innerHTML = '<tr><td colspan="4">Aucune analyse effectuée.</td></tr>';
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
      attemptsBody.innerHTML = '<tr><td colspan="4">Aucune analyse effectuée.</td></tr>';
      summaryBox.innerHTML = '<span class="badge is-success">Prêt</span>';
      setStatus('1. Transformer les requêtes, 2. Booléaniser, 3. Vérifier dans un sens ou dans l’autre.');
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






