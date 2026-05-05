from unittest import TestCase

from controller.expression_transformer import ExpressionTransformer
from controller.xpath_parser import XPathParser


class TestExpressionTransformer(TestCase):
    def setUp(self):
        self.parser = XPathParser()
        self.transformer = ExpressionTransformer()

    def _transform(self, expression):
        tree = self.parser.parse(expression)
        return self.transformer.transform(tree)

    def _assert_output_nodes(self, tpq, expected_u1, expected_u2):
        u1, u2 = tpq.get_output_nodes()
        assert u1 is not None
        assert u2 is not None
        assert u1.get_label() == expected_u1.get_label()
        assert u2.get_label() == expected_u2.get_label()

    def test_simple_transform(self):
        expressions = [
            "self[(lab = *)]",
            "self[(lab = person)]",
        ]

        tpq = self._transform(expressions[0])
        root = tpq.get_root()
        with self.subTest(expression=expressions[0]):
            assert root.get_label() == "*"
            assert root.get_children() == []
            assert root.get_descendants() == []
            self._assert_output_nodes(tpq, root, root)
            assert root.get_output_roles() == frozenset({"u1", "u2"})

        tpq = self._transform(expressions[1])
        root = tpq.get_root()
        with self.subTest(expression=expressions[1]):
            assert root.get_label() == "person"
            assert root.get_children() == []
            assert root.get_descendants() == []
            self._assert_output_nodes(tpq, root, root)
            assert root.get_output_roles() == frozenset({"u1", "u2"})


    def test_transform_with_wildcard_predicate(self):
        expressions = [
            "child[(lab = *)]",
            "descendant[(lab = *)]",
            "parent[(lab = *)]",
            "ancestor[(lab = *)]"
        ]

        tpq = self._transform(expressions[0])
        root = tpq.get_root()
        children = root.get_children()
        child = children[0]
        with self.subTest(expression=expressions[0]):
            assert root.get_label() == "*"
            assert len(children) == 1
            assert child.get_label() == "*"
            assert root.get_descendants() == []
            self._assert_output_nodes(tpq, root, child)
            assert root.get_output_roles() == frozenset({"u1"})
            assert child.get_output_roles() == frozenset({"u2"})

        tpq = self._transform(expressions[1])
        root = tpq.get_root()
        descendants = root.get_descendants()
        descendant = descendants[0]
        with self.subTest(expression=expressions[1]):
            assert root.get_label() == "*"
            assert root.get_children() == []
            assert len(descendants) == 1
            assert descendant.get_label() == "*"
            self._assert_output_nodes(tpq, root, descendant)
            assert root.get_output_roles() == frozenset({"u1"})
            assert descendant.get_output_roles() == frozenset({"u2"})

        tpq = self._transform(expressions[2])
        root = tpq.get_root()
        children = root.get_children()
        child = children[0]
        with self.subTest(expression=expressions[2]):
            assert root.get_label() == "*"
            assert len(children) == 1
            assert child.get_label() == "*"
            assert root.get_descendants() == []
            self._assert_output_nodes(tpq, root, child)
            assert root.get_output_roles() == frozenset({"u1"})
            assert child.get_output_roles() == frozenset({"u2"})

        tpq = self._transform(expressions[3])
        root = tpq.get_root()
        descendants = root.get_descendants()
        descendant = descendants[0]
        with self.subTest(expression=expressions[3]):
            assert root.get_label() == "*"
            assert root.get_children() == []
            assert len(descendants) == 1
            assert descendant.get_label() == "*"
            self._assert_output_nodes(tpq, root, descendant)
            assert root.get_output_roles() == frozenset({"u1"})
            assert descendant.get_output_roles() == frozenset({"u2"})

    def test_transform_with_label_predicate(self):
        expressions = [
            "child[(lab = person)]",
            "descendant[(lab = person)]",
            "parent[(lab = person)]",
            "ancestor[(lab = person)]",
            "self[(lab = person)& ?child[(lab = name)]]"
        ]

        tpq = self._transform(expressions[0])
        root = tpq.get_root()
        children = root.get_children()
        child = children[0]
        with self.subTest(expression=expressions[0]):
            assert root.get_label() == "*"
            assert len(children) == 1
            assert child.get_label() == "person"
            assert root.get_descendants() == []
            # TODO: root.output_node and child.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[1])
        root = tpq.get_root()
        descendants = root.get_descendants()
        descendant = descendants[0]
        with self.subTest(expression=expressions[1]):
            assert root.get_label() == "*"
            assert root.get_children() == []
            assert len(descendants) == 1
            assert descendant.get_label() == "person"
            # TODO: root.output_node and descendant.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[2])
        root = tpq.get_root()
        children = root.get_children()
        child = children[0]
        with self.subTest(expression=expressions[2]):
            assert root.get_label() == "person"
            assert len(children) == 1
            assert child.get_label() == "*"
            assert root.get_descendants() == []
            # TODO: child.output_node and root.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[3])
        root = tpq.get_root()
        descendants = root.get_descendants()
        descendant = descendants[0]
        with self.subTest(expression=expressions[3]):
            assert root.get_label() == "person"
            assert root.get_children() == []
            assert len(descendants) == 1
            assert descendant.get_label() == "*"
            # TODO: descendant.output_node and root.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[4])
        root = tpq.get_root()
        children = root.get_children()
        child = children[0]
        with self.subTest(expression=expressions[4]):
            assert root.get_label() == "person"
            assert len(children) == 1
            assert child.get_label() == "name"
            assert root.get_descendants() == []
            self._assert_output_nodes(tpq, root, root)
            assert root.get_output_roles() == frozenset({"u1", "u2"})
            assert child.get_output_roles() == frozenset()

    def test_transform_with_and_between_two_step_predicates(self):
        expression = "self[?child[(lab = name)] & ?descendant[(lab = age)]]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "*"
        assert len(root.get_children()) == 1
        assert root.get_children()[0].get_label() == "name"
        assert len(root.get_descendants()) == 1
        assert root.get_descendants()[0].get_label() == "age"
        self._assert_output_nodes(tpq, root, root)
        assert root.get_output_roles() == frozenset({"u1", "u2"})

    def test_transform_with_and_parent_then_ancestor_predicates(self):
        expression = "self[?parent[(lab = parent_node)] & ?ancestor[(lab = ancestor_node)]]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "ancestor_node"
        assert len(root.get_descendants()) == 1
        parent = root.get_descendants()[0]
        assert parent.get_label() == "parent_node"
        assert len(parent.get_children()) == 1
        output = parent.get_children()[0]
        assert output.get_label() == "*"
        self._assert_output_nodes(tpq, output, output)
        assert output.get_output_roles() == frozenset({"u1", "u2"})

    def test_transform_with_and_ancestor_then_parent_predicates(self):
        expression = "self[?ancestor[(lab = ancestor_node)] & ?parent[(lab = parent_node)]]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "ancestor_node"
        assert len(root.get_descendants()) == 1
        parent = root.get_descendants()[0]
        assert parent.get_label() == "parent_node"
        assert len(parent.get_children()) == 1
        output = parent.get_children()[0]
        assert output.get_label() == "*"
        self._assert_output_nodes(tpq, output, output)
        assert output.get_output_roles() == frozenset({"u1", "u2"})

    def test_transform_with_path_composition_applies_right_path_to_left_path(self):
        expression = "child[(lab = c)]/parent[(lab = p)]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "p"
        assert len(root.get_children()) == 1
        assert root.get_children()[0].get_label() == "c"
        assert root.get_descendants() == []
        self._assert_output_nodes(tpq, root, root.get_children()[0])
        assert root.get_output_roles() == frozenset({"u1"})
        assert root.get_children()[0].get_output_roles() == frozenset({"u2"})

    def test_transform_with_path_composition_child_then_child(self):
        expression = "child[(lab = c)]/child[(lab = d)]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "*"
        assert len(root.get_children()) == 1
        left = root.get_children()[0]
        assert left.get_label() == "c"
        assert len(left.get_children()) == 1
        right = left.get_children()[0]
        assert right.get_label() == "d"
        assert root.get_descendants() == []
        self._assert_output_nodes(tpq, root, right)
        assert root.get_output_roles() == frozenset({"u1"})
        assert right.get_output_roles() == frozenset({"u2"})

    def test_transform_with_path_composition_child_then_child_keeps_u1_on_start_node(self):
        expression = "child[(lab = d)]/child[(lab = a)]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "*"
        assert len(root.get_children()) == 1
        first = root.get_children()[0]
        assert first.get_label() == "d"
        assert len(first.get_children()) == 1
        second = first.get_children()[0]
        assert second.get_label() == "a"
        assert root.get_descendants() == []
        self._assert_output_nodes(tpq, root, second)
        assert root.get_output_roles() == frozenset({"u1"})
        assert second.get_output_roles() == frozenset({"u2"})

    def test_transform_preserves_left_output_node_through_ancestor_and_composition(self):
        expression = "(self[(lab = *)&?descendant[(lab = c)]&?ancestor[(lab = a)&?child[(lab = b)&?child[(lab = c)]]&?descendant[(lab = e)]]]/child[(lab = d)])"

        tpq = self._transform(expression)
        root = tpq.get_root()
        u1, u2 = tpq.get_output_nodes()

        assert root.get_label() == "a"
        assert u1 is not None and u1.get_label() == "*"
        assert u2 is not None and u2.get_label() == "d"
        assert tpq.get_output_nodes()[0] is u1
        assert tpq.get_output_nodes()[1] is u2

