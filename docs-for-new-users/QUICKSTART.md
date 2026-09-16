# BRD Agent — Quick Start & Usage Guide

Get BRD Agent running in 5 minutes, then learn how to use it.

---

## What is BRD Agent?

**BRD Agent** automatically analyzes any software repository and generates a comprehensive **Business Requirements Document (BRD)** with:

- ✅ System architecture and components
- ✅ Business rules and workflows  
- ✅ User journeys (8-10 per repository)
- ✅ API endpoints and data flow
- ✅ Acceptance test criteria
- ✅ Risk assessment and gaps
- ✅ Diagrams (architecture, sequence, data flow)

**Use cases:**
- 📊 Onboarding new team members — understand a codebase in 5 minutes
- 🔍 Code review — validate what the system is supposed to do
- 📋 Auto-generate requirements documentation from code
- 🎯 Gap analysis — find missing tests, docs, and features
- ⚠️ Risk assessment — identify vulnerabilities and tech debt

---

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.10 – 3.12 (3.13 works with limitations) | `python --version` |
| pip | Latest | `pip --version` |
| Anthropic API Key | — | Get from [console.anthropic.com](https://console.anthropic.com) |

**Corporate network?** HuggingFace is blocked? System automatically falls back to hash-based embeddings — everything still works.

---

## Step 1: Create `.env` File

Create a file named `.env` in the project root with your API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

> ⚠️ **Windows (PowerShell):** Don't use `echo` — it writes UTF-16.  
> Instead, use VS Code to create the file, or run:
> ```powershell
> Set-Content -Path .env -Value "ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE" -Encoding UTF8
> ```

---

## Step 2: Install Dependencies

```powershell
cd C:\path\to\BRD_agent
pip install -r requirements.txt
```

**Corporate/Proxy networks:**
```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

## Step 3: Launch the Web UI

```powershell
python -m streamlit run app.py
```

Opens at **http://localhost:8501**

**Port already in use?**
```powershell
python -m streamlit run app.py --server.port 8502
```

---

## Step 4: Upload & Analyze a Repository

1. In the Streamlit sidebar → **📤 Upload Repository**
2. Click **"Upload a .zip file"** and select your repository
3. System asks: **"Add Supporting Documents?"** → Click **"✅ Yes"** if you have specs/requirements files (optional)
4. Click **▶ Run Pipeline**

**Wait 2-5 minutes** while the system analyzes your code...

---

## Step 5: View Results

Once complete, three tabs are available:

| Tab | What it shows |
|---|---|
| **📄 Generate BRD** | Full BRD markdown with executive summary, architecture, business rules, user journeys, acceptance criteria |
| **💬 RAG Chat** | Ask questions about the repository — e.g., "What are the acceptance criteria?" or "How does authentication work?" |
| **🕸️ Hypergraph** | Visual graph of relationships between components and documents |

**Download BRD:** Click the download button to save the markdown to your computer.

---

## Using RAG Chat — Ask Questions About Your Code

The **RAG Chat** tab lets you ask natural language questions about the repository. The system searches through all ingested documents and provides grounded answers with citations.

### How It Works

1. Type your question in the chat box
2. System searches documents, ranks by relevance
3. Returns answer with cited sources
4. You can ask follow-up questions

### Example Queries

**Architecture & Design:**
- "What are the main components of this system?"
- "How is the database schema structured?"
- "What design patterns are used?"
- "Show me the user authentication flow"

**Business Logic:**
- "What are the business rules for payment?"
- "What's the acceptance criteria for checkout?"
- "How does order processing work?"
- "What validation rules exist?"

**Implementation Details:**
- "Which APIs are available?"
- "What error handling is implemented?"
- "How is caching implemented?"
- "What dependencies does this use?"

**Risk & Quality:**
- "What security issues are known?"
- "What test coverage exists?"
- "Are there any missing features?"
- "What performance bottlenecks exist?"

### Tips for Better Answers

✅ **Be specific:**
- ❌ "How does it work?"
- ✅ "How does the payment processing workflow handle failed transactions?"

✅ **Ask about specific artifacts:**
- ❌ "Tell me about validation"
- ✅ "What validation rules are defined in the business rules?"

✅ **Use follow-ups:**
- Ask "Why?" or "Give me an example" for clarification

✅ **Check the sources:**
- Each answer shows which documents it used
- Click sources to see the original context

### Confidence Indicators

The system shows confidence for each answer:

| Confidence | Meaning |
|---|---|
| **HIGH** | System found clear, direct information in documents |
| **MEDIUM** | System found relevant information but with some inference |
| **LOW** | System couldn't find specific information; answer is speculative |

If confidence is LOW, try:
- Rephrasing your question
- Using different keywords
- Asking about a different aspect

---

## Using Hypergraph — Visualize Component Relationships

The **Hypergraph** tab shows a visual graph of how documents and components relate to each other. It helps you understand the "big picture" of your codebase.

### How to Navigate

1. **View the graph** — Nodes represent documents, edges show relationships
2. **Hover over nodes** — See document name and type (BRD, business rules, API docs, etc.)
3. **Click on nodes** — View document details
4. **Zoom in/out** — Scroll to zoom
5. **Pan** — Click and drag the background to move around

### What the Edges Mean

| Relationship | Meaning |
|---|---|
| **references** | Document A cites or refers to Document B |
| **informs** | Document A provides context/background for Document B |
| **supersedes** | Document A replaces or updates Document B |
| **related** | General connection between documents |

### What to Look For

**Hubs (highly connected nodes):**
- Central documents that many others depend on
- Often business rules, architecture docs, or API specs
- These are critical — changes here affect many areas

**Isolated nodes:**
- Documents with few connections
- May indicate orphaned specs or missing integration with other docs
- Good candidates for review/cleanup

**Long chains:**
- Show dependency paths through the system
- Help trace impact of changes

### Example Insights

- **"Which business rules affect the most features?"** → Look for business_rules nodes with many "informs" connections
- **"Is authentication documented everywhere it's needed?"** → Find auth-related nodes and trace their connections
- **"What happens if this API changes?"** → Find the API node and see all incoming "references" edges

### No Graph Showing?

**Possible reasons:**
1. Ingestion just completed — graph takes a moment to build
2. Repository is very small — might have only 1-2 documents
3. Python 3.13 used — PyVis graph visualization doesn't support Python 3.13
   - Solution: Use Python 3.12, or view documents directly in RAG Chat instead

---

## Optional: Ingest Pre-Existing Knowledge Base

If you have BRD artifacts already in `KB/` folder, ingest them:

```powershell
python bin/ingest.py --all
```

Expected output:
```
[OK] Ingested: business_rules.json [business_rules]
[OK] Ingested: COMPREHENSIVE_BRD_spring-petclinic.md [brd]
...
[OK] Service 'spring-petclinic': 30 ingested, 0 skipped, 0 errors
```

---

## Optional: CLI Tools

### Query from Command Line

```powershell
python bin/query.py "What are the acceptance criteria?"
```

### Start REST API Server

```powershell
python bin/api_server.py
```

REST API runs at **http://localhost:8081**

---

## Project Structure

```
BRD_agent/
├── app.py                      # Streamlit entry point
├── .env                        # API key (create this, not in git)
├── requirements.txt
│
├── bin/                        # CLI tools
│   ├── ingest.py               # Ingest BRD artifacts
│   ├── query.py                # Query CLI
│   ├── annotate.py             # Feedback annotations
│   └── api_server.py           # REST API (port 8081)
│
├── kb_gen/                     # Core Python library
│   ├── core/                   # Configuration
│   ├── storage/                # Document registry
│   ├── hypergraph/             # Graph structure
│   ├── embeddings/             # ChromaDB + embeddings
│   ├── ingestion/              # File processing
│   ├── graph/                  # Graph operations
│   ├── rag/                    # RAG pipeline
│   └── hitl/                   # Feedback system
│
├── KB/                         # Knowledge Base output
│   ├── <service-name>/         # BRD artifacts per service
│   └── graph/
│       └── hypergraph.json     # Relationships between services
│
├── registry/
│   └── documents.json          # Document catalog with metadata
│
├── kb_store/                   # ChromaDB vector storage (auto-generated)
├── logs/
│   └── ingestion_progress.json # Change detection checkpoint
│
└── config/
    └── config.yaml             # Tool configuration
```

---

## Troubleshooting

### Python 3.13 + Graph Visualization Error
**Problem:** `pyvis` has no wheels for Python 3.13.  
**Solution:** Use Python 3.12, or skip graph visualization by using CLI tools only.

### UTF-16 `.env` File (PowerShell Windows)
**Problem:** `echo ANTHROPIC_API_KEY=... > .env` creates UTF-16 encoded file.  
**Solution:** Use `Set-Content -Encoding UTF8` as shown in Step 1.

### SSL/Corporate Network
**Problem:** HuggingFace/pip timeouts or SSL certificate errors.  
**Solution:** 
- For pip: Use `--trusted-host` flags (shown in Step 2)
- For embeddings: System automatically falls back to SHA-256 hash embeddings — no action needed

### Streamlit Port Already in Use
**Solution:** `python -m streamlit run app.py --server.port 8502`

### Slow Performance on Large Repositories
**Tip:** The first ingestion of a large repository takes longer. Subsequent queries are fast due to caching and change detection.

---

## Next Steps

- 📖 Read **[ARCHITECTURE.md](ARCHITECTURE.md)** to understand how the system works internally
- 🔧 Explore the **RAG Chat** to ask specific questions about your codebase
- 📊 Check **Hypergraph** tab to see component relationships
- 📝 Review **KB/** folder to see generated BRD artifacts
- 🤝 Use **bin/annotate.py** to provide feedback and improve results
