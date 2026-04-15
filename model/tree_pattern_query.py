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
		self.lab = {}
		self._frozen = False

	def add_node(self, node):
		if self._frozen:
			raise RuntimeError("Cannot add nodes after the tree is frozen.")
		if node not in self.nodes:
			self.nodes.append(node)
			# Add the label to the lab list if it's not already present
			if node.label not in self.lab:
				self.lab[node.label] = 1
			else:
				self.lab[node.label] += 1

	def set_nodes(self):
		if self._frozen:
			raise RuntimeError("Cannot modify frozen tree")
		visited = set()

		def dfs(node):
			if node in visited:
				return
			visited.add(node)

			self.add_node(node)

			for child in node.get_children():
				dfs(child)

			for descendant in node.get_descendants():
				dfs(descendant)

		dfs(self.root)
		self._frozen = True

	def get_root(self):
		return self.root

	def get_nodes(self):
		return self.nodes

	def get_labels(self):
		return self.lab

	def q(self, tree):
		# TODO: implement this method to output the result of the tree pattern query for the given tree
		pass
