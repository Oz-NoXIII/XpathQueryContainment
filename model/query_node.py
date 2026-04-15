"""
This module defines the QueryNode class, which represents a node in a tree pattern query.
"""


class QueryNode:
	"""
	A class representing a node in a tree pattern query.
	"""

	def __init__(self, label, parent=None, parent_edge=None):
		self.label = label

		# "/" edges
		self.children = []

		# "//" edges
		self.descendants = []

		self.parent = parent
		self.parent_edge = parent_edge  # "child" or "descendant"

	def get_label(self):
		return self.label

	def get_children(self):
		return self.children

	def get_descendants(self):
		return self.descendants

	def get_parent(self):
		return self.parent

	def set_parent(self, parent):
		self.parent = parent

	def set_parent_edge(self, edge_type):
		self.parent_edge = edge_type

	def add_child(self, child):
		self.children.append(child)
		child.set_parent(self)
		child.set_parent_edge("child")

	def add_descendant(self, descendant):
		self.descendants.append(descendant)
		descendant.set_parent(self)
		descendant.set_parent_edge("descendant")

	def __repr__(self):
		return f"QueryNode({self.label})"

	def __hash__(self):
		return id(self)

	def __eq__(self, other):
		return self is other
