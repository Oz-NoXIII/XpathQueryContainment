from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

from controller.expression_transformer import ExpressionTransformer
from controller.xpath_parser import XPathParser
from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery
from view.tpq_visualizer import TreePatternQueryVisualizer


class XmlTreeHomomorphismError(ValueError):
	"""Raised when the XML tree or XPath input cannot be processed."""



class XmlTreeHomomorphismAnalyzer:
	def __init__(self, parser: XPathParser | None = None, transformer: ExpressionTransformer | None = None):
		self.parser = parser or XPathParser()
		self.transformer = transformer or ExpressionTransformer()

	def parse_xpath(self, expression: str) -> TreePatternQuery:
		if not isinstance(expression, str) or not expression.strip():
			raise XmlTreeHomomorphismError("L'expression XPath ne peut pas être vide.")
		try:
			return self.transformer.transform(self.parser.parse(expression))
		except Exception as exc:  # pragma: no cover - forwarded to the UI
			raise XmlTreeHomomorphismError(str(exc)) from exc

	def _local_name(self, tag: str) -> str:
		if tag.startswith("{") and "}" in tag:
			return tag.split("}", 1)[1]
		return tag

	def parse_xml_tree(self, xml_text: str) -> TreePatternQuery:
		if not isinstance(xml_text, str) or not xml_text.strip():
			raise XmlTreeHomomorphismError("Le document XML ne peut pas être vide.")
		try:
			root_element = ET.fromstring(xml_text)
		except ET.ParseError as exc:
			raise XmlTreeHomomorphismError(f"XML invalide : {exc}") from exc

		memo: dict[ET.Element, QueryNode] = {}

		def build(element: ET.Element) -> QueryNode:
			if element in memo:
				return memo[element]
			node = QueryNode(self._local_name(element.tag))
			memo[element] = node
			for child_element in list(element):
				node.add_child(build(child_element))
			return node

		root = build(root_element)
		tpq = TreePatternQuery(root)
		tpq.set_nodes()
		return tpq

	def transform_xpath(self, expression: str) -> dict[str, Any]:
		tpq = self.parse_xpath(expression)
		visualizer = TreePatternQueryVisualizer(tpq)
		layout = visualizer.layout()
		# Reuse the existing graph codec structure for the front-end simply as SVG payload.
		# The page only needs the SVG and formatted query, so we keep the data lightweight.
		# Use a compact SVG for the small preview embedded in the UI to avoid
		# rendering the global title/legend which overlap the preview slot.
		return {
			"svg": visualizer.to_svg(compact=True),
			"formatted_query": visualizer._format_xpath_query_for_display(expression),
			"layout": {"width": layout.get("width"), "height": layout.get("height")},
		}

	def analyze(self, xpath_expression: str, xml_text: str) -> dict[str, Any]:
		tpq = self.parse_xpath(xpath_expression)
		tree = self.parse_xml_tree(xml_text)
		result = tpq.find_homomorphism(tree)
		tpq_visualizer = TreePatternQueryVisualizer(tpq)
		tree_visualizer = TreePatternQueryVisualizer(tree)
		return {
			"exists": result["exists"],
			"message": result["message"],
			"mapping": result["mapping"],
			"highlight_target_ids": result.get("highlight_target_ids", []),
			"tpq": {"svg": tpq_visualizer.to_svg(compact=True), "formatted_query": tpq_visualizer._format_xpath_query_for_display(xpath_expression)},
			# For the XML tree preview we do not display output node decorations (no green fill / badges)
			"xml_tree": {"svg": tree_visualizer.to_svg(compact=True, show_outputs=False)},
			"xpath_expression": xpath_expression,
			"xml_text": xml_text,
		}



def analyze_xpath_against_xml(xpath_expression: str, xml_text: str) -> dict[str, Any]:
	return XmlTreeHomomorphismAnalyzer().analyze(xpath_expression, xml_text)




