from __future__ import annotations

from typing import Any

from controller.tpq_graph_codec import GraphPayloadError, graph_payload_to_tpq
from model.tree_pattern_query import TreePatternQuery


class BoolTPQLabPayloadError(ValueError):
	"""Raised when a BoolTPQ_Lab payload is invalid."""

_ALLOWED_EDGE_TYPES = {"child", "descendant"}


def _require_dict(value: Any, message: str) -> dict[str, Any]:
	if not isinstance(value, dict):
		raise BoolTPQLabPayloadError(message)
	return value


def _require_list(value: Any, message: str) -> list[Any]:
	if not isinstance(value, list):
		raise BoolTPQLabPayloadError(message)
	return value


def _require_str(value: Any, message: str) -> str:
	if not isinstance(value, str) or not value:
		raise BoolTPQLabPayloadError(message)
	return value


def _validate_bool_tpq_lab_payload(payload: Any) -> dict[str, Any]:
	data = _require_dict(payload, "Le graphe doit être un objet JSON.")
	nodes_data = _require_list(data.get("nodes"), "Le graphe doit contenir une liste 'nodes'.")
	_require_list(data.get("edges"), "Le graphe doit contenir une liste 'edges'.")
	if not nodes_data:
		raise BoolTPQLabPayloadError("Le graphe doit contenir au moins un nœud.")

	seen_ids: set[str] = set()
	for index, node_data in enumerate(nodes_data, start=1):
		node = _require_dict(node_data, f"Le nœud #{index} doit être un objet JSON.")
		node_id = _require_str(node.get("id"), f"Le nœud #{index} doit avoir un identifiant non vide.")
		if node_id in seen_ids:
			raise BoolTPQLabPayloadError(f"L'identifiant de nœud '{node_id}' est dupliqué.")
		seen_ids.add(node_id)
		label = _require_str(node.get("label"), f"Le nœud '{node_id}' doit avoir un label non vide.")
		if label == "*":
			raise BoolTPQLabPayloadError(f"Le nœud '{node_id}' ne peut pas utiliser de wildcard.")
		roles = node.get("roles")
		if roles not in (None, []):
			raise BoolTPQLabPayloadError(f"Le nœud '{node_id}' ne doit pas contenir de rôles dans un BoolTPQ_Lab.")

	root_id = data.get("root_id")
	if root_id is not None:
		_require_str(root_id, "L'identifiant de racine doit être une chaîne non vide.")

	return data


def parse_bool_tpq_lab_payload(payload: Any) -> TreePatternQuery:
	"""Validate a BoolTPQ_Lab payload and convert it to a TreePatternQuery."""
	data = _validate_bool_tpq_lab_payload(payload)
	try:
		return graph_payload_to_tpq(data)
	except GraphPayloadError as exc:
		raise BoolTPQLabPayloadError(str(exc)) from exc


def find_bool_tpq_lab_homomorphism(source_payload: Any, target_payload: Any) -> dict[str, Any]:
	"""Find a label-preserving homomorphism from q1 to q2, if one exists."""
	source = parse_bool_tpq_lab_payload(source_payload)
	target = parse_bool_tpq_lab_payload(target_payload)
	return source.find_bool_tpq_lab_homomorphism(target)


def find_tpq_homomorphism(source_tpq: Any, target_tpq: Any) -> dict[str, Any]:
	"""Find a label-preserving homomorphism from source_tpq to target_tpq."""
	if not isinstance(source_tpq, TreePatternQuery) or not isinstance(target_tpq, TreePatternQuery):
		raise TypeError("Both arguments must be TreePatternQuery instances.")
	return source_tpq.find_homomorphism(target_tpq)

