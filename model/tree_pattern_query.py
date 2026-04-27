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

			for child in node.get_children():
				dfs(child)

			for descendant in node.get_descendants():
				dfs(descendant)

			node._frozen = True

		dfs(self.root)
		self._frozen = True

	def get_root(self):
		return self.root

	def get_nodes(self):
		return list(self.nodes)

	def get_labels(self):
		return dict(self.labs)

	def q(self, tree):
		# TODO: implement this method to output the result of the tree pattern query for the given tree
		pass

	def __repr__(self):
		return f"TreePatternQuery(root={self.root}, nodes={self.nodes}, lab={self.labs})"