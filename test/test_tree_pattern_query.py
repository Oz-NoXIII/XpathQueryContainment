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
		e = Qnode("F")
		t.get_nodes().append(e)
		assert t.get_nodes() == [n, c1, c2, d1, d2]
		# error if we try to modify the tree after it's frozen
		with self.assertRaises(RuntimeError):
			t.set_nodes()
		# error if we try to add a node after the tree is frozen
		with self.assertRaises(RuntimeError):
			t.add_node(Qnode("G"))
		# error if we try to modify a node after it's frozen
		with self.assertRaises(RuntimeError):
			n.add_child(Qnode("H"))
		# error if we try to modify a descendant after it's frozen
		with self.assertRaises(RuntimeError):
			n.add_descendant(Qnode("I"))

		# error if we try to modify a child after it's frozen
		with self.assertRaises(RuntimeError):
			c1.add_child(Qnode("J"))
		# error if we try to modify a child after it's frozen
		with self.assertRaises(RuntimeError):
			c1.add_descendant(Qnode("K"))

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

	def test_q(self):
		u1 = Qnode("A")
		u2 = Qnode("B")
		u1.add_child(u2)
		t = TPQ(u1)
		t.set_output_nodes(u1, u2)
		t.set_nodes()
		assert t.q(None) == (u1, u2)
		assert t.get_output_nodes() == (u1, u2)

		fallback_root = Qnode("C")
		fallback = TPQ(fallback_root)
		fallback.set_nodes()
		assert fallback.q(None) == (fallback_root, fallback_root)

	def test_to_boolean_tpq_attaches_sentinel_children(self):
		root = Qnode("root")
		output_leaf = Qnode("out")
		plain_leaf = Qnode("plain")
		root.add_child(output_leaf)
		root.add_child(plain_leaf)
		tpq = TPQ(root)
		tpq.set_output_nodes(root, output_leaf)
		tpq.set_nodes()

		boolean_tpq = tpq.to_boolean_tpq()
		boolean_root = boolean_tpq.get_root()

		assert boolean_tpq is not tpq
		assert boolean_tpq.is_boolean is True
		assert tpq.is_boolean is False
		assert tpq.get_root().get_children() == [output_leaf, plain_leaf]
		assert boolean_tpq.get_output_nodes() == (None, None)
		assert boolean_root.get_label() == "root"

		child_labels = [child.get_label() for child in boolean_root.get_children()]
		assert child_labels == ["out", "plain", "o1"]
		assert [child.get_label() for child in boolean_root.get_children()[0].get_children()] == ["o2"]
		assert [child.get_label() for child in boolean_root.get_children()[1].get_children()] == ["*"]

	def test_to_boolean_tpq_uses_resolved_output_u1(self):
		from controller.expression_transformer import ExpressionTransformer
		from controller.xpath_parser import XPathParser

		expression = "(self[(lab = *)&?descendant[(lab = c)]&?ancestor[(lab = a)&?child[(lab = b)&?child[(lab = c)]]&?descendant[(lab = e)]]]/child[(lab = d)])"
		tpq = ExpressionTransformer().transform(XPathParser().parse(expression))
		boolean_tpq = tpq.to_boolean_tpq()

		root = boolean_tpq.get_root()
		wildcard = root.get_descendants()[1]
		assert root.get_label() == "a"
		assert wildcard.get_label() == "*"
		assert {child.get_label() for child in wildcard.get_children()} == {"d", "o1"}

	def test_find_bool_tpq_lab_homomorphism_uses_model_nodes(self):
		source_root = Qnode("a")
		source_child = Qnode("c")
		source_descendant = Qnode("b")
		source_root.add_child(source_child)
		source_root.add_descendant(source_descendant)
		source = TPQ(source_root)
		source.set_nodes()

		target_root = Qnode("a")
		target_child = Qnode("c")
		target_mid = Qnode("x")
		target_descendant = Qnode("b")
		target_root.add_child(target_child)
		target_root.add_descendant(target_mid)
		target_mid.add_child(target_descendant)
		target = TPQ(target_root)
		target.set_nodes()

		result = source.find_bool_tpq_lab_homomorphism(target)

		assert result["exists"] is True
		assert [item["source_label"] for item in result["mapping"]] == ["a", "c", "b"]
		assert [item["target_label"] for item in result["mapping"]] == ["a", "c", "b"]
		assert result["highlight_target_ids"] == ["target_0", "target_1", "target_3"]

	def test_find_bool_tpq_lab_homomorphism_reports_failure(self):
		source_root = Qnode("a")
		source_child = Qnode("z")
		source_root.add_child(source_child)
		source = TPQ(source_root)
		source.set_nodes()

		target_root = Qnode("a")
		target_child = Qnode("c")
		target_root.add_child(target_child)
		target = TPQ(target_root)
		target.set_nodes()

		result = source.find_bool_tpq_lab_homomorphism(target)

		assert result["exists"] is False
		assert result["mapping"] == []

