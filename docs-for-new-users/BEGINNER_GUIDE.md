# BRD Agent — Beginner's Complete Guide

> Everything a new user needs to know to use the BRD Agent effectively.

---

## 🎯 What is BRD Agent?

**BRD = Business Requirements Document**

BRD Agent is an AI-powered system that **automatically analyzes any software repository** and generates a **comprehensive business requirements document** with:

- ✅ System scope and architecture
- ✅ Business rules and workflows  
- ✅ User journeys (8-10 per repo)
- ✅ API endpoints and data flow
- ✅ Acceptance test criteria
- ✅ Risk assessment
- ✅ Gap analysis (missing features/tests/docs)
- ✅ Diagrams (architecture, sequence, data flow)

**Use cases:**
- 📊 **New team member onboarding** — Understand a codebase in 5 minutes
- 🔍 **Code review** — See what the system is supposed to do
- 📋 **Requirements documentation** — Auto-generate from code
- 🎯 **Gap analysis** — Find missing tests, docs, and features
- ⚠️ **Risk assessment** — Identify vulnerabilities and tech debt

---

## 🚀 Quick Start (5 minutes)

### 1️⃣ Download & Open in Terminal

```powershell
cd C:\path\to\BRD_agent
```

### 2️⃣ Create `.env` File

Use **VS Code** to create `.env` in the project root:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Get your API key from [console.anthropic.com](https://console.anthropic.com)

### 3️⃣ Install & Launch

```powershell
pip install -r requirements.txt
python -m streamlit run app.py
```

Opens **http://localhost:8501**

### 4️⃣ Upload a Repository

1. In the sidebar → **📤 Upload Repository**
2. Click **"Upload a .zip file"**
3. Select a zipped repo (e.g., `my-project.zip`)
4. System asks: **"Add Supporting Documents?"** → Click **"✅ Yes"** to add specs/requirements files (optional)
5. Click **▶ Run Pipeline**

**Wait 2-5 minutes** while the system analyzes your code...

### 5️⃣ View the Results

Once complete:
- 📄 **Tab 1: Generate BRD** → Download comprehensive markdown BRD
- 💬 **Tab 2: RAG Chat** → Ask questions about the code
- 🕸️ **Tab 3: Hypergraph** → See relationships between components

---

## 📊 Understanding the Output

### What Each Section Means

#### **1. Executive Summary**
Tells you: *"What does this system do?"*
```
Example: "Springy Store is an e-commerce platform built with Spring Boot 
that manages products, orders, and payments."
```

#### **2. Architecture Diagram**
Shows: *"What are the major layers?"*
```
API Layer (Controllers) 
    ↓
Business Layer (Services)
    ↓
Data Layer (Repositories)
    ↓
Database
```

#### **3. Business Rules** (8-12 rules specific to YOUR repo)
Shows: *"What are the rules the system enforces?"*
```
Rule BR001: All user inputs must be validated before processing
Rule BR002: Orders cannot be placed without valid payment
Rule BR003: Inventory updates must be atomic
```

#### **4. User Journeys** (8-10 workflows specific to YOUR repo)
Shows: *"How do users interact with the system?"*
```
Journey J-001: Create Order
  1. User logs in
  2. Selects products
  3. Enters shipping address
  4. Processes payment
  5. Order confirmed

Journey J-002: Handle Payment Failure
  1. Payment gateway rejects transaction
  2. User notified of failure
  3. User can retry with different card
```

#### **5. API Endpoints**
Shows: *"What can I call?"*
```
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/products | GET | List all products |
| /api/orders | POST | Create new order |
| /api/orders/{id} | GET | View order details |
```

#### **6. Request/Response Examples**
Shows: *"What data format?"*
```json
POST /api/orders
{
  "customerId": "C-123",
  "items": [
    {"productId": "P-456", "quantity": 2}
  ],
  "shippingAddress": "123 Main St"
}

Response (200 OK):
{
  "orderId": "O-789",
  "status": "CONFIRMED",
  "total": 99.99
}
```

#### **7. Gap Analysis** (Testing/Documentation/Code)
Shows: *"What's missing?"*
```
GAP-001 [HIGH]: No Unit Tests
  - Impact: Bugs not caught before production
  - Effort: 2 sprints to implement

GAP-002 [MEDIUM]: Missing API Documentation  
  - Impact: Developers can't understand endpoints
  - Effort: 1 week

GAP-003 [MEDIUM]: Large Service Classes
  - Impact: Hard to maintain and test
  - Effort: Refactor over 3 sprints
```

#### **8. Risk Assessment** (Security, Performance, Code Quality)
Shows: *"What could go wrong?"*
```
RISK-001 [CRITICAL]: No Spring Security
  - Category: Security
  - Impact: Unauthorized access possible
  - Mitigation: Add Spring Security, implement OAuth2

RISK-002 [HIGH]: 50+ Dependencies
  - Category: Dependency Management
  - Impact: Transitive vulnerabilities
  - Mitigation: Audit and update dependencies regularly
```

#### **9. Acceptance Criteria**
Shows: *"How is success tested?"*
```
AC-001: User can create product
  Given: User is logged in as Admin
  When: User submits new product form
  Then: Product appears in catalog with ACTIVE status

AC-002: Invalid email is rejected
  Given: User registration form
  When: User enters invalid email "not-an-email"
  Then: Error message displayed, account not created
```

---

## 📁 File Structure You'll See

```
BRD_agent/
├── app.py                           # The Streamlit web interface
├── .env                             # Your API key (create this)
├── requirements.txt                 # Dependencies
│
├── KB/
│   ├── MyProject/                   # Your uploaded repo
│   │   ├── scope_definition.json    # System scope
│   │   ├── business_rules.json      # Business rules (8-12)
│   │   ├── journey_map.json         # User journeys (8-10)
│   │   ├── gap_analysis.json        # Missing features/tests/docs
│   │   ├── risk_register.json       # Risks identified
│   │   ├── acceptance_criteria.json # Test scenarios
│   │   ├── COMPREHENSIVE_BRD_MyProject.md  # Final markdown BRD
│   │   └── [25 other JSON files with detailed analysis]
│   │
│   └── graph/
│       └── hypergraph.json          # Relationships between services
│
├── .github/skills/agent-*/          # 9 AI agents (automated)
│   ├── agent-1-discovery/           # Discovers system structure
│   ├── agent-2-journey-mapping/     # Maps user workflows
│   ├── agent-3-business-rules/      # Extracts business rules
│   ├── agent-4-gap-analysis/        # Finds gaps
│   ├── agent-5-synthesis/           # Synthesizes findings
│   ├── agent-6-acceptance-criteria/ # Creates test scenarios
│   ├── agent-7-risk-dependency/     # Assesses risks
│   ├── agent-8-summarizer/          # Builds comprehensive BRD
│   └── agent-9-kb-store-sync/       # Indexes for search
│
└── docs-for-new-users/              # Documentation
    ├── BEGINNER_GUIDE.md            # This file!
    ├── getting-started.md           # CLI commands
    └── brd-examples/                # Real BRD examples
```

---

## 🎬 Step-by-Step Walkthrough: Analyzing a Real Repo

### Example: Upload Java Shopping System

#### **Step 1: Prepare Your Repo**

```powershell
# Your Java project folder
C:\my-projects\java-shopping-system\
├── src/
├── tests/
├── pom.xml
└── README.md

# Zip it
Compress-Archive -Path "C:\my-projects\java-shopping-system" -DestinationPath "shopping.zip"
```

#### **Step 2: Upload in UI**

1. Open **http://localhost:8501**
2. **Sidebar** → **📤 Upload Repository**
3. Click **"Upload a .zip file"** → Select `shopping.zip`
4. System asks: **"Add Supporting Documents?"**
   - If you have design docs/requirements → **"✅ Yes"** → Upload `.pdf`/`.md`
   - If just code → **"❌ No, Skip Documents"**
5. Click **▶ Run Pipeline**

#### **Step 3: Wait for Analysis**

Terminal output shows:
```
Agent 1: Discovery & Scoping... [90 seconds]
Agent 2: Journey Mapping... [60 seconds]
Agent 3: Business Rules... [45 seconds]
Agent 4: Gap Analysis... [45 seconds]
Agent 5: Synthesis... [30 seconds]
Agent 6: Acceptance Criteria... [60 seconds]
Agent 7: Risk Assessment... [45 seconds]
Agent 8: BRD Generation... [30 seconds]
Agent 9: KB Sync... [15 seconds]

✅ Pipeline finished. Hypergraph regenerated.
```

#### **Step 4: View Results**

**Tab 1: Generate BRD**
- Comprehensive markdown document with sections 1-9 above
- Download as ZIP with 25+ JSON artifacts
- Share with team

**Tab 2: RAG Chat**
- Ask: *"What are the main risks?"*
- System searches BRD and answers from analyzed data
- Example: *"CRITICAL: No Spring Security configured. Recommend OAuth2 implementation."*

**Tab 3: Hypergraph Explorer** (if multiple repos)
- See connections between services
- Find which service owns a feature
- Understand dependencies

---

## 🔧 Common Tasks

### ❓ "I want to see what a finished BRD looks like"

Check the examples in `docs-for-new-users/brd-examples/`:
- `spring-petclinic.md` — Pet store system
- `employee-simulator.md` — HR system
- `library-management.md` — Library system

Each shows real output from running the pipeline on actual repos.

### ❓ "How do I ask questions about my code?"

Go to **Tab 2: RAG Chat**

Try:
- *"What are the main business rules?"*
- *"What tests are missing?"*
- *"List all API endpoints"*
- *"What are the high-risk areas?"*
- *"Show me the user journeys"*

System searches all generated BRD artifacts and answers based on actual analysis.

### ❓ "I want to run the pipeline on a new repo"

```powershell
# Option 1: Use UI (easiest for beginners)
# Open http://localhost:8501 → Upload ZIP → Run Pipeline

# Option 2: Use CLI
.\run_brd_pipeline.ps1 -RepoPath "C:\path\to\my-repo"
# Output goes to KB\my-repo\
```

### ❓ "I want to query from the command line"

```powershell
python bin/query.py "What are the main risks?"
# Shows: CRITICAL risks found: No Spring Security, 50+ dependencies, etc.
```

### ❓ "I want to integrate with my API"

```powershell
# Start API server
python bin/api_server.py
# → http://localhost:8081

# Query from your code
curl -X POST http://localhost:8081/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What business rules apply?"}'
```

---

## ⚠️ Troubleshooting for Beginners

| Problem | Solution |
|---------|----------|
| **"ANTHROPIC_API_KEY not set"** | Create `.env` file in project root with your API key |
| **Port 8501 in use** | Use `python -m streamlit run app.py --server.port 8502` |
| **Pipeline takes 10 minutes** | This is NORMAL for repos >1000 LOC. LLM analysis takes time. |
| **"No vector store found"** | First time: run `python bin/ingest.py --all` to index the KB |
| **SSL/Network error** | On corporate network? This is expected. Add `--trusted-host` flag to pip |
| **Files say "No API key set"** | BRD still generated but without LLM enhancements. Add `.env` for better analysis |
| **Diagram looks wrong** | Diagrams are generated from code structure. Check your repo has proper package organization |
| **"Only 1 journey found"** | Repo is simple. More journeys are found in complex systems with multiple actors |

---

## 📚 When You're Ready for Advanced Features

Once comfortable with the basics:

1. **Read** `docs-for-new-users/getting-started.md` — More CLI commands
2. **Read** `docs-for-new-users/kb-store-guide.md` — How the system works internally
3. **Read** `BRD_GENERATION_GUIDE.md` — What each agent produces
4. **Read** `docs-for-new-users/AGENTS.md` — Agent architecture
5. **Explore** the API server at `/docs` for Swagger UI

---

## 💡 Tips for Success

✅ **DO:**
- Start with small repos (< 500 files) to understand output format
- Add supporting documents (design specs, requirements) for better analysis
- Read the comprehensive BRD completely on first run
- Share the BRD with team members
- Use RAG Chat to understand your own codebase better

❌ **DON'T:**
- Commit `.env` file to git (contains your API key!)
- Run pipeline on 100+ files simultaneously (may timeout)
- Delete `KB/graph/hypergraph.json` unless you need to reset relationships
- Share the markdown BRD with large file attachments (use the ZIP download)

---

## 🆘 Still Stuck?

1. **Setup issue?** → Read `SETUP_GUIDE.md`
2. **Command help?** → Read `docs-for-new-users/getting-started.md`
3. **Want examples?** → Check `docs-for-new-users/brd-examples/`
4. **Architecture question?** → (kb-store-guide.md coming soon)
5. **Report issue** → GitHub Issues

---

**You're ready to generate your first BRD! 🚀**
