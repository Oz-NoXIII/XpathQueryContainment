from __future__ import annotations

from collections import defaultdict
from typing import Any

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery

_ALLOWED_EDGE_TYPES = {"child", "descendant"}
_ALLOWED_ROLES = {"u1", "u2"}


class GraphPayloadError(ValueError):
	"""Raised when a graph payload cannot be converted into a TPQ."""


def _require_dict(value: Any, message: str) -> dict[str, Any]:
	if not isinstance(value, dict):
		raise GraphPayloadError(message)
	return value


def _require_list(value: Any, message: str) -> list[Any]:
	if not isinstance(value, list):
		raise GraphPayloadError(message)
	return value


def _require_str(value: Any, message: str) -> str:
	if not isinstance(value, str) or not value:
		raise GraphPayloadError(message)
	return value


def _normalize_roles(raw_roles: Any, node_id: str) -> list[str]:
	if raw_roles is None:
		return []
	if not isinstance(raw_roles, list):
		raise GraphPayloadError(f"Node '{node_id}' must expose its roles as a list")

	roles: list[str] = []
	for role in raw_roles:
		if role not in _ALLOWED_ROLES:
			raise GraphPayloadError(f"Unsupported output role '{role}' on node '{node_id}'")
		if role not in roles:
			roles.append(role)
	return roles


def tpq_to_graph_payload(tpq: TreePatternQuery) -> dict[str, Any]:
	"""Serialize a TPQ into a JSON-friendly graph payload."""
	root = tpq.get_root()
	output_u1 = getattr(tpq, "output_u1", None)
	output_u2 = getattr(tpq, "output_u2", None)
	is_boolean = bool(getattr(tpq, "is_boolean", False))

	nodes: list[dict[str, Any]] = []
	edges: list[dict[str, Any]] = []
	seen: dict[QueryNode, str] = {}

	def traverse(node: QueryNode, depth: int = 0) -> str:
		if node in seen:
			return seen[node]

		node_id = f"node_{len(nodes)}"
		seen[node] = node_id
		roles = sorted(node.get_output_roles())
		if not roles:
			if node is output_u1:
				roles.append("u1")
			if node is output_u2:
				roles.append("u2")

		nodes.append(
			{
				"id": node_id,
				"label": str(node.get_label()),
				"roles": roles,
				"is_root": node is root,
				"depth": depth,
			}
		)

		for child in node.get_children():
			child_id = traverse(child, depth + 1)
			edges.append({"source": node_id, "target": child_id, "type": "child"})
		for descendant in node.get_descendants():
			descendant_id = traverse(descendant, depth + 1)
			edges.append({"source": node_id, "target": descendant_id, "type": "descendant"})
		return node_id

	root_id = traverse(root)
	return {"root_id": root_id, "nodes": nodes, "edges": edges, "is_boolean": is_boolean}


def graph_payload_to_tpq(payload: dict[str, Any]) -> TreePatternQuery:
	"""Build a TPQ from a graph payload used by the graphical builder."""
	data = _require_dict(payload, "The graph payload must be a JSON object")
	nodes_data = _require_list(data.get("nodes"), "The graph payload must contain a 'nodes' list")
	edges_data = _require_list(data.get("edges"), "The graph payload must contain an 'edges' list")
	if not nodes_data:
		raise GraphPayloadError("The graph must contain at least one node")

	node_objects: dict[str, QueryNode] = {}
	roles_by_node_id: dict[str, list[str]] = {}
	incoming_counts: dict[str, int] = defaultdict(int)
	adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)

	for node_data in nodes_data:
		node_record = _require_dict(node_data, "Each node must be an object")
		node_id = _require_str(node_record.get("id"), "Each node must have a non-empty 'id'")
		if node_id in node_objects:
			raise GraphPayloadError(f"Duplicate node identifier '{node_id}'")
		label = node_record.get("label", "*")
		if not isinstance(label, str) or not label:
			raise GraphPayloadError(f"Node '{node_id}' must have a non-empty string label")
		node_objects[node_id] = QueryNode(label)
		setattr(node_objects[node_id], "graph_id", node_id)
		roles_by_node_id[node_id] = _normalize_roles(node_record.get("roles"), node_id)

	for edge_data in edges_data:
		edge_record = _require_dict(edge_data, "Each edge must be an object")
		source_id = _require_str(edge_record.get("source"), "Each edge must have a non-empty 'source'")
		target_id = _require_str(edge_record.get("target"), "Each edge must have a non-empty 'target'")
		edge_type = _require_str(edge_record.get("type"), "Each edge must have a non-empty 'type'")
		if edge_type not in _ALLOWED_EDGE_TYPES:
			raise GraphPayloadError(f"Unsupported edge type '{edge_type}'")
		if source_id not in node_objects:
			raise GraphPayloadError(f"Edge source '{source_id}' does not exist")
		if target_id not in node_objects:
			raise GraphPayloadError(f"Edge target '{target_id}' does not exist")
		if source_id == target_id:
			raise GraphPayloadError("A node cannot reference itself as a child or descendant")
		incoming_counts[target_id] += 1
		if incoming_counts[target_id] > 1:
			raise GraphPayloadError(f"Node '{target_id}' has more than one parent")
		adjacency[source_id].append((edge_type, target_id))

	root_id = data.get("root_id")
	if root_id is not None:
		root_id = _require_str(root_id, "The root identifier must be a non-empty string")
		if root_id not in node_objects:
			raise GraphPayloadError(f"Root node '{root_id}' does not exist")
		if incoming_counts[root_id] != 0:
			raise GraphPayloadError(f"Root node '{root_id}' must not have an incoming edge")
	else:
		roots = [node_id for node_id in node_objects if incoming_counts[node_id] == 0]
		if len(roots) != 1:
			raise GraphPayloadError("The graph must contain exactly one root node")
		root_id = roots[0]

	visited: set[str] = set()
	active: set[str] = set()

	def validate_structure(node_id: str):
		if node_id in active:
			raise GraphPayloadError("The graph contains a cycle")
		if node_id in visited:
			return

		active.add(node_id)
		for _edge_type, target_id in adjacency.get(node_id, []):
			validate_structure(target_id)
		active.remove(node_id)
		visited.add(node_id)

	validate_structure(root_id)
	if len(visited) != len(node_objects):
		missing = sorted(set(node_objects) - visited)
		raise GraphPayloadError(f"The graph contains disconnected nodes: {', '.join(missing)}")

	attached: set[str] = set()

	def attach(node_id: str):
		if node_id in attached:
			return node_objects[node_id]

		node = node_objects[node_id]
		attached.add(node_id)
		for edge_type, target_id in adjacency.get(node_id, []):
			child = node_objects[target_id]
			if child.get_parent() is not None and child.get_parent() is not node:
				raise GraphPayloadError(f"Node '{target_id}' already has a parent")
			if edge_type == "child":
				node.add_child(child)
			else:
				node.add_descendant(child)
			attach(target_id)
		return node

	root = attach(root_id)
	tpq = TreePatternQuery(root)

	output_u1 = None
	output_u2 = None
	for node_id, roles in roles_by_node_id.items():
		node = node_objects[node_id]
		for role in roles:
			node.add_output_role(role)
		if "u1" in roles:
			output_u1 = node
		if "u2" in roles:
			output_u2 = node

	if output_u1 is not None or output_u2 is not None:
		tpq.set_output_nodes(output_u1, output_u2)

	tpq.set_nodes()
	if data.get("is_boolean"):
		tpq.is_boolean = True
	return tpq


def booleanize_graph_payload(payload: dict[str, Any]) -> dict[str, Any]:
	"""Convert a builder payload to its booleanized graph representation."""
	return tpq_to_graph_payload(graph_payload_to_tpq(payload).to_boolean_tpq())


