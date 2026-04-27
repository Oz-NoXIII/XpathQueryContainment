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
            #TODO: root.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[1])
        root = tpq.get_root()
        with self.subTest(expression=expressions[1]):
            assert root.get_label() == "person"
            assert root.get_children() == []
            assert root.get_descendants() == []
            #TODO: root.output_node should be True, but this is not yet implemented in the transformer


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
            #TODO: root.output_node and child.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[1])
        root = tpq.get_root()
        descendants = root.get_descendants()
        descendant = descendants[0]
        with self.subTest(expression=expressions[1]):
            assert root.get_label() == "*"
            assert root.get_children() == []
            assert len(descendants) == 1
            assert descendant.get_label() == "*"
            #TODO: root.output_node and descendant.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[2])
        root = tpq.get_root()
        children = root.get_children()
        child = children[0]
        with self.subTest(expression=expressions[2]):
            assert root.get_label() == "*"
            assert len(children) == 1
            assert child.get_label() == "*"
            assert root.get_descendants() == []
            # TODO: child.output_node and root.output_node should be True, but this is not yet implemented in the transformer

        tpq = self._transform(expressions[3])
        root = tpq.get_root()
        descendants = root.get_descendants()
        descendant = descendants[0]
        with self.subTest(expression=expressions[3]):
            assert root.get_label() == "*"
            assert root.get_children() == []
            assert len(descendants) == 1
            assert descendant.get_label() == "*"
            # TODO: descendant.output_node and root.output_node should be True, but this is not yet implemented in the transformer

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
            # TODO: root.output_node should be True, but this is not yet implemented in the transformer

    def test_transform_with_and_between_two_step_predicates(self):
        expression = "self[?child[(lab = name)] & ?descendant[(lab = age)]]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "*"
        assert len(root.get_children()) == 1
        assert root.get_children()[0].get_label() == "name"
        assert len(root.get_descendants()) == 1
        assert root.get_descendants()[0].get_label() == "age"

    def test_transform_with_and_parent_then_ancestor_predicates(self):
        expression = "self[?parent[(lab = parent_node)] & ?ancestor[(lab = ancestor_node)]]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "ancestor_node"
        assert len(root.get_descendants()) == 1
        parent = root.get_descendants()[0]
        assert parent.get_label() == "parent_node"
        assert len(parent.get_children()) == 1
        assert parent.get_children()[0].get_label() == "*"

    def test_transform_with_and_ancestor_then_parent_predicates(self):
        expression = "self[?ancestor[(lab = ancestor_node)] & ?parent[(lab = parent_node)]]"

        tpq = self._transform(expression)
        root = tpq.get_root()

        assert root.get_label() == "ancestor_node"
        assert len(root.get_descendants()) == 1
        parent = root.get_descendants()[0]
        assert parent.get_label() == "parent_node"
        assert len(parent.get_children()) == 1
        assert parent.get_children()[0].get_label() == "*"
