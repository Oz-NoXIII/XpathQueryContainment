from unittest import TestCase

from model.tree_pattern_query import TreePatternQuery as TPQ
from model.query_node import QueryNode as Qnode

class TestTreePatternQuery(TestCase):
	def test_add_node(self):
		n = Qnode("A")
		t = TPQ(n)
		t.add_node(n)
		assert t.get_nodes() == [n]
		assert t.get_labels() == {"A": 1}

		# adding the same node again should not change the nodes list
		t.add_node(n)
		assert t.get_nodes() == [n]
		assert t.get_labels() == {"A": 1}

		# adding a different node with the same label should update the label count
		n2 = Qnode("A")
		t.add_node(n2)
		assert t.get_nodes() == [n, n2]
		assert t.get_labels() == {"A": 2}

		# error if we try to add a node after the tree is frozen
		t._frozen = True
		with self.assertRaises(RuntimeError):
			t.add_node(Qnode("B"))

	def test_get_root(self):
		n = Qnode("A")
		t = TPQ(n)
		assert t.get_root() == n

	def test_get_nodes(self):
		n = Qnode("A")
		c1 = Qnode("B")
		c2 = Qnode("C")
		n.add_child(c1)
		n.add_child(c2)
		d1 = Qnode("D")
		d2 = Qnode("E")
		n.add_descendant(d1)
		n.add_descendant(d2)
		t = TPQ(n)
		t.set_nodes()
		assert t.get_nodes() == [n, c1, c2, d1, d2]
		# error if we try to modify the tree after it's frozen
		with self.assertRaises(RuntimeError):
			t.set_nodes()

	def test_get_labels(self):
		n = Qnode("A")
		c1 = Qnode("B")
		c2 = Qnode("C")
		n.add_child(c1)
		n.add_child(c2)
		d1 = Qnode("D")
		d2 = Qnode("E")
		n.add_descendant(d1)
		n.add_descendant(d2)
		t = TPQ(n)
		t.set_nodes()
		assert t.get_labels() == {"A": 1, "B": 1, "C": 1, "D": 1, "E": 1}

	def test_output(self):
		# TODO: implement this test once the output method is implemented
		pass