from lark import Transformer, v_args

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery


class PathFragment:
    """Binary path fragment: tree root, current frontier, and entry step."""

    def __init__(self, root, frontier, entry_axis, entry_node):
        self.root = root
        self.frontier = frontier
        self.entry_axis = entry_axis
        self.entry_node = entry_node


# noinspection PyMethodMayBeStatic
class ExpressionTransformer(Transformer):
    """Build a TreePatternQuery directly from grammar alias methods."""

    def transform(self, tree):
        """Transform a Lark parse tree into a TreePatternQuery."""
        result = super().transform(tree)
        if isinstance(result, PathFragment):
            result = result.root
        if isinstance(result, list):
            result = self._materialize_step_fragment(result).root
        if isinstance(result, QueryNode):
            node = result
        else:
            raise NotImplementedError(f"Unsupported root expression type: {type(result).__name__}")

        # Ensure we use the true root of the tree, not just the returned node
        root = self._find_root(node)
        tpq = TreePatternQuery(root)
        tpq.set_nodes()
        return tpq

    def pe(self, args):
        if isinstance(args, list) and len(args) == 1:
            args = args[0]

        if isinstance(args, PathFragment):
            return args

        if isinstance(args, QueryNode):
            return PathFragment(args, args, "self", args)

        if self._is_step_fragment(args):
            return args

        raise NotImplementedError(f"Unsupported pe operands: {type(args).__name__}")

    @v_args(inline=True)
    def pe_compose(self, left, right):
        """Compose two path fragments by applying the right path to the left path."""
        left_fragment = self._materialize_fragment(left)
        right_fragment = self._materialize_fragment(right)

        # The right fragment is materialized as its own standalone mini-tree.
        # Before reusing its entry node in the composed path, detach it from that
        # temporary root so the node can be reattached under the left frontier.
        if right_fragment.entry_node.get_parent() is not None:
            self._detach_from_parent(right_fragment.entry_node)

        root, frontier = self._attach_step_with_frontier(
            left_fragment.frontier, right_fragment.entry_axis, right_fragment.entry_node
        )
        return PathFragment(root, frontier, left_fragment.entry_axis, left_fragment.entry_node)

    @v_args(inline=True)
    def pe_union(self, _left, _right):
        """XPath union is out of scope for this transformer."""
        raise NotImplementedError("Union 'U' is not supported by the TPQ transformer")

    def step(self, args):
        if len(args) == 2 and isinstance(args[0], str):
            return [args[0], args[1]]
        if len(args) == 1 and isinstance(args[0], list) and len(args[0]) == 2:
            return args[0]
        raise NotImplementedError("Complex steps are not supported yet")


    def ne(self, args):
        """Node expression wrapper with restricted support."""
        if len(args) != 1:
            raise NotImplementedError("Complex node expressions are not supported yet")
        return args[0]

    @v_args(inline=True)
    def lab(self, token):
        """Return a detached QueryNode carrying a concrete label."""
        return QueryNode(str(token))

    def wildcard(self, _args):
        """Return a detached QueryNode carrying wildcard label."""
        return QueryNode("*")

    def axis_self(self, _args):
        return "self"

    def axis_child(self, _args):
        return "child"

    def axis_descendant(self, _args):
        return "descendant"

    def axis_parent(self, _args):
        return "parent"

    def axis_ancestor(self, _args):
        return "ancestor"

    def and_(self, args):
        left, right = args

        if isinstance(left, QueryNode) and isinstance(right, QueryNode):
            return self._merge_node_content(left, right)

        if isinstance(left, QueryNode) and isinstance(right, list):
            axis, step_node = right
            return self._attach_step(left, axis, step_node)

        if isinstance(left, list) and isinstance(right, QueryNode):
            axis, step_node = left
            return self._attach_step(right, axis, step_node)

        if isinstance(left, list) and isinstance(right, list):
            pivot = QueryNode("*")
            axis_left, node_left = left
            axis_right, node_right = right

            self._attach_step(pivot, axis_left, node_left)
            return self._attach_step(pivot, axis_right, node_right)

        raise SyntaxError("Unsupported operands for AND expression")

    def or_(self, _args):
        """Boolean OR is out of scope."""
        raise NotImplementedError("OR in node expressions is not supported by the TPQ transformer")

    def not_(self, _args):
        """Boolean NOT is out of scope."""
        raise NotImplementedError("NOT in node expressions is not supported by the TPQ transformer")

    def _detach_from_parent(self, node):
        parent = node.get_parent()
        if parent is None:
            return

        if node.parent_edge == "child":
            parent.remove_child(node)
        elif node.parent_edge == "descendant":
            parent.remove_descendant(node)

    def _find_root(self, node):
        current = node
        while current.get_parent() is not None:
            current = current.get_parent()
        return current

    def _merge_labels(self, target, source):
        target_label = target.get_label()
        source_label = source.get_label()

        if target_label == "*":
            target.set_label(source_label)
            return
        if source_label == "*" or target_label == source_label:
            return

        raise SyntaxError(
            "AND between two nodes with concrete labels is not supported by the TPQ transformer"
        )

    def _labels_are_compatible(self, left_node, right_node):
        left = left_node.get_label()
        right = right_node.get_label()
        return left == "*" or right == "*" or left == right

    def _find_compatible_ancestor(
        self, start_node: QueryNode | None, constraint_node: QueryNode
    ) -> QueryNode | None:
        """Return the first ancestor that can satisfy the incoming node label constraint."""
        current = start_node
        while current is not None:
            if self._labels_are_compatible(current, constraint_node):
                return current
            current = current.get_parent()
        return None

    def _attach_via_edge(self, parent, edge, child):
        if edge == "child":
            parent.add_child(child)
        elif edge == "descendant":
            parent.add_descendant(child)
        else:
            raise SyntaxError(f"Unsupported edge type while rewiring: {edge}")

    def _is_step_fragment(self, fragment):
        return (
            isinstance(fragment, list)
            and len(fragment) == 2
            and isinstance(fragment[0], str)
            and isinstance(fragment[1], QueryNode)
        )

    def _materialize_step_fragment(self, step):
        axis, node = step

        if axis == "self":
            return PathFragment(node, node, axis, node)

        if axis == "child":
            root = QueryNode("*")
            root.add_child(node)
            return PathFragment(root, node, axis, node)

        if axis == "descendant":
            root = QueryNode("*")
            root.add_descendant(node)
            return PathFragment(root, node, axis, node)

        if axis == "parent":
            placeholder = QueryNode("*")
            node.add_child(placeholder)
            return PathFragment(node, placeholder, axis, node)

        if axis == "ancestor":
            placeholder = QueryNode("*")
            node.add_descendant(placeholder)
            return PathFragment(node, placeholder, axis, node)

        raise NotImplementedError(f"Unsupported axis in step fragment: {axis}")

    def _materialize_fragment(self, fragment):
        if isinstance(fragment, PathFragment):
            return fragment
        if isinstance(fragment, list):
            return self._materialize_step_fragment(fragment)
        if isinstance(fragment, QueryNode):
            return PathFragment(fragment, fragment, "self", fragment)
        raise SyntaxError(f"Unsupported fragment type: {type(fragment).__name__}")

    def _attach_step_with_frontier(self, pivot, axis, step_node):
        """Attach one step and return both the fragment root and the new frontier node."""
        root = self._find_root(pivot)

        if axis == "child":
            pivot.add_child(step_node)
            return root, step_node

        if axis == "descendant":
            pivot.add_descendant(step_node)
            return root, step_node

        if axis == "self":
            self._merge_node_content(pivot, step_node)
            return root, pivot

        if axis == "parent":
            for child in list(step_node.get_children()):
                if child.get_label() == "*" and not child.get_children() and not child.get_descendants():
                    step_node.remove_child(child)
                    break

            if pivot.get_parent() is None:
                step_node.add_child(pivot)
                return self._find_root(step_node), pivot

            parent = pivot.get_parent()
            if pivot.parent_edge == "child":
                self._merge_node_content(parent, step_node)
                return self._find_root(parent), pivot

            self._detach_from_parent(pivot)
            parent.add_descendant(step_node)
            step_node.add_child(pivot)
            return self._find_root(parent), pivot

        if axis == "ancestor":
            for descendant in list(step_node.get_descendants()):
                if descendant.get_label() == "*" and not descendant.get_children() and not descendant.get_descendants():
                    step_node.remove_descendant(descendant)
                    break

            if pivot.get_parent() is None:
                step_node.add_descendant(pivot)
                return self._find_root(step_node), pivot

            parent = pivot.get_parent()
            is_direct_parent = pivot.parent_edge == "child"
            is_ancestor_witness = pivot.parent_edge == "descendant"
            if not (is_direct_parent or is_ancestor_witness):
                raise SyntaxError(f"Unsupported parent edge for ancestor axis: {pivot.parent_edge}")

            compatible_ancestor = self._find_compatible_ancestor(parent, step_node)
            if compatible_ancestor is not None:
                self._merge_node_content(compatible_ancestor, step_node)
                return self._find_root(compatible_ancestor), pivot

            if is_ancestor_witness:
                raise SyntaxError(
                    "AND between ancestor constraints requires a compatible ancestor witness"
                )

            grand_parent = parent.get_parent()
            parent_edge = parent.parent_edge
            self._detach_from_parent(parent)
            step_node.add_descendant(parent)

            if grand_parent is not None:
                self._attach_via_edge(grand_parent, parent_edge, step_node)
                return self._find_root(grand_parent), pivot

            return self._find_root(step_node), pivot

        raise SyntaxError(f"Unsupported axis in AND expression: {axis}")


    def _merge_node_content(self, target, source):
        """Move source constraints into target and fuse labels."""
        if target is source:
            return target

        self._merge_labels(target, source)

        for child in list(source.get_children()):
            source.remove_child(child)
            target.add_child(child)

        for descendant in list(source.get_descendants()):
            source.remove_descendant(descendant)
            target.add_descendant(descendant)

        return target

    def _attach_step(self, pivot, axis, step_node):
        """Attach one-step constraint around the pivot and return the pivot (frontier).

        This method modifies the tree structure in-place by attaching the step_node
        relative to the pivot. The tree topology may change (e.g., ancestors may be
        added above the pivot), but the pivot itself remains the node on which the
        constraint is applied and should be returned to callers.
        """
        self._attach_step_with_frontier(pivot, axis, step_node)
        return pivot


