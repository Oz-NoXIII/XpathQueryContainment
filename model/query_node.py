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

		self.output_node = False
		self._frozen = False

	def get_label(self):
		return self.label

	def set_label(self, label):
		self.label = label

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
		if self._frozen:
			raise RuntimeError("Cannot modify frozen node")
		if child.parent is not None:
			raise ValueError("Node already has a parent")
		self.children.append(child)
		child.set_parent(self)
		child.set_parent_edge("child")

	def remove_child(self, child):
		if self._frozen:
			raise RuntimeError("Cannot modify frozen node")
		if child.parent is None:
			raise ValueError("Node does not have a parent")
		self.children.remove(child)
		child.set_parent(None)
		child.set_parent_edge(None)

	def add_descendant(self, descendant):
		if self._frozen:
			raise RuntimeError("Cannot modify frozen node")
		if descendant.parent is not None:
			raise ValueError("Node already has a parent")
		self.descendants.append(descendant)
		descendant.set_parent(self)
		descendant.set_parent_edge("descendant")

	def remove_descendant(self, descendant):
		if self._frozen:
			raise RuntimeError("Cannot modify frozen node")
		if descendant.parent is None:
			raise ValueError("Node does not have a parent")
		self.descendants.remove(descendant)
		descendant.set_parent(None)
		descendant.set_parent_edge(None)

	def is_an_output_node(self):
		return self.output_node

	def __repr__(self):
		return f"QueryNode({self.label})"

	def __hash__(self):
		return id(self)

	def __eq__(self, other):
		return self is other
