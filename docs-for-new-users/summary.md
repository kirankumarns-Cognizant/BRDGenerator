# Architecture & Pipeline Internals

> What happens inside the BRD Agent Framework — from document ingestion to RAG answer generation.

---

## What This Is

The **BRD Agent Framework** is a Python system with three layers:

| Layer | What it does |
|-------|-------------|
| **Ingestion** | Walks `KB/<service>/`, enriches metadata with Claude, chunks BRD documents, embeds into ChromaDB, registers in a JSON catalog, and adds nodes to the hypergraph |
| **RAG Pipeline** | Accepts a natural language question, runs 10-step hybrid retrieval, returns a grounded answer with citations |
| **Interfaces** | Streamlit UI (port 8501), FastAPI REST server (port 8081), CLI tools (`bin/`) |

Everything runs **fully locally** — no cloud services required except the Anthropic Claude API.

---

## Architecture Overview

```
KB/<service>/                   Source artifacts (JSON + MD BRD documents)
      │
      ▼
DocumentIngestor                Walks service folders
  ├─ _detect_artifact_type()    Keywords in filename/content → brd/journey_map/business_rules/etc.
  ├─ SHA-256 change detection   Skips unchanged files (logs/ingestion_progress.json)
  ├─ _enrich_metadata()         Claude Haiku: description, tags, useful_for, entity_mentions
  ├─ BRDChunker                 Heading-aware splitting for BRD/rules/journey docs
  │     max_chars=1400, overlap=180, triggers on ^#{1,3} headings
  ├─ ChromaDBStore.add()        Embeds and stores in kb_store/ (cosine collection)
  ├─ DocumentRegistry.add()     JSON catalog at registry/documents.json
  └─ DocumentHypergraph.add_node()  Graph at KB/graph/hypergraph.json
      │
      ▼
RAGQueryEngine.query(question)  10-step hybrid RAG pipeline (see below)
      │
      ▼
{answer, sources, intent, confidence, retrieval_method, telemetry}
```

---

## The 10-Step RAG Pipeline

```
query(question)
  │
  ├─ 1. IntentClassifier.classify_query(question, name_to_id)
  │      → (intent_label, relevant_artifact_ids)
  │      → Claude Haiku, sends up to 80 doc names, exponential backoff up to 3 retries
  │
  ├─ 2. ChromaDBStore.query(question, top_k=5)
  │      → (artifact_id, cosine_score, metadata) list
  │
  ├─ 3. Merge intent-predicted docs (baseline score 0.5) into candidates
  │
  ├─ 4. [if use_graph_expansion] GraphWalker.expand(seed_ids, max_depth=2)
  │      → BFS walk over DocumentHypergraph → additional artifact_ids
  │      → retrieval_method = "hybrid"
  │
  ├─ 5. [if enable_reranker] CrossEncoder rerank (BAAI/bge-reranker-base)
  │      → reordered by semantic relevance
  │
  ├─ 6. LateChunker.chunk_and_select(candidates, question, top_n=5)
  │      → sentence-boundary splitting, keyword-overlap scoring
  │      → top sentence windows with context_sentences=3
  │
  ├─ 7. [if max_score < 0.3] LocalRAG.search(question)
  │      → TF-IDF over registry metadata (name, description, tags, entity_mentions)
  │      → merged fallback results, retrieval_method = "local"
  │
  ├─ 8. LLM answer generation (Claude Haiku, max_tokens=1024)
  │      → strict_grounded=True: only use provided sources
  │      → confidence inferred from hedging language:
  │         "cannot/don't have" → LOW, "may/might" → MEDIUM, else HIGH
  │
  ├─ 9. Telemetry: registry.record_access(), ContextGraph.record_retrieval()
  │
  └─ 10. ConversationStore.add_turn() — persists session history
```

---

## Components

### DocumentRegistry (`kb_gen/storage/registry.py`)

JSON catalog at `registry/documents.json`. All documents indexed by `artifact_id`.

Key methods:
- `add_document(metadata)` — deduplicates by `file_path`, atomic write via temp file
- `get_document(artifact_id)` — returns full metadata dict
- `get_service_documents(service)` — all docs for a service
- `get_name_to_id_map()` — used by IntentClassifier
- `record_access(artifact_id, intent)` — increments access_count
- `update_usefulness(artifact_id, intent, useful)` — HITL feedback integration

Schema per document:
```json
{
  "artifact_id": "20240901_120000_UTC_a1b2c3d4",
  "name": "business_rules.json",
  "artifact_type": "business_rules",
  "service": "jpetstore-6",
  "file_path": "KB/jpetstore-6/business_rules.json",
  "format": "json",
  "description": "LLM-generated one-sentence summary",
  "tags": ["pet", "inventory", "checkout"],
  "useful_for": ["test_case_writing", "requirement_clarification"],
  "entity_mentions": ["Pet", "Order", "Account"],
  "access_count": 3,
  "usefulness_scores": { "business_rules": { "total": 2, "useful": 2 } }
}
```

---

### DocumentHypergraph (`kb_gen/hypergraph/structure.py`)

Directed graph persisted at `KB/graph/hypergraph.json` with atomic `.backup.json`.

**Nodes** — one per ingested document:
```json
{
  "artifact_id": "20240901_...",
  "name": "business_rules.json",
  "artifact_type": "business_rules",
  "service": "jpetstore-6",
  "tags": ["pet", "inventory"]
}
```

**Edges** — relationships between documents:

| edge_type | Meaning |
|-----------|---------|
| `references` | A cites B |
| `informs` | A provides context for B |
| `supersedes` | A replaces B |
| `related` | General relationship |

Key methods:
- `add_node(artifact_id, metadata)` — upsert
- `add_edge(from_id, to_id, edge_type, weight)` — deduplicated via `_edge_key_index`
- `find_related(artifact_id, max_depth=2)` — BFS traversal, returns related IDs

**Legacy format compatibility:** Older `hypergraph.json` files use `source`/`target`/`type` for edges and a list for `nodes`. The loader normalizes both schemas on load automatically.

---

### ChromaDBStore (`kb_gen/embeddings/chromadb_embedder.py`)

Persistent ChromaDB collection at `kb_store/`, cosine similarity.

- Collection name: `kb_documents` (configurable)
- Embedding chain: `VegasEmbeddingFunction` → tries `pyvegas` Gemini first, falls back to `LocalEmbedder`
- `LocalEmbedder`: tries sentence-transformers `all-MiniLM-L6-v2`; falls back to SHA-256 hash embeddings when HuggingFace is unreachable
- Scores: cosine similarity 0–1 (1 = identical), converted from ChromaDB L2 distance: `score = 1.0 - dist/2.0`

---

### BRDChunker (`kb_gen/ingestion/brd_chunker.py`)

Used for artifact types: `brd`, `business_rules`, `journey_map`.

- Splits on `^#{1,3}` headings (regex)
- `max_chars=1400`, `overlap_chars=180`, `max_chunks=5000`
- Returns list of `{chunk_id, text, char_start, char_end, heading}`

---

### IntentClassifier (`kb_gen/rag/intent_classifier.py`)

Sends up to 80 document names to Claude. Expects JSON response:
```json
{"intent": "business_rules", "relevant_docs": ["business_rules.json"], "confidence": "HIGH"}
```

- Maps doc names → `artifact_id` via `registry.get_name_to_id_map()`
- Exponential backoff: 1s → 2s → 4s (up to `KB_RAG_INTENT_MAX_RETRIES`, default 3)

---

### LateChunker (`kb_gen/rag/late_chunking.py`)

Post-retrieval step: splits each candidate document into sentence-boundary windows and scores each window by keyword overlap with the query. Returns top-N windows as snippets with surrounding context sentences.

---

### LocalRAG (`kb_gen/rag/local_rag.py`)

TF-IDF fallback when all vector search scores are below 0.3. Searches over registry metadata: `name`, `description`, `tags`, `entity_mentions`, `useful_for`. Returns normalized scores 0–1.

---

### ConversationStore (`kb_gen/rag/conversation_store.py`)

Persists session history at `KB/hitl/conversations/<session_id>.json`. Atomic writes.  
Methods: `add_turn`, `get_history`, `get_last_n`, `clear_session`.

---

### FeedbackStore + AnnotationTool (`kb_gen/hitl/`)

`FeedbackStore` appends to `KB/hitl/feedback.json`. Each record:
```json
{
  "artifact_id": "...",
  "query": "What are the business rules?",
  "intent": "business_rules",
  "useful": true,
  "note": "Covered all edge cases",
  "timestamp": "2024-09-01T12:00:00Z"
}
```

Feedback propagates to `registry.update_usefulness()` so high-usefulness documents get boosted in future rankings.

`AnnotationTool` is an interactive CLI loop: shows each source, prompts `y/n/s` (skip), delegates to FeedbackStore.

---

## Artifact Types

Detected automatically from filename and content keywords:

| artifact_type | Filename keywords | Content keywords |
|--------------|-------------------|-----------------|
| `brd` | brd, business_requirement | brd, business_requirement |
| `journey_map` | journey, flow | journey, flow |
| `business_rules` | rules, business_rule | rules, business_rule |
| `api_spec` | api, swagger, openapi | api, swagger, openapi |
| `gap_analysis` | gap | gap |
| `risk_register` | risk | risk |
| `feature_flag` | feature_flag, feature_toggle | feature_flag, feature_toggle |
| `document` | (default) | (default) |

---

## FastAPI Endpoints (`bin/api_server.py`)

Starts on port 8081 (override with `PORT` env var).

### Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest/service/{name}` | Ingest a single service folder |
| POST | `/ingest/document` | Ingest a single file — body: `{file_path, service}` |
| POST | `/ingest/reset` | Clear all registry + embeddings |

### Query

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Full RAG pipeline — body: `{question, session_id?}` |
| POST | `/query/local` | TF-IDF only, no LLM — body: `{question}` |

### Registry

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/registry/documents` | All documents (optional `?service=` filter) |
| GET | `/registry/documents/{id}` | Single document by artifact_id |
| DELETE | `/registry/documents/{id}` | Remove a document |
| GET | `/registry/services` | List all services |

### Graph

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/graph/nodes` | All hypergraph nodes |
| GET | `/graph/edges` | All hypergraph edges |
| GET | `/graph/related/{id}` | BFS-related nodes for a given artifact_id |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | `{"status":"ok","registry_count":N,"embeddings_count":N}` |
| GET | `/config` | Current `KBStoreConfig` values |

---

## Configuration (`kb_gen_config.yaml`)

```yaml
kb_root: KB                             # Where service folders live
registry_path: registry/documents.json # Document catalog
embeddings_db_path: kb_store           # ChromaDB persistent path
graph_path: KB/graph/hypergraph.json   # Hypergraph JSON

anthropic_model: claude-haiku-4-5-20251001  # LLM model
top_k_sources: 5                            # Sources returned per query
use_graph_expansion: true                   # BFS expansion via hypergraph
strict_grounded: true                       # Only answer from provided sources
use_brute_force_threshold: 0.3             # LocalRAG fallback threshold

json_ingestion_enabled: true               # Ingest .json files
brd_chunking_enabled: true                 # Chunk BRD/rules/journey docs
```

---

## Supported KB Services (Current)

| Service | Documents | Chunks |
|---------|-----------|--------|
| docusaurus | 30 | ~390 |
| jpetstore-6 | 15 | ~195 |
| library-management | 30 | ~390 |
| Library-Management-System-JAVA-master | 30 | ~390 |
| **Total** | **105** | **~1316** |

---

## Streamlit UI (`app.py`)

The RAG Chat tab:
- Connects to ChromaDB via `tools/adapters/chromadb_adapter.py`
- Discovers collections matching `brd_<repo_name>` pattern (different from `kb_documents` used by `bin/ingest.py`)
- Streams Claude responses via `client.messages.stream()`
- Shows source citations with relevance scores

The sidebar lets you select a repository and enter your API key (`.env` value is used automatically if present).

> **Note:** Streamlit uses `brd_<repo>` collection naming. `bin/ingest.py` writes to `kb_documents`. Use the Agent 9 button in the UI to run Streamlit-specific ingestion.

---

## Further Reading

- [Setup & Commands](getting-started.md) — Installation, CLI commands, troubleshooting
