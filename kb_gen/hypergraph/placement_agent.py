"""
PlacementAgent — LLM-driven hypergraph node placement (Gap 3).

Spec: when an artifact arrives, the placement agent receives the artifact content
and metadata and makes one of five decisions:
  1. PLACE_IN_EXISTING  — artifact belongs to an existing feature-group node
  2. CREATE_NEW_NODE    — artifact covers a new feature not yet in the hypergraph
  3. CREATE_HYPEREDGE   — artifact spans multiple existing nodes (bridge artifact)
  4. TEMP_NODE          — cannot classify confidently; create TEMP node + notification
  5. MERGE_PROPOSAL     — artifact appears to be the same concept as an existing node

Feature-group nodes are stored in the hypergraph with node_id prefix "fg_" and have a
special "type" field of "feature_group". Individual artifact nodes keep their artifact_id
as the key. The placement agent creates/updates feature-group nodes and edges that link
artifact nodes to their feature group.
"""
import json
import time
from typing import Dict, List, Optional, Tuple

from kb_gen.utils.api_client import get_anthropic_client, sanitize_error
from kb_gen.utils.notifications import NotificationWriter


PLACEMENT_SYSTEM = """You are a knowledge base placement agent. Your job is to decide
where a new artifact belongs in the knowledge base hypergraph.
Respond ONLY in valid JSON. No preamble. No markdown fences."""

PLACEMENT_PROMPT = """A new artifact has arrived. Decide its placement in the knowledge base.

ARTIFACT METADATA:
  name:          {name}
  artifact_type: {artifact_type}
  brand:         {brand}
  domain:        {domain}
  feature:       {feature}
  service:       {service}
  tags:          {tags}
  description:   {description}

EXISTING FEATURE-GROUP NODES (first 30):
{node_list}

Choose ONE of these decisions:
  PLACE_IN_EXISTING  — clearly fits an existing node
  CREATE_NEW_NODE    — covers a new feature not yet in any node
  CREATE_HYPEREDGE   — bridges 2+ existing nodes (cross-feature / cross-brand)
  TEMP_NODE          — genuinely ambiguous; cannot decide with confidence
  MERGE_PROPOSAL     — appears to be a duplicate/variant of an existing node

Respond with ONLY this JSON:
{{
  "decision": "PLACE_IN_EXISTING|CREATE_NEW_NODE|CREATE_HYPEREDGE|TEMP_NODE|MERGE_PROPOSAL",
  "target_node_id": "existing fg_... node_id if PLACE_IN_EXISTING or MERGE_PROPOSAL, else empty",
  "new_node_label": "human-readable label if CREATE_NEW_NODE, else empty",
  "new_node_id":    "fg_brand_domain_feature slug if CREATE_NEW_NODE, else empty",
  "bridge_node_ids": ["node_id1", "node_id2"] ,
  "reasoning":      "one sentence explaining the decision",
  "confidence":     "HIGH|MEDIUM|LOW"
}}"""


def _slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", text.lower().strip()).strip("_")


class PlacementAgent:
    """Makes LLM-driven placement decisions for incoming artifacts."""

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        notifications_path: str = "KB/graph/notifications.json",
    ):
        self.model = model
        self._client = None
        self._notifier = NotificationWriter(notifications_path)

    def _get_client(self):
        if self._client is None:
            self._client = get_anthropic_client()
        return self._client

    def place(self, artifact_id: str, metadata: Dict, hypergraph) -> Dict:
        """Run placement for one artifact. Modifies hypergraph in-place.

        Returns the placement result dict with keys:
          decision, target_node_id, reasoning, confidence, notification_id (if any).
        Never raises — always returns a result dict (with TEMP_NODE on failure).
        """
        existing_nodes = self._get_feature_group_nodes(hypergraph)
        node_list = self._format_node_list(existing_nodes)

        prompt = PLACEMENT_PROMPT.format(
            name=metadata.get("name", ""),
            artifact_type=metadata.get("artifact_type", ""),
            brand=metadata.get("brand", ""),
            domain=metadata.get("domain", ""),
            feature=metadata.get("feature", ""),
            service=metadata.get("service", ""),
            tags=", ".join(metadata.get("tags", [])),
            description=metadata.get("description", "")[:300],
            node_list=node_list,
        )

        decision_data = self._call_llm(prompt, artifact_id, metadata)
        self._apply_decision(artifact_id, metadata, hypergraph, decision_data, existing_nodes)
        return decision_data

    # ── LLM call ────────────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str, artifact_id: str, metadata: Dict) -> Dict:
        for attempt in range(3):
            try:
                client = self._get_client()
                resp = client.messages.create(
                    model=self.model,
                    max_tokens=512,
                    system=PLACEMENT_SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text.strip()
                if raw.startswith("```"):
                    parts = raw.split("```")
                    raw = parts[1][4:] if parts[1].startswith("json") else parts[1]
                return json.loads(raw.strip())
            except Exception as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    print(f"  [WARN] PlacementAgent LLM failed: {sanitize_error(str(exc))}")
        # Fallback: TEMP_NODE
        return {
            "decision": "TEMP_NODE",
            "target_node_id": "",
            "new_node_label": "",
            "new_node_id": "",
            "bridge_node_ids": [],
            "reasoning": "LLM unavailable — defaulting to TEMP_NODE",
            "confidence": "LOW",
        }

    # ── Decision application ─────────────────────────────────────────────────────

    def _apply_decision(
        self,
        artifact_id: str,
        metadata: Dict,
        hypergraph,
        decision: Dict,
        existing_nodes: Dict,
    ) -> None:
        d = decision.get("decision", "TEMP_NODE")

        if d == "PLACE_IN_EXISTING":
            self._place_in_existing(artifact_id, metadata, hypergraph, decision, existing_nodes)
        elif d == "CREATE_NEW_NODE":
            self._create_new_node(artifact_id, metadata, hypergraph, decision)
        elif d == "CREATE_HYPEREDGE":
            self._create_hyperedge(artifact_id, metadata, hypergraph, decision)
            self._write_notification("NEW_HYPEREDGE_REVIEW", artifact_id, metadata, decision, "MEDIUM")
        elif d == "MERGE_PROPOSAL":
            self._place_in_existing(artifact_id, metadata, hypergraph, decision, existing_nodes)
            self._write_notification("MERGE_PROPOSAL", artifact_id, metadata, decision, "MEDIUM")
        else:  # TEMP_NODE or fallback
            self._create_temp_node(artifact_id, metadata, hypergraph, decision)
            self._write_notification("TEMP_NODE_REVIEW", artifact_id, metadata, decision, "LOW")

    def _place_in_existing(
        self, artifact_id: str, metadata: Dict, hypergraph, decision: Dict, existing_nodes: Dict
    ) -> None:
        target = decision.get("target_node_id", "")
        if not target or target not in existing_nodes:
            # LLM hallucinated a node; fall back to CREATE_NEW_NODE
            self._create_new_node(artifact_id, metadata, hypergraph, decision)
            return
        node = existing_nodes[target]
        art_ids = node.setdefault("artifact_ids", [])
        if artifact_id not in art_ids:
            art_ids.append(artifact_id)
        hypergraph._data["nodes"][target] = node
        hypergraph.add_edge(artifact_id, target, edge_type="informs")
        hypergraph._save()

    def _create_new_node(
        self, artifact_id: str, metadata: Dict, hypergraph, decision: Dict
    ) -> None:
        brand = metadata.get("brand", "UNKNOWN")
        domain = metadata.get("domain", "unknown")
        feature = metadata.get("feature", "") or decision.get("new_node_label", "unknown")
        node_id = decision.get("new_node_id") or f"fg_{_slugify(brand)}_{_slugify(domain)}_{_slugify(feature)}"

        node = {
            "node_id": node_id,
            "type": "feature_group",
            "label": decision.get("new_node_label") or f"{brand} {domain} {feature}",
            "brand": brand,
            "domain": domain,
            "feature": feature,
            "artifact_ids": [artifact_id],
            "status": "ACTIVE",
            "created_by": "placement_agent",
            "human_reviewed": False,
        }
        hypergraph._data["nodes"][node_id] = node
        hypergraph.add_edge(artifact_id, node_id, edge_type="informs")
        # Index node aliases
        hypergraph._update_alias_index(node_id, {
            "service": domain, "domain": domain, "feature": feature,
            "brand": brand, "artifact_type": "feature_group", "tags": [feature, domain, brand],
        })
        hypergraph._save()

    def _create_hyperedge(
        self, artifact_id: str, metadata: Dict, hypergraph, decision: Dict
    ) -> None:
        bridge_ids = decision.get("bridge_node_ids", [])
        # Place in first bridge node and create edges to others
        if bridge_ids:
            hypergraph.add_edge(artifact_id, bridge_ids[0], edge_type="informs")
            for nid in bridge_ids[1:]:
                hypergraph.add_edge(bridge_ids[0], nid, edge_type="related")
        hypergraph._save()

    def _create_temp_node(
        self, artifact_id: str, metadata: Dict, hypergraph, decision: Dict
    ) -> None:
        from kb_gen.utils.artifact_id import generate_artifact_id
        temp_id = f"TEMP_{generate_artifact_id()}"
        node = {
            "node_id": temp_id,
            "type": "feature_group",
            "label": f"TEMP — {metadata.get('name', artifact_id)}",
            "artifact_ids": [artifact_id],
            "status": "TEMP",
            "placement_context": decision.get("reasoning", ""),
            "is_temp": True,
            "human_reviewed": False,
            "created_by": "placement_agent",
        }
        hypergraph._data["nodes"][temp_id] = node
        hypergraph.add_edge(artifact_id, temp_id, edge_type="related")
        hypergraph._save()

    # ── Notifications ────────────────────────────────────────────────────────────

    def _write_notification(
        self, notif_type: str, artifact_id: str, metadata: Dict, decision: Dict, priority: str
    ) -> None:
        self._notifier.write(
            notif_type=notif_type,
            artifact_id=artifact_id,
            artifact_name=metadata.get("name", artifact_id),
            placement_context=decision.get("reasoning", ""),
            candidate_nodes=[{"node_id": decision.get("target_node_id", "")}],
            recommended_action=f"Review placement decision: {decision.get('decision', '')}",
            priority=priority,
        )

    # ── Helpers ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_feature_group_nodes(hypergraph) -> Dict:
        return {
            nid: node
            for nid, node in hypergraph._data.get("nodes", {}).items()
            if node.get("type") == "feature_group"
        }

    @staticmethod
    def _format_node_list(nodes: Dict) -> str:
        if not nodes:
            return "(none — this will be the first feature-group node)"
        lines = []
        for nid, node in list(nodes.items())[:30]:
            label = node.get("label", nid)
            brand = node.get("brand", "")
            domain = node.get("domain", "")
            count = len(node.get("artifact_ids", []))
            lines.append(f"  {nid}: {label} | brand={brand} domain={domain} artifacts={count}")
        return "\n".join(lines)
