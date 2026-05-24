from argparse import ArgumentParser
import importlib
from pathlib import Path
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json

from controller.expression_transformer import ExpressionTransformer
from controller.bool_tpq_lab_homomorphism import find_bool_tpq_lab_homomorphism
from controller.xpath_containment import analyze_xpath_containment
from controller.xpath_containment import XPathContainmentAnalyzer
from controller.xml_tree_homomorphism import XmlTreeHomomorphismAnalyzer, analyze_xpath_against_xml
from controller.xpath_parser import XPathParser
from controller.tpq_graph_codec import booleanize_graph_payload, graph_payload_to_tpq, tpq_to_graph_payload
from view import TreePatternQueryBuilderPage, TreePatternQueryVisualizer, TPQXmlHomomorphismPage
from view import xpath_containment_page as containment_page_module


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
	parser.add_argument("--containment", action="store_true", help="Open the XPath containment page")
	parser.add_argument("--xml-tree", action="store_true", help="Open the TPQ versus XML tree homomorphism page")
	parser.add_argument("--port", type=int, default=8000, help="Port for the local web server")
	parser.add_argument("--no-open", action="store_true", help="Do not open the generated HTML file")
	args = parser.parse_args()
	if (args.builder or args.containment or args.xml_tree) and not args.serve:
		args.serve = True

	# If --serve is passed, start a local server that serves an interactive UI
	if args.serve and not args.static:
		host = "127.0.0.1"
		port = args.port
		parser_obj = XPathParser()
		transformer = ExpressionTransformer()
		builder_page = TreePatternQueryBuilderPage()
		xml_page = TPQXmlHomomorphismPage()
		containment_analyzer = XPathContainmentAnalyzer(parser_obj, transformer)
		xml_analyzer = XmlTreeHomomorphismAnalyzer(parser_obj, transformer)

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
				def _fresh_containment_page(self):
					module = importlib.reload(containment_page_module)
					return module.XPathContainmentPage()

				def _write(self, status, content, content_type="text/html"):
					self.send_response(status)
					self.send_header("Content-Type", f"{content_type}; charset=utf-8")
					self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
					self.send_header("Pragma", "no-cache")
					self.send_header("Expires", "0")
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

					if parsed.path == "/containment":
						try:
							containment_page = self._fresh_containment_page()
							html = containment_page.to_html(title="Vérification d'inclusion XPath via homomorphismes")
							self._write(200, html, content_type="text/html")
						except Exception as e:
							self._write(500, str(e), content_type="text/plain")
						return

					if parsed.path == "/tpq-xml":
						try:
							html = xml_page.to_html(title="Homomorphisme TPQ ↔ arbre XML")
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

					if parsed.path == '/containment/progress':
						pid = qs.get('progress_id', [None])[0]
						if not pid or not hasattr(self.server, 'progress_store') or pid not in self.server.progress_store:
							self._write(404, json.dumps({'message': 'unknown progress id'}), content_type='application/json')
						else:
							self._write(200, json.dumps(self.server.progress_store[pid]), content_type='application/json')
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
							# Invert the direction for containment check: to verify if q1 ⊆ q2, we check for a homomorphism q2 → q1
							result = find_bool_tpq_lab_homomorphism(payload.get("target"), payload.get("source"))
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

					if parsed.path == "/containment/analyze":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							result = analyze_xpath_containment(payload.get("q1", ""), payload.get("q2", ""))
							self._write(200, json.dumps(result), content_type="application/json")
						except Exception as e:
							self._write(400, json.dumps({"contained": False, "message": str(e), "attempts": []}), content_type="application/json")
						return

					if parsed.path == "/containment/transform":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							result = containment_analyzer.transform_queries(payload.get("q1", ""), payload.get("q2", ""))
							self._write(200, json.dumps(result), content_type="application/json")
						except Exception as e:
							self._write(400, json.dumps({"message": str(e)}), content_type="application/json")
						return

					if parsed.path == "/containment/booleanize":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							result = containment_analyzer.booleanize_queries(payload.get("q1", {}), payload.get("q2", {}))
							self._write(200, json.dumps(result), content_type="application/json")
						except Exception as e:
							self._write(400, json.dumps({"message": str(e)}), content_type="application/json")
						return

					if parsed.path == "/containment/check":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							source = payload.get("source", {})
							target = payload.get("target", {})
							if payload.get("direction", "forward") == "backward":
								source, target = target, source
							# support progress reporting via an optional progress_id
							progress_id = payload.get('progress_id') or ('p-' + __import__('uuid').uuid4().hex[:8])
							# initialize a simple progress store on the server
							if not hasattr(self.server, 'progress_store'):
								self.server.progress_store = {}
							self.server.progress_store[progress_id] = { 'attempted': 0, 'total': 0, 'done': False, 'result': None }
							source_tpq = graph_payload_to_tpq(source)
							target_tpq = graph_payload_to_tpq(target)

							def _progress_callback(attempted, total, lengths):
								store = self.server.progress_store.get(progress_id)
								if store is not None:
									store['attempted'] = attempted
									store['total'] = total

							def _worker():
								try:
									result = containment_analyzer.evaluate_containment(
										source_tpq,
										target_tpq,
										source_name=payload.get("source_name", "q1"),
										target_name=payload.get("target_name", "q2"),
										progress_callback=_progress_callback,
									)
									result['progress_id'] = progress_id
									store = self.server.progress_store.get(progress_id)
									if store is not None:
										store['result'] = result
										store['done'] = True
										store['attempted'] = store.get('attempted', 0)
										store['total'] = store.get('total', 0) or result.get('size_bound', 0)
								except Exception as exc:
									store = self.server.progress_store.get(progress_id)
									if store is not None:
										store['result'] = {"contained": False, "message": str(exc), "attempts": []}
										store['done'] = True

							thread = threading.Thread(target=_worker, daemon=True)
							thread.start()
							self._write(200, json.dumps({"progress_id": progress_id, "started": True}), content_type="application/json")
						except Exception as e:
							self._write(400, json.dumps({"contained": False, "message": str(e), "attempts": []}), content_type="application/json")
						return

					if parsed.path == "/tpq-xml/transform":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							result = xml_analyzer.transform_xpath(payload.get("xpath", ""))
							self._write(200, json.dumps(result), content_type="application/json")
						except Exception as e:
							self._write(400, json.dumps({"message": str(e)}), content_type="application/json")
						return

					if parsed.path == "/tpq-xml/analyze":
						content_length = int(self.headers.get("Content-Length", "0"))
						try:
							body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
							payload = json.loads(body)
							result = analyze_xpath_against_xml(payload.get("xpath", ""), payload.get("xml", ""))
							self._write(200, json.dumps(result), content_type="application/json")
						except Exception as e:
							self._write(400, json.dumps({"exists": False, "message": str(e), "mapping": []}), content_type="application/json")
						return

					self._write(404, "Not found", content_type="text/plain")

			return Handler

		server_address = (host, port)
		httpd = HTTPServer(server_address, make_handler())  # type: ignore[arg-type]
		if args.containment:
			url = f"http://{host}:{port}/containment"
		elif args.xml_tree:
			url = f"http://{host}:{port}/tpq-xml"
		elif args.builder:
			url = f"http://{host}:{port}/builder"
		else:
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
