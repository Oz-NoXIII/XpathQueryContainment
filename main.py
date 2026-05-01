from argparse import ArgumentParser
from pathlib import Path
import webbrowser

from controller.expression_transformer import ExpressionTransformer
from controller.xpath_parser import XPathParser
from view import TreePatternQueryVisualizer


DEFAULT_EXPRESSION = (
	"(self[(lab = *)&?descendant[(lab = c)]&?ancestor[(lab = a)&?child[(lab = b)&?child[(lab = c)]]&?descendant[(lab = e)]]]/child[(lab = d)])"
)


def main():
	parser = ArgumentParser(description="Visualize a TreePatternQuery as an SVG/HTML graph")
	parser.add_argument("expression", nargs="?", default=DEFAULT_EXPRESSION)
	parser.add_argument("-o", "--output", default="tpq_visualization.html")
	parser.add_argument("--static", action="store_true", help="Generate static SVG instead of interactive canvas")
	parser.add_argument("--no-open", action="store_true", help="Do not open the generated HTML file")
	args = parser.parse_args()

	tree = XPathParser().parse(args.expression)
	tpq = ExpressionTransformer().transform(tree)

	output_path = Path(args.output).resolve()
	visualizer = TreePatternQueryVisualizer(tpq)
	visualizer.save_html(
		output_path,
		title="TreePatternQuery visualisation",
		interactive=not args.static,
		xpath_query=args.expression,
	)

	print(f"Visualisation générée : {output_path}")
	if not args.no_open:
		webbrowser.open_new_tab(output_path.as_uri())


if __name__ == "__main__":
	main()
