# Hypergraph Guide: Understanding Shared Dependencies & Cross-Repo Patterns

## Table of Contents
1. [Overview](#overview)
2. [Architecture & Data Model](#architecture--data-model)
3. [How Shared Dependencies Are Detected](#how-shared-dependencies-are-detected)
4. [Query Strategies](#query-strategies)
5. [Python Implementation](#python-implementation)
6. [Prompt Strategies](#prompt-strategies)
7. [Troubleshooting](#troubleshooting)
8. [File Locations & Resources](#file-locations--resources)

---

## Overview

The hypergraph is a **JSON-based knowledge graph** that:

- **Organizes artifacts** into a hierarchy: Domain → Feature → Artifact
- **Detects shared dependencies** via technology family matching (deterministic) and LLM semantic analysis (optional)
- **Tracks relationships** between entities using 7 edge types
- **Enables cross-repo pattern discovery** through graph traversal
- **Stores data locally** as JSON with fast alias-based search indexing
- **Visualizes** interactively (HTML graph viewer with Vis.js)

**Key Output File:** `KB/graph/hypergraph.json` (~500KB+, contains 100s of cross-repo patterns)

---

## Architecture & Data Model

### Core Hypergraph Structure

```json
{
  "$schema": "hypergraph/v1",
  "nodes": [
    {
      "id": "domain_hr_management",
      "type": "domain",
      "label": "HR Management"
    },
    {
      "id": "feature_poc_hr_management_employeesimulator",
      "type": "feature",
      "label": "Employee Simulator",
      "domain_id": "domain_hr_management"
    },
    {
      "id": "artifact_a2836e6f-a75f-46b3-88ae-126bd3d03e18",
      "type": "artifact",
      "label": "dependency-register.json",
      "feature_id": "feature_poc_hr_management_employeesimulator"
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "type": "belongs_to_domain",
      "source": "feature_poc_hr_management_employeesimulator",
      "target": "domain_hr_management"
    },
    {
      "id": "edge_2",
      "type": "shares_dependency",
      "source": "feature_poc_hr_management_employeesimulator",
      "target": "feature_poc_ecommerce_petstore_jpetsore6",
      "properties": {
        "pattern_label": "Shared dependency: embedded-database",
        "confidence": "HIGH"
      }
    }
  ],
  "hyperedges": [
    {
      "id": "hedge_crp_1",
      "type": "cross_repo_pattern",
      "label": "Shared dependency: embedded-database",
      "node_ids": [
        "feature_poc_hr_management_employeesimulator",
        "feature_poc_ecommerce_petstore_jpetsore6",
        "feature_poc_leave_and_attendance_management_leavemanagement",
        "feature_poc_library_operations_librarymanagement",
        "feature_poc_veterinary_clinic_management_springpetclinic"
      ],
      "properties": {
        "pattern_type": "shared_dependency",
        "confidence": "HIGH",
        "repos": ["employee-simulator", "jpetstore-6", "leave-management", "library-management", "spring-petclinic"],
        "evidence": [
          "employee-simulator: embedded h2 database",
          "jpetstore-6: embedded h2 database",
          "leave-management: embedded h2 database"
        ]
      }
    }
  ],
  "alias_index": {
    "leave_request": ["entity_employee_simulator_leave_request", "entity_leave_management_leave_request"],
    "approval": ["entity_employee_simulator_approval_policy", "entity_leave_management_approval_workflow"],
    "spring_data": ["feature_poc_hr_management_employeesimulator", "feature_poc_ecommerce_petstore_jpetsore6"]
  },
  "stats": {
    "node_count": 450,
    "edge_count": 1200,
    "hyperedge_count": 75
  }
}
```

### Node Types

| Type | Represents | ID Pattern | Example |
|------|-----------|-----------|---------|
| `domain` | Business domain | `domain_*` | `domain_hr_management` |
| `feature` | Repository/microservice | `feature_poc_*_reponame` | `feature_poc_hr_management_employeesimulator` |
| `artifact` | Specific file/document | `artifact_[uuid]` | `artifact_a2836e6f-...` |

### Edge Types

| Edge Type | Direction | Meaning | Use Case |
|-----------|-----------|---------|----------|
| `belongs_to_domain` | feature → domain | Feature belongs to business domain | Navigate by domain |
| `has_artifact` | feature → artifact | Feature contains artifact file | Find documents/configs |
| `shares_dependency` | feature → feature | Both repos use same technology | Find tech overlap |
| `shares_pattern` | feature → feature | Both repos share business patterns | Find business logic overlap |
| `derived_from` | artifact → artifact | Artifact built from another | Trace lineage |
| `references` | artifact → artifact | Artifact references another | Find dependencies |
| `validates` | artifact → artifact | Artifact validates another | Trace validation |

### Hyperedges (Cross-Repo Patterns)

Hyperedges group multiple nodes into patterns. Two main types:

```typescript
// Type 1: Domain Group (intra-domain)
{
  "id": "hedge_dg_1",
  "type": "domain_group",
  "label": "HR Management Features",
  "node_ids": ["feature_...", "feature_...", "feature_..."],
  "properties": { "domain": "HR Management" }
}

// Type 2: Cross-Repo Pattern (cross-domain)
{
  "id": "hedge_crp_1",
  "type": "cross_repo_pattern",
  "label": "Shared dependency: spring-data",
  "node_ids": ["feature_...", "feature_...", "feature_..."],
  "properties": {
    "pattern_type": "shared_dependency",  // or "shared_regulation", "overlapping_business_rule"
    "confidence": "HIGH",  // HIGH, MEDIUM, LOW
    "repos": ["repo1", "repo2", "repo3"],
    "evidence": ["repo1 uses Spring Data JPA", "repo2 uses Spring Data MongoDB"]
  }
}
```

---

## How Shared Dependencies Are Detected

### Detection Strategy 1: Technology Family Matching (Deterministic)

The system has a `TECH_FAMILIES` map that groups related technologies:

```javascript
{
  "embedded-database": ["h2", "hsqldb", "derby", "sqlite"],
  "spring-data": ["spring-data-jpa", "spring-data-mongodb", "spring-data-redis"],
  "testing": ["junit", "mockito", "testng", "spock"],
  "logging": ["log4j", "slf4j", "logback"],
  "servlet-container": ["tomcat", "jetty", "undertow"],
  "spring-security": ["spring-security-core", "spring-security-oauth2"],
  "validation": ["javax-validation", "hibernate-validator"]
}
```

**Process:**
1. Extract dependencies from each repo's `dependency-register.json`
2. Normalize dependency names
3. Fuzzy match against `TECH_FAMILIES`
4. Group matching repos
5. Create `shared_dependency` hyperedges with **HIGH confidence**

**Output Example:**
```json
{
  "pattern_type": "shared_dependency",
  "label": "Shared dependency: embedded-database",
  "repos": ["employee-simulator", "jpetstore-6", "leave-management"],
  "confidence": "HIGH",
  "evidence": [
    "employee-simulator includes H2",
    "jpetstore-6 includes H2",
    "leave-management includes HSQLDB"
  ]
}
```

### Detection Strategy 2: Business Rules & Regulations (Deterministic)

Extracts rules from 4 schema variants:

**Schema Variants Supported:**
```json
// Variant 1: business_rules array
{ "business_rules": [{ "id": "rule_1", "name": "Approval Required", ... }] }

// Variant 2: rules array
{ "rules": ["validation", "workflow", "authorization"] }

// Variant 3: rules grouped by category
{ "groups": { "validation": ["rule1", "rule2"], "workflow": ["rule3"] } }

// Variant 4: rule_groups
{ "rule_groups": { "category": "rules[]" } }
```

**Process:**
1. Extract rules from each repo's `business-rules.json`
2. Normalize rule names and categories
3. Compare rule keywords across repos
4. Create `shared_regulation` or `overlapping_business_rule` hyperedges with **MEDIUM confidence**

**Output Example:**
```json
{
  "pattern_type": "overlapping_business_rule",
  "label": "Shared rule category: validation",
  "repos": ["employee-simulator", "leave-management"],
  "confidence": "MEDIUM",
  "evidence": [
    "employee-simulator has validation rule: mandatory_fields",
    "leave-management has validation rule: mandatory_fields"
  ]
}
```

### Detection Strategy 3: LLM-Powered Semantic Analysis (Non-Deterministic, Optional)

**Requires:** `GITHUB_TOKEN` environment variable

**Process:**
1. Call `analyzeSemantic()` method
2. Sends artifact metadata to Claude via GitHub Models API
3. Claude identifies semantic overlaps and business concept sharing
4. Returns 0-5 insights per analysis run
5. Create `semantic_overlap`, `shared_concept`, `migration_candidate`, or `reuse_opportunity` patterns

**Output Example:**
```json
{
  "pattern_type": "semantic_overlap",
  "label": "Semantic overlap: approval workflows",
  "repos": ["employee-simulator", "leave-management", "purchase-approval"],
  "confidence": "LOW",
  "evidence": [
    "All repos implement approval workflow pattern",
    "Similar state transitions: pending → approved → rejected"
  ]
}
```

---

## Query Strategies

### Strategy 1: Query by Technology (Best for Dependencies)

**Purpose:** Find which repos share a specific technology

**How it works:**
1. Search hyperedges for cross-repo patterns
2. Match keyword against pattern label (case-insensitive)
3. Return repos, confidence, and evidence

**Good Query Examples:**
```
"Find all repos using embedded databases"
"Which repos share Spring Data"
"Show shared testing frameworks"
"List all repos with logging configuration"
```

**Returns:**
```json
{
  "pattern": "Shared dependency: embedded-database",
  "repos": ["employee-simulator", "jpetstore-6", "leave-management", "library-management", "spring-petclinic"],
  "confidence": "HIGH",
  "evidence": [
    "employee-simulator: embedded h2 database",
    "jpetstore-6: embedded h2 database",
    "..."
  ]
}
```

### Strategy 2: Query by Business Concept (Best for Patterns)

**Purpose:** Find repos with similar business logic or entities

**How it works:**
1. Match query terms to entity nodes via alias_index
2. Two-hop traversal:
   - Hop 1: Direct relationships (score: 1.0)
   - Hop 2: Secondary relationships (score: 0.5)
3. Map entities back to features
4. Collect all artifacts from matched features

**Good Query Examples:**
```
"Find all repos with approval workflows"
"Which systems have notification services"
"Show repos that validate leave requests"
"List all repos with authorization rules"
```

**Returns:**
```json
{
  "entity_nodes": ["entity_employee_simulator_approval_policy", "entity_leave_management_approval_workflow"],
  "related_edges": [
    {
      "type": "shares_pattern",
      "from": "feature_poc_hr_management_employeesimulator",
      "to": "feature_poc_leave_and_attendance_management_leavemanagement",
      "properties": { "pattern_label": "Shared approval logic" }
    }
  ]
}
```

### Strategy 3: Direct Hyperedge Query (Raw Power)

**Purpose:** Get all cross-repo patterns with optional filtering

**How it works:**
1. Iterate all hyperedges with `type: "cross_repo_pattern"`
2. Filter by pattern_type (shared_dependency, shared_regulation, overlapping_business_rule)
3. Filter by confidence level (HIGH, MEDIUM, LOW)
4. Return full hyperedge with repos and evidence

**Query Examples:**
```python
# Get all high-confidence shared dependencies
engine.query_cross_repo_patterns(
  pattern_type="shared_dependency",
  min_confidence="HIGH"
)

# Get all overlapping business rules
engine.query_cross_repo_patterns(
  pattern_type="overlapping_business_rule"
)

# Get all patterns (no filtering)
engine.query_cross_repo_patterns()
```

**Returns:**
```json
[
  {
    "pattern": "Shared dependency: embedded-database",
    "type": "shared_dependency",
    "repos": ["employee-simulator", "jpetstore-6", "leave-management"],
    "confidence": "HIGH",
    "node_count": 3
  },
  {
    "pattern": "Shared rule category: validation",
    "type": "overlapping_business_rule",
    "repos": ["employee-simulator", "leave-management"],
    "confidence": "MEDIUM",
    "node_count": 2
  }
]
```

---

## Python Implementation

### Basic Query Engine

```python
import json
from pathlib import Path
from typing import List, Dict, Optional

class HypergraphQueryEngine:
    def __init__(self, hypergraph_path: str):
        """Initialize with path to hypergraph.json"""
        with open(hypergraph_path, 'r') as f:
            self.graph = json.load(f)
        self.alias_index = self.graph.get("alias_index", {})
        self.nodes = {n["id"]: n for n in self.graph.get("nodes", [])}
        self.edges = self.graph.get("edges", [])
        self.hyperedges = self.graph.get("hyperedges", [])
    
    def query_shared_dependencies(self, tech_keyword: str) -> List[Dict]:
        """
        Find repos sharing a technology family
        
        Args:
            tech_keyword: Technology name (e.g., "spring", "h2", "logging")
        
        Returns:
            List of matching patterns with repos and evidence
        """
        patterns = []
        for hedge in self.hyperedges:
            if hedge["type"] == "cross_repo_pattern":
                props = hedge.get("properties", {})
                if props.get("pattern_type") == "shared_dependency":
                    label = hedge["label"].lower()
                    if tech_keyword.lower() in label:
                        patterns.append({
                            "id": hedge["id"],
                            "pattern": hedge["label"],
                            "repos": props.get("repos", []),
                            "confidence": props.get("confidence"),
                            "evidence": props.get("evidence", []),
                            "repo_count": len(props.get("repos", []))
                        })
        return sorted(patterns, key=lambda x: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x["confidence"], 3),
            -x["repo_count"]
        ))
    
    def query_entity_relationships(self, entity_name: str) -> Dict:
        """
        Find business concepts across repos via entity nodes
        
        Args:
            entity_name: Entity concept (e.g., "approval", "notification")
        
        Returns:
            Dict with matched entity nodes and their relationships
        """
        # Find matching entities in alias index
        matching_nodes = []
        for term, node_ids in self.alias_index.items():
            if entity_name.lower() in term.lower():
                matching_nodes.extend(node_ids)
        
        if not matching_nodes:
            return {"error": f"No entity found for '{entity_name}'", "results": []}
        
        matching_nodes = list(set(matching_nodes))
        
        # Find edges connected to these entities
        related_edges = []
        for edge in self.edges:
            if edge["source"] in matching_nodes or edge["target"] in matching_nodes:
                related_edges.append({
                    "type": edge["type"],
                    "from": self._get_node_label(edge["source"]),
                    "to": self._get_node_label(edge["target"]),
                    "properties": edge.get("properties", {})
                })
        
        return {
            "entity_count": len(matching_nodes),
            "matching_entities": [self._get_node_label(nid) for nid in matching_nodes],
            "related_edges": related_edges
        }
    
    def query_cross_repo_patterns(
        self, 
        pattern_type: Optional[str] = None,
        min_confidence: Optional[str] = None,
        min_repos: int = 1
    ) -> List[Dict]:
        """
        List all cross-repo patterns with optional filtering
        
        Args:
            pattern_type: Filter by type (shared_dependency, shared_regulation, overlapping_business_rule)
            min_confidence: Filter by minimum confidence (HIGH, MEDIUM, LOW)
            min_repos: Filter by minimum number of repos
        
        Returns:
            List of cross-repo patterns
        """
        confidence_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        
        patterns = []
        for hedge in self.hyperedges:
            if hedge["type"] != "cross_repo_pattern":
                continue
            
            props = hedge.get("properties", {})
            ptype = props.get("pattern_type")
            conf = props.get("confidence")
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
                "pattern": hedge["label"],
                "type": ptype,
                "repos": repos,
                "confidence": conf,
                "repo_count": len(repos),
                "evidence_count": len(props.get("evidence", []))
            })
        
        # Sort by confidence and repo count
        return sorted(patterns, key=lambda x: (
            confidence_priority.get(x["confidence"], 3),
            -x["repo_count"]
        ))
    
    def get_repos_by_domain(self, domain_name: str) -> List[Dict]:
        """Get all repos in a specific domain"""
        repos = []
        domain_id = None
        
        # Find domain
        for node in self.nodes.values():
            if node["type"] == "domain" and domain_name.lower() in node.get("label", "").lower():
                domain_id = node["id"]
                break
        
        if not domain_id:
            return []
        
        # Find features in domain
        for edge in self.edges:
            if edge["type"] == "belongs_to_domain" and edge["target"] == domain_id:
                feature = self.nodes.get(edge["source"])
                if feature:
                    repos.append(feature)
        
        return repos
    
    def get_shared_patterns_by_repo(self, repo_name: str) -> List[Dict]:
        """Get all cross-repo patterns involving a specific repo"""
        patterns = []
        for hedge in self.hyperedges:
            if hedge["type"] == "cross_repo_pattern":
                repos = hedge.get("properties", {}).get("repos", [])
                if any(repo_name.lower() in repo.lower() for repo in repos):
                    patterns.append({
                        "pattern": hedge["label"],
                        "type": hedge.get("properties", {}).get("pattern_type"),
                        "confidence": hedge.get("properties", {}).get("confidence"),
                        "other_repos": [r for r in repos if repo_name.lower() not in r.lower()]
                    })
        return patterns
    
    def _get_node_label(self, node_id: str) -> str:
        """Helper to get node label"""
        node = self.nodes.get(node_id, {})
        return node.get("label", node_id)
    
    def get_stats(self) -> Dict:
        """Get hypergraph statistics"""
        cross_repo_patterns = [h for h in self.hyperedges if h["type"] == "cross_repo_pattern"]
        
        pattern_types = {}
        for pattern in cross_repo_patterns:
            ptype = pattern.get("properties", {}).get("pattern_type")
            pattern_types[ptype] = pattern_types.get(ptype, 0) + 1
        
        confidence_dist = {}
        for pattern in cross_repo_patterns:
            conf = pattern.get("properties", {}).get("confidence")
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_hyperedges": len(self.hyperedges),
            "cross_repo_patterns": len(cross_repo_patterns),
            "pattern_types": pattern_types,
            "confidence_distribution": confidence_dist,
            "unique_repos": len(set(
                repo for h in cross_repo_patterns 
                for repo in h.get("properties", {}).get("repos", [])
            ))
        }
```

### Streamlit Dashboard

```python
import streamlit as st
from pathlib import Path
from hypergraph_query_engine import HypergraphQueryEngine

st.set_page_config(page_title="Hypergraph Explorer", layout="wide")
st.title("🕸️ Cross-Repo Hypergraph Explorer")

# Initialize session state
if "engine" not in st.session_state:
    hypergraph_path = Path("KB/graph/hypergraph.json")
    if hypergraph_path.exists():
        st.session_state.engine = HypergraphQueryEngine(str(hypergraph_path))
    else:
        st.error(f"Hypergraph not found at {hypergraph_path}")
        st.stop()

engine = st.session_state.engine

# Display statistics
col1, col2, col3, col4, col5 = st.columns(5)
stats = engine.get_stats()

with col1:
    st.metric("Total Repos", stats["unique_repos"])
with col2:
    st.metric("Cross-Repo Patterns", stats["cross_repo_patterns"])
with col3:
    st.metric("Unique Nodes", stats["total_nodes"])
with col4:
    st.metric("Relationships", stats["total_edges"])
with col5:
    st.metric("Pattern Groups", stats["total_hyperedges"])

st.divider()

# Tabs for different query types
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Find Shared Technologies",
    "💼 Find Business Concepts", 
    "📊 All Cross-Repo Patterns",
    "🏢 Explore by Domain"
])

with tab1:
    st.subheader("Find Repos Sharing a Technology")
    st.write("Search for technologies like: 'spring', 'h2', 'logging', 'validation', 'testing'")
    
    tech = st.text_input(
        "Technology keyword:",
        placeholder="e.g., spring, embedded-database, logging",
        key="tech_search"
    )
    
    if tech:
        results = engine.query_shared_dependencies(tech)
        
        if results:
            st.success(f"Found {len(results)} matching pattern(s)")
            
            for result in results:
                with st.expander(
                    f"📌 {result['pattern']} ({result['confidence']}) — {result['repo_count']} repos"
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Repos:**")
                        for repo in result["repos"]:
                            st.write(f"- `{repo}`")
                    with col2:
                        st.write("**Evidence:**")
                        for ev in result["evidence"][:5]:  # Show first 5
                            st.write(f"- {ev}")
                        if len(result["evidence"]) > 5:
                            st.write(f"... and {len(result['evidence']) - 5} more")
        else:
            st.info("No patterns found for this technology")

with tab2:
    st.subheader("Find Business Concepts Across Repos")
    st.write("Search for concepts like: 'approval', 'notification', 'validation', 'authorization'")
    
    concept = st.text_input(
        "Business concept:",
        placeholder="e.g., approval, notification, validation",
        key="concept_search"
    )
    
    if concept:
        results = engine.query_entity_relationships(concept)
        
        if "error" in results:
            st.warning(results["error"])
        else:
            st.info(f"Found {results['entity_count']} matching entities")
            
            if results["matching_entities"]:
                st.write("**Matching Entities:**")
                for entity in results["matching_entities"]:
                    st.write(f"- {entity}")
            
            if results["related_edges"]:
                st.write(f"**Related Relationships ({len(results['related_edges'])}):**")
                for edge in results["related_edges"][:20]:
                    st.write(f"- `{edge['from']}` **{edge['type']}** `{edge['to']}`")

with tab3:
    st.subheader("All Cross-Repo Patterns")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pattern_type = st.selectbox(
            "Filter by type:",
            [None, "shared_dependency", "shared_regulation", "overlapping_business_rule"],
            format_func=lambda x: "All types" if x is None else x.replace("_", " ").title()
        )
    
    with col2:
        min_confidence = st.selectbox(
            "Minimum confidence:",
            [None, "HIGH", "MEDIUM", "LOW"],
            format_func=lambda x: "All confidence levels" if x is None else x
        )
    
    with col3:
        min_repos = st.slider("Minimum repos sharing pattern", min_value=1, max_value=10, value=1)
    
    results = engine.query_cross_repo_patterns(
        pattern_type=pattern_type,
        min_confidence=min_confidence,
        min_repos=min_repos
    )
    
    st.info(f"Showing {len(results)} pattern(s) out of {stats['cross_repo_patterns']} total")
    
    for result in results:
        with st.expander(
            f"📌 {result['pattern']} ({result['confidence']}) — {result['repo_count']} repos"
        ):
            st.write(f"**Type:** `{result['type']}`")
            st.write(f"**Repos:** {', '.join(f'`{r}`' for r in result['repos'])}")
            st.metric("Evidence Items", result["evidence_count"])

with tab4:
    st.subheader("Explore by Domain")
    
    # Get all domains
    domains = set()
    for node in engine.nodes.values():
        if node["type"] == "domain":
            domains.add(node["label"])
    
    domain = st.selectbox("Select domain:", sorted(domains))
    
    if domain:
        repos = engine.get_repos_by_domain(domain)
        
        if repos:
            st.write(f"**Repos in {domain}:**")
            for repo in repos:
                st.write(f"- `{repo['label']}`")
                
                # Show patterns for this repo
                patterns = engine.get_shared_patterns_by_repo(repo["label"])
                if patterns:
                    st.write("  *Shared patterns:*")
                    for pattern in patterns[:3]:
                        st.write(f"    - {pattern['pattern']} ({pattern['confidence']})")
        else:
            st.info("No repos found in this domain")

st.divider()

# Debug section
with st.expander("🔧 Debug Info"):
    st.json({
        "Hypergraph file": "KB/graph/hypergraph.json",
        "Total nodes": stats["total_nodes"],
        "Total edges": stats["total_edges"],
        "Cross-repo patterns": stats["cross_repo_patterns"],
        "Unique repos": stats["unique_repos"],
        "Pattern type distribution": stats["pattern_types"],
        "Confidence distribution": stats["confidence_distribution"]
    })
```

---

## Prompt Strategies

### For LLM-Based Querying (Agent Orchestrator)

#### Prompt 1: Find Shared Dependencies

```
System Prompt:
You are a code intelligence assistant analyzing cross-repository patterns.
Given a hypergraph.json file with shared dependencies, you analyze and extract insights.
Always provide specific repo names, not generalizations.
Format your output as structured JSON.

User Query Template:
"Analyze the hypergraph and find all repos sharing [TECHNOLOGY].
For each pattern found, provide:
1. Technology family (e.g., 'embedded-database', 'spring-data')
2. Repos sharing this technology
3. Confidence level (HIGH/MEDIUM/LOW)
4. Evidence from each repo
5. Migration or consolidation opportunities

Format as JSON with this structure:
{
  "shared_technology": "...",
  "repos": ["repo1", "repo2", ...],
  "confidence": "HIGH|MEDIUM|LOW",
  "evidence": [...],
  "recommendations": [...]
}"
```

#### Prompt 2: Find Business Pattern Overlap

```
User Query Template:
"Identify business rule overlaps across repos in the hypergraph.
Focus on:
1. Repos with validation rules
2. Repos with approval workflows
3. Repos with authorization patterns
4. Repos with notification systems

For each overlap, provide:
- Pattern type (validation, workflow, authorization, notification)
- Repos involved
- Overlapping rule keywords
- Opportunity for extraction/reuse

Format as structured data with specific repo names."
```

#### Prompt 3: Cross-Repo Risk & Impact Analysis

```
User Query Template:
"Given the hypergraph of shared dependencies, analyze impact if we refactor [REPO].
For each repo sharing a dependency with [REPO]:
1. List shared technologies
2. Count of shared patterns
3. Risk level if shared tech changes (HIGH/MEDIUM/LOW)
4. Repos that would be affected
5. Migration path recommendations

Be specific about which repos and patterns are affected."
```

#### Prompt 4: Identify Reuse Opportunities

```
User Query Template:
"Based on shared dependencies and business rules in the hypergraph, identify extraction candidates.
Look for:
1. Business logic used by 3+ repos
2. Technology patterns used by 4+ repos
3. Validation rules appearing in 2+ repos
4. Notification/approval workflows that could be services

For each candidate, recommend:
- What to extract (business logic, service, library)
- Which repos benefit
- Implementation cost vs. benefit
- Timeline (quick win vs. strategic)"
```

### Prompt Best Practices

**✅ DO:**
- Be specific: "embedded-database" not "database"
- Ask for structured output (JSON)
- Request evidence/proof
- Mention specific repo count thresholds
- Ask for actionable recommendations

**❌ DON'T:**
- Vague queries: "show patterns"
- Ask for natural language analysis only
- Assume patterns without evidence
- Request all patterns at once (too noisy)

---

## Troubleshooting

### Issue 1: "hypergraph.json is empty or too small"

**Symptoms:**
- File exists but < 100KB
- Very few patterns found

**Solutions:**

1. **Rebuild the hypergraph:**
   ```bash
   cd AGENTS/knowledge-base-rag/brd-pipeline
   npm run build-kb
   ```

2. **Check if KB/ has artifacts:**
   ```bash
   ls -la KB/*/
   # Should see: dependency-register.json, business-rules.json, brd.json
   ```

3. **Verify cross-repo analyzer ran:**
   ```bash
   grep -l "cross_repo_pattern" KB/graph/hypergraph.json
   # Should find matches
   ```

### Issue 2: "No shared dependencies found"

**Symptoms:**
- Query returns empty results
- Technologies exist but not grouped

**Solutions:**

1. **Check TECH_FAMILIES in code:**
   - Are the technologies in your repos listed?
   - Update `TECH_FAMILIES` map if missing

2. **Verify dependency-register.json exists:**
   ```bash
   find KB -name "dependency-register.json" | wc -l
   # Should be > 3
   ```

3. **Check artifact names:**
   - Dependencies must exactly match `TECH_FAMILIES` keys
   - Try searching for partial matches

### Issue 3: "Entity relationships not found"

**Symptoms:**
- Business concept query returns no results
- alias_index is empty

**Solutions:**

1. **Check if entity extraction ran:**
   ```bash
   grep "entity_" KB/graph/hypergraph.json | wc -l
   # Should be > 20
   ```

2. **Enable LLM semantic analysis (optional):**
   ```bash
   export GITHUB_TOKEN="your_token"
   npm run build-kb
   # Will extract semantic entities
   ```

3. **Manually add entity nodes** if needed:
   - Edit `hypergraph.json`
   - Add entity nodes with aliases
   - Rebuild alias_index

### Issue 4: "Python import errors"

**Symptoms:**
- `ImportError: json` or similar

**Solutions:**

```python
# Add to top of your script
import json
import sys
from pathlib import Path

# Ensure correct path
hypergraph_path = Path("KB/graph/hypergraph.json").resolve()
if not hypergraph_path.exists():
    raise FileNotFoundError(f"Hypergraph not found at {hypergraph_path}")
```

### Issue 5: "Streamlit dashboard is slow"

**Symptoms:**
- Tab switching is slow
- Queries take > 2 seconds

**Solutions:**

```python
# Cache the engine in session state
if "engine" not in st.session_state:
    st.session_state.engine = HypergraphQueryEngine("KB/graph/hypergraph.json")

# Use caching decorators
@st.cache_data
def get_all_patterns():
    return engine.query_cross_repo_patterns()
```

---

## File Locations & Resources

### Core Files

| File | Purpose | Size |
|------|---------|------|
| `KB/graph/hypergraph.json` | Main hypergraph database | 500KB+ |
| `AGENTS/knowledge-base-rag/brd-pipeline/src/kb-store/hypergraph-builder.ts` | Hypergraph construction | |
| `AGENTS/knowledge-base-rag/brd-pipeline/src/kb-store/cross-repo-analyzer.ts` | Shared dependency detection | |
| `AGENTS/knowledge-base-rag/brd-chat/src/retrieval/hypergraph-navigator.js` | Query engine | |

### Data Files

| Directory | Contains | Example |
|-----------|----------|---------|
| `KB/*/dependency-register.json` | Tech dependencies per repo | H2, Spring Data, Logging |
| `KB/*/business-rules.json` | Business rules per repo | Validation, Approval, Authorization |
| `KB/*/brd.json` | Business requirements | Domain description, features |
| `KB/registry/artifact_registry.json` | All artifacts with metadata | UUID, feature_id, type |

### Visualization

| File | Purpose |
|------|---------|
| `AGENTS/hypergraph/viewer/index.html` | Interactive graph viewer (Vis.js) |
| `AGENTS/hypergraph/viewer/_build-viewer.js` | Build script for viewer |

### Commands

```bash
# Build/rebuild hypergraph
cd AGENTS/knowledge-base-rag/brd-pipeline
npm run build-kb

# View hypergraph JSON
cat KB/graph/hypergraph.json | jq . | head -100

# Count cross-repo patterns
cat KB/graph/hypergraph.json | jq '.hyperedges[] | select(.type=="cross_repo_pattern")' | wc -l

# List all repos
cat KB/graph/hypergraph.json | jq '.hyperedges[] | select(.type=="cross_repo_pattern") | .properties.repos[]' | sort -u

# Get high-confidence patterns
cat KB/graph/hypergraph.json | jq '.hyperedges[] | select(.type=="cross_repo_pattern" and .properties.confidence=="HIGH")'
```

---

## Quick Reference

### Most Common Queries

```python
# 1. Find all repos using Spring
results = engine.query_shared_dependencies("spring")

# 2. Find repos with approval workflows
results = engine.query_entity_relationships("approval")

# 3. Get high-confidence patterns
results = engine.query_cross_repo_patterns(min_confidence="HIGH")

# 4. Get patterns by repo
patterns = engine.get_shared_patterns_by_repo("employee-simulator")

# 5. Get stats
stats = engine.get_stats()
```

### Most Common Prompts

```
"Find all repos sharing [TECHNOLOGY]"
"Which repos have [BUSINESS_CONCEPT]"
"Show cross-repo [PATTERN_TYPE] patterns"
"Identify extraction/reuse opportunities from shared [DEPENDENCY/RULE]"
"What's the impact if we change [REPO]'s [TECHNOLOGY]"
```

---

## Contact & Support

- **Index Status:** Check `gitnexus://repo/requirement-and-triage-agent/context`
- **Rebuild Index:** `npx gitnexus analyze`
- **GitNexus Skills:** `.claude/skills/gitnexus/*/SKILL.md`
