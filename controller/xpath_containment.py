from __future__ import annotations

from typing import Any, Iterator, Sequence

from controller.expression_transformer import ExpressionTransformer
from controller.xpath_parser import XPathParser
from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery
from controller.tpq_graph_codec import graph_payload_to_tpq, tpq_to_graph_payload
from view.tpq_visualizer import TreePatternQueryVisualizer


class XPathContainmentError(ValueError):
	"""Raised when XPath containment analysis cannot be completed."""


class XPathContainmentAnalyzer:
	"""Compute the containment workflow described in `PC.pdf`."""

	def __init__(self, parser: XPathParser | None = None, transformer: ExpressionTransformer | None = None):
		self.parser = parser or XPathParser()
		self.transformer = transformer or ExpressionTransformer()

	def parse_xpath(self, expression: str) -> TreePatternQuery:
		if not isinstance(expression, str) or not expression.strip():
			raise XPathContainmentError("L'expression XPath ne peut pas être vide.")
		try:
			return self.transformer.transform(self.parser.parse(expression))
		except Exception as exc:  # pragma: no cover - propagated to the caller/UI
			raise XPathContainmentError(str(exc)) from exc

	def _tpq_artifacts(self, tpq: TreePatternQuery, expression: str | None = None) -> dict[str, Any]:
		visualizer = TreePatternQueryVisualizer(tpq)
		layout = visualizer.layout()
		payload = tpq_to_graph_payload(tpq)
		payload["layout"] = {"width": layout.get("width"), "height": layout.get("height")}
		if expression is not None:
			payload["formatted_query"] = visualizer._format_xpath_query_for_display(expression)
		return {"payload": payload, "svg": visualizer.to_svg()}

	def transform_queries(self, q1_expression: str, q2_expression: str) -> dict[str, Any]:
		q1 = self.parse_xpath(q1_expression)
		q2 = self.parse_xpath(q2_expression)
		return {
			"q1": self._tpq_artifacts(q1, q1_expression),
			"q2": self._tpq_artifacts(q2, q2_expression),
		}

	def booleanize(self, tpq: TreePatternQuery) -> TreePatternQuery:
		if not isinstance(tpq, TreePatternQuery):
			raise TypeError("L'objet fourni doit être un TreePatternQuery.")
		return tpq.to_boolean_tpq()

	def booleanize_queries(self, q1_payload: dict[str, Any], q2_payload: dict[str, Any]) -> dict[str, Any]:
		q1 = self.booleanize(graph_payload_to_tpq(q1_payload))
		q2 = self.booleanize(graph_payload_to_tpq(q2_payload))
		return {
			"q1": self._tpq_artifacts(q1),
			"q2": self._tpq_artifacts(q2),
		}

	def clone_tpq(self, tpq: TreePatternQuery, freeze: bool = False) -> TreePatternQuery:
		if not isinstance(tpq, TreePatternQuery):
			raise TypeError("L'objet fourni doit être un TreePatternQuery.")

		memo: dict[QueryNode, QueryNode] = {}

		def clone_node(node: QueryNode) -> QueryNode:
			if node in memo:
				return memo[node]

			cloned = QueryNode(node.get_label())
			memo[node] = cloned
			for role in node.get_output_roles():
				cloned.add_output_role(role)

			for child in node.get_children():
				cloned_child = clone_node(child)
				cloned.add_child(cloned_child)

			for descendant in node.get_descendants():
				cloned_descendant = clone_node(descendant)
				cloned.add_descendant(cloned_descendant)

			return cloned

		cloned_root = clone_node(tpq.get_root())
		cloned_tpq = TreePatternQuery(cloned_root)
		cloned_tpq.is_boolean = bool(getattr(tpq, "is_boolean", False))
		if freeze:
			cloned_tpq.set_nodes()
		return cloned_tpq

	def descendant_edge_nodes(self, tpq: TreePatternQuery) -> list[QueryNode]:
		nodes = tpq.get_nodes() or tpq._preorder_nodes()
		return [node for node in nodes if getattr(node, "parent_edge", None) == "descendant"]

	def enumerate_length_combinations(self, descendant_count: int, size_bound: int) -> Iterator[tuple[int, ...]]:
		if descendant_count < 0:
			raise ValueError("Le nombre de descendants ne peut pas être négatif.")
		if size_bound < 0:
			raise ValueError("La borne de taille ne peut pas être négative.")

		if descendant_count == 0:
			yield ()
			return

		current: list[int] = []

		def backtrack(index: int, remaining_extra: int):
			if index == descendant_count:
				yield tuple(current)
				return

			for extra in range(remaining_extra + 1):
				current.append(extra + 1)
				yield from backtrack(index + 1, remaining_extra - extra)
				current.pop()

		yield from backtrack(0, size_bound)

	def build_canonical_tree(self, q1_boolean: TreePatternQuery, lengths: Sequence[int]) -> TreePatternQuery:
		if not isinstance(q1_boolean, TreePatternQuery):
			raise TypeError("Q1 doit être un TreePatternQuery.")
		if any(length < 1 for length in lengths):
			raise XPathContainmentError("Toutes les longueurs L doivent être positives.")

		canonical = self.clone_tpq(q1_boolean)
		descendant_nodes = self.descendant_edge_nodes(canonical)
		if len(lengths) != len(descendant_nodes):
			raise XPathContainmentError("Le vecteur L doit avoir la même taille que les nœuds descendant.")

		for node, length in zip(descendant_nodes, lengths):
			parent = node.get_parent()
			if parent is None:
				raise XPathContainmentError("Un nœud descendant n'a pas de parent à détacher.")
			if node.parent_edge != "descendant":
				continue

			parent.remove_descendant(node)
			previous = parent
			for _ in range(length - 1):
				bridge = QueryNode("*")
				previous.add_child(bridge)
				previous = bridge
			previous.add_child(node)

		canonical.set_nodes()
		return canonical

	def _label_compatible(self, left_label: str, right_label: str) -> bool:
		return left_label == "*" or right_label == "*" or left_label == right_label

	def evaluate_containment(self, source_tpq: TreePatternQuery, target_tpq: TreePatternQuery, *, source_name: str = "q1", target_name: str = "q2") -> dict[str, Any]:
		if not isinstance(source_tpq, TreePatternQuery) or not isinstance(target_tpq, TreePatternQuery):
			raise TypeError("Les deux arguments doivent être des TreePatternQuery.")

		source_nodes = source_tpq.get_nodes() or source_tpq._preorder_nodes()
		target_nodes = target_tpq.get_nodes() or target_tpq._preorder_nodes()
		source_descendants = self.descendant_edge_nodes(source_tpq)
		size_bound = len(source_nodes) * len(target_nodes)
		attempts: list[dict[str, Any]] = []

		contained = True
		counterexample_tree: TreePatternQuery | None = None
		counterexample_lengths: list[int] | None = None

		for lengths in self.enumerate_length_combinations(len(source_descendants), size_bound):
			canonical_tree = self.build_canonical_tree(source_tpq, lengths)
			homomorphism = self.find_homomorphism(target_tpq, canonical_tree)
			attempts.append(
				{
					"L": list(lengths),
					"exists": homomorphism["exists"],
					"message": homomorphism["message"],
					"canonical_tree_svg": TreePatternQueryVisualizer(canonical_tree).to_svg(),
					"mapping": homomorphism.get("mapping", []),
				}
			)
			if not homomorphism["exists"]:
				contained = False
				counterexample_tree = canonical_tree
				counterexample_lengths = list(lengths)
				break

		return {
			"contained": contained,
			"summary": (
				f"{source_name} est inclus dans {target_name}."
				if contained
				else f"{source_name} n'est pas inclus dans {target_name} : un arbre canonique Tc a servi de contre-exemple."
			),
			"size_bound": size_bound,
			"descendant_count": len(source_descendants),
			"attempts": attempts,
			"counterexample_lengths": counterexample_lengths,
			"counterexample_tree": TreePatternQueryVisualizer(counterexample_tree).to_svg() if counterexample_tree is not None else None,
		}

	def find_homomorphism(self, source_tpq: TreePatternQuery, target_tpq: TreePatternQuery) -> dict[str, Any]:
		if not isinstance(source_tpq, TreePatternQuery) or not isinstance(target_tpq, TreePatternQuery):
			raise TypeError("Les deux arguments doivent être des TreePatternQuery.")

		source_nodes = source_tpq.get_nodes() or source_tpq._preorder_nodes()
		target_nodes = target_tpq.get_nodes() or target_tpq._preorder_nodes()
		source_node_to_id = source_tpq._node_to_id_map("source")
		target_node_to_id = target_tpq._node_to_id_map("target")

		source_labels = {node: node.get_label() for node in source_nodes}
		target_labels = {node: node.get_label() for node in target_nodes}
		source_outgoing = {
			node: [("child", child) for child in node.get_children()] + [("descendant", descendant) for descendant in node.get_descendants()]
			for node in source_nodes
		}
		target_outgoing = {
			node: [("child", child) for child in node.get_children()] + [("descendant", descendant) for descendant in node.get_descendants()]
			for node in target_nodes
		}

		memo: dict[tuple[QueryNode, QueryNode], bool] = {}
		witness: dict[QueryNode, QueryNode] = {}

		def candidate_targets(parent_target: QueryNode, edge_type: str) -> list[QueryNode]:
			if edge_type == "child":
				return [child for _edge_type, child in target_outgoing.get(parent_target, []) if _edge_type == "child"]
			return target_tpq._strict_descendants(parent_target)

		def match(source_node: QueryNode, target_node: QueryNode) -> bool:
			key = (source_node, target_node)
			if key in memo:
				return memo[key]

			if not self._label_compatible(str(source_labels[source_node]), str(target_labels[target_node])):
				memo[key] = False
				return False

			for edge_type, child in source_outgoing.get(source_node, []):
				matched = False
				for candidate in candidate_targets(target_node, edge_type):
					if match(child, candidate):
						matched = True
						break
				if not matched:
					memo[key] = False
					return False

			witness[source_node] = target_node
			memo[key] = True
			return True

		exists = match(source_tpq.get_root(), target_tpq.get_root())
		if not exists:
			return {
				"exists": False,
				"message": "Aucun homomorphisme n'a été trouvé.",
				"mapping": [],
				"highlight_target_ids": [],
			}

		mapping = []
		for source_node in source_nodes:
			target_node = witness[source_node]
			mapping.append(
				{
					"source_id": source_node_to_id[source_node],
					"source_label": source_labels[source_node],
					"target_id": target_node_to_id[target_node],
					"target_label": target_labels[target_node],
				}
			)

		return {
			"exists": True,
			"message": "Homomorphisme trouvé.",
			"mapping": mapping,
			"highlight_target_ids": list(dict.fromkeys(item["target_id"] for item in mapping)),
		}

	def analyze(self, q1_expression: str, q2_expression: str) -> dict[str, Any]:
		steps = self.transform_queries(q1_expression, q2_expression)
		boolean_steps = self.booleanize_queries(steps["q1"]["payload"], steps["q2"]["payload"])
		q1_boolean = graph_payload_to_tpq(boolean_steps["q1"]["payload"])
		q2_boolean = graph_payload_to_tpq(boolean_steps["q2"]["payload"])
		containment = self.evaluate_containment(q1_boolean, q2_boolean, source_name="q1", target_name="q2")
		return {
			"contained": containment["contained"],
			"summary": containment["summary"],
			"step_raw": {"q1": steps["q1"], "q2": steps["q2"]},
			"step_booleanize": {"q1": boolean_steps["q1"], "q2": boolean_steps["q2"]},
			"size_bound": containment["size_bound"],
			"descendant_count": containment["descendant_count"],
			"attempts": containment["attempts"],
			"counterexample_lengths": containment["counterexample_lengths"],
			"counterexample_tree": containment["counterexample_tree"],
			"q1_expression": q1_expression,
			"q2_expression": q2_expression,
		}



def analyze_xpath_containment(q1_expression: str, q2_expression: str) -> dict[str, Any]:
	"""Convenience wrapper used by the HTTP layer and tests."""
	return XPathContainmentAnalyzer().analyze(q1_expression, q2_expression)



