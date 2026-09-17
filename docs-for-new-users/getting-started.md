# Getting Started — Guide & Commands

> Setup, commands, and troubleshooting for the BRD Agent Framework.

---

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.10 – 3.12 recommended (3.13 works with limitations) | `python --version` |
| pip | Latest | `pip --version` |
| Anthropic API Key | — | See below |

> **Python 3.13:** `pyvis` (graph visualization) has no wheels for 3.13. Everything else works. Use Python 3.12 if you need graph visualization.

> **Corporate network (e.g., Cognizant):** HuggingFace is blocked by SSL inspection. The system automatically falls back to hash-based embeddings — the pipeline runs fully offline. Search rankings are approximate but answers remain accurate.

---

## API Key Setup

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```



```powershell
Set-Content -Path .env -Value "ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE" -Encoding UTF8
```

---

## Repository Layout

```
BRD_agent/
├── app.py                      # Streamlit UI entry point
├── .env                        # API key (create this — not in git)
├── kb_gen_config.yaml          # Master configuration
├── requirements.txt
│
├── bin/                        # CLI entry points
│   ├── ingest.py               # Document ingestion
│   ├── query.py                # RAG query CLI
│   ├── annotate.py             # HITL annotation
│   └── api_server.py           # FastAPI REST server (port 8081)
│
├── kb_gen/                     # Core Python library
│   ├── core/                   # Config loader
│   ├── storage/                # Document registry
│   ├── hypergraph/             # Graph structure
│   ├── embeddings/             # ChromaDB + local embedder
│   ├── ingestion/              # File walker, BRD chunker
│   ├── graph/                  # Graph walker
│   ├── rag/                    # Hybrid RAG pipeline
│   └── hitl/                   # Human-in-the-loop feedback
│
├── KB/                         # Knowledge Base output (auto-generated)
│   ├── <service-name>/         # BRD artifacts per service
│   └── graph/
│       └── hypergraph.json     # Cross-service relationship graph
│
├── registry/
│   └── documents.json          # Document catalog with metadata
│
├── kb_store/                   # ChromaDB vector store (auto-generated)
├── logs/
│   └── ingestion_progress.json # SHA-256 change detection checkpoint
├── config/
│   └── config.yaml             # Tool adapter config
└── tools/
    └── adapters/
        └── chromadb_adapter.py # ChromaDB adapter used by Streamlit UI
```

---

## Installation

```powershell
cd C:\Users\<you>\Workspace\BRD_agent
pip install -r requirements.txt
```

Corporate network / SSL errors:

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

## Full End-to-End Flow

Follow these steps in order the first time.

### 1 — Create `.env`

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

### 2 — Ingest the Knowledge Base

```powershell
python bin/ingest.py --all
```

Expected output:
```
[LocalEmbedder] sentence-transformers model unavailable. Using hash-based fallback embeddings.
  [OK] Ingested: business_rules.json [business_rules]
  [OK] Ingested: COMPREHENSIVE_BRD_docusaurus.md [brd]
  ...
[OK] Service 'docusaurus': 30 ingested, 0 skipped, 0 errors
```

Ingest a single service:
```powershell
python bin/ingest.py docusaurus
```

### 3 — Run a test query

```powershell
python bin/query.py "What are the acceptance criteria?"
```

Expected output:
```
Querying: What are the acceptance criteria?
Intent: acceptance_criteria  |  Confidence: HIGH
Method: vector  |  Sources: 5
------------------------------------------------------------
Based on the provided sources...
------------------------------------------------------------
Sources:
  [1] acceptance_criteria_gherkin.json (score: 0.7103)
```

### 4 — Start the API server

```powershell
python bin/api_server.py
```

Server starts at `http://localhost:8081`. Verify:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8081/health').read().decode())"
# → {"status":"ok","registry_count":105,"embeddings_count":1316}
```

### 5 — Launch the Streamlit UI

```powershell
python -m streamlit run app.py
# → http://localhost:8501
```

Port conflict:
```powershell
python -m streamlit run app.py --server.port 8502
```

---

## Re-ingesting After Adding New KB Documents

SHA-256 change detection skips unchanged files automatically.

```powershell
python bin/ingest.py --all
```

---

## Interactive Query (REPL)

```powershell
python bin/query.py
# → KB RAG Query — interactive mode (Ctrl+C to exit)
# Question: What business rules apply to pet ownership?
```

---

## HITL Annotation

Annotate query results as useful/not-useful to improve rankings over time:

```powershell
python bin/annotate.py --query "What are the acceptance criteria?"
```

Feedback stored at `KB/hitl/feedback.json`, updates usefulness scores in the registry.

---

## API Server Commands

All endpoints run at `http://localhost:8081`.

```powershell
# Health check
curl http://localhost:8081/health

# Full RAG query
curl -X POST http://localhost:8081/query `
  -H "Content-Type: application/json" `
  -d '{"question": "What are the acceptance criteria for jpetstore?"}'

# TF-IDF only (no LLM)
curl -X POST http://localhost:8081/query/local `
  -H "Content-Type: application/json" `
  -d '{"question": "pet inventory rules"}'

# List all services
curl http://localhost:8081/registry/services

# All documents for a service
curl "http://localhost:8081/registry/documents?service=jpetstore-6"

# Ingest a new service folder
curl -X POST http://localhost:8081/ingest/service/my-new-service

# Graph: related nodes for an artifact
curl http://localhost:8081/graph/related/<artifact_id>

# Current config
curl http://localhost:8081/config
```

---

## Adding a New Service

1. Run the BRD pipeline on the source repo — produces `KB/<service-name>/*.json` and `*.md`.
2. Ingest:
   ```powershell
   python bin/ingest.py <service-name>
   ```
3. Verify:
   ```powershell
   curl http://localhost:8081/registry/services
   curl "http://localhost:8081/registry/documents?service=<service-name>"
   ```

No config changes needed — services are auto-discovered from `KB/` subdirectories.

---

## Key File Locations

| File | Purpose |
|------|---------|
| `.env` | API key — never commit |
| `kb_gen_config.yaml` | Master config: kb_root, model, top_k, graph paths |
| `config/config.yaml` | Tool adapter config (ChromaDB path, agent settings) |
| `KB/<service>/` | BRD artifact output |
| `registry/documents.json` | Document catalog with LLM-enriched metadata |
| `KB/graph/hypergraph.json` | Cross-service relationship graph |
| `kb_store/` | ChromaDB persistent vector store |
| `logs/ingestion_progress.json` | SHA-256 hashes for change detection |
| `KB/hitl/feedback.json` | HITL annotation feedback |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY not set` | Create `.env` in project root with the key |
| `HuggingFace SSL certificate error` | Expected on corporate networks — hash-based fallback runs automatically |
| `list indices must be integers or slices, not str` | Old `hypergraph.json` format — delete `KB/graph/hypergraph.json` and re-run ingest |
| `UnicodeEncodeError` on Windows terminal | Fixed in current code — all Unicode symbols replaced with ASCII |
| Port 8501 already in use | Use `--server.port 8502` or `taskkill /F /PID <pid>` |
| Port 8081 already in use | Set `$env:PORT=8082` then run `api_server.py` |
| `fastapi` not found | `pip install -r requirements.txt` |
| pip SSL error on corporate network | Add `--trusted-host pypi.org --trusted-host files.pythonhosted.org` |
| `pyvis` install fails on Python 3.13 | Expected — no Python 3.13 wheels; commented out in requirements.txt |
| Streamlit RAG Chat shows "No vector store found" | Run `python bin/ingest.py --all` first, then refresh |
| All queries return LOW confidence | Hash-based embeddings; rankings are approximate but functional |
| Ingest hangs with SSL retries | `HF_HUB_OFFLINE=1` is now set automatically in all `bin/` scripts |
| API server exits immediately | Normal in some shells — check with `curl http://localhost:8081/health` |
| Streamlit "No vector store found" (persists) | Streamlit uses `brd_<repo>` collections; `bin/ingest.py` uses `kb_documents`. Use Agent 9 button in the UI for Streamlit-specific ingest |

---

## Further Reading

- [Architecture & Pipeline Internals](kb-store-guide.md) — How the system works end to end
