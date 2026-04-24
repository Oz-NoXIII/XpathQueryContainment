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

    def and_(self, _args):
        """Boolean AND is out of scope."""
        raise NotImplementedError("AND in node expressions is not supported by the TPQ transformer")

    def or_(self, _args):
        """Boolean OR is out of scope."""
        raise NotImplementedError("OR in node expressions is not supported by the TPQ transformer")

    def not_(self, _args):
        """Boolean NOT is out of scope."""
        raise NotImplementedError("NOT in node expressions is not supported by the TPQ transformer")

