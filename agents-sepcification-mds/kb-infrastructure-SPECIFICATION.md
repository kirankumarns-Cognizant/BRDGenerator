# System Specification & Architecture Blueprint

## 1. Project Overview & System Goals

This module implements the Knowledge Base (KB) Store and RAG (Retrieval-Augmented Generation) infrastructure within the KnowledgebaseVegas platform. It is the shared knowledge layer that all other agents — Forward Engineering, ADLC, Requirement Breakdown — use to store, index, retrieve, and query business documents (BRDs, journey maps, API specs, feature flags, etc.).

Primary goals:
- Ingest documents from service folders into a structured catalog with rich metadata.
- Maintain a `DocumentRegistry` (JSON catalog) that tracks every indexed document with full metadata including artifact type, service, domain, tags, usage history, and hypergraph node ID.
- Build a `DocumentHypergraph` of relationships between documents across services (persisted as `KB/graph/hypergraph.json`).
- Embed documents using a vector embedding service (Gemini-backed `VegasEmbeddingService` via ChromaDB), with SHA256 change detection to avoid re-embedding unchanged documents.
- Provide a hybrid RAG query pipeline: intent classification (LLM) → vector retrieval → graph expansion → optional reranking → answer generation.
- Support `LateChunker` for contextual chunk generation and a `LocalRAG` fallback for offline/no-embedding use cases.
- Track usage telemetry per document (access count, query intents, usefulness scores) for adaptive retrieval.
- Expose a FastAPI server and a Streamlit UI for interactive querying.

Target runtime:
- Python 3.10+.
- Local execution on Windows, macOS, or Linux.
- API mode via FastAPI + Uvicorn.
- UI mode via Streamlit.
- CLI mode via `bin/` scripts.
- Configured via `kb_gen_config.yaml` plus `.env`.

---

## 2. Tech Stack & Dependencies

### Core stack
- Language: Python.
- Vector DB: ChromaDB (`chromadb>=0.5.0`).
- Embeddings: `sentence-transformers>=3.0.0`; also `VegasEmbeddingService` (Gemini-backed, from `pyvegas.langx.emas`).
- LLM (for intent classification and answer generation): Anthropic SDK (`anthropic>=0.40.0`). Fallback to `get_anthropic_client()` helper.
- Graph: NetworkX (`networkx>=3.0`), PyVis (`pyvis>=0.3.0`) for visualization.
- API layer: FastAPI (`fastapi>=0.115.0`), Uvicorn (`uvicorn>=0.32.0`), HTTPX.
- UI: Streamlit (`streamlit>=1.40.0`).
- Config: PyYAML, python-dotenv.
- Utilities: Rich, jsonschema, tiktoken.

### Required Python packages (`requirements.txt`)
- `anthropic>=0.40.0`
- `pyyaml>=6.0.1`
- `python-dotenv>=1.0.0`
- `sentence-transformers>=3.0.0`
- `chromadb>=0.5.0`
- `numpy>=1.24.0`
- `networkx>=3.0`
- `pyvis>=0.3.0`
- `fastapi>=0.115.0`
- `uvicorn>=0.32.0`
- `httpx>=0.27.0`
- `streamlit>=1.40.0`
- `rich>=13.9.0`
- `jsonschema>=4.23.0`
- `tiktoken>=0.7.0`

### Configuration (`kb_gen_config.yaml`)
Key fields:
- KB root path, registry path, embeddings DB path.
- Embedding model name (e.g., `gemini-embedding-001`), output dimensionality.
- Anthropic model name for intent classification and answer generation.
- BRD chunking settings: `brd_chunk_max_chars`, `brd_chunk_overlap_chars`, `brd_chunk_max_per_document`.
- JSON ingestion settings: `json_ingestion_enabled`, `json_included_files`.
- RAG settings: `top_k_sources`, `use_graph_expansion`, `strict_grounded`.
- Reranker: enabled/disabled via `KB_STORE_ENABLE_RERANKER` env var.

### Runtime prerequisites
- `ANTHROPIC_API_KEY` in `.env` or environment.
- ChromaDB writable directory at configured `embeddings_db_path`.
- Optional: `pyvegas` package for `VegasEmbeddingService`; falls back to `sentence-transformers` if absent.
- Optional: `KB_STORE_ENABLE_RERANKER=true` to enable `BAAI/bge-reranker-base` cross-encoder reranking.

---

## 3. Project Directory Structure

### `kb_gen/` package

```
kb_gen/
  __init__.py              ← exports KBStoreConfig, DocumentRegistry, RAGQueryEngine, KBLogger
  core/
    config_loader.py       ← KBStoreConfig: load + validate kb_gen_config.yaml
    metadata_schema.py     ← DocumentMetadata: all tracked fields per document
  storage/
    registry.py            ← DocumentRegistry: catalog of all ingested documents
  ingestion/
    ingestor.py            ← DocumentIngestor: walk service folders, enrich metadata, register
    brd_chunker.py         ← BRDChunker: split BRDs into overlapping chunks
  embeddings/
    chromadb_embedder.py   ← ChromaDBStore + VegasEmbeddingFunction: vector store operations
    local_embedder.py      ← LocalEmbedder: sentence-transformers fallback
    api_embedder.py        ← API-backed embedder
    smart_cache.py         ← SHA256 change-detection cache for embeddings
  hypergraph/
    structure.py           ← DocumentHypergraph: cross-service document relationship graph
  graph/
    graph_walker.py        ← GraphWalker: graph expansion during RAG retrieval
  rag/
    query_engine.py        ← RAGQueryEngine: hybrid RAG orchestrator
    intent_classifier.py   ← IntentClassifier: LLM-based intent + relevant docs
    context_graph.py       ← ContextGraph: query-session relationship graph
    local_rag.py           ← LocalRAG: TF-IDF fallback retrieval (no vector DB)
    late_chunking.py       ← LateChunker: contextual chunk generation
    simple_search.py       ← SimpleSearch: keyword search helper
    conversation_store.py  ← ConversationStore: multi-turn conversation history
  utils/
    logger.py              ← KBLogger: structured logging
    api_client.py          ← get_anthropic_client(): fallback-aware Anthropic client
    artifact_id.py         ← generate_artifact_id(): UUID generator
  hitl/
    ...                    ← HITL feedback and annotation tools
  tests/
    ...                    ← test suite
```

### KB storage structure
```
KB/
  <service_name>/           ← one folder per service
    *.md, *.json, *.docx    ← source documents
  graph/
    hypergraph.json         ← DocumentHypergraph (nodes + edges)
    hypergraph.backup.json  ← backup copy
  embeddings/               ← ChromaDB persistent store
registry/
  documents.json            ← DocumentRegistry catalog
logs/
  ingestion_progress.json   ← ingestion progress checkpoint
```

---

## 4. Data Schemas, Interfaces & State

### `DocumentMetadata` (all fields tracked per document)

**Base fields** (from artifact info):
- `artifact_id: str` — UUID.
- `name`, `original_filename`: file names.
- `artifact_type`: e.g., `journey_map`, `business_rules`, `brd`, `api_spec`, `feature_flag`.
- `producer_agent`, `producer_run_id`: which agent and run produced this.

**Classification:**
- `service`, `brand`, `domain`, `feature`.

**Document properties:**
- `version`, `format` (json, md, docx, etc.), `file_path`, `confidence` (HIGH/MEDIUM/LOW).

**Timestamps:** `created_at`, `updated_at` (ISO datetime).

**Lineage:**
- `client`, `derived_from: List[str]` (artifact IDs this derives from).

**LLM-enriched fields:**
- `description`, `tags: List[str]`, `useful_for: List[str]`, `entity_mentions: List[str]`, `notes`.

**Usage tracking (updated by RAG):**
- `used_for: List[str]`, `query_intents: List[str]`, `access_count: int`, `last_accessed`.
- `usefulness_scores: Dict[str, {total, useful}]`.

**Cross-service:**
- `alias: List[str]`, `entity_tags: List[str]`, `cross_service_references: List[{service, doc_id}]`.

**Hypergraph:**
- `hypergraph_node_id: str`.

### `DocumentRegistry` schema (`registry/documents.json`)
```json
{
  "documents": {
    "<artifact_id>": { ...DocumentMetadata fields... }
  },
  "services": {
    "<service_name>": ["<artifact_id>", ...]
  }
}
```

### `DocumentHypergraph` schema (`KB/graph/hypergraph.json`)
```json
{
  "nodes": {
    "<artifact_id>": {
      "artifact_id": "...",
      "name": "...",
      "artifact_type": "...",
      "service": "...",
      "tags": []
    }
  },
  "edges": [
    {
      "from": "<artifact_id>",
      "to": "<artifact_id>",
      "edge_type": "references|informs|supersedes|related",
      "weight": 1.0
    }
  ]
}
```

### `RAGQueryEngine` query result
```python
{
  "answer": str,
  "sources": [{"artifact_id", "name", "service", "snippet", "score"}],
  "intent": str,
  "confidence": "HIGH"|"MEDIUM"|"LOW",
  "retrieval_method": "vector"|"graph"|"local"|"hybrid",
  "telemetry": {...}
}
```

### Configuration: `KBStoreConfig`
- Loads from `kb_gen_config.yaml` with env var overrides (`KB_GEN_CONFIG_PATH`, `KB_GEN_BASE_DIR`).
- Candidate path discovery: CWD, `bin/`, env var, repo root walk.
- Exposes validated config values via attributes.

---

## 5. Functional Modules & Implementation Details

### 5.1 Document Ingestion

#### `ingestion/ingestor.py` — `DocumentIngestor`

`__init__`:
- Accepts `registry`, `hypergraph`, `kb_root`, `model`, `vector_store`.
- `brd_chunking_enabled`: if true, creates `BRDChunker` for splitting BRD files.
- `json_ingestion_enabled` / `json_included_files`: controls JSON file inclusion.
- Writes progress to `logs/ingestion_progress.json` via atomic tmp-file swap.

Ingestion flow per document:
1. Walk `KB/<service>/` for matching file extensions.
2. Compute SHA256 hash of file content for change detection.
3. If already embedded and hash unchanged: skip.
4. Read file content.
5. Call LLM to enrich metadata (`description`, `tags`, `useful_for`, `entity_mentions`).
6. If BRD: chunk with `BRDChunker`.
7. Embed chunks/document with `vector_store`.
8. Register metadata in `DocumentRegistry`.
9. Add node to `DocumentHypergraph`.

#### `ingestion/brd_chunker.py` — `BRDChunker`
- Splits BRD text into overlapping chunks by heading structure.
- Parameters: `max_chars` (default 1400), `overlap_chars` (default 180), `max_chunks` (default 5000), `min_per_document`.

### 5.2 Vector Store

#### `embeddings/chromadb_embedder.py` — `ChromaDBStore`
- Wraps ChromaDB persistent client.
- `VegasEmbeddingFunction`: ChromaDB `EmbeddingFunction` backed by `VegasEmbeddingService` (Gemini embeddings). Batch size up to 24; retries up to 2 times.
- Falls back to `LocalEmbedder` (sentence-transformers) when `VegasEmbeddingService` is unavailable.
- `add(artifact_id, text, metadata)`: embed and store.
- `query(text, top_k)`: ANN search returning `(artifact_id, score, metadata)` tuples.

#### `embeddings/smart_cache.py`
- Tracks SHA256 hashes of embedded texts.
- `needs_update(artifact_id, text) -> bool`: returns True if text changed or not yet embedded.

### 5.3 Hypergraph

#### `hypergraph/structure.py` — `DocumentHypergraph`
- `add_node(artifact_id, metadata)`: adds or updates a node.
- `add_edge(from_id, to_id, edge_type, weight)`: adds a directed edge; deduplicates via `_edge_key_index`.
- `find_related(artifact_id, edge_types, max_depth) -> List[str]`: graph walk to find related documents.
- Persisted to `KB/graph/hypergraph.json`; backup copy maintained atomically.

### 5.4 RAG Query Pipeline

#### `rag/query_engine.py` — `RAGQueryEngine`

Full query flow:
```
query(question)
  │
  ├─ IntentClassifier.classify_query(question, document_tags)
  │   → (intent_label, relevant_artifact_ids)
  │
  ├─ vector_store.query(question, top_k)
  │   → (artifact_id, score, metadata) list
  │
  ├─ [if use_graph_expansion] GraphWalker.expand(artifact_ids)
  │   → additional related artifact_ids from hypergraph
  │
  ├─ Merge + deduplicate candidates
  │
  ├─ [if enable_reranker] CrossEncoder rerank (BAAI/bge-reranker-base)
  │   → reordered candidates
  │
  ├─ LateChunker.chunk_and_select(candidates, question)
  │   → top chunks with context sentences
  │
  ├─ [if score < use_brute_force_threshold] LocalRAG.search(question)
  │   → TF-IDF fallback results merged
  │
  ├─ Anthropic LLM: answer generation with grounded sources
  │
  └─ Return: {answer, sources, intent, confidence, retrieval_method, telemetry}
```

`strict_grounded`: if True, answer must cite only retrieved sources (no hallucination).

`top_k_sources`: maximum number of sources to include in the answer context (default 5).

#### `rag/intent_classifier.py` — `IntentClassifier`
- `classify_query(query, document_tags) -> (intent_label, List[artifact_ids])`
- Sends doc name list (up to 80) to LLM; expects JSON `{intent, relevant_docs, confidence}`.
- Maps returned doc names back to artifact IDs via `name_to_id` dict.
- Retry logic: up to `KB_RAG_INTENT_MAX_RETRIES` (default 3) with exponential backoff.
- Sanitizes error messages to strip credentials before logging.

#### `rag/late_chunking.py` — `LateChunker`
- `min_chunk_size` (default 150), `max_chunk_size` (default 1500), `context_sentences` (default 3).
- Generates contextual chunks that include surrounding sentence context.

#### `rag/local_rag.py` — `LocalRAG`
- TF-IDF based retrieval directly from `DocumentRegistry`.
- Used as fallback when vector scores are below threshold.

#### `rag/context_graph.py` — `ContextGraph`
- Session-level relationship graph tracking which documents were retrieved together.
- Used to improve retrieval coherence across multi-turn queries.

#### `rag/conversation_store.py` — `ConversationStore`
- Persists multi-turn conversation history for a query session.

### 5.5 Graph Walker

#### `graph/graph_walker.py` — `GraphWalker`
- `__init__(chroma_collection, hypergraph)`.
- `expand(artifact_ids) -> List[str]`: given a seed set of artifact IDs, walks hypergraph edges to find related documents; optionally re-queries ChromaDB for each related node.

### 5.6 Configuration

#### `core/config_loader.py` — `KBStoreConfig`
- Config path discovery: `cwd`, `bin/`, env var `KB_GEN_CONFIG_PATH`, repo root walk.
- Base dir inference: if config is in `bin/` → parent is base. If in `kb_gen/config/` → 2 parents up.
- `_validate()`: checks required fields, known values, path existence.
- Exposes all config values as attributes.

### 5.7 Storage / Registry

#### `storage/registry.py` — `DocumentRegistry`
- `add_document(metadata) -> artifact_id`: replaces existing entry for same `file_path` (dedup by path).
- `get_document(artifact_id) -> Optional[Dict]`.
- `get_service_documents(service) -> List[Dict]`.
- `remove_document(artifact_id)`: removes from `documents` and `services` index.
- `find_artifact_ids_by_file_path(file_path) -> List[str]`: for dedup check.
- Auto-saves on every mutation via `_save()`.

---

## 6. Entry Points & Execution Flow

### Ingestion (CLI)
```
python bin/api_server.py          ← starts FastAPI server on port 8081
python bin/streamlit_app.py       ← starts Streamlit UI
python bin/execute_brd.py         ← ingest a single BRD
python bin/execute_brd_with_repo.py ← ingest BRD + scan repo
```

### Programmatic ingestion
```python
from kb_gen import KBStoreConfig, DocumentRegistry
from kb_gen.ingestion.ingestor import DocumentIngestor
from kb_gen.hypergraph.structure import DocumentHypergraph
from kb_gen.embeddings.chromadb_embedder import ChromaDBStore

config = KBStoreConfig("bin/kb_gen_config.yaml")
registry = DocumentRegistry(config.registry_path)
hypergraph = DocumentHypergraph(config.graph_path)
vector_store = ChromaDBStore(config.embeddings_path)

ingestor = DocumentIngestor(registry, hypergraph, kb_root=config.kb_root, vector_store=vector_store)
ingestor.ingest_service("my-service")
```

### Programmatic query
```python
from kb_gen import RAGQueryEngine, DocumentRegistry

registry = DocumentRegistry()
engine = RAGQueryEngine(registry, embeddings_db_path=config.embeddings_path)
result = engine.query("What are the acceptance criteria for the suspension workflow?")
print(result["answer"])
for src in result["sources"]:
    print(src["name"], src["score"])
```

### Ingestion flow (visual)
```
KB/<service>/*.md|json|docx
  │
  ├─ SHA256 change detection (smart_cache)
  ├─ LLM metadata enrichment (description, tags, useful_for, entity_mentions)
  ├─ BRD chunking (BRDChunker) — if enabled
  ├─ Vector embedding (ChromaDBStore / VegasEmbeddingFunction)
  ├─ DocumentRegistry.add_document()
  └─ DocumentHypergraph.add_node()
```

### Query flow (visual)
```
question
  │
  ├─ IntentClassifier → (intent, [relevant_artifact_ids])
  ├─ ChromaDB ANN search → top-K candidates
  ├─ GraphWalker expansion → related nodes from hypergraph
  ├─ Merge + dedup
  ├─ [opt] CrossEncoder rerank
  ├─ LateChunker → contextual chunks
  ├─ [fallback] LocalRAG (TF-IDF) if scores low
  ├─ Anthropic LLM → grounded answer
  └─ Return {answer, sources, intent, confidence}
```

---

## 7. Testing

### Test suite (`tests/`)
- Unit tests for `DocumentRegistry`, `DocumentHypergraph`, `BRDChunker`, `SmartCache`.
- Integration tests for `DocumentIngestor` (with mock LLM and mock vector store).
- RAG pipeline tests using `LocalRAG` (no vector DB required).

### Running tests
```bash
pytest tests/ -v
```

---

## 8. HITL Feedback Module

### Location: `kb_gen/hitl/`

The HITL (Human-in-the-Loop) module provides annotation and feedback tooling that allows human reviewers to rate retrieval quality and improve adaptive retrieval over time.

### 8.1 Key components

#### `hitl/feedback_store.py` — `FeedbackStore`
- Persists human feedback records to `KB/hitl/feedback.json`.
- `record_feedback(artifact_id, query, useful: bool, note: str)`: appends a feedback entry.
- `get_feedback(artifact_id)`: returns all feedback records for a document.
- Each record: `{artifact_id, query, useful, note, timestamp}`.

#### `hitl/annotation_tool.py` — `AnnotationTool`
- Interactive CLI for reviewing retrieval results and marking documents as useful or not.
- `annotate_query(query, results)`: presents ranked results and prompts the user for a `y/n` rating per source.
- Delegates `record_feedback` calls to `FeedbackStore`.

### 8.2 Usefulness score propagation

After each feedback record is saved, `DocumentRegistry.update_usefulness(artifact_id, query_intent, useful)` increments the document's `usefulness_scores[intent].total` counter and, if `useful=True`, its `.useful` counter. These scores are surfaced in RAG query telemetry and can be used to bias future vector retrieval weights.

### 8.3 Trigger

HITL feedback can be triggered:
- Manually via `python bin/annotate.py --query "..."` after a RAG query session.
- Programmatically by callers that have access to a `FeedbackStore` instance.

---

## 9. FastAPI Server Endpoint Surface

### Server: `bin/api_server.py` — starts FastAPI on port 8081 (configurable)

All endpoints consume and produce JSON unless noted.

#### Ingestion endpoints
| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest/service/{service_name}` | Trigger ingestion of all documents in `KB/<service_name>/`. Returns `{ingested, skipped, errors}`. |
| `POST` | `/ingest/document` | Ingest a single document by `file_path`. Body: `{file_path, service, artifact_type}`. |
| `POST` | `/ingest/reset` | Clear registry, embeddings, and hypergraph for the given service. Body: `{service_name}`. |

#### Query endpoints
| Method | Path | Description |
|---|---|---|
| `POST` | `/query` | Run a RAG query. Body: `{question, top_k?, use_graph_expansion?, strict_grounded?}`. Returns `{answer, sources, intent, confidence, retrieval_method, telemetry}`. |
| `POST` | `/query/local` | Run a TF-IDF-only LocalRAG query without vector DB. Body: `{question, top_k?}`. |

#### Registry endpoints
| Method | Path | Description |
|---|---|---|
| `GET` | `/registry/documents` | List all documents in the registry. Returns `{documents: [DocumentMetadata]}`. |
| `GET` | `/registry/documents/{artifact_id}` | Get a single document's metadata. |
| `GET` | `/registry/services` | List all indexed services. |
| `DELETE` | `/registry/documents/{artifact_id}` | Remove a document from registry and vector store. |

#### Graph endpoints
| Method | Path | Description |
|---|---|---|
| `GET` | `/graph/nodes` | List all hypergraph nodes. |
| `GET` | `/graph/edges` | List all hypergraph edges. |
| `GET` | `/graph/related/{artifact_id}` | Return related artifact IDs from graph walk. Query params: `edge_types`, `max_depth`. |

#### Health and config
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{status: ok, registry_count, embeddings_count}`. |
| `GET` | `/config` | Returns resolved `KBStoreConfig` values (non-secret fields only). |
