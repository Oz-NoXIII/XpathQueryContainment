from unittest import TestCase

from controller.xpath_containment import analyze_xpath_containment
from view.xpath_containment_page import XPathContainmentPage


class TestXPathContainment(TestCase):
	def test_analyze_xpath_containment_reports_success_for_identical_queries(self):
		result = analyze_xpath_containment("self[(lab = a)]", "self[(lab = a)]")

		assert result["contained"] is True
		assert "inclus" in result["summary"].lower()
		assert result["counterexample_tree"] is None
		assert len(result["attempts"]) == 1
		assert result["step_raw"]["q1"]["svg"].startswith("<svg")
		assert result["step_booleanize"]["q1"]["svg"].startswith("<svg")

	def test_analyze_xpath_containment_returns_counterexample_tree_when_no_homomorphism(self):
		result = analyze_xpath_containment("self[(lab = a)]", "self[(lab = b)]")

		assert result["contained"] is False
		assert "contre-exemple" in result["summary"].lower()
		assert result["counterexample_tree"] is not None
		assert result["counterexample_lengths"] == []
		assert len(result["attempts"]) == 1
		assert result["attempts"][0]["exists"] is False
		assert result["counterexample_tree"].startswith("<svg")

	def test_xpath_containment_page_contains_key_sections(self):
		page = XPathContainmentPage()

		html = page.to_html()

		assert "Vérification" in html
		assert "homomorphismes" in html
		assert "Transformer XPath → TPQ" in html
		assert "Booléaniser" in html
		assert "Vérifier q1 ⊆ q2" in html
		assert "Vérifier q2 ⊆ q1" in html
		assert "Arbre canonique Tc / contre-exemple" in html
		assert "q1 — TPQ brut" in html
		assert "q1 — booléanisé" in html
		assert "/containment/transform" in html
		assert "/containment/booleanize" in html
		assert "/containment/check" in html
		assert "PC.pdf" in html



