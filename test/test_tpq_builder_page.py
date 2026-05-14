from unittest import TestCase

from view.tpq_builder import TreePatternQueryBuilderPage


class TestTreePatternQueryBuilderPage(TestCase):
	def test_to_html_contains_builder_controls(self):
		page = TreePatternQueryBuilderPage()

		html = page.to_html()

		assert "Constructeur de BoolTPQ_Lab" in html
		assert "Trouver l'homomorphisme" in html
		assert "q1" in html
		assert "q2" in html
		assert "Importer JSON" in html
		assert "Exporter JSON" in html
		assert 'id="homomorphism-overlay"' in html
		assert "Homomorphisme trouvé entre q1 et q2." in html
		assert "Recherche en cours…" in html
		assert "renderHomomorphismOverlay" in html
		assert "Requête XPath" not in html
		assert "BoolTPQ_Lab" in html
		assert "wildcard" not in html




