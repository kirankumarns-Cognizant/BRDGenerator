# Architecture & Pipeline Internals

> Deep dive into how the BRD Agent system works under the hood.

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ USER INTERFACE LAYER                                │
├─────────────────────────────────────────────────────┤
│ • Streamlit Web UI (http://8501)                    │
│ • REST API Server (http://8081)                     │
│ • CLI Commands (bin/ingest.py, bin/query.py)        │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ APPLICATION LAYER                                   │
├─────────────────────────────────────────────────────┤
│ • Pipeline Orchestrator (9 AI Agents)               │
│ • BRD Generator (Claude LLM)                        │
│ • RAG Query Engine (Hybrid search)                  │
│ • Document Processor (PDF/CSV/MD parsing)           │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ STORAGE & INDEXING LAYER                            │
├─────────────────────────────────────────────────────┤
│ • ChromaDB (Vector embeddings)                      │
│ • Document Registry (JSON metadata)                 │
│ • Hypergraph (Service relationships)                │
│ • File Storage (KB/ directory)                      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ DATA PERSISTENCE LAYER                              │
├─────────────────────────────────────────────────────┤
│ • Filesystem (KB/, logs/, registry/)                │
│ • ChromaDB persistent store (kb_store/)             │
└─────────────────────────────────────────────────────┘
```

---

## 📊 End-to-End Pipeline Flow

### Phase 1: Repository Analysis (Agents 1-7)

```
1. SOURCE CODE
   │
   ├─→ Agent 1: Discovery & Scoping
   │   ├─ Detects frameworks (Spring, Hibernate, etc.)
   │   ├─ Counts components (Controllers, Services, Repos)
   │   ├─ Extracts package structure
   │   ├─ Analyzes dependencies
   │   └─ Output: scope_definition.json, artifact_catalog.json
   │
   ├─→ Agent 2: Journey Mapping
   │   ├─ Maps user workflows
   │   ├─ Identifies actors (User, Admin, System)
   │   ├─ Creates CRUD journeys per entity
   │   └─ Output: journey_map.json, journey_conflicts.json
   │
   ├─→ Agent 3: Business Rules
   │   ├─ Extracts validation rules
   │   ├─ Identifies constraints
   │   ├─ Maps workflows
   │   └─ Output: business_rules.json (8-12 rules)
   │
   ├─→ Agent 4: Gap Analysis
   │   ├─ Detects missing tests (Unit, Integration, E2E)
   │   ├─ Finds documentation gaps
   │   ├─ Analyzes code complexity
   │   └─ Output: gap_analysis.json (5-10 gaps)
   │
   ├─→ Agent 5: Synthesis
   │   ├─ Combines all findings
   │   ├─ Identifies design patterns
   │   └─ Output: synthesis_decisions.json
   │
   ├─→ Agent 6: Acceptance Criteria
   │   ├─ Creates positive test cases
   │   ├─ Creates negative test cases
   │   ├─ Creates boundary test cases
   │   └─ Output: acceptance_criteria.json (20-40 scenarios)
   │
   └─→ Agent 7: Risk & Dependency
       ├─ Assesses technology risks
       ├─ Identifies security issues
       ├─ Finds code quality risks
       └─ Output: risk_register.json (6-10 risks)
```

### Phase 2: BRD Generation (Agent 8)

```
Combined Outputs from Agents 1-7
   │
   ├─→ Agent 8: Comprehensive BRD Builder
   │   ├─ Loads all JSON artifacts
   │   ├─ Extracts actual API endpoints
   │   ├─ Generates diagrams:
   │   │  ├─ Architecture diagram (from components)
   │   │  ├─ Data flow diagram (from call chain)
   │   │  ├─ Sequence diagrams (from workflows)
   │   │  └─ Request/Response examples (from entities)
   │   │
   │   ├─ Builds markdown sections:
   │   │  ├─ Executive summary
   │   │  ├─ System overview
   │   │  ├─ Technology stack
   │   │  ├─ Component inventory
   │   │  ├─ API endpoints
   │   │  ├─ Business rules (from artifact)
   │   │  ├─ User journeys (from artifact)
   │   │  ├─ Gap analysis (from artifact)
   │   │  ├─ Risk assessment (from artifact)
   │   │  └─ Acceptance criteria (from artifact)
   │   │
   │   └─ Output: COMPREHENSIVE_BRD_<repo>.md
```

### Phase 3: Indexing & Search (Agent 9)

```
All BRD Artifacts (25+ JSON/MD files)
   │
   └─→ Agent 9: KB Store Sync
       ├─ Reads KB/<repo>/*.json and *.md
       ├─ Extracts semantic chunks
       ├─ Embeds vectors (ChromaDB)
       ├─ Updates document registry
       ├─ Builds hypergraph (service relationships)
       └─ Enables RAG search

Result: Artifacts searchable via:
   • Web UI: "RAG Chat" tab
   • CLI: python bin/query.py "question"
   • API: POST /query
```

---

## 💾 Storage Structure

### `KB/` Directory (Main Output)

```
KB/
├── MyRepo/                              # One directory per analyzed repo
│   ├── scope_definition.json            # What is this system?
│   ├── artifact_catalog.json            # All source files catalogued
│   ├── dependency_map.json              # External dependencies
│   ├── business_rules.json              # 8-12 business rules (JSON)
│   ├── actors.json                      # User roles detected
│   ├── journey_map.json                 # 8-10 user journeys
│   ├── gap_analysis.json                # 5-10 gaps (testing/docs/code)
│   ├── risk_register.json               # 6-10 risks with mitigation
│   ├── acceptance_criteria.json         # 20-40 test scenarios
│   ├── acceptance_criteria_gherkin.json # Gherkin format tests
│   ├── COMPREHENSIVE_BRD_MyRepo.md      # Final markdown BRD
│   ├── brd_executive_summary.md         # Executive summary
│   ├── _uploaded_documents/             # Supporting docs (if uploaded)
│   │   ├── specification.pdf
│   │   ├── requirements.md
│   │   └── design.csv
│   │
│   └── [15 more analysis files...]
│
├── graph/
│   ├── hypergraph.json                  # Cross-repo relationships
│   ├── hypergraph.backup.json           # Previous version
│   └── versions.json                    # Version history
│
└── [other repos...]
```

### `registry/` Directory (Search Index)

```
registry/
└── documents.json                       # Catalog of all indexed documents
    {
      "services": {
        "MyRepo": {
          "name": "MyRepo",
          "documents": [
            {
              "id": "scope_definition",
              "type": "artifact",
              "file": "scope_definition.json",
              "size": 2048,
              "last_updated": "2026-09-15T12:00:00"
            },
            {
              "id": "business_rules",
              "type": "artifact",
              "file": "business_rules.json",
              ...
            }
          ]
        }
      }
    }
```

### `kb_store/` Directory (Vector Embeddings)

```
kb_store/                               # ChromaDB persistent storage
├── chroma.sqlite3                      # Embedding database
├── embeddings.parquet                  # Vector data
└── metadata/
    └── [ChromaDB internals]

Contains:
• Vector embeddings for all document chunks
• Semantic search indices
• Collections for each repo (kb_brd_MyRepo, kb_documents, etc.)
```

---

## 🔄 Agent Execution Details

### What Each Agent Does

| Agent | Input | Process | Output | Files |
|-------|-------|---------|--------|-------|
| **1** | Source code | Scans files, detects frameworks, maps components | System overview, tech stack | 9 JSON files |
| **2** | Code structure | Analyzes flows, identifies actors | User workflows, journeys | 3 JSON files |
| **3** | Code logic | Extracts rules from validators/services | Business rules | 2 JSON files |
| **4** | File analysis | Checks test files, docs, complexity | Missing features/tests/docs | 4 JSON files |
| **5** | Outputs 1-4 | Synthesizes findings | Design decisions, flags | 2 JSON files |
| **6** | Code structure | Creates test scenarios | Acceptance criteria | 2 JSON files |
| **7** | Tech stack, code | Identifies risks | Risk register with mitigation | 4 JSON files |
| **8** | Outputs 1-7 | Generates comprehensive BRD | Markdown + diagrams | 1 markdown + supporting files |
| **9** | All outputs | Embeds into ChromaDB | Searchable index | Vector store + registry |

### Agent Parallelization

Agents 1-7 run **sequentially** (each depends on previous output):
```
Agent 1 (90s) → Agent 2 (60s) → Agent 3 (45s) → Agent 4 (45s) → 
Agent 5 (30s) → Agent 6 (60s) → Agent 7 (45s) → Agent 8 (30s) → Agent 9 (15s)

Total: ~7-8 minutes for typical repo
```

---

## 🔍 RAG Search System

### How Search Works

When user asks: *"What are the main risks?"*

```
┌────────────────────────────────┐
│ "What are the main risks?"     │
└──────────────┬─────────────────┘
               │
               ├─→ Intent Detection
               │   "risks" → Intent = "risk_assessment"
               │
               ├─→ Vector Search
               │   • Embed query
               │   • Find top 5 matching chunks
               │   • From risk_register.json
               │
               ├─→ Keyword Search (Fallback)
               │   • Search for "risk", "critical", "high"
               │   • In business_rules.json, gap_analysis.json
               │
               ├─→ Combine Results
               │   • Weight vector (70%) + keyword (30%)
               │   • Re-rank by relevance
               │   • Take top 3 sources
               │
               ├─→ LLM Synthesis
               │   • Send sources to Claude
               │   • "Answer this question using these sources"
               │
               └─→ Return Answer
                   "CRITICAL: No Spring Security (leads to unauthorized access)
                    HIGH: 50+ dependencies (transitive vulnerabilities)
                    HIGH: No API documentation (developer confusion)"
```

### Search Collections in ChromaDB

```
For each repository:
├── kb_brd_<repo>           # Comprehensive BRD content
├── kb_documents            # All artifact documents
├── kb_gaps                 # Gap analysis details
├── kb_risks                # Risk register
├── kb_rules                # Business rules
└── kb_journeys             # User journey definitions
```

---

## 🔗 Hypergraph (Multi-Repo Relationships)

For teams with multiple services:

```
hypergraph.json contains:
{
  "nodes": [
    {"id": "UserService", "type": "microservice", "repo": "user-service"},
    {"id": "OrderService", "type": "microservice", "repo": "order-service"},
    {"id": "PaymentService", "type": "microservice", "repo": "payment-service"}
  ],
  "edges": [
    {"from": "OrderService", "to": "PaymentService", "type": "calls"},
    {"from": "UserService", "to": "OrderService", "type": "publishes_events"}
  ]
}
```

**Enables queries like:**
- *"What services does UserService depend on?"*
- *"What breaks if PaymentService goes down?"*
- *"Show me all payments flowing through the system"*

---

## 📥 Ingestion Process

### When You Upload a Repo

```
1. Upload ZIP (5 MB repo)
   ↓
2. Extract to Sample_Repos/<repo-name>/
   ↓
3. Pipeline runs (9 agents)
   ↓
4. Outputs saved to KB/<repo-name>/
   └─ 25-30 JSON and markdown files
   ↓
5. Run: python bin/ingest.py <repo-name>
   ├─ Read KB/<repo-name>/*.json and *.md
   ├─ Split into semantic chunks (300 tokens each)
   ├─ Embed with ChromaDB
   ├─ Update registry/documents.json
   └─ Build hypergraph relationships
   ↓
6. Index ready for search!
```

### SHA-256 Change Detection

```
logs/ingestion_progress.json tracks:
{
  "business_rules.json": "a3b2c1d...",
  "gap_analysis.json": "f9e8d7c...",
  "journey_map.json": "5a4b3c2..."
}

Next ingest:
• Computes SHA-256 of each file
• Skips if hash matches (unchanged)
• Re-ingests only modified files
• Saves time on large KBs
```

---

## 🔌 API Endpoints (FastAPI)

### Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Server health check |
| POST | `/query` | Full RAG query (LLM + search) |
| POST | `/query/local` | TF-IDF search only (no LLM) |
| GET | `/registry/services` | List all analyzed repos |
| GET | `/registry/documents?service=X` | Get all docs for a repo |
| POST | `/ingest/service/<name>` | Re-ingest a service |
| GET | `/graph/related/<artifact-id>` | Related nodes in hypergraph |
| GET | `/config` | Current configuration |

### Example: Query via API

```powershell
curl -X POST http://localhost:8081/query `
  -H "Content-Type: application/json" `
  -d @- <<EOF
{
  "question": "What are the acceptance criteria?",
  "service": "MyRepo",
  "top_k": 5
}
EOF

Response:
{
  "answer": "Acceptance criteria include...",
  "confidence": 0.92,
  "sources": [
    {
      "document": "acceptance_criteria.json",
      "score": 0.87,
      "excerpt": "AC-001: User can create order..."
    }
  ]
}
```

---

## ⚙️ Configuration

### `kb_gen_config.yaml` (Master Config)

```yaml
# LLM Settings
llm:
  model: "claude-3.5-sonnet"
  max_tokens: 2000
  temperature: 0.7

# Search Settings
search:
  top_k: 5
  hybrid_weight: 0.6  # 60% vector, 40% keyword

# Paths
paths:
  kb_root: "./KB"
  registry: "./registry"
  kb_store: "./kb_store"
  logs: "./logs"

# Embedding
embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  fallback: "hash-based"  # On corporate networks
  chunk_size: 300
  chunk_overlap: 50
```

### `config/config.yaml` (Tool Adapter Config)

```yaml
# ChromaDB adapter for Streamlit
chromadb:
  path: "./kb_store"
  collection_prefix: "kb_"

# Agent settings
agents:
  enabled: [1, 2, 3, 4, 5, 6, 7, 8, 9]
  parallel: false  # Sequential for dependencies
  timeout_seconds: 3600
```

---

## 🚀 Performance Considerations

### Typical Times

| Operation | Time | Scale |
|-----------|------|-------|
| Agent 1-7 (code analysis) | 7-8 min | 1000 LOC repo |
| Agent 8 (BRD generation) | 30 sec | All analysis |
| Agent 9 (indexing) | 15 sec | 25 artifacts |
| Vector embedding | 2-5 sec | Per query |
| **Total pipeline** | **~10 min** | **First run** |
| Re-ingest (changed files only) | 1-2 min | Incremental |

### Optimization

- **Parallel agents**: Agents 1-7 currently sequential (could be parallelized)
- **Caching**: SHA-256 prevents re-processing unchanged files
- **Vector search**: ChromaDB is fast (~200ms per query)
- **LLM calls**: Rate-limited by Anthropic API (5 requests/min for free tier)

---

## 🔐 Security Considerations

**What's stored:**
- ✅ Code structure analysis (no source code itself)
- ✅ Extracted rules, journeys, risks (no secrets)
- ✅ Dependencies list (public)
- ✅ Test coverage analysis

**NOT stored:**
- ❌ Actual source code
- ❌ API keys or credentials
- ❌ Hardcoded secrets
- ❌ User data or passwords

**API Key Security:**
- Store in `.env` file (never in git)
- Loaded at runtime only
- Used for Claude API calls only
- Not stored in KB or logs

---

## 📈 Scalability

### Single Repository
- ✅ Supports up to 100K LOC
- ✅ 25-30 output files
- ✅ ~10-15 MB total storage

### Multiple Repositories
- ✅ Unlimited services
- ✅ Hypergraph links all services
- ✅ Cross-service search works
- ✅ Registry tracks relationships

### Limits
- ⚠️ ChromaDB: ~1M embeddings per instance
- ⚠️ Hypergraph: ~10K nodes (relationships)
- ⚠️ Query time: ~2-5s (with LLM synthesis)

---

**Ready to dive deeper? Explore the codebase with the architecture in mind!**
