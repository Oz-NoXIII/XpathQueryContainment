"""
This module defines the TreePatternQuery class, which represents a tree pattern query.
It allows you to define a tree pattern query and then execute the query against a given
tree to find the result of it.
"""


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
		return self.q(None)

	def get_root(self):
		return self.root

	def get_nodes(self):
		return list(self.nodes)

	def get_labels(self):
		return dict(self.labs)

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