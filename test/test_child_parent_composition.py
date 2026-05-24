"""Test to verify child/parent composition behavior and clarify user's concern."""
from unittest import TestCase
from controller.xpath_parser import XPathParser
from controller.expression_transformer import ExpressionTransformer


class TestChildParentComposition(TestCase):
    def setUp(self):
        self.parser = XPathParser()
        self.transformer = ExpressionTransformer()

    def _transform(self, expression):
        """Parse and transform an XPath expression into a TreePatternQuery."""
        tree = self.parser.parse(expression)
        return self.transformer.transform(tree)

    def test_child_parent_composition_assigns_correct_outputs(self):
        """Test that child/parent composition correctly assigns u1 to parent and u2 to child.

        For  `child[(lab = author)]/parent[(lab = post)]`:
        - The pattern describes: a post node that has an author child
        - u1 (first output): should be post
        - u2 (second output): should be post
        """
        expression = "child[(lab = author)]/parent[(lab = post)]"
        tpq = self._transform(expression)

        # Structure check
        root = tpq.get_root()
        self.assertEqual(root.get_label(), "post", "Root should be 'post'")
        self.assertEqual(len(root.get_children()), 1, "Root should have one child")
        self.assertEqual(root.get_children()[0].get_label(), "author", "Child should be 'author'")

        # Output check
        u1, u2 = tpq.get_output_nodes()
        self.assertIsNotNone(u1, "u1 should not be None")
        self.assertIsNotNone(u2, "u2 should not be None")
        self.assertEqual(u1.get_label(), "post", "u1 should be 'post'")
        self.assertEqual(u2.get_label(), "post", "u2 should be 'author'")
        self.assertIs(u1, u2, "u1 and u2 should be the same node")

        # Role check (this is what appears on the visualization)
        self.assertEqual(root.get_output_roles(), frozenset({"u1", "u2"}), "post should have u1 and u2 role")
        self.assertEqual(root.get_children()[0].get_output_roles(), frozenset(), "author should have no role")

    def test_matches_existing_test_semantics(self):
        """Verify our test matches the existing test semantics for similar expression."""
        # Test from test_expression_transformer.py line 220
        expression_test = "child[(lab = c)]/parent[(lab = p)]"
        tpq_test = self._transform(expression_test)

        root_test = tpq_test.get_root()
        self.assertEqual(root_test.get_label(), "p")
        self.assertEqual(root_test.get_children()[0].get_label(), "c")
        self.assertEqual(root_test.get_output_roles(), frozenset({"u1", "u2"}), "post should have u1 and u2 role")
        self.assertEqual(root_test.get_children()[0].get_output_roles(), frozenset(), "author should have no role")

        # Our test should have the same pattern
        expression_ours = "child[(lab = author)]/parent[(lab = post)]"
        tpq_ours = self._transform(expression_ours)

        root_ours = tpq_ours.get_root()
        self.assertEqual(root_ours.get_label(), "post")
        self.assertEqual(root_ours.get_children()[0].get_label(), "author")
        self.assertEqual(root_ours.get_output_roles(), frozenset({"u1", "u2"}), "post should have u1 and u2 role")
        self.assertEqual(root_ours.get_children()[0].get_output_roles(), frozenset(), "author should have no role")

