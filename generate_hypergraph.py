#!/usr/bin/env python3
"""
generate_hypergraph.py
======================
Scans all KB/<repo>/ folders produced by the BRD pipeline and writes
KB/graph/hypergraph.json that the Vis.js viewer can display.

Schema (hypergraph/v1):
  nodes      – domain | feature | artifact
  edges      – belongs_to_domain | has_artifact
  hyperedges – reserved / empty
  alias_index – search-term → {nodes, edges}
  stats       – counts
  version_metadata – run_id, timestamp, changes

Usage:
  python generate_hypergraph.py
  python generate_hypergraph.py --kb KB --out KB/graph/hypergraph.json
  python generate_hypergraph.py --domain-config domain_config.json
"""

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Import versioning module
sys.path.insert(0, str(Path(__file__).parent))
from hypergraph.versioning import VersionManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ARTIFACT_EXTENSIONS = {".json", ".md", ".feature", ".yaml", ".yml", ".txt"}

# Canonical artifact-type labels derived from file stems
ARTIFACT_TYPE_LABELS: dict[str, str] = {
    "artifact_catalog":            "Artifact Catalog",
    "business_rules":              "Business Rules",
    "user_journey_map":            "User Journey Map",
    "journey_map":                 "Journey Map",
    "journey_conflicts":           "Journey Conflicts",
    "brd_final":                   "BRD Final",
    "brd_executive_summary":       "BRD Executive Summary",
    "brd_gap_summary":             "BRD Gap Summary",
    "brd_test_gap_analysis":       "BRD Test Gap Analysis",
    "risk_register":               "Risk Register",
    "dependency_register":         "Dependency Register",
    "dependency_map":              "Dependency Map",
    "acceptance_criteria":         "Acceptance Criteria",
    "acceptance_criteria_gherkin": "Acceptance Criteria (Gherkin)",
    "scope_definition":            "Scope Definition",
    "actors":                      "Actors",
    "gap_analysis":                "Gap Analysis",
    "gap_register":                "Gap Register",
    "coverage_summary":            "Coverage Summary",
    "regulatory_flags":            "Regulatory Flags",
    "regulatory_unresolved":       "Regulatory Unresolved",
    "orphaned_rules":              "Orphaned Rules",
    "rule_test_coverage":          "Rule Test Coverage",
    "test_case_analysis":          "Test Case Analysis",
    "test_journey_coverage":       "Test Journey Coverage",
    "test_gap_risk_register":      "Test Gap Risk Register",
    "new_test_suggestions":        "New Test Suggestions",
    "prioritized_gap_closure_tests": "Prioritized Gap Closure Tests",
    "regression_gap_report":       "Regression Gap Report",
    "synthesis_decisions":         "Synthesis Decisions",
}


def slugify(text: str) -> str:
    """Convert a string to a safe lowercase slug (alphanumeric + hyphens)."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def artifact_label(stem: str, repo: str) -> str:
    label = ARTIFACT_TYPE_LABELS.get(stem, stem.replace("_", " ").title())
    return f"{label} ({repo})"


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_hypergraph(kb_dir: Path, domain_config: dict | None = None) -> dict:
    """Scan kb_dir and return a hypergraph dict."""

    nodes: list[dict] = []
    edges: list[dict] = []
    alias_index: dict[str, dict] = {}
    edge_counter = 0
    tech_stack_nodes: dict[str, str] = {}  # tech_name -> node_id

    def next_edge_id() -> str:
        nonlocal edge_counter
        edge_counter += 1
        return f"e{edge_counter:04d}"

    def add_alias(term: str, node_id: str) -> None:
        key = term.lower()
        if key not in alias_index:
            alias_index[key] = {"nodes": [], "edges": []}
        if node_id not in alias_index[key]["nodes"]:
            alias_index[key]["nodes"].append(node_id)

    def extract_tech_stack(repo_name: str) -> list[str]:
        """Extract tech stack from repo name and domain config."""
        tech_stack = []

        # Check domain config for explicit tech stack mapping
        if domain_config:
            tech_stack_info = domain_config.get("tech_stack_info", {})
            if repo_name in tech_stack_info:
                tech_stack.extend(tech_stack_info[repo_name])

        # Also extract from repo name patterns if not already set
        if not tech_stack:
            repo_lower = repo_name.lower()
            if "spring" in repo_lower or "springboot" in repo_lower:
                if "Spring Boot" not in tech_stack:
                    tech_stack.append("Spring Boot")
            if "java" in repo_lower:
                if "Java" not in tech_stack:
                    tech_stack.append("Java")
            if "python" in repo_lower or "django" in repo_lower or "flask" in repo_lower:
                if "Python" not in tech_stack:
                    tech_stack.append("Python")
            if "node" in repo_lower or "express" in repo_lower:
                if "Node.js" not in tech_stack:
                    tech_stack.append("Node.js")

        return list(set(tech_stack))  # Remove duplicates

    # ── 1. Discover repo folders ─────────────────────────────────────────
    repo_dirs = sorted(
        [d for d in kb_dir.iterdir() if d.is_dir() and d.name not in ("graph", "cache")]
    )

    if not repo_dirs:
        print(f"WARNING: No repo folders found under {kb_dir}")

    # ── 2. Determine domain assignments ─────────────────────────────────
    # domain_config may map repo_name → domain_name.
    # Fall back: each repo is its own domain.
    def get_domain(repo_name: str) -> str:
        if domain_config and repo_name in domain_config:
            return domain_config[repo_name]
        return repo_name  # repo is its own domain when no config provided

    # ── 3. Build domain nodes (deduplicated) ────────────────────────────
    domain_names: set[str] = set()
    for repo_dir in repo_dirs:
        domain_names.add(get_domain(repo_dir.name))

    domain_id_map: dict[str, str] = {}
    for domain_name in sorted(domain_names):
        slug = slugify(domain_name)
        nid = f"domain_{slug}"
        domain_id_map[domain_name] = nid
        nodes.append({
            "id": nid,
            "type": "domain",
            "label": domain_name,
            "properties": {},
        })
        add_alias(domain_name, nid)
        add_alias(slug, nid)

    # ── 4. Build feature + artifact nodes ───────────────────────────────
    for repo_dir in repo_dirs:
        repo_name = repo_dir.name
        slug = slugify(repo_name)
        feature_id = f"feature_{slug}"

        # Collect artifact files
        artifact_files = sorted([
            f for f in repo_dir.iterdir()
            if f.is_file() and f.suffix.lower() in ARTIFACT_EXTENSIONS
        ])

        # Extract tech stack for this repo
        tech_stack = extract_tech_stack(repo_name)

        # Feature node with tech stack info
        nodes.append({
            "id": feature_id,
            "type": "feature",
            "label": repo_name,
            "properties": {
                "repo_name": repo_name,
                "artifact_count": len(artifact_files),
                "tech_stack": tech_stack,
            },
        })
        add_alias(repo_name, feature_id)
        add_alias(slug, feature_id)

        # Create tech stack nodes and edges
        for tech in tech_stack:
            tech_slug = slugify(tech)
            tech_id = f"tech_{tech_slug}"

            # Create tech node if not already created
            if tech_id not in tech_stack_nodes:
                nodes.append({
                    "id": tech_id,
                    "type": "technology",
                    "label": tech,
                    "properties": {
                        "tech_name": tech,
                    },
                })
                tech_stack_nodes[tech_id] = tech
                add_alias(tech, tech_id)

            # Edge: feature → tech (uses/depends_on)
            edges.append({
                "id": next_edge_id(),
                "type": "uses_technology",
                "from": feature_id,
                "to": tech_id,
                "weight": 1.0,
            })

        # Edge: feature → domain
        domain_name = get_domain(repo_name)
        domain_id = domain_id_map[domain_name]
        edges.append({
            "id": next_edge_id(),
            "type": "belongs_to_domain",
            "source": feature_id,
            "target": domain_id,
            "properties": {},
        })

        # Artifact nodes + edges
        for artifact_file in artifact_files:
            stem = artifact_file.stem
            aslug = slugify(f"{repo_name}-{stem}")
            artifact_id = f"artifact_{aslug}"
            artifact_type = stem  # raw stem as artifact_type key
            label = artifact_label(stem, repo_name)

            nodes.append({
                "id": artifact_id,
                "type": "artifact",
                "label": label,
                "properties": {
                    "artifact_type": artifact_type,
                    "file_path": str(artifact_file).replace("\\", "/"),
                },
            })
            add_alias(stem, artifact_id)
            add_alias(artifact_type, artifact_id)
            add_alias(label.lower(), artifact_id)

            # Edge: feature → artifact
            edges.append({
                "id": next_edge_id(),
                "type": "has_artifact",
                "source": feature_id,
                "target": artifact_id,
                "properties": {},
            })

    # ── 5. Detect cross-repo patterns (hyperedges) ───────────────────────────
    hyperedges: list[dict] = []
    hyperedge_counter = 0
    repo_dependencies: dict[str, list[str]] = {}  # repo_name -> list of dependency types
    repo_techs: dict[str, list[str]] = {}  # repo_name -> list of specific technologies
    repo_business_rules: dict[str, list[str]] = {}  # repo_name -> list of rule categories

    # Common tech keywords to detect (focus on architectural & business impact)
    # Removed: generic categories like "Git", "Maven", "JSON" that don't show code reuse
    tech_keywords = {
        # frameworks & key architectures
        "spring": "Spring Framework",
        "springboot": "Spring Boot",
        "spring-boot": "Spring Boot",
        "springdata": "Spring Data",
        "spring-data": "Spring Data",
        "hibernate": "Hibernate ORM",
        
        # REST & API protocols
        "rest": "REST APIs",
        "restful": "REST APIs",
        "graphql": "GraphQL",
        "soap": "SOAP APIs",
        "grpc": "gRPC",
        
        # SQL Databases
        "mysql": "MySQL",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mariadb": "MariaDB",
        "oracle": "Oracle Database",
        "mssql": "SQL Server",
        "h2": "H2 Database",
        "hsqldb": "HSQLDB",
        
        # NoSQL Databases
        "mongodb": "MongoDB",
        "redis": "Redis",
        "cassandra": "Cassandra",
        "elasticsearch": "Elasticsearch",
        
        # JPA/ORM
        "jpa": "JPA/ORM",
        
        # Testing frameworks
        "junit": "JUnit Testing",
        "testng": "TestNG",
        "mockito": "Mockito Mocking",
        "selenium": "Selenium Testing",
        
        # Message queues
        "kafka": "Apache Kafka",
        "rabbitmq": "RabbitMQ",
        "activemq": "ActiveMQ",
        
        # Cloud & deployment
        "docker": "Docker",
        "kubernetes": "Kubernetes",
    }

    # Scan all repos for dependencies and business rules
    for repo_dir in sorted(kb_dir.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name in ("graph", "cache"):
            continue

        repo_name = repo_dir.name

        # Extract dependency types and specific technologies
        dep_file = repo_dir / "dependency_register.json"
        if dep_file.exists():
            try:
                dep_data = json.loads(dep_file.read_text(encoding="utf-8"))
                deps = dep_data.get("dependencies", {}).get("by_type", {})
                repo_dependencies[repo_name] = list(deps.keys())

                # Extract specific tech keywords from descriptions
                identified_deps = dep_data.get("dependencies", {}).get("identified_dependencies", [])
                techs = set()
                for dep in identified_deps:
                    description = dep.get("description", "").lower()
                    for keyword, tech_name in tech_keywords.items():
                        if keyword in description:
                            techs.add(tech_name)
                if techs:
                    repo_techs[repo_name] = list(techs)
            except Exception:
                pass

        # Also extract techs from BRD file
        brd_file = repo_dir / "brd_final.json"
        if brd_file.exists():
            try:
                brd_data = json.loads(brd_file.read_text(encoding="utf-8"))
                brd_text = json.dumps(brd_data).lower()
                techs = set(repo_techs.get(repo_name, []))
                for keyword, tech_name in tech_keywords.items():
                    if keyword in brd_text:
                        techs.add(tech_name)
                if techs:
                    repo_techs[repo_name] = list(techs)
            except Exception:
                pass

        # Extract business rule categories
        br_file = repo_dir / "business_rules.json"
        if br_file.exists():
            try:
                br_data = json.loads(br_file.read_text(encoding="utf-8"))
                rules = br_data.get("summary", {})
                rule_types = [k.replace("_", " ").title() for k in rules.keys() if rules[k] and k != "total_rules"]
                if rule_types:
                    repo_business_rules[repo_name] = rule_types
            except Exception:
                pass

    # Detect shared specific technologies (most specific patterns first)
    if repo_techs:
        tech_to_repos: dict[str, list[str]] = {}
        for repo, techs in repo_techs.items():
            for tech in techs:
                if tech not in tech_to_repos:
                    tech_to_repos[tech] = []
                tech_to_repos[tech].append(repo)

        # Create hyperedges for shared technologies (2+ repos)
        for tech, repos in sorted(tech_to_repos.items()):
            if len(repos) >= 2:
                feature_ids = []
                for repo in repos:
                    for node in nodes:
                        if node.get("type") == "feature" and repo.lower() in node.get("label", "").lower():
                            feature_ids.append(node["id"])
                            break

                if len(feature_ids) >= 2:
                    hyperedge_counter += 1
                    hyperedges.append({
                        "id": f"hedge_tech_{hyperedge_counter}",
                        "type": "cross_repo_pattern",
                        "label": f"Shared technology: {tech}",
                        "node_ids": feature_ids,
                        "properties": {
                            "pattern_type": "shared_dependency",
                            "confidence": "HIGH",
                            "repos": repos,
                            "evidence": [f"{repo} uses {tech}" for repo in repos],
                        },
                    })

    # Then detect shared dependency types (less specific patterns)
    if repo_dependencies:
        dep_type_to_repos: dict[str, list[str]] = {}
        for repo, dep_types in repo_dependencies.items():
            for dep_type in dep_types:
                if dep_type not in dep_type_to_repos:
                    dep_type_to_repos[dep_type] = []
                dep_type_to_repos[dep_type].append(repo)

        # Create hyperedges for shared dependency types (2+ repos)
        for dep_type, repos in dep_type_to_repos.items():
            if len(repos) >= 2:
                feature_ids = []
                for repo in repos:
                    # Find feature node for this repo
                    for node in nodes:
                        if node.get("type") == "feature" and repo.lower() in node.get("label", "").lower():
                            feature_ids.append(node["id"])
                            break

                if len(feature_ids) >= 2:
                    hyperedge_counter += 1
                    hyperedges.append({
                        "id": f"hedge_dep_{hyperedge_counter}",
                        "type": "cross_repo_pattern",
                        "label": f"Shared dependency type: {dep_type}",
                        "node_ids": feature_ids,
                        "properties": {
                            "pattern_type": "shared_dependency",
                            "confidence": "MEDIUM",
                            "repos": repos,
                            "evidence": [f"{repo} has {dep_type} dependency" for repo in repos],
                        },
                    })

    # ── 6. Assemble graph ────────────────────────────────────────────────
    return {
        "$schema": "hypergraph/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "nodes": nodes,
        "edges": edges,
        "hyperedges": hyperedges,
        "alias_index": alias_index,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "hyperedge_count": len(hyperedges),
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate hypergraph.json from BRD pipeline KB output folders."
    )
    parser.add_argument(
        "--kb",
        default="KB",
        help="Path to the KB directory (default: KB)",
    )
    parser.add_argument(
        "--out",
        default="KB/graph/hypergraph.json",
        help="Output path for hypergraph.json (default: KB/graph/hypergraph.json)",
    )
    parser.add_argument(
        "--domain-config",
        default=None,
        help="Optional JSON file mapping repo_name → domain_name",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run ID for versioning (auto-generated if not provided)",
    )
    args = parser.parse_args()

    kb_dir = Path(args.kb)
    out_path = Path(args.out)

    if not kb_dir.is_dir():
        print(f"ERROR: KB directory not found: {kb_dir}")
        sys.exit(1)

    domain_config: dict | None = None
    if args.domain_config:
        dc_path = Path(args.domain_config)
        if not dc_path.exists():
            print(f"ERROR: Domain config not found: {dc_path}")
            sys.exit(1)
        with open(dc_path, encoding="utf-8") as f:
            domain_config = json.load(f)
        print(f"Loaded domain config: {dc_path} ({len(domain_config)} entries)")

    print(f"Scanning: {kb_dir.resolve()}")
    graph = build_hypergraph(kb_dir, domain_config)

    # Use versioning system
    run_id = args.run_id or str(uuid.uuid4())[:8]
    version_manager = VersionManager(out_path.parent)

    success, msg = version_manager.save_versioned_graph(
        graph, run_id, kb_dir, domain_config
    )

    if success:
        print(msg)
    else:
        print(f"ERROR: {msg}")
        sys.exit(1)

    stats = graph["stats"]
    print(
        f"  nodes={stats['node_count']}  "
        f"edges={stats['edge_count']}  "
        f"aliases={len(graph['alias_index'])}"
    )


if __name__ == "__main__":
    main()
