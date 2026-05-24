from lark import Transformer, v_args

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery


class PathFragment:
    """Binary path fragment: tree root, current frontier, and entry step."""

    def __init__(self, root, frontier, entry_axis, entry_node, output_u1=None, output_u2=None):
        self.root = root
        self.frontier = frontier
        self.entry_axis = entry_axis
        self.entry_node = entry_node
        self.output_u1 = root if output_u1 is None else output_u1
        self.output_u2 = frontier if output_u2 is None else output_u2


# noinspection PyMethodMayBeStatic
class ExpressionTransformer(Transformer):
    """Build a TreePatternQuery directly from grammar alias methods."""

    def transform(self, tree):
        """Transform a Lark parse tree into a TreePatternQuery."""
        result = super().transform(tree)
        # Handle unary root query: ["?", content]
        if isinstance(result, list) and len(result) == 2 and result[0] == "?":
            content = result[1]
            if isinstance(content, PathFragment):
                node = content.root
                output_u1 = content.output_u1
                output_u2 = None  # Unary: no u2
            else:
                frag = self._materialize_fragment(content)
                node = frag.root
                output_u1 = frag.output_u1
                output_u2 = None  # Unary: no u2
        # ...existing code...
        elif isinstance(result, PathFragment):
            node = result.root
            output_u1 = result.output_u1
            output_u2 = result.output_u2
        elif isinstance(result, list) and not (len(result) == 2 and result[0] == "?"):
            result = self._materialize_step_fragment(result)
            node = result.root
            output_u1 = result.output_u1
            output_u2 = result.output_u2
        elif isinstance(result, QueryNode):
            node = result
            output_u1 = node
            output_u2 = node
        else:
            raise NotImplementedError(f"Unsupported root expression type: {type(result).__name__}")

        # Ensure we use the true root of the tree, not just the returned node
        root = self._find_root(node)
        tpq = TreePatternQuery(root)
        tpq.set_output_nodes(output_u1, output_u2)
        tpq.set_nodes()
        return tpq

    def pe(self, args):
        if isinstance(args, list) and len(args) == 1:
            args = args[0]

        # Handle unary predicate query: ["?", pe] should have output_u2 = None
        if isinstance(args, list) and len(args) == 2 and args[0] == "?":
            content = args[1]
            fragment = self._materialize_fragment(content)
            # Return a unary fragment with no u2 output
            return PathFragment(fragment.root, fragment.frontier, fragment.entry_axis, fragment.entry_node, fragment.output_u1, None)

        if isinstance(args, PathFragment):
            return args

        if isinstance(args, QueryNode):
            return PathFragment(args, args, "self", args, args, args)

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
        # Preserve the original u1 witness node through rewiring; it should keep
        # pointing to the same node object even if that node is moved higher.
        # However, when the right path involves parent/ancestor axes, the tree root
        # may change. In such cases, update output_u1 to the new root.
        output_u1 = left_fragment.output_u1

        # If the root changed (e.g., due to parent or ancestor navigation),
        # and the left output points to a wildcard that was created for the left path,
        # update output_u1 to point to the new root instead.
        if right_fragment.entry_axis in ("parent", "ancestor") and root != self._find_root(left_fragment.root):
            if isinstance(output_u1, QueryNode) and output_u1.get_label() == "*":
                output_u1 = root

        # Determine the composed fragment's u2 output. Normally u2 follows the
        # new frontier (the pivot after attachment). However, when the right path
        # moves the root upward (parent/ancestor), the semantic composition means
        # the witness nodes (u1 and u2) can coincide on the new root. In that
        # scenario place u2 on the new root as well so both outputs refer to the
        # same logical node (e.g., child[...] / parent[...] -> both u1/u2 on parent).
        output_u2 = frontier
        if right_fragment.entry_axis in ("parent", "ancestor"):
            output_u2 = root

        return PathFragment(root, frontier, left_fragment.entry_axis, left_fragment.entry_node, output_u1, output_u2)

    @v_args(inline=True)
    def pe_union(self, _left, _right):
        """XPath union is out of scope for this transformer."""
        raise NotImplementedError("Union 'U' is not supported by the TPQ transformer")

    def step(self, args):
        # Basic axis form: axis/? and a node/predicate
        if len(args) == 2 and isinstance(args[0], str):
            return [args[0], args[1]]

        # If the step is already materialized as a two-element fragment, pass it through
        if len(args) == 1 and isinstance(args[0], list) and len(args[0]) == 2:
            return args[0]

        # Complex step: support (step)[pred] where predicate may be
        # a plain QueryNode, a step fragment [axis, node], a PathFragment, or a
        # wrapped predicate of the form ['?', pe]. The parser calls functions
        # pairwise, so args will contain at most two elements here: inner and one
        # predicate.
        if len(args) == 2:
            inner = args[0]
            predicate = args[1]

            # Helper to unwrap predicate wrappers of the form ['?', content]
            if isinstance(predicate, list) and len(predicate) == 2 and predicate[0] == "?":
                predicate = predicate[1]

            # Case: inner is a step fragment (axis, node)
            if isinstance(inner, list) and len(inner) == 2 and isinstance(inner[0], str):
                inner_fragment = self._materialize_step_fragment(inner)
                pivot = inner_fragment.root
                axis, node = inner

                # Merge plain node predicate into the step node
                if isinstance(predicate, QueryNode):
                    self._merge_node_content(node, predicate)
                    return inner_fragment

                # Attach step-like predicate under the step's entry node (the actual
                # node selected by the inner step), not under the temporary root.
                # This makes predicates like child[(lab=post)][?child[(lab=comment)]]
                # attach the comment under the post node (entry node), which is the
                # expected XPath semantics.
                if isinstance(predicate, list) and len(predicate) == 2 and isinstance(predicate[0], str):
                    pred_axis, pred_node = predicate
                    self._attach_step(node, pred_axis, pred_node)
                    return inner_fragment

                # Materialize other fragment-like predicates (PathFragment or QueryNode)
                try:
                    pred_fragment = self._materialize_fragment(predicate)
                except Exception:
                    raise NotImplementedError("Unsupported predicate form in complex step")

                # Detach reused entry node if necessary before attaching
                if pred_fragment.entry_node.get_parent() is not None:
                    self._detach_from_parent(pred_fragment.entry_node)

                # Attach the predicate fragment under the entry node (the step node)
                self._attach_step(node, pred_fragment.entry_axis, pred_fragment.entry_node)
                return inner_fragment

            # Case: inner is a PathFragment (already materialized) with a predicate,
            # e.g. (pe)[pred]. We attach predicates to the fragment's pivot/root and
            # merge node predicates into the fragment entry node.
            if isinstance(inner, PathFragment):
                inner_fragment = inner
                pivot = inner_fragment.root
                node = inner_fragment.entry_node

                if isinstance(predicate, QueryNode):
                    self._merge_node_content(node, predicate)
                    return inner_fragment

                if isinstance(predicate, list) and len(predicate) == 2 and isinstance(predicate[0], str):
                    pred_axis, pred_node = predicate
                    self._attach_step(pivot, pred_axis, pred_node)
                    return inner_fragment

                try:
                    pred_fragment = self._materialize_fragment(predicate)
                except Exception:
                    raise NotImplementedError("Unsupported predicate form in complex step")

                if pred_fragment.entry_node.get_parent() is not None:
                    self._detach_from_parent(pred_fragment.entry_node)

                self._attach_step(pivot, pred_fragment.entry_axis, pred_fragment.entry_node)
                return inner_fragment

            # Case: inner is a plain QueryNode with a predicate, e.g. (node)[pred]
            if isinstance(inner, QueryNode):
                pivot = inner

                if isinstance(predicate, QueryNode):
                    self._merge_node_content(inner, predicate)
                    return pivot

                if isinstance(predicate, list) and len(predicate) == 2 and isinstance(predicate[0], str):
                    axis, step_node = predicate
                    self._attach_step(inner, axis, step_node)
                    return pivot

                try:
                    pred_fragment = self._materialize_fragment(predicate)
                except Exception:
                    raise NotImplementedError("Unsupported predicate form in complex step")

                if pred_fragment.entry_node.get_parent() is not None:
                    self._detach_from_parent(pred_fragment.entry_node)

                self._attach_step(inner, pred_fragment.entry_axis, pred_fragment.entry_node)
                return pivot

        raise NotImplementedError(f"step error:{args}")


    @v_args(inline=True)
    def ne_exist(self, pe):
        """Node expression wrapper. Wrap a path expression (pe) as an existential
        predicate of the form ["?", pe]. Using inline args keeps the inner
        representation simple for downstream handlers.
        """
        return ["?", pe]

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

        # Unwrap existential predicate wrapper ['?', content] if present
        def _unwrap(pred):
            if isinstance(pred, list) and len(pred) == 2 and pred[0] == "?":
                return pred[1]
            return pred

        left_u = _unwrap(left)
        right_u = _unwrap(right)

        # Classify operand into one of: QueryNode, step fragment [axis, node], or PathFragment
        def _classify(obj):
            if isinstance(obj, QueryNode):
                return "node", obj
            if isinstance(obj, PathFragment):
                return "fragment", obj
            if isinstance(obj, list) and len(obj) == 2 and isinstance(obj[0], str):
                return "step", obj
            raise SyntaxError("Unsupported operands for AND expression")

        left_kind, left_obj = _classify(left_u)
        right_kind, right_obj = _classify(right_u)

        # node & node => merge
        if left_kind == "node" and right_kind == "node":
            return self._merge_node_content(left_obj, right_obj)

        # node & step/fragment => attach predicate under the node pivot
        if left_kind == "node" and right_kind == "step":
            axis, step_node = right_obj
            return self._attach_step(left_obj, axis, step_node)

        if left_kind == "node" and right_kind == "fragment":
            frag = right_obj
            if frag.entry_node.get_parent() is not None:
                self._detach_from_parent(frag.entry_node)
            self._attach_step(left_obj, frag.entry_axis, frag.entry_node)
            return left_obj

        # step/fragment & node => attach under node pivot (symmetric)
        if left_kind == "step" and right_kind == "node":
            axis, step_node = left_obj
            return self._attach_step(right_obj, axis, step_node)

        if left_kind == "fragment" and right_kind == "node":
            frag = left_obj
            if frag.entry_node.get_parent() is not None:
                self._detach_from_parent(frag.entry_node)
            self._attach_step(right_obj, frag.entry_axis, frag.entry_node)
            return right_obj

        # step & step => attach both under a fresh pivot
        if left_kind == "step" and right_kind == "step":
            pivot = QueryNode("*")
            axis_left, node_left = left_obj
            axis_right, node_right = right_obj
            self._attach_step(pivot, axis_left, node_left)
            return self._attach_step(pivot, axis_right, node_right)

        # step & fragment or fragment & step => attach both under a fresh pivot
        if (left_kind == "step" and right_kind == "fragment") or (left_kind == "fragment" and right_kind == "step"):
            pivot = QueryNode("*")
            # attach left
            if left_kind == "step":
                axis_l, node_l = left_obj
                self._attach_step(pivot, axis_l, node_l)
            else:
                frag_l = left_obj
                if frag_l.entry_node.get_parent() is not None:
                    self._detach_from_parent(frag_l.entry_node)
                self._attach_step(pivot, frag_l.entry_axis, frag_l.entry_node)
            # attach right
            if right_kind == "step":
                axis_r, node_r = right_obj
                return self._attach_step(pivot, axis_r, node_r)
            else:
                frag_r = right_obj
                if frag_r.entry_node.get_parent() is not None:
                    self._detach_from_parent(frag_r.entry_node)
                return self._attach_step(pivot, frag_r.entry_axis, frag_r.entry_node)

        # fragment & fragment => attach both under a fresh pivot
        if left_kind == "fragment" and right_kind == "fragment":
            pivot = QueryNode("*")
            for frag in (left_obj, right_obj):
                if frag.entry_node.get_parent() is not None:
                    self._detach_from_parent(frag.entry_node)
                self._attach_step(pivot, frag.entry_axis, frag.entry_node)
            return pivot

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
        u2 = True
        if axis == "?":
            u2 = False
            axis, node = node

        if axis == "self":
            return PathFragment(node, node, axis, node, node, node if u2 else None)

        if axis == "child":
            root = QueryNode("*")
            root.add_child(node)
            return PathFragment(root, node, axis, node, root, node if u2 else None)

        if axis == "descendant":
            root = QueryNode("*")
            root.add_descendant(node)
            return PathFragment(root, node, axis, node, root, node if u2 else None)

        if axis == "parent":
            placeholder = QueryNode("*")
            node.add_child(placeholder)
            # For parent axis: u1 is the initial unnamed witness (placeholder),
            # u2 is the parent node we navigate to.
            return PathFragment(node, placeholder, axis, node, placeholder, node if u2 else None)

        if axis == "ancestor":
            placeholder = QueryNode("*")
            node.add_descendant(placeholder)
            # For ancestor axis: u1 is the initial unnamed witness (placeholder),
            # u2 is the ancestor node we navigate to.
            return PathFragment(node, placeholder, axis, node, placeholder, node if u2 else None)

        raise NotImplementedError(f"Unsupported axis in step fragment: {axis}")

    def _materialize_fragment(self, fragment):
        if isinstance(fragment, PathFragment):
            return fragment
        if isinstance(fragment, list):
            return self._materialize_step_fragment(fragment)
        if isinstance(fragment, QueryNode):
            return PathFragment(fragment, fragment, "self", fragment, fragment, fragment)
        raise SyntaxError(f"Unsupported fragment type: {type(fragment).__name__}")

    def _attach_step_with_frontier(self, pivot, axis, step_node):
        """Attach one step and return both the fragment root and the new frontier node."""
        root = self._find_root(pivot)

        if axis == "?":
            pass

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


