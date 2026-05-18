from unittest import TestCase
from controller.xpath_parser import XPathParser
from controller.expression_transformer import ExpressionTransformer


class TestPredicateAttachment(TestCase):
    def setUp(self):
        self.parser = XPathParser()
        self.transformer = ExpressionTransformer()

    def test_child_post_with_existential_child_attaches_under_post(self):
        expression = "child[(lab = post)][?child[(lab = comment)]]"
        tree = self.parser.parse(expression)
        tpq = self.transformer.transform(tree)

        root = tpq.get_root()
        # root should be a wildcard that has 'post' as its child
        self.assertEqual(root.get_label(), "*")
        children = root.get_children()
        self.assertEqual(len(children), 1)
        post = children[0]
        self.assertEqual(post.get_label(), "post")

        # post should have a child 'comment' attached by the existential predicate
        post_children = post.get_children()
        self.assertEqual(len(post_children), 1)
        comment = post_children[0]
        self.assertEqual(comment.get_label(), "comment")

        # Output roles: root u1, post u2, comment none
        u1, u2 = tpq.get_output_nodes()
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u2)
        self.assertEqual(u1.get_label(), root.get_label())
        self.assertEqual(u2.get_label(), post.get_label())
        self.assertEqual(root.get_output_roles(), frozenset({"u1"}))
        self.assertEqual(post.get_output_roles(), frozenset({"u2"}))
        self.assertEqual(comment.get_output_roles(), frozenset())


class TestParentAncestorOutputs(TestCase):
    """Tests for parent and ancestor axis output node semantics."""

    def setUp(self):
        self.parser = XPathParser()
        self.transformer = ExpressionTransformer()

    def test_parent_axis_standalone_outputs_u1_placeholder_u2_parent(self):
        """For parent[(lab = X)], u1 should be placeholder (*), u2 should be X."""
        expression = "parent[(lab = post)]"
        tree = self.parser.parse(expression)
        tpq = self.transformer.transform(tree)

        root = tpq.get_root()
        self.assertEqual(root.get_label(), "post")

        placeholder = root.get_children()[0]
        self.assertEqual(placeholder.get_label(), "*")

        u1, u2 = tpq.get_output_nodes()
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u2)
        # u1 should be the placeholder (initial unnamed witness)
        self.assertEqual(u1.get_label(), "*")
        # u2 should be the parent (post)
        self.assertEqual(u2.get_label(), "post")
        self.assertEqual(u1, placeholder)
        self.assertEqual(u2, root)

    def test_ancestor_axis_standalone_outputs_u1_placeholder_u2_ancestor(self):
        """For ancestor[(lab = X)], u1 should be placeholder (*), u2 should be X."""
        expression = "ancestor[(lab = ancestor_node)]"
        tree = self.parser.parse(expression)
        tpq = self.transformer.transform(tree)

        root = tpq.get_root()
        self.assertEqual(root.get_label(), "ancestor_node")

        placeholder = root.get_descendants()[0]
        self.assertEqual(placeholder.get_label(), "*")

        u1, u2 = tpq.get_output_nodes()
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u2)
        # u1 should be the placeholder (initial unnamed witness)
        self.assertEqual(u1.get_label(), "*")
        # u2 should be the ancestor (ancestor_node)
        self.assertEqual(u2.get_label(), "ancestor_node")
        self.assertEqual(u1, placeholder)
        self.assertEqual(u2, root)

    def test_child_parent_composition_both_outputs_on_parent(self):
        """For child[...]/parent[...], both u1 and u2 should be on the parent node."""
        expression = "child[(lab = author)]/parent[(lab = post)]"
        tree = self.parser.parse(expression)
        tpq = self.transformer.transform(tree)

        root = tpq.get_root()
        # Root should be 'post' (parent navigated to)
        self.assertEqual(root.get_label(), "post")

        # Post should have 'author' as child
        author = root.get_children()[0]
        self.assertEqual(author.get_label(), "author")

        u1, u2 = tpq.get_output_nodes()
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u2)
        # Both u1 and u2 should point to 'post' (the parent)
        self.assertEqual(u1.get_label(), "post")
        self.assertEqual(u2.get_label(), "post")
        self.assertIs(u1, root)
        self.assertIs(u2, root)

        # Verify output roles
        self.assertEqual(root.get_output_roles(), frozenset({"u1", "u2"}))
        self.assertEqual(author.get_output_roles(), frozenset())



