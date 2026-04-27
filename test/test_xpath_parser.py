from unittest import TestCase
from controller.xpath_parser import XPathParser, detect_grammar


class TestXPathParser(TestCase):
	def setUp(self):
		self.parser = XPathParser()

	def test_detect_grammar_returns_syntax_for_axis_names(self):
		syntax_inputs = [
			"self",
			"descendant",
			"next-sibling",
			"following",
			"child",
			"descendant-or-self",
			"following-sibling",
			"preceding",
			"parent",
			"ancestor",
			"previous-sibling",
			"ancestor-or-self",
			"preceding-sibling",
			"(child/parent)",
			"?following-sibling",
			"function(ancestor)"
		]

		for expression in syntax_inputs:
			with self.subTest(expression=expression):
				assert detect_grammar(expression) == "syntax"

	def test_detect_grammar_returns_abbreviated_for_non_axis_tokens(self):
		abbreviated_inputs = [
			".//person/name",
			".//childish",
			"CHILD",
			"person U name",
			"..//*[@id]",
		]

		for expression in abbreviated_inputs:
			with self.subTest(expression=expression):
				assert detect_grammar(expression) == "abbreviated_syntax"

	def test_parse_syntax_expressions(self):
		expressions = [
			"child",
			"?child",
			"child[(lab = *)]",
			"?child[!(lab = person)]",
			"((child/descendant)Uparent)",
			"?(descendant[((lab = person) | ?descendant[(lab = ame)])] U self)",
			"?( descendant[((lab = person) & !?child[(lab = birthplace)])] / child[(lab = name)] )"
		]

		for expression in expressions:
			with self.subTest(expression=expression):
				tree = self.parser.parse(expression)
				assert tree is not None

	def test_parse_abbreviated_expressions(self):
		expressions = [
			"./*",
			".[*]",
			"./*",
			".[*] & !person",
			"./*//*U..",
			".//*[.//*[person | .//ame] U .]",
			".//*[.//*[person & !./birthplace]/*[name]]",
		]

		for expression in expressions:
			with self.subTest(expression=expression):
				tree = self.parser.parse(expression)
				assert tree is not None

	def test_parse_invalid_syntax_expressions_raise_syntax_error(self):
		expressions = [
			"(child",
			"child[(lab = person]",
			"((child/descendant)U)",
		]

		for expression in expressions:
			with self.subTest(expression=expression):
				with self.assertRaises(SyntaxError) as cm:
					self.parser.parse(expression)

				assert "syntax" in str(cm.exception)

	def test_parse_invalid_abbreviated_expressions_raise_syntax_error(self):
		expressions = [
			".//person[",
			"person//",
			"person[name",
		]

		for expression in expressions:
			with self.subTest(expression=expression):
				with self.assertRaises(SyntaxError) as cm:
					self.parser.parse(expression)

				assert "abbreviated_syntax" in str(cm.exception)
