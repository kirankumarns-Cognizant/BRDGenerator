"""
HypergraphQueryEngine - Query interface for hypergraph.json
Provides 6 query methods to explore cross-repo patterns, technologies, and business concepts.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class HypergraphQueryEngine:
    """Query engine for hypergraph.json with support for technology, entity, and pattern queries."""

    def __init__(self, hypergraph_path: str):
        """Initialize with path to hypergraph.json"""
        with open(hypergraph_path, "r", encoding="utf-8") as f:
            self.graph = json.load(f)
        self.alias_index = self.graph.get("alias_index", {})
        self.nodes = {n["id"]: n for n in self.graph.get("nodes", [])}
        self.edges = self.graph.get("edges", [])
        self.hyperedges = self.graph.get("hyperedges", [])

    def query_shared_dependencies(self, tech_keyword: str) -> List[Dict]:
        """
        Find repos sharing a technology family.

        Args:
            tech_keyword: Technology name (e.g., "spring", "h2", "logging")

        Returns:
            List of matching patterns sorted by confidence and repo count
        """
        patterns = []
        for hedge in self.hyperedges:
            if hedge.get("type") == "cross_repo_pattern":
                props = hedge.get("properties", {})
                if props.get("pattern_type") == "shared_dependency":
                    label = hedge.get("label", "").lower()
                    if tech_keyword.lower() in label:
                        patterns.append({
                            "id": hedge["id"],
                            "pattern": hedge.get("label", ""),
                            "repos": props.get("repos", []),
                            "confidence": props.get("confidence", "UNKNOWN"),
                            "evidence": props.get("evidence", []),
                            "repo_count": len(props.get("repos", [])),
                        })

        # Sort by confidence (HIGH first), then by repo count
        confidence_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        return sorted(patterns, key=lambda x: (
            confidence_priority.get(x["confidence"], 3),
            -x["repo_count"]
        ))

    def query_entity_relationships(self, entity_name: str) -> Dict:
        """
        Find business concepts across repos via entity nodes.

        Args:
            entity_name: Entity concept (e.g., "approval", "notification")

        Returns:
            Dict with matched entity nodes and their relationships
        """
        # Find matching entities in alias index
        matching_nodes = []
        matching_terms = []

        for term, node_data in self.alias_index.items():
            if entity_name.lower() in term.lower():
                matching_terms.append(term)
                # node_data might be a list of IDs or a dict with "nodes" key
                if isinstance(node_data, list):
                    matching_nodes.extend(node_data)
                elif isinstance(node_data, dict) and "nodes" in node_data:
                    matching_nodes.extend(node_data["nodes"])

        if not matching_nodes:
            return {"error": f"No entity found for '{entity_name}'", "results": []}

        matching_nodes = list(set(matching_nodes))

        # Find edges connected to these entities
        related_edges = []
        for edge in self.edges:
            source = edge.get("from", edge.get("source", ""))
            target = edge.get("to", edge.get("target", ""))

            if source in matching_nodes or target in matching_nodes:
                related_edges.append({
                    "type": edge.get("type", edge.get("edge_type", "")),
                    "from": self._get_node_label(source),
                    "to": self._get_node_label(target),
                    "properties": edge.get("properties", {}),
                })

        return {
            "entity_count": len(matching_nodes),
            "matching_terms": matching_terms,
            "matching_entities": [self._get_node_label(nid) for nid in matching_nodes],
            "related_edges": related_edges,
        }

    def query_cross_repo_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_confidence: Optional[str] = None,
        min_repos: int = 1,
    ) -> List[Dict]:
        """
        List all cross-repo patterns with optional filtering.

        Args:
            pattern_type: Filter by type (shared_dependency, shared_regulation, overlapping_business_rule)
            min_confidence: Filter by minimum confidence (HIGH, MEDIUM, LOW)
            min_repos: Filter by minimum number of repos

        Returns:
            List of cross-repo patterns sorted by confidence and repo count
        """
        confidence_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

        patterns = []
        for hedge in self.hyperedges:
            if hedge.get("type") != "cross_repo_pattern":
                continue

            props = hedge.get("properties", {})
            ptype = props.get("pattern_type")
            conf = props.get("confidence", "UNKNOWN")
            repos = props.get("repos", [])

            # Apply filters
            if pattern_type and ptype != pattern_type:
                continue
            if min_confidence and confidence_priority.get(conf, 999) > confidence_priority.get(min_confidence, 999):
                continue
            if len(repos) < min_repos:
                continue

            patterns.append({
                "id": hedge["id"],
                "pattern": hedge.get("label", ""),
                "type": ptype,
                "repos": repos,
                "confidence": conf,
                "repo_count": len(repos),
                "evidence": props.get("evidence", []),
                "evidence_count": len(props.get("evidence", [])),
            })

        # Sort by confidence and repo count
        return sorted(patterns, key=lambda x: (
            confidence_priority.get(x["confidence"], 3),
            -x["repo_count"],
        ))

    def get_repos_by_domain(self, domain_name: str) -> List[Dict]:
        """Get all repos in a specific domain"""
        repos = []
        domain_id = None

        # Find domain node
        for node in self.nodes.values():
            if node.get("type") == "domain" and domain_name.lower() in node.get("label", "").lower():
                domain_id = node["id"]
                break

        if not domain_id:
            return []

        # Find features belonging to this domain
        for edge in self.edges:
            if edge.get("type") == "belongs_to_domain" and edge.get("to") == domain_id:
                source_id = edge.get("from", "")
                feature = self.nodes.get(source_id)
                if feature:
                    repos.append(feature)

        return repos

    def get_shared_patterns_by_repo(self, repo_name: str) -> List[Dict]:
        """Get all cross-repo patterns involving a specific repo"""
        patterns = []
        for hedge in self.hyperedges:
            if hedge.get("type") == "cross_repo_pattern":
                repos = hedge.get("properties", {}).get("repos", [])
                if any(repo_name.lower() in repo.lower() for repo in repos):
                    props = hedge.get("properties", {})
                    patterns.append({
                        "pattern": hedge.get("label", ""),
                        "type": props.get("pattern_type"),
                        "confidence": props.get("confidence", "UNKNOWN"),
                        "repo_count": len(repos),
                        "other_repos": [r for r in repos if repo_name.lower() not in r.lower()],
                        "evidence": props.get("evidence", []),
                    })
        return patterns

    def get_stats(self) -> Dict:
        """Get hypergraph statistics including pattern breakdown"""
        cross_repo_patterns = [h for h in self.hyperedges if h.get("type") == "cross_repo_pattern"]

        pattern_types = {}
        for pattern in cross_repo_patterns:
            ptype = pattern.get("properties", {}).get("pattern_type")
            pattern_types[ptype] = pattern_types.get(ptype, 0) + 1

        confidence_dist = {}
        for pattern in cross_repo_patterns:
            conf = pattern.get("properties", {}).get("confidence", "UNKNOWN")
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1

        unique_repos = set()
        for pattern in cross_repo_patterns:
            repos = pattern.get("properties", {}).get("repos", [])
            unique_repos.update(repos)

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_hyperedges": len(self.hyperedges),
            "cross_repo_patterns": len(cross_repo_patterns),
            "pattern_types": pattern_types,
            "confidence_distribution": confidence_dist,
            "unique_repos": len(unique_repos),
        }

    def _get_node_label(self, node_id: str) -> str:
        """Helper to get node label"""
        node = self.nodes.get(node_id, {})
        return node.get("label", node.get("name", node_id))

    def get_all_domains(self) -> List[str]:
        """Get all domain labels"""
        domains = []
        for node in self.nodes.values():
            if node.get("type") == "domain":
                domains.append(node.get("label", ""))
        return sorted(domains)

    def get_pattern_types(self) -> List[str]:
        """Get all available pattern types"""
        types = set()
        for hedge in self.hyperedges:
            if hedge.get("type") == "cross_repo_pattern":
                ptype = hedge.get("properties", {}).get("pattern_type")
                if ptype:
                    types.add(ptype)
        return sorted(types)

    def query_by_domain(self, domain_name: str) -> Dict:
        """
        Query all entities, patterns, and technologies for a specific domain.
        
        Args:
            domain_name: Domain name (e.g., "E-Commerce", "Banking", "Library Management")
        
        Returns:
            Dict with domain-specific entities, patterns, technologies, and repositories
        """
        domain_nodes = []
        domain_repos = []
        domain_entities = []
        domain_features = []
        domain_patterns = []
        
        # Find nodes belonging to this domain
        for node in self.nodes.values():
            node_domain = node.get("domain") or node.get("properties", {}).get("domain")
            if node_domain and node_domain.lower() == domain_name.lower():
                domain_nodes.append(node)
                
                # Categorize by type
                node_type = node.get("type", "")
                label = node.get("label", node.get("name", ""))
                
                if node_type == "repository":
                    domain_repos.append(label)
                elif node_type == "entity":
                    domain_entities.append(label)
                elif node_type == "feature":
                    domain_features.append(label)
        
        # Find patterns involving domain repos
        for hedge in self.hyperedges:
            if hedge.get("type") == "cross_repo_pattern":
                props = hedge.get("properties", {})
                repos = props.get("repos", [])
                
                # Check if pattern involves domain repos
                if any(repo in domain_repos for repo in repos):
                    domain_patterns.append({
                        "label": hedge.get("label", ""),
                        "type": props.get("pattern_type", ""),
                        "confidence": props.get("confidence", "UNKNOWN"),
                        "repos": repos,
                        "evidence_count": len(props.get("evidence", [])),
                    })
        
        return {
            "domain": domain_name,
            "repositories": domain_repos,
            "entities": domain_entities,
            "features": domain_features,
            "patterns": domain_patterns,
            "entity_count": len(domain_entities),
            "feature_count": len(domain_features),
            "repo_count": len(domain_repos),
            "pattern_count": len(domain_patterns),
        }

    def query_domain_features_only(self, domain_name: str, search_term: Optional[str] = None) -> List[str]:
        """
        Get only features relevant to a domain, optionally filtered by search term.
        
        Args:
            domain_name: Domain name (e.g., "E-Commerce", "Banking")
            search_term: Optional term to filter features
        
        Returns:
            List of domain-specific features matching search term
        """
        # Load domain config to get predefined features
        try:
            config_path = Path(__file__).parent / "domain_config.json"
            with open(config_path, "r", encoding="utf-8") as f:
                domain_config = json.load(f)
                domain_features = domain_config.get("domain_features", {}).get(domain_name, [])
        except:
            domain_features = []
        
        # Also find features in graph for this domain
        graph_features = []
        for node in self.nodes.values():
            if node.get("type") == "feature":
                node_domain = node.get("domain") or node.get("properties", {}).get("domain")
                if node_domain and node_domain.lower() == domain_name.lower():
                    graph_features.append(node.get("label", node.get("name", "")))
        
        # Combine and deduplicate
        all_features = list(set(domain_features + graph_features))
        
        # Filter by search term if provided
        if search_term:
            filtered = [f for f in all_features if search_term.lower() in f.lower()]
            return sorted(filtered)
        
        return sorted(all_features)

    def query_domain_related_repos(self, domain_name: str) -> List[str]:
        """
        Get all repositories linked to a specific domain.
        
        Args:
            domain_name: Domain name (e.g., "E-Commerce", "Banking")
        
        Returns:
            List of repository names for the domain
        """
        try:
            config_path = Path(__file__).parent / "domain_config.json"
            with open(config_path, "r", encoding="utf-8") as f:
                domain_config = json.load(f)
                # Find all repos with this domain
                repos = [repo for repo, domain in domain_config.items() 
                        if domain == domain_name and repo != "tech_stack_info" and repo != "domain_features"]
                return sorted(repos)
        except:
            return []

