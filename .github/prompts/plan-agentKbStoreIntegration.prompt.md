# Planning Agent KB Store Integration

## Objective
Design and implement integration between agents and the centralized knowledge base (KB) store for organizational learning and pattern detection.

## Current State
- Agents write outputs to `kb_store/{repo_name}/agent_{n}/` directories
- Each agent produces JSON outputs
- No cross-project pattern detection
- No historical comparison
- Limited organizational learning

## Target State
- All agent outputs indexed in ChromaDB vector store
- Cross-project semantic search enabled
- Pattern detection across multiple analyses
- Historical trend analysis
- Automated similarity detection
- Organizational knowledge graph

## Architecture

### KB Store Structure
```
kb_store/
├── chromadb_index/           # Vector embeddings
├── knowledge_graph/          # Neo4j or JSON graph
├── projects/
│   └── {repo_name}/
│       ├── agent_1/
│       ├── agent_2/
│       └── ...
├── patterns/                 # Detected patterns
│   ├── journey_patterns.json
│   ├── rule_patterns.json
│   └── gap_patterns.json
├── historical/               # Time-series data
│   └── project_metrics.json
└── logs/
    ├── agent_interactions.log
    ├── tool_executions.log
    └── policy_violations.log
```

### Integration Points

#### 1. Agent Output → KB Store (Agent 9)
```python
# Agent 9: KB Store Sync Agent
def sync_to_kb(agent_outputs, repo_name):
    """
    Indexes all agent outputs to KB store
    """
    # Index to ChromaDB for semantic search
    vectorize_and_store(agent_outputs)
    
    # Update knowledge graph
    update_knowledge_graph(agent_outputs, repo_name)
    
    # Detect patterns
    patterns = detect_patterns(agent_outputs)
    
    # Compare with historical data
    trends = compare_with_history(agent_outputs, repo_name)
    
    return {
        "indexed_documents": count,
        "patterns_detected": patterns,
        "historical_trends": trends
    }
```

#### 2. KB Store → Agent Input (Agent 5)
```python
# Agent 5: Synthesis with KB context
def resolve_conflict_with_kb(conflict, kb_manager):
    """
    Uses KB to resolve conflicts based on similar past cases
    """
    # Search for similar conflicts in KB
    similar_conflicts = kb_manager.search_similar(
        conflict.description,
        type="conflict",
        limit=5
    )
    
    # Find resolution patterns
    resolutions = [c.resolution for c in similar_conflicts]
    
    # Apply most common resolution pattern
    recommended_resolution = find_consensus(resolutions)
    
    return recommended_resolution
```

## Implementation Plan

### Phase 1: Basic KB Integration
**Goal**: Store all agent outputs in KB

**Tasks**:
1. Implement `KBManager` class in `kb/kb_manager.py`
2. Add ChromaDB indexing for all JSON outputs
3. Create Agent 9 skeleton
4. Test basic store/retrieve operations

**Acceptance Criteria**:
- All agent JSON outputs indexed
- Basic search functionality works
- Agent 9 produces sync report

### Phase 2: Pattern Detection
**Goal**: Detect recurring patterns across projects

**Tasks**:
1. Implement pattern detection algorithms
2. Create pattern templates for journeys, rules, gaps
3. Add pattern similarity scoring
4. Generate pattern catalog

**Acceptance Criteria**:
- Detects journey patterns (e.g., "Login flow")
- Detects rule patterns (e.g., "Email validation")
- Produces confidence-scored pattern matches

### Phase 3: Historical Comparison
**Goal**: Compare current analysis with past projects

**Tasks**:
1. Add time-series data storage
2. Implement metric tracking over time
3. Create trend analysis reports
4. Add anomaly detection

**Acceptance Criteria**:
- Tracks metrics per project over time
- Generates trend reports
- Flags anomalies (e.g., "Gap count unusually high")

### Phase 4: Knowledge Graph
**Goal**: Build organizational knowledge graph

**Tasks**:
1. Design graph schema (Projects → Components → Journeys → Rules)
2. Implement graph builder
3. Add graph query API
4. Create graph visualization

**Acceptance Criteria**:
- Graph connects all entities
- Supports path queries
- Visualizes in Mermaid/D3.js

### Phase 5: Agent KB Context Integration
**Goal**: Agents use KB for better decisions

**Tasks**:
1. Add KB context to Agent 5 synthesis
2. Use pattern detection in Agent 2 (journeys)
3. Use historical gaps in Agent 4
4. Add conflict resolution with KB precedent

**Acceptance Criteria**:
- Agent 5 cites KB when resolving conflicts
- Agent 2 suggests common journey patterns
- Agent 4 compares gap profiles

## API Design

### KB Manager Interface
```python
class KBManager:
    def store_agent_output(self, agent_name, repo_name, output_data):
        """Store agent output to KB"""
        pass
    
    def search_similar(self, query, type=None, limit=10):
        """Semantic search across KB"""
        pass
    
    def detect_patterns(self, entity_type):
        """Detect patterns for journeys, rules, etc."""
        pass
    
    def get_historical_metrics(self, repo_name):
        """Get metrics for a specific project"""
        pass
    
    def query_graph(self, cypher_query):
        """Query knowledge graph"""
        pass
    
    def get_conflict_precedents(self, conflict_description):
        """Find similar past conflicts and resolutions"""
        pass
```

### ChromaDB Collections
```python
collections = {
    "scope_definitions": "Agent 1 scope outputs",
    "journeys": "Agent 2 journey outputs",
    "business_rules": "Agent 3 rule outputs",
    "gaps": "Agent 4 gap outputs",
    "conflicts": "Agent 5 conflict outputs",
    "acceptance_criteria": "Agent 6 AC outputs",
    "risks": "Agent 7 risk outputs"
}
```

## Configuration Changes

Add to `config.yaml`:
```yaml
global:
  vector_store:
    adapter: chromadb_adapter
    path: ./kb_store/chromadb_index
    collection_name: brd_poc
    embedding_model: all-MiniLM-L6-v2
    enabled: true
  
  knowledge_graph:
    enabled: false  # Phase 4
    type: json  # json | neo4j
    path: ./kb_store/knowledge_graph

agents:
  agent_9_kb_store_sync:
    name: "KB Store Sync Agent"
    description: "Synchronizes analysis with KB and detects patterns"
    enabled: true
    llm: global.llm_secondary
    
    features:
      semantic_indexing: true
      pattern_detection: true
      historical_comparison: true
      knowledge_graph: false  # Phase 4
    
    pattern_detection:
      min_similarity_threshold: 0.85
      min_pattern_occurrences: 3
      entity_types:
        - journey
        - business_rule
        - gap
        - conflict
```

## Testing Strategy

### Unit Tests
- Test KB store/retrieve
- Test pattern detection algorithms
- Test similarity scoring
- Test graph queries

### Integration Tests
- Test Agent 9 full sync
- Test Agent 5 with KB context
- Test cross-project pattern detection
- Test historical comparison

### Performance Tests
- Index 100 projects
- Search response time < 200ms
- Pattern detection on 1000 rules
- Graph query performance

## Success Metrics
- **Coverage**: 100% of agent outputs indexed
- **Search Quality**: >90% relevant results in top 5
- **Pattern Detection**: Detect known patterns with >85% accuracy
- **Performance**: <200ms search response time
- **Utility**: Agents cite KB in >30% of conflict resolutions

## Rollout Plan
1. **Week 1-2**: Implement Phase 1 (basic KB integration)
2. **Week 3-4**: Implement Phase 2 (pattern detection)
3. **Week 5-6**: Implement Phase 3 (historical comparison)
4. **Week 7-8**: Implement Phase 4 (knowledge graph)
5. **Week 9-10**: Implement Phase 5 (agent KB context integration)
6. **Week 11-12**: Testing, optimization, documentation

## Dependencies
- `chromadb>=0.5.0`
- `sentence-transformers>=3.0.0`
- `networkx>=3.0` (for graph)
- `neo4j>=5.0` (optional, for Phase 4)

## Documentation Requirements
- KB Manager API reference
- Pattern detection guide
- Graph query examples
- Agent KB integration guide
- Performance tuning guide
