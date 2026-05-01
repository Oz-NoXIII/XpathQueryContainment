from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery
from view import TreePatternQueryVisualizer


class TestTreePatternQueryVisualizer(TestCase):
	# noinspection PyMethodMayBeStatic
	def _build_sample_query(self):
		root = QueryNode("root")
		child = QueryNode("child")
		descendant = QueryNode("descendant")
		root.add_child(child)
		root.add_descendant(descendant)
		tpq = TreePatternQuery(root)
		tpq.set_nodes()
		return tpq, root, child, descendant

	def test_layout_contains_nodes_and_edge_types(self):
		tpq, root, child, descendant = self._build_sample_query()
		visualizer = TreePatternQueryVisualizer(tpq)

		layout = visualizer.layout()

		assert layout["root"] is root
		assert len(layout["positions"]) == 3
		assert {edge["type"] for edge in layout["edges"]} == {"child", "descendant"}
		assert layout["positions"][child][1] > layout["positions"][root][1]
		assert layout["positions"][descendant][1] > layout["positions"][root][1]

	def test_svg_renders_circles_and_double_lines(self):
		tpq, _root, _child, _descendant = self._build_sample_query()
		visualizer = TreePatternQueryVisualizer(tpq)

		svg = visualizer.to_svg()

		assert svg.count("<circle") == 3
		assert svg.count('class="edge child"') == 1
		assert svg.count('class="edge descendant"') == 2
		assert "child/parent" in svg
		assert "descendant/ancestor" in svg

	def test_save_html_writes_a_self_contained_page(self):
		tpq, *_ = self._build_sample_query()
		visualizer = TreePatternQueryVisualizer(tpq)

		with TemporaryDirectory() as tmp_dir:
			output = Path(tmp_dir) / "graph.html"
			written = visualizer.save_html(output, interactive=False)

			assert written == output
			content = output.read_text(encoding="utf-8")
			assert "<!doctype html>" in content.lower()
			assert "TreePatternQuery visualisation" in content
			assert "Requête XPath" not in content
			assert "prefers-color-scheme: dark" in content
			assert "--tpq-node-fill" in content
			assert "theme-switch" in content
			assert "tpq-theme" in content
			assert "applyTheme" in content

	def test_save_html_static_displays_xpath_query(self):
		tpq, *_ = self._build_sample_query()
		visualizer = TreePatternQueryVisualizer(tpq)
		xpath_query = "self[(lab = a)]/child[(lab = b)]"

		with TemporaryDirectory() as tmp_dir:
			output = Path(tmp_dir) / "graph_static_query.html"
			visualizer.save_html(output, interactive=False, xpath_query=xpath_query)

			content = output.read_text(encoding="utf-8")
			assert "Requête XPath" in content
			assert "self[" in content
			assert "/" in content
			assert "child[" in content
			assert "\n" in content

	def test_save_html_interactive_generates_canvas(self):
		tpq, *_ = self._build_sample_query()
		visualizer = TreePatternQueryVisualizer(tpq)
		xpath_query = "self[(lab = a)]/child[(lab = b)]"

		with TemporaryDirectory() as tmp_dir:
			output = Path(tmp_dir) / "graph.html"
			written = visualizer.save_html(output, interactive=True, xpath_query=xpath_query)

			assert written == output
			content = output.read_text(encoding="utf-8")
			assert "<!doctype html>" in content.lower()
			assert "<canvas" in content
			assert "requestAnimationFrame" in content
			assert "resolveCollisions" in content
			assert "collisionPadding" in content
			assert "maxSpeed" in content
			assert "enforceHierarchy" in content
			assert "hierarchyForce" in content
			assert "targetY" in content
			assert "rootPadding" in content
			assert "settleSpeedThreshold" in content
			assert "settleFrames" in content
			assert "isPinned" in content
			assert "isFixed" in content
			assert "isSimulationSettled" in content
			assert "Requête XPath" in content
			assert "self[" in content
			assert "/" in content
			assert "child[" in content
			assert "\n" in content
			assert "prefers-color-scheme: dark" in content
			assert "getThemeColors" in content
			assert "themeColors" in content
			assert "theme-switch" in content
			assert "tpq-theme" in content
			assert "applyTheme" in content

	def test_save_html_escapes_xpath_query(self):
		tpq, *_ = self._build_sample_query()
		visualizer = TreePatternQueryVisualizer(tpq)
		xpath_query = '<node attr="x&y">'

		with TemporaryDirectory() as tmp_dir:
			output = Path(tmp_dir) / "graph_escape.html"
			visualizer.save_html(output, interactive=True, xpath_query=xpath_query)

			content = output.read_text(encoding="utf-8")
			assert '&lt;node attr=&quot;x&amp;y&quot;&gt;' in content
			assert xpath_query not in content

	def test_format_xpath_query_for_display_structures_query(self):
		tpq, *_ = self._build_sample_query()
		visualizer = TreePatternQueryVisualizer(tpq)

		formatted = visualizer._format_xpath_query_for_display("self[(lab = a)&?child[(lab = b)]]/child[(lab = c)]")

		assert "\n" in formatted
		assert "self[" in formatted
		assert "?child[" in formatted
		assert "/" in formatted

	def test_visualizer_uses_q_outputs_for_complex_query(self):
		from controller.expression_transformer import ExpressionTransformer
		from controller.xpath_parser import XPathParser

		expression = "(self[(lab = *)&?descendant[(lab = c)]&?ancestor[(lab = a)&?child[(lab = b)&?child[(lab = c)]]&?descendant[(lab = e)]]]/child[(lab = d)])"
		tpq = ExpressionTransformer().transform(XPathParser().parse(expression))
		visualizer = TreePatternQueryVisualizer(tpq)

		svg = visualizer.to_svg()

		assert 'data-output-roles="u1"' in svg
		assert 'data-output-roles="u2"' in svg
		assert 'data-output-roles="u1,u2"' not in svg











