# 📋 BRD Agent — Complete Documentation & Architecture Guide

> **Welcome!** This guide explains what BRD Agent does, how it works, and how to use it.

---

## 🎯 What is BRD Agent?

**BRD = Business Requirements Document**

BRD Agent is an **AI-powered multi-agent system** that automatically analyzes Java legacy codebases and generates comprehensive **Business Requirements Documents** with:

✅ System scope and architecture  
✅ Business rules and workflows  
✅ User journeys and flows  
✅ API endpoints and data interactions  
✅ Acceptance test criteria  
✅ Risk assessment and dependencies  
✅ Gap analysis (missing features/tests)  
✅ Architecture diagrams  

> **NEW in v3.0 — Claude Code Native Path.** In addition to the Python pipeline described below, you can now generate a BRD entirely through the Claude Code VS Code extension by typing `/brd generate <repo>`. This route dispatches to 8 registered subagents via Claude Code's Agent tool — no Python subprocess, no API-key setup, no fallback signal analysis. See **[Alternative: Claude Code Native Path](#-alternative-claude-code-native-path-v30)** below.

### Why Use BRD Agent?

| Use Case | Benefit |
|----------|---------|
| **Onboarding New Team Members** | Understand complex systems in minutes, not weeks |
| **Code Reviews** | Know what the system is supposed to do |
| **Requirements Documentation** | Auto-generate from code (no manual work) |
| **Legacy System Analysis** | Understand decades-old Java code |
| **Gap Analysis** | Find missing tests, documentation, and features |
| **Risk Assessment** | Identify vulnerabilities and tech debt |
| **System Maintenance** | Keep documentation up-to-date automatically |

---

## 🏗️ Architecture Overview

### System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                    BRD Agent System (v2.0)                         │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  INPUT LAYER                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Source Repository (Java/Python/.NET/Any Codebase)         │ │
│  │  • Source files (.java, .py, .cs, etc.)                    │ │
│  │  • Config files (pom.xml, build.gradle, application.yml)   │ │
│  │  • Documentation (README, comments)                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                            │                                       │
│                            ▼                                       │
│  ORCHESTRATION LAYER                                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Multi-Provider LLM System (Auto-Detection & Fallback)     │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │ Priority Chain:                                        │ │ │
│  │  │ 1. API Keys (Claude/OpenAI/Gemini) → Best Quality    │ │ │
│  │  │ 2. GitHub Copilot Chat (VS Code) → Good Quality      │ │ │
│  │  │ 3. Claude Code (VS Code) → Good Quality (FREE!)      │ │ │
│  │  │ 4. Static Analysis → Basic Quality (Fallback)        │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                            │                                       │
│                            ▼                                       │
│  ANALYSIS LAYER (9 Specialized Agents)                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Agent 1: Discovery & Scoping                              │ │
│  │  ├─ Scan repository structure                              │ │
│  │  ├─ Identify all Java classes and packages                │ │
│  │  └─ Extract project metadata                               │ │
│  │                                                              │ │
│  │  Agent 2: Journey Mapping                                  │ │
│  │  ├─ Trace user workflows through code                     │ │
│  │  ├─ Map business processes                                 │ │
│  │  └─ Identify decision points                               │ │
│  │                                                              │ │
│  │  Agent 3: Business Rules Extraction                        │ │
│  │  ├─ Find validation rules in code                          │ │
│  │  ├─ Extract business constraints                           │ │
│  │  └─ Document business logic                                │ │
│  │                                                              │ │
│  │  Agent 4: Gap Analysis                                     │ │
│  │  ├─ Find missing tests                                     │ │
│  │  ├─ Identify documentation gaps                            │ │
│  │  └─ Spot error handling issues                             │ │
│  │                                                              │ │
│  │  Agent 5: Synthesis                                        │ │
│  │  ├─ Combine all findings                                   │ │
│  │  ├─ Create coherent narrative                              │ │
│  │  └─ Generate diagrams                                      │ │
│  │                                                              │ │
│  │  Agent 6: Acceptance Criteria                              │ │
│  │  ├─ Generate test scenarios                                │ │
│  │  ├─ Create validation criteria                             │ │
│  │  └─ Map requirements to tests                              │ │
│  │                                                              │ │
│  │  Agent 7: Risk & Dependencies                              │ │
│  │  ├─ Identify security vulnerabilities                      │ │
│  │  ├─ Find tech debt                                         │ │
│  │  └─ Map dependencies                                       │ │
│  │                                                              │ │
│  │  Agent 8: Summarizer                                       │ │
│  │  ├─ Create executive summary                               │ │
│  │  ├─ Highlight key findings                                 │ │
│  │  └─ Generate report                                        │ │
│  │                                                              │ │
│  │  Agent 9: KB Store Sync                                    │ │
│  │  ├─ Store artifacts in vector DB                           │ │
│  │  ├─ Enable semantic search                                 │ │
│  │  └─ Update document registry                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                            │                                       │
│                            ▼                                       │
│  STORAGE LAYER                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Knowledge Base (ChromaDB + File System)                   │ │
│  │  ├─ Vector embeddings (semantic search)                    │ │
│  │  ├─ JSON artifacts (structured data)                       │ │
│  │  ├─ Markdown documents (human-readable)                    │ │
│  │  └─ Document registry (metadata)                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                            │                                       │
│                            ▼                                       │
│  OUTPUT LAYER                                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  BRD Artifacts (31 Documents + Diagrams)                   │ │
│  │  ├─ Business Rules (JSON + Markdown)                       │ │
│  │  ├─ Journey Maps (JSON + Markdown)                         │ │
│  │  ├─ API Documentation (JSON + Markdown)                    │ │
│  │  ├─ Acceptance Criteria (JSON + Markdown)                  │ │
│  │  ├─ Risk Assessment (JSON + Markdown)                      │ │
│  │  ├─ Architecture Diagrams (SVG/PNG)                        │ │
│  │  ├─ Comprehensive BRD (Markdown)                           │ │
│  │  └─ Executive Summary (Markdown)                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
└───────────────────────────────────────────────────────────────────┘

        ↓ CONSUMPTION LAYER ↓

┌─────────────────────────────────────────────────────────────────┐
│  Web UI (Streamlit)  │  REST API  │  CLI Tools  │  Exports      │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Provider LLM System (NEW!)

The system intelligently selects the best available LLM provider:

```
WITHOUT API KEY:
├─ VS Code Extension Available?
│  ├─ GitHub Copilot Chat (2nd priority, paid)
│  └─ Claude Code (3rd priority, FREE!)
└─ Fallback: Static Analysis (basic)

WITH API KEY:
├─ Anthropic Claude API (1st priority, BEST)
├─ OpenAI GPT-4/3.5 (1st priority, BEST)
├─ Google Gemini (1st priority, BEST)
└─ Fallback: Extensions → Static

PRIORITY CHAIN:
┌─────────────────────────────────────────┐
│ 1st: API Keys (Best Quality)            │  ← Use this if available
├─────────────────────────────────────────┤
│ 2nd: GitHub Copilot Chat (VS Code)      │  ← $10/month
├─────────────────────────────────────────┤
│ 3rd: Claude Code (VS Code)              │  ← FREE!
├─────────────────────────────────────────┤
│ 4th: Static Analysis (Fallback)         │  ← Basic quality
└─────────────────────────────────────────┘
```

---

## 🔄 How It Works (Step-by-Step)

### Phase 1: Repository Discovery & Scoping

```
STEP 1: Scan Repository
   ├─ Agent 1 discovers all Java files
   ├─ Identifies entry points and main classes
   ├─ Reads configuration files (pom.xml, application.yml, etc.)
   ├─ Maps dependencies and imports
   └─ OUTPUT: Scope definition + Artifact catalog

STEP 2: Extract Project Metadata
   ├─ Identify frameworks (Spring, Jakarta, JSF, etc.)
   ├─ Detect databases and integrations
   ├─ Find API endpoints and controllers
   ├─ Parse configuration and properties
   └─ OUTPUT: Dependency map + Architecture skeleton
```

### Phase 2: Business Logic Analysis

```
STEP 3: Journey Mapping (Agent 2)
   ├─ Trace user workflows through code
   ├─ Identify business processes
   ├─ Map decision points and branches
   ├─ Document flow from UI → Business Logic → Database
   └─ OUTPUT: User journeys + Flow diagrams

STEP 4: Extract Business Rules (Agent 3)
   ├─ Find validation rules in code
   ├─ Extract business constraints
   ├─ Identify calculation logic
   ├─ Document authorization/authentication rules
   └─ OUTPUT: Business rules JSON + Markdown

STEP 5: API Documentation
   ├─ Extract REST endpoints (via reflection/annotation parsing)
   ├─ Document request/response schemas
   ├─ Identify authentication requirements
   ├─ Map API flow to business logic
   └─ OUTPUT: API documentation + OpenAPI spec
```

### Phase 3: Quality & Gap Analysis

```
STEP 6: Gap Analysis (Agent 4)
   ├─ Find missing test coverage
   ├─ Identify documentation gaps
   ├─ Spot error handling issues
   ├─ Flag missing edge cases
   └─ OUTPUT: Gap report + Improvement recommendations

STEP 7: Risk Assessment (Agent 7)
   ├─ Identify security vulnerabilities
   ├─ Find tech debt and deprecated patterns
   ├─ Map critical dependencies
   ├─ Assess maintainability
   └─ OUTPUT: Risk report + Mitigation strategies

STEP 8: Acceptance Criteria (Agent 6)
   ├─ Generate test scenarios
   ├─ Create validation criteria
   ├─ Map requirements to tests
   ├─ Define success metrics
   └─ OUTPUT: Acceptance criteria + Test templates
```

### Phase 4: Synthesis & Storage

```
STEP 9: Synthesis (Agent 5)
   ├─ Combine all agent outputs
   ├─ Create coherent narrative
   ├─ Generate architecture diagrams
   ├─ Build sequence diagrams
   ├─ Create data flow diagrams
   └─ OUTPUT: Comprehensive BRD + Visual diagrams

STEP 10: Summary (Agent 8)
   ├─ Write executive summary
   ├─ Highlight key findings
   ├─ Create quick reference
   ├─ Generate recommendation list
   └─ OUTPUT: Summary document + Key insights

STEP 11: Knowledge Base Sync (Agent 9)
   ├─ Store all artifacts in ChromaDB
   ├─ Generate vector embeddings
   ├─ Build semantic search index
   ├─ Update document registry
   └─ OUTPUT: Searchable knowledge base ready for queries
```

---

## 💾 What Gets Generated?

After processing a repository, you get **31+ artifacts**:

### Core Structured Data (JSON)
```
business_rules.json              # All business rules
journey_map.json                 # User workflows
acceptance_criteria.json         # Test scenarios
api_endpoints.json               # REST API documentation
dependencies.json                # System dependencies
risk_assessment.json             # Risk analysis
gap_analysis.json                # Gaps and improvements
data_models.json                 # Database schemas
configuration_map.json           # Config settings
integration_map.json             # External integrations
```

### Comprehensive Reports (Markdown)
```
COMPREHENSIVE_BRD.md             # Full BRD document (50+ pages)
ARCHITECTURE.md                  # System architecture
USER_JOURNEYS.md                 # Detailed workflows
API_DOCUMENTATION.md             # Complete API guide
RISK_REPORT.md                   # Risk & security analysis
IMPLEMENTATION_GUIDE.md          # How to build/improve
GAP_ANALYSIS_REPORT.md           # Missing items
EXECUTIVE_SUMMARY.md             # High-level overview
CONFIGURATION_GUIDE.md           # Config documentation
TESTING_STRATEGY.md              # Test coverage strategy
+ 20 more specialized documents
```

### Visual Diagrams
```
architecture_diagram.svg         # System components
sequence_diagram.svg             # Message flows
data_flow_diagram.svg            # Data movement
entity_relationship_diagram.svg  # Database schema
deployment_diagram.svg           # Production setup
class_hierarchy_diagram.svg      # OO relationships
```

---

## 🚀 Quick Start (5 Steps)

### Step 1: Install Python & Dependencies

```powershell
# Check Python version (3.10-3.12 recommended)
python --version

# Navigate to project
cd C:\path\to\BRD_agent

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Check Available LLM Providers

```powershell
# Test which providers are available on your system
python test_multi_provider.py
```

**Output Example:**
```
🔍 Detecting LLM providers...
  ✅ Claude Code extension detected in VS Code
  ✅ GitHub Copilot Chat extension detected in VS Code
  ⚪ Claude API not available (ANTHROPIC_API_KEY not set)

🚀 Using: GitHub Copilot Chat (VS Code Extension)
```

### Step 3: (Optional) Add API Key

Create `.env` file in project root for faster/better quality output:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Or skip this step and use free Claude Code extension!

### Step 4: Generate BRD for Your Repository

```powershell
# Run full BRD generation pipeline
python run_all_agents.py "path/to/your-java-repo" --output "KB/my-repo"

# Examples:
python run_all_agents.py "C:\workspace\spring-app" --output "KB/spring-app"
python run_all_agents.py ".\Sample_Repos\Springy-Store-Microservices" --output "KB/springy-store"
```

**What happens:**
- Scans your entire repository
- Runs 9 agents to analyze code
- Generates 31+ artifacts
- Stores in `KB/my-repo/`
- Completes in 2-30 minutes depending on repo size

### Step 5: Explore Results

```powershell
# Make artifacts searchable
python bin/ingest.py my-repo

# Launch interactive web UI
streamlit run app.py
```

Open **http://localhost:8501** and:
- Browse generated BRD documents
- Search knowledge base
- Ask questions about the system
- Export reports

---

## 🆕 Alternative: Claude Code Native Path (v3.0)

The Python pipeline described above is the **original** BRD Agent flow. As of v3.0, there is a **second route** that runs entirely inside the Claude Code VS Code extension — no Python subprocess, no `.env`, no ChromaDB.

### When to use which route?

| Situation | Recommended route |
|---|---|
| You already open the repo in VS Code with Claude Code installed | **Native `/brd` skill** |
| You want repeatable CI-style batch runs across many repos | **Python pipeline** (`run_all_agents.py`) |
| You want vector-DB ingestion + Streamlit UI | **Python pipeline** |
| You want the highest-quality one-shot BRD without setup | **Native `/brd` skill** |
| You want to run headless without Claude Code | **Python pipeline** with API key |

### How the native path works

```
User types /brd generate <repo> [<kb-path>] in Claude Code
        │
        ▼
Claude Code loads .claude/skills/brd/SKILL.md as instructions
        │
        ▼
Main assistant plans 8 stages via TodoWrite
        │
        ▼
For each stage, spawns a subagent via the Agent tool:
   Stage 1 → subagent_type: brd-discovery
   Stage 2 → subagent_type: brd-dependencies
   Stage 3 → subagent_type: brd-journey-rules
   Stage 4 → subagent_type: brd-gap-analysis
   Stage 5 → subagent_type: brd-synthesis        (opus)
   Stage 6 → subagent_type: brd-acceptance
   Stage 7 → subagent_type: brd-risk
   Stage 8 → subagent_type: brd-summarizer       (opus)
        │
        ▼
Each subagent Read/Grep/Writes its own artifacts to KB/<repo>/
        │
        ▼
Main assistant returns final report (top-3 critical items + links)
```

### Files that make this work

| File | Role |
|---|---|
| `.claude/skills/brd/SKILL.md` | The `/brd` slash-command entry point |
| `.claude/agents/brd-discovery.md` | Stage 1 subagent definition |
| `.claude/agents/brd-dependencies.md` | Stage 2 subagent |
| `.claude/agents/brd-journey-rules.md` | Stage 3 subagent |
| `.claude/agents/brd-gap-analysis.md` | Stage 4 subagent |
| `.claude/agents/brd-synthesis.md` | Stage 5 subagent (opus) |
| `.claude/agents/brd-acceptance.md` | Stage 6 subagent |
| `.claude/agents/brd-risk.md` | Stage 7 subagent |
| `.claude/agents/brd-summarizer.md` | Stage 8 subagent (opus) |

Each subagent file has proper Claude Code YAML frontmatter (`name`, `description`, `tools`, `model`) so Claude Code auto-discovers it on session start and exposes it as a `subagent_type` value for the Agent tool.

### Usage

```
# In a Claude Code session:
/brd generate C:\path\to\my-repo

# Or with an explicit output folder:
/brd generate C:\path\to\my-repo C:\path\to\KB\my-repo
```

Output goes to `KB/<repo-basename>/` by default. Produces **33 artifacts** including the comprehensive markdown BRD, structured JSON evidence, OpenAPI spec, and Gherkin acceptance criteria.

### Important caveats

1. **Session restart may be needed** the first time — Claude Code scans `.claude/agents/*.md` at session init, so if you just added the files (or pulled a fresh checkout) restart the extension before running `/brd`.
2. The native path **does not** ingest into ChromaDB. If you want semantic search across the generated artifacts, follow up with `python bin/ingest.py <repo>` from a terminal.
3. The Python pipeline files (`kb_gen/`, `run_all_agents.py`, `brd_orchestrator.py`) are untouched by v3.0 and remain the fallback for headless / API-key-based runs.

### Verify the subagents are discoverable

In a fresh Claude Code session, ask:

```
list available agent types
```

You should see the built-ins (`Explore`, `Plan`, `general-purpose`, `statusline-setup`, `claude-code-guide`) **plus** the eight `brd-*` names. If they're missing, your Claude Code build doesn't auto-load `.claude/agents/` — open an issue or fall back to the Python route.

---

## 📊 LLM Provider Options

### Option 1: Use API Key (RECOMMENDED for production)

**Best Quality** | Works from Terminal | Costs $$$

```powershell
# Get API key from https://console.anthropic.com
# Then create .env file:
echo ANTHROPIC_API_KEY=sk-ant-... > .env

# Now run pipeline
python run_all_agents.py "repo-path" --output "KB/output"
```

**Supported API Keys:**
- ✅ Anthropic Claude API (best for code analysis)
- ✅ OpenAI GPT-4/3.5 (good for general analysis)
- ✅ Google Gemini (good for code analysis)

### Option 2: Use VS Code Extension (FREE)

**Good Quality** | No Terminal Support | FREE!

1. Install **Claude Code** extension in VS Code (completely free)
2. Leave `.env` blank (no API key needed)
3. System auto-detects extension
4. Run: `streamlit run app.py`
5. Works with Streamlit web UI

**Why this works:**
- Claude Code is available in VS Code
- Streamlit can access VS Code environment
- No API costs!

### Option 3: Fallback Static Analysis (FREE)

**Basic Quality** | Always Available | FREE!

If no API key and no extensions:
- Uses pattern matching and heuristics
- Still generates useful documentation
- Good for quick analysis
- Works everywhere

---

## 📁 Project Structure

```
BRD_agent/
│
├── 📄 README Files
│   ├── README.md (main overview)
│   ├── SETUP_GUIDE.md (installation)
│   └── QUICK_REFERENCE.md (common commands)
│
├── 🐍 Python Entry Points
│   ├── run_all_agents.py              # Main: Generate BRD for any repo
│   ├── test_multi_provider.py          # Test: Check LLM providers
│   ├── app.py                          # Web UI: Streamlit dashboard
│   └── run_brd_pipeline.ps1           # PowerShell: BRD generation
│
├── ⚙️ Configuration
│   ├── .env                           # Your API keys (KEEP SECRET!)
│   ├── kb_gen_config.yaml             # Master configuration
│   └── config.yaml                    # Agent settings
│
├── 🧠 Core Logic (kb_gen/)
│   ├── core/
│   │   ├── agent1_discovery.py        # Repository scanning
│   │   ├── agent2_journey_mapping.py  # User workflows
│   │   ├── agent3_business_rules.py   # Business logic extraction
│   │   ├── agent4_gap_analysis.py     # Gap detection
│   │   ├── agent5_synthesis.py        # Diagram generation
│   │   ├── agent6_acceptance.py       # Test criteria
│   │   ├── agent7_risk.py             # Risk assessment
│   │   ├── agent8_summarizer.py       # Summary generation
│   │   └── agent9_kb_sync.py          # Knowledge base storage
│   │
│   ├── utils/
│   │   ├── multi_provider_llm.py      # NEW! LLM orchestration & fallback
│   │   ├── agent_llm.py               # Agent LLM wrapper
│   │   └── provider_adapters/         # LLM provider implementations
│   │       ├── anthropic_adapter.py
│   │       ├── openai_adapter.py
│   │       ├── gemini_adapter.py
│   │       ├── github_copilot_adapter.py
│   │       └── claude_code_adapter.py
│   │
│   ├── storage/
│   │   └── chromadb_store.py          # Vector database integration
│   │
│   └── rag/
│       └── query_engine.py            # Semantic search
│
├── 🔧 CLI Tools (bin/)
│   ├── ingest.py                      # Index KB in ChromaDB
│   ├── query.py                       # Search from CLI
│   └── api_server.py                  # REST API server
│
├── 💾 Knowledge Base
│   ├── KB/                            # Generated BRD artifacts
│   │   ├── springy-store/             # Example: Springy Store
│   │   ├── spring-petclinic/          # Example: Spring PetClinic
│   │   └── your-repo/                 # Your generated docs
│   │
│   ├── kb_store/                      # ChromaDB vector store
│   │   └── chroma.sqlite3
│   │
│   └── registry/
│       └── documents.json             # Document catalog
│
├── 📚 Documentation (docs-for-new-users/)
│   ├── README.md                      # YOU ARE HERE
│   ├── BEGINNER_GUIDE.md              # Step-by-step tutorial
│   ├── AGENTS.md                      # What each agent does
│   ├── getting-started.md             # CLI commands & examples
│   ├── kb-store-guide.md              # Search & storage details
│   └── brd-examples/                  # Real BRD examples
│
└── 📋 Dependencies
    └── requirements.txt               # Python packages
```

---

## 🛠️ Common Commands

### Generate BRD for a Repository

```powershell
# Full BRD generation pipeline
python run_all_agents.py "path/to/java-repo" --output "KB/my-repo"

# Examples
python run_all_agents.py "C:\workspace\my-app" --output "KB/my-app"
python run_all_agents.py ".\Sample_Repos\spring-boot-crud" --output "KB/spring-crud"
```

### Test LLM Providers

```powershell
# Shows which providers are available and which is active
python test_multi_provider.py
```

**Output shows:**
- ✅/❌ Each provider status
- 🚀 Which one is currently selected
- 📝 Setup instructions for each

### Ingest Knowledge Base

```powershell
# Ingest a specific repository
python bin/ingest.py my-repo

# Ingest all repositories
python bin/ingest.py --all
```

### Launch Web UI

```powershell
# Default: http://localhost:8501
streamlit run app.py

# Custom port
streamlit run app.py --server.port 8502
```

### Query Knowledge Base from CLI

```powershell
# Search artifacts
python bin/query.py "What are the business rules?"

# Multi-word queries
python bin/query.py "acceptance criteria for payment processing"
```

### Start REST API Server

```powershell
# Runs on http://localhost:8081
python bin/api_server.py

# Custom port
$env:PORT=8082; python bin/api_server.py
```

---

## 🤔 Frequently Asked Questions

### Q: Do I NEED an API key?

**A:** NO! You can use BRD Agent completely free with Claude Code extension. Options:

1. **Free:** Claude Code (VS Code extension) ← Recommended for beginners
2. **Free:** GitHub Copilot Chat (if you have paid subscription)
3. **Free:** Static Analysis (basic fallback)
4. **Paid:** Anthropic Claude API ($0.003/1K tokens) ← Best quality

### Q: Can I run from terminal without API key?

**A:** No, terminal commands don't have access to VS Code extensions.

**Solutions:**
- Add API key → Works from terminal with great quality
- Use Streamlit → Works from terminal but needs extension or API key
- Copy artifacts to Streamlit → Use extension in VS Code for generation

### Q: How long does BRD generation take?

**A:** Depends on repository size:

| Size | Time | Artifacts |
|------|------|-----------|
| Small (< 10K lines) | 2-5 min | 25-30 |
| Medium (10K-50K) | 5-15 min | 28-31 |
| Large (50K+ lines) | 15-45 min | 31+ |

### Q: What Java versions are supported?

**A:** The system analyzes source code, not runtime:
- ✅ Java 8+ codebases (oldest supported)
- ✅ Any framework (Spring, Jakarta, JSF, Quarkus, etc.)
- ✅ Any architecture (monolith, microservices, etc.)

### Q: Can I use this for non-Java projects?

**A:** Yes! Works with any multi-file codebase:
- ✅ Python (Django, Flask, FastAPI)
- ✅ Node.js (Express, NestJS)
- ✅ .NET (ASP.NET, .NET Core)
- ✅ Go, Rust, etc.

### Q: What if I have both API key and extensions?

**A:** API key takes priority:
```
1. API Key (if set) ← Uses this first (best)
2. GitHub Copilot Chat ← Uses if no API key
3. Claude Code ← Uses if no Chat extension
4. Static Analysis ← Uses as last resort
```

### Q: Can I use multiple API providers together?

**A:** Yes! Set multiple keys in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

System will use the first available.

### Q: How accurate is the generated BRD?

**A:** Depends on LLM provider and code quality:
- **With API Key:** 90-95% accuracy (requires review)
- **With Extension:** 80-90% accuracy (requires review)
- **Static Analysis:** 60-75% accuracy (needs verification)

Always review and validate generated content!

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "ANTHROPIC_API_KEY not set" | Use free extensions or set .env file |
| "No vector store found" | Run `python bin/ingest.py --all` first |
| "Port 8501 already in use" | Use `streamlit run app.py --server.port 8502` |
| "Module not found: kb_gen" | Run `pip install -r requirements.txt` |
| "Claude Code not detected" | Install from VS Code extensions marketplace |
| "Timeout during generation" | Increase timeout in `kb_gen_config.yaml` |
| "SSL error on corporate network" | Use `pip --trusted-host` or proxy settings |
| "ChromaDB connection error" | Delete `kb_store/` and re-run ingest |

---

## 📚 Documentation Map

### For New Users
1. **[README.md](README.md)** ← Start here (this file)
2. **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)** - Step-by-step tutorial
3. **[getting-started.md](getting-started.md)** - CLI commands and examples

### For Understanding the System
4. **[AGENTS.md](AGENTS.md)** - What each of the 9 agents does
5. **[kb-store-guide.md](kb-store-guide.md)** - How search and storage works

### For Real Examples
6. **[brd-examples/](brd-examples/)** - See actual BRD output

### For Setup & Troubleshooting
7. **[../SETUP_GUIDE.md](../SETUP_GUIDE.md)** - Installation instructions

---

## 🎓 Learning Path

**Day 1 - Basics:**
1. Read [README.md](README.md) (this file) - 10 min
2. Follow [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) - 20 min
3. Run `test_multi_provider.py` - 2 min
4. Review [getting-started.md](getting-started.md) - 15 min

**Day 2 - First Generation:**
1. Run: `python run_all_agents.py "Sample_Repos/Springy-Store-Microservices" --output "KB/springy-store"`
2. Run: `python bin/ingest.py springy-store`
3. Run: `streamlit run app.py`
4. Explore generated artifacts in Web UI

**Day 3 - Deep Dive:**
1. Read [AGENTS.md](AGENTS.md) - Understand each agent
2. Read [kb-store-guide.md](kb-store-guide.md) - Learn search mechanism
3. Try CLI commands from [getting-started.md](getting-started.md)
4. Generate BRD for your own repository

**Day 4 - Advanced:**
1. Set up API key for better quality
2. Customize configuration in `kb_gen_config.yaml`
3. Try REST API server: `python bin/api_server.py`
4. Build integrations with your tools

---

## 🔗 External Resources

- **Claude API Docs:** https://docs.anthropic.com
- **ChromaDB Documentation:** https://docs.trychroma.com
- **Streamlit Guide:** https://docs.streamlit.io
- **BRD Best Practices:** https://www.businessanalysismodeling.com

---

## 💡 Pro Tips

1. **For Corporate Networks:** SSL errors are expected - system auto-falls back to hash-based embeddings
2. **Large Repositories:** Set longer timeouts in `kb_gen_config.yaml`
3. **Multiple Repositories:** Ingest all with `python bin/ingest.py --all`
4. **Team Collaboration:** Export artifacts to Confluence/SharePoint
5. **Continuous Updates:** Re-run periodically to keep BRD current

---

## 📞 Support & Help

| Question | Where to Look |
|----------|---------------|
| "How do I install?" | [SETUP_GUIDE.md](../SETUP_GUIDE.md) |
| "I'm new, where to start?" | [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) |
| "How does it work?" | [README.md](README.md) ← You're reading it! |
| "What commands are available?" | [getting-started.md](getting-started.md) |
| "What do agents do?" | [AGENTS.md](AGENTS.md) |
| "How is data stored?" | [kb-store-guide.md](kb-store-guide.md) |
| "Need examples?" | [brd-examples/](brd-examples/) |

---

## 🎉 You're Ready!

You now understand:
- ✅ What BRD Agent does
- ✅ How the architecture works
- ✅ What LLM providers are available
- ✅ Step-by-step workflow
- ✅ What you'll get as output
- ✅ Common commands

**Next Steps:**
1. Follow [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) for hands-on tutorial
2. Run `python test_multi_provider.py` to check your setup
3. Generate your first BRD!

---

**Last Updated:** September 2026  
**Version:** 3.0 (Claude Code Native Path + Multi-Provider LLM System)  
**Status:** Production Ready ✅
