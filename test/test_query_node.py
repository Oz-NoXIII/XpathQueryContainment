from unittest import TestCase

from model.query_node import QueryNode as Qnode


class TestQueryNode(TestCase):

	def test_set_label(self):
		n = Qnode("A")
		n.set_label("name")
		assert n.get_label() == "name"

	def test_get_label(self):
		n = Qnode("A")
		assert n.get_label() == "A"

	def test_get_children(self):
		n = Qnode("A")
		c1 = Qnode("B")
		c2 = Qnode("C")
		n.add_child(c1)
		n.add_child(c2)
		assert n.get_children() == [c1, c2]

	def test_get_descendants(self):
		n = Qnode("A")
		d1 = Qnode("D")
		d2 = Qnode("E")
		n.add_descendant(d1)
		n.add_descendant(d2)
		assert n.get_descendants() == [d1, d2]

	def test_get_parent(self):
		n = Qnode("A")
		c = Qnode("B")
		n.add_child(c)
		assert c.get_parent() == n

	def test_set_parent(self):
		n = Qnode("A")
		c = Qnode("B")
		c.set_parent(n)
		assert c.get_parent() == n

	def test_set_parent_edge(self):
		n = Qnode("A")
		c = Qnode("B")
		d = Qnode("C")
		n.add_child(c)
		n.add_descendant(d)
		assert c.parent_edge == "child"
		assert d.parent_edge == "descendant"

	def test_add_child(self):
		n = Qnode("A")
		c1 = Qnode("B")
		c2 = Qnode("C")
		n.add_child(c1)
		n.add_child(c2)
		assert n.get_children() == [c1, c2]
		assert c1.get_parent() == n
		assert c1.parent_edge == "child"
		assert c2.get_parent() == n
		assert c2.parent_edge == "child"

		# adding a child that already has a parent should raise an error
		m = Qnode("D")
		with self.assertRaises(ValueError):
			m.add_child(c1)

	def test_remove_child(self):
		n = Qnode("A")
		c1 = Qnode("B")
		n.add_child(c1)

		n._frozen = True
		with self.assertRaises(RuntimeError):
			n.remove_child(c1)

		n._frozen = False
		n.remove_child(c1)

		assert c1.get_parent() is None
		assert c1.parent_edge is None

		with self.assertRaises(ValueError):
			n.remove_child(c1)

	def test_add_descendant(self):
		n = Qnode("A")
		d1 = Qnode("D")
		d2 = Qnode("E")
		n.add_descendant(d1)
		n.add_descendant(d2)
		assert n.get_descendants() == [d1, d2]
		assert d1.get_parent() == n
		assert d1.parent_edge == "descendant"
		assert d2.get_parent() == n
		assert d2.parent_edge == "descendant"

		# adding a descendant that already has a parent should raise an error
		m = Qnode("D")
		with self.assertRaises(ValueError):
			m.add_descendant(d1)

	def test_remove_descendant(self):
		n = Qnode("A")
		d1 = Qnode("B")
		n.add_descendant(d1)

		n._frozen = True
		with self.assertRaises(RuntimeError):
			n.remove_descendant(d1)

		n._frozen = False
		n.remove_descendant(d1)

		assert d1.get_parent() is None
		assert d1.parent_edge is None

		with self.assertRaises(ValueError):
			n.remove_descendant(d1)

	def test_repr(self):
		n = Qnode("A")
		assert repr(n) == "QueryNode(A)"

	def test_str(self):
		n = Qnode("A")
		assert str(n) == "QueryNode(A)"

	def test_hash(self):
		n1 = Qnode("A")
		n2 = Qnode("A")
		assert hash(n1) != hash(n2)

	def test_eq(self):
		n1 = Qnode("A")
		n2 = Qnode("A")
		assert n1 == n1
		assert n1 != n2