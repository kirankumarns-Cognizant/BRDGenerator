"""
Hypergraph Versioning System
=============================
Manages atomic backups, diff tracking, and version history for hypergraph.json.
Implements versioning strategy with:
  - Atomic backup creation before overwriting
  - Diff/comparison logic to track changes between runs
  - Version metadata (run_id, timestamp, change summary)
  - Version history archive
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class HypergraphDiff:
    """Computes and represents differences between two hypergraph versions."""

    def __init__(self, old_graph: Optional[dict], new_graph: dict):
        """
        Args:
            old_graph: Previous hypergraph.json (None if first run)
            new_graph: Current hypergraph.json
        """
        self.old_graph = old_graph or {"nodes": [], "edges": [], "stats": {}}
        self.new_graph = new_graph
        self.changes = self._compute_changes()

    def _compute_changes(self) -> Dict[str, Any]:
        """Compute differences in nodes, edges, and stats."""
        old_nodes = self._index_nodes(self.old_graph.get("nodes", []))
        new_nodes = self._index_nodes(self.new_graph.get("nodes", []))

        old_edges = self._index_edges(self.old_graph.get("edges", []))
        new_edges = self._index_edges(self.new_graph.get("edges", []))

        old_stats = self.old_graph.get("stats", {})
        new_stats = self.new_graph.get("stats", {})

        return {
            "nodes_added": [n for n in new_nodes if n not in old_nodes],
            "nodes_removed": [n for n in old_nodes if n not in new_nodes],
            "nodes_modified": self._find_modified_nodes(old_nodes, new_nodes),
            "edges_added": [e for e in new_edges if e not in old_edges],
            "edges_removed": [e for e in old_edges if e not in new_edges],
            "stats_delta": {
                "node_count": new_stats.get("node_count", 0)
                - old_stats.get("node_count", 0),
                "edge_count": new_stats.get("edge_count", 0)
                - old_stats.get("edge_count", 0),
                "hyperedge_count": new_stats.get("hyperedge_count", 0)
                - old_stats.get("hyperedge_count", 0),
            },
        }

    def _index_nodes(self, nodes: List[dict]) -> List[str]:
        """Index nodes by ID for comparison."""
        if isinstance(nodes, dict):
            return sorted(nodes.keys())
        return sorted([n.get("id", "") for n in nodes])

    def _index_edges(self, edges: List[dict]) -> List[str]:
        """Index edges for comparison (by from-to-type)."""
        edge_keys = []
        for e in edges:
            from_id = e.get("from") or e.get("source", "")
            to_id = e.get("to") or e.get("target", "")
            edge_type = e.get("type") or e.get("edge_type", "")
            edge_keys.append(f"{from_id}→{to_id}({edge_type})")
        return sorted(edge_keys)

    def _find_modified_nodes(self, old_ids: List[str], new_ids: List[str]) -> List[str]:
        """Find nodes that exist in both but may have changed properties."""
        modified = []
        old_nodes_dict = self._get_nodes_dict(self.old_graph.get("nodes", []))
        new_nodes_dict = self._get_nodes_dict(self.new_graph.get("nodes", []))

        for node_id in old_ids:
            if node_id in new_ids:
                old_node = old_nodes_dict.get(node_id, {})
                new_node = new_nodes_dict.get(node_id, {})
                if old_node.get("label") != new_node.get("label"):
                    modified.append(node_id)

        return modified

    def _get_nodes_dict(self, nodes: List[dict]) -> Dict[str, dict]:
        """Convert nodes list to dict indexed by ID."""
        if isinstance(nodes, dict):
            return nodes
        return {n.get("id", ""): n for n in nodes}

    def summary(self) -> str:
        """Return a human-readable summary of changes."""
        lines = []
        changes = self.changes

        if changes["nodes_added"]:
            lines.append(f"+ {len(changes['nodes_added'])} nodes added")
        if changes["nodes_removed"]:
            lines.append(f"- {len(changes['nodes_removed'])} nodes removed")
        if changes["nodes_modified"]:
            lines.append(f"~ {len(changes['nodes_modified'])} nodes modified")

        if changes["edges_added"]:
            lines.append(f"+ {len(changes['edges_added'])} edges added")
        if changes["edges_removed"]:
            lines.append(f"- {len(changes['edges_removed'])} edges removed")

        delta = changes["stats_delta"]
        if delta["node_count"] != 0:
            sign = "+" if delta["node_count"] > 0 else ""
            lines.append(f"nodes: {sign}{delta['node_count']}")
        if delta["edge_count"] != 0:
            sign = "+" if delta["edge_count"] > 0 else ""
            lines.append(f"edges: {sign}{delta['edge_count']}")

        return " | ".join(lines) if lines else "No changes"

    def details(self) -> str:
        """Return detailed change report."""
        lines = ["=== HYPERGRAPH CHANGE REPORT ===\n"]

        changes = self.changes
        if changes["nodes_added"]:
            lines.append(f"NODES ADDED ({len(changes['nodes_added'])}):")
            for node_id in changes["nodes_added"][:10]:
                lines.append(f"  + {node_id}")
            if len(changes["nodes_added"]) > 10:
                lines.append(
                    f"  ... and {len(changes['nodes_added']) - 10} more"
                )
            lines.append("")

        if changes["nodes_removed"]:
            lines.append(f"NODES REMOVED ({len(changes['nodes_removed'])}):")
            for node_id in changes["nodes_removed"][:10]:
                lines.append(f"  - {node_id}")
            if len(changes["nodes_removed"]) > 10:
                lines.append(
                    f"  ... and {len(changes['nodes_removed']) - 10} more"
                )
            lines.append("")

        if changes["edges_added"]:
            lines.append(f"EDGES ADDED ({len(changes['edges_added'])}):")
            for edge_key in changes["edges_added"][:10]:
                lines.append(f"  + {edge_key}")
            if len(changes["edges_added"]) > 10:
                lines.append(
                    f"  ... and {len(changes['edges_added']) - 10} more"
                )
            lines.append("")

        if changes["edges_removed"]:
            lines.append(f"EDGES REMOVED ({len(changes['edges_removed'])}):")
            for edge_key in changes["edges_removed"][:10]:
                lines.append(f"  - {edge_key}")
            if len(changes["edges_removed"]) > 10:
                lines.append(
                    f"  ... and {len(changes['edges_removed']) - 10} more"
                )
            lines.append("")

        return "\n".join(lines)


class VersionManager:
    """Manages versioning, backups, and history for hypergraph.json."""

    def __init__(self, graph_dir: Path):
        """
        Args:
            graph_dir: Path to KB/graph/ directory
        """
        self.graph_dir = Path(graph_dir)
        self.graph_path = self.graph_dir / "hypergraph.json"
        self.backup_path = self.graph_dir / "hypergraph.backup.json"
        self.history_dir = self.graph_dir / "history"
        self.versions_log = self.graph_dir / "versions.json"

        # Create history directory if it doesn't exist
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def create_atomic_backup(self) -> bool:
        """Create atomic backup before overwriting main graph file."""
        if not self.graph_path.exists():
            return False

        try:
            # Atomic backup: write to temp file first, then rename
            temp_backup = self.backup_path.with_suffix(".tmp")
            shutil.copy2(self.graph_path, temp_backup)
            temp_backup.replace(self.backup_path)
            return True
        except Exception as e:
            print(f"WARNING: Failed to create atomic backup: {e}")
            return False

    def save_versioned_graph(
        self, graph: dict, run_id: str, kb_dir: Path, domain_config: Optional[dict] = None
    ) -> Tuple[bool, str]:
        """
        Save graph with version metadata and maintain history.

        Args:
            graph: The hypergraph dict to save
            run_id: Unique identifier for this run
            kb_dir: Path to KB directory (for computing stats)
            domain_config: Optional domain config for metadata

        Returns:
            (success, message)
        """
        try:
            # Load previous graph for diff
            old_graph = None
            if self.graph_path.exists():
                try:
                    with open(self.graph_path, "r", encoding="utf-8") as f:
                        old_graph = json.load(f)
                except Exception:
                    pass

            # Create atomic backup of old version
            self.create_atomic_backup()

            # Compute diff
            diff = HypergraphDiff(old_graph, graph)
            change_summary = diff.summary()

            # Add version metadata
            now = datetime.now(timezone.utc).isoformat()
            graph["version_metadata"] = {
                "run_id": run_id,
                "generated_at": now,
                "created_at": now,
                "change_summary": change_summary,
                "changes_detail": diff.changes,
            }

            # Save main graph
            self.graph_dir.mkdir(parents=True, exist_ok=True)
            with open(self.graph_path, "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, default=str)

            # Save versioned copy to history
            version_filename = f"hypergraph_{run_id}_{now.replace(':', '-')}.json"
            version_path = self.history_dir / version_filename
            with open(version_path, "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, default=str)

            # Update versions log
            self._update_versions_log(run_id, now, change_summary)

            msg = (
                f"Graph saved with version tracking:\n"
                f"  Run ID: {run_id}\n"
                f"  Changes: {change_summary}"
            )
            return True, msg

        except Exception as e:
            return False, f"Failed to save versioned graph: {e}"

    def _update_versions_log(self, run_id: str, timestamp: str, change_summary: str):
        """Update the versions.json log file."""
        try:
            versions = {}
            if self.versions_log.exists():
                with open(self.versions_log, "r", encoding="utf-8") as f:
                    versions = json.load(f)

            versions[run_id] = {
                "timestamp": timestamp,
                "change_summary": change_summary,
            }

            with open(self.versions_log, "w", encoding="utf-8") as f:
                json.dump(versions, f, indent=2)
        except Exception as e:
            print(f"WARNING: Failed to update versions log: {e}")

    def get_version_history(self) -> Dict[str, dict]:
        """Get the complete version history."""
        if not self.versions_log.exists():
            return {}

        try:
            with open(self.versions_log, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_version_details(self, run_id: str) -> Optional[dict]:
        """Get metadata for a specific version."""
        if not self.graph_path.exists():
            return None

        try:
            with open(self.graph_path, "r", encoding="utf-8") as f:
                graph = json.load(f)
                if graph.get("version_metadata", {}).get("run_id") == run_id:
                    return graph.get("version_metadata", {})
        except Exception:
            pass

        return None

    def load_version(self, run_id: str) -> Optional[dict]:
        """Load a specific versioned graph by run_id."""
        if not self.history_dir.exists():
            return None

        try:
            # Find version file matching run_id
            for version_file in sorted(self.history_dir.glob(f"hypergraph_{run_id}_*.json")):
                with open(version_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        return None

    def compare_versions(
        self, run_id_1: str, run_id_2: str
    ) -> Optional[Tuple[HypergraphDiff, str]]:
        """Compare two versions and return diff + report."""
        graph1 = self.load_version(run_id_1)
        graph2 = self.load_version(run_id_2)

        if graph1 is None or graph2 is None:
            return None

        diff = HypergraphDiff(graph1, graph2)
        return diff, diff.details()
