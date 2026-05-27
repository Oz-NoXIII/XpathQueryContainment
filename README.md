[![Tests & Quality Checks](https://github.com/Oz-NoXIII/XpathQueryContainment/actions/workflows/tests.yml/badge.svg)](https://github.com/Oz-NoXIII/XpathQueryContainment/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/Oz-NoXIII/XpathQueryContainment/badge.svg?branch=main)](https://coveralls.io/github/Oz-NoXIII/XpathQueryContainment?branch=main)

# XpathQueryContainment - complete webapp user guide

This application lets you work with XPath queries as `TreePatternQuery` (TPQ) graphs, test homomorphisms, and verify query containment.

The project supports two usage modes:
- **HTML file mode** (generate a local visualization file)
- **local webapp mode** (HTTP server + interactive pages)

## 1) Prerequisites

- Python installed (examples below use `python`)
- Python dependency: `lark` (plus test tools from `requirements-dev.txt`)

Install dependencies from the project root:

```powershell
python -m pip install -r requirements-dev.txt
```

## 2) Quick start

### Start the webapp (recommended)

```powershell
python main.py --serve
```

Then open:
- `http://127.0.0.1:8000/`

### Start directly on a specific feature page

```powershell
python main.py --builder
python main.py --containment
python main.py --xml-tree
```

These flags automatically enable server mode (`--serve`) and open:
- `/builder`
- `/containment`
- `/tpq-xml`

### Generate an HTML file only (no server)

```powershell
python main.py --static -o tpq_static.html
```

## 3) Webapp pages and how to use them

## 3.1 Page `/` - TPQ visualizer from XPath

Goal: enter an XPath expression and visualize the corresponding TPQ.

How it works:
- TPQ is rendered as SVG/HTML with interaction (node dragging)
- `light/dark/auto` theme is available
- `child` and `descendant` relations are shown differently

Typical usage:
1. Open `http://127.0.0.1:8000/`
2. Add `?expression=...` in the URL if needed
3. Inspect the graph and drag nodes for readability

Example URL:

```text
http://127.0.0.1:8000/?expression=(self[(lab=a)]/child[(lab=b)])
```

## 3.2 Page `/builder` - BoolTPQ_Lab visual builder

Goal: visually build two graphs (`q1`, `q2`) and verify homomorphism/containment.

Main features:
- add `child` or `descendant` nodes
- rename nodes and delete subtrees
- drag-and-drop node layout
- JSON export/import for each graph
- load sample graph pair
- display found mapping

Recommended workflow:
1. Build `q1` and `q2`
2. Check labels, root, and structure
3. Click **Verify containment**
4. Read the textual result and mapping list

Notes:
- only `child` and `descendant` edges are supported
- each graph must remain a valid tree (one root, no cycles)

## 3.3 Page `/containment` - XPath containment via homomorphisms

Goal: verify `q1 subset q2` (and the reverse) using the TPQ workflow.

Page pipeline:
1. **Transform XPath -> TPQ**
2. **Booleanize** both queries
3. **Check q1 subset q2** or **check q2 subset q1**

What the page displays:
- raw TPQ for `q1` and `q2`
- booleanized TPQs
- search progress (bar + percentage)
- table of attempted `L` combinations
- final result and `Tc` counterexample when needed

Best practices:
- start with simple queries
- review TPQ transformations before running checks
- test both directions to assess equivalence (`q1 subset q2` and `q2 subset q1`)

## 3.4 Page `/tpq-xml` - TPQ versus XML tree homomorphism

Goal: verify whether a TPQ (built from XPath) has a homomorphism into an XML tree.

Recommended workflow:
1. Enter XPath and XML
2. Click **Transform query**
3. Click **Check homomorphism**

Provided results:
- TPQ rendering
- XML tree rendering
- `true/false` result message
- source -> target mapping list
- arrows between mapped nodes

## 4) CLI options (`main.py`)

```powershell
python main.py [expression] [options]
```

Available options:
- `expression` (positional): XPath to analyze (optional)
- `-o`, `--output`: HTML output path in non-server mode
- `--static`: static rendering (no interactive animation)
- `--serve`: start local web server
- `--builder`: open builder page (`/builder`)
- `--containment`: open containment page (`/containment`)
- `--xml-tree`: open TPQ/XML page (`/tpq-xml`)
- `--port`: HTTP port (default `8000`)
- `--no-open`: do not auto-open browser

## 5) Run tests

From the project root:

```powershell
pytest
```

Tests are located in `test/` (see `pytest.ini`).

## 6) Troubleshooting

- **Browser does not open**: run with `--serve` and open the URL manually.
- **Port already in use**: choose another port (`--port 8010`, for example).
- **XPath parsing error**: simplify the query and validate incrementally.
- **Unexpected containment result**: check both directions (`q1 subset q2` and `q2 subset q1`) and inspect booleanized TPQs.

## 7) Useful project structure

- `main.py`: CLI entrypoint + web server
- `controller/`: parsing, transformation, homomorphism/containment logic
- `view/`: HTML/CSS/JS page generation
- `model/`: TPQ data structures
- `grammar/`: Lark grammars
- `test/`: unit and functional tests
