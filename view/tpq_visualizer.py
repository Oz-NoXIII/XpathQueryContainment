from __future__ import annotations

from html import escape
from math import hypot
from pathlib import Path
from string import Template
from typing import Any

from model.query_node import QueryNode
from model.tree_pattern_query import TreePatternQuery


# noinspection PyMethodMayBeStatic
class TreePatternQueryVisualizer:
    """Render a TreePatternQuery as an SVG/HTML graph."""

    def __init__(
        self,
        tree_pattern_query: TreePatternQuery,
        *,
        node_radius: int = 24,
        horizontal_gap: int = 110,
        vertical_gap: int = 110,
        padding: int = 40,
        descendant_offset: int = 4,
    ):
        self.tree_pattern_query = tree_pattern_query
        self.node_radius = node_radius
        self.horizontal_gap = horizontal_gap
        self.vertical_gap = vertical_gap
        self.padding = padding
        self.descendant_offset = descendant_offset

    def update(self, tree_pattern_query: TreePatternQuery):
        """Swap the rendered query and refresh the next snapshot."""
        self.tree_pattern_query = tree_pattern_query

    def _iter_outgoing(self, node: QueryNode):
        for child in node.get_children():
            yield "child", child
        for descendant in node.get_descendants():
            yield "descendant", descendant

    def _measure_widths(self, node: QueryNode, cache: dict[QueryNode, float]) -> float:
        label_text = str(node.get_label())
        own_width = max(self.node_radius * 2 + 16, len(label_text) * 8 + 24)

        outgoing = list(self._iter_outgoing(node))
        if not outgoing:
            cache[node] = float(own_width)
            return cache[node]

        children_width = sum(self._measure_widths(child, cache) for _edge_type, child in outgoing)
        cache[node] = float(max(own_width, children_width))
        return cache[node]

    def layout(self) -> dict[str, Any]:
        root = self.tree_pattern_query.get_root()
        widths: dict[QueryNode, float] = {}
        self._measure_widths(root, widths)

        positions: dict[QueryNode, tuple[float, float]] = {}
        edges: list[dict[str, Any]] = []
        max_depth = 0

        def place(node: QueryNode, depth: int, left: float) -> float:
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            outgoing = list(self._iter_outgoing(node))
            own_width = widths[node]
            y = self.padding + depth * self.vertical_gap

            if not outgoing:
                x = left + own_width / 2
                positions[node] = (x, y)
                return own_width

            child_widths = [(edge_type, child, widths[child]) for edge_type, child in outgoing]
            total_children_width = sum(width for _edge_type, _child, width in child_widths)
            block_width = max(own_width, total_children_width)
            cursor = left + (block_width - total_children_width) / 2
            centers = []

            for edge_type, child, child_width in child_widths:
                place(child, depth + 1, cursor)
                edges.append(
                    {
                        "parent": node,
                        "child": child,
                        "type": edge_type,
                    }
                )
                centers.append(positions[child][0])
                cursor += child_width

            x = sum(centers) / len(centers)
            positions[node] = (x, y)
            return block_width

        total_width = place(root, 0, self.padding)
        max_x = max(x for x, _y in positions.values()) if positions else 0
        max_y = max(y for _x, y in positions.values()) if positions else 0

        return {
            "root": root,
            "positions": positions,
            "edges": edges,
            "width": int(max(total_width + self.padding * 2, max_x + self.padding)),
            "height": int(max_y + self.padding * 2),
        }

    def _layout(self) -> dict[str, Any]:
        return self.layout()

    def _shrink_segment(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> tuple[float, float, float, float]:
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        length = hypot(dx, dy) or 1.0
        ux = dx / length
        uy = dy / length
        return (
            x1 + ux * self.node_radius,
            y1 + uy * self.node_radius,
            x2 - ux * self.node_radius,
            y2 - uy * self.node_radius,
        )

    def _line_points(self, start: tuple[float, float], end: tuple[float, float], offset: float = 0.0):
        x1, y1 = start
        x2, y2 = end
        if offset == 0:
            return x1, y1, x2, y2

        dx = x2 - x1
        dy = y2 - y1
        length = hypot(dx, dy) or 1.0
        ox = -dy / length * offset
        oy = dx / length * offset
        return x1 + ox, y1 + oy, x2 + ox, y2 + oy

    def _format_xpath_query_for_display(self, query: str) -> str:
        """Pretty-print an XPath-like expression for easier reading in HTML."""
        compact = " ".join(query.strip().split())
        if not compact:
            return ""

        lines: list[str] = []
        current = []
        indent = 0
        i = 0

        def flush_line():
            text = "".join(current).strip()
            if text:
                lines.append(("  " * max(0, indent)) + text)
            current.clear()

        while i < len(compact):
            ch = compact[i]
            nxt = compact[i + 1] if i + 1 < len(compact) else ""

            if ch == "(":
                current.append(ch)
                flush_line()
                indent += 1
            elif ch == ")":
                flush_line()
                indent = max(0, indent - 1)
                current.append(ch)
                flush_line()
            elif ch == "[":
                current.append(ch)
                flush_line()
                indent += 1
            elif ch == "]":
                flush_line()
                indent = max(0, indent - 1)
                current.append(ch)
                flush_line()
            elif ch in {"&", "|"}:
                prev = compact[i - 1] if i > 0 else ""
                is_boolean_operator = not prev.isalnum() and not nxt.isalnum()
                if is_boolean_operator:
                    flush_line()
                    current.append(ch)
                    flush_line()
                else:
                    current.append(ch)
            elif ch == "/" and nxt == "/":
                flush_line()
                current.append("//")
                flush_line()
                i += 1
            elif ch == "/":
                flush_line()
                current.append("/")
                flush_line()
            else:
                current.append(ch)

            i += 1

        flush_line()
        return "\n".join(lines)

    def _theme_switch_html(self) -> str:
        return """
        <div id="tpq-theme" class="theme-switch" role="group" aria-label="Choix du thème">
          <span class="theme-switch-label">Thème</span>
          <button type="button" class="theme-option" data-theme-option="light" aria-pressed="false">Clair</button>
          <button type="button" class="theme-option" data-theme-option="dark" aria-pressed="false">Sombre</button>
          <button type="button" class="theme-option" data-theme-option="auto" aria-pressed="false">Auto</button>
        </div>
        """.strip()

    def _theme_switch_script(self) -> str:
        return """
    const themeStorageKey = 'tpq-theme';
    const themeRoot = document.documentElement;
    const themeButtons = Array.from(document.querySelectorAll('[data-theme-option]'));
    const themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    let currentTheme = 'auto';

    function readStoredTheme() {
      try {
        const storedTheme = window.localStorage.getItem(themeStorageKey);
        return storedTheme === 'light' || storedTheme === 'dark' || storedTheme === 'auto' ? storedTheme : 'auto';
      } catch (error) {
        return 'auto';
      }
    }

    function storeTheme(theme) {
      try {
        window.localStorage.setItem(themeStorageKey, theme);
      } catch (error) {
        // Storage may be unavailable; ignore.
      }
    }

    function syncThemeButtons(theme) {
      themeButtons.forEach(button => {
        const isActive = button.dataset.themeOption === theme;
        button.setAttribute('aria-pressed', String(isActive));
        button.classList.toggle('is-active', isActive);
      });
    }

    function applyTheme(theme, persist = true) {
      currentTheme = theme === 'light' || theme === 'dark' ? theme : 'auto';

      if (currentTheme === 'auto') {
        themeRoot.removeAttribute('data-theme');
        themeRoot.style.colorScheme = 'light dark';
      } else {
        themeRoot.setAttribute('data-theme', currentTheme);
        themeRoot.style.colorScheme = currentTheme;
      }

      if (persist) {
        storeTheme(currentTheme);
      }

      syncThemeButtons(currentTheme);

      if (typeof window.refreshThemeColors === 'function') {
        window.refreshThemeColors();
      }
    }

    window.applyTheme = applyTheme;

    themeButtons.forEach(button => {
      button.addEventListener('click', () => applyTheme(button.dataset.themeOption));
    });

    if (typeof themeMediaQuery.addEventListener === 'function') {
      themeMediaQuery.addEventListener('change', () => {
        if (currentTheme === 'auto') {
          applyTheme('auto', false);
        }
      });
    } else if (typeof themeMediaQuery.addListener === 'function') {
      themeMediaQuery.addListener(() => {
        if (currentTheme === 'auto') {
          applyTheme('auto', false);
        }
      });
    }

    applyTheme(readStoredTheme(), false);
        """.strip()

    def to_svg(self) -> str:
        layout = self.layout()
        positions = layout["positions"]
        width = layout["width"]
        height = layout["height"]
        output_u1, output_u2 = self.tree_pattern_query.get_output_nodes()

        svg_parts = [f'<svg id="tpq-svg" xmlns="http://www.w3.org/2000/svg" '
                     f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">', "<defs>", "<style>",
                     "text { font-family: Arial, Helvetica, sans-serif; font-size: 14px; }",
                     ".edge { stroke: var(--tpq-edge, #333); stroke-width: 2; stroke-linecap: round; fill: none; }",
                     ".edge.child { stroke-dasharray: none; }", ".edge.descendant { stroke-width: 1.8; }",
                      ".node-circle { fill: var(--tpq-node-fill, #f7fbff); stroke: var(--tpq-node-stroke, #1f4e79); stroke-width: 2; }",
                      ".node-circle.output { fill: #7ccf7c; }",
                     ".node-label { fill: var(--tpq-node-label, #102a43); text-anchor: middle; dominant-baseline: middle; }",
                     ".legend { fill: var(--tpq-legend, #334e68); font-size: 13px; }",
                     ".title { fill: var(--tpq-title, #102a43); font-size: 18px; font-weight: bold; }", "</style>",
                     "</defs>",
                     f'<text class="title" x="{self.padding}" y="{self.padding / 2 + 8}">TreePatternQuery</text>']

        for edge in layout["edges"]:
            parent = edge["parent"]
            child = edge["child"]
            edge_type = edge["type"]
            start = positions[parent]
            end = positions[child]
            segment = self._shrink_segment(start, end)

            if edge_type == "child":
                svg_parts.append(
                    f'<line class="edge child" x1="{segment[0]}" y1="{segment[1]}" '
                    f'x2="{segment[2]}" y2="{segment[3]}" />'
                )
            elif edge_type == "descendant":
                for offset in (-self.descendant_offset, self.descendant_offset):
                    x1, y1, x2, y2 = self._line_points((segment[0], segment[1]), (segment[2], segment[3]), offset)
                    svg_parts.append(
                        f'<line class="edge descendant" x1="{x1}" y1="{y1}" '
                        f'x2="{x2}" y2="{y2}" />'
                    )
            else:
                raise SyntaxError(f"Unsupported edge type for visualization: {edge_type}")

        for node, (x, y) in positions.items():
            label = escape(str(node.get_label()))
            roles = []
            if node is output_u1:
                roles.append("u1")
            if node is output_u2:
                roles.append("u2")
            extra_class = " output" if roles else ""
            roles_attr = f' data-output-roles="{','.join(roles)}"' if roles else ''
            svg_parts.append(f'<circle class="node-circle{extra_class}" cx="{x}" cy="{y}" r="{self.node_radius}"{roles_attr} />')
            svg_parts.append(f'<text class="node-label" x="{x}" y="{y}">{label}</text>')

        legend_y = height - self.padding / 2
        svg_parts.append(
            f'<text class="legend" x="{self.padding}" y="{legend_y}">'
            "Ligne simple = relation child/parent · Double ligne = relation descendant/ancestor"
            "</text>"
        )
        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    def to_html(
        self,
        title: str = "TreePatternQuery visualisation",
        interactive: bool = True,
        xpath_query: str | None = None,
    ) -> str:
        theme_switch = self._theme_switch_html()
        theme_script = self._theme_switch_script()

        if interactive:
            return self._to_interactive_html(title, xpath_query=xpath_query)
        else:
            svg = self.to_svg()
            query_block = ""
            if xpath_query:
                escaped_query = escape(self._format_xpath_query_for_display(xpath_query))
                query_block = (
                    '<p class="query-label">Requête XPath :</p>'
                    f'<pre class="query-value">{escaped_query}</pre>'
                )
            html_template = Template(
                """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>$title</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f4f7fb;
      --text: #102a43;
      --header-bg: #ffffff;
      --border: #d9e2ec;
      --hint: #486581;
      --panel-bg: #ffffff;
      --query-bg: #f0f4f8;
      --shadow: rgba(16, 42, 67, 0.08);
      --tpq-edge: #334e68;
      --tpq-node-fill: #f7fbff;
      --tpq-node-stroke: #1f4e79;
      --tpq-node-label: #102a43;
      --tpq-legend: #334e68;
      --tpq-title: #102a43;
    }
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme='light']) {
        --bg: #0f1720;
        --text: #e6edf5;
        --header-bg: #111b26;
        --border: #2a3a4a;
        --hint: #9ab1c9;
        --panel-bg: #111b26;
        --query-bg: #172534;
        --shadow: rgba(0, 0, 0, 0.45);
        --tpq-edge: #9ab1c9;
        --tpq-node-fill: #173047;
        --tpq-node-stroke: #88b3de;
        --tpq-node-label: #e6edf5;
        --tpq-legend: #9ab1c9;
        --tpq-title: #e6edf5;
      }
    }
    :root[data-theme='light'] {
      color-scheme: light;
      --bg: #f4f7fb;
      --text: #102a43;
      --header-bg: #ffffff;
      --border: #d9e2ec;
      --hint: #486581;
      --panel-bg: #ffffff;
      --query-bg: #f0f4f8;
      --shadow: rgba(16, 42, 67, 0.08);
      --tpq-edge: #334e68;
      --tpq-node-fill: #f7fbff;
      --tpq-node-stroke: #1f4e79;
      --tpq-node-label: #102a43;
      --tpq-legend: #334e68;
      --tpq-title: #102a43;
    }
    :root[data-theme='dark'] {
      color-scheme: dark;
      --bg: #0f1720;
      --text: #e6edf5;
      --header-bg: #111b26;
      --border: #2a3a4a;
      --hint: #9ab1c9;
      --panel-bg: #111b26;
      --query-bg: #172534;
      --shadow: rgba(0, 0, 0, 0.45);
      --tpq-edge: #9ab1c9;
      --tpq-node-fill: #173047;
      --tpq-node-stroke: #88b3de;
      --tpq-node-label: #e6edf5;
      --tpq-legend: #9ab1c9;
      --tpq-title: #e6edf5;
    }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      padding: 16px 20px 8px;
      background: var(--header-bg);
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .header-top {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      flex-wrap: wrap;
    }
    .header-copy {
      min-width: 0;
    }
    .hint {
      margin: 6px 0 0;
      color: var(--hint);
      font-size: 14px;
    }
    .query-label {
      margin: 10px 0 4px;
      font-size: 12px;
      color: var(--hint);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .query-value {
      margin: 0;
      padding: 10px;
      background: var(--query-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-word;
    }
    main {
      padding: 16px;
      overflow: auto;
    }
    .graph-shell {
      display: inline-block;
      background: var(--panel-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 6px 20px var(--shadow);
      padding: 12px;
    }
    .theme-switch {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--panel-bg);
      box-shadow: 0 2px 8px var(--shadow);
    }
    .theme-switch-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--hint);
      margin-right: 2px;
    }
    .theme-option {
      appearance: none;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text);
      border-radius: 999px;
      padding: 6px 12px;
      font-size: 13px;
      cursor: pointer;
      transition: background 0.2s, color 0.2s, border-color 0.2s;
    }
    .theme-option:hover {
      background: var(--query-bg);
    }
    .theme-option.is-active {
      background: var(--tpq-edge);
      border-color: var(--tpq-edge);
      color: white;
    }
  </style>
</head>
<body>
  <header>
    <div class="header-top">
      <div class="header-copy">
        <strong>$title</strong>
        <p class="hint">Les cercles contiennent les labels. Les traits simples représentent les liens child/parent, les doubles traits les liens descendant/ancestor.</p>
      </div>
      $theme_switch
    </div>
    $query_block
  </header>
  <main>
    <div class="graph-shell">
      $svg
    </div>
  </main>
  <script>
$theme_script
  </script>
</body>
</html>"""
            )
            return html_template.substitute(
                title=escape(title),
                svg=svg,
                query_block=query_block,
                theme_switch=theme_switch,
                theme_script=theme_script,
            )

    def _to_interactive_html(self, title: str, xpath_query: str | None = None) -> str:
        """Generate an interactive HTML/SVG with force-directed layout and animations."""
        import json

        theme_switch = self._theme_switch_html()
        theme_script = self._theme_switch_script()

        # Build node and edge lists for the graph
        nodes_list = []
        edges_list = []
        nodes_by_id = {}
        node_counter = [0]
        output_u1, output_u2 = self.tree_pattern_query.get_output_nodes()

        def traverse(node: QueryNode, depth: int = 0):
            node_id = id(node)
            if node_id in nodes_by_id:
                return nodes_by_id[node_id]

            idx = node_counter[0]
            node_counter[0] += 1
            label = str(node.get_label())
            roles = []
            if node is output_u1:
                roles.append("u1")
            if node is output_u2:
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

        traverse(self.tree_pattern_query.get_root())

        graph_data = json.dumps({"nodes": nodes_list, "edges": edges_list})

        # Provide an editable input in the header so the user can type a query
        query_block = ""
        if xpath_query:
            # show the formatted query inside a textarea so it can be edited
            # keep the pretty-printed display for readability, but allow editing the raw expression
            raw_query = xpath_query
            pretty = escape(self._format_xpath_query_for_display(xpath_query))
            query_block = (
                '<p class="query-label">Requête XPath :</p>'
                f'<textarea id="xpath-input" class="query-value" rows="3">{escape(raw_query)}</textarea>'
                f'<div style="margin-top:8px;"><button id="update-xpath">Mettre à jour</button></div>'
                f'<p class="query-label" style="margin-top:8px;">Requête (mise en forme) :</p>'
                f'<pre class="query-value">{pretty}</pre>'
            )

        html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no" />
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg-start: #f4f7fb;
      --bg-end: #e8f0f8;
      --text: #102a43;
      --header-bg: #ffffff;
      --border: #d9e2ec;
      --hint: #486581;
      --query-bg: #f0f4f8;
      --panel-bg: #ffffff;
      --button-bg: #1f4e79;
      --button-hover: #152f52;
      --canvas-bg: #f4f7fb;
      --edge: #1f4e79;
      --node-fill: #f7fbff;
      --node-stroke: #1f4e79;
      --node-text: #102a43;
      --shadow: rgba(16, 42, 67, 0.15);
    }}
    @media (prefers-color-scheme: dark) {{
      :root:not([data-theme='light']) {{
        --bg-start: #0f1720;
        --bg-end: #101a26;
        --text: #e6edf5;
        --header-bg: #111b26;
        --border: #2a3a4a;
        --hint: #9ab1c9;
        --query-bg: #172534;
        --panel-bg: #111b26;
        --button-bg: #2c5f8f;
        --button-hover: #3a75ad;
        --canvas-bg: #0f1720;
        --edge: #88b3de;
        --node-fill: #173047;
        --node-stroke: #88b3de;
        --node-text: #e6edf5;
        --shadow: rgba(0, 0, 0, 0.45);
      }}
    }}
    :root[data-theme='light'] {{
      color-scheme: light;
      --bg-start: #f4f7fb;
      --bg-end: #e8f0f8;
      --text: #102a43;
      --header-bg: #ffffff;
      --border: #d9e2ec;
      --hint: #486581;
      --query-bg: #f0f4f8;
      --panel-bg: #ffffff;
      --button-bg: #1f4e79;
      --button-hover: #152f52;
      --canvas-bg: #f4f7fb;
      --edge: #1f4e79;
      --node-fill: #f7fbff;
      --node-stroke: #1f4e79;
      --node-text: #102a43;
      --shadow: rgba(16, 42, 67, 0.15);
    }}
    :root[data-theme='dark'] {{
      color-scheme: dark;
      --bg-start: #0f1720;
      --bg-end: #101a26;
      --text: #e6edf5;
      --header-bg: #111b26;
      --border: #2a3a4a;
      --hint: #9ab1c9;
      --query-bg: #172534;
      --panel-bg: #111b26;
      --button-bg: #2c5f8f;
      --button-hover: #3a75ad;
      --canvas-bg: #0f1720;
      --edge: #88b3de;
      --node-fill: #173047;
      --node-stroke: #88b3de;
      --node-text: #e6edf5;
      --shadow: rgba(0, 0, 0, 0.45);
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: linear-gradient(135deg, var(--bg-start) 0%, var(--bg-end) 100%);
      color: var(--text);
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      padding: 16px 20px;
      background: var(--header-bg);
      border-bottom: 1px solid var(--border);
      box-shadow: 0 2px 8px rgba(16, 42, 67, 0.1);
      z-index: 100;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      flex-wrap: wrap;
    }}
    .header-copy {{
      min-width: 0;
    }}
    header h1 {{
      margin: 0 0 8px 0;
      font-size: 20px;
    }}
    .hint {{
      margin: 0;
      font-size: 13px;
      color: var(--hint);
    }}
    .query-label {{
      margin: 10px 0 4px;
      font-size: 12px;
      color: var(--hint);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .query-value {{
      margin: 0;
      padding: 10px;
      background: var(--query-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 120px;
      overflow: auto;
    }}
    main {{
      flex: 1;
      position: relative;
      overflow: hidden;
    }}
    canvas {{
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }}
    canvas:active {{
      cursor: grabbing;
    }}
    .controls {{
      position: absolute;
      bottom: 16px;
      right: 16px;
      background: var(--panel-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      box-shadow: 0 4px 12px var(--shadow);
    }}
    .theme-switch {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--panel-bg);
      box-shadow: 0 2px 8px var(--shadow);
    }}
    .theme-switch-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--hint);
      margin-right: 2px;
    }}
    .theme-option {{
      appearance: none;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text);
      border-radius: 999px;
      padding: 6px 12px;
      font-size: 13px;
      cursor: pointer;
      transition: background 0.2s, color 0.2s, border-color 0.2s;
    }}
    .theme-option:hover {{
      background: var(--query-bg);
    }}
    .theme-option.is-active {{
      background: var(--button-bg);
      border-color: var(--button-bg);
      color: white;
    }}
    button {{
      padding: 8px 16px;
      margin-right: 8px;
      background: var(--button-bg);
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 13px;
      transition: background 0.2s;
    }}
    button:hover {{
      background: var(--button-hover);
    }}
    button:last-child {{
      margin-right: 0;
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-top">
      <div class="header-copy">
        <h1>{escape(title)}</h1>
        <p class="hint">Drag les nœuds pour les déplacer. Traits simples = child/parent · Doubles traits = descendant/ancestor</p>
      </div>
      {theme_switch}
    </div>
    {query_block}
  </header>
  <main>
    <canvas id="graph"></canvas>
    <div class="controls">
      <button onclick="resetAnimation()">Réinitialiser</button>
      <button onclick="toggleAnimation()">Pause/Play</button>
    </div>
  </main>

  <script>
    const canvas = document.getElementById('graph');
    const ctx = canvas.getContext('2d');

{theme_script}

    function readCssVar(name, fallback) {{
      const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return value || fallback;
    }}

    function getThemeColors() {{
      return {{
        canvasBg: readCssVar('--canvas-bg', '#f4f7fb'),
        edge: readCssVar('--edge', '#1f4e79'),
        nodeFill: readCssVar('--node-fill', '#f7fbff'),
        nodeStroke: readCssVar('--node-stroke', '#1f4e79'),
        nodeText: readCssVar('--node-text', '#102a43')
      }};
    }}

    let themeColors = getThemeColors();
    window.refreshThemeColors = () => {{
      themeColors = getThemeColors();
    }};
    window.refreshThemeColors();
    
    // Données du graphe (chargées dynamiquement depuis le serveur)
    let nodes = [];
    let edges = [];
    const initialExpression = {json.dumps(xpath_query or '')};

    async function fetchGraph(expression) {{
      try {{
        const params = new URLSearchParams({{ expression }});
        const resp = await fetch('/graph?' + params.toString());
        if (!resp.ok) {{
          const text = await resp.text();
          alert('Erreur lors de la génération du graphe: ' + resp.status + '\\n' + text);
          return;
        }}
        const data = await resp.json();
        nodes.length = 0;
        edges.length = 0;
        data.nodes.forEach(n => nodes.push(n));
        data.edges.forEach(e => edges.push(e));
        animationState.maxTime = nodes.length * 200;
        initializeLayout();
        resetAnimation();
      }} catch (err) {{
        alert('Erreur réseau: ' + err);
      }}
    }}

    // État de l'animation
    let animationState = {{
      isRunning: true,
      progress: 0,
      maxTime: nodes.length * 200,
      elapsedTime: 0
    }};
    
    // Paramètres du layout
    const params = {{
      nodeRadius: 24,
      friction: 0.82,
      repulsion: 1400,
      attraction: 0.14,
      centralForce: 0.006,
      dampening: 0.88,
      collisionPadding: 12,
      maxSpeed: 7,
      hierarchyForce: 0.11,
      levelGap: 130,
      rootPadding: 42,
      childGap: 106,
      descendantGap: 128,
      settleSpeedThreshold: 0.05,
      settleFrames: 45
    }};
    
    // Initialiser les positions avec un layout radial initial
    function initializeLayout() {{
      const centerX = canvas.width / 2;
      const levelMap = new Map();
      let maxDepth = 0;

      nodes.forEach(node => {{
        const depth = Number.isFinite(node.depth) ? node.depth : 0;
        maxDepth = Math.max(maxDepth, depth);
        if (!levelMap.has(depth)) {{
          levelMap.set(depth, []);
        }}
        levelMap.get(depth).push(node);
      }});

      const availableHeight = Math.max(canvas.height - params.rootPadding * 2, params.levelGap);
      const levelGap = Math.min(params.levelGap, Math.max(params.nodeRadius * 3, availableHeight / Math.max(1, maxDepth + 1)));

      [...levelMap.keys()].sort((a, b) => a - b).forEach(depth => {{
        const row = levelMap.get(depth);
        const y = params.rootPadding + depth * levelGap;
        const spread = Math.max(canvas.width - params.rootPadding * 2, row.length * params.nodeRadius * 3);
        const step = row.length > 1 ? spread / (row.length - 1) : 0;
        const startX = row.length > 1 ? params.rootPadding : centerX;

        row.forEach((node, i) => {{
          node.x = row.length > 1 ? startX + i * step : centerX;
          node.y = y;
          node.targetY = y;
          node.depth = depth;
          node.isPinned = depth === 0;
          node.isFixed = false;
          node.vx = (Math.random() - 0.5) * 1.2;
          node.vy = (Math.random() - 0.5) * 1.2;
          node.appearTime = Math.max(0, nodes.length * 240 - node.index * 70);
          node.isVisible = false;
        }});
      }});
    }}
    
    function resizeCanvas() {{
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      initializeLayout();
    }}
    
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    
    // Simulation physique
    function applyForces() {{
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      
      // Réinitialiser les forces
      nodes.forEach(node => {{
        node.fx = 0;
        node.fy = 0;
      }});
      
      // Forces de répulsion (nœud-nœud)
      for (let i = 0; i < nodes.length; i++) {{
        for (let j = i + 1; j < nodes.length; j++) {{
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.hypot(dx, dy) || 0.1;
          const force = params.repulsion / (dist * dist + 180);
          
          nodes[i].fx -= (dx / dist) * force;
          nodes[i].fy -= (dy / dist) * force;
          nodes[j].fx += (dx / dist) * force;
          nodes[j].fy += (dy / dist) * force;
        }}
      }}
      
      // Forces d'attraction (arêtes)
      edges.forEach(edge => {{
        const source = nodes[edge.source];
        const target = nodes[edge.target];
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.hypot(dx, dy) || 0.1;
        const force = dist * params.attraction;
        
        source.fx += (dx / dist) * force;
        source.fy += (dy / dist) * force;
        target.fx -= (dx / dist) * force;
        target.fy -= (dy / dist) * force;
      }});
      
      // Force vers le centre
      nodes.forEach(node => {{
        const dx = centerX - node.x;
        const dy = centerY - node.y;
        const dist = Math.hypot(dx, dy) || 0.1;
        node.fx += (dx / dist) * params.centralForce;
        node.fy += (dy / dist) * params.centralForce;

        const targetY = Number.isFinite(node.targetY) ? node.targetY : params.rootPadding;
        node.fy += (targetY - node.y) * params.hierarchyForce;
      }});
      
      // Appliquer les forces
      nodes.forEach(node => {{
        if (node.isDragging || node.isFixed) return;
        if (node.isPinned && node.depth === 0) return;
        
        node.vx = (node.vx + node.fx) * params.dampening;
        node.vy = (node.vy + node.fy) * params.dampening;
        
        node.vx *= params.friction;
        node.vy *= params.friction;

        const speed = Math.hypot(node.vx, node.vy);
        if (speed > params.maxSpeed) {{
          const ratio = params.maxSpeed / speed;
          node.vx *= ratio;
          node.vy *= ratio;
        }}
        
        node.x += node.vx;
        node.y += node.vy;
        
        // Limiter aux bords
        const padding = params.nodeRadius + 10;
        node.x = Math.max(padding, Math.min(canvas.width - padding, node.x));
        node.y = Math.max(padding, Math.min(canvas.height - padding, node.y));
      }});

      resolveCollisions();
      enforceHierarchy();
    }}

    function resolveCollisions() {{
      const minDistance = params.nodeRadius * 2 + params.collisionPadding;
      const iterations = 2;

      for (let k = 0; k < iterations; k++) {{
        for (let i = 0; i < nodes.length; i++) {{
          for (let j = i + 1; j < nodes.length; j++) {{
            const a = nodes[i];
            const b = nodes[j];
            if (!a.isVisible || !b.isVisible) continue;
            if (a.isFixed && b.isFixed) continue;

            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let dist = Math.hypot(dx, dy);

            if (dist === 0) {{
              dx = (Math.random() - 0.5) * 0.01;
              dy = (Math.random() - 0.5) * 0.01;
              dist = Math.hypot(dx, dy) || 0.01;
            }}

            if (dist < minDistance) {{
              const overlap = (minDistance - dist) / 2;
              const ux = dx / dist;
              const uy = dy / dist;

              if (!a.isDragging && !a.isFixed) {{
                a.x -= ux * overlap;
                a.y -= uy * overlap;
                a.vx -= ux * overlap * 0.08;
                a.vy -= uy * overlap * 0.08;
              }}

              if (!b.isDragging && !b.isFixed) {{
                b.x += ux * overlap;
                b.y += uy * overlap;
                b.vx += ux * overlap * 0.08;
                b.vy += uy * overlap * 0.08;
              }}
            }}
          }}
        }}
      }}
    }}

    function enforceHierarchy() {{
      const iterations = 2;

      for (let round = 0; round < iterations; round++) {{
        nodes.forEach(node => {{
          if (!node.isVisible || node.isDragging || node.isFixed) return;
          if (node.isPinned && node.depth === 0) {{
            node.y = params.rootPadding;
          }}

          if (node.depth === 0) {{
            node.y = params.rootPadding;
            node.vy = Math.min(node.vy, 0);
          }} else if (Number.isFinite(node.targetY)) {{
            node.y += (node.targetY - node.y) * 0.35;
          }}
        }});

        edges.forEach(edge => {{
          const source = nodes[edge.source];
          const target = nodes[edge.target];
          if (!source.isVisible || !target.isVisible) return;

          const minGap = edge.type === 'descendant' ? params.descendantGap : params.childGap;
          const desiredTop = source.y + minGap;
          if (target.y < desiredTop) {{
            const correction = desiredTop - target.y;
            if (!source.isDragging && !source.isFixed && source.depth > 0) {{
              source.y -= correction * 0.22;
            }} else if (source.depth === 0) {{
              source.y = params.rootPadding;
            }}
            if (!target.isDragging && !target.isFixed) {{
              target.y += correction * 0.78;
            }}
          }}
        }});
      }}

      nodes.forEach(node => {{
        if (node.depth === 0) {{
          node.y = params.rootPadding;
        }}
      }});
    }}

    function isSimulationSettled() {{
      return nodes.every(node => {{
        if (!node.isVisible || node.isDragging) return false;
        const speed = Math.hypot(node.vx || 0, node.vy || 0);
        return speed <= params.settleSpeedThreshold;
      }});
    }}
    
    // Rendu
    function draw() {{
      ctx.fillStyle = themeColors.canvasBg;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Mettre à jour la visibilité des nœuds
      nodes.forEach(node => {{
        if (animationState.elapsedTime >= node.appearTime) {{
          node.isVisible = true;
        }}
      }});
      
      // Dessiner les arêtes
      edges.forEach(edge => {{
        const source = nodes[edge.source];
        const target = nodes[edge.target];
        
        if (!source.isVisible || !target.isVisible) return;
        
        // Calculer les points d'arrivée sur la bordure des cercles
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.hypot(dx, dy) || 0.1;
        const ux = dx / dist;
        const uy = dy / dist;
        
        const x1 = source.x + ux * params.nodeRadius;
        const y1 = source.y + uy * params.nodeRadius;
        const x2 = target.x - ux * params.nodeRadius;
        const y2 = target.y - uy * params.nodeRadius;
        
        ctx.strokeStyle = themeColors.edge;
        ctx.lineWidth = 1.5;
        
        if (edge.type === 'descendant') {{
          // Double ligne pour descendant
          const offsetX = -uy * 4;
          const offsetY = ux * 4;
          
          ctx.beginPath();
          ctx.moveTo(x1 + offsetX, y1 + offsetY);
          ctx.lineTo(x2 + offsetX, y2 + offsetY);
          ctx.stroke();
          
          ctx.beginPath();
          ctx.moveTo(x1 - offsetX, y1 - offsetY);
          ctx.lineTo(x2 - offsetX, y2 - offsetY);
          ctx.stroke();
        }} else {{
          // Ligne simple pour child
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }}
      }});
      
        // Dessiner les nœuds
       nodes.forEach(node => {{
        if (!node.isVisible) return;
        
        // Cercle: si node.roles présent, mettre un fond vert plus visible
        const hasRoles = Array.isArray(node.roles) && node.roles.length > 0;
        if (hasRoles) {{
          ctx.fillStyle = '#7ccf7c';
          ctx.strokeStyle = '#2e8b57';
        }} else {{
          ctx.fillStyle = themeColors.nodeFill;
          ctx.strokeStyle = themeColors.nodeStroke;
        }}
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(node.x, node.y, params.nodeRadius, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();

        // Label
        ctx.fillStyle = themeColors.nodeText;
        ctx.font = 'bold 13px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.label, node.x, node.y);

        // Badges for roles (u1 / u2) drawn as small circles with text
        if (hasRoles) {{
          const badgeRadius = 10;
          let badgeOffset = 0;
          node.roles.forEach((role, i) => {{
            const bx = node.x + params.nodeRadius * 0.65 + badgeOffset;
            const by = node.y - params.nodeRadius * 0.65;
            const color = role === 'u1' ? '#2e8b57' : '#0b9aa6';
            // circle
            ctx.beginPath();
            ctx.fillStyle = color;
            ctx.arc(bx, by, badgeRadius, 0, 2 * Math.PI);
            ctx.fill();
            // text
            ctx.fillStyle = 'white';
            ctx.font = 'bold 10px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(role, bx, by);
            badgeOffset += badgeRadius * 1.8;
          }});
        }}
      }});
    }}
    
    // Gestion du drag
    let draggedNode = null;
    
    canvas.addEventListener('mousedown', (e) => {{
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      nodes.forEach(node => {{
        if (!node.isVisible) return;
        if (node.depth === 0) return;
        const dist = Math.hypot(x - node.x, y - node.y);
        if (dist < params.nodeRadius + 5) {{
          draggedNode = node;
          node.isDragging = true;
          node.isPinned = true;
          node.isFixed = false;
          animationState.isRunning = true;
          animationState.settleCounter = 0;
        }}
      }});
    }});
    
    canvas.addEventListener('mousemove', (e) => {{
      if (!draggedNode) return;
      const rect = canvas.getBoundingClientRect();
      draggedNode.x = e.clientX - rect.left;
      draggedNode.y = e.clientY - rect.top;
      draggedNode.vx = 0;
      draggedNode.vy = 0;
      draggedNode.targetY = draggedNode.y;
    }});
    
    canvas.addEventListener('mouseup', () => {{
      if (draggedNode) {{
        draggedNode.isDragging = false;
        draggedNode.isPinned = true;
        draggedNode.isFixed = true;
        draggedNode.vx = 0;
        draggedNode.vy = 0;
        draggedNode = null;
      }}
    }});
    
    function update() {{
      if (animationState.isRunning) {{
        animationState.elapsedTime += 16;
      }}
      
      applyForces();
      draw();

      if (!draggedNode && isSimulationSettled()) {{
        animationState.settleCounter = (animationState.settleCounter || 0) + 1;
        if (animationState.settleCounter >= params.settleFrames) {{
          animationState.isRunning = false;
        }}
      }} else {{
        animationState.settleCounter = 0;
      }}

      requestAnimationFrame(update);
    }}
    
    function resetAnimation() {{
      animationState.elapsedTime = 0;
      animationState.isRunning = true;
      animationState.settleCounter = 0;
      initializeLayout();
    }}
    
    function toggleAnimation() {{
      animationState.isRunning = !animationState.isRunning;
      if (animationState.isRunning) {{
        animationState.settleCounter = 0;
      }}
    }}

    // Hook for the update button in the header + initial loading
    document.addEventListener('DOMContentLoaded', () => {{
      const btn = document.getElementById('update-xpath');
      const ta = document.getElementById('xpath-input');

      const loadExpression = async (expr) => {{
        await fetchGraph(expr);
        try {{ history.replaceState(null, '', '?expression=' + encodeURIComponent(expr)); }} catch (_) {{}}
      }};

      if (btn) {{
        btn.addEventListener('click', () => {{
          const expr = ta ? ta.value : '';
          loadExpression(expr);
        }});
      }}

      if (ta) {{
        const urlParams = new URLSearchParams(window.location.search);
        const q = urlParams.get('expression') || initialExpression || ta.value || '';
        ta.value = q;
        loadExpression(q);
      }}
    }});
    
    update();
  </script>
</body>
</html>"""
        return html

    def save_svg(self, path: str | Path) -> Path:
        output_path: Path = Path(path)
        output_path.write_text(self.to_svg(), encoding="utf-8")
        return output_path

    def save_html(
        self,
        path: str | Path,
        title: str = "TreePatternQuery visualisation",
        interactive: bool = True,
        xpath_query: str | None = None,
    ) -> Path:
        output_path: Path = Path(path)
        output_path.write_text(
            self.to_html(title=title, interactive=interactive, xpath_query=xpath_query),
            encoding="utf-8",
        )
        return output_path














