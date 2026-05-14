from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery
from view.tpq_visualizer import TreePatternQueryVisualizer


def _default_graph(root_label: str = "a") -> dict:
	return {
		"root_id": "node_0",
		"nodes": [{"id": "node_0", "label": root_label}],
		"edges": [],
	}


class BooleanTPQLabBuilderPage:
	"""Editor graphique pour deux BoolTPQ_Lab et leur homomorphisme."""

	def __init__(self, source_payload: dict | None = None, target_payload: dict | None = None):
		self.source_payload = source_payload or _default_graph("a")
		self.target_payload = target_payload or _default_graph("a")
		self._theme_assets = TreePatternQueryVisualizer(TreePatternQuery(QueryNode("a")))

	def _theme_switch_html(self) -> str:
		return self._theme_assets._theme_switch_html()

	def _theme_switch_script(self) -> str:
		return self._theme_assets._theme_switch_script()

	def to_html(self, title: str = "Constructeur de BoolTPQ_Lab") -> str:
		template = Template(
			"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>$title</title>
  <style>
    :root { color-scheme: light dark; --bg:#f4f7fb; --text:#102a43; --header-bg:#fff; --border:#d9e2ec; --hint:#486581; --panel-bg:#fff; --panel-alt-bg:#f0f4f8; --shadow:rgba(16,42,67,.08); --primary:#1f4e79; --primary-hover:#163d5d; --danger:#c44536; --danger-hover:#9e372b; --success:#2f855a; --selected:#ed8936; --mapped:#2f855a; --node-fill:#f7fbff; --node-stroke:#1f4e79; --node-text:#102a43; --edge-child:#334e68; --edge-descendant:#5b7ea6; --json-bg:#f0f4f8; }
    @media (prefers-color-scheme: dark) { :root:not([data-theme='light']) { --bg:#0f1720; --text:#e6edf5; --header-bg:#111b26; --border:#2a3a4a; --hint:#9ab1c9; --panel-bg:#111b26; --panel-alt-bg:#172534; --shadow:rgba(0,0,0,.45); --primary:#2c5f8f; --primary-hover:#3a75ad; --danger:#d65f4c; --danger-hover:#e07c67; --success:#3ea76a; --selected:#f6ad55; --mapped:#3ea76a; --node-fill:#173047; --node-stroke:#88b3de; --node-text:#e6edf5; --edge-child:#9ab1c9; --edge-descendant:#88b3de; --json-bg:#172534; } }
    :root[data-theme='light'] { color-scheme: light; }
    :root[data-theme='dark'] { color-scheme: dark; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Arial, Helvetica, sans-serif; background:var(--bg); color:var(--text); min-height:100vh; display:flex; flex-direction:column; }
    header { padding:16px 20px 12px; background:var(--header-bg); border-bottom:1px solid var(--border); box-shadow:0 2px 8px var(--shadow); display:flex; flex-direction:column; gap:12px; }
    .header-top { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap; }
    .header-copy { max-width:880px; }
    h1 { margin:0 0 6px; font-size:20px; }
    .hint { margin:0; font-size:13px; color:var(--hint); line-height:1.45; }
    .toolbar, .card-toolbar { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
    button, .theme-option { appearance:none; border:none; border-radius:8px; padding:8px 12px; font-size:13px; cursor:pointer; color:white; background:var(--primary); transition:background .2s, transform .1s; }
    button:hover, .theme-option:hover { background:var(--primary-hover); }
    button:active { transform:translateY(1px); }
    .ghost { background:transparent; color:var(--text); border:1px solid var(--border); }
    .ghost:hover { background:var(--panel-alt-bg); }
    .danger { background:var(--danger); }
    .danger:hover { background:var(--danger-hover); }
    main { flex:1; position:relative; display:grid; grid-template-columns: 1fr 1fr 360px; gap:14px; padding:14px; min-height:0; }
    .query-card, .result-panel { background:var(--panel-bg); border:1px solid var(--border); border-radius:14px; box-shadow:0 6px 20px var(--shadow); min-height:0; }
    .query-card { display:flex; flex-direction:column; min-width:0; }
    .query-card header { background:transparent; box-shadow:none; border-bottom:1px solid var(--border); padding:12px 12px 10px; gap:10px; }
    .query-title-row { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap; }
    .query-card h2 { margin:0; font-size:16px; }
    .subhint { margin:4px 0 0; font-size:12px; color:var(--hint); }
    .graph-shell { position:relative; flex:1; min-height:320px; overflow:hidden; background:linear-gradient(180deg, rgba(120,160,200,.05), transparent 35%); }
    svg.graph { width:100%; height:100%; display:block; touch-action:none; cursor:default; }
    .query-side { border-top:1px solid var(--border); padding:12px; display:grid; gap:10px; }
    .mini-grid { display:grid; grid-template-columns:auto 1fr; gap:6px 10px; font-size:13px; align-items:center; }
    .field { display:grid; gap:6px; }
    .field label { font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--hint); }
    .field input[type="text"], .field textarea { width:100%; border:1px solid var(--border); border-radius:8px; background:var(--panel-alt-bg); color:var(--text); padding:9px 10px; font:inherit; }
    .field textarea { min-height:150px; resize:vertical; font-family: Consolas, 'Courier New', monospace; background:var(--json-bg); }
    .status { margin:0; font-size:13px; color:var(--hint); white-space:pre-wrap; line-height:1.45; }
    .status.is-error { color:#e07c67; }
    .status.is-success { color:#4ab97a; }
    .result-panel { padding:14px; display:grid; gap:12px; overflow:auto; }
    .result-box { border:1px solid var(--border); border-radius:12px; background:var(--panel-alt-bg); padding:12px; min-height:120px; white-space:pre-wrap; line-height:1.45; font-size:13px; }
    .mapping-list { margin:0; padding-left:18px; font-size:13px; line-height:1.5; }
    .homomorphism-overlay { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; z-index:3; overflow:visible; }
    .homomorphism-overlay .homomorphism-arrow { fill:none; stroke-width:3; stroke-linecap:round; stroke-linejoin:round; }
    .homomorphism-overlay .homomorphism-arrow.is-tentative { stroke:var(--selected); stroke-dasharray:8 6; opacity:.55; }
    .homomorphism-overlay .homomorphism-arrow.is-committed { stroke:var(--mapped); opacity:.92; }
    .homomorphism-overlay .homomorphism-label { fill:var(--hint); font-size:11px; font-family:Arial, Helvetica, sans-serif; }
    .theme-switch { display:inline-flex; align-items:center; gap:8px; flex-wrap:wrap; justify-content:flex-end; padding:8px 10px; border:1px solid var(--border); border-radius:999px; background:var(--panel-bg); box-shadow:0 2px 8px var(--shadow); }
    .theme-switch-label { font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--hint); }
    .theme-option.is-active { background:var(--primary); border-color:var(--primary); color:white; }
    @media (max-width: 1300px) { main { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <div class="header-top">
      <div class="header-copy">
        <h1>$title</h1>
        <p class="hint">Construisez deux <strong>BoolTPQ_Lab</strong> côte à côte, puis cliquez sur <strong>Trouver l'homomorphisme</strong> pour comparer <code>q1</code> vers <code>q2</code>. Les labels sont obligatoires et les relations utilisent uniquement <code>child</code> et <code>descendant</code>.</p>
      </div>
      $theme_switch
    </div>
    <div class="toolbar">
      <button type="button" id="find-homomorphism">Trouver l'homomorphisme</button>
      <button type="button" id="reset-all" class="ghost">Réinitialiser les deux</button>
      <button type="button" id="copy-result" class="ghost">Copier le résultat</button>
      <button type="button" id="load-sample" class="ghost">Charger un exemple</button>
    </div>
  </header>
  <main>
    <section class="query-card" data-query="q1">$query_body_1</section>
    <section class="query-card" data-query="q2">$query_body_2</section>
    <aside class="result-panel">
      <h2>Homomorphisme q1 → q2</h2>
      <div class="result-box" id="homomorphism-result">Aucun résultat pour le moment.</div>
      <div><strong>Mapping</strong><ol class="mapping-list" id="mapping-list"></ol></div>
    </aside>
    <svg class="homomorphism-overlay" id="homomorphism-overlay" aria-hidden="true"></svg>
  </main>
  <script>
$theme_script
    const initialPayloads = { q1: $source_json, q2: $target_json };
    const queries = {};
    const resultBox = document.getElementById('homomorphism-result');
    const mappingList = document.getElementById('mapping-list');
    const homomorphismOverlay = document.getElementById('homomorphism-overlay');
    const homomorphismState = { runId: 0, active: false, edges: [] };

    function clonePayload(payload) { return JSON.parse(JSON.stringify(payload)); }
    function createEmptyState(name, rootLabel) { return { name, nodes: [{ id: 'node_0', label: rootLabel || 'a', parentId: null, edgeType: null, x: 0, y: 0 }], selectedId: 'node_0', nextId: 1, highlightedTargets: new Set() }; }
    function computeNextId(nodes) { var maxIndex = 0; nodes.forEach(function(node) { var parts = String(node.id).split('_'); if (parts.length === 2) { var idx = parseInt(parts[1], 10); if (!isNaN(idx)) { maxIndex = Math.max(maxIndex, idx + 1); } } }); return maxIndex; }
    function getNode(state, nodeId) { return state.nodes.find(function(node) { return node.id === nodeId; }) || null; }
    function getChildren(state, nodeId) { return state.nodes.filter(function(node) { return node.parentId === nodeId; }); }
    function preorder(state, nodeId, output) { var node = getNode(state, nodeId); if (!node) { return output; } output.push(node); getChildren(state, nodeId).forEach(function(child) { preorder(state, child.id, output); }); return output; }
    function getRootId(state) { var root = state.nodes.find(function(node) { return node.parentId === null; }); return root ? root.id : null; }
    function setStatus(state, message, kind) { var panel = document.querySelector('[data-query="' + state.name + '"] [data-status]'); if (panel) { panel.textContent = message; panel.className = ('status ' + (kind || '')).trim(); } }
    function syncQueryPanel(state) { var panel = document.querySelector('[data-query="' + state.name + '"]'); if (!panel) { return; } var selected = getNode(state, state.selectedId); panel.querySelector('[data-root]').textContent = getRootId(state) || '—'; panel.querySelector('[data-selected]').textContent = selected ? selected.id : '—'; panel.querySelector('[data-parent]').textContent = selected && selected.parentId ? selected.parentId : '—'; panel.querySelector('[data-edge]').textContent = selected && selected.edgeType ? selected.edgeType : '—'; panel.querySelector('input[type="text"]').value = selected ? selected.label : ''; panel.querySelector('textarea').value = JSON.stringify(serializeState(state), null, 2); }
    function serializeState(state) { return { root_id: getRootId(state), nodes: state.nodes.map(function(node) { return { id: node.id, label: node.label }; }), edges: state.nodes.filter(function(node) { return node.parentId; }).map(function(node) { return { source: node.parentId, target: node.id, type: node.edgeType }; }) }; }
    function getChildrenFromMap(nodesById, nodeId) { return Array.from(nodesById.values()).filter(function(node) { return node.parentId === nodeId; }); }
    function validatePayload(payload) { if (!payload || typeof payload !== 'object') { throw new Error("Le JSON doit contenir un objet."); } var nodes = Array.isArray(payload.nodes) ? payload.nodes : []; var edges = Array.isArray(payload.edges) ? payload.edges : []; if (!nodes.length) { throw new Error("Le graphe doit contenir au moins un nœud."); } var nodesById = new Map(); nodes.forEach(function(node, index) { if (!node || typeof node !== 'object') { throw new Error("Le nœud #" + (index + 1) + " doit être un objet."); } if (typeof node.id !== 'string' || !node.id) { throw new Error("Le nœud #" + (index + 1) + " doit avoir un identifiant."); } if (nodesById.has(node.id)) { throw new Error("L'identifiant " + node.id + " est dupliqué."); } var label = typeof node.label === 'string' ? node.label.trim() : ''; if (!label) { throw new Error("Le nœud " + node.id + " doit avoir un label."); } if (label === '*') { throw new Error("Les labels doivent rester concrets."); } if (node.roles && Array.isArray(node.roles) && node.roles.length) { throw new Error("Les BoolTPQ_Lab n'utilisent pas de rôles."); } nodesById.set(node.id, { id: node.id, label: label, parentId: null, edgeType: null, x: 0, y: 0 }); }); edges.forEach(function(edge, index) { if (!edge || typeof edge !== 'object') { throw new Error("L'arête #" + (index + 1) + " doit être un objet."); } if (!nodesById.has(edge.source) || !nodesById.has(edge.target)) { throw new Error("L'arête #" + (index + 1) + " référence un nœud inexistant."); } if (edge.type !== 'child' && edge.type !== 'descendant') { throw new Error("Type d'arête non supporté: " + edge.type); } var target = nodesById.get(edge.target); if (target.parentId && target.parentId !== edge.source) { throw new Error("Le nœud " + edge.target + " a déjà un parent."); } target.parentId = edge.source; target.edgeType = edge.type; }); var roots = Array.from(nodesById.values()).filter(function(node) { return node.parentId === null; }); if (roots.length !== 1) { throw new Error("Le graphe doit contenir exactement une racine."); } var rootId = payload.root_id || roots[0].id; if (!nodesById.has(rootId)) { throw new Error("La racine " + rootId + " est inconnue."); } if (nodesById.get(rootId).parentId !== null) { throw new Error("La racine ne doit pas avoir de parent."); } var visiting = new Set(); var visited = new Set(); function dfs(nodeId) { if (visiting.has(nodeId)) { throw new Error("Le graphe contient un cycle."); } if (visited.has(nodeId)) { return; } visiting.add(nodeId); getChildrenFromMap(nodesById, nodeId).forEach(function(child) { dfs(child.id); }); visiting.delete(nodeId); visited.add(nodeId); } dfs(rootId); if (visited.size !== nodesById.size) { var missing = Array.from(nodesById.keys()).filter(function(nodeId) { return !visited.has(nodeId); }); throw new Error("Le graphe contient des nœuds déconnectés: " + missing.join(', ')); } return { rootId, nodesById }; }
    function preorderFromMap(nodesById, nodeId, output) { var node = nodesById.get(nodeId); if (!node) { return output; } output.push(node); getChildrenFromMap(nodesById, nodeId).forEach(function(child) { preorderFromMap(nodesById, child.id, output); }); return output; }
    function loadPayloadIntoState(state, payload) { homomorphismState.runId += 1; homomorphismState.active = false; homomorphismState.edges = []; renderHomomorphismOverlay(); var parsed = validatePayload(payload); state.nodes = preorderFromMap(parsed.nodesById, parsed.rootId, []).map(function(node) { return Object.assign({}, node); }); state.selectedId = parsed.rootId; state.nextId = computeNextId(state.nodes); state.highlightedTargets = new Set(); layoutQuery(state); setStatus(state, 'Le graphe a été chargé.', 'is-success'); syncQueryPanel(state); renderQuery(state); }
    function layoutQuery(state) { var width = Math.max(520, Math.floor(state._svgWidth || 520)); var rootId = getRootId(state); if (!rootId) { return; } var byDepth = new Map(); function walk(nodeId, depth) { var node = getNode(state, nodeId); if (!node) { return; } node.depth = depth; if (!byDepth.has(depth)) { byDepth.set(depth, []); } byDepth.get(depth).push(node); getChildren(state, nodeId).forEach(function(child) { walk(child.id, depth + 1); }); } walk(rootId, 0); byDepth.forEach(function(nodes, depth) { var y = 60 + depth * 120; var spread = Math.max(width - 96, (nodes.length - 1) * 120); var startX = nodes.length > 1 ? 48 : width / 2; var step = nodes.length > 1 ? spread / (nodes.length - 1) : 0; nodes.forEach(function(node, index) { node.x = nodes.length > 1 ? startX + index * step : width / 2; node.y = y; }); }); }
    function candidateTargets(targetState, targetParentNode, edgeType) { if (edgeType === 'child') { return getChildren(targetState, targetParentNode.id); } var result = []; function collect(node) { getChildren(targetState, node.id).forEach(function(child) { result.push(child); collect(child); }); } collect(targetParentNode); return result; }
    function preorderNodes(state) { return preorder(state, getRootId(state), []); }
    function findHomomorphism(sourceState, targetState) { var memo = new Map(); var witness = new Map(); function match(sourceNode, targetNode) { var key = sourceNode.id + '->' + targetNode.id; if (memo.has(key)) { return memo.get(key); } if (sourceNode.label !== targetNode.label) { memo.set(key, false); return false; } var outgoing = getChildren(sourceState, sourceNode.id); for (var i = 0; i < outgoing.length; i += 1) { var child = outgoing[i]; var candidates = candidateTargets(targetState, targetNode, child.edgeType || 'child'); var ok = false; for (var j = 0; j < candidates.length; j += 1) { if (match(child, candidates[j])) { ok = true; witness.set(child.id, candidates[j].id); break; } } if (!ok) { memo.set(key, false); return false; } } witness.set(sourceNode.id, targetNode.id); memo.set(key, true); return true; } var sourceRoot = getNode(sourceState, getRootId(sourceState)); var targetRoot = getNode(targetState, getRootId(targetState)); if (!sourceRoot || !targetRoot) { return { exists: false, mapping: [] }; } if (!match(sourceRoot, targetRoot)) { return { exists: false, mapping: [] }; } var ordered = preorderNodes(sourceState); var mapping = ordered.map(function(sourceNode) { var targetId = witness.get(sourceNode.id); var targetNode = getNode(targetState, targetId); return { source_id: sourceNode.id, source_label: sourceNode.label, target_id: targetId, target_label: targetNode ? targetNode.label : '' }; }); return { exists: true, mapping: mapping, highlight_target_ids: Array.from(new Set(mapping.map(function(item) { return item.target_id; }))) }; }
    function renderQuery(state) { var panel = document.querySelector('[data-query="' + state.name + '"]'); if (!panel) { return; } var svg = panel.querySelector('svg.graph'); var rect = svg.getBoundingClientRect(); state._svgWidth = rect.width || 520; state._svgHeight = rect.height || 360; svg.setAttribute('viewBox', '0 0 ' + state._svgWidth + ' ' + state._svgHeight); svg.innerHTML = ''; var edges = document.createDocumentFragment(); state.nodes.forEach(function(node) { if (!node.parentId) { return; } var parent = getNode(state, node.parentId); if (!parent) { return; } var dx = node.x - parent.x; var dy = node.y - parent.y; var length = Math.hypot(dx, dy) || 1; var ux = dx / length; var uy = dy / length; var x1 = parent.x + ux * 24; var y1 = parent.y + uy * 24; var x2 = node.x - ux * 24; var y2 = node.y - uy * 24; if (node.edgeType === 'descendant') { [-4, 4].forEach(function(offset) { var ox = -uy * offset; var oy = ux * offset; var line = document.createElementNS('http://www.w3.org/2000/svg', 'line'); line.setAttribute('x1', String(x1 + ox)); line.setAttribute('y1', String(y1 + oy)); line.setAttribute('x2', String(x2 + ox)); line.setAttribute('y2', String(y2 + oy)); line.setAttribute('stroke', 'var(--edge-descendant)'); line.setAttribute('stroke-width', '2'); line.setAttribute('stroke-linecap', 'round'); edges.appendChild(line); }); } else { var lineChild = document.createElementNS('http://www.w3.org/2000/svg', 'line'); lineChild.setAttribute('x1', String(x1)); lineChild.setAttribute('y1', String(y1)); lineChild.setAttribute('x2', String(x2)); lineChild.setAttribute('y2', String(y2)); lineChild.setAttribute('stroke', 'var(--edge-child)'); lineChild.setAttribute('stroke-width', '2'); lineChild.setAttribute('stroke-linecap', 'round'); edges.appendChild(lineChild); } }); svg.appendChild(edges); state.nodes.forEach(function(node) { var group = document.createElementNS('http://www.w3.org/2000/svg', 'g'); group.setAttribute('data-node-id', node.id); group.style.cursor = 'grab'; var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle'); circle.setAttribute('cx', String(node.x)); circle.setAttribute('cy', String(node.y)); circle.setAttribute('r', '24'); circle.setAttribute('fill', state.highlightedTargets.has(node.id) ? 'var(--mapped)' : 'var(--node-fill)'); circle.setAttribute('stroke', node.id === state.selectedId ? 'var(--selected)' : 'var(--node-stroke)'); circle.setAttribute('stroke-width', node.id === state.selectedId ? '4' : '2'); group.appendChild(circle); var text = document.createElementNS('http://www.w3.org/2000/svg', 'text'); text.setAttribute('x', String(node.x)); text.setAttribute('y', String(node.y)); text.setAttribute('fill', 'var(--node-text)'); text.setAttribute('text-anchor', 'middle'); text.setAttribute('dominant-baseline', 'middle'); text.setAttribute('font-size', '13'); text.setAttribute('font-weight', 'bold'); text.textContent = node.label; group.appendChild(text); svg.appendChild(group); }); syncQueryPanel(state); }
    function syncNodeLabelInput(state) { var panel = document.querySelector('[data-query="' + state.name + '"]'); if (!panel) { return; } var selected = getNode(state, state.selectedId); var input = panel.querySelector('input[type="text"]'); if (selected && input) { input.value = selected.label; } }
    function setSelectedNodeLabel(state, value) { var selected = getNode(state, state.selectedId); if (!selected) { return; } var label = value.trim() || 'a'; if (label === '*') { window.alert('Les labels doivent rester concrets.'); return; } selected.label = label; renderQuery(state); }
    function addNode(state, edgeType) { var parent = getNode(state, state.selectedId); if (!parent) { setStatus(state, "Sélectionnez d'abord un nœud.", 'is-error'); return; } var label = window.prompt('Label du nouveau nœud', 'a'); if (label === null) { return; } label = label.trim() || 'a'; if (label === '*') { window.alert('Les labels doivent rester concrets.'); return; } var newNode = { id: 'node_' + state.nextId, label: label, parentId: parent.id, edgeType: edgeType, x: parent.x + (edgeType === 'child' ? 140 : 110), y: parent.y + 120 }; state.nextId += 1; state.nodes.push(newNode); state.selectedId = newNode.id; layoutQuery(state); setStatus(state, 'Nœud ' + newNode.id + ' ajouté.', 'is-success'); renderQuery(state); }
    function renameSelected(state) { var selected = getNode(state, state.selectedId); if (!selected) { return; } var label = window.prompt('Nouveau label', selected.label); if (label === null) { return; } label = label.trim() || 'a'; if (label === '*') { window.alert('Les labels doivent rester concrets.'); return; } selected.label = label; setStatus(state, 'Nœud ' + selected.id + ' renommé.', 'is-success'); renderQuery(state); }
    function deleteSelected(state) { var selected = getNode(state, state.selectedId); if (!selected) { return; } if (!selected.parentId) { setStatus(state, 'La racine ne peut pas être supprimée.', 'is-error'); return; } var toRemove = new Set(); function collect(nodeId) { toRemove.add(nodeId); getChildren(state, nodeId).forEach(function(child) { collect(child.id); }); } collect(selected.id); state.nodes = state.nodes.filter(function(node) { return !toRemove.has(node.id); }); state.selectedId = getRootId(state); state.nextId = computeNextId(state.nodes); layoutQuery(state); setStatus(state, 'Sous-arbre supprimé.', 'is-success'); renderQuery(state); }
    function centerQuery(state) { layoutQuery(state); setStatus(state, 'Disposition recalculée.', 'is-success'); renderQuery(state); }
    function exportJson(state) { var panel = document.querySelector('[data-query="' + state.name + '"]'); if (!panel) { return; } panel.querySelector('textarea').value = JSON.stringify(serializeState(state), null, 2); setStatus(state, 'JSON exporté dans la zone de texte.', 'is-success'); }
    function importJson(state) { var panel = document.querySelector('[data-query="' + state.name + '"]'); if (!panel) { return; } try { loadPayloadIntoState(state, JSON.parse(panel.querySelector('textarea').value)); } catch (error) { setStatus(state, 'Import impossible : ' + error.message, 'is-error'); } }
    async function findHomomorphism() { try { var response = await fetch('/builder/homomorphism', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: serializeState(queries.q1), target: serializeState(queries.q2) }) }); var data = await response.json(); if (!response.ok) { throw new Error(data && data.message ? data.message : 'Erreur serveur'); } resultBox.textContent = data.message; mappingList.innerHTML = ''; if (data.exists) { queries.q2.highlightedTargets = new Set(data.highlight_target_ids || []); data.mapping.forEach(function(item) { var li = document.createElement('li'); li.textContent = item.source_id + ' (' + item.source_label + ') → ' + item.target_id + ' (' + item.target_label + ')'; mappingList.appendChild(li); }); } else { queries.q2.highlightedTargets = new Set(); } renderQuery(queries.q2); } catch (error) { resultBox.textContent = 'Erreur : ' + error.message; mappingList.innerHTML = ''; } }
    function resetAll() { loadPayloadIntoState(queries.q1, clonePayload(initialPayloads.q1)); loadPayloadIntoState(queries.q2, clonePayload(initialPayloads.q2)); resultBox.textContent = 'Aucun résultat pour le moment.'; mappingList.innerHTML = ''; }
    function loadSample() { var sampleQ1 = { root_id: 'node_0', nodes: [ { id: 'node_0', label: 'a' }, { id: 'node_1', label: 'b' }, { id: 'node_2', label: 'c' } ], edges: [ { source: 'node_0', target: 'node_1', type: 'child' }, { source: 'node_1', target: 'node_2', type: 'descendant' } ] }; var sampleQ2 = { root_id: 'node_0', nodes: [ { id: 'node_0', label: 'a' }, { id: 'node_1', label: 'b' }, { id: 'node_2', label: 'c' }, { id: 'node_3', label: 'd' } ], edges: [ { source: 'node_0', target: 'node_1', type: 'child' }, { source: 'node_1', target: 'node_2', type: 'descendant' }, { source: 'node_0', target: 'node_3', type: 'descendant' } ] }; loadPayloadIntoState(queries.q1, sampleQ1); loadPayloadIntoState(queries.q2, sampleQ2); resultBox.textContent = "Exemple chargé. Cliquez sur Trouver l'homomorphisme."; mappingList.innerHTML = ''; }
    function attachCardHandlers(state) { var panel = document.querySelector('[data-query="' + state.name + '"]'); var svg = panel.querySelector('svg.graph'); var dragged = null; panel.querySelectorAll('button[data-action]').forEach(function(button) { var action = button.getAttribute('data-action'); button.addEventListener('click', function() { if (action === 'add-child') { addNode(state, 'child'); } else if (action === 'add-descendant') { addNode(state, 'descendant'); } else if (action === 'rename') { renameSelected(state); } else if (action === 'delete') { deleteSelected(state); } else if (action === 'center') { centerQuery(state); } else if (action === 'export-json') { exportJson(state); } else if (action === 'import-json') { importJson(state); } }); }); panel.querySelector('input[type="text"]').addEventListener('input', function(event) { setSelectedNodeLabel(state, event.target.value); }); svg.addEventListener('pointerdown', function(event) { var rect = svg.getBoundingClientRect(); var x = event.clientX - rect.left; var y = event.clientY - rect.top; var node = null; for (var i = state.nodes.length - 1; i >= 0; i -= 1) { var candidate = state.nodes[i]; if (Math.hypot(candidate.x - x, candidate.y - y) <= 30) { node = candidate; break; } } if (!node) { return; } state.selectedId = node.id; dragged = { node: node, offsetX: x - node.x, offsetY: y - node.y }; svg.setPointerCapture(event.pointerId); renderQuery(state); }); svg.addEventListener('pointermove', function(event) { if (!dragged) { return; } var rect = svg.getBoundingClientRect(); dragged.node.x = event.clientX - rect.left - dragged.offsetX; dragged.node.y = event.clientY - rect.top - dragged.offsetY; renderQuery(state); }); svg.addEventListener('pointerup', function() { dragged = null; }); svg.addEventListener('pointerleave', function() { dragged = null; }); }
    function nextAnimationFrame() { return new Promise(function(resolve) { window.requestAnimationFrame(function() { resolve(); }); }); }
    function sleep(ms) { return new Promise(function(resolve) { window.setTimeout(resolve, ms); }); }
    function cancelHomomorphismOverlay() { homomorphismState.runId += 1; homomorphismState.active = false; homomorphismState.edges = []; renderHomomorphismOverlay(); }
    function getOverlayPoint(queryName, nodeId, side) { if (!homomorphismOverlay) { return null; } var panel = document.querySelector('[data-query="' + queryName + '"]'); if (!panel) { return null; } var node = panel.querySelector('[data-node-id="' + nodeId + '"] circle'); if (!node) { return null; } var nodeRect = node.getBoundingClientRect(); var overlayRect = homomorphismOverlay.getBoundingClientRect(); var radius = Math.max(nodeRect.width, nodeRect.height) / 2; var direction = side === 'source' ? 1 : -1; return { x: nodeRect.left - overlayRect.left + nodeRect.width / 2 + direction * radius * 0.85, y: nodeRect.top - overlayRect.top + nodeRect.height / 2 }; }
    function renderHomomorphismOverlay() { if (!homomorphismOverlay) { return; } var rect = homomorphismOverlay.getBoundingClientRect(); homomorphismOverlay.setAttribute('viewBox', '0 0 ' + Math.max(1, rect.width) + ' ' + Math.max(1, rect.height)); homomorphismOverlay.innerHTML = ''; if (!homomorphismState.active) { return; } var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs'); var marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker'); marker.setAttribute('id', 'homomorphism-arrowhead'); marker.setAttribute('viewBox', '0 0 10 10'); marker.setAttribute('refX', '8.5'); marker.setAttribute('refY', '5'); marker.setAttribute('markerWidth', '7'); marker.setAttribute('markerHeight', '7'); marker.setAttribute('orient', 'auto-start-reverse'); var arrow = document.createElementNS('http://www.w3.org/2000/svg', 'path'); arrow.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z'); arrow.setAttribute('fill', 'currentColor'); marker.appendChild(arrow); defs.appendChild(marker); homomorphismOverlay.appendChild(defs); homomorphismState.edges.forEach(function(edge) { var sourcePoint = getOverlayPoint('q1', edge.sourceId, 'source'); var targetPoint = getOverlayPoint('q2', edge.targetId, 'target'); if (!sourcePoint || !targetPoint) { return; } var path = document.createElementNS('http://www.w3.org/2000/svg', 'path'); var midX = (sourcePoint.x + targetPoint.x) / 2; var curve = Math.max(32, Math.abs(targetPoint.x - sourcePoint.x) * 0.25); var control1X = midX + curve; var control2X = midX - curve; path.setAttribute('d', 'M ' + sourcePoint.x + ' ' + sourcePoint.y + ' C ' + control1X + ' ' + sourcePoint.y + ', ' + control2X + ' ' + targetPoint.y + ', ' + targetPoint.x + ' ' + targetPoint.y); path.setAttribute('class', 'homomorphism-arrow ' + (edge.status === 'committed' ? 'is-committed' : 'is-tentative')); path.setAttribute('marker-end', 'url(#homomorphism-arrowhead)'); homomorphismOverlay.appendChild(path); var label = document.createElementNS('http://www.w3.org/2000/svg', 'text'); label.setAttribute('class', 'homomorphism-label'); label.setAttribute('x', String((sourcePoint.x + targetPoint.x) / 2)); label.setAttribute('y', String((sourcePoint.y + targetPoint.y) / 2 - 6)); label.setAttribute('text-anchor', 'middle'); label.textContent = edge.status === 'committed' ? edge.sourceId + ' → ' + edge.targetId : '...'; homomorphismOverlay.appendChild(label); }); }
    function renderQuery(state) { var panel = document.querySelector('[data-query="' + state.name + '"]'); if (!panel) { return; } var svg = panel.querySelector('svg.graph'); var rect = svg.getBoundingClientRect(); state._svgWidth = rect.width || 520; state._svgHeight = rect.height || 360; svg.setAttribute('viewBox', '0 0 ' + state._svgWidth + ' ' + state._svgHeight); svg.innerHTML = ''; var edges = document.createDocumentFragment(); state.nodes.forEach(function(node) { if (!node.parentId) { return; } var parent = getNode(state, node.parentId); if (!parent) { return; } var dx = node.x - parent.x; var dy = node.y - parent.y; var length = Math.hypot(dx, dy) || 1; var ux = dx / length; var uy = dy / length; var x1 = parent.x + ux * 24; var y1 = parent.y + uy * 24; var x2 = node.x - ux * 24; var y2 = node.y - uy * 24; if (node.edgeType === 'descendant') { [-4, 4].forEach(function(offset) { var ox = -uy * offset; var oy = ux * offset; var line = document.createElementNS('http://www.w3.org/2000/svg', 'line'); line.setAttribute('x1', String(x1 + ox)); line.setAttribute('y1', String(y1 + oy)); line.setAttribute('x2', String(x2 + ox)); line.setAttribute('y2', String(y2 + oy)); line.setAttribute('stroke', 'var(--edge-descendant)'); line.setAttribute('stroke-width', '2'); line.setAttribute('stroke-linecap', 'round'); edges.appendChild(line); }); } else { var lineChild = document.createElementNS('http://www.w3.org/2000/svg', 'line'); lineChild.setAttribute('x1', String(x1)); lineChild.setAttribute('y1', String(y1)); lineChild.setAttribute('x2', String(x2)); lineChild.setAttribute('y2', String(y2)); lineChild.setAttribute('stroke', 'var(--edge-child)'); lineChild.setAttribute('stroke-width', '2'); lineChild.setAttribute('stroke-linecap', 'round'); edges.appendChild(lineChild); } }); svg.appendChild(edges); state.nodes.forEach(function(node) { var group = document.createElementNS('http://www.w3.org/2000/svg', 'g'); group.setAttribute('data-node-id', node.id); group.style.cursor = 'grab'; var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle'); circle.setAttribute('cx', String(node.x)); circle.setAttribute('cy', String(node.y)); circle.setAttribute('r', '24'); circle.setAttribute('fill', state.highlightedTargets.has(node.id) ? 'var(--mapped)' : 'var(--node-fill)'); circle.setAttribute('stroke', node.id === state.selectedId ? 'var(--selected)' : 'var(--node-stroke)'); circle.setAttribute('stroke-width', node.id === state.selectedId ? '4' : '2'); group.appendChild(circle); var text = document.createElementNS('http://www.w3.org/2000/svg', 'text'); text.setAttribute('x', String(node.x)); text.setAttribute('y', String(node.y)); text.setAttribute('fill', 'var(--node-text)'); text.setAttribute('text-anchor', 'middle'); text.setAttribute('dominant-baseline', 'middle'); text.setAttribute('font-size', '13'); text.setAttribute('font-weight', 'bold'); text.textContent = node.label; group.appendChild(text); svg.appendChild(group); }); syncQueryPanel(state); if (homomorphismState.active) { renderHomomorphismOverlay(); } }
    async function findHomomorphism() { var runId = homomorphismState.runId + 1; homomorphismState.runId = runId; homomorphismState.active = true; homomorphismState.edges = []; resultBox.textContent = 'Recherche en cours…'; mappingList.innerHTML = ''; queries.q2.highlightedTargets = new Set(); renderQuery(queries.q1); renderQuery(queries.q2); function ensureRun() { if (runId !== homomorphismState.runId) { throw new Error('Recherche annulée.'); } } function removeEdge(edge) { var index = homomorphismState.edges.indexOf(edge); if (index !== -1) { homomorphismState.edges.splice(index, 1); } } async function tick() { ensureRun(); renderHomomorphismOverlay(); await nextAnimationFrame(); await sleep(80); ensureRun(); } try { var sourceState = queries.q1; var targetState = queries.q2; var memo = new Map(); var witness = new Map(); async function match(sourceNode, targetNode) { ensureRun(); var key = sourceNode.id + '->' + targetNode.id; if (memo.has(key)) { return memo.get(key); } var edge = { sourceId: sourceNode.id, targetId: targetNode.id, status: 'tentative' }; homomorphismState.edges.push(edge); renderHomomorphismOverlay(); await tick(); if (sourceNode.label !== targetNode.label) { removeEdge(edge); memo.set(key, false); renderHomomorphismOverlay(); return false; } var outgoing = getChildren(sourceState, sourceNode.id); for (var i = 0; i < outgoing.length; i += 1) { var child = outgoing[i]; var candidates = candidateTargets(targetState, targetNode, child.edgeType || 'child'); var matched = false; for (var j = 0; j < candidates.length; j += 1) { if (await match(child, candidates[j])) { witness.set(child.id, candidates[j].id); matched = true; break; } } if (!matched) { removeEdge(edge); memo.set(key, false); renderHomomorphismOverlay(); return false; } } edge.status = 'committed'; witness.set(sourceNode.id, targetNode.id); memo.set(key, true); renderHomomorphismOverlay(); await tick(); return true; } var sourceRoot = getNode(sourceState, getRootId(sourceState)); var targetRoot = getNode(targetState, getRootId(targetState)); if (!sourceRoot || !targetRoot) { throw new Error('Les deux graphes doivent contenir une racine.'); } var exists = await match(sourceRoot, targetRoot); ensureRun(); if (!exists) { homomorphismState.active = false; homomorphismState.edges = []; resultBox.textContent = "Aucun homomorphisme n'a été trouvé entre q1 et q2."; queries.q2.highlightedTargets = new Set(); mappingList.innerHTML = ''; renderQuery(queries.q2); renderHomomorphismOverlay(); return; } var ordered = preorderNodes(sourceState); var mapping = ordered.map(function(sourceNode) { var targetId = witness.get(sourceNode.id); var targetNode = getNode(targetState, targetId); return { source_id: sourceNode.id, source_label: sourceNode.label, target_id: targetId, target_label: targetNode ? targetNode.label : '' }; }); homomorphismState.edges = mapping.map(function(item) { return { sourceId: item.source_id, targetId: item.target_id, status: 'committed' }; }); homomorphismState.active = true; queries.q2.highlightedTargets = new Set(mapping.map(function(item) { return item.target_id; })); resultBox.textContent = 'Homomorphisme trouvé entre q1 et q2.'; mappingList.innerHTML = ''; mapping.forEach(function(item) { var li = document.createElement('li'); li.textContent = item.source_id + ' (' + item.source_label + ') → ' + item.target_id + ' (' + item.target_label + ')'; mappingList.appendChild(li); }); renderQuery(queries.q2); renderHomomorphismOverlay(); } catch (error) { if (error && error.message === 'Recherche annulée.') { return; } homomorphismState.active = false; homomorphismState.edges = []; resultBox.textContent = 'Erreur : ' + error.message; mappingList.innerHTML = ''; queries.q2.highlightedTargets = new Set(); renderQuery(queries.q2); renderHomomorphismOverlay(); } }
    function boot() {
      queries.q1 = createEmptyState('q1', 'a');
      queries.q2 = createEmptyState('q2', 'a');
      // Essayez de charger les payloads initiaux fournis par le serveur.
      // Si la validation échoue, on bascule proprement sur l'état vide créé ci-dessus
      // au lieu de laisser une exception interrompre l'initialisation (boutons inactifs).
      try {
        loadPayloadIntoState(queries.q1, clonePayload(initialPayloads.q1));
      } catch (err) {
        // garde l'état par défaut et affiche un message discret
        setStatus(queries.q1, 'Payload initial invalide, état par défaut chargé.', 'is-error');
        renderQuery(queries.q1);
      }
      try {
        loadPayloadIntoState(queries.q2, clonePayload(initialPayloads.q2));
      } catch (err) {
        setStatus(queries.q2, 'Payload initial invalide, état par défaut chargé.', 'is-error');
        renderQuery(queries.q2);
      }

      attachCardHandlers(queries.q1);
      attachCardHandlers(queries.q2);
      document.getElementById('find-homomorphism').addEventListener('click', findHomomorphism);
      document.getElementById('reset-all').addEventListener('click', resetAll);
      document.getElementById('copy-result').addEventListener('click', function() { var text = resultBox.textContent + '\\n' + Array.from(mappingList.children).map(function(li) { return li.textContent; }).join('\\n'); navigator.clipboard.writeText(text).catch(function() {}); });
      document.getElementById('load-sample').addEventListener('click', loadSample);
      window.addEventListener('resize', function() { renderQuery(queries.q1); renderQuery(queries.q2); });
      resultBox.textContent = 'Aucun résultat pour le moment.';
    }
    boot();
  </script>
</body>
</html>"""
		)
		query_body_1 = """<header>
        <div class=\"query-title-row\">
          <div>
            <h2>q1</h2>
            <p class=\"subhint\">Source du homomorphisme</p>
          </div>
          <div class=\"card-toolbar\">
            <button type=\"button\" data-action=\"add-child\">Ajouter child</button>
            <button type=\"button\" data-action=\"add-descendant\">Ajouter descendant</button>
            <button type=\"button\" data-action=\"rename\" class=\"ghost\">Renommer</button>
            <button type=\"button\" data-action=\"delete\" class=\"danger\">Supprimer</button>
            <button type=\"button\" data-action=\"center\" class=\"ghost\">Centrer</button>
          </div>
        </div>
      </header>
      <div class=\"graph-shell\"><svg class=\"graph\" data-graph aria-label=\"Graphique q1\"></svg></div>
      <div class=\"query-side\">
        <div class=\"mini-grid\">
          <strong>Racine</strong><span data-root>—</span>
          <strong>Sélection</strong><span data-selected>—</span>
          <strong>Parent</strong><span data-parent>—</span>
          <strong>Arête</strong><span data-edge>—</span>
        </div>
        <div class=\"field\"><label for=\"label-q1\">Label sélectionné</label><input id=\"label-q1\" type=\"text\" placeholder=\"Label du nœud\" /></div>
        <div class=\"field\"><label for=\"json-q1\">JSON</label><textarea id=\"json-q1\" spellcheck=\"false\"></textarea></div>
        <div class=\"card-toolbar\"><button type=\"button\" data-action=\"export-json\" class=\"ghost\">Exporter JSON</button><button type=\"button\" data-action=\"import-json\" class=\"ghost\">Importer JSON</button></div>
        <p class=\"status\" data-status>Prêt.</p>
      </div>"""
		query_body_2 = query_body_1.replace('q1', 'q2').replace('Source du homomorphisme', 'Cible du homomorphisme')
		return template.substitute(
			title=escape(title),
			theme_switch=self._theme_switch_html(),
			theme_script=self._theme_switch_script(),
			source_json=json.dumps(self.source_payload, ensure_ascii=False),
			target_json=json.dumps(self.target_payload, ensure_ascii=False),
			query_body_1=query_body_1,
			query_body_2=query_body_2,
		)

	def save_html(self, path: str | Path):
		output_path = Path(path)
		output_path.write_text(self.to_html(), encoding="utf-8")
		return output_path


TreePatternQueryBuilderPage = BooleanTPQLabBuilderPage








