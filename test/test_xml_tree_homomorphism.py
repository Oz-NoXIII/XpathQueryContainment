from unittest import TestCase

from controller.xml_tree_homomorphism import analyze_xpath_against_xml
from view.tpq_xml_homomorphism_page import TPQXmlHomomorphismPage


class TestXmlTreeHomomorphism(TestCase):
	def test_analyze_xpath_against_xml_reports_success(self):
		result = analyze_xpath_against_xml("self[(lab = a)&?child[(lab = b)]]", "<a><b /></a>")

		assert result["exists"] is True
		assert result["mapping"]
		assert result["tpq"]["svg"].startswith("<svg")
		assert result["xml_tree"]["svg"].startswith("<svg")

	def test_analyze_xpath_against_xml_reports_failure(self):
		result = analyze_xpath_against_xml("self[(lab = a)&?child[(lab = c)]]", "<a><b /></a>")

		assert result["exists"] is False
		assert result["mapping"] == []

	def test_tpq_xml_homomorphism_page_contains_key_sections(self):
		page = TPQXmlHomomorphismPage()

		html = page.to_html()

		assert "Homomorphisme TPQ ↔ arbre XML" in html
		assert "Transformer la requête" in html
		assert "Vérifier l'homomorphisme" in html
		assert "Arbre XML" in html
		assert 'id="homomorphism-overlay"' in html
		assert "circle[data-node-index]" in html
		assert "line[data-source-index]" in html
		assert "renderHomomorphismOverlay" in html

	def test_tpq_xml_homomorphism_page_escapes_initial_inputs(self):
		page = TPQXmlHomomorphismPage(
			xpath_expression='self[(lab = "a\'b")&?child[(lab = c)]]',
			xml_text='<a attr="x\'y"><b /></a>',
		)

		html = page.to_html()

		assert 'const initialXPath = ' in html
		assert 'const initialXml = ' in html
		assert 'const initialXPath = "self[(lab = \\\"a\'b\\\")&?child[(lab = c)]]";' in html
		assert 'const initialXml = "<a attr=\\\"x\'y\\\"><b /></a>";' in html








