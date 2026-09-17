# BRD Agent — Complete Setup & Installation Guide

> Get up and running in 5 steps. No API key required (optional for better quality).

---

## Prerequisites

| Requirement | Version | Check | Optional? |
|---|---|---|---|
| Python | 3.10 – 3.12 recommended | `python --version` | Required |
| pip | Latest | `pip --version` | Required |
| LLM Provider | **See Below** | Multiple options | Optional* |

> **\* No API key required!** System auto-detects: API Keys → GitHub Copilot Chat → Claude Code → Static Analysis

> **Corporate network (e.g. Cognizant):** SSL inspection blocks HuggingFace. System falls back to hash-based embeddings automatically — everything still works.

> **Python 3.13:** Works, except `pyvis` graph visualization has no wheels. Use Python 3.12 if needed.

---

## LLM Provider Options (Choose One or Leave Blank)

### Option 1: Use API Key (RECOMMENDED for production)

**Best Quality** | Cost: $0.003/1K tokens | Works from terminal

Get from: [console.anthropic.com](https://console.anthropic.com)

```powershell
# Step A: Get API key
# Visit https://console.anthropic.com and create key

# Step B: Create .env file in project root with:
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE

# OR use OpenAI:
OPENAI_API_KEY=sk-...

# OR use Google Gemini:
GOOGLE_API_KEY=...
```

### Option 2: Use VS Code Extensions (FREE!)

**Good Quality** | Cost: FREE | Requires VS Code

1. Install **Claude Code** extension in VS Code (completely free)
2. Leave `.env` file blank
3. System auto-detects extension
4. Use: `streamlit run app.py`

### Option 3: Use Static Analysis (FREE!)

**Basic Quality** | Cost: FREE | Fallback only

- No setup needed
- System auto-detects when no API key
- Works everywhere
- Lower quality but still useful

---

## Step 1 — Install Python & Dependencies

```powershell
# Check Python version (3.10-3.12 recommended)
python --version

# Navigate to project directory
cd C:\path\to\BRD_agent

# Install all dependencies
pip install -r requirements.txt
```

**On corporate networks with SSL errors:**

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

## Step 2 — Optional: Create `.env` File

**Skip this if using Claude Code extension (free)**

In the project root, create a file named `.env`:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

**Do NOT use PowerShell `echo ... > .env`** — it writes UTF-16 which Python cannot read.  
Use VS Code to create the file, or run:

```powershell
Set-Content -Path .env -Value "ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE" -Encoding UTF8
```

---

## Step 3 — Test LLM Providers (RECOMMENDED)

This shows which LLM providers are available on your system:

```powershell
python test_multi_provider.py
```

**Example Output:**

```
🔍 Detecting LLM providers...
  ⚪ Claude API not available (ANTHROPIC_API_KEY not set)
  ⚪ OpenAI API not available (OPENAI_API_KEY not set)
  ⚪ Google Gemini API not available (GOOGLE_API_KEY not set)
  ✅ GitHub Copilot Chat extension detected in VS Code
  ✅ Claude Code extension detected in VS Code

🚀 Using: GitHub Copilot Chat (VS Code Extension)

📊 Available Providers:
⚪ Claude API (Anthropic)                   [requires API key]
⚪ OpenAI (GPT-4, GPT-3.5)                  [requires API key]
⚪ Google Gemini                            [requires API key]
✅ GitHub Copilot Chat (VS Code Extension)  [no API key needed]
✅ Claude Code (VS Code Extension)          [no API key needed]
✅ Static Analysis                          [fallback]
```

---

## Step 4 — Generate Your First BRD

### Option A: Quick Test with Sample Repository

```powershell
# Use included sample
python run_all_agents.py "Sample_Repos/Springy-Store-Microservices" --output "KB/springy-store"
```

### Option B: Generate for Your Own Repository

```powershell
# Point to your Java repository
python run_all_agents.py "C:\path\to\your-java-repo" --output "KB/my-repo"

# Examples:
python run_all_agents.py "C:\workspace\my-app" --output "KB/my-app"
python run_all_agents.py ".\Sample_Repos\spring-petclinic" --output "KB/petclinic"
```

**What happens:**
- Scans your entire repository
- Runs 9 specialized agents
- Generates 31+ artifacts (JSON + Markdown + Diagrams)
- Stores in `KB/<repo-name>/`
- Takes 2-30 minutes depending on size

---

## Step 5 — Explore Results

### Index the Knowledge Base

```powershell
# Make artifacts searchable in ChromaDB
python bin/ingest.py my-repo
```

Expected output:
```
[LocalEmbedder] sentence-transformers model unavailable. Using hash-based fallback embeddings.
  [OK] Ingested: business_rules.json [business_rules]
  [OK] Ingested: COMPREHENSIVE_BRD.md [brd]
  ...
[OK] Service '"'"'my-repo'"'"': 31 ingested, 0 skipped, 0 errors
```

### Launch Interactive Web UI

```powershell
python -m streamlit run app.py
```

Opens at **http://localhost:8501**

In the sidebar:
- Select repository from dropdown
- Browse generated documents
- Search knowledge base
- Ask questions about the system

**Port conflict?**
```powershell
python -m streamlit run app.py --server.port 8502
```

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Test LLM providers | `python test_multi_provider.py` |
| Generate BRD | `python run_all_agents.py "repo-path" --output "KB/my-repo"` |
| Index KB | `python bin/ingest.py my-repo` |
| Web UI | `streamlit run app.py` |
| CLI search | `python bin/query.py "your question"` |
| REST API | `python bin/api_server.py` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No LLM provider available | Run `python test_multi_provider.py` to check |
| API key not working | Verify key in `.env` file (no spaces) |
| HuggingFace SSL error | Expected on corporate networks - auto-falls back |
| fastapi/chromadb not found | `pip install -r requirements.txt` |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |
| No vector store found | `python bin/ingest.py --all` |

---

## Next Steps

1. Read [docs-for-new-users/README.md](docs-for-new-users/README.md) for complete overview
2. Follow [docs-for-new-users/BEGINNER_GUIDE.md](docs-for-new-users/BEGINNER_GUIDE.md) for hands-on tutorial
3. Check [docs-for-new-users/getting-started.md](docs-for-new-users/getting-started.md) for all commands

---

**Version:** 2.0 (Multi-Provider LLM System)  
**Last Updated:** September 2026  
**Status:** Production Ready ✅
