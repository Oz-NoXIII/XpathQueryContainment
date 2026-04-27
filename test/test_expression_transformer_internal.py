from unittest import TestCase

from controller.expression_transformer import ExpressionTransformer
from model.query_node import QueryNode


class TestExpressionTransformerInternalMethods(TestCase):
    def setUp(self):
        self.transformer = ExpressionTransformer()

    def test_detach_from_parent_handles_child_and_descendant_edges(self):
        parent = QueryNode("parent")
        child = QueryNode("child")
        parent.add_child(child)

        self.transformer._detach_from_parent(child)
        assert child.get_parent() is None
        assert parent.get_children() == []

        ancestor = QueryNode("ancestor")
        descendant = QueryNode("descendant")
        ancestor.add_descendant(descendant)

        self.transformer._detach_from_parent(descendant)
        assert descendant.get_parent() is None
        assert ancestor.get_descendants() == []

    def test_find_root_returns_topmost_ancestor(self):
        root = QueryNode("root")
        middle = QueryNode("middle")
        leaf = QueryNode("leaf")

        root.add_child(middle)
        middle.add_descendant(leaf)

        assert self.transformer._find_root(leaf) is root

    def test_merge_labels_supports_wildcards_and_rejects_conflicts(self):
        target = QueryNode("*")
        source = QueryNode("person")

        self.transformer._merge_labels(target, source)
        assert target.get_label() == "person"

        same_target = QueryNode("person")
        wildcard_source = QueryNode("*")
        self.transformer._merge_labels(same_target, wildcard_source)
        assert same_target.get_label() == "person"

        with self.assertRaises(SyntaxError):
            self.transformer._merge_labels(QueryNode("person"), QueryNode("book"))

    def test_labels_are_compatible(self):
        assert self.transformer._labels_are_compatible(QueryNode("*"), QueryNode("book"))
        assert self.transformer._labels_are_compatible(QueryNode("book"), QueryNode("*"))
        assert self.transformer._labels_are_compatible(QueryNode("book"), QueryNode("book"))
        assert not self.transformer._labels_are_compatible(QueryNode("book"), QueryNode("author"))

    def test_find_compatible_ancestor_returns_first_match(self):
        root = QueryNode("company")
        parent = QueryNode("department")
        node = QueryNode("employee")
        root.add_descendant(parent)
        parent.add_child(node)

        found = self.transformer._find_compatible_ancestor(node.get_parent(), QueryNode("*"))
        assert found is parent

        found_specific = self.transformer._find_compatible_ancestor(node.get_parent(), QueryNode("company"))
        assert found_specific is root

        missing = self.transformer._find_compatible_ancestor(node.get_parent(), QueryNode("project"))
        assert missing is None

    def test_attach_via_edge_adds_expected_relationship_and_validates_edge(self):
        parent = QueryNode("parent")
        child = QueryNode("child")
        descendant = QueryNode("descendant")

        self.transformer._attach_via_edge(parent, "child", child)
        self.transformer._attach_via_edge(parent, "descendant", descendant)

        assert parent.get_children() == [child]
        assert parent.get_descendants() == [descendant]

        with self.assertRaises(SyntaxError):
            self.transformer._attach_via_edge(QueryNode("x"), "invalid", QueryNode("y"))

    def test_merge_node_content_merges_labels_and_moves_edges(self):
        target = QueryNode("*")
        source = QueryNode("person")

        source_child = QueryNode("name")
        source_descendant = QueryNode("age")
        source.add_child(source_child)
        source.add_descendant(source_descendant)

        merged = self.transformer._merge_node_content(target, source)

        assert merged is target
        assert target.get_label() == "person"
        assert target.get_children() == [source_child]
        assert target.get_descendants() == [source_descendant]
        assert source.get_children() == []
        assert source.get_descendants() == []

    def test_merge_node_content_returns_same_node_for_self_merge(self):
        node = QueryNode("person")
        assert self.transformer._merge_node_content(node, node) is node

    def test_attach_step_child_descendant_and_self(self):
        pivot = QueryNode("*")

        child_node = QueryNode("name")
        root = self.transformer._attach_step(pivot, "child", child_node)
        assert root is pivot
        assert pivot.get_children() == [child_node]

        descendant_node = QueryNode("age")
        root = self.transformer._attach_step(pivot, "descendant", descendant_node)
        assert root is pivot
        assert pivot.get_descendants() == [descendant_node]

        self_node = QueryNode("person")
        root = self.transformer._attach_step(pivot, "self", self_node)
        assert root is pivot
        assert pivot.get_label() == "person"

    def test_attach_step_parent_without_parent_wraps_pivot(self):
        pivot = QueryNode("pivot")
        step_node = QueryNode("parent")

        root = self.transformer._attach_step(pivot, "parent", step_node)

        assert root is step_node
        assert step_node.get_children() == [pivot]

    def test_attach_step_parent_with_direct_parent_merges_label_on_parent(self):
        parent = QueryNode("*")
        pivot = QueryNode("pivot")
        parent.add_child(pivot)

        root = self.transformer._attach_step(pivot, "parent", QueryNode("department"))

        assert root is parent
        assert parent.get_label() == "department"
        assert parent.get_children() == [pivot]

    def test_attach_step_parent_with_ancestor_parent_inserts_between(self):
        ancestor = QueryNode("ancestor")
        pivot = QueryNode("pivot")
        ancestor.add_descendant(pivot)
        step_node = QueryNode("parent")

        root = self.transformer._attach_step(pivot, "parent", step_node)

        assert root is ancestor
        assert ancestor.get_descendants() == [step_node]
        assert step_node.get_children() == [pivot]

    def test_attach_step_ancestor_without_parent_wraps_pivot(self):
        pivot = QueryNode("pivot")
        step_node = QueryNode("ancestor")

        root = self.transformer._attach_step(pivot, "ancestor", step_node)

        assert root is step_node
        assert step_node.get_descendants() == [pivot]

    def test_attach_step_ancestor_reuses_compatible_ancestor(self):
        ancestor = QueryNode("department")
        pivot = QueryNode("employee")
        ancestor.add_child(pivot)

        root = self.transformer._attach_step(pivot, "ancestor", QueryNode("department"))

        assert root is ancestor
        assert ancestor.get_children() == [pivot]

    def test_attach_step_ancestor_with_descendant_edge_and_no_compatible_witness_raises(self):
        witness = QueryNode("witness")
        pivot = QueryNode("pivot")
        witness.add_descendant(pivot)

        with self.assertRaises(SyntaxError):
            self.transformer._attach_step(pivot, "ancestor", QueryNode("missing"))

    def test_attach_step_ancestor_with_direct_parent_inserts_new_ancestor(self):
        grand_parent = QueryNode("grand")
        parent = QueryNode("parent")
        pivot = QueryNode("pivot")
        grand_parent.add_child(parent)
        parent.add_child(pivot)

        step_node = QueryNode("ancestor")
        root = self.transformer._attach_step(pivot, "ancestor", step_node)

        assert root is grand_parent
        assert grand_parent.get_children() == [step_node]
        assert step_node.get_descendants() == [parent]
        assert parent.get_children() == [pivot]

    def test_attach_step_rejects_unknown_axis(self):
        with self.assertRaises(SyntaxError):
            self.transformer._attach_step(QueryNode("pivot"), "sibling", QueryNode("x"))

