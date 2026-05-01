from argparse import ArgumentParser
from pathlib import Path
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json

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
	parser.add_argument("--serve", action="store_true", help="Start a local web server to interactively edit the XPath")
	parser.add_argument("--port", type=int, default=8000, help="Port for the local web server")
	parser.add_argument("--no-open", action="store_true", help="Do not open the generated HTML file")
	args = parser.parse_args()

	# If --serve is passed, start a local server that serves an interactive UI
	if args.serve and not args.static:
		host = "127.0.0.1"
		port = args.port
		parser_obj = XPathParser()
		transformer = ExpressionTransformer()

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
							tree = parser_obj.parse(expr)
							tpq = transformer.transform(tree)
							visualizer = TreePatternQueryVisualizer(tpq)
							html = visualizer.to_html(title="TreePatternQuery visualisation", interactive=True, xpath_query=expr)
							self._write(200, html, content_type="text/html")
						except Exception as e:
							tb = str(e)
							self._write(500, f"Erreur lors du parsing: {tb}", content_type="text/plain")
						return

					if parsed.path == "/graph":
						expr = qs.get("expression", [args.expression])[0]
						try:
							tree = parser_obj.parse(expr)
							tpq = transformer.transform(tree)
							# Build nodes/edges as in visualizer._to_interactive_html
							nodes_list = []
							edges_list = []
							nodes_by_id = {}
							node_counter = [0]

							def traverse(node, depth=0):
								node_id = id(node)
								if node_id in nodes_by_id:
									return nodes_by_id[node_id]
								idx = node_counter[0]
								node_counter[0] += 1
								label = str(node.get_label())
								roles = []
								u1, u2 = tpq.get_output_nodes()
								if node is u1:
									roles.append("u1")
								if node is u2:
									roles.append("u2")
								nodes_list.append({"id": f"node_{idx}", "label": label, "index": idx, "depth": depth, "roles": roles})
								nodes_by_id[node_id] = idx

								for child in node.get_children():
									child_idx = traverse(child, depth + 1)
									edges_list.append({"source": idx, "target": child_idx, "type": "child"})
								for desc in node.get_descendants():
									desc_idx = traverse(desc, depth + 1)
									edges_list.append({"source": idx, "target": desc_idx, "type": "descendant"})
								return idx

							traverse(tpq.get_root())
							payload = json.dumps({"nodes": nodes_list, "edges": edges_list})
							self._write(200, payload, content_type="application/json")
						except Exception as e:
							self._write(500, str(e), content_type="text/plain")
						return

					# Not found
					self._write(404, "Not found", content_type="text/plain")

			return Handler

		server_address = (host, port)
		httpd = HTTPServer(server_address, make_handler())
		url = f"http://{host}:{port}/?expression={quote(args.expression or '')}"
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
