#!/usr/bin/env python3
"""
Build Hypergraph Viewer — embeds hypergraph.json into the standalone HTML viewer.

Usage:
  python docs/build_viewer.py                              # default paths
  python docs/build_viewer.py --graph KB/graph/hypergraph.json --out docs/index.html
  python docs/build_viewer.py --serve                      # build + open in browser

Works with both schemas:
  - Array-based (current TS KB Store)
  - Object-based (Python KB Store from architecture spec)
"""
import json
import sys
import argparse
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DEFAULT_GRAPH = SCRIPT_DIR.parent / "KB" / "graph" / "hypergraph.json"
VIEWER_TEMPLATE = SCRIPT_DIR / "hypergraph-viewer-v3.html"
DEFAULT_OUTPUT = SCRIPT_DIR / "hypergraph-viewer.html"
VIS_JS = SCRIPT_DIR / "vis-network.min.js"


def build(graph_path: Path, output_path: Path, inline_vis: bool = False) -> Path:
    """Embed graph JSON into viewer HTML."""

    if not graph_path.exists():
        print(f"ERROR: Graph not found: {graph_path}")
        sys.exit(1)

    if not VIEWER_TEMPLATE.exists():
        print(f"ERROR: Viewer template not found: {VIEWER_TEMPLATE}")
        sys.exit(1)

    # Load and validate graph
    with open(graph_path, encoding="utf-8") as f:
        graph = json.load(f)

    # Validate minimum structure
    has_nodes = "nodes" in graph
    has_edges = "edges" in graph
    if not has_nodes:
        print("WARNING: No 'nodes' key found in graph JSON")

    # Stats
    if isinstance(graph.get("nodes"), list):
        node_count = len(graph["nodes"])
    elif isinstance(graph.get("nodes"), dict):
        node_count = len(graph["nodes"])
    else:
        node_count = 0

    edge_count = len(graph.get("edges", []))
    he_count = len(graph.get("hyperedges", []))
    alias_count = len(graph.get("alias_index", {}))

    print(f"Graph: {node_count} nodes, {edge_count} edges, {he_count} hyperedges, {alias_count} aliases")

    # Read viewer template
    with open(VIEWER_TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    # Serialize graph as compact JSON
    graph_json = json.dumps(graph, separators=(",", ":"), default=str)

    # Inject graph data BEFORE the DOMContentLoaded listener
    inject_script = f"<script>var GRAPH_DATA={graph_json};</script>\n"

    # If inline_vis requested, embed vis-network.min.js too (fully standalone)
    if inline_vis and VIS_JS.exists():
        with open(VIS_JS, encoding="utf-8") as f:
            vis_code = f.read()
        # Replace the external script tag with inline
        html = html.replace(
            '<script src="vis-network.min.js"></script>',
            f"<script>{vis_code}</script>"
        )
        print("Vis.js inlined for standalone use")

    # Insert graph data script before closing </body>
    html = html.replace("</body>", inject_script + "</body>")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = output_path.stat().st_size / 1024
    print(f"Written: {output_path} ({size_kb:.0f} KB)")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Build Hypergraph Viewer")
    parser.add_argument("--graph", type=str, default=str(DEFAULT_GRAPH),
                        help="Path to hypergraph.json")
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUTPUT),
                        help="Output HTML path")
    parser.add_argument("--inline", action="store_true",
                        help="Inline vis-network.min.js for fully standalone HTML")
    parser.add_argument("--serve", action="store_true",
                        help="Build and open in default browser")
    args = parser.parse_args()

    output = build(Path(args.graph), Path(args.out), inline_vis=args.inline)

    if args.serve:
        url = output.resolve().as_uri()
        print(f"Opening: {url}")
        webbrowser.open(url)


if __name__ == "__main__":
    main()
