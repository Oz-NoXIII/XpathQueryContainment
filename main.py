from argparse import ArgumentParser
from pathlib import Path
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json

from controller.expression_transformer import ExpressionTransformer
from controller.bool_tpq_lab_homomorphism import find_bool_tpq_lab_homomorphism
from controller.xpath_parser import XPathParser
from controller.tpq_graph_codec import booleanize_graph_payload, tpq_to_graph_payload
from view import TreePatternQueryBuilderPage, TreePatternQueryVisualizer


DEFAULT_EXPRESSION = (
	"(self[(lab = *)&?descendant[(lab = c)]&?ancestor[(lab = a)&?child[(lab = b)&?child[(lab = c)]]&?descendant[(lab = e)]]]/child[(lab = d)])"
)


def main():
	parser = ArgumentParser(description="Visualize a TreePatternQuery as an SVG/HTML graph")
	parser.add_argument("expression", nargs="?", default=DEFAULT_EXPRESSION)
	parser.add_argument("-o", "--output", default="tpq_visualization.html")
	parser.add_argument("--static", action="store_true", help="Generate static SVG instead of interactive canvas")
	parser.add_argument("--serve", action="store_true", help="Start a local web server to interactively edit the XPath")
	parser.add_argument("--builder", action="store_true", help="Open the graphical TPQ builder page instead of the XPath page")
	parser.add_argument("--port", type=int, default=8000, help="Port for the local web server")
	parser.add_argument("--no-open", action="store_true", help="Do not open the generated HTML file")
	args = parser.parse_args()
	if args.builder and not args.serve:
		args.serve = True

	# If --serve is passed, start a local server that serves an interactive UI
	if args.serve and not args.static:
		host = "127.0.0.1"
		port = args.port
		parser_obj = XPathParser()
		transformer = ExpressionTransformer()
		builder_page = TreePatternQueryBuilderPage()

		def build_graph_payload(expression: str, booleanize: bool = False):
			tree = parser_obj.parse(expression)
			tpq = transformer.transform(tree)
			payload = tpq_to_graph_payload(tpq)
			# Include a suggested layout size so the interactive canvas can be
			# resized to the graph content and allow page scrolling when needed.
			visualizer = TreePatternQueryVisualizer(tpq)
			layout = visualizer.layout()
			payload["layout"] = {"width": layout.get("width"), "height": layout.get("height")}
			payload["formatted_query"] = visualizer._format_xpath_query_for_display(expression)
			if booleanize:
				tpq = tpq.to_boolean_tpq()
				payload = tpq_to_graph_payload(tpq)
				visualizer = TreePatternQueryVisualizer(tpq)
				layout = visualizer.layout()
				payload["layout"] = {"width": layout.get("width"), "height": layout.get("height")}
				payload["formatted_query"] = visualizer._format_xpath_query_for_display(expression)
				payload["formatted_query"] += "\n(booléanisé)"
			return payload

		def make_handler():
			class Handler(BaseHTTPRequestHandler):
				def _write(self, status, content, content_type="text/html"):
					self.send_response(status)
					self.send_header("Content-Type", f"{content_type}; charset=utf-8")
					self.end_headers()
					if isinstance(content, str):
						self.wfile.write(content.encode("utf-8"))
					else:
						self.wfile.write(content)

				def do_GET(self):
					parsed = urlparse(self.path)
					qs = parse_qs(parsed.query)
					if parsed.path in ("/", ""):
						expr = qs.get("expression", [args.expression])[0]
						try:
							tpq = transformer.transform(parser_obj.parse(expr))
							visualizer = TreePatternQueryVisualizer(tpq)
							html = visualizer.to_html(title="TreePatternQuery visualisation", interactive=True, xpath_query=expr)
							self._write(200, html, content_type="text/html")
						except Exception as e:
							tb = str(e)
							self._write(500, f"Erreur lors du parsing: {tb}", content_type="text/plain")
						return

					if parsed.path == "/builder":
						try:
							html = builder_page.to_html(title="Constructeur de BoolTPQ_Lab")
							self._write(200, html, content_type="text/html")
						except Exception as e:
							self._write(500, str(e), content_type="text/plain")
						return

					if parsed.path == "/graph":
						expr = qs.get("expression", [args.expression])[0]
						try:
							payload = json.dumps(build_graph_payload(expr))
							self._write(200, payload, content_type="application/json")
						except Exception as e:
							self._write(500, str(e), content_type="text/plain")
						return

					if parsed.path == "/booleanize":
						expr = qs.get("expression", [args.expression])[0]
						try:
							payload_data = build_graph_payload(expr, booleanize=True)
							payload = json.dumps(payload_data)
							self._write(200, payload, content_type="application/json")
						except Exception as e:
							self._write(500, str(e), content_type="text/plain")
						return

					# Not found
					self._write(404, "Not found", content_type="text/plain")

				def do_POST(self):
					parsed = urlparse(self.path)
					if parsed.path == "/builder/homomorphism":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							result = find_bool_tpq_lab_homomorphism(payload.get("source"), payload.get("target"))
							self._write(200, json.dumps(result), content_type="application/json")
						except Exception as e:
							self._write(400, json.dumps({"exists": False, "message": str(e), "mapping": []}), content_type="application/json")
						return

					if parsed.path == "/builder/booleanize":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							booleanized = booleanize_graph_payload(payload)
							self._write(200, json.dumps(booleanized), content_type="application/json")
						except Exception as e:
							self._write(400, str(e), content_type="text/plain")
						return

					self._write(404, "Not found", content_type="text/plain")

			return Handler

		server_address = (host, port)
		httpd = HTTPServer(server_address, make_handler())  # type: ignore[arg-type]
		url = f"http://{host}:{port}/builder" if args.builder else f"http://{host}:{port}/?expression={quote(args.expression or '')}"
		print(f"Démarrage du serveur local sur {host}:{port}\nOuvrir {url}")
		if not args.no_open:
			webbrowser.open_new_tab(url)
		try:
			httpd.serve_forever()
		except KeyboardInterrupt:
			print("Arrêt du serveur")
			httpd.server_close()
		return

	# Génération de fichier HTML/PNG habituel
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
