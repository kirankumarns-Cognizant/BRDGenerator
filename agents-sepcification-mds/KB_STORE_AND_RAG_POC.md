# KB Store Component — Build Instructions v2
## For AI Coding Agents (Claude Code / GitHub Copilot / Claude CLI)

---

## IMPORTANT — READ FIRST

This document is the complete specification for building the KB Store Component. You are an AI coding agent. Read this entire document before writing a single line of code. Build phase by phase. Test each phase before moving to the next. Self-correct if tests fail.

The KB Store is a **standalone, independent component**. It does not know which agent produced the artifacts it consumes. It only knows a folder path. It can be triggered automatically after any agent run or manually by a developer pointing it at an existing artifact folder.

### Rules You Must Follow
- Read ALL sections before starting Phase 1
- Complete each phase fully before starting the next
- Run the validation test for each phase — if it fails, fix before proceeding
- Never hardcode paths, credentials, or storage types in component code
- All configuration lives in `config/kb_store_config.yaml`
- Registry and hypergraph storage type is user-configured — JSON or SQLite
- Confluence sync must fail gracefully — if unavailable, log and continue, never crash
- Hypergraph placement agent makes intelligent decisions — not pattern matching
- Notifications are async and non-blocking — pipeline never waits for human
- Query log is always written — it seeds the Phase 2 FAQ cache
- Commit working code after each phase passes validation

---

## WHAT THIS COMPONENT DOES

```
INPUT:
  Folder path         — raw agent output artifacts (JSON, docx, etc.)
  Domain config JSON  — optional business context for intelligent placement
  kb_store_config.yaml — storage types, Confluence credentials, paths

PIPELINE:
  [1] Receive artifacts from input path
  [2] Rename per naming convention
  [3] Extract metadata via LLM
  [4] Resolve conflicts against registry
  [5] Place in hypergraph (intelligent LLM-driven placement)
  [6] Write JSON artifacts to folder structure
  [7] Sync to Confluence (if configured and accessible)
  [8] Update artifact registry (SQLite or JSON)
  [9] Update lineage links
  [10] Write query log entry (seeds Phase 2 FAQ cache)
  [11] Write ingestion summary log

OUTPUT:
  KB/{Brand}/{Domain}/{Feature}/          renamed JSON artifacts
  KB/graph/hypergraph.json                navigation layer
  KB/graph/notifications.json             async placement review items
  KB/cache/query_log.json                 RAG query log (Phase 2 seed)
  registry/artifact_registry.db|json     master artifact index
  registry/ingestion_log.json             run summary
```

---

## PROJECT STRUCTURE

Build exactly this structure. Do not deviate.

```
kb_store/
│
├── config/
│   └── kb_store_config.yaml          # Master config — everything here
│
├── core/
│   ├── __init__.py
│   ├── config_loader.py              # Loads and validates config
│   ├── artifact_receiver.py          # Reads from input path
│   ├── artifact_renamer.py           # Applies naming convention via LLM
│   ├── metadata_extractor.py         # Extracts metadata via LLM
│   ├── conflict_resolver.py          # Checks registry, resolves or escalates
│   └── lineage_tracker.py            # Manages derived_from relationships
│
├── hypergraph/
│   ├── __init__.py
│   ├── hypergraph_interface.py       # Abstract interface — code calls this only
│   ├── json_hypergraph.py            # JSON adapter (POC)
│   ├── sqlite_hypergraph.py          # SQLite adapter (production)
│   ├── hypergraph_factory.py         # Returns correct adapter from config
│   └── placement_agent.py            # Intelligent LLM placement decisions
│
├── storage/
│   ├── __init__.py
│   ├── json_writer.py                # Writes artifacts to KB folder
│   ├── confluence_sync.py            # Confluence pages + TOC (graceful fallback)
│   └── registry/
│       ├── __init__.py
│       ├── registry_interface.py     # Abstract interface
│       ├── sqlite_registry.py        # SQLite adapter
│       ├── json_registry.py          # JSON adapter
│       └── registry_factory.py      # Returns correct adapter from config
│
├── cache/
│   ├── __init__.py
│   └── query_log.py                  # Logs RAG queries — Phase 2 FAQ seed
│
├── domain/
│   ├── __init__.py
│   ├── domain_loader.py              # Loads domain config JSON
│   └── configs/
│       ├── value_domain.json         # Value enterprise domain config
│       ├── empty_domain.json         # Template for unknown domain
│       └── example_domain.json       # New client template
│
├── utils/
│   ├── __init__.py
│   ├── artifact_id.py                # UUID + UTC timestamp ID generation
│   ├── logger.py                     # Structured run logger
│   └── ingestion_log.py              # Run summary writer
│
├── hitl/
│   ├── __init__.py
│   └── hitl_handler.py               # CLI conflict display
│
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   └── sample_artifacts/
│   │       ├── raw_journey_map.json
│   │       ├── raw_business_rules.json
│   │       └── raw_brd_final.json
│   ├── test_phase1_config.py
│   ├── test_phase2_receiver.py
│   ├── test_phase3_metadata.py
│   ├── test_phase4_registry.py
│   ├── test_phase5_hypergraph.py
│   ├── test_phase6_placement.py
│   ├── test_phase7_confluence.py
│   ├── test_phase8_writer.py
│   └── test_phase9_integration.py
│
├── KB/                               # Runtime output (created at runtime)
│   └── .gitkeep
│
├── HITL_PENDING/                     # Conflict HITL files
│   └── .gitkeep
│
├── requirements.txt
├── .env.example
├── .gitignore
└── kb_store.py                       # Entry point
```

---

## REQUIREMENTS.TXT

```
# LLM
anthropic>=0.40.0

# Config
pyyaml>=6.0.1
python-dotenv>=1.0.0

# Confluence sync
atlassian-python-api>=3.41.0

# Embeddings (install now — used by RAG component later)
sentence-transformers>=3.0.0
chromadb>=0.5.0

# Utilities
rich>=13.9.0
jsonschema>=4.23.0

# Stdlib (no install): sqlite3, uuid, pathlib, json, os, datetime, typing, abc
```

---

## .ENV.EXAMPLE

```bash
# Copy to .env — never commit .env to git
ANTHROPIC_API_KEY=your_key_here

# Confluence — fill when available
CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_USERNAME=your_email@company.com
CONFLUENCE_API_TOKEN=your_token_here
CONFLUENCE_SPACE_KEY=SDLC
CONFLUENCE_CLOUD=true
```

---

## CONFLUENCE SETUP INSTRUCTIONS

```
1. Log in at id.atlassian.com
2. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
3. Click "Create API token" — label it: kb-store-agent
4. Copy token — you only see it once
5. Add to .env:
   CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki
   CONFLUENCE_USERNAME=your_email@company.com
   CONFLUENCE_API_TOKEN=<paste token>
   CONFLUENCE_SPACE_KEY=SDLC
6. pip install atlassian-python-api
7. Set confluence.enabled: true in kb_store_config.yaml
8. If access denied at runtime — KB Store logs and continues gracefully
```

---

## .GITIGNORE

```
.env
__pycache__/
*.pyc
.pytest_cache/
KB/
HITL_PENDING/
*.db
.DS_Store
```

---

## DOMAIN CONFIG FILES

### `domain/configs/value_domain.json`
```json
{
  "client_name": "Value Enterprise",
  "description": "Value is a group of prepaid wireless brands including StraightTalk, TotalWireless, TracFone, and Walmart Family Mobile. Migrating from Legacy Java platform to NSA.",
  "brands": ["StraightTalk", "TotalWireless", "TracFone", "WalmartFamilyMobile"],
  "domains": ["service_ordering", "payments", "identity", "catalog", "provisioning", "billing"],
  "legacy_tech": ["Java", "Spring", "Oracle DB", "SOAP APIs", "Selenium"],
  "nsa_tech": ["NSA Platform", "REST APIs", "Event-driven"],
  "known_entities": ["ServiceOrder", "Customer", "Plan", "Payment", "Device", "Activation", "PortIn"],
  "shared_elements": ["Authentication", "Customer identity", "Payment gateway", "Plan catalog"],
  "known_rules": [],
  "notes": "Migration ongoing. New NSA development happening in parallel."
}
```

### `domain/configs/empty_domain.json`
```json
{
  "client_name": "",
  "description": "",
  "brands": [],
  "domains": [],
  "legacy_tech": [],
  "nsa_tech": [],
  "known_entities": [],
  "shared_elements": [],
  "known_rules": [],
  "notes": "Domain unknown — placement agent will discover entities from artifact content."
}
```

### `domain/configs/example_domain.json`
```json
{
  "client_name": "Example Client",
  "description": "Plain English description of what this client does and what is being built or migrated.",
  "brands": ["Brand1", "Brand2"],
  "domains": ["domain1", "domain2"],
  "legacy_tech": ["Java", "Oracle"],
  "nsa_tech": ["NewPlatform", "REST"],
  "known_entities": ["Entity1", "Entity2"],
  "shared_elements": ["SharedConcept1"],
  "known_rules": [],
  "notes": "Any additional context that helps the LLM understand this domain."
}
```

---

## TEST FIXTURE FILES

Create these in `tests/fixtures/sample_artifacts/`:

### `raw_journey_map.json`
```json
{
  "component_name": "SampleService",
  "domain": "service_ordering",
  "journeys": [
    {
      "name": "Standard Payment Happy Path",
      "type": "happy",
      "actor": "Customer",
      "trigger": "Customer submits payment",
      "steps": ["Validate customer", "Check eligibility", "Process payment"],
      "outcome": "Payment processed successfully",
      "confidence": "HIGH"
    }
  ],
  "total_journeys": 1,
  "confidence": "HIGH",
  "producer_agent": "brd_agent",
  "run_id": "test-run-001"
}
```

### `raw_business_rules.json`
```json
{
  "component_name": "SampleService",
  "domain": "service_ordering",
  "rules": [
    {
      "id": "BR-001",
      "name": "High Value Transaction Threshold",
      "plain_english": "Transactions over $1000 require manager approval",
      "rule_type": "validation",
      "confidence": "HIGH"
    }
  ],
  "total_rules": 1,
  "producer_agent": "brd_agent",
  "run_id": "test-run-001"
}
```

### `raw_brd_final.json`
```json
{
  "component_name": "SampleService",
  "domain": "service_ordering",
  "brd_version": "0.1.0-poc",
  "locked": true,
  "overall_confidence": 0.75,
  "scope": {"in_scope": ["processPayment", "checkEligibility"]},
  "journeys": [],
  "business_rules": [],
  "producer_agent": "brd_agent",
  "run_id": "test-run-001"
}
```

---

## KB_STORE_CONFIG.YAML

```yaml
# =============================================================================
# KB STORE — MASTER CONFIGURATION
# =============================================================================
# SETUP INSTRUCTIONS:
#   1. Fill in resource paths below
#   2. Choose registry.type: json (simple POC) or sqlite (parallel writes)
#   3. Choose hypergraph.type: json (POC) or sqlite (production)
#   4. Set confluence.enabled: true when Confluence is configured
#   5. Run: python kb_store.py --path ./your/artifact/folder
#
# REGISTRY & HYPERGRAPH STORAGE CHOICE:
#   Ask yourself: do I need concurrent parallel writes from multiple agents?
#   YES → use sqlite for both registry and hypergraph
#   NO  → use json for both (simpler, human-readable, git-versionable)
# =============================================================================

# ── INPUT ────────────────────────────────────────────────────────────────────
input:
  path: ""                      # CHANGE THIS for manual mode
                                # e.g. ./brd_agent_poc/KB/sample_repo/
  recursive: true
  file_types:
    - "*.json"
    - "*.docx"
    - "*.md"
    - "*.feature"
  exclude_patterns:
    - "run_metadata.json"
    - "event_log*"
    - "hitl_*"
    - "*.meta.json"
    - "ingestion_log.json"
    - "query_log.json"

# ── OUTPUT ───────────────────────────────────────────────────────────────────
output:
  kb_root: ./KB
  hitl_pending: ./HITL_PENDING

# ── REGISTRY ─────────────────────────────────────────────────────────────────
registry:
  type: json                    # json | sqlite
  path: ./registry
  filename: artifact_registry
  backup_on_write: true

# ── HYPERGRAPH ───────────────────────────────────────────────────────────────
hypergraph:
  type: json                    # json | sqlite
                                # Future: kuzu (enterprise graph DB)
  path: ./KB/graph
  filename: hypergraph
  notifications_file: ./KB/graph/notifications.json

# ── CONFLUENCE ───────────────────────────────────────────────────────────────
confluence:
  enabled: false
  parent_page_title: "SDLC Knowledge Base"
  create_toc: true
  update_existing: true

# ── LLM ──────────────────────────────────────────────────────────────────────
llm:
  provider: anthropic
  model: claude-haiku-4-5-20251001
  temperature: 0.1
  max_tokens: 2048
  placement_model: claude-sonnet-4-5   # Placement needs stronger reasoning

# ── DOMAIN CONFIG ────────────────────────────────────────────────────────────
domain:
  config_path: ./domain/configs/value_domain.json

# ── NAMING CONVENTION ────────────────────────────────────────────────────────
artifact_types:
  - journey_map
  - business_rules
  - gap_analysis
  - brd_final
  - scope_definition
  - test_cases
  - ac_criteria
  - code_review
  - defect_analysis
  - actor_definitions
  - dependency_map
  - risk_register
  - regression_gaps
  - api_spec
  - story_brief

brand_prefixes:
  StraightTalk: ST
  TotalWireless: TW
  TracFone: TF
  WalmartFamilyMobile: WFM
  Shared: SHARED
  Value: VALUE
  External: EXT

# ── CONFLICT RESOLUTION ──────────────────────────────────────────────────────
conflict_resolution:
  auto_overwrite_newer_version: true
  auto_flag_lower_confidence: true
  hitl_on_potential_duplicate: true
  max_autonomous_decisions_per_run: 10

# ── PLACEMENT AGENT ──────────────────────────────────────────────────────────
placement:
  similarity_threshold_place: 0.85    # above this → place in existing node
  similarity_threshold_temp: 0.60     # below this → create TEMP node
  # between thresholds → LLM decides
  max_candidate_nodes: 5              # compare against top N existing nodes
  auto_create_hyperedge: true         # create cross-brand edges automatically
  notification_on_new_node: false     # notify when new permanent node created?
  notification_on_hyperedge: true     # notify when new hyperedge created?
  notification_on_temp: true          # always notify on TEMP node

# ── QUERY LOG ────────────────────────────────────────────────────────────────
query_log:
  enabled: true
  path: ./KB/cache/query_log.json
  max_entries: 10000              # rotate after this many entries

# ── INGESTION LOG ────────────────────────────────────────────────────────────
ingestion_log:
  path: ./registry/ingestion_log.json
  keep_last_n_runs: 50
```

---

## PHASE 1 — Config + Scaffold + Domain Loader + Artifact ID

### Goal
Project scaffold created. Config loads. Domain loader works. Artifact IDs generate correctly. All tests pass without API calls.

### Step 1.1 — Project Scaffold
Create all directories, `__init__.py` files, `.gitignore`, `.env.example`, `requirements.txt`. Create `KB/.gitkeep` and `HITL_PENDING/.gitkeep`. Create all test fixture files.

### Step 1.2 — Config Loader

Create `core/config_loader.py`:

```python
"""
Config Loader — single source of truth for all KB Store configuration.
Every other module reads configuration from here.
Never import pyyaml directly in other modules.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class KBStoreConfig:

    def __init__(self, config_path: str = "config/kb_store_config.yaml"):
        self.config_path = Path(config_path)
        self._raw = self._load()
        self._validate()

    def _load(self) -> Dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _validate(self):
        required = ["input", "output", "registry", "hypergraph",
                    "confluence", "llm", "domain", "placement"]
        for key in required:
            if key not in self._raw:
                raise ValueError(f"Missing required config section: {key}")

    # ── INPUT ──────────────────────────────────────────────────
    @property
    def input_path(self) -> str:
        return self._raw["input"].get("path", "")

    @property
    def input_recursive(self) -> bool:
        return self._raw["input"].get("recursive", True)

    @property
    def input_file_types(self) -> list:
        return self._raw["input"].get("file_types", ["*.json"])

    @property
    def input_exclude_patterns(self) -> list:
        return self._raw["input"].get("exclude_patterns", [])

    # ── OUTPUT ─────────────────────────────────────────────────
    @property
    def kb_root(self) -> Path:
        return Path(self._raw["output"]["kb_root"])

    @property
    def hitl_pending_path(self) -> Path:
        return Path(self._raw["output"]["hitl_pending"])

    # ── REGISTRY ───────────────────────────────────────────────
    @property
    def registry_type(self) -> str:
        t = self._raw["registry"].get("type", "json")
        if t not in ["json", "sqlite"]:
            raise ValueError(f"registry.type must be json or sqlite, got: {t}")
        return t

    @property
    def registry_path(self) -> Path:
        return Path(self._raw["registry"]["path"])

    @property
    def registry_filename(self) -> str:
        return self._raw["registry"]["filename"]

    @property
    def registry_backup(self) -> bool:
        return self._raw["registry"].get("backup_on_write", True)

    # ── HYPERGRAPH ─────────────────────────────────────────────
    @property
    def hypergraph_type(self) -> str:
        t = self._raw["hypergraph"].get("type", "json")
        if t not in ["json", "sqlite"]:
            raise ValueError(f"hypergraph.type must be json or sqlite, got: {t}")
        return t

    @property
    def hypergraph_path(self) -> Path:
        return Path(self._raw["hypergraph"]["path"])

    @property
    def hypergraph_filename(self) -> str:
        return self._raw["hypergraph"]["filename"]

    @property
    def notifications_file(self) -> Path:
        return Path(self._raw["hypergraph"]["notifications_file"])

    # ── CONFLUENCE ─────────────────────────────────────────────
    @property
    def confluence_enabled(self) -> bool:
        return self._raw["confluence"].get("enabled", False)

    @property
    def confluence_credentials(self) -> Dict:
        return {
            "url": os.getenv("CONFLUENCE_URL", ""),
            "username": os.getenv("CONFLUENCE_USERNAME", ""),
            "api_token": os.getenv("CONFLUENCE_API_TOKEN", ""),
            "space_key": os.getenv("CONFLUENCE_SPACE_KEY", "SDLC"),
            "is_cloud": os.getenv("CONFLUENCE_CLOUD", "true").lower() == "true"
        }

    @property
    def confluence_parent_page(self) -> str:
        return self._raw["confluence"].get("parent_page_title", "SDLC Knowledge Base")

    # ── LLM ────────────────────────────────────────────────────
    @property
    def llm_model(self) -> str:
        return self._raw["llm"].get("model", "claude-haiku-4-5-20251001")

    @property
    def llm_placement_model(self) -> str:
        return self._raw["llm"].get("placement_model", "claude-sonnet-4-5")

    @property
    def llm_temperature(self) -> float:
        return self._raw["llm"].get("temperature", 0.1)

    @property
    def llm_max_tokens(self) -> int:
        return self._raw["llm"].get("max_tokens", 2048)

    # ── DOMAIN ─────────────────────────────────────────────────
    @property
    def domain_config_path(self) -> str:
        return self._raw["domain"].get("config_path", "./domain/configs/empty_domain.json")

    # ── NAMING ─────────────────────────────────────────────────
    @property
    def artifact_types(self) -> list:
        return self._raw.get("artifact_types", [])

    @property
    def brand_prefixes(self) -> Dict:
        return self._raw.get("brand_prefixes", {})

    # ── PLACEMENT ──────────────────────────────────────────────
    @property
    def placement_similarity_place(self) -> float:
        return self._raw["placement"].get("similarity_threshold_place", 0.85)

    @property
    def placement_similarity_temp(self) -> float:
        return self._raw["placement"].get("similarity_threshold_temp", 0.60)

    @property
    def placement_max_candidates(self) -> int:
        return self._raw["placement"].get("max_candidate_nodes", 5)

    @property
    def placement_auto_hyperedge(self) -> bool:
        return self._raw["placement"].get("auto_create_hyperedge", True)

    # ── QUERY LOG ──────────────────────────────────────────────
    @property
    def query_log_enabled(self) -> bool:
        return self._raw.get("query_log", {}).get("enabled", True)

    @property
    def query_log_path(self) -> Path:
        return Path(self._raw.get("query_log", {}).get("path", "./KB/cache/query_log.json"))

    @property
    def query_log_max_entries(self) -> int:
        return self._raw.get("query_log", {}).get("max_entries", 10000)

    # ── INGESTION LOG ──────────────────────────────────────────
    @property
    def ingestion_log_path(self) -> Path:
        return Path(self._raw["ingestion_log"]["path"])

    @property
    def ingestion_log_keep_n(self) -> int:
        return self._raw["ingestion_log"].get("keep_last_n_runs", 50)

    @property
    def raw(self) -> Dict:
        return self._raw
```

### Step 1.3 — Artifact ID Generator

Create `utils/artifact_id.py`:

```python
"""
Artifact ID — UUID + UTC timestamp.
Format: YYYYMMDD_HHMMSS_UTC_{uuid4_8chars}
Sortable by creation time. Unique across parallel runs in any timezone.
"""
import uuid
from datetime import datetime, timezone

def generate_artifact_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
    short = str(uuid.uuid4()).replace("-", "")[:8]
    return f"{ts}_{short}"

def parse_artifact_id(artifact_id: str) -> dict:
    parts = artifact_id.split("_")
    if len(parts) < 4:
        return {"artifact_id": artifact_id, "valid": False}
    return {
        "artifact_id": artifact_id,
        "date": parts[0],
        "time": parts[1],
        "timezone": parts[2],
        "short_uuid": parts[3],
        "valid": True
    }
```

### Step 1.4 — Domain Loader

Create `domain/domain_loader.py`:

```python
"""
Domain Loader — reads domain config JSON.
Provides ontology prompt for LLM calls throughout KB Store.
Returns empty domain gracefully if config missing or empty.
"""
import json
from pathlib import Path
from typing import Dict
from rich.console import Console

console = Console()

EMPTY_DOMAIN = {
    "client_name": "", "description": "", "brands": [],
    "domains": [], "legacy_tech": [], "nsa_tech": [],
    "known_entities": [], "shared_elements": [], "known_rules": [], "notes": ""
}

class DomainLoader:

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._domain = self._load()

    def _load(self) -> Dict:
        if not self.config_path.exists():
            console.print(f"[dim yellow]⚠️  Domain config not found: {self.config_path}. Using empty domain.[/dim yellow]")
            return EMPTY_DOMAIN
        try:
            with open(self.config_path) as f:
                domain = json.load(f)
            if domain.get("client_name"):
                console.print(f"[dim green]✓ Domain config loaded: {self.config_path.name} ({domain['client_name']})[/dim green]")
            return domain
        except Exception as e:
            console.print(f"[dim yellow]⚠️  Domain config parse error: {e}. Using empty domain.[/dim yellow]")
            return EMPTY_DOMAIN

    def get_ontology_prompt(self) -> str:
        """Context prompt passed to LLM for entity extraction and placement decisions."""
        d = self._domain
        if not d.get("client_name"):
            return "No domain context available. Infer everything from artifact content."
        lines = [
            f"Client: {d['client_name']}",
            f"Context: {d.get('description', '')}",
        ]
        if d.get("brands"):
            lines.append(f"Brands: {', '.join(d['brands'])}")
        if d.get("domains"):
            lines.append(f"Business domains: {', '.join(d['domains'])}")
        if d.get("known_entities"):
            lines.append(f"Known entities: {', '.join(d['known_entities'])}")
        if d.get("shared_elements"):
            lines.append(f"Shared elements across brands: {', '.join(d['shared_elements'])}")
        if d.get("notes"):
            lines.append(f"Notes: {d['notes']}")
        return "\n".join(lines)

    @property
    def brands(self) -> list:
        return self._domain.get("brands", [])

    @property
    def client_name(self) -> str:
        return self._domain.get("client_name", "")

    @property
    def raw(self) -> Dict:
        return self._domain
```

### Step 1.5 — Logger and Ingestion Log

Create `utils/logger.py`:

```python
import json
from datetime import datetime, timezone
from rich.console import Console

console = Console()

class KBLogger:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.events = []

    def info(self, msg: str, **kw):
        self._log("INFO", msg, **kw)
        console.print(f"[dim]{msg}[/dim]")

    def success(self, msg: str, **kw):
        self._log("SUCCESS", msg, **kw)
        console.print(f"[green]✓ {msg}[/green]")

    def warning(self, msg: str, **kw):
        self._log("WARNING", msg, **kw)
        console.print(f"[yellow]⚠️  {msg}[/yellow]")

    def error(self, msg: str, **kw):
        self._log("ERROR", msg, **kw)
        console.print(f"[red]✗ {msg}[/red]")

    def _log(self, level: str, msg: str, **kw):
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "level": level,
            "message": msg,
            **kw
        })

    def get_events(self) -> list:
        return self.events
```

Create `utils/ingestion_log.py`:

```python
import json
from datetime import datetime, timezone
from pathlib import Path

class IngestionLog:
    def __init__(self, config):
        self.log_path = config.ingestion_log_path
        self.keep_n = config.ingestion_log_keep_n
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, summary: dict):
        existing = self._read()
        existing.append({"timestamp": datetime.now(timezone.utc).isoformat(), **summary})
        trimmed = existing[-self.keep_n:]
        with open(self.log_path, "w") as f:
            json.dump(trimmed, f, indent=2, default=str)

    def _read(self) -> list:
        if not self.log_path.exists():
            return []
        with open(self.log_path) as f:
            return json.load(f)
```

### Phase 1 Validation Test

Create `tests/test_phase1_config.py`:

```python
"""
Phase 1 Validation Tests — run without API
Run: pytest tests/test_phase1_config.py -v
All must pass before Phase 2.
"""
import pytest
import time
from pathlib import Path
from core.config_loader import KBStoreConfig
from utils.artifact_id import generate_artifact_id, parse_artifact_id
from domain.domain_loader import DomainLoader

def test_config_file_exists():
    assert Path("config/kb_store_config.yaml").exists()

def test_config_loads():
    config = KBStoreConfig()
    assert config is not None

def test_config_required_sections():
    config = KBStoreConfig()
    for section in ["input", "output", "registry", "hypergraph",
                    "confluence", "llm", "domain", "placement"]:
        assert section in config.raw

def test_registry_type_valid():
    config = KBStoreConfig()
    assert config.registry_type in ["json", "sqlite"]

def test_hypergraph_type_valid():
    config = KBStoreConfig()
    assert config.hypergraph_type in ["json", "sqlite"]

def test_artifact_id_unique():
    id1 = generate_artifact_id()
    time.sleep(1.1)
    id2 = generate_artifact_id()
    assert id1 != id2

def test_artifact_id_sortable():
    id1 = generate_artifact_id()
    time.sleep(1.1)
    id2 = generate_artifact_id()
    assert id1 < id2

def test_artifact_id_parse():
    aid = generate_artifact_id()
    parsed = parse_artifact_id(aid)
    assert parsed["valid"] is True
    assert parsed["timezone"] == "UTC"

def test_domain_loader_value():
    loader = DomainLoader("./domain/configs/value_domain.json")
    assert loader.client_name == "Value Enterprise"
    assert "StraightTalk" in loader.brands

def test_domain_loader_missing_file():
    loader = DomainLoader("./nonexistent.json")
    assert loader.client_name == ""

def test_domain_loader_empty_prompt():
    loader = DomainLoader("./domain/configs/empty_domain.json")
    prompt = loader.get_ontology_prompt()
    assert "No domain context" in prompt

def test_domain_loader_value_prompt():
    loader = DomainLoader("./domain/configs/value_domain.json")
    prompt = loader.get_ontology_prompt()
    assert "Value Enterprise" in prompt
    assert len(prompt) > 50

def test_fixture_files_exist():
    base = Path("tests/fixtures/sample_artifacts")
    assert (base / "raw_journey_map.json").exists()
    assert (base / "raw_business_rules.json").exists()
    assert (base / "raw_brd_final.json").exists()

def test_kb_dirs_creatable(tmp_path):
    (tmp_path / "KB").mkdir()
    (tmp_path / "HITL_PENDING").mkdir()
    assert (tmp_path / "KB").exists()
```

---

## PHASE 2 — Artifact Receiver + Renamer

### Goal
KB Store reads all artifacts from input path. Detects artifact types from filename and content signals. Renames per convention using LLM for missing fields. Produces rename manifest without writing anything.

### Step 2.1 — Artifact Receiver

Create `core/artifact_receiver.py`:

```python
"""
Artifact Receiver — reads raw artifact files from input path.
Detects artifact types from filename signals and content keys.
Does NOT rename or write — only receives and categorizes.
"""
import json
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

# Content key signals per artifact type
ARTIFACT_SIGNALS = {
    "journey_map":      ["journeys", "journey_inventory", "journey_map", "actors"],
    "business_rules":   ["rules", "business_rules", "rule_catalog"],
    "gap_analysis":     ["gaps", "gap_analysis", "gap_register", "blocking_gaps"],
    "brd_final":        ["brd_version", "locked", "brd_final", "brd_locked"],
    "scope_definition": ["in_scope", "out_of_scope", "scope_definition"],
    "test_cases":       ["test_cases", "test_scenarios", "test_methods"],
    "ac_criteria":      ["acceptance_criteria", "given", "when", "then"],
    "actor_definitions":["actors", "actor_registry", "roles"],
    "dependency_map":   ["dependencies", "dependency_register"],
    "risk_register":    ["risks", "risk_register", "risk_level"],
    "regression_gaps":  ["regression_gap", "coverage_gaps"],
    "code_review":      ["code_review", "review_findings"],
    "defect_analysis":  ["defect", "root_cause", "triage"],
    "story_brief":      ["story", "epic", "user_story"],
    "api_spec":         ["api_spec", "openapi", "swagger", "endpoints"],
}

class ArtifactReceiver:

    def __init__(self, config):
        self.config = config
        self.exclude_patterns = config.input_exclude_patterns
        self.file_types = config.input_file_types

    def receive(self, input_path: str) -> List[Dict]:
        path = Path(input_path)
        if not path.exists():
            console.print(f"[red]✗ Input path not found: {input_path}[/red]")
            return []

        files = list(path.rglob("*")) if self.config.input_recursive else list(path.glob("*"))
        artifacts = []

        for file_path in files:
            if not file_path.is_file():
                continue
            if self._is_excluded(file_path.name):
                continue
            if not self._matches_type(file_path.name):
                continue
            artifact = self._read(file_path)
            if artifact:
                artifacts.append(artifact)

        console.print(f"[dim]  📥 Received {len(artifacts)} artifacts from {input_path}[/dim]")
        return artifacts

    def _read(self, file_path: Path) -> Optional[Dict]:
        try:
            content = None
            preview = {}

            if file_path.suffix == ".json":
                with open(file_path) as f:
                    content = json.load(f)
                preview = content if isinstance(content, dict) else {}
            else:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")[:2000]
                except Exception:
                    content = ""

            return {
                "original_path": str(file_path),
                "original_filename": file_path.name,
                "extension": file_path.suffix,
                "size_bytes": file_path.stat().st_size,
                "content": content,
                "content_preview": preview,
                "detected_type": self._detect_type(file_path.name, preview),
                "detected_agent": preview.get("producer_agent", "unknown"),
                "detected_run_id": preview.get("run_id", ""),
                "detected_component": preview.get("component_name", ""),
                "detected_domain": preview.get("domain", ""),
                "detected_confidence": preview.get("confidence", "UNKNOWN"),
            }
        except Exception as e:
            console.print(f"[dim yellow]⚠️  Could not read {file_path.name}: {e}[/dim yellow]")
            return None

    def _detect_type(self, filename: str, content: Dict) -> str:
        fname = filename.lower()
        for atype, signals in ARTIFACT_SIGNALS.items():
            if any(s in fname for s in signals):
                return atype
        content_keys = " ".join(str(k).lower() for k in content.keys())
        for atype, signals in ARTIFACT_SIGNALS.items():
            if any(s in content_keys for s in signals):
                return atype
        return "unknown"

    def _is_excluded(self, filename: str) -> bool:
        return any(fnmatch.fnmatch(filename, p) for p in self.exclude_patterns)

    def _matches_type(self, filename: str) -> bool:
        return any(fnmatch.fnmatch(filename, p) for p in self.file_types)
```

### Step 2.2 — Artifact Renamer

Create `core/artifact_renamer.py`:

```python
"""
Artifact Renamer — applies naming convention to received artifacts.
Uses LLM to infer brand/domain/feature when not determinable from content.
Produces rename manifest — does NOT write files.

Naming convention: {brand}_{domain_short}_{feature}_{artifact_type}_v{version}.{ext}
"""
import json
import os
from typing import Dict, List
from rich.console import Console
import anthropic

console = Console()

RENAME_SYSTEM = """You are naming enterprise knowledge artifacts following a strict convention.
Given artifact content, extract the naming fields.
Respond ONLY in valid JSON. No preamble. No markdown fences."""

RENAME_PROMPT = """Determine naming fields for this artifact.

DOMAIN CONTEXT:
{domain_context}

ARTIFACT TYPE (detected): {artifact_type}
ORIGINAL FILENAME: {filename}
CONTENT PREVIEW:
{content_preview}

Respond with ONLY this JSON:
{{
  "brand": "ST|TW|TF|WFM|SHARED|VALUE|EXT",
  "domain": "service_ordering|payments|identity|catalog|provisioning|billing|unknown",
  "feature": "short feature name e.g. Activation, PortIn, Subscription",
  "version": "1",
  "confidence": "HIGH|MEDIUM|LOW",
  "reasoning": "one line explanation"
}}"""

class ArtifactRenamer:

    def __init__(self, config, domain_loader):
        self.config = config
        self.domain_loader = domain_loader
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def create_rename_manifest(self, artifacts: List[Dict]) -> List[Dict]:
        manifest = []
        for artifact in artifacts:
            item = self._rename(artifact)
            manifest.append(item)
            status = "✓" if item["rename_confidence"] != "LOW" else "⚠"
            console.print(f"[dim]  {status} {artifact['original_filename']} → {item['new_filename']}[/dim]")
        return manifest

    def _rename(self, artifact: Dict) -> Dict:
        fields = self._extract_from_content(artifact)
        if self._needs_llm(fields, artifact):
            fields = self._extract_via_llm(artifact, fields)
        new_filename = self._build_filename(fields, artifact["extension"])
        return {
            **artifact,
            "naming_fields": fields,
            "new_filename": new_filename,
            "new_relative_path": self._build_path(fields, new_filename),
            "rename_confidence": fields.get("confidence", "LOW")
        }

    def _extract_from_content(self, artifact: Dict) -> Dict:
        preview = artifact.get("content_preview", {})
        brand = self._detect_brand(preview)
        domain = artifact.get("detected_domain") or preview.get("domain", "")
        feature = preview.get("component_name") or preview.get("feature", "")
        atype = artifact.get("detected_type", "unknown")
        confident = all([brand, domain, feature, atype != "unknown"])
        return {
            "brand": brand, "domain": domain, "feature": feature,
            "artifact_type": atype, "version": "1",
            "confidence": "HIGH" if confident else "LOW"
        }

    def _detect_brand(self, content: Dict) -> str:
        content_str = json.dumps(content).lower()
        for brand, prefix in self.config.brand_prefixes.items():
            if brand.lower() in content_str:
                return prefix
        brands = self.domain_loader.brands
        if len(brands) == 1:
            return self.config.brand_prefixes.get(brands[0], "EXT")
        return ""

    def _needs_llm(self, fields: Dict, artifact: Dict) -> bool:
        return not all([fields.get("brand"), fields.get("domain"),
                        fields.get("feature"), fields.get("artifact_type") != "unknown"])

    def _extract_via_llm(self, artifact: Dict, existing: Dict) -> Dict:
        try:
            preview = json.dumps(artifact.get("content_preview", {}), indent=2)[:1500]
            prompt = RENAME_PROMPT.format(
                domain_context=self.domain_loader.get_ontology_prompt()[:500],
                artifact_type=existing.get("artifact_type", "unknown"),
                filename=artifact["original_filename"],
                content_preview=preview
            )
            resp = self.client.messages.create(
                model=self.config.llm_model,
                max_tokens=self.config.llm_max_tokens,
                system=RENAME_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except Exception as e:
            console.print(f"[dim yellow]⚠️  LLM rename failed for {artifact['original_filename']}: {e}[/dim yellow]")
            return {**existing, "brand": existing.get("brand") or "EXT",
                    "domain": existing.get("domain") or "unknown",
                    "feature": existing.get("feature") or "unknown",
                    "confidence": "LOW"}

    def _build_filename(self, fields: Dict, ext: str) -> str:
        brand = fields.get("brand", "EXT")
        domain = fields.get("domain", "unknown")
        domain_short = "".join(w[0].upper() for w in domain.split("_")) if "_" in domain else domain[:8]
        feature = fields.get("feature", "unknown").replace(" ", "").replace("-", "")
        atype = fields.get("artifact_type", "artifact")
        ver = fields.get("version", "1")
        return f"{brand}_{domain_short}_{feature}_{atype}_v{ver}{ext}"

    def _build_path(self, fields: Dict, filename: str) -> str:
        brand_map = {v: k for k, v in self.config.brand_prefixes.items()}
        brand_full = brand_map.get(fields.get("brand", "EXT"), "External")
        domain = fields.get("domain", "unknown")
        feature = fields.get("feature", "unknown")
        return f"{brand_full}/{domain}/{feature}/{filename}"
```

### Phase 2 Validation Test

Create `tests/test_phase2_receiver.py`:

```python
"""
Phase 2 Validation Tests
Run: SKIP_API_TESTS=true pytest tests/test_phase2_receiver.py -v
"""
import pytest, os
from pathlib import Path
from core.config_loader import KBStoreConfig
from core.artifact_receiver import ArtifactReceiver
from domain.domain_loader import DomainLoader

SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

@pytest.fixture
def config(): return KBStoreConfig()
@pytest.fixture
def receiver(config): return ArtifactReceiver(config)

def test_receiver_reads_fixtures(receiver):
    artifacts = receiver.receive("tests/fixtures/sample_artifacts")
    assert len(artifacts) >= 3

def test_detects_journey_map(receiver):
    artifacts = receiver.receive("tests/fixtures/sample_artifacts")
    assert "journey_map" in [a["detected_type"] for a in artifacts]

def test_detects_business_rules(receiver):
    artifacts = receiver.receive("tests/fixtures/sample_artifacts")
    assert "business_rules" in [a["detected_type"] for a in artifacts]

def test_detects_brd_final(receiver):
    artifacts = receiver.receive("tests/fixtures/sample_artifacts")
    assert "brd_final" in [a["detected_type"] for a in artifacts]

def test_handles_missing_path(receiver):
    assert receiver.receive("./nonexistent/") == []

def test_excludes_patterns(receiver):
    artifacts = receiver.receive("tests/fixtures/sample_artifacts")
    names = [a["original_filename"] for a in artifacts]
    assert not any("run_metadata" in n for n in names)

def test_renamer_builds_filename(config):
    from core.artifact_renamer import ArtifactRenamer
    domain = DomainLoader(config.domain_config_path)
    renamer = ArtifactRenamer(config, domain)
    fields = {"brand": "ST", "domain": "service_ordering",
               "feature": "Activation", "artifact_type": "journey_map", "version": "1"}
    fn = renamer._build_filename(fields, ".json")
    assert fn.startswith("ST_") and "journey_map" in fn and fn.endswith(".json")

def test_renamer_manifest_no_files_written(config, tmp_path):
    from core.artifact_renamer import ArtifactRenamer
    domain = DomainLoader(config.domain_config_path)
    renamer = ArtifactRenamer(config, domain)
    receiver = ArtifactReceiver(config)
    artifacts = receiver.receive("tests/fixtures/sample_artifacts")
    manifest = renamer.create_rename_manifest(artifacts)
    assert len(manifest) == len(artifacts)
    for item in manifest:
        assert "new_filename" in item
        assert "new_relative_path" in item
```

---

## PHASE 3 — Metadata Extractor

### Goal
For every artifact — extract structured metadata via LLM. All base fields always populated. LLM enriches additional fields from content.

### Step 3.1 — Metadata Extractor

Create `core/metadata_extractor.py`:

```python
"""
Metadata Extractor — creates metadata node for each artifact.
Base fields always populated from naming fields and artifact content.
LLM enriches: description, tags, useful_for, entity_mentions.
Sparse schema — fields absent when unknown, not null.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, List
from rich.console import Console
import anthropic
from utils.artifact_id import generate_artifact_id

console = Console()

META_SYSTEM = """You extract structured metadata from software artifacts.
Extract only what you can confidently determine. Omit fields you cannot determine.
Respond ONLY in valid JSON. No preamble. No markdown."""

META_PROMPT = """Extract metadata from this artifact.

DOMAIN CONTEXT: {domain_context}
ARTIFACT TYPE: {artifact_type}
FILENAME: {filename}
PRODUCER: {producer}

CONTENT:
{content}

Respond with ONLY this JSON (omit fields you cannot determine):
{{
  "description": "one sentence — what this artifact contains",
  "tags": ["business", "relevant", "tags"],
  "useful_for": ["test_case_writing", "code_generation", "defect_triage",
                 "architecture_decision", "hitl_support", "requirement_clarification"],
  "entity_mentions": ["business entities mentioned"],
  "notes": "important observations"
}}"""

class MetadataExtractor:

    def __init__(self, config, domain_loader):
        self.config = config
        self.domain_loader = domain_loader
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def extract_batch(self, manifest: List[Dict]) -> List[Dict]:
        for item in manifest:
            item["metadata"] = self.extract(item)
            console.print(f"[dim]  📋 Metadata: {item['metadata']['name']}[/dim]")
        return manifest

    def extract(self, item: Dict) -> Dict:
        fields = item.get("naming_fields", {})
        now = datetime.now(timezone.utc).isoformat()

        base = {
            "artifact_id": generate_artifact_id(),
            "name": item["new_filename"],
            "original_filename": item["original_filename"],
            "artifact_type": fields.get("artifact_type", "unknown"),
            "producer_agent": item.get("detected_agent", "unknown"),
            "producer_run_id": item.get("detected_run_id", ""),
            "brand": fields.get("brand", ""),
            "domain": fields.get("domain", ""),
            "feature": fields.get("feature", ""),
            "version": fields.get("version", "1"),
            "format": item["extension"].lstrip("."),
            "file_path": item.get("new_relative_path", ""),
            "confluence_url": "",
            "confidence": fields.get("confidence", "UNKNOWN"),
            "created_at": now,
            "updated_at": now,
            "client": self.domain_loader.client_name or "unknown",
            "derived_from": [],
            # Evolves over time — empty at creation
            "used_for": [],
            "query_intents": [],
            "hitl_decisions_informed": [],
            "co_retrieved_with": [],
            "usefulness_scores": {},
            "access_count": 0,
            "last_accessed": None,
            "superseded_by": None,
            "entity_tags": [],
            "cross_brand_relevance": [],
            "alias": [],
            "notes": "",
            "hypergraph_node_id": "",  # set by placement agent
        }

        enriched = self._enrich_via_llm(item, fields)
        merged = {**base, **{k: v for k, v in enriched.items() if v}}
        # Never let LLM override these
        merged["artifact_id"] = base["artifact_id"]
        merged["created_at"] = base["created_at"]
        return merged

    def _enrich_via_llm(self, item: Dict, fields: Dict) -> Dict:
        try:
            content = item.get("content", {})
            content_str = json.dumps(content, default=str)[:2000] if isinstance(content, dict) else str(content)[:2000]
            prompt = META_PROMPT.format(
                domain_context=self.domain_loader.get_ontology_prompt()[:400],
                artifact_type=fields.get("artifact_type", "unknown"),
                filename=item.get("new_filename", ""),
                producer=item.get("detected_agent", "unknown"),
                content=content_str
            )
            resp = self.client.messages.create(
                model=self.config.llm_model,
                max_tokens=self.config.llm_max_tokens,
                system=META_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except Exception as e:
            console.print(f"[dim yellow]⚠️  Metadata LLM failed: {e}[/dim yellow]")
            return {}
```

### Phase 3 Validation Test

Create `tests/test_phase3_metadata.py`:

```python
"""
Phase 3 Validation Tests
Run: SKIP_API_TESTS=true pytest tests/test_phase3_metadata.py -v
"""
import pytest, os
from utils.artifact_id import generate_artifact_id
from datetime import datetime, timezone

SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

REQUIRED_BASE_FIELDS = [
    "artifact_id", "name", "artifact_type", "producer_agent",
    "brand", "domain", "feature", "version", "format", "confidence",
    "created_at", "updated_at", "derived_from", "used_for",
    "query_intents", "access_count", "hypergraph_node_id"
]

def make_manifest_item(overrides=None):
    item = {
        "new_filename": "ST_SO_Activation_journey_map_v1.json",
        "original_filename": "raw_journey_map.json",
        "extension": ".json",
        "new_relative_path": "StraightTalk/service_ordering/Activation/",
        "detected_agent": "brd_agent",
        "detected_run_id": "test-run-001",
        "content": {"journeys": [], "domain": "service_ordering"},
        "content_preview": {"journeys": [], "domain": "service_ordering"},
        "naming_fields": {
            "brand": "ST", "domain": "service_ordering",
            "feature": "Activation", "artifact_type": "journey_map",
            "version": "1", "confidence": "HIGH"
        }
    }
    if overrides:
        item.update(overrides)
    return item

def test_base_fields_always_present():
    """Test base fields without API call."""
    aid = generate_artifact_id()
    now = datetime.now(timezone.utc).isoformat()
    item = make_manifest_item()
    fields = item["naming_fields"]

    base = {
        "artifact_id": aid,
        "name": item["new_filename"],
        "artifact_type": fields["artifact_type"],
        "producer_agent": item["detected_agent"],
        "brand": fields["brand"],
        "domain": fields["domain"],
        "feature": fields["feature"],
        "version": fields["version"],
        "format": item["extension"].lstrip("."),
        "confidence": fields["confidence"],
        "created_at": now,
        "updated_at": now,
        "derived_from": [],
        "used_for": [],
        "query_intents": [],
        "access_count": 0,
        "hypergraph_node_id": "",
    }
    for field in REQUIRED_BASE_FIELDS:
        assert field in base, f"Missing: {field}"

def test_artifact_id_unique():
    import time
    id1 = generate_artifact_id()
    time.sleep(1.1)
    id2 = generate_artifact_id()
    assert id1 != id2

@pytest.mark.skipif(SKIP_API, reason="API test")
def test_llm_enrichment(tmp_path):
    from core.config_loader import KBStoreConfig
    from core.metadata_extractor import MetadataExtractor
    from domain.domain_loader import DomainLoader
    config = KBStoreConfig()
    domain = DomainLoader(config.domain_config_path)
    extractor = MetadataExtractor(config, domain)
    item = make_manifest_item()
    metadata = extractor.extract(item)
    assert metadata["artifact_id"] != ""
    assert metadata["name"] == item["new_filename"]
    assert metadata["artifact_type"] == "journey_map"
```

---

## PHASE 4 — Registry (SQLite + JSON Adapters)

### Goal
Artifact registry reads and writes correctly for both adapter types. Concurrent writes handled by SQLite WAL. Writeback updates metadata correctly.

### Step 4.1 — Registry Interface

Create `storage/registry/registry_interface.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class RegistryInterface(ABC):

    @abstractmethod
    def insert(self, metadata: Dict) -> str:
        """Insert artifact. Returns artifact_id."""
        pass

    @abstractmethod
    def update(self, artifact_id: str, fields: Dict) -> bool:
        pass

    @abstractmethod
    def get(self, artifact_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> List[Dict]:
        pass

    @abstractmethod
    def find_by_fields(self, brand: str = None, domain: str = None,
                       feature: str = None, artifact_type: str = None) -> List[Dict]:
        pass

    @abstractmethod
    def list_all(self) -> List[Dict]:
        pass

    @abstractmethod
    def writeback(self, artifact_id: str, query_intent: str, task_type: str,
                  was_useful: bool, session_id: str = "",
                  hitl_decision_id: str = "") -> bool:
        """Update artifact metadata after RAG query use."""
        pass

    @abstractmethod
    def log_conflict(self, artifact_id: str, conflict_type: str,
                     resolution: str, rationale: str) -> None:
        pass
```

### Step 4.2 — JSON Registry

Create `storage/registry/json_registry.py`:

```python
"""
JSON Registry — stores artifact registry as a JSON file.
Uses threading.Lock for same-process concurrent writes.
For multi-process concurrent writes — use SQLite registry instead.
"""
import json
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

class JSONRegistry:

    def __init__(self, registry_path: Path, filename: str, backup: bool = True):
        self.file = registry_path / f"{filename}.json"
        self.conflicts_file = registry_path / f"{filename}_conflicts.json"
        self.backup = backup
        self._lock = threading.Lock()
        registry_path.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self):
        if not self.file.exists():
            self._write({"artifacts": {}, "last_updated": "", "total": 0})
        if not self.conflicts_file.exists():
            with open(self.conflicts_file, "w") as f:
                json.dump([], f)

    def _read(self) -> Dict:
        with open(self.file) as f:
            return json.load(f)

    def _write(self, data: Dict):
        if self.backup and self.file.exists():
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            shutil.copy2(self.file, self.file.parent / f"backup_{ts}_{self.file.name}")
        tmp = self.file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, default=str)
        tmp.replace(self.file)

    def insert(self, metadata: Dict) -> str:
        with self._lock:
            data = self._read()
            aid = metadata["artifact_id"]
            data["artifacts"][aid] = metadata
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            data["total"] = len(data["artifacts"])
            self._write(data)
            return aid

    def update(self, artifact_id: str, fields: Dict) -> bool:
        with self._lock:
            data = self._read()
            if artifact_id not in data["artifacts"]:
                return False
            data["artifacts"][artifact_id].update(fields)
            data["artifacts"][artifact_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            self._write(data)
            return True

    def get(self, artifact_id: str) -> Optional[Dict]:
        return self._read()["artifacts"].get(artifact_id)

    def find_by_name(self, name: str) -> List[Dict]:
        return [a for a in self._read()["artifacts"].values()
                if a.get("name", "").lower() == name.lower()]

    def find_by_fields(self, brand=None, domain=None, feature=None, artifact_type=None) -> List[Dict]:
        results = []
        for a in self._read()["artifacts"].values():
            if brand and a.get("brand") != brand: continue
            if domain and a.get("domain") != domain: continue
            if feature and a.get("feature") != feature: continue
            if artifact_type and a.get("artifact_type") != artifact_type: continue
            results.append(a)
        return results

    def list_all(self) -> List[Dict]:
        return list(self._read()["artifacts"].values())

    def writeback(self, artifact_id: str, query_intent: str, task_type: str,
                  was_useful: bool, session_id: str = "", hitl_decision_id: str = "") -> bool:
        with self._lock:
            data = self._read()
            if artifact_id not in data["artifacts"]:
                return False
            a = data["artifacts"][artifact_id]
            if task_type and task_type not in a.get("used_for", []):
                a.setdefault("used_for", []).append(task_type)
            if query_intent and query_intent not in a.get("query_intents", []):
                a.setdefault("query_intents", []).append(query_intent)
            if hitl_decision_id:
                a.setdefault("hitl_decisions_informed", []).append(hitl_decision_id)
            a["access_count"] = a.get("access_count", 0) + 1
            a["last_accessed"] = datetime.now(timezone.utc).isoformat()
            scores = a.setdefault("usefulness_scores", {})
            if task_type:
                scores.setdefault(task_type, {"total": 0, "useful": 0})
                scores[task_type]["total"] += 1
                if was_useful:
                    scores[task_type]["useful"] += 1
            a["updated_at"] = datetime.now(timezone.utc).isoformat()
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            self._write(data)
            return True

    def log_conflict(self, artifact_id: str, conflict_type: str, resolution: str, rationale: str):
        with open(self.conflicts_file) as f:
            conflicts = json.load(f)
        conflicts.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "artifact_id": artifact_id,
            "conflict_type": conflict_type,
            "resolution": resolution,
            "rationale": rationale
        })
        with open(self.conflicts_file, "w") as f:
            json.dump(conflicts, f, indent=2)
```

### Step 4.3 — SQLite Registry

Create `storage/registry/sqlite_registry.py`:

```python
"""
SQLite Registry — handles concurrent parallel agent writes via WAL mode.
Use this when multiple agents run in parallel writing to the same KB.
"""
import sqlite3
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

class SQLiteRegistry:

    def __init__(self, registry_path: Path, filename: str, backup: bool = True):
        self.db_file = registry_path / f"{filename}.db"
        self.backup = backup
        registry_path.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    artifact_type TEXT,
                    brand TEXT,
                    domain TEXT,
                    feature TEXT,
                    confidence TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    metadata_json TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON artifacts(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_brand_domain ON artifacts(brand, domain)")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conflict_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT, artifact_id TEXT,
                    conflict_type TEXT, resolution TEXT, rationale TEXT
                )
            """)
            conn.commit()

    def _conn(self):
        conn = sqlite3.connect(self.db_file, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _backup_db(self):
        if self.backup and self.db_file.exists():
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            shutil.copy2(self.db_file, self.db_file.parent / f"backup_{ts}_{self.db_file.name}")

    def insert(self, metadata: Dict) -> str:
        self._backup_db()
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO artifacts
                (artifact_id, name, artifact_type, brand, domain, feature,
                 confidence, created_at, updated_at, access_count, metadata_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                metadata["artifact_id"], metadata.get("name", ""),
                metadata.get("artifact_type", ""), metadata.get("brand", ""),
                metadata.get("domain", ""), metadata.get("feature", ""),
                metadata.get("confidence", ""), metadata.get("created_at", ""),
                metadata.get("updated_at", ""), metadata.get("access_count", 0),
                json.dumps(metadata)
            ))
            conn.commit()
        return metadata["artifact_id"]

    def update(self, artifact_id: str, fields: Dict) -> bool:
        existing = self.get(artifact_id)
        if not existing:
            return False
        existing.update(fields)
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        return bool(self.insert(existing))

    def get(self, artifact_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT metadata_json FROM artifacts WHERE artifact_id=?",
                               (artifact_id,)).fetchone()
        return json.loads(row["metadata_json"]) if row else None

    def find_by_name(self, name: str) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT metadata_json FROM artifacts WHERE LOWER(name)=LOWER(?)",
                                (name,)).fetchall()
        return [json.loads(r["metadata_json"]) for r in rows]

    def find_by_fields(self, brand=None, domain=None, feature=None, artifact_type=None) -> List[Dict]:
        q = "SELECT metadata_json FROM artifacts WHERE 1=1"
        params = []
        if brand: q += " AND brand=?"; params.append(brand)
        if domain: q += " AND domain=?"; params.append(domain)
        if feature: q += " AND feature=?"; params.append(feature)
        if artifact_type: q += " AND artifact_type=?"; params.append(artifact_type)
        with self._conn() as conn:
            rows = conn.execute(q, params).fetchall()
        return [json.loads(r["metadata_json"]) for r in rows]

    def list_all(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT metadata_json FROM artifacts").fetchall()
        return [json.loads(r["metadata_json"]) for r in rows]

    def writeback(self, artifact_id: str, query_intent: str, task_type: str,
                  was_useful: bool, session_id: str = "", hitl_decision_id: str = "") -> bool:
        existing = self.get(artifact_id)
        if not existing: return False
        if task_type and task_type not in existing.get("used_for", []):
            existing.setdefault("used_for", []).append(task_type)
        if query_intent and query_intent not in existing.get("query_intents", []):
            existing.setdefault("query_intents", []).append(query_intent)
        if hitl_decision_id:
            existing.setdefault("hitl_decisions_informed", []).append(hitl_decision_id)
        existing["access_count"] = existing.get("access_count", 0) + 1
        existing["last_accessed"] = datetime.now(timezone.utc).isoformat()
        if task_type:
            scores = existing.setdefault("usefulness_scores", {})
            scores.setdefault(task_type, {"total": 0, "useful": 0})
            scores[task_type]["total"] += 1
            if was_useful: scores[task_type]["useful"] += 1
        return bool(self.update(artifact_id, existing))

    def log_conflict(self, artifact_id: str, conflict_type: str, resolution: str, rationale: str):
        with self._conn() as conn:
            conn.execute("INSERT INTO conflict_log (timestamp,artifact_id,conflict_type,resolution,rationale) VALUES(?,?,?,?,?)",
                         (datetime.now(timezone.utc).isoformat(), artifact_id, conflict_type, resolution, rationale))
            conn.commit()
```

### Step 4.4 — Registry Factory

Create `storage/registry/registry_factory.py`:

```python
from pathlib import Path

def get_registry(config):
    """Returns SQLite or JSON registry based on config. Agent code never imports adapters directly."""
    if config.registry_type == "sqlite":
        from storage.registry.sqlite_registry import SQLiteRegistry
        return SQLiteRegistry(config.registry_path, config.registry_filename, config.registry_backup)
    else:
        from storage.registry.json_registry import JSONRegistry
        return JSONRegistry(config.registry_path, config.registry_filename, config.registry_backup)
```

### Phase 4 Validation Test

Create `tests/test_phase4_registry.py`:

```python
"""
Phase 4 Validation Tests
Run: pytest tests/test_phase4_registry.py -v
"""
import pytest
from pathlib import Path
from utils.artifact_id import generate_artifact_id

def make_meta(suffix="", brand="ST", confidence="HIGH", version="1"):
    return {
        "artifact_id": generate_artifact_id(),
        "name": f"ST_SO_Activation_journey_map_v{version}{suffix}.json",
        "artifact_type": "journey_map",
        "producer_agent": "brd_agent",
        "producer_run_id": "run-001",
        "brand": brand, "domain": "service_ordering", "feature": "Activation",
        "version": version, "format": "json", "confidence": confidence,
        "client": "Value", "created_at": "2026-05-13T00:00:00+00:00",
        "updated_at": "2026-05-13T00:00:00+00:00",
        "derived_from": [], "used_for": [], "query_intents": [],
        "access_count": 0, "last_accessed": None, "usefulness_scores": {},
        "hypergraph_node_id": ""
    }

@pytest.mark.parametrize("rtype", ["json", "sqlite"])
def test_insert_and_get(tmp_path, rtype):
    from storage.registry.json_registry import JSONRegistry
    from storage.registry.sqlite_registry import SQLiteRegistry
    reg = JSONRegistry(tmp_path, "t", backup=False) if rtype == "json" else SQLiteRegistry(tmp_path, "t", backup=False)
    m = make_meta()
    aid = reg.insert(m)
    result = reg.get(aid)
    assert result is not None
    assert result["artifact_id"] == aid

@pytest.mark.parametrize("rtype", ["json", "sqlite"])
def test_find_by_fields(tmp_path, rtype):
    from storage.registry.json_registry import JSONRegistry
    from storage.registry.sqlite_registry import SQLiteRegistry
    reg = JSONRegistry(tmp_path, "t", backup=False) if rtype == "json" else SQLiteRegistry(tmp_path, "t", backup=False)
    reg.insert(make_meta("_1", brand="ST"))
    reg.insert(make_meta("_2", brand="TW"))
    assert len(reg.find_by_fields(brand="ST")) == 1

@pytest.mark.parametrize("rtype", ["json", "sqlite"])
def test_writeback(tmp_path, rtype):
    from storage.registry.json_registry import JSONRegistry
    from storage.registry.sqlite_registry import SQLiteRegistry
    reg = JSONRegistry(tmp_path, "t", backup=False) if rtype == "json" else SQLiteRegistry(tmp_path, "t", backup=False)
    m = make_meta()
    aid = reg.insert(m)
    reg.writeback(aid, "defect_triage", "defect_triage", True)
    updated = reg.get(aid)
    assert updated["access_count"] == 1
    assert "defect_triage" in updated["used_for"]

def test_factory_returns_json(tmp_path):
    from storage.registry.registry_factory import get_registry
    class MockConfig:
        registry_type = "json"
        registry_path = tmp_path
        registry_filename = "test"
        registry_backup = False
    from storage.registry.json_registry import JSONRegistry
    assert isinstance(get_registry(MockConfig()), JSONRegistry)
```

---

## PHASE 5 — Hypergraph (JSON + SQLite Adapters)

### Goal
Hypergraph stores nodes, hyperedges, alias index, temp nodes. Both JSON and SQLite adapters work. Notifications file writes correctly.

### Step 5.1 — Hypergraph Interface

Create `hypergraph/hypergraph_interface.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

class HypergraphInterface(ABC):

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def find_nodes_by_fields(self, brand: str = None, domain: str = None,
                              feature: str = None) -> List[Dict]:
        pass

    @abstractmethod
    def find_nodes_by_alias(self, alias_term: str) -> List[Dict]:
        """Find nodes and edges matching an alias term. Used by RAG intent routing."""
        pass

    @abstractmethod
    def create_node(self, node_data: Dict) -> str:
        """Create new permanent node. Returns node_id."""
        pass

    @abstractmethod
    def create_temp_node(self, temp_data: Dict) -> str:
        """Create TEMP node pending human review. Returns temp_node_id."""
        pass

    @abstractmethod
    def append_artifact_to_node(self, node_id: str, artifact_id: str) -> bool:
        """Add artifact UUID to existing node."""
        pass

    @abstractmethod
    def create_hyperedge(self, edge_data: Dict) -> str:
        """Create hyperedge connecting multiple nodes. Returns edge_id."""
        pass

    @abstractmethod
    def get_artifact_ids_for_query(self, intent: str, brand: str = None) -> List[str]:
        """
        Main RAG navigation method.
        Given intent keywords and optional brand filter —
        return list of artifact UUIDs to search in vector store.
        """
        pass

    @abstractmethod
    def update_aliases(self, node_id: str, new_aliases: List[str]) -> bool:
        pass

    @abstractmethod
    def list_all_nodes(self) -> List[Dict]:
        pass
```

### Step 5.2 — JSON Hypergraph

Create `hypergraph/json_hypergraph.py`:

```python
"""
JSON Hypergraph — stores navigation graph as a JSON file.
Human-readable, git-versionable, zero dependency.
Use for POC. Upgrade to SQLite for production concurrent writes.
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

EMPTY_GRAPH = {
    "hypergraph_version": "1.0",
    "last_updated": "",
    "nodes": {},
    "hyperedges": {},
    "alias_index": {},
    "temp_nodes": {}
}

class JSONHypergraph:

    def __init__(self, graph_path: Path, filename: str):
        self.file = graph_path / f"{filename}.json"
        self._lock = threading.Lock()
        graph_path.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self):
        if not self.file.exists():
            self._write(EMPTY_GRAPH.copy())

    def _read(self) -> Dict:
        with open(self.file) as f:
            return json.load(f)

    def _write(self, data: Dict):
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        tmp = self.file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, default=str)
        tmp.replace(self.file)

    def get_node(self, node_id: str) -> Optional[Dict]:
        data = self._read()
        return data["nodes"].get(node_id) or data["temp_nodes"].get(node_id)

    def find_nodes_by_fields(self, brand=None, domain=None, feature=None) -> List[Dict]:
        data = self._read()
        results = []
        for node in data["nodes"].values():
            if brand and node.get("brand") != brand: continue
            if domain and node.get("domain") != domain: continue
            if feature and node.get("feature") != feature: continue
            results.append(node)
        return results

    def find_nodes_by_alias(self, alias_term: str) -> List[Dict]:
        data = self._read()
        term_lower = alias_term.lower()

        # Direct alias index lookup
        matched_node_ids = set()
        matched_edge_ids = set()
        for alias, mapping in data["alias_index"].items():
            if term_lower in alias.lower() or alias.lower() in term_lower:
                matched_node_ids.update(mapping.get("nodes", []))
                matched_edge_ids.update(mapping.get("edges", []))

        # Also collect nodes from matched edges
        for edge_id in matched_edge_ids:
            edge = data["hyperedges"].get(edge_id, {})
            matched_node_ids.update(edge.get("connects_nodes", []))

        return [data["nodes"][nid] for nid in matched_node_ids if nid in data["nodes"]]

    def create_node(self, node_data: Dict) -> str:
        with self._lock:
            data = self._read()
            node_id = node_data["node_id"]
            data["nodes"][node_id] = node_data
            # Add aliases to index
            for alias in node_data.get("aliases", []):
                self._add_alias(data, alias.lower(), node_id=node_id)
            self._write(data)
            return node_id

    def create_temp_node(self, temp_data: Dict) -> str:
        with self._lock:
            data = self._read()
            node_id = temp_data["node_id"]
            data["temp_nodes"][node_id] = temp_data
            self._write(data)
            return node_id

    def append_artifact_to_node(self, node_id: str, artifact_id: str) -> bool:
        with self._lock:
            data = self._read()
            if node_id not in data["nodes"]:
                return False
            if artifact_id not in data["nodes"][node_id].get("artifact_ids", []):
                data["nodes"][node_id].setdefault("artifact_ids", []).append(artifact_id)
                data["nodes"][node_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
                self._write(data)
            return True

    def create_hyperedge(self, edge_data: Dict) -> str:
        with self._lock:
            data = self._read()
            edge_id = edge_data["edge_id"]
            data["hyperedges"][edge_id] = edge_data
            for alias in edge_data.get("aliases", []):
                self._add_alias(data, alias.lower(), edge_id=edge_id)
            self._write(data)
            return edge_id

    def get_artifact_ids_for_query(self, intent: str, brand: str = None) -> List[str]:
        nodes = self.find_nodes_by_alias(intent)
        if brand:
            nodes = [n for n in nodes if not n.get("brand") or n.get("brand") == brand]
        artifact_ids = []
        for node in nodes:
            artifact_ids.extend(node.get("artifact_ids", []))
        return list(set(artifact_ids))

    def update_aliases(self, node_id: str, new_aliases: List[str]) -> bool:
        with self._lock:
            data = self._read()
            if node_id not in data["nodes"]:
                return False
            existing = set(data["nodes"][node_id].get("aliases", []))
            for alias in new_aliases:
                if alias not in existing:
                    data["nodes"][node_id].setdefault("aliases", []).append(alias)
                    self._add_alias(data, alias.lower(), node_id=node_id)
            self._write(data)
            return True

    def list_all_nodes(self) -> List[Dict]:
        return list(self._read()["nodes"].values())

    def _add_alias(self, data: Dict, alias: str, node_id: str = None, edge_id: str = None):
        entry = data["alias_index"].setdefault(alias, {"nodes": [], "edges": []})
        if node_id and node_id not in entry["nodes"]:
            entry["nodes"].append(node_id)
        if edge_id and edge_id not in entry["edges"]:
            entry["edges"].append(edge_id)
```

### Step 5.3 — SQLite Hypergraph

Create `hypergraph/sqlite_hypergraph.py`:

```python
"""
SQLite Hypergraph — handles concurrent writes for production.
Same interface as JSON hypergraph. Swap via config.
"""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

class SQLiteHypergraph:

    def __init__(self, graph_path: Path, filename: str):
        self.db_file = graph_path / f"{filename}.db"
        graph_path.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    brand TEXT, domain TEXT, feature TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    is_temp INTEGER DEFAULT 0,
                    node_json TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hyperedges (
                    edge_id TEXT PRIMARY KEY,
                    edge_type TEXT,
                    edge_json TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alias_index (
                    alias_term TEXT,
                    target_type TEXT,
                    target_id TEXT,
                    PRIMARY KEY (alias_term, target_type, target_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alias ON alias_index(alias_term)")
            conn.commit()

    def _conn(self):
        conn = sqlite3.connect(self.db_file, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def get_node(self, node_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT node_json FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        return json.loads(row["node_json"]) if row else None

    def find_nodes_by_fields(self, brand=None, domain=None, feature=None) -> List[Dict]:
        q = "SELECT node_json FROM nodes WHERE is_temp=0"
        params = []
        if brand: q += " AND brand=?"; params.append(brand)
        if domain: q += " AND domain=?"; params.append(domain)
        if feature: q += " AND feature=?"; params.append(feature)
        with self._conn() as conn:
            rows = conn.execute(q, params).fetchall()
        return [json.loads(r["node_json"]) for r in rows]

    def find_nodes_by_alias(self, alias_term: str) -> List[Dict]:
        term_lower = f"%{alias_term.lower()}%"
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT target_id, target_type FROM alias_index WHERE LOWER(alias_term) LIKE ?",
                (term_lower,)
            ).fetchall()
        node_ids = set()
        for row in rows:
            if row["target_type"] == "node":
                node_ids.add(row["target_id"])
            elif row["target_type"] == "edge":
                edge = self._get_edge(row["target_id"])
                if edge:
                    node_ids.update(edge.get("connects_nodes", []))

        results = []
        for nid in node_ids:
            node = self.get_node(nid)
            if node:
                results.append(node)
        return results

    def _get_edge(self, edge_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT edge_json FROM hyperedges WHERE edge_id=?", (edge_id,)).fetchone()
        return json.loads(row["edge_json"]) if row else None

    def create_node(self, node_data: Dict) -> str:
        nid = node_data["node_id"]
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO nodes (node_id, brand, domain, feature, status, is_temp, node_json)
                VALUES (?,?,?,?,?,?,?)
            """, (nid, node_data.get("brand", ""), node_data.get("domain", ""),
                  node_data.get("feature", ""), node_data.get("status", "ACTIVE"),
                  int(node_data.get("is_temp", False)), json.dumps(node_data)))
            for alias in node_data.get("aliases", []):
                conn.execute("INSERT OR IGNORE INTO alias_index VALUES (?,?,?)",
                             (alias.lower(), "node", nid))
            conn.commit()
        return nid

    def create_temp_node(self, temp_data: Dict) -> str:
        temp_data["is_temp"] = True
        temp_data["status"] = "TEMP"
        return self.create_node(temp_data)

    def append_artifact_to_node(self, node_id: str, artifact_id: str) -> bool:
        node = self.get_node(node_id)
        if not node: return False
        if artifact_id not in node.get("artifact_ids", []):
            node.setdefault("artifact_ids", []).append(artifact_id)
            node["last_updated"] = datetime.now(timezone.utc).isoformat()
            with self._conn() as conn:
                conn.execute("UPDATE nodes SET node_json=? WHERE node_id=?", (json.dumps(node), node_id))
                conn.commit()
        return True

    def create_hyperedge(self, edge_data: Dict) -> str:
        eid = edge_data["edge_id"]
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO hyperedges VALUES (?,?,?)",
                         (eid, edge_data.get("edge_type", ""), json.dumps(edge_data)))
            for alias in edge_data.get("aliases", []):
                conn.execute("INSERT OR IGNORE INTO alias_index VALUES (?,?,?)",
                             (alias.lower(), "edge", eid))
            conn.commit()
        return eid

    def get_artifact_ids_for_query(self, intent: str, brand: str = None) -> List[str]:
        nodes = self.find_nodes_by_alias(intent)
        if brand:
            nodes = [n for n in nodes if not n.get("brand") or n.get("brand") == brand]
        ids = []
        for node in nodes:
            ids.extend(node.get("artifact_ids", []))
        return list(set(ids))

    def update_aliases(self, node_id: str, new_aliases: List[str]) -> bool:
        node = self.get_node(node_id)
        if not node: return False
        existing = set(node.get("aliases", []))
        with self._conn() as conn:
            for alias in new_aliases:
                if alias not in existing:
                    node.setdefault("aliases", []).append(alias)
                    conn.execute("INSERT OR IGNORE INTO alias_index VALUES (?,?,?)",
                                 (alias.lower(), "node", node_id))
            conn.execute("UPDATE nodes SET node_json=? WHERE node_id=?", (json.dumps(node), node_id))
            conn.commit()
        return True

    def list_all_nodes(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT node_json FROM nodes WHERE is_temp=0").fetchall()
        return [json.loads(r["node_json"]) for r in rows]
```

### Step 5.4 — Hypergraph Factory

Create `hypergraph/hypergraph_factory.py`:

```python
from pathlib import Path

def get_hypergraph(config):
    """Returns JSON or SQLite hypergraph based on config."""
    if config.hypergraph_type == "sqlite":
        from hypergraph.sqlite_hypergraph import SQLiteHypergraph
        return SQLiteHypergraph(config.hypergraph_path, config.hypergraph_filename)
    else:
        from hypergraph.json_hypergraph import JSONHypergraph
        return JSONHypergraph(config.hypergraph_path, config.hypergraph_filename)
```

### Phase 5 Validation Test

Create `tests/test_phase5_hypergraph.py`:

```python
"""
Phase 5 Validation Tests
Run: pytest tests/test_phase5_hypergraph.py -v
"""
import pytest
from pathlib import Path

def make_node(node_id, brand="ST", domain="service_ordering", feature="Activation"):
    return {
        "node_id": node_id,
        "label": f"{brand} {domain} {feature}",
        "brand": brand, "domain": domain, "feature": feature,
        "artifact_ids": [],
        "aliases": ["activation flow", "new activation"],
        "confidence": "HIGH",
        "status": "ACTIVE",
        "is_temp": False,
        "created_at": "2026-05-13T00:00:00Z",
        "human_reviewed": False
    }

@pytest.mark.parametrize("htype", ["json", "sqlite"])
def test_create_and_get_node(tmp_path, htype):
    from hypergraph.json_hypergraph import JSONHypergraph
    from hypergraph.sqlite_hypergraph import SQLiteHypergraph
    hg = JSONHypergraph(tmp_path, "hg") if htype == "json" else SQLiteHypergraph(tmp_path, "hg")
    node = make_node("node_ST_SO_Activation")
    nid = hg.create_node(node)
    result = hg.get_node(nid)
    assert result is not None
    assert result["node_id"] == nid

@pytest.mark.parametrize("htype", ["json", "sqlite"])
def test_append_artifact(tmp_path, htype):
    from hypergraph.json_hypergraph import JSONHypergraph
    from hypergraph.sqlite_hypergraph import SQLiteHypergraph
    hg = JSONHypergraph(tmp_path, "hg") if htype == "json" else SQLiteHypergraph(tmp_path, "hg")
    hg.create_node(make_node("node_ST_SO_Activation"))
    hg.append_artifact_to_node("node_ST_SO_Activation", "uuid_abc123")
    node = hg.get_node("node_ST_SO_Activation")
    assert "uuid_abc123" in node["artifact_ids"]

@pytest.mark.parametrize("htype", ["json", "sqlite"])
def test_alias_lookup(tmp_path, htype):
    from hypergraph.json_hypergraph import JSONHypergraph
    from hypergraph.sqlite_hypergraph import SQLiteHypergraph
    hg = JSONHypergraph(tmp_path, "hg") if htype == "json" else SQLiteHypergraph(tmp_path, "hg")
    hg.create_node(make_node("node_ST_SO_Activation"))
    results = hg.find_nodes_by_alias("activation")
    assert len(results) > 0

@pytest.mark.parametrize("htype", ["json", "sqlite"])
def test_get_artifact_ids_for_query(tmp_path, htype):
    from hypergraph.json_hypergraph import JSONHypergraph
    from hypergraph.sqlite_hypergraph import SQLiteHypergraph
    hg = JSONHypergraph(tmp_path, "hg") if htype == "json" else SQLiteHypergraph(tmp_path, "hg")
    node = make_node("node_ST_SO_Activation")
    hg.create_node(node)
    hg.append_artifact_to_node("node_ST_SO_Activation", "uuid_123")
    ids = hg.get_artifact_ids_for_query("activation", brand="ST")
    assert "uuid_123" in ids

@pytest.mark.parametrize("htype", ["json", "sqlite"])
def test_create_hyperedge(tmp_path, htype):
    from hypergraph.json_hypergraph import JSONHypergraph
    from hypergraph.sqlite_hypergraph import SQLiteHypergraph
    hg = JSONHypergraph(tmp_path, "hg") if htype == "json" else SQLiteHypergraph(tmp_path, "hg")
    hg.create_node(make_node("node_ST_SO_Activation", brand="ST"))
    hg.create_node(make_node("node_TW_SO_Activation", brand="TW"))
    edge = {
        "edge_id": "edge_SO_crossbrand",
        "label": "Service Ordering Cross Brand",
        "edge_type": "SAME_CONCEPT_DIFFERENT_BRAND",
        "connects_nodes": ["node_ST_SO_Activation", "node_TW_SO_Activation"],
        "aliases": ["order management", "service ordering all brands"],
        "similarity_score": 0.87,
        "human_reviewed": False
    }
    eid = hg.create_hyperedge(edge)
    assert eid == "edge_SO_crossbrand"
```

---

## PHASE 6 — Placement Agent

### Goal
Placement agent makes intelligent LLM-driven decisions about where each artifact goes in the hypergraph. Five decisions implemented. Notifications written async. Never blocks pipeline.

### Step 6.1 — Notification Writer

Create `hypergraph/notification_writer.py`:

```python
"""
Writes async notifications for human review.
Never blocks the pipeline. Human reviews periodically.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from utils.artifact_id import generate_artifact_id

class NotificationWriter:

    def __init__(self, notifications_file: Path):
        self.file = notifications_file
        self.file.parent.mkdir(parents=True, exist_ok=True)
        if not self.file.exists():
            self._write([])

    def write(self, notification_type: str, artifact_id: str,
              artifact_name: str, context: str, candidates: list = None,
              recommended_action: str = "", priority: str = "MEDIUM"):
        notifications = self._read()
        notifications.append({
            "notification_id": f"notif_{generate_artifact_id()}",
            "type": notification_type,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "PENDING",
            "artifact_id": artifact_id,
            "artifact_name": artifact_name,
            "placement_context": context,
            "candidate_nodes": candidates or [],
            "recommended_action": recommended_action,
            "human_decision": "",
            "resolved_at": ""
        })
        self._write(notifications)

    def _read(self) -> list:
        with open(self.file) as f:
            return json.load(f)

    def _write(self, data: list):
        with open(self.file, "w") as f:
            json.dump(data, f, indent=2, default=str)
```

### Step 6.2 — Placement Agent

Create `hypergraph/placement_agent.py`:

```python
"""
Placement Agent — intelligent LLM-driven hypergraph placement.

Five placement decisions:
  1. PLACE_IN_EXISTING   — append UUID to existing node (HIGH confidence)
  2. CREATE_NEW_NODE     — create new permanent node (HIGH confidence)
  3. CREATE_HYPEREDGE    — connect multiple nodes, place in best (MEDIUM confidence)
  4. TEMP_NODE           — cannot decide, create TEMP + notification (LOW confidence)
  5. MERGE_PROPOSAL      — same concept as existing, propose merge + notification

Uses LLM with full artifact context + domain context + existing nodes for reasoning.
Never blocks the pipeline — notifications are async.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from rich.console import Console
import anthropic

from hypergraph.notification_writer import NotificationWriter
from utils.artifact_id import generate_artifact_id

console = Console()

PLACEMENT_SYSTEM = """You are an intelligent knowledge graph placement agent for an enterprise SDLC knowledge base.

Your job is to decide where a new artifact belongs in the hypergraph — a navigation structure that groups artifacts by business feature, domain, and brand.

You have full context about:
- The artifact being placed (content, type, metadata)
- The domain (business context, brands, entities)
- Existing hypergraph nodes (what groups already exist)

Make ONE of these decisions:

1. PLACE_IN_EXISTING — artifact clearly belongs to an existing node
2. CREATE_NEW_NODE — artifact covers a new feature not yet in the graph
3. CREATE_HYPEREDGE — artifact spans multiple existing nodes, create a connection
4. TEMP_NODE — cannot determine placement confidently
5. MERGE_PROPOSAL — artifact appears to cover same concept as existing node from different angle

Be intelligent. Do NOT just pattern match on field names.
Consider: what is this artifact actually about? What business concept does it cover?
Which existing node (if any) covers the same concept?

Respond ONLY in valid JSON. No preamble. No markdown."""

PLACEMENT_PROMPT = """Place this artifact in the knowledge hypergraph.

DOMAIN CONTEXT:
{domain_context}

ARTIFACT BEING PLACED:
Name: {artifact_name}
Type: {artifact_type}
Brand: {brand}
Domain: {domain}
Feature: {feature}
Description: {description}
Entity mentions: {entities}
Producer: {producer}
Content summary: {content_summary}

EXISTING HYPERGRAPH NODES (top candidates by field similarity):
{existing_nodes}

DECISION OPTIONS:
1. PLACE_IN_EXISTING — append to an existing node
2. CREATE_NEW_NODE — create new permanent node
3. CREATE_HYPEREDGE — artifact connects multiple concepts
4. TEMP_NODE — cannot determine placement
5. MERGE_PROPOSAL — same concept as existing node

Respond with ONLY this JSON:
{{
  "decision": "PLACE_IN_EXISTING|CREATE_NEW_NODE|CREATE_HYPEREDGE|TEMP_NODE|MERGE_PROPOSAL",
  "confidence": "HIGH|MEDIUM|LOW",
  "reasoning": "clear explanation of why this decision",

  "target_node_id": "node_id if PLACE_IN_EXISTING or MERGE_PROPOSAL",

  "new_node": {{
    "node_id": "node_{{brand}}_{{domain_short}}_{{feature}} if CREATE_NEW_NODE",
    "label": "human readable label",
    "brand": "brand code",
    "domain": "domain",
    "feature": "feature name",
    "aliases": ["natural language terms that map to this node"]
  }},

  "hyperedge": {{
    "edge_id": "edge_{{descriptive_name}} if CREATE_HYPEREDGE",
    "label": "human readable edge label",
    "edge_type": "SAME_DOMAIN|SAME_CONCEPT_DIFFERENT_BRAND|SHARED_FLOW|CROSS_FEATURE",
    "connects_nodes": ["list of node_ids this connects"],
    "aliases": ["terms that map to this edge"],
    "differences": ["known differences between connected nodes"],
    "primary_node": "which node to primarily place artifact in"
  }},

  "new_aliases": ["any new alias terms to add to existing node if PLACE_IN_EXISTING"],
  "merge_candidate_node": "node_id to potentially merge with if MERGE_PROPOSAL",
  "notification_priority": "LOW|MEDIUM|HIGH"
}}"""


class PlacementAgent:

    def __init__(self, config, domain_loader, hypergraph, notification_writer: NotificationWriter):
        self.config = config
        self.domain_loader = domain_loader
        self.hypergraph = hypergraph
        self.notifications = notification_writer
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def place(self, metadata: Dict) -> Tuple[str, Dict]:
        """
        Place artifact in hypergraph.
        Returns (decision_type, updated_metadata).
        """
        # Find candidate nodes by field matching first
        candidates = self._find_candidates(metadata)

        # Call LLM for intelligent decision
        decision = self._decide_via_llm(metadata, candidates)
        decision_type = decision.get("decision", "TEMP_NODE")

        console.print(f"[dim]  🧠 Placement: {decision_type} ({decision.get('confidence', '?')}) — {decision.get('reasoning', '')[:60]}[/dim]")

        updated_metadata = self._execute_decision(decision, metadata)
        return decision_type, updated_metadata

    def _find_candidates(self, metadata: Dict) -> List[Dict]:
        """Find existing nodes that might match this artifact."""
        brand = metadata.get("brand", "")
        domain = metadata.get("domain", "")
        feature = metadata.get("feature", "")

        candidates = self.hypergraph.find_nodes_by_fields(
            brand=brand or None,
            domain=domain or None
        )

        # Also search by alias using feature name
        if feature:
            alias_matches = self.hypergraph.find_nodes_by_alias(feature)
            for node in alias_matches:
                if not any(n["node_id"] == node["node_id"] for n in candidates):
                    candidates.append(node)

        return candidates[:self.config.placement_max_candidates]

    def _decide_via_llm(self, metadata: Dict, candidates: List[Dict]) -> Dict:
        """Use LLM to make intelligent placement decision."""
        try:
            content = metadata.get("content", {})
            content_summary = ""
            if isinstance(content, dict):
                content_summary = json.dumps(content, default=str)[:800]
            else:
                content_summary = str(content)[:800]

            existing_nodes_str = json.dumps([
                {
                    "node_id": n["node_id"],
                    "label": n.get("label", ""),
                    "brand": n.get("brand", ""),
                    "domain": n.get("domain", ""),
                    "feature": n.get("feature", ""),
                    "aliases": n.get("aliases", [])[:5],
                    "artifact_count": len(n.get("artifact_ids", []))
                }
                for n in candidates
            ], indent=2)

            prompt = PLACEMENT_PROMPT.format(
                domain_context=self.domain_loader.get_ontology_prompt()[:600],
                artifact_name=metadata.get("name", ""),
                artifact_type=metadata.get("artifact_type", ""),
                brand=metadata.get("brand", ""),
                domain=metadata.get("domain", ""),
                feature=metadata.get("feature", ""),
                description=metadata.get("description", ""),
                entities=", ".join(metadata.get("entity_tags", [])[:10]),
                producer=metadata.get("producer_agent", ""),
                content_summary=content_summary,
                existing_nodes=existing_nodes_str if candidates else "No existing nodes found."
            )

            resp = self.client.messages.create(
                model=self.config.llm_placement_model,
                max_tokens=2048,
                system=PLACEMENT_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())

        except Exception as e:
            console.print(f"[dim yellow]⚠️  Placement LLM failed: {e}. Defaulting to TEMP_NODE.[/dim yellow]")
            return {
                "decision": "TEMP_NODE",
                "confidence": "LOW",
                "reasoning": f"LLM placement failed: {e}",
                "notification_priority": "MEDIUM"
            }

    def _execute_decision(self, decision: Dict, metadata: Dict) -> Dict:
        """Execute the placement decision and update metadata."""
        artifact_id = metadata["artifact_id"]
        artifact_name = metadata["name"]
        decision_type = decision.get("decision", "TEMP_NODE")

        if decision_type == "PLACE_IN_EXISTING":
            target_id = decision.get("target_node_id", "")
            if target_id and self.hypergraph.get_node(target_id):
                self.hypergraph.append_artifact_to_node(target_id, artifact_id)
                new_aliases = decision.get("new_aliases", [])
                if new_aliases:
                    self.hypergraph.update_aliases(target_id, new_aliases)
                metadata["hypergraph_node_id"] = target_id
                console.print(f"[dim green]  ✓ Placed in: {target_id}[/dim green]")
            else:
                # Target not found — fall through to TEMP
                return self._create_temp(decision, metadata)

        elif decision_type == "CREATE_NEW_NODE":
            new_node_data = decision.get("new_node", {})
            if new_node_data:
                new_node_data["artifact_ids"] = [artifact_id]
                new_node_data["status"] = "ACTIVE"
                new_node_data["is_temp"] = False
                new_node_data["created_at"] = datetime.now(timezone.utc).isoformat()
                new_node_data["created_by"] = "placement_agent"
                new_node_data["human_reviewed"] = False
                node_id = self.hypergraph.create_node(new_node_data)
                metadata["hypergraph_node_id"] = node_id
                console.print(f"[dim green]  ✓ Created new node: {node_id}[/dim green]")
            else:
                return self._create_temp(decision, metadata)

        elif decision_type == "CREATE_HYPEREDGE":
            edge_data = decision.get("hyperedge", {})
            primary_node = edge_data.get("primary_node", "")
            if edge_data and primary_node:
                # Place in primary node
                if self.hypergraph.get_node(primary_node):
                    self.hypergraph.append_artifact_to_node(primary_node, artifact_id)
                    metadata["hypergraph_node_id"] = primary_node
                else:
                    # Primary node doesn't exist — create it
                    new_node = {
                        "node_id": primary_node,
                        "label": primary_node,
                        "artifact_ids": [artifact_id],
                        "aliases": [],
                        "status": "ACTIVE", "is_temp": False,
                        "created_by": "placement_agent",
                        "human_reviewed": False,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    self.hypergraph.create_node(new_node)
                    metadata["hypergraph_node_id"] = primary_node

                # Create the hyperedge
                edge_data["created_at"] = datetime.now(timezone.utc).isoformat()
                edge_data["created_by"] = "placement_agent"
                edge_data["human_reviewed"] = False
                self.hypergraph.create_hyperedge(edge_data)

                # Send notification if configured
                if self.config.raw["placement"].get("notification_on_hyperedge", True):
                    self.notifications.write(
                        notification_type="NEW_HYPEREDGE_REVIEW",
                        artifact_id=artifact_id,
                        artifact_name=artifact_name,
                        context=decision.get("reasoning", ""),
                        recommended_action=f"Review new hyperedge: {edge_data.get('edge_id', '')}",
                        priority=decision.get("notification_priority", "MEDIUM")
                    )
            else:
                return self._create_temp(decision, metadata)

        elif decision_type == "MERGE_PROPOSAL":
            # Place in both candidate nodes temporarily
            target_id = decision.get("target_node_id", "")
            merge_candidate = decision.get("merge_candidate_node", "")
            if target_id and self.hypergraph.get_node(target_id):
                self.hypergraph.append_artifact_to_node(target_id, artifact_id)
                metadata["hypergraph_node_id"] = target_id
            if merge_candidate and merge_candidate != target_id and self.hypergraph.get_node(merge_candidate):
                self.hypergraph.append_artifact_to_node(merge_candidate, artifact_id)

            self.notifications.write(
                notification_type="MERGE_PROPOSAL",
                artifact_id=artifact_id,
                artifact_name=artifact_name,
                context=decision.get("reasoning", ""),
                candidates=[
                    {"node_id": target_id, "reason": "primary placement"},
                    {"node_id": merge_candidate, "reason": "merge candidate"}
                ],
                recommended_action="Review and confirm merge or keep separate",
                priority=decision.get("notification_priority", "MEDIUM")
            )
            console.print(f"[dim yellow]  ⚡ Merge proposal: {target_id} ↔ {merge_candidate}[/dim yellow]")

        else:  # TEMP_NODE
            return self._create_temp(decision, metadata)

        return metadata

    def _create_temp(self, decision: Dict, metadata: Dict) -> Dict:
        """Create TEMP node and send notification."""
        artifact_id = metadata["artifact_id"]
        temp_id = f"TEMP_{generate_artifact_id()}"
        temp_node = {
            "node_id": temp_id,
            "is_temp": True,
            "status": "TEMP",
            "artifact_ids": [artifact_id],
            "placement_context": decision.get("reasoning", "Could not determine placement"),
            "candidate_nodes": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.hypergraph.create_temp_node(temp_node)
        metadata["hypergraph_node_id"] = temp_id

        self.notifications.write(
            notification_type="TEMP_NODE_REVIEW",
            artifact_id=artifact_id,
            artifact_name=metadata["name"],
            context=decision.get("reasoning", ""),
            recommended_action="Review and assign to correct hypergraph node",
            priority=decision.get("notification_priority", "MEDIUM")
        )
        console.print(f"[dim yellow]  📋 TEMP node created: {temp_id}[/dim yellow]")
        return metadata
```

### Phase 6 Validation Test

Create `tests/test_phase6_placement.py`:

```python
"""
Phase 6 Validation Tests
Run: SKIP_API_TESTS=true pytest tests/test_phase6_placement.py -v
"""
import pytest, os, json
from pathlib import Path
from utils.artifact_id import generate_artifact_id

SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

def make_metadata():
    return {
        "artifact_id": generate_artifact_id(),
        "name": "ST_SO_Activation_journey_map_v1.json",
        "artifact_type": "journey_map",
        "brand": "ST", "domain": "service_ordering", "feature": "Activation",
        "confidence": "HIGH", "producer_agent": "brd_agent",
        "description": "Journey map for StraightTalk activation flow",
        "entity_tags": ["ServiceOrder", "Customer", "Activation"],
        "used_for": [], "query_intents": [], "access_count": 0,
        "hypergraph_node_id": "", "content": {}
    }

def test_notification_writer(tmp_path):
    from hypergraph.notification_writer import NotificationWriter
    nw = NotificationWriter(tmp_path / "notifications.json")
    nw.write("TEMP_NODE_REVIEW", "abc123", "test.json", "Could not decide", priority="MEDIUM")
    with open(tmp_path / "notifications.json") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["type"] == "TEMP_NODE_REVIEW"
    assert data[0]["status"] == "PENDING"

def test_notifications_non_blocking(tmp_path):
    from hypergraph.notification_writer import NotificationWriter
    nw = NotificationWriter(tmp_path / "notifications.json")
    # Should not raise even if called many times
    for i in range(5):
        nw.write("TEMP_NODE_REVIEW", f"id_{i}", f"artifact_{i}.json", "test")
    with open(tmp_path / "notifications.json") as f:
        data = json.load(f)
    assert len(data) == 5

@pytest.mark.skipif(SKIP_API, reason="API test")
def test_placement_agent_places_in_existing(tmp_path):
    from core.config_loader import KBStoreConfig
    from domain.domain_loader import DomainLoader
    from hypergraph.json_hypergraph import JSONHypergraph
    from hypergraph.notification_writer import NotificationWriter
    from hypergraph.placement_agent import PlacementAgent

    config = KBStoreConfig()
    domain = DomainLoader(config.domain_config_path)
    hg = JSONHypergraph(tmp_path / "graph", "hg")
    nw = NotificationWriter(tmp_path / "notifications.json")

    # Pre-create node
    hg.create_node({
        "node_id": "node_ST_SO_Activation",
        "label": "StraightTalk Service Ordering Activation",
        "brand": "ST", "domain": "service_ordering", "feature": "Activation",
        "artifact_ids": [], "aliases": ["activation flow", "new activation"],
        "confidence": "HIGH", "status": "ACTIVE", "is_temp": False,
        "created_at": "2026-05-13", "human_reviewed": False
    })

    agent = PlacementAgent(config, domain, hg, nw)
    metadata = make_metadata()
    decision_type, updated = agent.place(metadata)

    assert decision_type in ["PLACE_IN_EXISTING", "CREATE_NEW_NODE", "CREATE_HYPEREDGE", "TEMP_NODE", "MERGE_PROPOSAL"]
    assert updated["hypergraph_node_id"] != ""

@pytest.mark.skipif(SKIP_API, reason="API test")
def test_placement_creates_temp_on_unknown(tmp_path):
    from core.config_loader import KBStoreConfig
    from domain.domain_loader import DomainLoader
    from hypergraph.json_hypergraph import JSONHypergraph
    from hypergraph.notification_writer import NotificationWriter
    from hypergraph.placement_agent import PlacementAgent

    config = KBStoreConfig()
    domain = DomainLoader("./domain/configs/empty_domain.json")  # Unknown domain
    hg = JSONHypergraph(tmp_path / "graph", "hg")
    nw = NotificationWriter(tmp_path / "notifications.json")

    agent = PlacementAgent(config, domain, hg, nw)
    metadata = {
        "artifact_id": generate_artifact_id(),
        "name": "mystery_artifact.json",
        "artifact_type": "unknown",
        "brand": "", "domain": "", "feature": "",
        "confidence": "LOW", "producer_agent": "unknown",
        "description": "", "entity_tags": [],
        "used_for": [], "query_intents": [], "access_count": 0,
        "hypergraph_node_id": "", "content": {}
    }
    decision_type, updated = agent.place(metadata)
    # Should not crash — should create TEMP or some node
    assert updated["hypergraph_node_id"] != ""
```

---

## PHASE 7 — Confluence Sync + JSON Writer + Lineage + Conflict Resolver

### Goal
JSON artifacts written to correct KB folder. Confluence pages created/updated mirroring hypergraph structure. Lineage tracked. Conflict resolution works. All fail gracefully.

### Step 7.1 — JSON Writer

Create `storage/json_writer.py`:

```python
"""
JSON Writer — writes renamed artifacts to KB folder structure.
Folder structure mirrors hypergraph node structure.
"""
import json
import shutil
from pathlib import Path
from typing import Dict
from rich.console import Console

console = Console()

class JSONWriter:

    def __init__(self, config):
        self.kb_root = config.kb_root
        self.kb_root.mkdir(parents=True, exist_ok=True)

    def write(self, manifest_item: Dict) -> Path:
        rel_path = manifest_item.get("new_relative_path", "")
        full_path = self.kb_root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        content = manifest_item.get("content")
        ext = manifest_item.get("extension", ".json")

        if ext == ".json" and isinstance(content, dict):
            with open(full_path, "w") as f:
                json.dump(content, f, indent=2, default=str)
        elif ext == ".json":
            with open(full_path, "w") as f:
                f.write(str(content) if content else "")
        else:
            original = manifest_item.get("original_path")
            if original and Path(original).exists():
                shutil.copy2(original, full_path)
            else:
                with open(full_path, "w") as f:
                    f.write(str(content) if content else "")

        console.print(f"[dim green]  💾 KB ← {manifest_item['new_filename']}[/dim green]")
        return full_path

    def write_metadata_sidecar(self, metadata: Dict, artifact_path: Path) -> Path:
        sidecar = artifact_path.with_suffix(".meta.json")
        with open(sidecar, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        return sidecar
```

### Step 7.2 — Confluence Sync

Create `storage/confluence_sync.py`:

```python
"""
Confluence Sync — creates pages mirroring hypergraph structure.
Structure: Space → Brand → Domain → Feature → Artifact page
TOC auto-generated on feature pages.

GRACEFUL DEGRADATION: if unavailable for any reason — logs and continues.
Never crashes the pipeline.
"""
import json
from typing import Dict, Optional
from rich.console import Console

console = Console()

class ConfluenceSync:

    def __init__(self, config):
        self.config = config
        self.enabled = config.confluence_enabled
        self._client = None
        self._available = False
        if self.enabled:
            self._init()

    def _init(self):
        try:
            from atlassian import Confluence
        except ImportError:
            console.print("[dim yellow]⚠️  atlassian-python-api not installed. pip install atlassian-python-api. Confluence disabled.[/dim yellow]")
            self.enabled = False
            return

        creds = self.config.confluence_credentials
        if not all([creds["url"], creds["username"], creds["api_token"]]):
            console.print("[dim yellow]⚠️  Confluence credentials not set in .env. Confluence disabled.[/dim yellow]")
            self.enabled = False
            return

        try:
            self._client = Confluence(
                url=creds["url"], username=creds["username"],
                password=creds["api_token"], cloud=creds["is_cloud"]
            )
            self._client.get_space(creds["space_key"])
            self._available = True
            console.print(f"[dim green]✓ Confluence connected: {creds['url']}[/dim green]")
        except Exception as e:
            console.print(f"[dim yellow]⚠️  Confluence connection failed: {e}. Disabled for this run.[/dim yellow]")
            self.enabled = False

    def sync_artifact(self, metadata: Dict, content: Dict) -> Optional[str]:
        """Sync artifact to Confluence. Returns URL or None."""
        if not self.enabled or not self._available:
            return None
        try:
            space_key = self.config.confluence_credentials["space_key"]
            # Ensure hierarchy: Parent → Brand → Domain → Feature
            self._ensure_page(space_key, metadata.get("brand", "Unknown"), self.config.confluence_parent_page)
            self._ensure_page(space_key, metadata.get("domain", "Unknown"), metadata.get("brand", "Unknown"))
            self._ensure_page(space_key, metadata.get("feature", "Unknown"), metadata.get("domain", "Unknown"))

            title = metadata["name"]
            body = self._build_page(metadata, content)

            existing = self._client.get_page_by_title(space_key, title)
            if existing and self.config.raw["confluence"].get("update_existing", True):
                self._client.update_page(page_id=existing["id"], title=title, body=body)
                url = f"{self.config.confluence_credentials['url']}/pages/{existing['id']}"
            else:
                feature_page = self._client.get_page_by_title(space_key, metadata.get("feature", "Unknown"))
                parent_id = feature_page["id"] if feature_page else None
                new_page = self._client.create_page(space=space_key, title=title, body=body, parent_id=parent_id)
                url = f"{self.config.confluence_credentials['url']}/pages/{new_page['id']}"

            self._update_feature_toc(space_key, metadata, url)
            console.print(f"[dim green]  📄 Confluence ← {metadata['name']}[/dim green]")
            return url
        except Exception as e:
            console.print(f"[dim yellow]  ⚠️  Confluence sync failed for {metadata.get('name', '')}: {e}[/dim yellow]")
            return None

    def _ensure_page(self, space_key: str, title: str, parent_title: str) -> Optional[str]:
        try:
            existing = self._client.get_page_by_title(space_key, title)
            if existing:
                return existing["id"]
            parent = self._client.get_page_by_title(space_key, parent_title)
            parent_id = parent["id"] if parent else None
            new_page = self._client.create_page(
                space=space_key, title=title,
                body=f"<p><strong>{title}</strong></p>", parent_id=parent_id
            )
            return new_page["id"]
        except Exception:
            return None

    def _build_page(self, metadata: Dict, content: Dict) -> str:
        rows = "".join(f"<tr><th>{k.replace('_',' ').title()}</th><td>{v}</td></tr>"
                       for k, v in [
                           ("Artifact ID", metadata.get("artifact_id", "")),
                           ("Type", metadata.get("artifact_type", "")),
                           ("Producer", metadata.get("producer_agent", "")),
                           ("Brand", metadata.get("brand", "")),
                           ("Domain", metadata.get("domain", "")),
                           ("Feature", metadata.get("feature", "")),
                           ("Confidence", metadata.get("confidence", "")),
                           ("Created", metadata.get("created_at", "")[:10]),
                           ("Description", metadata.get("description", "")),
                       ])
        content_str = json.dumps(content, indent=2, default=str)[:5000]
        return f"""<table><tbody>{rows}</tbody></table>
<h3>Content</h3>
<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">json</ac:parameter>
<ac:plain-text-body><![CDATA[{content_str}]]></ac:plain-text-body>
</ac:structured-macro>"""

    def _update_feature_toc(self, space_key: str, metadata: Dict, url: str):
        try:
            feature_page = self._client.get_page_by_title(space_key, metadata.get("feature", ""))
            if not feature_page:
                return
            body = feature_page.get("body", {}).get("storage", {}).get("value", "")
            if url not in body:
                entry = (f'<p>📄 <a href="{url}">{metadata["name"]}</a> '
                         f'| {metadata["producer_agent"]} | {metadata["confidence"]} '
                         f'| {metadata.get("created_at", "")[:10]}</p>')
                self._client.update_page(page_id=feature_page["id"],
                                         title=metadata.get("feature", ""),
                                         body=body + entry)
        except Exception:
            pass
```

### Step 7.3 — Conflict Resolver

Create `core/conflict_resolver.py`:

```python
"""
Conflict Resolver — checks registry before every write.
House rules:
  1. Never silently overwrite — always log the decision
  2. Prefer higher confidence artifact
  3. Never merge without HITL confirmation
  4. When in doubt — keep both, flag, surface to HITL
  5. Every decision logged with rationale
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple
from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.panel import Panel

console = Console()
CONF = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}

class ConflictResolver:

    def __init__(self, config, registry):
        self.config = config
        self.registry = registry
        self.hitl_path = config.hitl_pending_path
        self.hitl_path.mkdir(parents=True, exist_ok=True)

    def check_and_resolve(self, metadata: Dict) -> Tuple[str, Dict]:
        """
        Returns (action, resolved_metadata).
        action: insert | overwrite | skip | hitl_pending
        """
        by_name = self.registry.find_by_name(metadata["name"])
        by_fields = self.registry.find_by_fields(
            brand=metadata.get("brand"),
            domain=metadata.get("domain"),
            feature=metadata.get("feature"),
            artifact_type=metadata.get("artifact_type")
        )

        if not by_name and not by_fields:
            return "insert", metadata

        if by_name:
            return self._resolve_name_conflict(metadata, by_name[0])

        if by_fields:
            return self._resolve_field_conflict(metadata, by_fields[0])

        return "insert", metadata

    def _resolve_name_conflict(self, new: Dict, existing: Dict) -> Tuple[str, Dict]:
        new_ver = int(new.get("version", "1"))
        existing_ver = int(existing.get("version", "1"))
        new_conf = CONF.get(new.get("confidence", "UNKNOWN"), 0)
        existing_conf = CONF.get(existing.get("confidence", "UNKNOWN"), 0)

        if new_ver > existing_ver and self.config.raw["conflict_resolution"]["auto_overwrite_newer_version"]:
            new["artifact_id"] = existing["artifact_id"]
            self.registry.log_conflict(existing["artifact_id"], "VERSION_UPDATE",
                                       "AUTO_OVERWRITE", f"v{new_ver} > v{existing_ver}")
            return "overwrite", new

        if new_conf < existing_conf and self.config.raw["conflict_resolution"]["auto_flag_lower_confidence"]:
            self.registry.log_conflict(existing["artifact_id"], "LOWER_CONFIDENCE_REJECTED",
                                       "KEEP_EXISTING", f"{new.get('confidence')} < {existing.get('confidence')}")
            console.print(f"[dim yellow]  ⚠️  Skipping — lower confidence than existing[/dim yellow]")
            return "skip", existing

        return self._hitl(new, existing, "SAME_VERSION_CONFLICT")

    def _resolve_field_conflict(self, new: Dict, existing: Dict) -> Tuple[str, Dict]:
        if not self.config.raw["conflict_resolution"]["hitl_on_potential_duplicate"]:
            return "insert", new
        return self._hitl(new, existing, "POTENTIAL_DUPLICATE")

    def _hitl(self, new: Dict, existing: Dict, conflict_type: str) -> Tuple[str, Dict]:
        console.print(Panel(
            f"[bold yellow]⚡ Conflict: {conflict_type}[/bold yellow]\n"
            f"New: {new.get('name')} ({new.get('confidence')})\n"
            f"Existing: {existing.get('name')} ({existing.get('confidence')})",
            title="🔀 Conflict", border_style="yellow"
        ))
        options = [
            "Keep existing — discard new",
            "Use new — overwrite existing",
            "Keep both — insert as separate",
            "Defer — write to HITL_PENDING file"
        ]
        for i, opt in enumerate(options, 1):
            console.print(f"  {i}. {opt}")

        try:
            choice = int(IntPrompt.ask("Choice", choices=["1","2","3","4"]))
            comment = Prompt.ask("Comments (Enter to skip)", default="")
        except Exception:
            choice = 4
            comment = "Auto-deferred — no interactive terminal"

        rationale = f"{options[choice-1]}. {comment}"

        if choice == 1:
            self.registry.log_conflict(existing["artifact_id"], conflict_type, "KEPT_EXISTING", rationale)
            return "skip", existing
        elif choice == 2:
            new["artifact_id"] = existing["artifact_id"]
            self.registry.log_conflict(existing["artifact_id"], conflict_type, "OVERWRITTEN", rationale)
            return "overwrite", new
        elif choice == 3:
            self.registry.log_conflict(existing["artifact_id"], conflict_type, "KEPT_BOTH", rationale)
            return "insert", new
        else:
            self._write_hitl_file(new, existing, conflict_type)
            return "hitl_pending", new

    def _write_hitl_file(self, new: Dict, existing: Dict, conflict_type: str):
        import json
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.hitl_path / f"conflict_{new.get('name', 'unknown')}_{ts}.txt"
        path.write_text(f"""
=== KB STORE CONFLICT — HUMAN REVIEW REQUIRED ===
Type: {conflict_type}  |  Date: {datetime.now(timezone.utc).isoformat()}

NEW:      {new.get('name')} (confidence: {new.get('confidence')})
EXISTING: {existing.get('name')} (confidence: {existing.get('confidence')}, accessed: {existing.get('access_count',0)} times)

OPTIONS:
1. Keep existing — discard new
2. Use new — overwrite existing
3. Keep both

YOUR CHOICE: ___
YOUR COMMENTS:

=== Save file. Re-run kb_store.py to process. ===
""")
        console.print(f"[yellow]  📝 HITL written: {path}[/yellow]")
```

### Step 7.4 — Lineage Tracker

Create `core/lineage_tracker.py`:

```python
"""
Lineage Tracker — manages derived_from relationships.
Both registry and metadata updated simultaneously.
"""
from typing import Dict, List
from rich.console import Console

console = Console()

DERIVATION_MAP = {
    "brd_final": ["journey_map", "business_rules", "gap_analysis", "scope_definition", "ac_criteria"],
    "test_cases": ["ac_criteria", "journey_map"],
    "ac_criteria": ["brd_final", "journey_map", "business_rules"],
    "code_review": ["brd_final", "ac_criteria"],
    "defect_analysis": ["test_cases", "business_rules"],
    "regression_gaps": ["test_cases", "ac_criteria"],
}

class LineageTracker:

    def __init__(self, registry):
        self.registry = registry

    def link(self, artifact_id: str, derived_from_ids: List[str]) -> bool:
        if not derived_from_ids:
            return True
        artifact = self.registry.get(artifact_id)
        if not artifact:
            return False
        existing = artifact.get("derived_from", [])
        new_lineage = list(set(existing + derived_from_ids))
        return self.registry.update(artifact_id, {"derived_from": new_lineage})

    def infer_from_run(self, artifact_id: str, run_id: str) -> List[str]:
        """Infer lineage from other artifacts in same run."""
        if not run_id:
            return []
        artifact = self.registry.get(artifact_id)
        if not artifact:
            return []
        atype = artifact.get("artifact_type", "")
        source_types = DERIVATION_MAP.get(atype, [])
        if not source_types:
            return []
        return [
            a["artifact_id"] for a in self.registry.list_all()
            if a.get("producer_run_id") == run_id
            and a.get("artifact_type") in source_types
            and a.get("artifact_id") != artifact_id
        ]
```

### Phase 7 Validation Test

Create `tests/test_phase7_confluence.py`:

```python
"""
Phase 7 Validation Tests
Run: pytest tests/test_phase7_confluence.py -v
"""
import pytest
from pathlib import Path
from storage.confluence_sync import ConfluenceSync
from storage.json_writer import JSONWriter
from core.config_loader import KBStoreConfig

def test_confluence_disabled_returns_none():
    config = KBStoreConfig()
    config._raw["confluence"]["enabled"] = False
    sync = ConfluenceSync(config)
    result = sync.sync_artifact({"name": "test.json"}, {})
    assert result is None

def test_confluence_missing_library_degrades(monkeypatch):
    import builtins
    real = builtins.__import__
    def mock(name, *a, **kw):
        if name == "atlassian": raise ImportError("not installed")
        return real(name, *a, **kw)
    config = KBStoreConfig()
    config._raw["confluence"]["enabled"] = True
    monkeypatch.setattr(builtins, "__import__", mock)
    sync = ConfluenceSync(config)
    assert not sync.enabled

def test_json_writer_creates_file(tmp_path):
    config = KBStoreConfig()
    config._raw["output"]["kb_root"] = str(tmp_path / "KB")
    writer = JSONWriter(config)
    item = {
        "new_filename": "ST_SO_Activation_journey_map_v1.json",
        "new_relative_path": "StraightTalk/service_ordering/Activation/ST_SO_Activation_journey_map_v1.json",
        "content": {"journeys": [], "domain": "service_ordering"},
        "extension": ".json"
    }
    path = writer.write(item)
    assert path.exists()
    import json
    with open(path) as f:
        data = json.load(f)
    assert data["domain"] == "service_ordering"

def test_lineage_tracker_links(tmp_path):
    from storage.registry.json_registry import JSONRegistry
    from core.lineage_tracker import LineageTracker
    from utils.artifact_id import generate_artifact_id

    reg = JSONRegistry(tmp_path, "t", backup=False)
    tracker = LineageTracker(reg)

    source_id = generate_artifact_id()
    derived_id = generate_artifact_id()

    import time; time.sleep(1.1)
    for aid, atype in [(source_id, "journey_map"), (derived_id, "brd_final")]:
        reg.insert({
            "artifact_id": aid, "name": f"{atype}.json", "artifact_type": atype,
            "brand": "ST", "domain": "so", "feature": "Act", "version": "1",
            "format": "json", "confidence": "HIGH",
            "created_at": "2026", "updated_at": "2026",
            "derived_from": [], "used_for": [], "query_intents": [],
            "access_count": 0, "last_accessed": None,
            "producer_run_id": "run-001", "hypergraph_node_id": ""
        })

    tracker.link(derived_id, [source_id])
    updated = reg.get(derived_id)
    assert source_id in updated["derived_from"]
```

---

## PHASE 8 — Query Log

### Goal
Every RAG query interaction is logged to query_log.json. Seeds the Phase 2 FAQ cache. Simple append operation — never blocks anything.

### Step 8.1 — Query Log

Create `cache/query_log.py`:

```python
"""
Query Log — logs RAG query interactions.
This is a Phase 2 seed — data collected now, used later for FAQ cache.
Simple append to JSON. Non-blocking. Never crashes the pipeline.

Each entry records:
  - The query text
  - Which artifacts were retrieved
  - What the answer was
  - Whether it was useful
  - Session context

When Phase 2 builds the FAQ cache — this log is the training data.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console

console = Console()

class QueryLog:

    def __init__(self, config):
        self.enabled = config.query_log_enabled
        self.log_path = config.query_log_path
        self.max_entries = config.query_log_max_entries
        if self.enabled:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_path.exists():
                self._write([])

    def log(self, query_text: str, source_artifact_ids: List[str],
            answer_summary: str, intent_label: str = "",
            was_useful: bool = True, session_id: str = "",
            hypergraph_nodes_used: List[str] = None,
            retrieval_mode: str = "targeted") -> bool:
        """
        Log a RAG query interaction.

        Args:
            query_text: The original query
            source_artifact_ids: Which artifact UUIDs were retrieved
            answer_summary: Brief summary of the answer (not full answer — for size)
            intent_label: Classified intent (defect_triage, test_case_writing, etc.)
            was_useful: Did the answer satisfy the query
            session_id: Session this query belongs to
            hypergraph_nodes_used: Which hypergraph nodes were navigated
            retrieval_mode: 'targeted' (hypergraph-guided) or 'brute_force' (fallback)

        Returns: True if logged, False if disabled or error
        """
        if not self.enabled:
            return False
        try:
            entries = self._read()

            entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query_text": query_text,
                "intent_label": intent_label,
                "retrieval_mode": retrieval_mode,
                "hypergraph_nodes_used": hypergraph_nodes_used or [],
                "source_artifact_ids": source_artifact_ids,
                "answer_summary": answer_summary[:500],  # cap for storage
                "was_useful": was_useful,
                "session_id": session_id,
                # Phase 2 fields — populated by FAQ cache builder later
                "cached": False,
                "cache_hit": False,
                "source_artifact_versions": {}  # will be filled by FAQ cache
            })

            # Rotate if needed
            if len(entries) > self.max_entries:
                entries = entries[-self.max_entries:]
                console.print(f"[dim]Query log rotated to {self.max_entries} entries[/dim]")

            self._write(entries)
            return True
        except Exception as e:
            console.print(f"[dim yellow]⚠️  Query log write failed: {e}[/dim yellow]")
            return False

    def get_recent(self, n: int = 100) -> List[Dict]:
        """Get most recent N query log entries."""
        if not self.enabled:
            return []
        try:
            return self._read()[-n:]
        except Exception:
            return []

    def get_by_artifact(self, artifact_id: str) -> List[Dict]:
        """Get all queries that retrieved a specific artifact."""
        if not self.enabled:
            return []
        try:
            return [e for e in self._read() if artifact_id in e.get("source_artifact_ids", [])]
        except Exception:
            return []

    def get_stats(self) -> Dict:
        """Summary stats — useful for understanding query patterns."""
        if not self.enabled:
            return {}
        try:
            entries = self._read()
            if not entries:
                return {"total": 0}
            intents = {}
            for e in entries:
                intent = e.get("intent_label", "unknown")
                intents[intent] = intents.get(intent, 0) + 1
            return {
                "total": len(entries),
                "targeted": sum(1 for e in entries if e.get("retrieval_mode") == "targeted"),
                "brute_force": sum(1 for e in entries if e.get("retrieval_mode") == "brute_force"),
                "useful": sum(1 for e in entries if e.get("was_useful", True)),
                "intent_breakdown": intents
            }
        except Exception:
            return {}

    def _read(self) -> List:
        if not self.log_path.exists():
            return []
        with open(self.log_path) as f:
            return json.load(f)

    def _write(self, data: List):
        with open(self.log_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
```

### Phase 8 Validation Test

Create `tests/test_phase8_writer.py` (combined writer + query log tests):

```python
"""
Phase 8 Validation Tests
Run: pytest tests/test_phase8_writer.py -v
"""
import pytest
from pathlib import Path

def test_query_log_writes_entry(tmp_path):
    from core.config_loader import KBStoreConfig
    from cache.query_log import QueryLog
    config = KBStoreConfig()
    config._raw["query_log"]["path"] = str(tmp_path / "query_log.json")
    log = QueryLog(config)
    result = log.log(
        query_text="how does activation work?",
        source_artifact_ids=["uuid_abc123", "uuid_def456"],
        answer_summary="Activation requires customer validation then payment processing",
        intent_label="service_ordering_activation",
        was_useful=True,
        session_id="session-001",
        hypergraph_nodes_used=["node_ST_SO_Activation"],
        retrieval_mode="targeted"
    )
    assert result is True
    entries = log.get_recent(10)
    assert len(entries) == 1
    assert entries[0]["query_text"] == "how does activation work?"
    assert "uuid_abc123" in entries[0]["source_artifact_ids"]
    assert entries[0]["retrieval_mode"] == "targeted"

def test_query_log_disabled_returns_false(tmp_path):
    from core.config_loader import KBStoreConfig
    from cache.query_log import QueryLog
    config = KBStoreConfig()
    config._raw["query_log"]["enabled"] = False
    log = QueryLog(config)
    result = log.log("test query", [], "test answer")
    assert result is False

def test_query_log_rotates(tmp_path):
    from core.config_loader import KBStoreConfig
    from cache.query_log import QueryLog
    config = KBStoreConfig()
    config._raw["query_log"]["path"] = str(tmp_path / "query_log.json")
    config._raw["query_log"]["max_entries"] = 5
    log = QueryLog(config)
    for i in range(8):
        log.log(f"query {i}", [f"uuid_{i}"], f"answer {i}")
    entries = log.get_recent(100)
    assert len(entries) == 5  # rotated

def test_query_log_stats(tmp_path):
    from core.config_loader import KBStoreConfig
    from cache.query_log import QueryLog
    config = KBStoreConfig()
    config._raw["query_log"]["path"] = str(tmp_path / "query_log.json")
    log = QueryLog(config)
    log.log("q1", ["a1"], "ans1", intent_label="defect_triage", retrieval_mode="targeted")
    log.log("q2", ["a2"], "ans2", intent_label="defect_triage", retrieval_mode="brute_force")
    log.log("q3", ["a3"], "ans3", intent_label="test_case_writing", retrieval_mode="targeted")
    stats = log.get_stats()
    assert stats["total"] == 3
    assert stats["targeted"] == 2
    assert stats["brute_force"] == 1
    assert stats["intent_breakdown"]["defect_triage"] == 2

def test_query_log_by_artifact(tmp_path):
    from core.config_loader import KBStoreConfig
    from cache.query_log import QueryLog
    config = KBStoreConfig()
    config._raw["query_log"]["path"] = str(tmp_path / "query_log.json")
    log = QueryLog(config)
    log.log("q1", ["uuid_target", "uuid_other"], "ans1")
    log.log("q2", ["uuid_other"], "ans2")
    results = log.get_by_artifact("uuid_target")
    assert len(results) == 1
```

---

## PHASE 9 — Orchestrator + Entry Point + Integration

### Goal
Full KB Store pipeline runs end-to-end. Auto and manual modes work. All components connected. Integration test passes on fixture files.

### Step 9.1 — KB Store Orchestrator

Create `core/kb_store_orchestrator.py`:

```python
"""
KB Store Orchestrator — connects all components and runs the full pipeline.
Called by kb_store.py entry point.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict
from rich.console import Console
from rich.rule import Rule

from core.config_loader import KBStoreConfig
from core.artifact_receiver import ArtifactReceiver
from core.artifact_renamer import ArtifactRenamer
from core.metadata_extractor import MetadataExtractor
from core.conflict_resolver import ConflictResolver
from core.lineage_tracker import LineageTracker
from hypergraph.hypergraph_factory import get_hypergraph
from hypergraph.placement_agent import PlacementAgent
from hypergraph.notification_writer import NotificationWriter
from storage.json_writer import JSONWriter
from storage.confluence_sync import ConfluenceSync
from storage.registry.registry_factory import get_registry
from cache.query_log import QueryLog
from domain.domain_loader import DomainLoader
from utils.logger import KBLogger
from utils.ingestion_log import IngestionLog

console = Console()

class KBStoreOrchestrator:

    def __init__(self, config: KBStoreConfig):
        self.config = config
        self.domain_loader = DomainLoader(config.domain_config_path)
        self.registry = get_registry(config)
        self.hypergraph = get_hypergraph(config)
        self.notification_writer = NotificationWriter(config.notifications_file)
        self.run_id = str(uuid.uuid4())
        self.logger = KBLogger(self.run_id)
        self.ingestion_log = IngestionLog(config)
        self.query_log = QueryLog(config)

        self.receiver = ArtifactReceiver(config)
        self.renamer = ArtifactRenamer(config, self.domain_loader)
        self.extractor = MetadataExtractor(config, self.domain_loader)
        self.resolver = ConflictResolver(config, self.registry)
        self.tracker = LineageTracker(self.registry)
        self.placement_agent = PlacementAgent(config, self.domain_loader,
                                              self.hypergraph, self.notification_writer)
        self.writer = JSONWriter(config)
        self.confluence = ConfluenceSync(config)

    def run(self, input_path: str) -> Dict:
        console.print(Rule("[bold blue]KB Store — Ingestion Run[/bold blue]"))
        console.print(f"[dim]Run ID: {self.run_id}[/dim]")
        console.print(f"[dim]Input: {input_path}[/dim]\n")

        stats = {
            "run_id": self.run_id,
            "input_path": input_path,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "artifacts_received": 0,
            "artifacts_inserted": 0,
            "artifacts_overwritten": 0,
            "artifacts_skipped": 0,
            "artifacts_hitl_pending": 0,
            "placement_decisions": {"PLACE_IN_EXISTING": 0, "CREATE_NEW_NODE": 0,
                                    "CREATE_HYPEREDGE": 0, "TEMP_NODE": 0, "MERGE_PROPOSAL": 0},
            "confluence_pages": 0,
            "errors": []
        }

        try:
            # Step 1: Receive
            console.print("[bold]Step 1 — Receiving artifacts[/bold]")
            artifacts = self.receiver.receive(input_path)
            stats["artifacts_received"] = len(artifacts)
            if not artifacts:
                console.print("[yellow]No artifacts found. Exiting.[/yellow]")
                return stats

            # Step 2: Rename
            console.print(f"\n[bold]Step 2 — Renaming {len(artifacts)} artifacts[/bold]")
            manifest = self.renamer.create_rename_manifest(artifacts)

            # Step 3: Extract metadata
            console.print(f"\n[bold]Step 3 — Extracting metadata[/bold]")
            manifest = self.extractor.extract_batch(manifest)

            # Step 4: Process each artifact
            console.print(f"\n[bold]Step 4 — Conflict check + Placement + Write[/bold]")
            for item in manifest:
                try:
                    self._process_artifact(item, stats)
                except Exception as e:
                    stats["errors"].append(f"{item.get('new_filename', '?')}: {e}")
                    console.print(f"[red]  ✗ Failed: {item.get('new_filename', '?')}: {e}[/red]")

        except Exception as e:
            stats["errors"].append(f"Pipeline error: {e}")
            console.print(f"[red]Pipeline error: {e}[/red]")
            import traceback; traceback.print_exc()
        finally:
            stats["completed_at"] = datetime.now(timezone.utc).isoformat()
            self.ingestion_log.write(stats)
            self._print_summary(stats)

        return stats

    def _process_artifact(self, item: Dict, stats: Dict):
        metadata = item.get("metadata", {})
        if not metadata.get("artifact_id"):
            return

        # Conflict check
        action, resolved_metadata = self.resolver.check_and_resolve(metadata)

        if action == "skip":
            stats["artifacts_skipped"] += 1
            return
        if action == "hitl_pending":
            stats["artifacts_hitl_pending"] += 1
            return

        # Placement agent — intelligent hypergraph placement
        decision_type, resolved_metadata = self.placement_agent.place(resolved_metadata)
        stats["placement_decisions"][decision_type] = stats["placement_decisions"].get(decision_type, 0) + 1

        # Write JSON file
        written_path = self.writer.write(item)
        self.writer.write_metadata_sidecar(resolved_metadata, written_path)

        # Confluence sync
        confluence_url = self.confluence.sync_artifact(resolved_metadata, item.get("content", {}))
        if confluence_url:
            resolved_metadata["confluence_url"] = confluence_url
            stats["confluence_pages"] += 1

        # Registry write
        if action == "insert":
            self.registry.insert(resolved_metadata)
            stats["artifacts_inserted"] += 1
        elif action == "overwrite":
            self.registry.update(resolved_metadata["artifact_id"], resolved_metadata)
            stats["artifacts_overwritten"] += 1

        # Lineage
        run_id = resolved_metadata.get("producer_run_id", "")
        sources = self.tracker.infer_from_run(resolved_metadata["artifact_id"], run_id)
        if sources:
            self.tracker.link(resolved_metadata["artifact_id"], sources)

    def _print_summary(self, stats: Dict):
        console.print(Rule("[bold green]KB Store — Complete[/bold green]"))
        console.print(f"[green]Received:     {stats['artifacts_received']}[/green]")
        console.print(f"[green]Inserted:     {stats['artifacts_inserted']}[/green]")
        console.print(f"[blue]Overwritten:  {stats['artifacts_overwritten']}[/blue]")
        console.print(f"[dim]Skipped:      {stats['artifacts_skipped']}[/dim]")
        console.print(f"[yellow]HITL Pending: {stats['artifacts_hitl_pending']}[/yellow]")
        console.print(f"[dim]Placements:   {stats['placement_decisions']}[/dim]")
        if stats["errors"]:
            console.print(f"[red]Errors:       {len(stats['errors'])}[/red]")
```

### Step 9.2 — Entry Point

Create `kb_store.py`:

```python
"""
KB Store Entry Point
Usage:
  Auto mode   : python kb_store.py --path ./agent/output/folder
  Manual mode : Set input.path in config then: python kb_store.py
  Config mode : python kb_store.py --config ./custom_config.yaml --path ./folder
"""
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

def main():
    parser = argparse.ArgumentParser(description="KB Store — Artifact ingestion")
    parser.add_argument("--path", type=str, default="", help="Input artifact folder path")
    parser.add_argument("--config", type=str, default="config/kb_store_config.yaml")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY not set in .env[/red]")
        sys.exit(1)

    from core.config_loader import KBStoreConfig
    from core.kb_store_orchestrator import KBStoreOrchestrator

    config = KBStoreConfig(args.config)
    orchestrator = KBStoreOrchestrator(config)

    input_path = args.path or config.input_path
    if not input_path:
        console.print("[red]Error: No input path. Use --path or set input.path in config.[/red]")
        sys.exit(1)
    if not Path(input_path).exists():
        console.print(f"[red]Error: Path not found: {input_path}[/red]")
        sys.exit(1)

    stats = orchestrator.run(input_path)
    sys.exit(0 if not stats.get("errors") else 1)

if __name__ == "__main__":
    main()
```

### Step 9.3 — BRD Agent Integration Hook

Add this to the BRD Agent POC's `orchestrator/pipeline.py` at the end of `BRDPipeline.run()`:

```python
# Auto-trigger KB Store after BRD pipeline completes
import subprocess, sys
kb_output_path = str(self.kb_manager.kb_root / repo_name)
try:
    subprocess.run(
        [sys.executable, "../kb_store/kb_store.py", "--path", kb_output_path],
        check=False  # KB Store failure does not fail BRD run
    )
except Exception as e:
    console.print(f"[dim yellow]⚠️  KB Store auto-trigger failed: {e}[/dim yellow]")
```

### Phase 9 Integration Test

Create `tests/test_phase9_integration.py`:

```python
"""
Phase 9 — Full Integration Test
Run: SKIP_API_TESTS=true pytest tests/test_phase9_integration.py -v
Set SKIP_API_TESTS=false to run with real API calls.
"""
import pytest, os, json
from pathlib import Path

SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

@pytest.mark.skipif(SKIP_API, reason="API test")
def test_full_pipeline_on_fixtures(tmp_path):
    from core.config_loader import KBStoreConfig
    from core.kb_store_orchestrator import KBStoreOrchestrator

    config = KBStoreConfig()
    config._raw["output"]["kb_root"] = str(tmp_path / "KB")
    config._raw["registry"]["path"] = str(tmp_path / "registry")
    config._raw["hypergraph"]["path"] = str(tmp_path / "KB" / "graph")
    config._raw["hypergraph"]["notifications_file"] = str(tmp_path / "KB" / "graph" / "notifications.json")
    config._raw["ingestion_log"]["path"] = str(tmp_path / "registry" / "ingestion_log.json")
    config._raw["query_log"]["path"] = str(tmp_path / "KB" / "cache" / "query_log.json")
    config._raw["confluence"]["enabled"] = False

    orchestrator = KBStoreOrchestrator(config)
    stats = orchestrator.run("tests/fixtures/sample_artifacts")

    assert stats["artifacts_received"] >= 3
    assert stats["artifacts_inserted"] >= 1
    assert len(stats["errors"]) == 0

    kb_root = tmp_path / "KB"
    assert kb_root.exists()
    assert (tmp_path / "registry" / "ingestion_log.json").exists()

def test_hypergraph_rag_navigation(tmp_path):
    """Test the main RAG navigation path: alias → node → artifact UUIDs."""
    from hypergraph.json_hypergraph import JSONHypergraph
    hg = JSONHypergraph(tmp_path / "graph", "hg")

    # Simulate what placement agent would create
    hg.create_node({
        "node_id": "node_ST_SO_Activation",
        "label": "StraightTalk Activation",
        "brand": "ST", "domain": "service_ordering", "feature": "Activation",
        "artifact_ids": ["uuid_journey", "uuid_rules", "uuid_brd"],
        "aliases": ["activation", "new activation", "service activation", "order management"],
        "confidence": "HIGH", "status": "ACTIVE", "is_temp": False,
        "created_at": "2026-05-13", "human_reviewed": True
    })

    # RAG navigation: intent → hypergraph → artifact UUIDs
    ids = hg.get_artifact_ids_for_query("activation", brand="ST")
    assert "uuid_journey" in ids
    assert "uuid_rules" in ids
    assert "uuid_brd" in ids

def test_query_log_persists(tmp_path):
    from core.config_loader import KBStoreConfig
    from cache.query_log import QueryLog
    config = KBStoreConfig()
    config._raw["query_log"]["path"] = str(tmp_path / "query_log.json")

    log = QueryLog(config)
    log.log("how does activation work?", ["uuid_abc"], "Activation flow answer",
            intent_label="service_ordering", was_useful=True,
            hypergraph_nodes_used=["node_ST_SO_Activation"], retrieval_mode="targeted")

    # Verify it persists across instances
    log2 = QueryLog(config)
    entries = log2.get_recent(10)
    assert len(entries) == 1
    assert entries[0]["retrieval_mode"] == "targeted"
    assert entries[0]["was_useful"] is True

def test_registry_and_hypergraph_consistent(tmp_path):
    """Artifact in registry should also be in hypergraph node."""
    from storage.registry.json_registry import JSONRegistry
    from hypergraph.json_hypergraph import JSONHypergraph
    from utils.artifact_id import generate_artifact_id

    reg = JSONRegistry(tmp_path / "registry", "t", backup=False)
    hg = JSONHypergraph(tmp_path / "graph", "hg")

    artifact_id = generate_artifact_id()

    # Insert into registry
    reg.insert({
        "artifact_id": artifact_id, "name": "test.json",
        "artifact_type": "journey_map", "brand": "ST",
        "domain": "service_ordering", "feature": "Activation",
        "version": "1", "format": "json", "confidence": "HIGH",
        "created_at": "2026", "updated_at": "2026",
        "derived_from": [], "used_for": [], "query_intents": [],
        "access_count": 0, "last_accessed": None,
        "hypergraph_node_id": "node_ST_SO_Activation"
    })

    # Create node in hypergraph and add artifact
    hg.create_node({
        "node_id": "node_ST_SO_Activation",
        "label": "test", "brand": "ST",
        "domain": "service_ordering", "feature": "Activation",
        "artifact_ids": [], "aliases": ["activation"],
        "status": "ACTIVE", "is_temp": False, "created_at": "2026", "human_reviewed": False
    })
    hg.append_artifact_to_node("node_ST_SO_Activation", artifact_id)

    # Verify consistency
    from_registry = reg.get(artifact_id)
    from_hypergraph = hg.get_artifact_ids_for_query("activation", brand="ST")

    assert from_registry is not None
    assert artifact_id in from_hypergraph
```

---

## QUICK START GUIDE

```bash
# 1. Create project and install
mkdir kb_store && cd kb_store
pip install -r requirements.txt

# 2. Environment setup
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY
# Add Confluence credentials when available

# 3. Configure
# Edit config/kb_store_config.yaml
# Choose registry.type: json or sqlite
# Choose hypergraph.type: json or sqlite
# Set input.path for manual mode
# Set confluence.enabled: true when ready

# 4. Run Phase 1 tests (no API needed)
SKIP_API_TESTS=true pytest tests/test_phase1_config.py -v

# 5. Run on fixture files (uses API)
python kb_store.py --path tests/fixtures/sample_artifacts

# 6. Run on BRD Agent output
python kb_store.py --path ../brd_agent_poc/KB/your_repo_name/

# 7. Run all non-API tests
SKIP_API_TESTS=true pytest tests/ -v

# 8. Run full integration (uses API)
pytest tests/ -v -s

# Check outputs:
# KB/              — renamed artifacts in folder structure
# KB/graph/        — hypergraph.json + notifications.json
# KB/cache/        — query_log.json
# registry/        — artifact_registry.json|db + ingestion_log.json
# HITL_PENDING/    — conflict files needing human review
```

---

## SELF-CORRECTION GUIDE

**Config loads but registry_type error**
Check spelling in yaml — must be exactly `json` or `sqlite`.

**Receiver finds 0 artifacts**
Check input.path is correct. Check file_types patterns. Check exclude_patterns not too broad.

**LLM returns invalid JSON (renamer or metadata)**
Add retry in `_extract_via_llm`: on parse error send raw back with "Return ONLY valid JSON, no other text: {raw}". Max 3 retries.

**Placement agent always creates TEMP nodes**
Check domain config is populated. Ensure existing nodes exist in hypergraph before running. First run always creates new nodes — subsequent runs place in existing.

**SQLite locked error**
Ensure WAL mode in `_init_db()`. Increase `timeout=30` in `sqlite3.connect()`.

**Confluence sync crashes instead of degrading**
Every Confluence call must be in try/except. Check `_ensure_page` and `_update_feature_toc` both have exception handlers.

**Hypergraph alias lookup returns empty**
Check aliases are lowercased when stored and when queried. Check alias index is updated in `create_node()`.

---

## RAG COMPONENT CONTRACT

When building the RAG Component MD — these are the KB Store outputs it depends on:

```
Hypergraph navigation:
  hg = get_hypergraph(config)
  artifact_ids = hg.get_artifact_ids_for_query(intent, brand=brand_filter)
  # Returns: list of artifact UUIDs to search in vector store

Registry writeback (called after every RAG query):
  registry.writeback(
      artifact_id,
      query_intent="defect_triage",
      task_type="defect_triage",
      was_useful=True,
      session_id="session-xyz"
  )

Query log (called after every RAG query):
  query_log.log(
      query_text="...",
      source_artifact_ids=["uuid1", "uuid2"],
      answer_summary="...",
      intent_label="defect_triage",
      was_useful=True,
      session_id="session-xyz",
      hypergraph_nodes_used=["node_ST_SO_Activation"],
      retrieval_mode="targeted"  # or "brute_force" for fallback
  )

Artifact files are in:
  KB/{Brand}/{Domain}/{Feature}/{artifact_name}.json
  → these are what LightRAG ingests for embeddings

Vector store is initialized at:
  KB/graph/lightrag/   (RAG component owns this)
```

---

*End of KB Store Component Build Instructions v2*
*Version: 2.0 | Includes: Hypergraph + Placement Agent + Query Log*
*Next: RAG Component MD*

---

# PART 2 — RAG COMPONENT
## Setup Once. Query Always. Embeddings Auto-Update With Every KB Store Run.

---

## IMPORTANT — HOW PARTS 1 AND 2 WORK TOGETHER

```
EVERY BRD AGENT RUN:
  BRD Agent → KB Store (Part 1) → Embedding Hook → LightRAG ingests new artifacts
                                                      (skips already embedded)

ONCE (setup only):
  Part 2 Phases 11-12 → LightRAG initialized → Initial bulk ingestion

ALWAYS AVAILABLE (query layer):
  Part 2 Phase 13 → Query interface → answer any question against KB
```

LightRAG tracks processed documents in its internal KV store at KB/graph/lightrag/. When the embedding hook fires after a KB Store run — LightRAG checks its store and only processes artifacts it has not seen before. You never re-embed what is already embedded. Handled by LightRAG natively.

Do NOT re-run Part 2 Phases 11-12 after initial setup. The embedding hook in Phase 10 handles all incremental ingestion.

---

## ADDITIONAL REQUIREMENTS FOR PART 2

Add to requirements.txt:

```
lightrag-hku>=1.0.0
streamlit>=1.40.0
fastapi>=0.115.0
uvicorn>=0.32.0
httpx>=0.27.0
```

### LightRAG Installation Notes

```bash
pip install lightrag-hku
python -c "from lightrag import LightRAG; print('LightRAG OK')"

# If dependency conflicts:
pip install lightrag-hku --no-deps
pip install networkx tiktoken aiohttp

# Fallback if LightRAG unavailable:
# Set rag.adapter: chromadb_direct in config
```

---

## ADDITIONAL CONFIG — ADD TO KB_STORE_CONFIG.YAML

```yaml
embeddings:
  enabled: false              # SET TO true after Phase 11-12 setup
  adapter: lightrag           # lightrag | chromadb_direct
  lightrag_working_dir: ./KB/graph/lightrag
  embedding_model: all-MiniLM-L6-v2
  llm_model: claude-haiku-4-5-20251001
  chunk_size: 1200
  chunk_overlap: 100
  skip_existing: true

rag:
  adapter: lightrag
  lightrag_working_dir: ./KB/graph/lightrag
  confidence_threshold_high: 0.75
  confidence_threshold_low: 0.40
  max_results: 5
  session_timeout_minutes: 60
  intent_model: llm
  intent_llm_model: claude-haiku-4-5-20251001

ui:
  title: "Enterprise Knowledge Base"
  show_navigation_path: true
  show_source_documents: true
  show_confidence: true
  port: 8501
```

---

## ADDITIONAL PROJECT STRUCTURE FOR PART 2

```
kb_store/
├── rag/
│   ├── __init__.py
│   ├── embedding_hook.py
│   ├── rag_interface.py
│   ├── lightrag_adapter.py
│   ├── chromadb_adapter.py
│   ├── rag_factory.py
│   ├── intent_recognizer.py
│   ├── query_engine.py
│   ├── session_manager.py
│   └── setup_rag.py
├── interfaces/
│   ├── __init__.py
│   ├── agent_interface.py
│   ├── rest_api.py
│   └── streamlit_ui.py
└── tests/
    ├── test_phase10_embedding.py
    ├── test_phase11_lightrag.py
    ├── test_phase12_query.py
    ├── test_phase13_interfaces.py
    └── test_phase14_integration.py
```

---

## PHASE 10 — Embedding Hook (Added to KB Store)

### Goal
Every KB Store run automatically ingests new artifacts into LightRAG. Disabled by default. Enabled after RAG setup is complete.

### Step 10.1 — Embedding Hook

Create `rag/embedding_hook.py`:

```python
"""
Embedding Hook — fires at end of every KB Store run.
Ingests new artifacts into LightRAG. Skips already-embedded (LightRAG native).
Disabled by default — enable after completing Phase 11-12.
"""
import asyncio
import json
from pathlib import Path
from typing import List, Dict
from rich.console import Console

console = Console()

class EmbeddingHook:

    def __init__(self, config):
        self.config = config
        embed_cfg = config.raw.get("embeddings", {})
        self.enabled = embed_cfg.get("enabled", False)
        self.working_dir = embed_cfg.get("lightrag_working_dir", "./KB/graph/lightrag")
        self.adapter_type = embed_cfg.get("adapter", "lightrag")
        self._rag = None

    def run(self, newly_ingested_paths: List[str]) -> Dict:
        if not self.enabled:
            console.print("[dim]  ⚪ Embedding hook disabled — enable after RAG setup.[/dim]")
            return {"status": "disabled", "processed": 0}
        if not newly_ingested_paths:
            return {"status": "no_new_artifacts", "processed": 0}

        console.print(f"\n[bold]Embedding Hook — {len(newly_ingested_paths)} new artifact(s)[/bold]")
        try:
            rag = self._get_rag()
            results = asyncio.run(self._ingest(rag, newly_ingested_paths))
            console.print(f"[green]  ✓ Embedded {results['processed']} artifact(s)[/green]")
            return results
        except Exception as e:
            console.print(f"[yellow]  ⚠️  Embedding hook failed: {e}[/yellow]")
            return {"status": "error", "error": str(e), "processed": 0}

    async def _ingest(self, rag, paths: List[str]) -> Dict:
        processed = 0
        errors = []
        for path_str in paths:
            path = Path(path_str)
            if not path.exists() or path.suffix not in [".json", ".md", ".txt"]:
                continue
            try:
                text = self._to_readable_text(path)
                if text:
                    await rag.ainsert(text)
                    processed += 1
                    console.print(f"[dim]    ✓ Embedded: {path.name}[/dim]")
            except Exception as e:
                errors.append(f"{path.name}: {e}")
        return {"status": "ok", "processed": processed, "errors": errors}

    def _to_readable_text(self, path: Path) -> str:
        """Convert artifact to readable text for better LightRAG entity extraction."""
        try:
            if path.suffix == ".json":
                with open(path) as f:
                    data = json.load(f)
                lines = [f"Artifact: {path.name}"]
                for key in ["component_name", "domain", "feature", "brand", "description"]:
                    if data.get(key):
                        lines.append(f"{key.replace('_', ' ').title()}: {data[key]}")
                for key in ["journeys", "rules", "gaps", "risks", "test_cases", "acceptance_criteria"]:
                    items = data.get(key, [])
                    if items:
                        lines.append(f"\n{key.replace('_', ' ').title()}:")
                        for item in items[:20]:
                            if isinstance(item, dict):
                                name = item.get("name", item.get("id", ""))
                                desc = item.get("plain_english", item.get("description", ""))
                                if name:
                                    lines.append(f"  - {name}: {desc}")
                            else:
                                lines.append(f"  - {item}")
                return "\n".join(lines)
            else:
                return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _get_rag(self):
        if self._rag is None:
            if self.adapter_type == "lightrag":
                from rag.lightrag_adapter import create_lightrag
                self._rag = create_lightrag(self.config)
            else:
                from rag.chromadb_adapter import ChromaDBDirectAdapter
                self._rag = ChromaDBDirectAdapter(self.config)
        return self._rag
```

### Step 10.2 — Wire Hook Into KB Store Orchestrator

In `core/kb_store_orchestrator.py` make these changes:

```python
# Add to imports at top:
from rag.embedding_hook import EmbeddingHook

# Add to __init__:
self.embedding_hook = EmbeddingHook(config)

# Add tracking list inside run() at start of try block:
newly_written_paths = []

# In _process_artifact() after self.writer.write(item):
newly_written_paths.append(str(written_path))

# At end of run() before finally block:
if newly_written_paths:
    embed_result = self.embedding_hook.run(newly_written_paths)
    stats["embedding"] = embed_result
```

### Phase 10 Validation Test

Create `tests/test_phase10_embedding.py`:

```python
"""
Phase 10 Validation Tests
Run: SKIP_API_TESTS=true pytest tests/test_phase10_embedding.py -v
"""
import pytest, os
SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

def test_hook_disabled_by_default():
    from core.config_loader import KBStoreConfig
    from rag.embedding_hook import EmbeddingHook
    config = KBStoreConfig()
    config._raw.setdefault("embeddings", {})["enabled"] = False
    hook = EmbeddingHook(config)
    result = hook.run(["some/path.json"])
    assert result["status"] == "disabled"

def test_hook_no_paths():
    from core.config_loader import KBStoreConfig
    from rag.embedding_hook import EmbeddingHook
    config = KBStoreConfig()
    config._raw.setdefault("embeddings", {})["enabled"] = True
    hook = EmbeddingHook(config)
    result = hook.run([])
    assert result["status"] == "no_new_artifacts"

def test_to_readable_text(tmp_path):
    import json
    from core.config_loader import KBStoreConfig
    from rag.embedding_hook import EmbeddingHook
    config = KBStoreConfig()
    config._raw.setdefault("embeddings", {})["enabled"] = False
    hook = EmbeddingHook(config)
    test_file = tmp_path / "journey_map.json"
    data = {
        "component_name": "SampleService",
        "domain": "service_ordering",
        "journeys": [{"name": "Happy Path", "plain_english": "Customer activates"}]
    }
    with open(test_file, "w") as f:
        json.dump(data, f)
    text = hook._to_readable_text(test_file)
    assert "SampleService" in text
    assert "Happy Path" in text
```

---

## PHASE 11 — LightRAG Setup + Initial Bulk Ingestion

### Goal
LightRAG initialized. All existing KB artifacts ingested. Run ONCE after KB Store has populated the KB folder.

### Step 11.1 — LightRAG Adapter

Create `rag/lightrag_adapter.py`:

```python
"""
LightRAG Adapter — initializes LightRAG with sentence-transformers embeddings
and Claude Haiku for entity extraction.
Falls back to ChromaDB if LightRAG unavailable.
"""
import os
import asyncio
from pathlib import Path
from rich.console import Console

console = Console()

def create_lightrag(config):
    try:
        from lightrag import LightRAG
        from lightrag.utils import EmbeddingFunc
        from sentence_transformers import SentenceTransformer
        import anthropic as anthropic_sdk

        embed_cfg = config.raw.get("embeddings", {})
        rag_cfg = config.raw.get("rag", {})
        working_dir = embed_cfg.get("lightrag_working_dir") or rag_cfg.get("lightrag_working_dir", "./KB/graph/lightrag")
        embed_model_name = embed_cfg.get("embedding_model", "all-MiniLM-L6-v2")
        llm_model = embed_cfg.get("llm_model", "claude-haiku-4-5-20251001")

        Path(working_dir).mkdir(parents=True, exist_ok=True)
        st_model = SentenceTransformer(embed_model_name)

        async def embedding_func(texts):
            return st_model.encode(texts, normalize_embeddings=True).tolist()

        async def llm_func(prompt, system_prompt=None, **kwargs):
            client = anthropic_sdk.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            resp = client.messages.create(
                model=llm_model, max_tokens=2048,
                system=system_prompt or "You are a helpful assistant.",
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.content[0].text

        rag = LightRAG(
            working_dir=working_dir,
            llm_model_func=llm_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=384,
                max_token_size=8192,
                func=embedding_func
            )
        )
        console.print(f"[dim green]✓ LightRAG initialized: {working_dir}[/dim green]")
        return rag

    except ImportError as e:
        console.print(f"[yellow]LightRAG not available: {e}. Using ChromaDB fallback.[/yellow]")
        from rag.chromadb_adapter import ChromaDBDirectAdapter
        return ChromaDBDirectAdapter(config)
    except Exception as e:
        console.print(f"[red]LightRAG init failed: {e}[/red]")
        raise


async def bulk_ingest_kb(rag, kb_root: str, domain_context: str = "") -> dict:
    """Bulk ingest all KB artifacts. Run ONCE. LightRAG skips already-processed."""
    from rag.embedding_hook import EmbeddingHook

    kb_path = Path(kb_root)
    if not kb_path.exists():
        return {"processed": 0, "error": "KB root not found"}

    exclude = {"run_metadata.json", "ingestion_log.json", "query_log.json",
               "notifications.json", "hypergraph.json"}

    files = [
        f for f in kb_path.rglob("*.json")
        if f.name not in exclude
        and ".meta." not in f.name
        and "lightrag" not in str(f)
        and "registry" not in str(f)
        and "cache" not in str(f)
        and "graph" not in str(f)
    ]

    console.print(f"[bold]Bulk ingestion — {len(files)} artifacts[/bold]")

    class _FakeConfig:
        raw = {"embeddings": {"enabled": False}}
    hook = EmbeddingHook(_FakeConfig())

    processed = 0
    errors = []
    for file_path in files:
        try:
            import json
            with open(file_path) as f:
                data = json.load(f)
            text = hook._to_readable_text(file_path)
            if domain_context:
                text = f"DOMAIN CONTEXT:\n{domain_context}\n\n{text}"
            await rag.ainsert(text)
            processed += 1
            if processed % 10 == 0:
                console.print(f"[dim]  {processed}/{len(files)} embedded[/dim]")
        except Exception as e:
            errors.append(f"{file_path.name}: {e}")

    console.print(f"[green]✓ Bulk ingestion: {processed}/{len(files)}[/green]")
    return {"processed": processed, "total": len(files), "errors": errors}
```

### Step 11.2 — ChromaDB Fallback

Create `rag/chromadb_adapter.py`:

```python
"""
ChromaDB Direct Adapter — fallback when LightRAG unavailable.
Vector similarity only — no entity graph.
"""
from pathlib import Path
from rich.console import Console

console = Console()

class ChromaDBDirectAdapter:

    def __init__(self, config):
        working_dir = config.raw.get("rag", {}).get("lightrag_working_dir", "./KB/graph/lightrag")
        self.persist_path = str(Path(working_dir) / "chromadb_fallback")
        self._collection = None
        self._embedder = None

    def _init(self):
        if self._collection is None:
            import chromadb
            from sentence_transformers import SentenceTransformer
            client = chromadb.PersistentClient(path=self.persist_path)
            self._collection = client.get_or_create_collection("kb_artifacts")
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")

    async def ainsert(self, text: str):
        self._init()
        try:
            doc_id = str(hash(text[:200]))
            if self._collection.get(ids=[doc_id])["ids"]:
                return
            emb = self._embedder.encode(text[:2000]).tolist()
            self._collection.add(documents=[text[:2000]], embeddings=[emb], ids=[doc_id])
        except Exception as e:
            console.print(f"[dim yellow]ChromaDB insert: {e}[/dim yellow]")

    async def aquery(self, query: str, param=None) -> str:
        self._init()
        try:
            emb = self._embedder.encode(query).tolist()
            results = self._collection.query(query_embeddings=[emb], n_results=5)
            if results and results["documents"]:
                return "\n\n---\n\n".join(results["documents"][0][:3])
            return ""
        except Exception as e:
            return ""
```

### Step 11.3 — RAG Factory

Create `rag/rag_factory.py`:

```python
def get_rag(config):
    adapter = config.raw.get("rag", {}).get("adapter", "lightrag")
    if adapter == "lightrag":
        from rag.lightrag_adapter import create_lightrag
        return create_lightrag(config)
    from rag.chromadb_adapter import ChromaDBDirectAdapter
    return ChromaDBDirectAdapter(config)
```

### Step 11.4 — Setup Script (Run Once)

Create `rag/setup_rag.py`:

```python
"""
RAG Setup — run ONCE after KB Store has populated KB folder.
Usage: python rag/setup_rag.py [--kb-root ./KB] [--config config/kb_store_config.yaml]
After this: set embeddings.enabled: true in config.
"""
import argparse, asyncio, sys, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.rule import Rule

console = Console()

async def setup(kb_root: str, config_path: str):
    console.print(Rule("[bold blue]RAG Setup — Initial Bulk Ingestion[/bold blue]"))
    console.print("[dim]Run ONCE. Future ingestion handled by embedding hook.[/dim]\n")

    from core.config_loader import KBStoreConfig
    from domain.domain_loader import DomainLoader
    from rag.lightrag_adapter import create_lightrag, bulk_ingest_kb

    config = KBStoreConfig(config_path)
    domain = DomainLoader(config.domain_config_path)

    console.print("[bold]Step 1 — Initializing LightRAG[/bold]")
    rag = create_lightrag(config)

    console.print(f"\n[bold]Step 2 — Bulk ingesting from {kb_root}[/bold]")
    results = await bulk_ingest_kb(rag, kb_root, domain.get_ontology_prompt())

    console.print(Rule("[bold green]Setup Complete[/bold green]"))
    console.print(f"[green]Embedded: {results['processed']}[/green]")
    console.print("\nNext steps:")
    console.print("  1. Set embeddings.enabled: true in config")
    console.print("  2. Run: streamlit run interfaces/streamlit_ui.py")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb-root", default="./KB")
    parser.add_argument("--config", default="config/kb_store_config.yaml")
    args = parser.parse_args()
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY not set[/red]")
        sys.exit(1)
    asyncio.run(setup(args.kb_root, args.config))

if __name__ == "__main__":
    main()
```

### Phase 11 Validation Test

Create `tests/test_phase11_lightrag.py`:

```python
"""Phase 11 Validation Tests"""
import pytest, os
SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

def test_lightrag_importable():
    try:
        from lightrag import LightRAG
    except ImportError:
        pytest.skip("lightrag-hku not installed: pip install lightrag-hku")

def test_chromadb_fallback_importable():
    from rag.chromadb_adapter import ChromaDBDirectAdapter
    assert ChromaDBDirectAdapter is not None

def test_rag_factory_chromadb(tmp_path):
    from core.config_loader import KBStoreConfig
    from rag.rag_factory import get_rag
    from rag.chromadb_adapter import ChromaDBDirectAdapter
    config = KBStoreConfig()
    config._raw.setdefault("rag", {})["adapter"] = "chromadb_direct"
    assert isinstance(get_rag(config), ChromaDBDirectAdapter)

@pytest.mark.skipif(SKIP_API, reason="API + LightRAG")
def test_lightrag_insert_query(tmp_path):
    from core.config_loader import KBStoreConfig
    import asyncio
    config = KBStoreConfig()
    config._raw.setdefault("embeddings", {})["lightrag_working_dir"] = str(tmp_path / "lr")
    config._raw.setdefault("rag", {})["lightrag_working_dir"] = str(tmp_path / "lr")
    from rag.lightrag_adapter import create_lightrag
    rag = create_lightrag(config)
    async def run():
        await rag.ainsert("StraightTalk activation needs customer validation.")
        return await rag.aquery("how does activation work?")
    answer = asyncio.run(run())
    assert answer and len(answer) > 10
```

---

## PHASE 12 — Query Engine + Intent Recognition + Session

### Goal
Full query flow: intent → hypergraph → targeted search → confidence → write-back → log. Brute force fallback works. Session context maintained.

### Step 12.1 — Intent Recognizer

Create `rag/intent_recognizer.py`:

```python
"""Intent Recognizer — LLM-based query classification before hypergraph navigation."""
import json, os
from typing import Dict
from rich.console import Console
import anthropic

console = Console()

INTENT_SYSTEM = """You are an intent classifier for an enterprise knowledge base.
Extract search intent to navigate the knowledge graph.
Respond ONLY in valid JSON."""

INTENT_PROMPT = """Classify this query.

DOMAIN CONTEXT:
{domain_context}

QUERY: "{query}"

JSON response:
{{
  "domain": "service_ordering|payments|identity|catalog|unknown",
  "brand": "ST|TW|TF|WFM|unknown",
  "topic": "specific topic e.g. activation, portin, subscription",
  "intent_label": "defect_triage|test_case_writing|code_generation|architecture_decision|requirement_clarification|general_knowledge",
  "search_terms": ["terms", "to", "search"],
  "confidence": "HIGH|MEDIUM|LOW"
}}"""

class IntentRecognizer:

    def __init__(self, config, domain_loader):
        self.config = config
        self.domain_loader = domain_loader
        self.model = config.raw.get("rag", {}).get("intent_llm_model", "claude-haiku-4-5-20251001")
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def recognize(self, query: str) -> Dict:
        try:
            prompt = INTENT_PROMPT.format(
                domain_context=self.domain_loader.get_ontology_prompt()[:600],
                query=query
            )
            resp = self.client.messages.create(
                model=self.model, max_tokens=512, system=INTENT_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            intent = json.loads(raw.strip())
            console.print(f"[dim]  🎯 Intent: {intent.get('domain')}/{intent.get('topic')}[/dim]")
            return intent
        except Exception as e:
            console.print(f"[dim yellow]Intent recognition failed: {e}[/dim yellow]")
            return {"domain": "unknown", "brand": "unknown", "topic": "",
                    "intent_label": "general_knowledge",
                    "search_terms": query.split()[:5], "confidence": "LOW"}
```

### Step 12.2 — Session Manager

Create `rag/session_manager.py`:

```python
"""In-memory session context. POC only — clears on process restart."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

class SessionManager:

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    def create_session(self, who: str = "human") -> str:
        sid = str(uuid.uuid4())
        self._sessions[sid] = {
            "session_id": sid, "created_at": datetime.now(timezone.utc).isoformat(),
            "last_active": datetime.now(timezone.utc).isoformat(),
            "agent_or_human": who, "queries": [], "retrieved_artifacts": [],
            "context_summary": ""
        }
        return sid

    def get_session(self, sid: str) -> Optional[Dict]:
        return self._sessions.get(sid)

    def update_session(self, sid: str, query: str, answer: str, artifact_ids: List[str]):
        if sid not in self._sessions: return
        s = self._sessions[sid]
        s["queries"].append({"query": query, "answer_summary": answer[:200],
                             "timestamp": datetime.now(timezone.utc).isoformat()})
        for aid in artifact_ids:
            if aid not in s["retrieved_artifacts"]:
                s["retrieved_artifacts"].append(aid)
        s["last_active"] = datetime.now(timezone.utc).isoformat()
        s["context_summary"] = " | ".join(f"Q: {q['query'][:50]}" for q in s["queries"][-3:])

    def get_context(self, sid: str) -> str:
        return self._sessions.get(sid, {}).get("context_summary", "")

    def end_session(self, sid: str):
        self._sessions.pop(sid, None)
```

### Step 12.3 — Query Engine

Create `rag/query_engine.py`:

```python
"""
Query Engine — full query flow.
HIGH confidence: targeted search hit.
LOW confidence: brute force fallback.
NOT_FOUND: nothing retrieved even with brute force.
Source artifacts always listed for human audit.
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from rich.console import Console

console = Console()

NOT_FOUND = (
    "I could not find relevant information in the knowledge base. "
    "The KB may not contain artifacts for this topic yet. "
    "Run the BRD Agent on the relevant repository to generate knowledge."
)

@dataclass
class QueryResult:
    query: str
    answer: str
    confidence: str           # HIGH | LOW | NOT_FOUND
    source_artifacts: List[Dict]
    hypergraph_nodes_used: List[str]
    retrieval_mode: str       # targeted | brute_force
    intent: Dict = field(default_factory=dict)
    session_id: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items()}

class QueryEngine:

    def __init__(self, config, rag, hypergraph, registry,
                 intent_recognizer, session_manager, query_log):
        self.config = config
        self.rag = rag
        self.hypergraph = hypergraph
        self.registry = registry
        self.intent_rec = intent_recognizer
        self.session_mgr = session_manager
        self.query_log = query_log
        rag_cfg = config.raw.get("rag", {})
        self.thresh_high = rag_cfg.get("confidence_threshold_high", 0.75)
        self.thresh_low = rag_cfg.get("confidence_threshold_low", 0.40)

    def query(self, text: str, session_id: Optional[str] = None,
              brand: Optional[str] = None) -> QueryResult:
        return asyncio.run(self.aquery(text, session_id, brand))

    async def aquery(self, text: str, session_id: Optional[str] = None,
                     brand: Optional[str] = None) -> QueryResult:
        ts = datetime.now(timezone.utc).isoformat()
        if not session_id:
            session_id = self.session_mgr.create_session()

        ctx = self.session_mgr.get_context(session_id)
        enriched = f"Context: {ctx}\n\nQuery: {text}" if ctx else text

        intent = self.intent_rec.recognize(text)
        brand_filter = brand or (intent.get("brand") if intent.get("brand") != "unknown" else None)

        # Hypergraph navigation
        artifact_ids = []
        for term in intent.get("search_terms", [text.split()[0]]):
            artifact_ids.extend(self.hypergraph.get_artifact_ids_for_query(term, brand=brand_filter))
        if intent.get("topic"):
            artifact_ids.extend(self.hypergraph.get_artifact_ids_for_query(intent["topic"], brand=brand_filter))
        artifact_ids = list(set(artifact_ids))

        result = QueryResult(query=text, answer="", confidence="NOT_FOUND",
                             source_artifacts=[], hypergraph_nodes_used=[],
                             retrieval_mode="targeted", intent=intent,
                             session_id=session_id, timestamp=ts)

        if artifact_ids:
            console.print(f"[dim]  📍 Targeted: {len(artifact_ids)} artifact(s)[/dim]")
            try:
                from lightrag import QueryParam
                answer = await self.rag.aquery(enriched, param=QueryParam(mode="naive"))
            except Exception:
                answer = await self.rag.aquery(enriched)

            if answer and len(answer) > 50:
                result.answer = answer
                result.confidence = "HIGH"
                result.source_artifacts = self._get_details(artifact_ids[:5])
                result.retrieval_mode = "targeted"
            else:
                result = await self._brute_force(result, enriched)
        else:
            console.print("[dim]  🔍 No hypergraph match — brute force[/dim]")
            result = await self._brute_force(result, enriched)

        self._writeback(result, intent, session_id)
        self.session_mgr.update_session(session_id, text, result.answer,
                                        [a["artifact_id"] for a in result.source_artifacts])
        return result

    async def _brute_force(self, result: QueryResult, query: str) -> QueryResult:
        try:
            from lightrag import QueryParam
            answer = await self.rag.aquery(query, param=QueryParam(mode="hybrid"))
        except Exception:
            answer = await self.rag.aquery(query)

        if answer and len(answer) > 50:
            result.answer = answer
            result.confidence = "LOW"
            result.retrieval_mode = "brute_force"
        else:
            result.answer = NOT_FOUND
            result.confidence = "NOT_FOUND"
        return result

    def _get_details(self, ids: List[str]) -> List[Dict]:
        details = []
        for aid in ids:
            a = self.registry.get(aid)
            if a:
                details.append({
                    "artifact_id": aid,
                    "name": a.get("name", ""),
                    "artifact_type": a.get("artifact_type", ""),
                    "file_path": a.get("file_path", ""),
                    "confidence": a.get("confidence", ""),
                    "producer_agent": a.get("producer_agent", "")
                })
        return details

    def _writeback(self, result: QueryResult, intent: Dict, session_id: str):
        label = intent.get("intent_label", "general_knowledge")
        useful = result.confidence == "HIGH"
        for a in result.source_artifacts:
            try:
                self.registry.writeback(a["artifact_id"], label, label, useful, session_id)
            except Exception:
                pass
        try:
            self.query_log.log(
                result.query, [a["artifact_id"] for a in result.source_artifacts],
                result.answer[:500], label, useful, session_id,
                result.hypergraph_nodes_used, result.retrieval_mode
            )
        except Exception:
            pass
```

### Phase 12 Validation Test

Create `tests/test_phase12_query.py`:

```python
"""Phase 12 Validation Tests"""
import pytest, os
SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

def test_query_result_dataclass():
    from rag.query_engine import QueryResult
    r = QueryResult(query="test", answer="ans", confidence="HIGH",
                    source_artifacts=[{"artifact_id": "abc"}],
                    hypergraph_nodes_used=["node1"], retrieval_mode="targeted")
    d = r.to_dict()
    assert d["confidence"] == "HIGH"
    assert d["retrieval_mode"] == "targeted"

def test_session_manager_lifecycle():
    from rag.session_manager import SessionManager
    sm = SessionManager()
    sid = sm.create_session("human")
    sm.update_session(sid, "q1", "a1", ["uuid1"])
    assert sm.get_context(sid) != ""
    sm.end_session(sid)
    assert sm.get_session(sid) is None

@pytest.mark.skipif(SKIP_API, reason="API test")
def test_intent_recognizer(tmp_path):
    from core.config_loader import KBStoreConfig
    from domain.domain_loader import DomainLoader
    from rag.intent_recognizer import IntentRecognizer
    config = KBStoreConfig()
    domain = DomainLoader(config.domain_config_path)
    rec = IntentRecognizer(config, domain)
    intent = rec.recognize("how does StraightTalk activation work?")
    assert "domain" in intent
    assert len(intent.get("search_terms", [])) > 0
```

---

## PHASE 13 — Query Interfaces

### Step 13.1 — Agent Interface

Create `interfaces/agent_interface.py`:

```python
"""
Agent Interface — Python function. Import and call directly.
from interfaces.agent_interface import KBQueryClient
client = KBQueryClient()
result = client.query("how does activation work?", brand="ST")
"""
from typing import Optional, Dict

class KBQueryClient:

    def __init__(self, config_path: str = "config/kb_store_config.yaml"):
        self.config_path = config_path
        self._engine = None
        self._session_id = None

    def _init(self):
        if self._engine is not None: return
        from core.config_loader import KBStoreConfig
        from domain.domain_loader import DomainLoader
        from hypergraph.hypergraph_factory import get_hypergraph
        from storage.registry.registry_factory import get_registry
        from rag.rag_factory import get_rag
        from rag.intent_recognizer import IntentRecognizer
        from rag.session_manager import SessionManager
        from cache.query_log import QueryLog
        from rag.query_engine import QueryEngine

        config = KBStoreConfig(self.config_path)
        domain = DomainLoader(config.domain_config_path)
        rag = get_rag(config)
        hg = get_hypergraph(config)
        reg = get_registry(config)
        sm = SessionManager()
        self._engine = QueryEngine(config, rag, hg, reg,
                                   IntentRecognizer(config, domain), sm, QueryLog(config))
        self._session_id = sm.create_session("agent")

    def query(self, text: str, brand: Optional[str] = None,
              new_session: bool = False) -> Dict:
        self._init()
        if new_session:
            from rag.session_manager import SessionManager
            sm = SessionManager()
            self._session_id = sm.create_session("agent")
        result = self._engine.query(text, self._session_id, brand)
        return result.to_dict()
```

### Step 13.2 — REST API (Optional)

Create `interfaces/rest_api.py`:

```python
"""
Optional REST endpoint. Use when agent is in different process.
Run: python interfaces/rest_api.py
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="KB Query API")
_client = None

class QueryRequest(BaseModel):
    query: str
    brand: Optional[str] = None
    new_session: bool = False

@app.on_event("startup")
async def startup():
    global _client
    from interfaces.agent_interface import KBQueryClient
    _client = KBQueryClient()
    _client._init()

@app.post("/query")
async def query(req: QueryRequest):
    return _client.query(req.query, req.brand, req.new_session)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 13.3 — Streamlit Human UI

Create `interfaces/streamlit_ui.py`:

```python
"""
Streamlit chat UI for human KB queries.
Run: streamlit run interfaces/streamlit_ui.py

Shows: answer + confidence badge + source documents + navigation path (expandable).
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Enterprise KB", page_icon="🧠", layout="wide")

@st.cache_resource
def get_client():
    from interfaces.agent_interface import KBQueryClient
    return KBQueryClient()

def confidence_badge(c: str):
    if c == "HIGH": st.success("✅ HIGH CONFIDENCE — targeted retrieval")
    elif c == "LOW": st.warning("⚠️ LOW CONFIDENCE — brute force search")
    else: st.error("❌ NOT FOUND — no relevant knowledge found")

def show_sources(artifacts: list):
    if not artifacts:
        st.caption("No specific sources identified")
        return
    st.markdown("**Source Documents:**")
    for a in artifacts:
        cols = st.columns([3, 2, 2])
        cols[0].caption(f"📄 {a.get('name', '?')}")
        cols[1].caption(f"{a.get('artifact_type', '?')}")
        cols[2].caption(f"Confidence: {a.get('confidence', '?')}")

def show_nav(nodes: list, mode: str, intent: dict):
    with st.expander("🔍 How I found this", expanded=False):
        st.caption(f"Mode: {mode}")
        if intent:
            st.caption(f"Intent: {intent.get('domain')}/{intent.get('topic')} — {intent.get('intent_label')}")
        st.caption(f"Nodes: {', '.join(nodes) if nodes else 'None (brute force)'}")

with st.sidebar:
    st.title("🧠 Enterprise KB")
    brand = st.selectbox("Brand filter", ["All", "ST", "TW", "TF", "WFM"])
    brand_val = None if brand == "All" else brand
    if st.button("New Session"):
        for key in ["messages"]:
            st.session_state.pop(key, None)
        st.rerun()

st.title("🧠 Enterprise Knowledge Base")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            r = msg["content"]
            st.write(r["answer"])
            confidence_badge(r["confidence"])
            show_sources(r["source_artifacts"])
            show_nav(r["hypergraph_nodes_used"], r["retrieval_mode"], r["intent"])

if prompt := st.chat_input("Ask about your knowledge base..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            try:
                result = get_client().query(prompt, brand=brand_val)
            except Exception as e:
                result = {"answer": f"Error: {e}", "confidence": "NOT_FOUND",
                          "source_artifacts": [], "hypergraph_nodes_used": [],
                          "retrieval_mode": "error", "intent": {}, "session_id": ""}
        st.write(result["answer"])
        confidence_badge(result["confidence"])
        show_sources(result["source_artifacts"])
        show_nav(result["hypergraph_nodes_used"], result["retrieval_mode"], result["intent"])
    st.session_state.messages.append({"role": "assistant", "content": result})
```

### Phase 13 Validation Test

Create `tests/test_phase13_interfaces.py`:

```python
"""Phase 13 Validation Tests"""
import pytest, os
SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

def test_agent_interface_importable():
    from interfaces.agent_interface import KBQueryClient
    assert KBQueryClient is not None

def test_rest_api_health():
    from fastapi.testclient import TestClient
    from interfaces.rest_api import app
    client = TestClient(app)
    # Health check without startup
    assert app is not None
```

---

## PHASE 14 — Full Integration Test

Create `tests/test_phase14_integration.py`:

```python
"""Phase 14 — Full End-to-End Integration"""
import pytest, os
SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

def test_hypergraph_navigation_without_api(tmp_path):
    from hypergraph.json_hypergraph import JSONHypergraph
    hg = JSONHypergraph(tmp_path / "graph", "hg")
    hg.create_node({
        "node_id": "node_ST_SO_Activation", "label": "ST Activation",
        "brand": "ST", "domain": "service_ordering", "feature": "Activation",
        "artifact_ids": ["uuid1", "uuid2"],
        "aliases": ["activation", "activate service", "new activation"],
        "confidence": "HIGH", "status": "ACTIVE", "is_temp": False,
        "created_at": "2026", "human_reviewed": True
    })
    for term in ["activation", "activate service"]:
        ids = hg.get_artifact_ids_for_query(term)
        assert "uuid1" in ids, f"Failed for: {term}"

def test_query_log_end_to_end(tmp_path):
    from core.config_loader import KBStoreConfig
    from cache.query_log import QueryLog
    config = KBStoreConfig()
    config._raw["query_log"]["path"] = str(tmp_path / "qlog.json")
    log = QueryLog(config)
    log.log("activation query", ["a1", "a2"], "answer here",
            "service_ordering", True, "s1", ["node_1"], "targeted")
    entries = log.get_recent(5)
    assert len(entries) == 1
    assert entries[0]["retrieval_mode"] == "targeted"
    stats = log.get_stats()
    assert stats["targeted"] == 1

@pytest.mark.skipif(SKIP_API, reason="Full API + LightRAG")
def test_full_kb_to_rag_flow(tmp_path):
    from core.config_loader import KBStoreConfig
    from core.kb_store_orchestrator import KBStoreOrchestrator

    config = KBStoreConfig()
    config._raw["output"]["kb_root"] = str(tmp_path / "KB")
    config._raw["registry"]["path"] = str(tmp_path / "registry")
    config._raw["hypergraph"]["path"] = str(tmp_path / "KB" / "graph")
    config._raw["hypergraph"]["notifications_file"] = str(tmp_path / "KB" / "graph" / "notifications.json")
    config._raw["ingestion_log"]["path"] = str(tmp_path / "registry" / "ingestion_log.json")
    config._raw["query_log"]["path"] = str(tmp_path / "KB" / "cache" / "query_log.json")
    config._raw["confluence"]["enabled"] = False
    lr_dir = str(tmp_path / "KB" / "graph" / "lightrag")
    config._raw.setdefault("embeddings", {}).update({"enabled": True, "lightrag_working_dir": lr_dir})
    config._raw.setdefault("rag", {}).update({"lightrag_working_dir": lr_dir})

    orchestrator = KBStoreOrchestrator(config)
    stats = orchestrator.run("tests/fixtures/sample_artifacts")
    assert stats["artifacts_inserted"] >= 1

    from hypergraph.hypergraph_factory import get_hypergraph
    hg = get_hypergraph(config)
    assert len(hg.list_all_nodes()) > 0
```

---

## COMPLETE QUICK START

```bash
# ONE TIME SETUP
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
pip install lightrag-hku
python -c "from lightrag import LightRAG; print('LightRAG OK')"

# RUN KB STORE ON BRD OUTPUT
python kb_store.py --path tests/fixtures/sample_artifacts

# RAG SETUP (run once after KB Store)
python rag/setup_rag.py --kb-root ./KB
# Then set embeddings.enabled: true in config

# EVERY BRD AGENT RUN (embedding auto-happens)
python kb_store.py --path ../brd_agent_poc/KB/new_repo/

# QUERY — HUMAN
streamlit run interfaces/streamlit_ui.py

# QUERY — AGENT
from interfaces.agent_interface import KBQueryClient
client = KBQueryClient()
result = client.query("how does activation work?", brand="ST")
print(result["answer"], result["confidence"])
print(result["source_artifacts"])

# QUERY — REST
python interfaces/rest_api.py
curl -X POST http://localhost:8000/query \
     -d '{"query": "activation flow?", "brand": "ST"}'
```

---

## SELF-CORRECTION GUIDE — PART 2

**LightRAG import fails:** `pip install lightrag-hku`. Fallback: set `rag.adapter: chromadb_direct`.

**Embedding dimension mismatch:** `all-MiniLM-L6-v2` = 384 dims. Update `embedding_dim` in `create_lightrag()` if you change model.

**LightRAG re-embeds everything:** Ensure `lightrag_working_dir` is the same path across all runs.

**Query always NOT_FOUND:** Verify `setup_rag.py` ran and `KB/graph/lightrag/` is populated. Check `embeddings.enabled: true`.

**Targeted search falls to brute force:** Hypergraph may have no nodes. Check `hg.list_all_nodes()`.

**Streamlit crashes:** Run from `kb_store/` directory. Ensure `.env` is loaded.

---

## PHASE 2 ROADMAP — FAQ CACHE

When `query_log.json` has accumulated enough entries:
- Build ChromaDB index of query embeddings from the log
- Similarity threshold 0.92 → return cached answer (zero RAG cost)
- Cache invalidation: KB Store marks stale when source artifact updates
- The log we have been writing since Phase 8 seeds this with no extra effort

---

*End of KB Store + RAG Component Build Instructions*
*Version: 2.0 | Part 1: KB Store (Phases 1-10) | Part 2: RAG (Phases 11-14)*
