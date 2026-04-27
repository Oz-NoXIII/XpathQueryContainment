from lark import Transformer, v_args

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery


class ExpressionTransformer(Transformer):
    """Build a TreePatternQuery directly from grammar alias methods."""

    def transform(self, tree):
        """Transform a Lark parse tree into a TreePatternQuery."""
        result = super().transform(tree)
        if isinstance(result, QueryNode):
            root = result
        else:
            raise NotImplementedError(f"Unsupported root expression type: {type(result).__name__}")

        tpq = TreePatternQuery(root)
        tpq.set_nodes()
        return tpq

    @v_args(inline=True)
    def pe(self, args):
        if args[0]== "self":
            return args[1]
        elif args[0]== "child":
            node = QueryNode("*")
            node.add_child(args[1])
            return node
        elif args[0]== "descendant":
            node = QueryNode("*")
            node.add_descendant(args[1])
            return node
        elif args[0]== "parent":
            node = QueryNode("*")
            args[1].add_child(node)
            return args[1]
        elif args[0]== "ancestor":
            node = QueryNode("*")
            args[1].add_descendant(node)
            return args[1]
        return None

    @v_args(inline=True)
    def pe_compose(self, left, right):
        """XPath compose is out of scope for this transformer."""
        raise NotImplementedError("compose '/' is not supported by the TPQ transformer")

    @v_args(inline=True)
    def pe_union(self, _left, _right):
        """XPath union is out of scope for this transformer."""
        raise NotImplementedError("Union 'U' is not supported by the TPQ transformer")

    def step(self, args):
        if isinstance(args[0], str):
            axis = args[0]
            node = args[1]

            return [axis, node]
        else:
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
        """TODO"""
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
        """Attach one step constraint around the pivot and return the fragment root."""
        root = self._find_root(pivot)

        if axis == "child":
            pivot.add_child(step_node)
            return root

        if axis == "descendant":
            pivot.add_descendant(step_node)
            return root

        if axis == "self":
            self._merge_node_content(pivot, step_node)
            return root

        if axis == "parent":
            if pivot.get_parent() is None:
                step_node.add_child(pivot)
                return self._find_root(step_node)

            parent = pivot.get_parent()
            if pivot.parent_edge == "child":
                self._merge_node_content(parent, step_node)
                return self._find_root(parent)

            # Existing ancestor constraint + new parent constraint: insert between parent and pivot.
            self._detach_from_parent(pivot)
            parent.add_descendant(step_node)
            step_node.add_child(pivot)
            return self._find_root(parent)

        if axis == "ancestor":
            if pivot.get_parent() is None:
                step_node.add_descendant(pivot)
                return self._find_root(step_node)

            parent = pivot.get_parent()
            is_direct_parent = pivot.parent_edge == "child"
            is_ancestor_witness = pivot.parent_edge == "descendant"
            if not (is_direct_parent or is_ancestor_witness):
                raise SyntaxError(f"Unsupported parent edge for ancestor axis: {pivot.parent_edge}")

            compatible_ancestor = self._find_compatible_ancestor(parent, step_node)
            if compatible_ancestor is not None:
                # Reuse an existing ancestor witness (parent or higher ancestor) when labels allow it.
                self._merge_node_content(compatible_ancestor, step_node)
                return self._find_root(compatible_ancestor)

            if is_ancestor_witness:
                raise SyntaxError(
                    "AND between ancestor constraints requires a compatible ancestor witness"
                )

            # No reusable witness found and the parent is a direct child: insert ancestor => parent => pivot.
            grand_parent = parent.get_parent()
            parent_edge = parent.parent_edge
            self._detach_from_parent(parent)
            step_node.add_descendant(parent)

            if grand_parent is not None:
                self._attach_via_edge(grand_parent, parent_edge, step_node)
                return self._find_root(grand_parent)

            return self._find_root(step_node)

        raise SyntaxError(f"Unsupported axis in AND expression: {axis}")
