"""
Capability 3: Hypergraph Explorer
Embeds the existing Vis.js hypergraph viewer with GRAPH_DATA injected directly,
so the graph loads instantly without a file picker.
"""

import copy
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import uuid

import streamlit as st

# Import versioning system and query engine
sys.path.insert(0, str(Path(__file__).parent.parent))
from hypergraph.versioning import VersionManager, HypergraphDiff
from hypergraph_query_engine import HypergraphQueryEngine


# ── Query engine (cached) ────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _load_query_engine(graph_path: str) -> HypergraphQueryEngine | None:
    p = Path(graph_path)
    if not p.exists():
        return None
    try:
        return HypergraphQueryEngine(str(p))
    except Exception:
        return None


# ── Graph loading (cached, refreshes every 60 s) ──────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _load_graph(graph_path: str) -> dict | None:
    p = Path(graph_path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _graph_path(project_root: Path) -> Path:
    return project_root / "KB" / "graph" / "hypergraph.json"


def _artifact_preview_text(file_path: Path, max_chars: int | None = None) -> str | None:
    if not file_path.exists():
        return "[Artifact file not found]"

    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    text = text.strip()
    if not text:
        return "[Artifact file exists but contains no generated content yet]"

    return text


def _artifact_candidate_paths(properties: dict, node_id: str, project_root: Path) -> list[Path]:
    """Build candidate artifact paths from explicit file_path and predictable KB naming."""
    candidates: list[Path] = []

    # 1) Primary source: explicit file_path from graph node.
    file_path = properties.get("file_path")
    if isinstance(file_path, str) and file_path.strip():
        p = Path(file_path)
        candidates.append(p if p.is_absolute() else project_root / p)

    # 2) Fallbacks derived from repo + artifact_type naming conventions.
    repo_name = properties.get("repo_name")
    if not repo_name and node_id.startswith("artifact_"):
        parts = node_id.split("-")
        # artifact_<repo-name>-<artifact-type>
        if len(parts) >= 3:
            repo_name = "-".join(parts[1:-2]) if len(parts) > 4 else "-".join(parts[1:-1])

    artifact_type = properties.get("artifact_type")
    if isinstance(repo_name, str) and repo_name.strip() and isinstance(artifact_type, str) and artifact_type.strip():
        repo_dir = project_root / "KB" / repo_name
        stem = artifact_type.strip()
        # Typical artifact files are json, markdown, or gherkin feature files.
        for ext in (".json", ".md", ".feature"):
            candidates.append(repo_dir / f"{stem}{ext}")

    # Deduplicate while preserving order.
    seen: set[str] = set()
    unique_candidates: list[Path] = []
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique_candidates.append(path)

    return unique_candidates


def _enrich_graph_for_viewer(graph: dict, project_root: Path) -> dict:
    enriched = copy.deepcopy(graph)

    for node in enriched.get("nodes", []):
        if node.get("type") != "artifact":
            continue

        properties = node.setdefault("properties", {})
        candidates = _artifact_candidate_paths(properties, str(node.get("id", "")), project_root)
        resolved_path = next((p for p in candidates if p.exists()), None)

        if resolved_path is None:
            properties["artifact_exists"] = False
            if candidates:
                properties["artifact_preview"] = (
                    "[Artifact file not found]\nTried:\n" + "\n".join(str(p) for p in candidates[:5])
                )
            else:
                properties["artifact_preview"] = "[Artifact file path metadata missing]"
            continue

        preview = _artifact_preview_text(resolved_path)
        properties["artifact_exists"] = True
        properties["resolved_file_path"] = str(resolved_path)
        properties["artifact_preview"] = preview or "[Unable to read artifact content]"

    return enriched


# ── HTML assembly ─────────────────────────────────────────────────────────────

def _build_embedded_html(graph: dict, viewer_dir: Path, target_node: str | None = None) -> str:
    """
    Read the standalone vis.js HTML viewer and:
    1. Inline vis-network.min.js (avoids relative-path issues inside st.components)
    2. Inject GRAPH_DATA so initFromEmbedded() boots without the file picker
    3. Optionally inject TARGET_NODE for navigation to a specific node
    """
    html_path = viewer_dir / "hypergraph-viewer-v3.html"
    vis_js_path = viewer_dir / "vis-network.min.js"

    html = html_path.read_text(encoding="utf-8")
    vis_js = vis_js_path.read_text(encoding="utf-8")

    # Remove any hardcoded graph payload from the template to avoid stale/demo data conflicts.
    html = re.sub(
        r"<script>\s*var\s+GRAPH_DATA\s*=.*?</script>",
        "",
        html,
        flags=re.DOTALL,
    )

    # Replace relative <script src="vis-network.min.js"> with inlined script
    html = html.replace(
        '<script src="vis-network.min.js"></script>',
        f"<script>{vis_js}</script>",
    )

    # Inject graph data before </body> — viewer checks typeof GRAPH_DATA !== 'undefined'
    graph_script = f"<script>var GRAPH_DATA = {json.dumps(graph)};"
    if target_node:
        graph_script += f"var TARGET_NODE = {json.dumps(target_node)};"
    graph_script += "</script>"
    html = html.replace("</body>", f"{graph_script}\n</body>")

    return html


# ── Regeneration helper ───────────────────────────────────────────────────────

def _regenerate(project_root: Path) -> tuple[bool, str]:
    """Run generate_hypergraph.py and return (success, message)."""
    script = project_root / "generate_hypergraph.py"
    kb_dir = str(project_root / "KB")
    out = str(project_root / "KB" / "graph" / "hypergraph.json")
    domain_config = str(project_root / "domain_config.json")
    run_id = str(uuid.uuid4())[:8]  # Generate run ID for versioning

    cmd = [sys.executable, str(script), "--kb", kb_dir, "--out", out, "--run-id", run_id]
    if Path(domain_config).exists():
        cmd.extend(["--domain-config", domain_config])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(project_root),
    )
    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, (result.stdout + result.stderr).strip()


def _render_version_info(project_root: Path, graph: dict) -> None:
    """Display version metadata and history."""
    graph_dir = project_root / "KB" / "graph"
    version_mgr = VersionManager(graph_dir)

    # Get current version metadata
    version_meta = graph.get("version_metadata", {})
    run_id = version_meta.get("run_id", "unknown")
    generated_at = version_meta.get("generated_at", "")
    change_summary = version_meta.get("change_summary", "No changes")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Run ID", run_id[:12])
    with col2:
        st.metric("Change Summary", change_summary.split("|")[0].strip() if "|" in change_summary else "—")
    with col3:
        if generated_at:
            dt = datetime.fromisoformat(generated_at)
            st.metric("Generated", dt.strftime("%Y-%m-%d %H:%M"))

    # Version history
    with st.expander("📜 Version History & Comparison"):
        history = version_mgr.get_version_history()

        if history:
            st.write(f"**Total versions: {len(history)}**")

            # Create sortable list of versions
            versions_list = sorted(
                history.items(),
                key=lambda x: x[1].get("timestamp", ""),
                reverse=True
            )

            cols = st.columns([2, 3, 3])
            with cols[0]:
                st.write("**Run ID**")
            with cols[1]:
                st.write("**Timestamp**")
            with cols[2]:
                st.write("**Changes**")

            for v_run_id, v_meta in versions_list[:10]:
                cols = st.columns([2, 3, 3])
                with cols[0]:
                    st.code(v_run_id[:12], language=None)
                with cols[1]:
                    ts = v_meta.get("timestamp", "")
                    if ts:
                        dt = datetime.fromisoformat(ts)
                        st.text(dt.strftime("%Y-%m-%d %H:%M"))
                with cols[2]:
                    st.caption(v_meta.get("change_summary", "—"))

            if len(versions_list) > 10:
                st.caption(f"Showing 10 of {len(versions_list)} versions")

        else:
            st.info("No version history yet. Generate hypergraph to create versions.")


def _build_tech_stack_graph(graph: dict, viewer_dir: Path, project_root: Path = None) -> str:
    """
    Create a filtered hypergraph showing technology nodes, repos, and shared domains.
    Highlights code reuse opportunities where repos share domains and tech stacks.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Load domain info to identify shared code opportunities
    shared_repos = set()

    try:
        if project_root:
            import json
            with open(project_root / "domain_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)

            repo_to_domain = {k: v for k, v in config.items() if k != "tech_stack_info"}
            domain_to_repos = {}
            for repo, domain in repo_to_domain.items():
                if domain not in domain_to_repos:
                    domain_to_repos[domain] = []
                domain_to_repos[domain].append(repo)

            # Find repos with shared domains
            for domain, repos in domain_to_repos.items():
                if len(repos) > 1:
                    shared_repos.update(repos)
    except:
        pass

    # Get technology nodes
    tech_nodes = [n for n in nodes if n.get("type") == "technology"]
    tech_ids = set(n.get("id") for n in tech_nodes)

    # Get all uses_technology edges to find connected repos
    tech_edges = [e for e in edges if e.get("type") == "uses_technology"]
    connected_repo_ids = set(e.get("from", "") for e in tech_edges)

    # Get domain nodes that have feature children (better filtering)
    domain_nodes = [n for n in nodes if n.get("type") == "domain"]
    domain_to_repos_graph = {}
    for e in edges:
        if e.get("type") == "belongs_to_domain":
            domain_id = e.get("to", "")
            repo_id = e.get("from", "")
            if domain_id not in domain_to_repos_graph:
                domain_to_repos_graph[domain_id] = []
            domain_to_repos_graph[domain_id].append(repo_id)

    # Get feature nodes connected to techs
    feature_nodes = [n for n in nodes if n.get("type") == "feature" and n.get("id") in connected_repo_ids]

    # Highlight shared repos
    for fn in feature_nodes:
        repo_name = fn.get("label", "")
        if any(shared_repo in repo_name for shared_repo in shared_repos):
            if "properties" not in fn:
                fn["properties"] = {}
            fn["properties"]["shared_domain"] = True

    # Get domain nodes that connect to our repos
    feature_ids = set(n.get("id") for n in feature_nodes)
    relevant_domain_ids = set()
    for domain_id, repo_ids in domain_to_repos_graph.items():
        if any(rid in feature_ids for rid in repo_ids):
            relevant_domain_ids.add(domain_id)

    domain_nodes_filtered = [n for n in domain_nodes if n.get("id") in relevant_domain_ids]

    # Collect all nodes to keep
    all_node_ids = tech_ids | feature_ids | relevant_domain_ids

    # Get all edges that connect our kept nodes
    filtered_edges = [
        e for e in edges
        if (e.get("from") in all_node_ids and e.get("to") in all_node_ids)
    ]

    # Create filtered graph
    filtered_graph = {
        "$schema": "hypergraph/v1",
        "generated_at": graph.get("generated_at", ""),
        "nodes": tech_nodes + feature_nodes + domain_nodes_filtered,
        "edges": filtered_edges,
        "hyperedges": [],
        "alias_index": {},
        "stats": {
            "node_count": len(tech_nodes) + len(feature_nodes) + len(domain_nodes_filtered),
            "edge_count": len(filtered_edges),
            "hyperedge_count": 0,
        },
    }

    return _build_embedded_html(filtered_graph, viewer_dir)


def _show_version_modal(project_root: Path, graph: dict) -> None:
    """Display version history modal when button is clicked."""
    if not st.session_state.get("show_version_modal", False):
        return

    graph_dir = project_root / "KB" / "graph"
    version_mgr = VersionManager(graph_dir)
    history = version_mgr.get_version_history()

    st.divider()
    st.subheader("📊 Version History & Comparison")

    if not history:
        st.info("No version history yet.")
        return

    # Get current version
    current_run_id = graph.get("version_metadata", {}).get("run_id", "unknown")

    # Create three-column version comparison interface
    st.write(f"**Total versions: {len(history)}**")

    # Version selection dropdowns
    col1, col2, col3 = st.columns([2, 2, 2])

    versions_list = sorted(history.keys(), key=lambda x: history[x].get("timestamp", ""), reverse=True)

    with col1:
        selected_v1 = st.selectbox(
            "Version 1",
            versions_list,
            index=0,
            format_func=lambda x: f"{x[:12]} ({history[x].get('timestamp', '')[:10]})",
            key="v1_select"
        )

    with col2:
        st.write("")  # Spacer
        st.write("**vs**")

    with col3:
        # Set Version 2 to second most recent by default
        default_v2_idx = 1 if len(versions_list) > 1 else 0
        selected_v2 = st.selectbox(
            "Version 2",
            versions_list,
            index=default_v2_idx,
            format_func=lambda x: f"{x[:12]} ({history[x].get('timestamp', '')[:10]})",
            key="v2_select"
        )

    if st.button("Compare Versions", use_container_width=True):
        # Load graphs
        g1 = version_mgr.load_version(selected_v1)
        g2 = version_mgr.load_version(selected_v2)

        if g1 is None or g2 is None:
            st.error("Could not load selected versions.")
            return

        # Compute diff
        diff = HypergraphDiff(g1, g2)
        changes = diff.changes

        # Display comparison
        st.write(f"**Comparing {selected_v1[:12]} → {selected_v2[:12]}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Nodes Added", len(changes["nodes_added"]))
        with col2:
            st.metric("Nodes Removed", len(changes["nodes_removed"]))
        with col3:
            st.metric("Edges Added", len(changes["edges_added"]))
        with col4:
            st.metric("Edges Removed", len(changes["edges_removed"]))

        # Detailed report
        with st.expander("Detailed Change Report"):
            st.text(diff.details())

    st.divider()

    # Show all versions in table format
    st.write("**All Versions:**")
    cols = st.columns([2, 3, 4, 2])
    with cols[0]:
        st.write("**Run ID**")
    with cols[1]:
        st.write("**Timestamp**")
    with cols[2]:
        st.write("**Changes**")
    with cols[3]:
        st.write("**Status**")

    for v_run_id in versions_list:
        v_meta = history[v_run_id]
        cols = st.columns([2, 3, 4, 2])

        with cols[0]:
            if v_run_id == current_run_id:
                st.markdown(f"**{v_run_id[:12]}** ✓")
            else:
                st.code(v_run_id[:12], language=None)

        with cols[1]:
            ts = v_meta.get("timestamp", "")
            if ts:
                dt = datetime.fromisoformat(ts)
                st.text(dt.strftime("%Y-%m-%d %H:%M"))

        with cols[2]:
            st.caption(v_meta.get("change_summary", "—"))

        with cols[3]:
            if v_run_id == current_run_id:
                st.write("Current")


# ── Helper functions ──────────────────────────────────────────────────────────

def _find_shared_hub_nodes(graph: dict) -> list[str]:
    """Return technology node IDs used by more than one repository/feature."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    tech_ids = {n.get("id") for n in nodes if n.get("type") == "technology"}
    if not tech_ids:
        return []

    tech_to_repos: dict[str, set[str]] = {}
    for edge in edges:
        if edge.get("type") != "uses_technology":
            continue

        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")

        if target in tech_ids and source:
            tech_to_repos.setdefault(target, set()).add(source)

    return sorted([tech_id for tech_id, repos in tech_to_repos.items() if len(repos) > 1])


# ── Render ────────────────────────────────────────────────────────────────────

def render(project_root: Path) -> None:
    # Make tab text orange (matching visualization)
    st.markdown("""
    <style>
    [data-baseweb="tab"] {
        color: #FF9500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("🕸️ Hypergraph Explorer")
    st.caption(
        "Interactive knowledge graph of all BRD artifacts across analyzed repositories. "
        "Use the viewer's search, filter, and cluster controls to explore relationships. "
        "[JSON viewer v2 — full content, no truncation]"
    )

    viewer_dir = project_root / "hypergraph" / "viewer"
    gpath = _graph_path(project_root)

    # ── Controls row ──────────────────────────────────────────────────────────
    col_regen, col_version, col_stats = st.columns([1.5, 1.5, 5])

    with col_regen:
        if st.button("🔄 Regenerate", help="Re-scan KB/ and rebuild hypergraph.json", use_container_width=True):
            with st.spinner("Scanning KB artifacts…"):
                ok, msg = _regenerate(project_root)
            if ok:
                _load_graph.clear()
                st.success("Hypergraph regenerated.")
            else:
                st.error(f"Generation failed:\n{msg}")
            st.rerun()

    with col_version:
        if st.button("📜 Version History", help="View and compare hypergraph versions", use_container_width=True):
            st.session_state.show_version_modal = True

    # ── Load graph ────────────────────────────────────────────────────────────
    graph = _load_graph(str(gpath))

    if graph is None:
        with col_stats:
            st.info(
                "No `KB/graph/hypergraph.json` found. "
                "Click **Regenerate Hypergraph** to build it from your KB artifacts."
            )
        return

    stats = graph.get("stats", {})
    alias_count = len(graph.get("alias_index", {}))

    graph = _enrich_graph_for_viewer(graph, project_root)

    with col_stats:
        m1, m2, m3 = st.columns(3)
        m1.metric("Nodes", stats.get("node_count", 0))
        m2.metric("Edges", stats.get("edge_count", 0))
        m3.metric("Search Aliases", alias_count)

    # ── Version Modal (if button clicked) - Display below buttons ────────────────
    _show_version_modal(project_root, graph)

    # ── Check viewer assets ───────────────────────────────────────────────────
    html_path = viewer_dir / "hypergraph-viewer-v3.html"
    vis_js_path = viewer_dir / "vis-network.min.js"

    if not html_path.exists() or not vis_js_path.exists():
        st.error(
            f"Viewer assets not found in `{viewer_dir}`. "
            "Expected `hypergraph-viewer-v3.html` and `vis-network.min.js`."
        )
        return

    # ── Build and embed the viewer ────────────────────────────────────────────
    try:
        embedded_html = _build_embedded_html(graph, viewer_dir, None)
    except Exception as exc:
        st.error(f"Failed to build viewer: {exc}")
        return

    st.divider()

    # Display using components.html (iframe-based, more reliable)
    import streamlit.components.v1 as components
    import hashlib
    html_hash = hashlib.md5(embedded_html.encode("utf-8", errors="ignore")).hexdigest()[:12]
    # Prepend a unique comment so any content change forces Streamlit to re-embed the iframe
    embedded_html = f"<!-- v2-{html_hash} -->\n" + embedded_html
    components.html(embedded_html, height=900, scrolling=True)

    st.divider()

    # ── Enhanced Statistics & Pattern Distribution ────────────────────────────
    st.markdown("# 📊 Hypergraph Statistics", unsafe_allow_html=False)

    engine = _load_query_engine(str(gpath))
    if engine:
        stats = engine.get_stats()

        # Display stats in columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Repos", stats["unique_repos"])
        with col2:
            st.metric("Cross-Repo Patterns", stats["cross_repo_patterns"])
        with col3:
            st.metric("Total Nodes", stats["total_nodes"])
        with col4:
            st.metric("Total Edges", stats["total_edges"])

        # Pattern type and confidence summary
        if stats["pattern_types"]:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Pattern Types:**")
                for ptype, count in sorted(stats["pattern_types"].items(), key=lambda x: x[1], reverse=True):
                    st.write(f"- {ptype or 'unknown'}: {count}")
            with col2:
                st.write("**Confidence Levels:**")
                for conf, count in sorted(stats["confidence_distribution"].items(), key=lambda x: x[1], reverse=True):
                    st.write(f"- {conf}: {count}")

        st.divider()
