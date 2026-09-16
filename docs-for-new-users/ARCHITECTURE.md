# Architecture & How It Works Inside

Deep dive into the BRD Agent system — from ingestion to RAG query answering.

---

## System Overview

BRD Agent is a **three-layer Python system**:

| Layer | What it does |
|-------|-------------|
| **Ingestion Layer** | Walks KB folders, enriches metadata with Claude, chunks documents, embeds into ChromaDB, registers in catalog, builds hypergraph |
| **RAG Pipeline** | Accepts questions, runs 10-step hybrid retrieval, returns grounded answers with citations |
| **Interface Layer** | Streamlit UI (8501), FastAPI REST (8081), CLI tools |

Everything runs **locally** (except Claude API calls).

---

## 3-Layer Architecture

```
┌────────────────────────────────────────────────────────────────┐
│ INTERFACES (User-Facing)                                       │
├────────────────────────────────────────────────────────────────┤
│ • Streamlit Web UI (http://localhost:8501)                     │
│ • REST API Server (http://localhost:8081)                      │
│ • CLI Tools (bin/ingest.py, bin/query.py, bin/annotate.py)     │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ APPLICATION LOGIC                                              │
├────────────────────────────────────────────────────────────────┤
│ • Document Ingestor & Enricher (Claude Haiku)                 │
│ • Hybrid RAG Pipeline (10-step retrieval)                     │
│ • Intent Classifier, Vector Search, Graph Expansion           │
│ • Late Chunker, Fallback RAG, Answer Generator                │
│ • Feedback Collection (HITL)                                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ STORAGE & INDEXING                                             │
├────────────────────────────────────────────────────────────────┤
│ • ChromaDB (kb_store/) — Vector embeddings, cosine search     │
│ • Document Registry (registry/documents.json) — Metadata      │
│ • Hypergraph (KB/graph/hypergraph.json) — Relationships       │
│ • Knowledge Base (KB/<service>/) — Raw artifacts              │
└────────────────────────────────────────────────────────────────┘
```

---

## The Ingestion Pipeline

When you run `python bin/ingest.py --all` or upload a repo:

```
KB/<service>/                   Source files (JSON, MD, etc.)
      ↓
DocumentIngestor
  ├─ detect_artifact_type()     Keywords → brd/journey_map/business_rules
  ├─ SHA-256 detection          Skip unchanged files (logs/ingestion_progress.json)
  ├─ enrich_metadata()          Claude Haiku: description, tags, entity_mentions
  ├─ BRDChunker                 Heading-aware splits (max 1400 chars, overlap 180)
  ├─ ChromaDBStore.add()        Embed & store with cosine similarity
  ├─ DocumentRegistry.add()     Add to registry/documents.json catalog
  └─ DocumentHypergraph.add()   Add node to KB/graph/hypergraph.json
      ↓
Ready for RAG queries
```

### Key Components

**DocumentRegistry (registry/documents.json)**
```json
{
  "artifact_id": "20240901_120000_UTC_a1b2c3d4",
  "name": "business_rules.json",
  "artifact_type": "business_rules",
  "service": "jpetstore-6",
  "file_path": "KB/jpetstore-6/business_rules.json",
  "description": "LLM summary of content",
  "tags": ["pet", "inventory", "checkout"],
  "useful_for": ["test_case_writing", "requirement_clarification"],
  "entity_mentions": ["Pet", "Order", "Account"],
  "access_count": 3
}
```

**DocumentHypergraph (KB/graph/hypergraph.json)**

Directed graph of document relationships:

```json
{
  "nodes": [
    {
      "artifact_id": "...",
      "name": "business_rules.json",
      "artifact_type": "business_rules",
      "service": "jpetstore-6",
      "tags": ["pet", "inventory"]
    }
  ],
  "edges": [
    {
      "from_id": "...",
      "to_id": "...",
      "edge_type": "references",  // "references" | "informs" | "supersedes" | "related"
      "weight": 0.8
    }
  ]
}
```

**ChromaDBStore (kb_store/)**
- Persistent ChromaDB collection
- Embedding function tries Gemini/PyVegas first, falls back to sentence-transformers
- If HuggingFace blocked: falls back to SHA-256 hash embeddings
- Scoring: cosine similarity (0–1, where 1 = identical)

---

## The 10-Step RAG Pipeline

When you ask a question via chat, UI, or CLI:

```
Question: "What are the acceptance criteria?"
  │
  ├─→ 1. INTENT CLASSIFICATION (Claude Haiku)
  │      Sends up to 80 document names to Claude
  │      Returns: {"intent": "acceptance_criteria", "relevant_docs": [...]}
  │
  ├─→ 2. VECTOR SEARCH (ChromaDB)
  │      Cosine similarity search, top 5 matches
  │      Returns: [(artifact_id, score, metadata), ...]
  │
  ├─→ 3. SCORE MERGING
  │      Combines intent predictions (baseline score 0.5) + vector results
  │
  ├─→ 4. HYPERGRAPH EXPANSION (Optional)
  │      BFS walk from seed documents, max depth 2
  │      Adds related documents to candidate list
  │      Sets retrieval_method = "hybrid"
  │
  ├─→ 5. CROSS-ENCODER RERANKING (Optional)
  │      BAAI/bge-reranker-base reorders candidates by semantic relevance
  │
  ├─→ 6. LATE CHUNKING
  │      Splits each document into sentence boundaries
  │      Scores windows by keyword overlap with question
  │      Selects top sentence windows with context
  │
  ├─→ 7. LOCAL RAG FALLBACK (if max_score < 0.3)
  │      TF-IDF search over registry metadata
  │      Metadata includes: name, description, tags, entity_mentions
  │      Sets retrieval_method = "local"
  │
  ├─→ 8. LLM ANSWER GENERATION (Claude Haiku)
  │      Takes retrieved snippets + question
  │      Generates grounded answer (strict_grounded=True)
  │      Infers confidence from hedging language:
  │         "cannot/don't have" → LOW
  │         "may/might" → MEDIUM
  │         else → HIGH
  │
  ├─→ 9. TELEMETRY
  │      Logs access counts to registry
  │      Records retrieval method in context graph
  │
  └─→ 10. CONVERSATION HISTORY
         Persists turn in ConversationStore
```

**Output:**
```json
{
  "answer": "The acceptance criteria include...",
  "sources": [
    {"artifact_id": "...", "name": "acceptance_criteria.json", "snippet": "..."}
  ],
  "intent": "acceptance_criteria",
  "confidence": "HIGH",
  "retrieval_method": "hybrid",
  "telemetry": {
    "intent_latency_ms": 1200,
    "vector_search_latency_ms": 45,
    "ranking_latency_ms": 120,
    "llm_latency_ms": 950
  }
}
```

---

## Key Components Explained

### IntentClassifier
Sends document names to Claude, expects JSON response with predicted intent and relevant docs. Includes exponential backoff (1s → 2s → 4s) for retries.

### BRDChunker
Splits on `^#{1,3}` headings (MD level 1-3). Settings:
- `max_chars=1400`
- `overlap_chars=180`
- `max_chunks=5000`
Designed for BRD, business_rules, and journey_map artifacts.

### LateChunker
Post-retrieval stage. Splits candidates into sentence boundaries, scores each window by keyword overlap, returns top-N with surrounding context sentences.

### LocalRAG
TF-IDF fallback when vector search fails (max_score < 0.3). Searches metadata: name, description, tags, entity_mentions, useful_for.

### ConversationStore
Persists user queries and answers. Enables multi-turn awareness and feedback tracking.

---

## Data Flow Example

### Ingestion
```
Input: KB/jpetstore-6/business_rules.json
  ↓
Detect type: "business_rules"
  ↓
Metadata enrichment:
  description: "Pet store business rules for inventory, orders, checkout"
  tags: ["pet", "inventory", "payment", "checkout"]
  entity_mentions: ["Pet", "Order", "Inventory", "Account"]
  ↓
Chunk by headings:
  Chunk 1: "Rule: Inventory must never go negative"
  Chunk 2: "Rule: Orders can only be placed by registered users"
  ...
  ↓
Embed each chunk (cosine similarity in ChromaDB)
  ↓
Register in documents.json:
  artifact_id: "20240901_120000_UTC_a1b2c3d4"
  ↓
Add hypergraph node
  ↓
Ready for queries
```

### Query Example
```
User: "What payment methods are accepted?"
  ↓
Intent classifier → identifies "business_rules" as relevant
  ↓
Vector search → finds chunks mentioning "payment"
  ↓
Hypergraph expansion → adds related docs like "api_endpoints"
  ↓
Reranking → orders by relevance
  ↓
Late chunking → extracts specific sentences about payment
  ↓
LLM synthesis → "The system accepts credit cards, PayPal, and bank transfers..."
  ↓
Answer returned with sources + confidence
```

---

## Configuration

**kb_gen_config.yaml** controls pipeline behavior:

```yaml
ingestion:
  artifact_types: [brd, business_rules, journey_map, ...]
  chunk_max_chars: 1400
  chunk_overlap_chars: 180

rag:
  use_graph_expansion: true
  graph_max_depth: 2
  enable_reranker: true
  late_chunker_top_n: 5
  fallback_threshold: 0.3

embeddings:
  embedding_function: "vegas"  # or "local"
  chromadb_collection: "kb_documents"

llm:
  model: "claude-3-5-haiku-20241022"
  max_tokens: 1024
  temperature: 0.3
```

---

## Embedding Strategy

The system tries multiple embeddings in order:

1. **Gemini/PyVegas** (requires HuggingFace access)
2. **Sentence Transformers** (`all-MiniLM-L6-v2`) — standard multilingual embeddings
3. **SHA-256 Hash Fallback** — offline, deterministic, lower quality but functional

Corporate networks automatically skip steps 1-2 and use step 3, so everything still works.

---

## Performance Notes

- **First ingestion:** Slower (metadata enrichment + embedding all chunks)
- **Subsequent queries:** Fast (cached embeddings, vector search is ~45ms)
- **Large repos (100+ services):** Hypergraph expansion adds ~200ms per query
- **Reranking:** Adds ~100-150ms but improves answer quality

---

## Human-In-The-Loop (HITL)

Users can annotate query results:

```
"Is this answer useful?" → [Yes / No]
```

Feedback updates `registry.documents.json`:
- Increments `access_count` per document
- Updates `usefulness_scores` per intent type

Over time, documents marked as useful get higher implicit priority in future searches.

---

## Extending the System

### Add New Artifact Type
1. Define type in `kb_gen/ingestion/artifact_detector.py`
2. Add keywords/patterns for detection
3. Optionally add custom chunker
4. Update `kb_gen_config.yaml` to include new type

### Add Custom Embedding
1. Subclass `EmbeddingFunction` in `kb_gen/embeddings/`
2. Update `kb_gen_config.yaml` to reference it

### Add Custom RAG Step
1. Create new module in `kb_gen/rag/`
2. Hook into `RAGQueryEngine.query()` pipeline
3. Add telemetry/logging

---

## Troubleshooting

### Low Relevance Scores
**Cause:** Embeddings mismatch between ingestion & query.  
**Fix:** Ensure same embedding function for both. Check `kb_gen_config.yaml`.

### Hypergraph Not Expanding
**Cause:** No edges in KB/graph/hypergraph.json or all nodes isolated.  
**Fix:** Run ingestion with `--rebuild-graph` flag to recompute relationships.

### Slow Vector Search
**Cause:** Large ChromaDB collection without cleanup.  
**Fix:** Rebuild kb_store with `python bin/ingest.py --rebuild-chromadb`.

---

## See Also

- [QUICKSTART.md](QUICKSTART.md) — Setup & usage guide
- [kb_gen_config.yaml](../kb_gen_config.yaml) — All configuration options
- [bin/](../bin/) — CLI tool documentation
