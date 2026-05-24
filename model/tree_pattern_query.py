"""
This module defines the TreePatternQuery class, which represents a tree pattern query.
It allows you to define a tree pattern query and then execute the query against a given
tree to find the result of it.
"""

from __future__ import annotations

from typing import Any

from model.query_node import QueryNode


class TreePatternQuery:
	"""
	A class representing a tree pattern query.
	"""

	def __init__(self, root):
		self.root = root
		self.nodes = []
		self.labs = {}
		self.output_u1 = None
		self.output_u2 = None
		self.is_boolean = False
		self._frozen = False

	def add_node(self, node):
		if self._frozen:
			raise RuntimeError("Cannot add nodes after the tree is frozen.")
		if node not in self.nodes:
			self.nodes.append(node)
			# Add the label to the labs list if it's not already present
			if node.label not in self.labs:
				self.labs[node.label] = 1
			else:
				self.labs[node.label] += 1

	def set_nodes(self):
		if self._frozen:
			raise RuntimeError("Cannot modify frozen tree")

		def dfs(node):
			self.add_node(node)
			if node.is_u1_output_node():
				self.output_u1 = node
			if node.is_u2_output_node():
				self.output_u2 = node

			for child in node.get_children():
				dfs(child)

			for descendant in node.get_descendants():
				dfs(descendant)

			node._frozen = True

		dfs(self.root)
		self._frozen = True

	def set_output_nodes(self, u1, u2):
		self.output_u1 = u1
		self.output_u2 = u2
		if u1 is not None:
			u1.add_output_role("u1")
		if u2 is not None:
			u2.add_output_role("u2")

	def get_output_nodes(self):
		return self.output_u1, self.output_u2

	def to_boolean_tpq(self):
		"""Return a boolean TPQ obtained by attaching sentinel children.

		Each output node u_i gets a fresh child labeled o_i, and each non-output
		leaf gets a fresh wildcard child labeled *.
		"""
		if getattr(self, 'is_boolean', False):
			return self

		# Booleanization should use the output nodes resolved during construction.
		# If construction is correct, we should not need q() here.
		output_u1 = self.output_u1
		output_u2 = self.output_u2

		memo = {}

		def clone(node):
			node_id = id(node)
			if node_id in memo:
				return memo[node_id]

			cloned = QueryNode(node.get_label())
			memo[node_id] = cloned

			for child in node.get_children():
				cloned_child = clone(child)
				cloned.add_child(cloned_child)

			for descendant in node.get_descendants():
				cloned_descendant = clone(descendant)
				cloned.add_descendant(cloned_descendant)

			has_outgoing_edges = bool(node.get_children() or node.get_descendants())
			if node is output_u1:
				cloned.add_child(QueryNode("o1"))
			if node is output_u2:
				cloned.add_child(QueryNode("o2"))
			if not has_outgoing_edges and node is not output_u1 and node is not output_u2:
				cloned.add_child(QueryNode("*"))

			return cloned

		boolean_root = clone(self.root)
		boolean_tpq = TreePatternQuery(boolean_root)
		boolean_tpq.is_boolean = True
		boolean_tpq.set_nodes()
		return boolean_tpq

	def booleanize(self):
		"""Alias for to_boolean_tpq()."""
		return self.to_boolean_tpq()

	def get_root(self):
		return self.root

	def get_nodes(self):
		return list(self.nodes)

	def get_labels(self):
		return dict(self.labs)

	def _preorder_nodes(self, node=None, result=None):
		if result is None:
			result = []
		if node is None:
			node = self.root
		if node in result:
			return result
		result.append(node)
		for child in node.get_children():
			self._preorder_nodes(child, result)
		for descendant in node.get_descendants():
			self._preorder_nodes(descendant, result)
		return result

	def _strict_descendants(self, node):
		result = []
		stack = list(reversed(node.get_children())) + list(reversed(node.get_descendants()))
		seen = set()
		while stack:
			current = stack.pop()
			if current in seen:
				continue
			seen.add(current)
			result.append(current)
			for child in reversed(current.get_children()):
				stack.append(child)
			for descendant in reversed(current.get_descendants()):
				stack.append(descendant)
		return result

	def _node_to_id_map(self, prefix):
		mapping = {}
		for index, node in enumerate(self.get_nodes() or self._preorder_nodes()):
			# Prefer an existing explicit graph_id, otherwise generate one
			node_id = getattr(node, "graph_id", None)
			if not isinstance(node_id, str) or not node_id:
				node_id = f"{prefix}_{index}"
			# Persist the id on the node so renderers can reuse it
			setattr(node, "graph_id", node_id)
			mapping[node] = node_id
		return mapping

	def find_bool_tpq_lab_homomorphism(self, target_tpq: TreePatternQuery) -> dict[str, Any]:
		"""Find a label-preserving homomorphism from this BoolTPQ_Lab to another one."""
		if not isinstance(target_tpq, TreePatternQuery):
			raise TypeError("The target query must be a TreePatternQuery instance.")

		source_nodes = self.get_nodes() or self._preorder_nodes()
		target_nodes = target_tpq.get_nodes() or target_tpq._preorder_nodes()
		source_node_to_id = self._node_to_id_map("source")
		target_node_to_id = target_tpq._node_to_id_map("target")

		source_labels = {node: node.get_label() for node in source_nodes}
		target_labels = {node: node.get_label() for node in target_nodes}
		source_outgoing = {node: [("child", child) for child in node.get_children()] + [("descendant", descendant) for descendant in node.get_descendants()] for node in source_nodes}
		target_outgoing = {node: [("child", child) for child in node.get_children()] + [("descendant", descendant) for descendant in node.get_descendants()] for node in target_nodes}

		memo = {}
		witness = {}

		def candidate_targets(parent_target, edge_type):
			if edge_type == "child":
				return [child for _edge_type, child in target_outgoing.get(parent_target, []) if _edge_type == "child"]
			return target_tpq._strict_descendants(parent_target)

		def match(source_node, target_node):
			key = (source_node, target_node)
			if key in memo:
				return memo[key]

			# Support wildcard labels: '*' matches any label.
			slabel = source_labels[source_node]
			tlabel = target_labels[target_node]
			if slabel != '*' and tlabel != '*' and slabel != tlabel:
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

		exists = match(self.root, target_tpq.root)
		if not exists:
			return {
				"exists": False,
				"message": "Aucun homomorphisme n'a été trouvé entre q1 et q2.",
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
			"message": "Homomorphisme trouvé entre q1 et q2.",
			"mapping": mapping,
			"highlight_target_ids": list(dict.fromkeys(item["target_id"] for item in mapping)),
		}

	def find_homomorphism(self, target_tpq: TreePatternQuery) -> dict[str, Any]:
		"""Alias used by the backend to compare two TreePatternQuery instances."""
		return self.find_bool_tpq_lab_homomorphism(target_tpq)

	def q(self, tree):
		# If this TPQ represents a boolean query (BoolTPQ), there are no output nodes.
		if getattr(self, 'is_boolean', False):
			return None, None

		# The transformer may have marked output nodes during construction; q()
		# also repairs compositions where the left output should be the nearest
		# wildcard ancestor of u2 in the final tree.
		output_u1 = self.output_u1
		output_u2 = self.output_u2

		if output_u1 is None or output_u2 is None:
			for node in self.nodes:
				if output_u1 is None and node.is_u1_output_node():
					output_u1 = node
				if output_u2 is None and node.is_u2_output_node():
					output_u2 = node

		def find_wildcard_ancestor(node):
			current = node
			while current is not None:
				if current.get_label() == "*":
					return current
				current = current.get_parent()
			return None

		# Only apply wildcard ancestor logic if output_u1 is None or is the root.
		# This preserves explicitly-set output nodes like u1=d in child[(lab=d)]/child[(lab=a)]
		if output_u2 is not None and (output_u1 is None or output_u1 is self.root):
			wildcard_ancestor = find_wildcard_ancestor(output_u2)
			if wildcard_ancestor is not None:
				output_u1 = wildcard_ancestor

		if output_u1 is None:
			output_u1 = self.root
		if output_u2 is None:
			output_u2 = self.root

		return output_u1, output_u2

	def __repr__(self):
		return f"TreePatternQuery(root={self.root}, nodes={self.nodes}, lab={self.labs})"