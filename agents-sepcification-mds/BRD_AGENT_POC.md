# BRD Agentic Framework — POC Build Instructions
## For AI Coding Agents (Claude Code / GitHub Copilot / Claude CLI)

---

## IMPORTANT — READ FIRST

This document is the complete specification for building the BRD Agentic Framework POC. You are an AI coding agent. Your job is to read this entire document before writing a single line of code, then build phase by phase, test each phase before moving to the next, and self-correct if tests fail.

### Rules You Must Follow
- Read ALL sections before starting Phase 1
- Complete each phase fully before starting the next
- Run the validation test for each phase — if it fails, fix it before proceeding
- Never hardcode values that belong in config.yaml
- Never write agent logic inside tool files — agents call interfaces, interfaces call adapters
- When a tool is marked `enabled: false` in config, the stub adapter must return an empty result gracefully — never raise an exception
- All file paths come from config — never hardcode paths in agent code
- Every agent must write `human_feedback` field to state — even if empty string
- Commit working code after each phase passes validation

---

## ARCHITECTURE OVERVIEW

### What We Are Building
An autonomous 7-agent pipeline that takes a cloned Java Legacy application repository as input and produces a locked Business Requirements Document (BRD). The pipeline uses LangGraph for orchestration, Claude as the primary LLM, and stores all findings in a structured KB folder.

### The Big Picture

```
INPUT: Cloned Git repo (local path) + config.yaml
          |
          v
ORCHESTRATOR (LangGraph pipeline)
          |
    ------+------
    |            |
AGENT 1: Discovery & Scoping
    |
    +--parallel--+
    |            |
AGENT 2:      AGENT 3:
Journey       Business
Mapping       Rules
    |            |
    +-----+------+
          |
    AGENT 4: Gap Analysis
          |
    AGENT 5: Synthesis, Conflict Resolution & BRD Lock
          |
    +-----+------+
    |            |
AGENT 6:      AGENT 7:
Acceptance    Risk &
Criteria      Dependency
    |            |
    +-----+------+
          |
OUTPUT: KB/{repo_name}/  (JSON files + brd_final.docx)
```

### Key Design Principles
1. **Config drives everything** — models, tools, paths, sub-agents, all in config.yaml
2. **Agents call interfaces** — never adapters directly. Adapters are swapped via config.
3. **Stub adapter** — any disabled tool returns empty result, never crashes
4. **HITL is non-blocking** — CLI for simple decisions, file-based for complex reviews
5. **KB is organized** — by repo → component → task, with intuitive filenames
6. **State flows through LangGraph** — every agent reads context summary, writes findings, passes handoff notes

---

## PROJECT STRUCTURE

Build exactly this structure. Do not deviate.

```
brd_agent_poc/
│
├── config/
│   └── config.yaml                    # Master control plane — ALL configuration here
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                  # Base class all agents inherit from
│   ├── agent_1_discovery.py
│   ├── agent_2_journey.py
│   ├── agent_3_rules.py
│   ├── agent_4_gap.py
│   ├── agent_5_synthesis.py
│   ├── agent_6_ac.py
│   └── agent_7_risk.py
│
├── orchestrator/
│   ├── __init__.py
│   ├── pipeline.py                    # LangGraph pipeline definition
│   └── state.py                       # LangGraph state schema
│
├── tools/
│   ├── __init__.py
│   ├── interfaces/                    # Agents call ONLY these
│   │   ├── __init__.py
│   │   ├── repo_scanner_interface.py
│   │   ├── doc_parser_interface.py
│   │   ├── code_analyzer_interface.py
│   │   ├── vector_store_interface.py
│   │   └── ontology_extractor_interface.py
│   └── adapters/                      # Actual implementations — swapped via config
│       ├── __init__.py
│       ├── gitpython_adapter.py       # Repo scanning
│       ├── tree_sitter_adapter.py     # AST parsing
│       ├── semgrep_adapter.py         # Pattern-based rule extraction
│       ├── chromadb_adapter.py        # Vector store
│       ├── unstructured_adapter.py    # Document parsing
│       └── stub_adapter.py            # Returns empty for disabled tools
│
├── hitl/
│   ├── __init__.py
│   └── hitl_handler.py               # CLI display + file write/read
│
├── kb/
│   ├── __init__.py
│   └── kb_manager.py                 # KB write + ChromaDB indexing
│
├── output/
│   ├── __init__.py
│   └── brd_generator.py              # JSON Schema + python-docx BRD output
│
├── visualizer/
│   ├── __init__.py
│   └── generate_diagram.py           # Reads config → generates Mermaid diagram
│
├── config_loader/
│   ├── __init__.py
│   └── config_loader.py              # Loads config.yaml, resolves overrides, validates
│
├── KB/                               # Runtime KB output (created at runtime)
│   └── .gitkeep
│
├── HITL_PENDING/                     # HITL review files (created at runtime)
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── test_phase1_config.py
│   ├── test_phase2_state.py
│   ├── test_phase3_agents.py
│   ├── test_phase4_hitl.py
│   ├── test_phase5_pipeline.py
│   ├── test_phase6_output.py
│   └── test_phase7_integration.py
│
├── sample_repo/                       # Minimal Java sample for testing
│   └── src/
│       └── main/java/
│           └── SampleService.java
│
├── architecture.md                    # Generated Mermaid diagram — update after config changes
├── requirements.txt
├── .env.example                       # Template — never commit real .env
├── .gitignore
└── main.py                            # Entry point
```

---

## REQUIREMENTS.TXT

Create this file exactly as shown:

```
# Core orchestration
langgraph>=0.2.0
langchain>=0.3.0
langchain-anthropic>=0.3.0
langchain-unstructured>=0.1.0
anthropic>=0.40.0

# Code analysis
tree-sitter>=0.23.0
tree-sitter-java>=0.23.0
javalang>=0.13.0
semgrep>=1.90.0

# Repo scanning
gitpython>=3.1.40
gitparse>=0.1.0
pydriller>=2.6

# Document parsing
unstructured>=0.15.0
pdfplumber>=0.11.0
python-docx>=1.1.0

# Vector store & embeddings
chromadb>=0.5.0
sentence-transformers>=3.0.0

# State & config
pyyaml>=6.0.1
python-dotenv>=1.0.0
jsonschema>=4.23.0

# Observability
langsmith>=0.1.130

# CLI display
rich>=13.9.0
```

---

## .ENV.EXAMPLE

```bash
# Copy this to .env and fill in your values
# NEVER commit .env to git

ANTHROPIC_API_KEY=your_anthropic_api_key_here
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=brd_agent_poc

# These are disabled for POC — fill when available
JIRA_TOKEN=
CONFLUENCE_TOKEN=
UNSTRUCTURED_API_KEY=
```

---

## .GITIGNORE

```
.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
KB/
HITL_PENDING/
*.db
.DS_Store
node_modules/
```

---

## CONFIG.YAML — MASTER CONTROL PLANE

This is the most important file in the project. Every configuration decision lives here. Agent code must never hardcode anything that belongs here.

```yaml
# =============================================================================
# BRD AGENT POC — MASTER CONFIGURATION
# =============================================================================
# HOW TO USE THIS FILE:
#   1. Fill in resource paths for your local environment
#   2. Enable/disable tools using the enabled: true/false flag
#   3. Swap tool adapters by changing the adapter: field
#   4. Change models per agent using the llm: override
#   5. Run: python visualizer/generate_diagram.py to update architecture.md
#
# NEVER hardcode paths or credentials in agent code.
# ALL configuration belongs here.
# =============================================================================

# ── GLOBAL DEFAULTS ──────────────────────────────────────────────────────────
# All agents use these unless they specify an override in their section below.
global:
  llm_primary:
    provider: anthropic
    model: claude-sonnet-4-5          # Primary reasoning model
    temperature: 0.2
    max_tokens: 4096

  llm_secondary:
    provider: anthropic
    model: claude-haiku-4-5-20251001  # Faster/cheaper for high-volume extraction
    temperature: 0.1
    max_tokens: 2048

  vector_store:
    adapter: chromadb_adapter
    path: ./KB/chromadb_index
    collection_name: brd_poc
    embedding_model: all-MiniLM-L6-v2  # sentence-transformers model
    enabled: true

  state_store:
    type: langgraph
    event_log_type: sqlite
    event_log_path: ./KB/event_log.db

  kb_output:
    root: ./KB
    hitl_pending: ./HITL_PENDING

  observability:
    langsmith_enabled: true
    project_name: brd_agent_poc

  hitl:
    mode: cli             # cli = show in terminal and wait
                          # file = write to file and continue
                          # both = show in terminal AND write to file
    default_timeout: null # null = wait indefinitely

  confidence_thresholds:
    global_minimum: 0.5   # Below this — proceed but warn
    critical_minimum: 0.4 # Below this — trigger HITL

# ── RESOURCES ─────────────────────────────────────────────────────────────────
# Fill in these paths when setting up the project.
# Each resource has an enabled flag — set to false if not available.
resources:
  repo:
    path: ./sample_repo   # CHANGE THIS: absolute or relative path to cloned repo
    language: java        # java | python | typescript
    enabled: true

  test_suite:
    path: ./sample_repo   # CHANGE THIS: path to test directory (can be same as repo)
    format: auto          # auto = agent inspects and decides
                          # gherkin | selenium_java | pytest | junit
    enabled: true

  jira:
    base_url: ""          # e.g. https://yourcompany.atlassian.net
    project_key: ""       # e.g. MIGR
    token_env: JIRA_TOKEN # environment variable name containing the token
    enabled: false        # Set to true when Jira is connected

  confluence:
    base_url: ""
    space_key: ""
    token_env: CONFLUENCE_TOKEN
    enabled: false

  nsa_spec:
    path: ""              # Path to NSA OpenAPI/Swagger YAML or JSON spec
    enabled: false        # Set to true when NSA spec is available

  ontology_extractor:
    endpoint: ""          # Service endpoint when available
    enabled: false        # Returns empty stub when false

# ── AGENTS ────────────────────────────────────────────────────────────────────
# Each agent section defines:
#   - llm: which model to use (uses global if not specified)
#   - sub_agents: which sub-agents are active (set enabled: false to skip)
#   - tools: which tools are available (adapter + interface + resource)
#   - hitl: when and how to ask for human input
#   - kb_output: what files this agent writes to KB
agents:

  agent_1_discovery:
    name: "Discovery & Scoping Agent"
    description: "Scans repo, locates artifacts, defines scope boundaries"
    enabled: true
    llm: global.llm_primary
    sub_agents:
      intake_parser:
        enabled: true
        description: "Extracts component name, domain, priority from run config"
      repo_scanner:
        enabled: true
        description: "Scans repo file tree and structure"
      artifact_locator:
        enabled: true
        description: "Finds specs, docs, config files related to component"
      dependency_mapper:
        enabled: true
        description: "Maps upstream/downstream system connections"
      scope_boundary_writer:
        enabled: true
        description: "Produces formal scope definition"

    tools:
      repo_scanner:
        interface: repo_scanner_interface
        adapter: gitpython_adapter
        resource: repo
        enabled: true
      doc_parser:
        interface: doc_parser_interface
        adapter: unstructured_adapter
        resource: repo
        enabled: true
      jira_loader:
        interface: doc_parser_interface
        adapter: stub_adapter
        resource: jira
        enabled: false   # Enable when Jira connected
      confluence_loader:
        interface: doc_parser_interface
        adapter: stub_adapter
        resource: confluence
        enabled: false   # Enable when Confluence connected
      ontology_extractor:
        interface: ontology_extractor_interface
        adapter: stub_adapter
        resource: ontology_extractor
        enabled: false   # Enable when service available

    hitl:
      ambiguous_scope:
        trigger: "Scope boundary cannot be determined from available artifacts"
        type: cli
        options:
          - "Proceed with best-guess scope and flag as LOW confidence"
          - "Narrow scope to only what is explicitly documented"
          - "Expand scope to include likely related components"
        allow_freetext: true
      low_confidence_artifact:
        trigger: "Artifact found but confidence score below threshold"
        type: cli
        options:
          - "Include with LOW confidence flag"
          - "Exclude from this run"
          - "Flag for SME review"
        allow_freetext: true

    kb_output:
      scope_definition: "scope_definition.json"
      artifact_catalog: "artifact_catalog.json"
      dependency_map: "dependency_map.json"

  agent_2_journey:
    name: "Journey Mapping Agent"
    description: "Maps all user and system journeys from code, docs, and test suites"
    enabled: true
    llm: global.llm_primary

    sub_agents:
      actor_extractor:
        enabled: true
        description: "Identifies all users, systems, and external actors"
      entry_point_scanner:
        enabled: true
        description: "Finds all entry points — routes, endpoints, triggers"
      happy_path_builder:
        enabled: true
        description: "Constructs primary success journeys per actor"
      alternate_path_builder:
        enabled: true
        description: "Constructs error paths, alternates, edge cases"
      role_variant_detector:
        enabled: true
        description: "Finds behavior differences by role/permission"
      channel_variant_detector:
        enabled: true
        description: "Finds web/mobile/API/batch behavioral differences"
      test_suite_miner:
        enabled: true
        description: "Mines test suite for encoded journey behavior — the goldmine"
      journey_conflict_detector:
        enabled: true
        description: "Detects contradictions across sources"
      journey_gap_detector:
        enabled: true
        description: "Finds journeys in code/tests but not in docs"
      journey_inventory_writer:
        enabled: true
        description: "Produces structured journey catalog"

    tools:
      repo_scanner:
        interface: repo_scanner_interface
        adapter: gitpython_adapter
        resource: repo
        enabled: true
      code_analyzer:
        interface: code_analyzer_interface
        adapter: tree_sitter_adapter
        resource: repo
        enabled: true
      test_suite_parser:
        interface: code_analyzer_interface
        adapter: tree_sitter_adapter
        resource: test_suite
        enabled: true   # Parses Java Selenium test files
      ontology_extractor:
        interface: ontology_extractor_interface
        adapter: stub_adapter
        resource: ontology_extractor
        enabled: false

    hitl:
      journey_conflict:
        trigger: "Two sources describe same journey differently"
        type: cli
        options:
          - "Use source A (documentation)"
          - "Use source B (test suite / code)"
          - "Merge both into single journey with variants"
          - "Flag as unresolved conflict"
        allow_freetext: true
      tribal_knowledge:
        trigger: "Journey exists only in test suite — no documentation found"
        type: none
        action: "flag_low_confidence"  # Proceed automatically — flag it
      test_suite_only:
        trigger: "Journey found in tests but not in specs"
        type: none
        action: "flag_low_confidence"

    kb_output:
      journey_map: "journey_map.json"
      test_journey_coverage: "test_journey_coverage.json"
      journey_conflicts: "journey_conflicts.json"
      actors: "actors.json"

  agent_3_rules:
    name: "Business Rules Extraction Agent"
    description: "Extracts and plain-Englishes all business rules from code, config, docs"
    enabled: true
    llm: global.llm_secondary  # Haiku — high-volume extraction task

    sub_agents:
      code_rule_extractor:
        enabled: true
        description: "Extracts rules from Java code — conditionals, validations, calculations"
      config_rule_extractor:
        enabled: true
        description: "Extracts rules from config files, properties, feature flags"
      document_rule_extractor:
        enabled: true
        description: "Extracts stated rules from docs and specs"
      rule_normalizer:
        enabled: true
        description: "Translates technical rules into plain English"
      rule_deduplicator:
        enabled: true
        description: "Merges overlapping rules, distinguishes genuinely different ones"
      rule_journey_linker:
        enabled: true
        description: "Maps each rule to the journeys it governs"
      regulatory_flagger:
        enabled: true
        description: "Flags PII, financial, compliance-related rules"
      rules_catalog_writer:
        enabled: true
        description: "Produces structured rules catalog"

    tools:
      code_analyzer:
        interface: code_analyzer_interface
        adapter: semgrep_adapter
        resource: repo
        enabled: true   # Semgrep for pattern-based rule extraction
      ast_parser:
        interface: code_analyzer_interface
        adapter: tree_sitter_adapter
        resource: repo
        enabled: true   # Tree-sitter for structural analysis
      doc_parser:
        interface: doc_parser_interface
        adapter: unstructured_adapter
        resource: repo
        enabled: true
      ontology_extractor:
        interface: ontology_extractor_interface
        adapter: stub_adapter
        resource: ontology_extractor
        enabled: false

    hitl:
      ambiguous_rule_translation:
        trigger: "Rule extracted from code but plain English meaning is uncertain"
        type: file
        template: "rule_translation_review.txt"
        action: mark_pending
        allow_freetext: true
      regulatory_smell:
        trigger: "Rule appears to have regulatory or compliance implications"
        type: none
        action: "flag_regulatory"   # Auto-flag, do not block
      orphaned_rule:
        trigger: "Rule extracted but cannot be mapped to any known journey"
        type: none
        action: "flag_orphaned"     # Auto-flag, do not block

    kb_output:
      business_rules: "business_rules.json"
      regulatory_flags: "regulatory_flags.json"
      orphaned_rules: "orphaned_rules.json"

  agent_4_gap:
    name: "Gap Analysis Agent"
    description: "Compares Legacy behavior against NSA capabilities, classifies every gap"
    enabled: true
    llm: global.llm_primary

    sub_agents:
      nsa_spec_parser:
        enabled: false        # Disabled — no NSA spec available yet
        description: "Parses NSA API contracts and capability registry"
      journey_to_nsa_mapper:
        enabled: true
        description: "Maps each Legacy journey to NSA equivalent (best effort)"
      data_field_mapper:
        enabled: false        # Disabled — needs NSA schema
        description: "Maps Legacy data fields to NSA schema"
      rule_compatibility_checker:
        enabled: true
        description: "Checks whether NSA can enforce each business rule natively"
      gap_classifier:
        enabled: true
        description: "Classifies gaps: CLEAN_MAP / TRANSFORM / MISSING / DEFERRED"
      risk_scorer:
        enabled: true
        description: "Scores each gap by likelihood x business impact"
      gap_register_writer:
        enabled: true
        description: "Produces structured gap register"

    tools:
      nsa_spec_parser:
        interface: doc_parser_interface
        adapter: stub_adapter
        resource: nsa_spec
        enabled: false      # Returns empty — NSA spec not yet available
      code_analyzer:
        interface: code_analyzer_interface
        adapter: tree_sitter_adapter
        resource: repo
        enabled: true

    hitl:
      uncertain_gap_classification:
        trigger: "Cannot determine if gap is TRANSFORM or MISSING without NSA knowledge"
        type: file
        template: "gap_classification_review.txt"
        action: mark_pending
        allow_freetext: true
      blocking_gap:
        trigger: "Gap identified that will prevent migration without resolution"
        type: cli
        options:
          - "Mark as DEFERRED — address in later sprint"
          - "Mark as MISSING — must be built in NSA before migration"
          - "Provide NSA context (add free text below)"
          - "Mark as ACCEPTED_RISK — proceed with known limitation"
        allow_freetext: true

    kb_output:
      gap_analysis: "gap_analysis.json"
      blocking_gaps: "blocking_gaps.json"
      gap_register: "gap_register.json"

  agent_5_synthesis:
    name: "Synthesis, Conflict Resolution & BRD Lock Agent"
    description: "Cross-examines all agent outputs, resolves conflicts, assembles and locks BRD"
    enabled: true
    llm: global.llm_primary   # Always use primary — this is the most complex reasoning task

    sub_agents:
      cross_agent_conflict_detector:
        enabled: true
        description: "Detects conflicts between outputs of Agents 1-4"
      coverage_gap_detector:
        enabled: true
        description: "Finds journeys without rules, rules without journeys, etc."
      confidence_chain_validator:
        enabled: true
        description: "Ensures confidence scores are internally consistent across chains"
      assumption_dependency_mapper:
        enabled: true
        description: "Maps assumption dependencies — if A1 falls, what else collapses"
      terminology_harmonizer:
        enabled: true
        description: "Ensures consistent terminology across all four agent outputs"
      kg_conflict_resolver:
        enabled: false        # Phase 2 — KB query not yet available
        description: "Resolves conflicts using prior KB knowledge"
      evidence_weigher:
        enabled: true
        description: "Scores source credibility and recommends winner in conflicts"
      pattern_based_resolver:
        enabled: true
        description: "Applies known conflict resolution patterns"
      patch_dispatcher:
        enabled: true
        description: "Sends fix instructions back to relevant agent sub-agents"
      patch_validator:
        enabled: true
        description: "Confirms patches resolve the conflict"
      decision_package_builder:
        enabled: true
        description: "Builds structured human decision packages"
      human_router:
        enabled: true
        description: "Routes decision packages to the right human type"
      response_ingester:
        enabled: true
        description: "Parses human feedback back into the system"
      brd_section_updater:
        enabled: true
        description: "Applies decisions to BRD sections"
      section_assembler:
        enabled: true
        description: "Assembles all sections into coherent BRD structure"
      narrative_writer:
        enabled: true
        description: "Produces human-readable BRD narrative"
      structured_brd_writer:
        enabled: true
        description: "Produces machine-readable BRD JSON"
      consistency_final_check:
        enabled: true
        description: "Final pass for internal consistency"
      confidence_scorer:
        enabled: true
        description: "Calculates overall BRD confidence score"
      lock_gate:
        enabled: true
        description: "Enforces exit criteria before locking BRD"
      brd_version_stamper:
        enabled: true
        description: "Version stamps the locked BRD"

    tools:
      vector_store:
        interface: vector_store_interface
        adapter: chromadb_adapter
        resource: global.vector_store
        enabled: true

    hitl:
      unresolvable_conflict:
        trigger: "Cross-agent conflict cannot be resolved autonomously"
        type: file
        template: "conflict_resolution_review.txt"
        action: mark_pending
        allow_freetext: true
      high_risk_assumption_chain:
        trigger: "Assumption chain where failure of one cascades to multiple findings"
        type: cli
        options:
          - "Accept risk — proceed with chain as-is"
          - "Validate assumption — flag for SME confirmation"
          - "Defer — remove dependent sections from this BRD version"
        allow_freetext: true
      confidence_below_threshold:
        trigger: "Overall BRD confidence below critical minimum threshold"
        type: cli
        options:
          - "Proceed with LOW confidence warning stamped in BRD"
          - "Revisit specific low-confidence agent"
          - "Defer BRD — more information needed"
        allow_freetext: true
      blocking_gap_unresolved:
        trigger: "Blocking gap still unresolved after autonomous resolution attempts"
        type: cli
        options:
          - "Force proceed — stamp as known blocker in BRD"
          - "Mark section as DEFERRED"
          - "Escalate to architecture review"
        allow_freetext: true

    kb_output:
      conflict_register: "conflict_register.json"
      synthesis_decisions: "synthesis_decisions.json"
      brd_locked_json: "brd_final.json"
      brd_locked_docx: "brd_final.docx"

  agent_6_ac:
    name: "Acceptance Criteria Agent"
    description: "Converts journeys and rules into verifiable acceptance criteria"
    enabled: true
    llm: global.llm_secondary  # Haiku — structured conversion task

    sub_agents:
      journey_to_ac_converter:
        enabled: true
        description: "Converts each journey to Given/When/Then AC statements"
      rule_to_ac_converter:
        enabled: true
        description: "Converts each business rule to verifiable AC statements"
      ac_deduplicator:
        enabled: true
        description: "Merges duplicate or overlapping AC statements"
      ac_gap_checker:
        enabled: true
        description: "Ensures every journey and rule has at least one AC"
      gherkin_formatter:
        enabled: true
        description: "Formats ACs as Gherkin Scenario/Given/When/Then"
      regression_suite_comparator:
        enabled: true
        description: "Compares new ACs against existing test suite for coverage gaps"
      test_case_seeder:
        enabled: true
        description: "Suggests new test cases for uncovered ACs"

    tools:
      test_suite_parser:
        interface: code_analyzer_interface
        adapter: tree_sitter_adapter
        resource: test_suite
        enabled: true

    hitl:
      untestable_journey:
        trigger: "Journey has no clear verifiable outcome — AC cannot be written"
        type: none
        action: "flag_needs_validation"   # Proceed, mark AC as needing human validation

    kb_output:
      acceptance_criteria: "acceptance_criteria.json"
      acceptance_criteria_gherkin: "acceptance_criteria.feature"
      regression_gap_report: "regression_gap_report.json"
      new_test_suggestions: "new_test_suggestions.json"

  agent_7_risk:
    name: "Dependency & Risk Agent"
    description: "Maps dependencies and produces risk register"
    enabled: true
    llm: global.llm_secondary  # Haiku — structured analysis task

    sub_agents:
      system_dependency_mapper:
        enabled: true
        description: "Maps what this feature calls and what calls it"
      data_dependency_mapper:
        enabled: true
        description: "Maps shared data stores, tables, queues"
      team_dependency_mapper:
        enabled: false      # No org chart data available for POC
        description: "Maps team and vendor dependencies"
      regulatory_compliance_scanner:
        enabled: true
        description: "Scans for PII, financial, audit, consent requirements"
      risk_assessor:
        enabled: true
        description: "Scores risks by likelihood x business impact"
      risk_register_writer:
        enabled: true
        description: "Produces structured risk register"
      dependency_register_writer:
        enabled: true
        description: "Produces structured dependency register"

    tools:
      code_analyzer:
        interface: code_analyzer_interface
        adapter: tree_sitter_adapter
        resource: repo
        enabled: true
      doc_parser:
        interface: doc_parser_interface
        adapter: unstructured_adapter
        resource: repo
        enabled: true

    hitl:
      regulatory_flag_no_guidance:
        trigger: "Regulatory risk flagged but no compliance guidance available"
        type: none
        action: "flag_regulatory_unresolved"  # Auto-flag HIGH risk, do not block

    kb_output:
      risk_register: "risk_register.json"
      dependency_register: "dependency_register.json"
      regulatory_unresolved: "regulatory_unresolved.json"

# ── ORCHESTRATOR ──────────────────────────────────────────────────────────────
orchestrator:
  brd_version: "0.1.0-poc"

  pipeline:
    sequence:
      - agent_1_discovery
      - parallel:
          - agent_2_journey
          - agent_3_rules
      - agent_4_gap
      - agent_5_synthesis
      - parallel:
          - agent_6_ac
          - agent_7_risk

  confidence:
    global_minimum: 0.5
    critical_path_minimum: 0.4

  hitl:
    final_review_before_lock: true   # Show summary and ask human to confirm lock
```

---

## PHASE 1 — Config System + Project Scaffold + Static Visualizer

### Goal
Bootstrap the project. Config loads correctly. Every agent receives its configuration. Architecture diagram generates from config. Stub adapters work. Nothing crashes.

### Step 1.1 — Create Project Scaffold
Create all directories and empty `__init__.py` files. Create `.gitignore`, `.env.example`, `requirements.txt` as specified above. Create `KB/.gitkeep` and `HITL_PENDING/.gitkeep`.

### Step 1.2 — Config Loader

Create `config_loader/config_loader.py`:

```python
"""
Config Loader — reads config.yaml, resolves global overrides, validates structure.
This is the single source of truth for all configuration in the system.
"""
import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class ConfigLoader:
    """
    Loads and validates config.yaml.
    Resolves global defaults vs per-agent overrides.
    Provides typed access to all configuration values.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self._raw = self._load_raw()
        self._validate()

    def _load_raw(self) -> Dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _validate(self):
        """Validate required top-level keys exist."""
        required = ["global", "resources", "agents", "orchestrator"]
        for key in required:
            if key not in self._raw:
                raise ValueError(f"Missing required config section: {key}")

    def get_global(self) -> Dict:
        return self._raw.get("global", {})

    def get_resources(self) -> Dict:
        return self._raw.get("resources", {})

    def get_agent_config(self, agent_name: str) -> Dict:
        """
        Returns merged config for an agent.
        Per-agent values override globals where specified.
        """
        agents = self._raw.get("agents", {})
        if agent_name not in agents:
            raise ValueError(f"Agent not found in config: {agent_name}")

        agent_cfg = agents[agent_name]

        # Resolve LLM — use global if agent doesn't specify override
        llm_ref = agent_cfg.get("llm", "global.llm_primary")
        if isinstance(llm_ref, str) and llm_ref.startswith("global."):
            global_key = llm_ref.split(".", 1)[1]
            agent_cfg["llm_resolved"] = self._raw["global"].get(global_key, {})
        else:
            agent_cfg["llm_resolved"] = llm_ref

        return agent_cfg

    def get_orchestrator_config(self) -> Dict:
        return self._raw.get("orchestrator", {})

    def get_resource(self, resource_name: str) -> Dict:
        resources = self._raw.get("resources", {})
        if resource_name not in resources:
            return {"enabled": False}
        return resources[resource_name]

    def is_resource_enabled(self, resource_name: str) -> bool:
        return self.get_resource(resource_name).get("enabled", False)

    def is_agent_enabled(self, agent_name: str) -> bool:
        agents = self._raw.get("agents", {})
        return agents.get(agent_name, {}).get("enabled", False)

    def is_tool_enabled(self, agent_name: str, tool_name: str) -> bool:
        agent_cfg = self.get_agent_config(agent_name)
        tools = agent_cfg.get("tools", {})
        return tools.get(tool_name, {}).get("enabled", False)

    def is_sub_agent_enabled(self, agent_name: str, sub_agent_name: str) -> bool:
        agent_cfg = self.get_agent_config(agent_name)
        sub_agents = agent_cfg.get("sub_agents", {})
        return sub_agents.get(sub_agent_name, {}).get("enabled", False)

    def get_kb_output_path(self, agent_name: str, output_key: str,
                           repo_name: str, component_name: str = "") -> Path:
        """Returns the full KB output path for an agent's output file."""
        root = Path(self._raw["global"]["kb_output"]["root"])
        agent_cfg = self.get_agent_config(agent_name)
        kb_outputs = agent_cfg.get("kb_output", {})
        filename = kb_outputs.get(output_key, f"{output_key}.json")

        if component_name:
            return root / repo_name / component_name / filename
        return root / repo_name / "application_level" / filename

    def get_api_key(self, env_var: str) -> Optional[str]:
        """Read API key from environment — never from config."""
        return os.getenv(env_var)

    def get_tool_adapter(self, agent_name: str, tool_name: str) -> str:
        """Returns the adapter name for a given agent tool."""
        agent_cfg = self.get_agent_config(agent_name)
        tools = agent_cfg.get("tools", {})
        tool = tools.get(tool_name, {})
        if not tool.get("enabled", False):
            return "stub_adapter"
        return tool.get("adapter", "stub_adapter")

    @property
    def raw(self) -> Dict:
        return self._raw
```

### Step 1.3 — Stub Adapter

Create `tools/adapters/stub_adapter.py`:

```python
"""
Stub Adapter — returns empty results for any disabled tool.
Never raises exceptions. Logs that the tool is disabled.
"""
from typing import Any
from rich.console import Console

console = Console()

class StubAdapter:
    """
    Universal stub for disabled tools.
    All methods return appropriate empty values based on return type hints.
    Agent code should handle empty returns gracefully.
    """

    def __init__(self, tool_name: str = "unknown", resource_name: str = "unknown"):
        self.tool_name = tool_name
        self.resource_name = resource_name
        self._log_disabled()

    def _log_disabled(self):
        console.print(
            f"[dim]⚪ Tool [{self.tool_name}] is disabled "
            f"(resource: {self.resource_name}). Returning empty result.[/dim]"
        )

    def __getattr__(self, name: str):
        """Catch all method calls and return empty results."""
        def stub_method(*args, **kwargs) -> Any:
            return {}
        return stub_method

    # Explicit stubs for known interface methods
    def scan_directory(self, path: str) -> dict:
        return {"files": [], "directories": [], "disabled": True}

    def get_file(self, path: str) -> str:
        return ""

    def find_pattern(self, pattern: str) -> list:
        return []

    def parse_document(self, path: str) -> dict:
        return {"content": "", "sections": [], "disabled": True}

    def extract_sections(self, path: str) -> list:
        return []

    def analyze_file(self, path: str) -> dict:
        return {"classes": [], "methods": [], "disabled": True}

    def extract_rules(self, path: str) -> list:
        return []

    def find_conditionals(self, path: str) -> list:
        return []

    def index(self, doc: dict, metadata: dict) -> None:
        return None

    def search(self, query: str, top_k: int = 5) -> list:
        return []

    def extract(self, text: str) -> dict:
        return {}

    def normalize(self, term: str) -> str:
        return term  # Return as-is if disabled
```

### Step 1.4 — Tool Interfaces

Create each interface file in `tools/interfaces/`. Each interface defines the contract that all adapters must implement.

**`tools/interfaces/repo_scanner_interface.py`**:
```python
"""
Repo Scanner Interface — contract for all repo scanning adapters.
Agents call these methods. Never call adapters directly.
"""
from abc import ABC, abstractmethod
from typing import Dict, List

class RepoScannerInterface(ABC):

    @abstractmethod
    def scan_directory(self, path: str) -> Dict:
        """
        Scan directory and return file tree.
        Returns: {
            "files": [{"path": str, "extension": str, "size_bytes": int}],
            "directories": [str],
            "language_stats": {"java": {"files": int, "bytes": int}},
            "total_files": int
        }
        """
        pass

    @abstractmethod
    def get_file(self, path: str) -> str:
        """Read and return file contents as string."""
        pass

    @abstractmethod
    def find_pattern(self, pattern: str, path: str = None) -> List[Dict]:
        """
        Find files or content matching pattern.
        Returns: [{"file": str, "matches": [str], "line_numbers": [int]}]
        """
        pass

    @abstractmethod
    def get_file_tree(self, path: str) -> List[str]:
        """Return flat list of all file paths under directory."""
        pass
```

**`tools/interfaces/code_analyzer_interface.py`**:
```python
"""
Code Analyzer Interface — contract for all code analysis adapters.
"""
from abc import ABC, abstractmethod
from typing import Dict, List

class CodeAnalyzerInterface(ABC):

    @abstractmethod
    def analyze_file(self, path: str) -> Dict:
        """
        Analyze a source code file and return structural information.
        Returns: {
            "classes": [{"name": str, "methods": [str], "line": int}],
            "methods": [{"name": str, "parameters": [str], "return_type": str,
                        "annotations": [str], "body_lines": [str]}],
            "imports": [str],
            "language": str
        }
        """
        pass

    @abstractmethod
    def extract_rules(self, path: str) -> List[Dict]:
        """
        Extract business rule candidates from a file.
        Returns: [{
            "type": "conditional|validation|calculation|eligibility",
            "code_snippet": str,
            "line_number": int,
            "context": str,  # surrounding code for LLM interpretation
            "complexity": "simple|complex"
        }]
        """
        pass

    @abstractmethod
    def find_conditionals(self, path: str) -> List[Dict]:
        """
        Find all conditional statements (if/else, switch, ternary).
        Returns: [{"code": str, "line": int, "type": str}]
        """
        pass

    @abstractmethod
    def find_test_methods(self, path: str) -> List[Dict]:
        """
        Find all test methods in a test file.
        Returns: [{
            "name": str,
            "annotations": [str],  # @Test, @Before, etc.
            "body": str,
            "assertions": [str],
            "page_objects_used": [str]
        }]
        """
        pass
```

**`tools/interfaces/doc_parser_interface.py`**:
```python
from abc import ABC, abstractmethod
from typing import Dict, List

class DocParserInterface(ABC):

    @abstractmethod
    def parse_document(self, path: str) -> Dict:
        """
        Parse document and return structured content.
        Returns: {
            "title": str,
            "content": str,
            "sections": [{"heading": str, "content": str}],
            "metadata": {"file_type": str, "page_count": int}
        }
        """
        pass

    @abstractmethod
    def extract_sections(self, path: str) -> List[Dict]:
        """Extract sections/headings as separate chunks."""
        pass
```

**`tools/interfaces/vector_store_interface.py`**:
```python
from abc import ABC, abstractmethod
from typing import Dict, List

class VectorStoreInterface(ABC):

    @abstractmethod
    def index(self, doc: Dict, metadata: Dict) -> None:
        """Index a document with metadata for later retrieval."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5,
               filter_metadata: Dict = None) -> List[Dict]:
        """
        Search for similar documents.
        Returns: [{"content": str, "metadata": Dict, "score": float}]
        """
        pass
```

**`tools/interfaces/ontology_extractor_interface.py`**:
```python
from abc import ABC, abstractmethod
from typing import Dict

class OntologyExtractorInterface(ABC):

    @abstractmethod
    def extract(self, text: str) -> Dict:
        """
        Extract domain vocabulary from text.
        Returns: {"terms": [{"term": str, "definition": str, "domain": str}]}
        """
        pass

    @abstractmethod
    def normalize(self, term: str) -> str:
        """Normalize a term against known ontology. Returns canonical form."""
        pass
```

### Step 1.5 — Tool Factory

Create `tools/tool_factory.py`:

```python
"""
Tool Factory — instantiates the correct adapter for a given tool,
based on configuration. Agents call this to get their tools.
"""
from config_loader.config_loader import ConfigLoader
from tools.adapters.stub_adapter import StubAdapter

def get_tool(agent_name: str, tool_name: str,
             config: ConfigLoader) -> object:
    """
    Returns the correct adapter instance for a given agent tool.
    If tool is disabled or adapter not found — returns StubAdapter.
    """
    agent_cfg = config.get_agent_config(agent_name)
    tools = agent_cfg.get("tools", {})
    tool_cfg = tools.get(tool_name, {})

    if not tool_cfg.get("enabled", False):
        return StubAdapter(tool_name=tool_name,
                          resource_name=tool_cfg.get("resource", "unknown"))

    adapter_name = tool_cfg.get("adapter", "stub_adapter")
    resource_name = tool_cfg.get("resource", "")
    resource_cfg = config.get_resource(resource_name) if resource_name else {}

    try:
        adapter = _load_adapter(adapter_name, resource_cfg)
        return adapter
    except Exception as e:
        print(f"⚠️  Failed to load adapter [{adapter_name}]: {e}. Using stub.")
        return StubAdapter(tool_name=tool_name, resource_name=resource_name)

def _load_adapter(adapter_name: str, resource_cfg: dict) -> object:
    """Dynamically imports and instantiates the adapter."""
    adapter_map = {
        "gitpython_adapter": "tools.adapters.gitpython_adapter.GitPythonAdapter",
        "tree_sitter_adapter": "tools.adapters.tree_sitter_adapter.TreeSitterAdapter",
        "semgrep_adapter": "tools.adapters.semgrep_adapter.SemgrepAdapter",
        "chromadb_adapter": "tools.adapters.chromadb_adapter.ChromaDBAdapter",
        "unstructured_adapter": "tools.adapters.unstructured_adapter.UnstructuredAdapter",
        "stub_adapter": "tools.adapters.stub_adapter.StubAdapter",
    }

    if adapter_name not in adapter_map:
        raise ValueError(f"Unknown adapter: {adapter_name}")

    class_path = adapter_map[adapter_name]
    module_path, class_name = class_path.rsplit(".", 1)

    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(resource_cfg=resource_cfg)
```

### Step 1.6 — Static Visualizer

Create `visualizer/generate_diagram.py`:

```python
"""
Generate Architecture Diagram from config.yaml
Run: python visualizer/generate_diagram.py
Output: architecture.md (Mermaid diagram)

This shows the current state of the framework — active agents,
their tools, models, and connections. Disabled tools shown in grey.
Re-run after any config change to keep architecture.md current.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader.config_loader import ConfigLoader
from rich.console import Console

console = Console()

def generate_mermaid(config: ConfigLoader) -> str:
    raw = config.raw
    agents = raw.get("agents", {})
    orchestrator = raw.get("orchestrator", {})
    sequence = orchestrator.get("pipeline", {}).get("sequence", [])

    lines = ["```mermaid", "graph TD"]
    lines.append("  INTAKE([🚀 Migration Request]) --> ORCH[Orchestrator]")
    lines.append("")

    # Colors per agent
    colors = {
        "agent_1_discovery": "#1B3A5C",
        "agent_2_journey": "#1F6B75",
        "agent_3_rules": "#5B4A8A",
        "agent_4_gap": "#2E7D4F",
        "agent_5_synthesis": "#7D5A00",
        "agent_6_ac": "#1F6B75",
        "agent_7_risk": "#8B1A1A",
    }

    short_names = {
        "agent_1_discovery": "AG1\nDiscovery",
        "agent_2_journey": "AG2\nJourney Mapping",
        "agent_3_rules": "AG3\nBusiness Rules",
        "agent_4_gap": "AG4\nGap Analysis",
        "agent_5_synthesis": "AG5\nSynthesis & Lock",
        "agent_6_ac": "AG6\nAcceptance Criteria",
        "agent_7_risk": "AG7\nRisk & Dependency",
    }

    # Build pipeline connections from sequence
    prev = "ORCH"
    for step in sequence:
        if isinstance(step, dict) and "parallel" in step:
            parallel_agents = step["parallel"]
            for agent_name in parallel_agents:
                lines.append(f"  {prev} --> {agent_name.upper()}")
            prev_list = [a.upper() for a in parallel_agents]
            # Connect parallel agents to next
            next_step_idx = sequence.index(step) + 1
            if next_step_idx < len(sequence):
                next_step = sequence[next_step_idx]
                if isinstance(next_step, str):
                    for p in prev_list:
                        lines.append(f"  {p} --> {next_step.upper()}")
        elif isinstance(step, str):
            lines.append(f"  {prev} --> {step.upper()}")
            prev = step.upper()

    lines.append("")
    lines.append("  AG7_RISK --> KB[(📁 KB Storage)]")
    lines.append("  AG6_AC --> KB")
    lines.append("  AG5_SYNTHESIS --> KB")
    lines.append("")

    # Agent detail nodes
    for agent_name, agent_cfg in agents.items():
        if not agent_cfg.get("enabled", False):
            continue

        model = agent_cfg.get("llm", "global.llm_primary")
        if "secondary" in str(model):
            model_label = "🔵 Claude Haiku"
        else:
            model_label = "🟢 Claude Sonnet"

        # Count active vs disabled tools
        tools = agent_cfg.get("tools", {})
        active_tools = [t for t, v in tools.items() if v.get("enabled", False)]
        disabled_tools = [t for t, v in tools.items() if not v.get("enabled", False)]

        tool_text = "\\n".join([f"✓ {t}" for t in active_tools[:4]])
        if disabled_tools:
            tool_text += "\\n" + "\\n".join([f"✗ {t}" for t in disabled_tools[:2]])

        agent_id = agent_name.upper()
        lines.append(f'  {agent_id} --> {agent_id}_TOOLS["{tool_text}"]')
        lines.append(f'  {agent_id} --> {agent_id}_MODEL["{model_label}"]')
        lines.append("")

    # Style active agents
    for agent_name, color in colors.items():
        if agents.get(agent_name, {}).get("enabled", False):
            lines.append(f"  style {agent_name.upper()} fill:{color},color:#fff")

    lines.append("  style KB fill:#2C3E50,color:#fff")
    lines.append("  style ORCH fill:#0D1B2A,color:#fff")
    lines.append("  style INTAKE fill:#1A5276,color:#fff")
    lines.append("```")

    return "\n".join(lines)


def generate_tool_summary(config: ConfigLoader) -> str:
    """Generate a text summary of enabled vs disabled tools per agent."""
    raw = config.raw
    agents = raw.get("agents", {})
    lines = ["\n## Tool Status Per Agent\n"]
    lines.append("| Agent | Tool | Status | Adapter |")
    lines.append("|-------|------|--------|---------|")

    for agent_name, agent_cfg in agents.items():
        if not agent_cfg.get("enabled", False):
            continue
        tools = agent_cfg.get("tools", {})
        for tool_name, tool_cfg in tools.items():
            status = "✅ Enabled" if tool_cfg.get("enabled") else "⚫ Disabled"
            adapter = tool_cfg.get("adapter", "stub_adapter")
            lines.append(f"| {agent_name} | {tool_name} | {status} | {adapter} |")

    return "\n".join(lines)


def main():
    console.print("\n[bold blue]🔧 Generating Architecture Diagram from config.yaml...[/bold blue]\n")

    config = ConfigLoader()

    mermaid = generate_mermaid(config)
    tool_summary = generate_tool_summary(config)

    output = f"""# BRD Agent Framework — Architecture Diagram
*Auto-generated from config/config.yaml — re-run `python visualizer/generate_diagram.py` after config changes*

## Pipeline Flow

{mermaid}

{tool_summary}

## Legend
- ✅ Enabled — tool is connected and active
- ⚫ Disabled — tool returns empty stub (not connected yet)
- 🟢 Claude Sonnet — primary reasoning model
- 🔵 Claude Haiku — secondary model for high-volume tasks
"""

    output_path = Path("architecture.md")
    output_path.write_text(output)
    console.print(f"[green]✅ Architecture diagram written to: {output_path}[/green]")
    console.print(f"[dim]Open architecture.md in GitHub or any Mermaid renderer to view.[/dim]\n")


if __name__ == "__main__":
    main()
```

### Step 1.7 — Sample Repo for Testing

Create `sample_repo/src/main/java/SampleService.java`:

```java
package com.legacy.sample;

import java.util.Date;

/**
 * Sample Legacy Java Service for POC testing.
 * This file gives agents something to analyze.
 */
public class SampleService {

    private static final double PREMIUM_THRESHOLD = 1000.00;
    private static final int MAX_RETRY_COUNT = 3;

    /**
     * Process a payment transaction.
     * Business Rule: Transactions over $1000 require manager approval.
     */
    public boolean processPayment(String customerId, double amount, String type) {
        if (customerId == null || customerId.isEmpty()) {
            throw new IllegalArgumentException("Customer ID cannot be null or empty");
        }

        if (amount <= 0) {
            return false; // Invalid amount
        }

        if (amount > PREMIUM_THRESHOLD) {
            // BR-001: High value transactions need approval
            boolean approved = requestManagerApproval(customerId, amount);
            if (!approved) {
                return false;
            }
        }

        if ("SUBSCRIPTION".equals(type)) {
            return processSubscription(customerId, amount);
        } else if ("ONE_TIME".equals(type)) {
            return processOneTimePayment(customerId, amount);
        }

        return false;
    }

    /**
     * Check customer eligibility for subscription.
     * Business Rule: Customer must be active and have valid payment method.
     */
    public boolean checkEligibility(String customerId, String planId) {
        Customer customer = getCustomer(customerId);
        if (customer == null) {
            return false;
        }

        if (!customer.isActive()) {
            return false;
        }

        if (customer.hasOutstandingBalance()) {
            return false; // BR-002: Outstanding balance blocks subscription
        }

        Plan plan = getPlan(planId);
        if (plan == null || !plan.isAvailable()) {
            return false;
        }

        return true;
    }

    private boolean requestManagerApproval(String customerId, double amount) {
        // Stub for POC
        return true;
    }

    private boolean processSubscription(String customerId, double amount) {
        return true;
    }

    private boolean processOneTimePayment(String customerId, double amount) {
        return true;
    }

    private Customer getCustomer(String id) { return null; }
    private Plan getPlan(String id) { return null; }
}

class Customer {
    public boolean isActive() { return true; }
    public boolean hasOutstandingBalance() { return false; }
}

class Plan {
    public boolean isAvailable() { return true; }
}
```

Also create `sample_repo/src/test/java/SampleServiceTest.java`:

```java
package com.legacy.sample;

import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Selenium/JUnit test cases for SampleService.
 * These encode the journeys agent 2 will mine.
 */
public class SampleServiceTest {

    @Test
    public void testProcessPayment_StandardAmount_Success() {
        // Journey: Standard payment happy path
        SampleService service = new SampleService();
        boolean result = service.processPayment("CUST001", 500.00, "ONE_TIME");
        assertTrue("Standard payment should succeed", result);
    }

    @Test
    public void testProcessPayment_HighValue_RequiresApproval() {
        // Journey: High value payment requires manager approval
        SampleService service = new SampleService();
        boolean result = service.processPayment("CUST001", 1500.00, "ONE_TIME");
        // BR-001: High value threshold validation
        assertTrue("High value payment with approval should succeed", result);
    }

    @Test
    public void testProcessPayment_NullCustomer_Fails() {
        // Journey: Invalid customer error path
        SampleService service = new SampleService();
        try {
            service.processPayment(null, 100.00, "ONE_TIME");
            fail("Should throw exception for null customer");
        } catch (IllegalArgumentException e) {
            // Expected
        }
    }

    @Test
    public void testCheckEligibility_ActiveCustomer_NoBalance_Success() {
        // Journey: Eligible customer subscription check
        SampleService service = new SampleService();
        boolean result = service.checkEligibility("CUST001", "PLAN_BASIC");
        assertTrue("Active customer with no balance should be eligible", result);
    }

    @Test
    public void testProcessPayment_ZeroAmount_Fails() {
        // Journey: Edge case — zero amount payment
        SampleService service = new SampleService();
        boolean result = service.processPayment("CUST001", 0.00, "ONE_TIME");
        assertFalse("Zero amount payment should fail", result);
    }
}
```

### Step 1.8 — Phase 1 Validation Test

Create `tests/test_phase1_config.py`:

```python
"""
Phase 1 Validation Tests
Run: pytest tests/test_phase1_config.py -v
All tests must pass before proceeding to Phase 2.
"""
import pytest
from pathlib import Path
from config_loader.config_loader import ConfigLoader
from tools.adapters.stub_adapter import StubAdapter
from tools.tool_factory import get_tool


def test_config_file_exists():
    assert Path("config/config.yaml").exists(), "config.yaml must exist"

def test_config_loads_without_error():
    config = ConfigLoader()
    assert config is not None

def test_config_has_required_sections():
    config = ConfigLoader()
    raw = config.raw
    for section in ["global", "resources", "agents", "orchestrator"]:
        assert section in raw, f"Missing section: {section}"

def test_all_seven_agents_present():
    config = ConfigLoader()
    agents = config.raw.get("agents", {})
    expected = [
        "agent_1_discovery", "agent_2_journey", "agent_3_rules",
        "agent_4_gap", "agent_5_synthesis", "agent_6_ac", "agent_7_risk"
    ]
    for agent in expected:
        assert agent in agents, f"Missing agent: {agent}"

def test_each_agent_receives_llm_config():
    config = ConfigLoader()
    for agent_name in ["agent_1_discovery", "agent_2_journey", "agent_3_rules",
                       "agent_4_gap", "agent_5_synthesis", "agent_6_ac", "agent_7_risk"]:
        agent_cfg = config.get_agent_config(agent_name)
        assert "llm_resolved" in agent_cfg, f"{agent_name} missing resolved LLM config"
        assert "model" in agent_cfg["llm_resolved"], f"{agent_name} LLM config missing model"

def test_each_agent_has_kb_output_defined():
    config = ConfigLoader()
    for agent_name in ["agent_1_discovery", "agent_2_journey", "agent_3_rules",
                       "agent_4_gap", "agent_5_synthesis", "agent_6_ac", "agent_7_risk"]:
        agent_cfg = config.get_agent_config(agent_name)
        assert "kb_output" in agent_cfg, f"{agent_name} missing kb_output definition"
        assert len(agent_cfg["kb_output"]) > 0, f"{agent_name} kb_output is empty"

def test_stub_adapter_never_raises():
    stub = StubAdapter(tool_name="test_tool", resource_name="test_resource")
    # All methods should return empty, never raise
    assert stub.scan_directory("/any/path") == {"files": [], "directories": [], "disabled": True}
    assert stub.get_file("/any/file.java") == ""
    assert stub.find_pattern("anything") == []
    assert stub.parse_document("/any/doc.pdf") == {"content": "", "sections": [], "disabled": True}
    assert stub.extract_rules("/any/file.java") == []
    assert stub.search("anything", 5) == []
    assert stub.normalize("any term") == "any term"

def test_disabled_tool_returns_stub():
    config = ConfigLoader()
    # ontology extractor is disabled in default config
    tool = get_tool("agent_1_discovery", "ontology_extractor", config)
    assert isinstance(tool, StubAdapter)

def test_enabled_tool_does_not_return_stub():
    config = ConfigLoader()
    # repo_scanner is enabled in default config
    tool = get_tool("agent_1_discovery", "repo_scanner", config)
    assert not isinstance(tool, StubAdapter)

def test_kb_directories_exist_or_are_created():
    config = ConfigLoader()
    kb_root = Path(config.raw["global"]["kb_output"]["root"])
    hitl_root = Path(config.raw["global"]["kb_output"]["hitl_pending"])
    # These will be created at runtime — just check they can be created
    kb_root.mkdir(parents=True, exist_ok=True)
    hitl_root.mkdir(parents=True, exist_ok=True)
    assert kb_root.exists()
    assert hitl_root.exists()

def test_resource_enabled_flag_works():
    config = ConfigLoader()
    assert config.is_resource_enabled("repo") == True
    assert config.is_resource_enabled("jira") == False
    assert config.is_resource_enabled("nsa_spec") == False

def test_visualizer_generates_architecture_md():
    from visualizer.generate_diagram import generate_mermaid
    config = ConfigLoader()
    diagram = generate_mermaid(config)
    assert "graph TD" in diagram
    assert "ORCH" in diagram
    assert "KB" in diagram
```

### Phase 1 Self-Correction Instructions
If any test fails:
1. `test_config_loads_without_error` — check YAML syntax in config.yaml
2. `test_each_agent_receives_llm_config` — ensure `_resolve_llm` in ConfigLoader handles `global.llm_primary` and `global.llm_secondary` string references
3. `test_disabled_tool_returns_stub` — check `get_tool` in tool_factory returns StubAdapter when `enabled: false`
4. `test_enabled_tool_does_not_return_stub` — check gitpython_adapter.py exists and imports correctly

---

## PHASE 2 — State Store + KB Storage + LangGraph Pipeline Skeleton

### Goal
LangGraph pipeline runs end-to-end with placeholder agents. State passes correctly between agents. SQLite event log writes. KB folder structure creates on first run.

### Step 2.1 — LangGraph State Schema

Create `orchestrator/state.py`:

```python
"""
LangGraph State Schema — the shared memory passed between all agents.
Every agent reads this on activation and writes updates back.
"""
from typing import TypedDict, List, Dict, Optional, Annotated
import operator

class HumanFeedback(TypedDict):
    agent_1: str
    agent_2: str
    agent_3: str
    agent_4: str
    agent_5: str
    agent_6: str
    agent_7: str

class Warning(TypedDict):
    agent: str
    type: str
    message: str
    confidence: float

class HandoffNotes(TypedDict):
    from_agent: str
    key_findings: List[str]
    watch_out_for: List[str]
    confidence_flags: List[str]

class OpenItem(TypedDict):
    type: str  # question | conflict | assumption | blocker
    agent: str
    description: str
    priority: str  # HIGH | MEDIUM | LOW
    status: str  # open | pending_human | resolved

class BRDState(TypedDict):
    # ── RUN IDENTITY ─────────────────────────────────────────
    run_id: str
    repo_name: str
    repo_path: str
    component_name: str
    brd_version: str
    current_agent: str
    overall_confidence: float

    # ── ROLLING SUMMARY — updated by each agent ───────────────
    scope: Dict                  # Agent 1 writes this
    artifact_catalog: List[Dict] # Agent 1 writes this
    journey_summary: Dict        # Agent 2 writes this
    rules_summary: Dict          # Agent 3 writes this
    gaps_summary: Dict           # Agent 4 writes this
    synthesis_summary: Dict      # Agent 5 writes this
    ac_summary: Dict             # Agent 6 writes this
    risk_summary: Dict           # Agent 7 writes this

    # ── AGENT OUTPUTS — full structured outputs ───────────────
    scope_definition: Dict
    artifact_catalog_full: List[Dict]
    dependency_map: Dict
    journey_inventory: List[Dict]
    test_journey_matrix: Dict
    journey_conflicts: List[Dict]
    business_rules: List[Dict]
    regulatory_flags: List[Dict]
    orphaned_rules: List[Dict]
    gap_analysis: List[Dict]
    blocking_gaps: List[Dict]
    conflict_register: List[Dict]
    synthesis_decisions: List[Dict]
    acceptance_criteria: List[Dict]
    regression_gap_report: Dict
    risk_register: List[Dict]
    dependency_register: List[Dict]

    # ── HANDOFF NOTES — each agent briefs the next ────────────
    handoff_notes: HandoffNotes

    # ── HUMAN FEEDBACK — always present, sometimes empty ──────
    human_feedback: HumanFeedback

    # ── HITL STATUS ───────────────────────────────────────────
    hitl_pending: List[Dict]     # Items awaiting human review

    # ── WARNINGS — accumulated across all agents ──────────────
    warnings: Annotated[List[Warning], operator.add]  # Append-only

    # ── OPEN ITEMS ────────────────────────────────────────────
    open_items: List[OpenItem]

    # ── BRD OUTPUT ───────────────────────────────────────────
    brd_locked: bool
    brd_json_path: str
    brd_docx_path: str


def get_initial_state(run_id: str, repo_path: str,
                      repo_name: str, brd_version: str) -> BRDState:
    """Returns a fresh initial state for a new BRD run."""
    return BRDState(
        run_id=run_id,
        repo_name=repo_name,
        repo_path=repo_path,
        component_name="",
        brd_version=brd_version,
        current_agent="",
        overall_confidence=0.0,

        scope={},
        artifact_catalog=[],
        journey_summary={},
        rules_summary={},
        gaps_summary={},
        synthesis_summary={},
        ac_summary={},
        risk_summary={},

        scope_definition={},
        artifact_catalog_full=[],
        dependency_map={},
        journey_inventory=[],
        test_journey_matrix={},
        journey_conflicts=[],
        business_rules=[],
        regulatory_flags=[],
        orphaned_rules=[],
        gap_analysis=[],
        blocking_gaps=[],
        conflict_register=[],
        synthesis_decisions=[],
        acceptance_criteria=[],
        regression_gap_report={},
        risk_register=[],
        dependency_register=[],

        handoff_notes=HandoffNotes(
            from_agent="",
            key_findings=[],
            watch_out_for=[],
            confidence_flags=[]
        ),

        human_feedback=HumanFeedback(
            agent_1="", agent_2="", agent_3="",
            agent_4="", agent_5="", agent_6="", agent_7=""
        ),

        hitl_pending=[],
        warnings=[],
        open_items=[],
        brd_locked=False,
        brd_json_path="",
        brd_docx_path=""
    )
```

### Step 2.2 — Event Log

Create `orchestrator/event_log.py`:

```python
"""
SQLite Event Log — append-only audit trail for every agent action.
Every finding, decision, HITL trigger, and tool call is logged here.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

class EventLog:

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    is_hitl INTEGER DEFAULT 0,
                    is_kb_candidate INTEGER DEFAULT 0,
                    linked_event_ids TEXT DEFAULT '[]'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_run_agent
                ON events (run_id, agent_id)
            """)
            conn.commit()

    def log(self, run_id: str, agent_id: str, event_type: str,
            payload: Dict, confidence: float = 0.0,
            is_hitl: bool = False, is_kb_candidate: bool = False,
            linked_event_ids: list = None) -> str:
        """Log an event. Returns the event_id."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                event_id, timestamp, run_id, agent_id, event_type,
                json.dumps(payload), confidence,
                int(is_hitl), int(is_kb_candidate),
                json.dumps(linked_event_ids or [])
            ))
            conn.commit()
        return event_id

    def get_events_for_run(self, run_id: str, agent_id: str = None,
                           event_type: str = None) -> list:
        """Query events with optional filters."""
        query = "SELECT * FROM events WHERE run_id = ?"
        params = [run_id]
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
```

### Step 2.3 — KB Manager

Create `kb/kb_manager.py`:

```python
"""
KB Manager — writes agent outputs to KB folder structure.
Also indexes documents in ChromaDB for future retrieval.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()

class KBManager:

    def __init__(self, config):
        self.config = config
        self.kb_root = Path(config.raw["global"]["kb_output"]["root"])
        self._vector_store = None

    def _get_vector_store(self):
        """Lazy-load vector store adapter."""
        if self._vector_store is None:
            vs_config = self.config.raw["global"]["vector_store"]
            if vs_config.get("enabled", False):
                from tools.adapters.chromadb_adapter import ChromaDBAdapter
                self._vector_store = ChromaDBAdapter(resource_cfg=vs_config)
            else:
                from tools.adapters.stub_adapter import StubAdapter
                self._vector_store = StubAdapter(tool_name="vector_store")
        return self._vector_store

    def write(self, repo_name: str, component_name: str,
              filename: str, data: Any, agent_name: str = "",
              index_in_vector_store: bool = True) -> Path:
        """
        Write agent output to KB.
        Returns path where file was written.
        """
        # Build folder path
        if component_name:
            folder = self.kb_root / repo_name / component_name
        else:
            folder = self.kb_root / repo_name / "application_level"

        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / filename

        # Write JSON or string
        with open(file_path, "w") as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f, indent=2, default=str)
            else:
                f.write(str(data))

        console.print(f"[green]  💾 KB ← {filename}[/green] [dim]({folder})[/dim]")

        # Index in ChromaDB if enabled
        if index_in_vector_store and isinstance(data, (dict, list)):
            try:
                vs = self._get_vector_store()
                content = json.dumps(data, default=str)
                metadata = {
                    "repo": repo_name,
                    "component": component_name,
                    "agent": agent_name,
                    "filename": filename,
                    "timestamp": datetime.utcnow().isoformat()
                }
                vs.index({"content": content, "id": str(file_path)}, metadata)
            except Exception as e:
                console.print(f"[dim yellow]  ⚠️  ChromaDB index failed: {e}[/dim yellow]")

        return file_path

    def write_run_metadata(self, repo_name: str, run_id: str,
                           config_snapshot: Dict, overall_confidence: float):
        """Write metadata for the entire run."""
        metadata = {
            "run_id": run_id,
            "repo_name": repo_name,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_confidence": overall_confidence,
            "config_snapshot": {
                "brd_version": config_snapshot.get("orchestrator", {}).get("brd_version"),
                "agents_enabled": [
                    k for k, v in config_snapshot.get("agents", {}).items()
                    if v.get("enabled", False)
                ]
            }
        }
        self.write(repo_name, "", "run_metadata.json", metadata, "orchestrator", False)

    def check_hitl_feedback(self, hitl_file_path: str) -> Optional[str]:
        """
        Check if human has provided feedback in a HITL file.
        Returns feedback string if found, None if still pending.
        """
        path = Path(hitl_file_path)
        if not path.exists():
            return None

        content = path.read_text()
        # Look for human response after "YOUR CHOICE" marker
        if "YOUR CHOICE (enter number):" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "YOUR CHOICE (enter number):" in line:
                    choice_line = line.split(":")[-1].strip()
                    if choice_line and choice_line != "___":
                        return content  # Return full content for ingestion
        return None
```

### Step 2.4 — Base Agent

Create `agents/base_agent.py`:

```python
"""
Base Agent — all 7 agents inherit from this.
Implements the activation flow:
  1. Read context summary
  2. Apply house rules
  3. Check KB hits
  4. Read handoff notes
  5. Scan open items
  6. Do work
  7. Write events
  8. Update state
  9. Write handoff notes
  10. Stage KB candidates
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
import anthropic
import os

from orchestrator.state import BRDState
from orchestrator.event_log import EventLog
from kb.kb_manager import KBManager
from hitl.hitl_handler import HITLHandler
from config_loader.config_loader import ConfigLoader
from tools.tool_factory import get_tool

console = Console()

class BaseAgent(ABC):

    def __init__(self, agent_name: str, agent_number: int,
                 config: ConfigLoader, event_log: EventLog,
                 kb_manager: KBManager):
        self.agent_name = agent_name
        self.agent_number = agent_number
        self.config = config
        self.event_log = event_log
        self.kb_manager = kb_manager
        self.agent_cfg = config.get_agent_config(agent_name)
        self.hitl = HITLHandler(config, agent_name, kb_manager)

        # Set up LLM client
        llm_cfg = self.agent_cfg.get("llm_resolved", {})
        self.llm_model = llm_cfg.get("model", "claude-sonnet-4-5")
        self.llm_temperature = llm_cfg.get("temperature", 0.2)
        self.llm_max_tokens = llm_cfg.get("max_tokens", 4096)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def run(self, state: BRDState) -> BRDState:
        """Main entry point — implements the standard activation flow."""
        self._print_activation_banner()

        # Step 1: Read context (already in state)
        self._log_event(state, "AGENT", "agent_activated",
                       {"model": self.llm_model}, confidence=1.0)

        # Step 2: Apply house rules (intrinsic — part of LLM prompt)
        # Step 3: Check handoff notes from previous agent
        self._review_handoff_notes(state)

        # Step 4: Check for pending HITL feedback
        self._check_pending_hitl(state)

        # Step 5: Do the work
        state = self.execute(state)

        # Step 6: Update current_agent in state
        state["current_agent"] = self.agent_name

        # Step 7: Log completion
        self._log_event(state, "AGENT", "agent_completed",
                       {"confidence": state.get("overall_confidence", 0.0)})

        return state

    @abstractmethod
    def execute(self, state: BRDState) -> BRDState:
        """
        Agent-specific logic. Override in each agent.
        Must return updated state.
        """
        pass

    def call_llm(self, system_prompt: str, user_prompt: str,
                 max_tokens: int = None) -> str:
        """Call Claude with the agent's configured model."""
        response = self.client.messages.create(
            model=self.llm_model,
            max_tokens=max_tokens or self.llm_max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text

    def get_tool(self, tool_name: str):
        """Get a tool adapter by name from config."""
        return get_tool(self.agent_name, tool_name, self.config)

    def is_sub_agent_enabled(self, sub_agent_name: str) -> bool:
        return self.config.is_sub_agent_enabled(self.agent_name, sub_agent_name)

    def add_warning(self, state: BRDState, warning_type: str,
                    message: str, confidence: float) -> BRDState:
        """Add a warning to state. Warnings accumulate across all agents."""
        warning = {
            "agent": self.agent_name,
            "type": warning_type,
            "message": message,
            "confidence": confidence
        }
        state["warnings"].append(warning)
        console.print(f"[yellow]  ⚠️  WARNING: {message}[/yellow]")
        return state

    def add_open_item(self, state: BRDState, item_type: str,
                      description: str, priority: str = "MEDIUM") -> BRDState:
        state["open_items"].append({
            "type": item_type,
            "agent": self.agent_name,
            "description": description,
            "priority": priority,
            "status": "open"
        })
        return state

    def write_kb(self, state: BRDState, output_key: str, data: Any):
        """Write data to KB using the agent's configured output filename."""
        agent_cfg = self.config.get_agent_config(self.agent_name)
        kb_outputs = agent_cfg.get("kb_output", {})
        filename = kb_outputs.get(output_key, f"{output_key}.json")

        self.kb_manager.write(
            repo_name=state["repo_name"],
            component_name=state.get("component_name", ""),
            filename=filename,
            data=data,
            agent_name=self.agent_name
        )

    def set_handoff_notes(self, state: BRDState, key_findings: list,
                          watch_out_for: list, confidence_flags: list) -> BRDState:
        state["handoff_notes"] = {
            "from_agent": self.agent_name,
            "key_findings": key_findings,
            "watch_out_for": watch_out_for,
            "confidence_flags": confidence_flags
        }
        return state

    def set_human_feedback(self, state: BRDState, feedback: str) -> BRDState:
        """Record human feedback in state for this agent."""
        agent_num = self.agent_name.split("_")[1]  # e.g. "1" from "agent_1_discovery"
        feedback_key = f"agent_{agent_num}"
        state["human_feedback"][feedback_key] = feedback
        return state

    def _log_event(self, state: BRDState, category: str, event_type: str,
                   payload: Dict, confidence: float = 0.0,
                   is_hitl: bool = False, is_kb_candidate: bool = False):
        """Log to SQLite event log."""
        self.event_log.log(
            run_id=state["run_id"],
            agent_id=self.agent_name,
            event_type=f"{category}.{event_type}",
            payload=payload,
            confidence=confidence,
            is_hitl=is_hitl,
            is_kb_candidate=is_kb_candidate
        )

    def _review_handoff_notes(self, state: BRDState):
        """Print handoff notes from previous agent."""
        notes = state.get("handoff_notes", {})
        if notes.get("from_agent"):
            console.print(f"\n[dim]📋 Handoff from {notes['from_agent']}:[/dim]")
            for finding in notes.get("key_findings", []):
                console.print(f"[dim]   • {finding}[/dim]")
            for flag in notes.get("confidence_flags", []):
                console.print(f"[dim yellow]   ⚠ {flag}[/dim yellow]")

    def _check_pending_hitl(self, state: BRDState):
        """Check if any HITL items from previous run have feedback."""
        pending = state.get("hitl_pending", [])
        for item in pending:
            if item.get("agent") == self.agent_name:
                feedback = self.kb_manager.check_hitl_feedback(
                    item.get("file_path", "")
                )
                if feedback:
                    console.print(f"[green]  ✅ Human feedback received for: {item.get('trigger')}[/green]")
                    self.set_human_feedback(state, feedback)
                    self._log_event(state, "HITL", "human_input_received",
                                   {"item": item, "feedback_length": len(feedback)})

    def _print_activation_banner(self):
        agent_cfg = self.agent_cfg
        name = agent_cfg.get("name", self.agent_name)
        desc = agent_cfg.get("description", "")
        console.print(Panel(
            f"[bold]{name}[/bold]\n[dim]{desc}[/dim]\n"
            f"[dim]Model: {self.llm_model}[/dim]",
            title=f"🤖 Agent {self.agent_number}",
            border_style="blue"
        ))
```

### Step 2.5 — LangGraph Pipeline Skeleton

Create `orchestrator/pipeline.py`:

```python
"""
LangGraph Pipeline — defines the agent execution graph.
Agents run in sequence with parallel execution where configured.
"""
import uuid
from pathlib import Path
from typing import Dict
from langgraph.graph import StateGraph, END
from rich.console import Console
from rich.rule import Rule

from orchestrator.state import BRDState, get_initial_state
from orchestrator.event_log import EventLog
from kb.kb_manager import KBManager
from config_loader.config_loader import ConfigLoader

console = Console()

class BRDPipeline:

    def __init__(self, config: ConfigLoader):
        self.config = config
        orch_cfg = config.get_orchestrator_config()
        self.brd_version = orch_cfg.get("brd_version", "0.1.0-poc")

        # Initialize shared services
        event_log_path = config.raw["global"]["state_store"]["event_log_path"]
        self.event_log = EventLog(event_log_path)
        self.kb_manager = KBManager(config)

        # Import agents
        self.agents = self._load_agents()
        self.graph = self._build_graph()

    def _load_agents(self) -> Dict:
        """Import and instantiate all enabled agents."""
        from agents.agent_1_discovery import Agent1Discovery
        from agents.agent_2_journey import Agent2Journey
        from agents.agent_3_rules import Agent3Rules
        from agents.agent_4_gap import Agent4Gap
        from agents.agent_5_synthesis import Agent5Synthesis
        from agents.agent_6_ac import Agent6AC
        from agents.agent_7_risk import Agent7Risk

        agent_classes = {
            "agent_1_discovery": (Agent1Discovery, 1),
            "agent_2_journey": (Agent2Journey, 2),
            "agent_3_rules": (Agent3Rules, 3),
            "agent_4_gap": (Agent4Gap, 4),
            "agent_5_synthesis": (Agent5Synthesis, 5),
            "agent_6_ac": (Agent6AC, 6),
            "agent_7_risk": (Agent7Risk, 7),
        }

        agents = {}
        for name, (cls, num) in agent_classes.items():
            if self.config.is_agent_enabled(name):
                agents[name] = cls(
                    agent_name=name,
                    agent_number=num,
                    config=self.config,
                    event_log=self.event_log,
                    kb_manager=self.kb_manager
                )
        return agents

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine from config pipeline sequence."""
        graph = StateGraph(BRDState)

        # Add nodes for each enabled agent
        for name, agent in self.agents.items():
            graph.add_node(name, agent.run)

        # Build edges from pipeline config
        orch_cfg = self.config.get_orchestrator_config()
        sequence = orch_cfg.get("pipeline", {}).get("sequence", [])

        self._add_edges(graph, sequence)
        return graph.compile()

    def _add_edges(self, graph: StateGraph, sequence: list):
        """
        Add edges to graph from sequence config.
        Handles both sequential and parallel steps.
        """
        prev_nodes = None

        for i, step in enumerate(sequence):
            if isinstance(step, str):
                # Sequential step
                current_node = step
                if prev_nodes is None:
                    graph.set_entry_point(current_node)
                elif isinstance(prev_nodes, list):
                    for prev in prev_nodes:
                        graph.add_edge(prev, current_node)
                else:
                    graph.add_edge(prev_nodes, current_node)

                # Check if next step is also sequential
                if i + 1 < len(sequence):
                    next_step = sequence[i + 1]
                    if isinstance(next_step, str):
                        graph.add_edge(current_node, next_step)
                else:
                    graph.add_edge(current_node, END)

                prev_nodes = current_node

            elif isinstance(step, dict) and "parallel" in step:
                # Parallel step
                parallel_nodes = step["parallel"]

                if prev_nodes is None:
                    # Parallel as entry point (unusual but handled)
                    graph.set_entry_point(parallel_nodes[0])
                    for node in parallel_nodes[1:]:
                        graph.add_edge(parallel_nodes[0], node)
                elif isinstance(prev_nodes, str):
                    for node in parallel_nodes:
                        graph.add_edge(prev_nodes, node)
                elif isinstance(prev_nodes, list):
                    for prev in prev_nodes:
                        for node in parallel_nodes:
                            graph.add_edge(prev, node)

                # Connect parallel nodes to next step
                if i + 1 < len(sequence):
                    next_step = sequence[i + 1]
                    if isinstance(next_step, str):
                        for node in parallel_nodes:
                            graph.add_edge(node, next_step)
                    elif isinstance(next_step, dict) and "parallel" in next_step:
                        for node in parallel_nodes:
                            for next_node in next_step["parallel"]:
                                graph.add_edge(node, next_node)
                else:
                    for node in parallel_nodes:
                        graph.add_edge(node, END)

                prev_nodes = parallel_nodes

    def run(self, repo_path: str, component_name: str = "") -> BRDState:
        """
        Execute the full BRD pipeline for a repository.
        Returns final state containing all outputs.
        """
        repo_name = Path(repo_path).name
        run_id = str(uuid.uuid4())

        console.print(Rule(f"[bold blue]BRD Agent POC — Starting Run[/bold blue]"))
        console.print(f"[dim]Run ID: {run_id}[/dim]")
        console.print(f"[dim]Repo: {repo_path}[/dim]")
        console.print(f"[dim]BRD Version: {self.brd_version}[/dim]\n")

        # Initialize state
        initial_state = get_initial_state(
            run_id=run_id,
            repo_path=repo_path,
            repo_name=repo_name,
            brd_version=self.brd_version
        )
        initial_state["component_name"] = component_name

        # Write run metadata to KB
        self.kb_manager.write_run_metadata(
            repo_name=repo_name,
            run_id=run_id,
            config_snapshot=self.config.raw,
            overall_confidence=0.0
        )

        # Execute graph
        final_state = self.graph.invoke(initial_state)

        # Final summary
        console.print(Rule("[bold green]BRD Pipeline Complete[/bold green]"))
        console.print(f"[green]Overall Confidence: {final_state.get('overall_confidence', 0.0):.2f}[/green]")
        console.print(f"[green]BRD Locked: {final_state.get('brd_locked', False)}[/green]")
        console.print(f"[dim]KB Output: {self.kb_manager.kb_root / repo_name}[/dim]\n")

        return final_state
```

### Step 2.6 — HITL Handler

Create `hitl/hitl_handler.py`:

```python
"""
HITL Handler — manages human-in-the-loop interactions.
CLI mode: displays to terminal, waits for input.
File mode: writes to HITL_PENDING folder, agent checks on next run.
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

console = Console()

HITL_FILE_TEMPLATE = """
=============================================================================
BRD AGENT — HUMAN REVIEW REQUIRED
=============================================================================
Agent:    {agent_name}
Trigger:  {trigger}
Date:     {timestamp}
Status:   PENDING_HUMAN_REVIEW
=============================================================================

CONTEXT:
{context}

OPTIONS:
{options_text}

YOUR CHOICE (enter number): ___

YOUR COMMENTS / ADDITIONAL CONTEXT:
(Add your feedback below this line)


=============================================================================
END OF REVIEW — Save this file when done. Agent will read it on next run.
=============================================================================
"""

class HITLHandler:

    def __init__(self, config, agent_name: str, kb_manager):
        self.config = config
        self.agent_name = agent_name
        self.kb_manager = kb_manager
        self.hitl_pending_root = Path(
            config.raw["global"]["kb_output"]["hitl_pending"]
        )
        self.hitl_pending_root.mkdir(parents=True, exist_ok=True)
        self.global_mode = config.raw.get("global", {}).get("hitl", {}).get("mode", "cli")

    def handle(self, state: Dict, trigger_name: str, context: str,
               options: List[str], allow_freetext: bool = True,
               hitl_type: str = None) -> Dict:
        """
        Handle a HITL trigger based on config.
        Returns updated state with human_feedback recorded.
        """
        agent_cfg = self.config.get_agent_config(self.agent_name)
        hitl_cfg = agent_cfg.get("hitl", {}).get(trigger_name, {})
        mode = hitl_type or hitl_cfg.get("type", self.global_mode)

        if mode == "none":
            # Auto-handle — apply configured action
            action = hitl_cfg.get("action", "proceed")
            console.print(f"[dim]  ℹ️  Auto-handling HITL [{trigger_name}]: {action}[/dim]")
            return state

        trigger_desc = hitl_cfg.get("trigger", trigger_name)

        if mode == "cli":
            return self._handle_cli(state, trigger_desc, context,
                                   options, allow_freetext, trigger_name)
        elif mode == "file":
            template = hitl_cfg.get("template", f"{trigger_name}.txt")
            return self._handle_file(state, trigger_desc, context,
                                    options, template, trigger_name)
        elif mode == "both":
            state = self._handle_file(state, trigger_desc, context,
                                     options, f"{trigger_name}.txt", trigger_name)
            return self._handle_cli(state, trigger_desc, context,
                                   options, allow_freetext, trigger_name)
        return state

    def _handle_cli(self, state: Dict, trigger: str, context: str,
                    options: List[str], allow_freetext: bool,
                    trigger_name: str) -> Dict:
        """Display HITL in CLI and wait for human input."""
        console.print(Panel(
            f"[bold yellow]⚡ Human Input Required[/bold yellow]\n"
            f"[dim]{trigger}[/dim]",
            title="🧑 HITL",
            border_style="yellow"
        ))
        console.print(f"\n[bold]Context:[/bold]\n{context}\n")
        console.print("[bold]Options:[/bold]")
        for i, opt in enumerate(options, 1):
            console.print(f"  {i}. {opt}")

        choice = IntPrompt.ask(
            "\nYour choice",
            choices=[str(i) for i in range(1, len(options) + 1)]
        )
        chosen = options[int(choice) - 1]
        comment = ""
        if allow_freetext:
            comment = Prompt.ask("Additional comments (press Enter to skip)", default="")

        feedback = f"Choice: {choice}. {chosen}"
        if comment:
            feedback += f"\nComment: {comment}"

        console.print(f"[green]  ✅ Human selected: {chosen}[/green]\n")
        return self._record_feedback(state, trigger_name, feedback)

    def _handle_file(self, state: Dict, trigger: str, context: str,
                     options: List[str], template_name: str,
                     trigger_name: str) -> Dict:
        """Write HITL file and mark as pending."""
        options_text = "\n".join(
            [f"{i+1}. {opt}" for i, opt in enumerate(options)]
        )

        content = HITL_FILE_TEMPLATE.format(
            agent_name=self.agent_name,
            trigger=trigger,
            timestamp=datetime.utcnow().isoformat(),
            context=context,
            options_text=options_text
        )

        file_path = self.hitl_pending_root / f"{self.agent_name}_{trigger_name}.txt"
        file_path.write_text(content)

        console.print(f"[yellow]  📝 HITL file written: {file_path}[/yellow]")
        console.print(f"[dim]     Review and fill in your choice, then re-run.[/dim]")

        # Mark as pending in state
        if "hitl_pending" not in state:
            state["hitl_pending"] = []
        state["hitl_pending"].append({
            "agent": self.agent_name,
            "trigger": trigger,
            "file_path": str(file_path),
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat()
        })

        return state

    def _record_feedback(self, state: Dict, trigger_name: str,
                         feedback: str) -> Dict:
        """Record human feedback in state."""
        agent_num = self.agent_name.split("_")[1]
        existing = state.get("human_feedback", {}).get(f"agent_{agent_num}", "")
        new_feedback = f"{existing}\n[{trigger_name}]: {feedback}".strip()
        state["human_feedback"][f"agent_{agent_num}"] = new_feedback
        return state
```

### Phase 2 Validation Test

Create `tests/test_phase2_state.py`:

```python
"""
Phase 2 Validation Tests
Run: pytest tests/test_phase2_state.py -v
"""
import pytest
import uuid
from orchestrator.state import BRDState, get_initial_state
from orchestrator.event_log import EventLog
from kb.kb_manager import KBManager
from config_loader.config_loader import ConfigLoader

def test_initial_state_has_all_required_fields():
    state = get_initial_state("test-run", "./sample_repo", "sample_repo", "0.1.0-poc")
    required_fields = [
        "run_id", "repo_name", "repo_path", "human_feedback",
        "warnings", "open_items", "hitl_pending", "brd_locked"
    ]
    for field in required_fields:
        assert field in state, f"Missing field: {field}"

def test_human_feedback_has_all_agent_keys():
    state = get_initial_state("test-run", "./sample_repo", "sample_repo", "0.1.0-poc")
    for i in range(1, 8):
        assert f"agent_{i}" in state["human_feedback"]

def test_event_log_writes_and_reads(tmp_path):
    log = EventLog(str(tmp_path / "test.db"))
    event_id = log.log(
        run_id="test-run",
        agent_id="agent_1_discovery",
        event_type="AGENT.agent_activated",
        payload={"test": "data"},
        confidence=0.9
    )
    assert event_id is not None

    events = log.get_events_for_run("test-run")
    assert len(events) == 1
    assert events[0]["event_type"] == "AGENT.agent_activated"

def test_kb_manager_writes_json(tmp_path):
    config = ConfigLoader()
    manager = KBManager(config)
    manager.kb_root = tmp_path

    test_data = {"journeys": [{"name": "Happy Path", "actor": "Customer"}]}
    path = manager.write("test_repo", "test_component", "journey_map.json",
                         test_data, "agent_2_journey", False)
    assert path.exists()
    import json
    with open(path) as f:
        loaded = json.load(f)
    assert loaded["journeys"][0]["name"] == "Happy Path"

def test_pipeline_builds_without_error():
    from orchestrator.pipeline import BRDPipeline
    config = ConfigLoader()
    pipeline = BRDPipeline(config)
    assert pipeline.graph is not None

def test_warnings_accumulate_in_state():
    state = get_initial_state("test-run", "./sample_repo", "sample_repo", "0.1.0-poc")
    state["warnings"].append({"agent": "agent_1", "type": "LOW_CONFIDENCE",
                              "message": "test warning", "confidence": 0.3})
    state["warnings"].append({"agent": "agent_2", "type": "CONFLICT",
                              "message": "journey conflict", "confidence": 0.5})
    assert len(state["warnings"]) == 2
```

---

## PHASE 3 — Agents 1-4 With Available Tools

### Goal
Agents 1, 2, 3, and 4 run and produce real output from the sample repo. KB files are written. HITL triggers work.

### Step 3.1 — Tool Adapters

Implement each adapter. Each must implement its interface contract.

**`tools/adapters/gitpython_adapter.py`**:
```python
"""
GitPython Adapter — repo scanning and file access.
Implements RepoScannerInterface using gitpython + pathlib for local repos.
"""
import os
from pathlib import Path
from typing import Dict, List
from tools.interfaces.repo_scanner_interface import RepoScannerInterface

class GitPythonAdapter(RepoScannerInterface):

    def __init__(self, resource_cfg: Dict = None):
        self.resource_cfg = resource_cfg or {}
        self.repo_path = Path(resource_cfg.get("path", "."))

    def scan_directory(self, path: str = None) -> Dict:
        """Scan directory and return file tree with language stats."""
        scan_path = Path(path) if path else self.repo_path
        files = []
        language_stats = {}

        ext_to_language = {
            ".java": "java", ".py": "python", ".js": "javascript",
            ".ts": "typescript", ".xml": "xml", ".yaml": "yaml",
            ".yml": "yaml", ".json": "json", ".properties": "properties",
            ".md": "markdown", ".txt": "text"
        }

        for file_path in scan_path.rglob("*"):
            if file_path.is_file() and not any(
                part.startswith(".") for part in file_path.parts
            ):
                ext = file_path.suffix.lower()
                lang = ext_to_language.get(ext, "other")
                size = file_path.stat().st_size

                files.append({
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(scan_path)),
                    "extension": ext,
                    "language": lang,
                    "size_bytes": size
                })

                if lang not in language_stats:
                    language_stats[lang] = {"files": 0, "bytes": 0}
                language_stats[lang]["files"] += 1
                language_stats[lang]["bytes"] += size

        directories = [
            str(d.relative_to(scan_path))
            for d in scan_path.rglob("*")
            if d.is_dir() and not any(p.startswith(".") for p in d.parts)
        ]

        return {
            "files": files,
            "directories": directories,
            "language_stats": language_stats,
            "total_files": len(files),
            "scan_root": str(scan_path)
        }

    def get_file(self, path: str) -> str:
        """Read file contents."""
        try:
            return Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"# Error reading file: {e}"

    def find_pattern(self, pattern: str, path: str = None) -> List[Dict]:
        """Find files matching a glob pattern."""
        scan_path = Path(path) if path else self.repo_path
        results = []
        for match in scan_path.rglob(pattern):
            if match.is_file():
                results.append({
                    "file": str(match),
                    "relative_path": str(match.relative_to(scan_path))
                })
        return results

    def get_file_tree(self, path: str = None) -> List[str]:
        """Return flat list of all file paths."""
        result = self.scan_directory(path)
        return [f["path"] for f in result["files"]]
```

**`tools/adapters/tree_sitter_adapter.py`**:
```python
"""
Tree-sitter Adapter — Java AST parsing and test method extraction.
Uses tree-sitter for structural analysis and javalang as fallback.
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, List
from tools.interfaces.code_analyzer_interface import CodeAnalyzerInterface

class TreeSitterAdapter(CodeAnalyzerInterface):

    def __init__(self, resource_cfg: Dict = None):
        self.resource_cfg = resource_cfg or {}
        self.language = resource_cfg.get("language", "java")
        self._parser = None

    def _get_parser(self):
        """Lazy-initialize tree-sitter parser."""
        if self._parser is None:
            try:
                import tree_sitter_java as tsjava
                from tree_sitter import Language, Parser
                JAVA_LANGUAGE = Language(tsjava.language())
                self._parser = Parser(JAVA_LANGUAGE)
            except Exception as e:
                self._parser = None
        return self._parser

    def analyze_file(self, path: str) -> Dict:
        """Parse Java file and extract structural information."""
        content = Path(path).read_text(encoding="utf-8", errors="ignore")

        # Try tree-sitter first
        parser = self._get_parser()
        if parser:
            return self._analyze_with_tree_sitter(content, path)

        # Fallback to javalang
        return self._analyze_with_javalang(content, path)

    def _analyze_with_tree_sitter(self, content: str, path: str) -> Dict:
        """Use tree-sitter for AST analysis."""
        try:
            from tree_sitter import Language, Parser
            parser = self._get_parser()
            tree = parser.parse(bytes(content, "utf-8"))
            root = tree.root_node

            classes = []
            methods = []

            # Walk tree for class and method declarations
            def walk(node):
                if node.type == "class_declaration":
                    class_name = ""
                    for child in node.children:
                        if child.type == "identifier":
                            class_name = content[child.start_byte:child.end_byte]
                    classes.append({
                        "name": class_name,
                        "line": node.start_point[0],
                        "methods": []
                    })
                elif node.type == "method_declaration":
                    method_name = ""
                    annotations = []
                    for child in node.children:
                        if child.type == "identifier":
                            method_name = content[child.start_byte:child.end_byte]
                        elif child.type == "modifiers":
                            for mod_child in child.children:
                                if mod_child.type == "marker_annotation":
                                    annotations.append(
                                        content[mod_child.start_byte:mod_child.end_byte]
                                    )
                    body = content[node.start_byte:node.end_byte]
                    methods.append({
                        "name": method_name,
                        "annotations": annotations,
                        "body": body[:500],  # First 500 chars
                        "line": node.start_point[0]
                    })
                for child in node.children:
                    walk(child)

            walk(root)
            return {
                "classes": classes,
                "methods": methods,
                "imports": self._extract_imports(content),
                "language": "java",
                "parser": "tree-sitter"
            }
        except Exception as e:
            return self._analyze_with_javalang(content, path)

    def _analyze_with_javalang(self, content: str, path: str) -> Dict:
        """Fallback: use javalang for Java parsing."""
        try:
            import javalang
            tree = javalang.parse.parse(content)
            classes = []
            methods = []

            for _, node in tree.filter(javalang.tree.ClassDeclaration):
                class_info = {"name": node.name, "methods": []}
                for method in node.methods:
                    annotations = [a.name for a in (method.annotations or [])]
                    class_info["methods"].append(method.name)
                    methods.append({
                        "name": method.name,
                        "annotations": annotations,
                        "parameters": [p.name for p in (method.parameters or [])],
                        "return_type": str(method.return_type) if method.return_type else "void",
                        "body": ""  # javalang doesn't give raw body easily
                    })
                classes.append(class_info)

            return {
                "classes": classes,
                "methods": methods,
                "imports": self._extract_imports(content),
                "language": "java",
                "parser": "javalang"
            }
        except Exception as e:
            return {
                "classes": [], "methods": [], "imports": [],
                "language": "java", "parser": "failed",
                "error": str(e)
            }

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements."""
        imports = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("import ") and line.endswith(";"):
                imports.append(line[7:-1])
        return imports

    def extract_rules(self, path: str) -> List[Dict]:
        """
        Extract business rule candidates from Java file.
        Looks for: if/else blocks, validation patterns, threshold constants,
        business-named methods, switch statements.
        """
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
        rules = []
        lines = content.split("\n")

        rule_patterns = [
            ("validation", ["if (", "if(", "throw new", "IllegalArgument",
                           "validate", "isValid", "check"]),
            ("eligibility", ["isEligible", "canProcess", "hasAccess",
                            "isAllowed", "checkEligibility"]),
            ("calculation", ["calculate", "compute", "total", "amount",
                            "price", "rate", "fee"]),
            ("threshold", ["THRESHOLD", "MAX_", "MIN_", "LIMIT_", "final double",
                          "final int", "static final"]),
            ("conditional", ["else if", "switch (", "switch(", "? :", "ternary"]),
        ]

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("//"):
                continue

            for rule_type, keywords in rule_patterns:
                if any(kw.lower() in line_stripped.lower() for kw in keywords):
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 5)
                    context = "\n".join(lines[context_start:context_end])

                    rules.append({
                        "type": rule_type,
                        "code_snippet": line_stripped,
                        "line_number": i + 1,
                        "context": context,
                        "complexity": "complex" if len(line_stripped) > 80 else "simple",
                        "file": path
                    })
                    break  # One rule type per line

        return rules

    def find_conditionals(self, path: str) -> List[Dict]:
        """Find all conditional statements."""
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
        conditionals = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("if ") or stripped.startswith("if("):
                conditionals.append({
                    "code": stripped[:200],
                    "line": i + 1,
                    "type": "if_statement"
                })
            elif stripped.startswith("switch"):
                conditionals.append({
                    "code": stripped[:200],
                    "line": i + 1,
                    "type": "switch_statement"
                })

        return conditionals

    def find_test_methods(self, path: str) -> List[Dict]:
        """Extract test methods from Java test files."""
        analysis = self.analyze_file(path)
        test_methods = []

        for method in analysis.get("methods", []):
            if "@Test" in method.get("annotations", []):
                body = method.get("body", "")
                # Extract assertions
                assertions = [
                    line.strip() for line in body.split("\n")
                    if "assert" in line.lower() or "verify" in line.lower()
                ]
                # Extract page object / service calls
                service_calls = [
                    line.strip() for line in body.split("\n")
                    if "Service" in line or "Repository" in line or "Driver" in line
                ]

                test_methods.append({
                    "name": method["name"],
                    "annotations": method.get("annotations", []),
                    "body": body[:1000],
                    "assertions": assertions[:5],
                    "service_calls": service_calls[:5]
                })

        return test_methods
```

**`tools/adapters/semgrep_adapter.py`**:
```python
"""
Semgrep Adapter — pattern-based rule extraction from Java code.
Runs semgrep CLI as subprocess with Java ruleset.
"""
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List
from tools.interfaces.code_analyzer_interface import CodeAnalyzerInterface

class SemgrepAdapter(CodeAnalyzerInterface):

    def __init__(self, resource_cfg: Dict = None):
        self.resource_cfg = resource_cfg or {}
        self.repo_path = Path(resource_cfg.get("path", "."))

    def analyze_file(self, path: str) -> Dict:
        """Semgrep doesn't do structural analysis — delegate to tree-sitter pattern."""
        return {"message": "Use tree_sitter_adapter for structural analysis"}

    def extract_rules(self, path: str) -> List[Dict]:
        """
        Use Semgrep to find business rule patterns in Java code.
        Writes custom rules for validation, eligibility, calculation patterns.
        """
        semgrep_rules = self._get_business_rule_patterns()
        results = []

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(semgrep_rules)
            rules_file = f.name

        try:
            result = subprocess.run(
                ["semgrep", "--config", rules_file,
                 "--json", "--quiet", path],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode in [0, 1]:  # 0=no findings, 1=findings found
                output = json.loads(result.stdout) if result.stdout else {"results": []}
                for finding in output.get("results", []):
                    results.append({
                        "type": finding.get("check_id", "").replace("brd-poc-", ""),
                        "code_snippet": finding.get("extra", {}).get("lines", ""),
                        "line_number": finding.get("start", {}).get("line", 0),
                        "context": finding.get("extra", {}).get("message", ""),
                        "complexity": "simple",
                        "file": path,
                        "source": "semgrep"
                    })
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            # Semgrep not installed — return empty
            pass
        except Exception:
            pass
        finally:
            Path(rules_file).unlink(missing_ok=True)

        return results

    def find_conditionals(self, path: str) -> List[Dict]:
        return []  # Tree-sitter handles this better

    def find_test_methods(self, path: str) -> List[Dict]:
        return []  # Tree-sitter handles this

    def _get_business_rule_patterns(self) -> str:
        """Custom Semgrep YAML rules for Java business rule detection."""
        return """
rules:
  - id: brd-poc-validation-rule
    patterns:
      - pattern: |
          if ($CONDITION) {
            throw new $EXCEPTION(...);
          }
    message: "Validation rule detected: throws exception on condition"
    languages: [java]
    severity: INFO

  - id: brd-poc-threshold-constant
    pattern: |
      private static final $TYPE $NAME = $VALUE;
    message: "Business threshold or constant detected"
    languages: [java]
    severity: INFO

  - id: brd-poc-eligibility-check
    patterns:
      - pattern: |
          if (!$OBJ.$METHOD()) {
            return false;
          }
    message: "Eligibility check detected"
    languages: [java]
    severity: INFO

  - id: brd-poc-null-check
    pattern: |
      if ($VAR == null || $VAR.isEmpty()) {
        throw new IllegalArgumentException(...);
      }
    message: "Null/empty validation rule detected"
    languages: [java]
    severity: INFO
"""
```

**`tools/adapters/chromadb_adapter.py`**:
```python
"""
ChromaDB Adapter — local vector store for KB indexing.
"""
from typing import Dict, List
from tools.interfaces.vector_store_interface import VectorStoreInterface

class ChromaDBAdapter(VectorStoreInterface):

    def __init__(self, resource_cfg: Dict = None):
        self.resource_cfg = resource_cfg or {}
        self.path = resource_cfg.get("path", "./KB/chromadb_index")
        self.collection_name = resource_cfg.get("collection_name", "brd_poc")
        self.embedding_model = resource_cfg.get("embedding_model", "all-MiniLM-L6-v2")
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is None:
            import chromadb
            from chromadb.config import Settings
            from sentence_transformers import SentenceTransformer

            self._client = chromadb.PersistentClient(path=self.path)
            self._embedder = SentenceTransformer(self.embedding_model)

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def index(self, doc: Dict, metadata: Dict) -> None:
        """Index a document."""
        try:
            collection = self._get_collection()
            content = doc.get("content", "")
            doc_id = doc.get("id", str(hash(content)))

            embedding = self._embedder.encode(content[:2000]).tolist()
            collection.add(
                documents=[content[:2000]],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception as e:
            pass  # KB indexing failure is non-fatal

    def search(self, query: str, top_k: int = 5,
               filter_metadata: Dict = None) -> List[Dict]:
        """Search for similar documents."""
        try:
            collection = self._get_collection()
            embedding = self._embedder.encode(query).tolist()

            where = filter_metadata if filter_metadata else None
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, collection.count()),
                where=where
            )

            output = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    output.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "score": 1.0 - results["distances"][0][i]
                    })
            return output
        except Exception:
            return []
```

**`tools/adapters/unstructured_adapter.py`**:
```python
"""
Unstructured Adapter — document parsing for PDF, Word, HTML, etc.
"""
from pathlib import Path
from typing import Dict, List
from tools.interfaces.doc_parser_interface import DocParserInterface

class UnstructuredAdapter(DocParserInterface):

    def __init__(self, resource_cfg: Dict = None):
        self.resource_cfg = resource_cfg or {}

    def parse_document(self, path: str) -> Dict:
        """Parse document using unstructured."""
        file_path = Path(path)
        if not file_path.exists():
            return {"content": "", "sections": [], "error": "File not found"}

        # For simple text/code files — just read them
        if file_path.suffix in [".java", ".py", ".js", ".ts", ".xml",
                                  ".yaml", ".yml", ".properties", ".txt", ".md"]:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return {
                "title": file_path.name,
                "content": content,
                "sections": [{"heading": "Content", "content": content}],
                "metadata": {"file_type": file_path.suffix, "file_name": file_path.name}
            }

        # For rich documents — use unstructured
        try:
            from unstructured.partition.auto import partition
            elements = partition(filename=str(file_path))
            sections = []
            current_section = {"heading": "Introduction", "content": ""}

            for element in elements:
                el_type = type(element).__name__
                text = str(element)

                if el_type == "Title":
                    if current_section["content"]:
                        sections.append(current_section)
                    current_section = {"heading": text, "content": ""}
                else:
                    current_section["content"] += f"\n{text}"

            if current_section["content"]:
                sections.append(current_section)

            full_content = "\n\n".join(
                [f"# {s['heading']}\n{s['content']}" for s in sections]
            )

            return {
                "title": file_path.name,
                "content": full_content,
                "sections": sections,
                "metadata": {
                    "file_type": file_path.suffix,
                    "file_name": file_path.name,
                    "element_count": len(elements)
                }
            }
        except Exception as e:
            # Final fallback — raw text
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                return {
                    "title": file_path.name,
                    "content": content,
                    "sections": [{"heading": "Content", "content": content}],
                    "metadata": {"file_type": file_path.suffix,
                                "error": str(e)}
                }
            except Exception:
                return {"content": "", "sections": [], "error": str(e)}

    def extract_sections(self, path: str) -> List[Dict]:
        """Extract sections as separate chunks."""
        result = self.parse_document(path)
        return result.get("sections", [])
```

### Step 3.2 — Agent Implementations

Implement each agent following this pattern. The agent:
1. Reads what it needs from state
2. Calls LLM with structured prompt based on BA cognitive model
3. Parses response
4. Writes to KB
5. Updates state
6. Handles HITL if needed
7. Writes handoff notes

**`agents/agent_1_discovery.py`**:

```python
"""
Agent 1 — Discovery & Scoping Agent
"The Investigator"
Scans repo, locates artifacts, defines scope boundaries.
"""
import json
from pathlib import Path
from agents.base_agent import BaseAgent
from orchestrator.state import BRDState

DISCOVERY_SYSTEM_PROMPT = """You are a Senior Business Analyst with 10+ years of experience
in Legacy system migration. Your current task is Discovery & Scoping.

You think like a systems thinker — never looking at a feature in isolation.
You are a skeptical reader — documentation is a hypothesis, not a fact.
You hunt for hidden complexity and tribal knowledge.

Your job is to:
1. Analyze the repository structure and identify the main components
2. Define clear scope boundaries for the migration
3. Identify all dependencies
4. Assess the confidence level of your findings

HOUSE RULES:
- Never jump to conclusions with a single source
- Every assumption must be logged
- Scope boundary is ambiguous? Flag it.
- Tribal knowledge smell? Flag it.
- Always state your confidence level (HIGH/MEDIUM/LOW)

Respond ONLY in valid JSON matching the schema provided. No preamble, no markdown."""

DISCOVERY_USER_PROMPT = """Analyze this repository and produce a scope definition.

REPOSITORY SCAN RESULTS:
{repo_scan}

EXISTING ARTIFACTS FOUND:
{artifacts}

COMPONENT NAME (if known): {component_name}

Produce a JSON response with this exact schema:
{{
  "component_name": "string — inferred from repo if not provided",
  "domain": "string — business domain (payments/identity/catalog/etc)",
  "description": "string — what this component does in plain English",
  "in_scope": ["list of features/modules explicitly in scope"],
  "out_of_scope": ["list of features/modules explicitly out of scope"],
  "deferred": ["list of items to address later"],
  "confidence": "HIGH|MEDIUM|LOW",
  "confidence_reason": "string — why this confidence level",
  "assumptions": [
    {{
      "statement": "string",
      "basis": "string — why I'm assuming this",
      "risk_if_wrong": "string",
      "owner": "string — who can confirm this"
    }}
  ],
  "warnings": ["list of any concerns or tribal knowledge risks"],
  "dependencies": [
    {{
      "name": "string — system or module name",
      "type": "upstream|downstream|shared_data",
      "description": "string"
    }}
  ],
  "artifact_catalog": [
    {{
      "path": "string",
      "type": "source_code|test|config|documentation",
      "relevance": "HIGH|MEDIUM|LOW",
      "notes": "string"
    }}
  ]
}}"""

class Agent1Discovery(BaseAgent):

    def execute(self, state: BRDState) -> BRDState:
        """Discovery & Scoping execution."""
        repo_path = state["repo_path"]
        repo_name = state["repo_name"]

        # Step 1: Scan repo with repo_scanner tool
        repo_scanner = self.get_tool("repo_scanner")
        scan_result = repo_scanner.scan_directory(repo_path)

        self._log_event(state, "DISCOVERY", "repo_scanned",
                       {"total_files": scan_result.get("total_files", 0),
                        "language_stats": scan_result.get("language_stats", {})},
                       confidence=1.0, is_kb_candidate=True)

        # Step 2: Find relevant artifacts
        artifacts = self._find_artifacts(scan_result, repo_path)

        # Step 3: Check for existing HITL feedback on scope
        existing_feedback = state["human_feedback"].get("agent_1", "")

        # Step 4: Call LLM with BA cognitive model
        repo_summary = self._summarize_scan(scan_result)
        artifacts_summary = json.dumps(artifacts[:20], indent=2)  # Limit for token budget

        user_prompt = DISCOVERY_USER_PROMPT.format(
            repo_scan=repo_summary,
            artifacts=artifacts_summary,
            component_name=state.get("component_name", "")
        )

        if existing_feedback:
            user_prompt += f"\n\nHUMAN FEEDBACK FROM PREVIOUS RUN:\n{existing_feedback}\nPlease incorporate this feedback."

        raw_response = self.call_llm(DISCOVERY_SYSTEM_PROMPT, user_prompt)

        # Step 5: Parse response
        scope_definition = self._parse_llm_response(raw_response)

        # Step 6: Check confidence — trigger HITL if too low
        confidence = scope_definition.get("confidence", "LOW")
        confidence_score = {"HIGH": 0.9, "MEDIUM": 0.7, "LOW": 0.4}.get(confidence, 0.4)

        if confidence == "LOW":
            state = self.hitl.handle(
                state=state,
                trigger_name="ambiguous_scope",
                context=f"Confidence is LOW because: {scope_definition.get('confidence_reason', 'unknown')}",
                options=self.agent_cfg["hitl"]["ambiguous_scope"]["options"]
            )

        # Step 7: Add warnings to state
        for warning in scope_definition.get("warnings", []):
            state = self.add_warning(state, "DISCOVERY_WARNING", warning, confidence_score)

        # Step 8: Write to KB
        self.write_kb(state, "scope_definition", scope_definition)
        self.write_kb(state, "artifact_catalog",
                     {"artifacts": artifacts, "total": len(artifacts)})
        self.write_kb(state, "dependency_map",
                     {"dependencies": scope_definition.get("dependencies", [])})

        # Step 9: Update state
        state["scope_definition"] = scope_definition
        state["scope"] = {
            "in_scope": scope_definition.get("in_scope", []),
            "out_of_scope": scope_definition.get("out_of_scope", []),
            "component_name": scope_definition.get("component_name", repo_name),
            "domain": scope_definition.get("domain", "unknown"),
            "confidence": confidence
        }
        state["component_name"] = scope_definition.get("component_name", repo_name)
        state["overall_confidence"] = confidence_score

        # Log assumptions
        for assumption in scope_definition.get("assumptions", []):
            self._log_event(state, "ASSUMPTION", "assumption_logged",
                           assumption, confidence=0.5)

        # Step 10: Write handoff notes
        state = self.set_handoff_notes(
            state,
            key_findings=[
                f"Component: {scope_definition.get('component_name')}",
                f"Domain: {scope_definition.get('domain')}",
                f"In-scope items: {len(scope_definition.get('in_scope', []))}",
                f"Confidence: {confidence}"
            ],
            watch_out_for=scope_definition.get("warnings", [])[:3],
            confidence_flags=[f"Overall confidence: {confidence}"] if confidence != "HIGH" else []
        )

        return state

    def _find_artifacts(self, scan_result: dict, repo_path: str) -> list:
        """Find relevant artifacts in the scan result."""
        relevant_extensions = {".java", ".xml", ".yaml", ".yml",
                               ".properties", ".md", ".txt", ".json"}
        artifacts = []

        for file_info in scan_result.get("files", []):
            ext = file_info.get("extension", "")
            if ext in relevant_extensions:
                rel_path = file_info.get("relative_path", file_info.get("path", ""))
                artifacts.append({
                    "path": rel_path,
                    "type": self._classify_artifact(rel_path, ext),
                    "size_bytes": file_info.get("size_bytes", 0),
                    "language": file_info.get("language", "unknown")
                })

        return artifacts[:100]  # Cap at 100 for token budget

    def _classify_artifact(self, path: str, ext: str) -> str:
        path_lower = path.lower()
        if "test" in path_lower:
            return "test"
        elif ext in [".yaml", ".yml", ".properties", ".json"]:
            return "config"
        elif ext in [".md", ".txt"]:
            return "documentation"
        else:
            return "source_code"

    def _summarize_scan(self, scan_result: dict) -> str:
        """Create a token-efficient summary of the repo scan."""
        stats = scan_result.get("language_stats", {})
        total = scan_result.get("total_files", 0)
        summary_lines = [f"Total files: {total}"]

        for lang, info in stats.items():
            if info["files"] > 0:
                summary_lines.append(f"  {lang}: {info['files']} files")

        # Sample of file paths for context
        files = scan_result.get("files", [])[:30]
        summary_lines.append("\nSample file paths:")
        for f in files:
            summary_lines.append(f"  {f.get('relative_path', '')}")

        return "\n".join(summary_lines)

    def _parse_llm_response(self, raw: str) -> dict:
        """Parse LLM JSON response with error handling."""
        try:
            # Strip markdown code blocks if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except Exception as e:
            return {
                "component_name": "unknown",
                "domain": "unknown",
                "description": "Could not parse LLM response",
                "in_scope": [],
                "out_of_scope": [],
                "confidence": "LOW",
                "confidence_reason": f"Parse error: {e}",
                "assumptions": [],
                "warnings": [f"LLM response parse failed: {e}"],
                "dependencies": [],
                "artifact_catalog": []
            }
```

**For Agents 2, 3, 4, 5, 6, 7** — implement following the exact same pattern as Agent 1:

Each agent must have:
- A `SYSTEM_PROMPT` constant encoding the BA cognitive model for that agent's task
- A `USER_PROMPT` template with JSON schema for structured output
- An `execute()` method that:
  1. Gets its tools from config via `self.get_tool()`
  2. Reads relevant state from previous agents
  3. Checks for human feedback
  4. Calls LLM with structured prompt
  5. Parses JSON response
  6. Handles HITL triggers per config
  7. Writes findings to KB via `self.write_kb()`
  8. Updates state
  9. Writes handoff notes via `self.set_handoff_notes()`

**Agent 2 key responsibilities:**
- Read file tree from Agent 1's scan
- Use `tree_sitter_adapter` to find test files and parse test methods
- Send test method names, bodies, assertions to LLM for journey interpretation
- Output: `journey_map.json`, `test_journey_coverage.json`, `actors.json`
- HITL: `journey_conflict` trigger when two sources describe same journey differently

**Agent 3 key responsibilities:**
- Use `semgrep_adapter` for pattern-based rule extraction
- Use `tree_sitter_adapter` for structural rule extraction
- Send code snippets to LLM for plain-English translation
- Output: `business_rules.json`, `regulatory_flags.json`, `orphaned_rules.json`
- HITL: `ambiguous_rule_translation` trigger (file-based) for uncertain translations

**Agent 4 key responsibilities:**
- Read journey_inventory and business_rules from state
- NSA spec parser is disabled — use LLM knowledge of common NSA patterns
- Classify each journey and rule as CLEAN_MAP / TRANSFORM / MISSING / DEFERRED
- Output: `gap_analysis.json`, `blocking_gaps.json`, `gap_register.json`
- HITL: `blocking_gap` trigger via CLI for unclassifiable gaps

### Phase 3 Validation Test

Create `tests/test_phase3_agents.py`:

```python
"""
Phase 3 Validation Tests
Run: pytest tests/test_phase3_agents.py -v
"""
import pytest
from pathlib import Path
from config_loader.config_loader import ConfigLoader
from orchestrator.state import get_initial_state
from orchestrator.event_log import EventLog
from kb.kb_manager import KBManager

@pytest.fixture
def pipeline_components(tmp_path):
    config = ConfigLoader()
    event_log = EventLog(str(tmp_path / "events.db"))
    kb_manager = KBManager(config)
    kb_manager.kb_root = tmp_path / "KB"
    return config, event_log, kb_manager

def test_agent_1_runs_on_sample_repo(pipeline_components):
    config, event_log, kb_manager = pipeline_components
    from agents.agent_1_discovery import Agent1Discovery

    agent = Agent1Discovery("agent_1_discovery", 1, config, event_log, kb_manager)
    state = get_initial_state("test", "./sample_repo", "sample_repo", "0.1.0-poc")
    state["repo_path"] = "./sample_repo"

    result_state = agent.run(state)
    assert result_state["scope_definition"] != {}
    assert "component_name" in result_state["scope_definition"]
    assert result_state["overall_confidence"] > 0
    assert result_state["handoff_notes"]["from_agent"] == "agent_1_discovery"

def test_agent_1_writes_kb_files(pipeline_components):
    config, event_log, kb_manager = pipeline_components
    from agents.agent_1_discovery import Agent1Discovery

    agent = Agent1Discovery("agent_1_discovery", 1, config, event_log, kb_manager)
    state = get_initial_state("test", "./sample_repo", "sample_repo", "0.1.0-poc")
    state["repo_path"] = "./sample_repo"

    result_state = agent.run(state)
    kb_root = kb_manager.kb_root
    repo_name = "sample_repo"

    # Check KB files exist
    assert any((kb_root / repo_name).rglob("scope_definition.json"))

def test_stub_tools_dont_break_agent_1(pipeline_components):
    config, event_log, kb_manager = pipeline_components
    from agents.agent_1_discovery import Agent1Discovery

    agent = Agent1Discovery("agent_1_discovery", 1, config, event_log, kb_manager)
    state = get_initial_state("test", "./sample_repo", "sample_repo", "0.1.0-poc")
    state["repo_path"] = "./sample_repo"

    # Should not raise even if some tools return empty
    result_state = agent.run(state)
    assert result_state is not None

def test_human_feedback_field_always_present(pipeline_components):
    config, event_log, kb_manager = pipeline_components
    from agents.agent_1_discovery import Agent1Discovery

    agent = Agent1Discovery("agent_1_discovery", 1, config, event_log, kb_manager)
    state = get_initial_state("test", "./sample_repo", "sample_repo", "0.1.0-poc")
    state["repo_path"] = "./sample_repo"

    result_state = agent.run(state)
    assert "human_feedback" in result_state
    assert "agent_1" in result_state["human_feedback"]

def test_tree_sitter_adapter_parses_java():
    from tools.adapters.tree_sitter_adapter import TreeSitterAdapter
    adapter = TreeSitterAdapter({"language": "java"})
    result = adapter.analyze_file("sample_repo/src/main/java/SampleService.java")
    assert "methods" in result
    assert len(result["methods"]) > 0

def test_tree_sitter_finds_test_methods():
    from tools.adapters.tree_sitter_adapter import TreeSitterAdapter
    adapter = TreeSitterAdapter({"language": "java"})
    result = adapter.find_test_methods("sample_repo/src/test/java/SampleServiceTest.java")
    assert len(result) > 0
    for method in result:
        assert "name" in method

def test_gitpython_scans_sample_repo():
    from tools.adapters.gitpython_adapter import GitPythonAdapter
    adapter = GitPythonAdapter({"path": "./sample_repo"})
    result = adapter.scan_directory("./sample_repo")
    assert result["total_files"] > 0
    assert "java" in result["language_stats"]
```

---

## PHASE 4 — Agent 5 Synthesis + HITL Mechanism

### Goal
Agent 5 runs cross-agent conflict detection, evidence weighing, and BRD assembly. CLI and file-based HITL work correctly. BRD JSON is produced.

### Step 4.1 — Agent 5 Implementation

Agent 5 is the most complex. It must:

1. **Read all four agent outputs from state**
2. **Run cross-agent conflict detection** — find contradictions between scope/journeys/rules/gaps
3. **Run coverage gap detection** — find journeys with no rules, rules with no journeys
4. **Run confidence chain validation** — LOW rule → LOW journey that depends on it
5. **Attempt autonomous resolution** using evidence weighing
6. **Trigger HITL for unresolvable conflicts** (file-based)
7. **Assemble BRD JSON** from all validated outputs
8. **Calculate overall confidence score**
9. **Apply lock gate** — check exit criteria

**`agents/agent_5_synthesis.py`** system prompt must instruct the LLM to:
- Think as a Senior BA doing final review
- Cross-examine four document streams simultaneously
- Produce a conflict register and synthesis decisions
- Assemble a coherent BRD narrative
- Score overall confidence honestly

Key LLM calls in Agent 5:
- **Call 1**: Conflict detection — send all four outputs, ask for conflicts and coverage gaps
- **Call 2**: Evidence weighing — for each conflict, weigh sources and recommend resolution
- **Call 3**: BRD assembly — assemble final narrative from validated findings
- **Call 4**: Consistency check — read assembled BRD, check for contradictions

### Phase 4 Validation Test

Create `tests/test_phase4_hitl.py`:

```python
"""
Phase 4 Validation Tests
Run: pytest tests/test_phase4_hitl.py -v
"""
import pytest
from pathlib import Path
from hitl.hitl_handler import HITLHandler
from config_loader.config_loader import ConfigLoader
from orchestrator.state import get_initial_state

def test_hitl_file_writes_to_pending_folder(tmp_path):
    config = ConfigLoader()
    config.raw["global"]["kb_output"]["hitl_pending"] = str(tmp_path / "HITL")

    from kb.kb_manager import KBManager
    kb_manager = KBManager(config)

    handler = HITLHandler(config, "agent_3_rules", kb_manager)
    state = get_initial_state("test", "./sample_repo", "sample_repo", "0.1.0-poc")

    # Override mode to file for test
    config.raw["agents"]["agent_3_rules"]["hitl"]["ambiguous_rule_translation"]["type"] = "file"
    result_state = handler.handle(
        state=state,
        trigger_name="ambiguous_rule_translation",
        context="Rule extracted: if (amount > THRESHOLD) — meaning unclear",
        options=["Accept agent translation", "Reject and provide correction", "Mark as defer"],
        hitl_type="file"
    )

    # File should be written
    hitl_files = list((tmp_path / "HITL").glob("*.txt"))
    assert len(hitl_files) > 0

    # State should have pending item
    assert len(result_state.get("hitl_pending", [])) > 0

def test_hitl_file_format_contains_required_sections(tmp_path):
    config = ConfigLoader()
    config.raw["global"]["kb_output"]["hitl_pending"] = str(tmp_path / "HITL")

    from kb.kb_manager import KBManager
    kb_manager = KBManager(config)
    handler = HITLHandler(config, "agent_3_rules", kb_manager)
    state = get_initial_state("test", "./sample_repo", "sample_repo", "0.1.0-poc")

    handler.handle(
        state=state,
        trigger_name="ambiguous_rule_translation",
        context="Test context",
        options=["Option 1", "Option 2"],
        hitl_type="file"
    )

    hitl_file = list((tmp_path / "HITL").glob("*.txt"))[0]
    content = hitl_file.read_text()
    assert "CONTEXT:" in content
    assert "OPTIONS:" in content
    assert "YOUR CHOICE" in content
    assert "YOUR COMMENTS" in content
    assert "PENDING_HUMAN_REVIEW" in content

def test_hitl_none_mode_proceeds_automatically():
    config = ConfigLoader()
    from kb.kb_manager import KBManager
    kb_manager = KBManager(config)
    handler = HITLHandler(config, "agent_2_journey", kb_manager)
    state = get_initial_state("test", "./sample_repo", "sample_repo", "0.1.0-poc")

    # tribal_knowledge is mode: none in config
    result_state = handler.handle(
        state=state,
        trigger_name="tribal_knowledge",
        context="Journey only in test suite",
        options=["Proceed", "Skip"],
        hitl_type="none"
    )
    # Should proceed without blocking
    assert result_state is not None
    assert len(result_state.get("hitl_pending", [])) == 0
```

---

## PHASE 5 — Agents 6 & 7 + Orchestrator Final Assembly

### Goal
Agents 6 and 7 run in parallel after Agent 5. Orchestrator assembles final BRD. All KB files are written. Full pipeline runs end-to-end.

### Step 5.1 — Agent 6 (Acceptance Criteria)

Agent 6 reads the locked BRD from state and:
- Converts every journey to Given/When/Then format
- Converts every business rule to a verifiable AC
- Formats as both JSON and Gherkin (.feature file)
- Compares against test suite to find coverage gaps
- Suggests new test cases

LLM prompt should instruct the model to:
- Write ACs as unambiguous, testable statements
- Never use weasel words (should, usually, typically)
- Always name the actor
- Always state the expected outcome clearly

### Step 5.2 — Agent 7 (Risk & Dependency)

Agent 7 reads scope, journeys, rules, and gaps and:
- Maps system dependencies from code (import statements, service calls)
- Flags PII, financial data, audit trail requirements from regulatory_flags
- Scores each risk: likelihood × business impact
- Produces risk_register.json and dependency_register.json

### Phase 5 Validation Test

Create `tests/test_phase5_pipeline.py`:

```python
"""
Phase 5 Validation Tests — Full Pipeline
Run: pytest tests/test_phase5_pipeline.py -v
WARNING: This test calls the Anthropic API and will incur costs.
         Set SKIP_API_TESTS=true to skip.
"""
import pytest
import os
from pathlib import Path

SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

@pytest.mark.skipif(SKIP_API, reason="Skipping API tests")
def test_full_pipeline_runs_on_sample_repo(tmp_path):
    from orchestrator.pipeline import BRDPipeline
    from config_loader.config_loader import ConfigLoader

    config = ConfigLoader()
    config.raw["global"]["kb_output"]["root"] = str(tmp_path / "KB")
    config.raw["global"]["state_store"]["event_log_path"] = str(tmp_path / "events.db")

    pipeline = BRDPipeline(config)
    final_state = pipeline.run("./sample_repo", "SampleService")

    # All agents should have run
    assert final_state["scope_definition"] != {}
    assert final_state["overall_confidence"] > 0

@pytest.mark.skipif(SKIP_API, reason="Skipping API tests")
def test_kb_files_produced_after_pipeline(tmp_path):
    from orchestrator.pipeline import BRDPipeline
    from config_loader.config_loader import ConfigLoader

    config = ConfigLoader()
    config.raw["global"]["kb_output"]["root"] = str(tmp_path / "KB")
    config.raw["global"]["state_store"]["event_log_path"] = str(tmp_path / "events.db")

    pipeline = BRDPipeline(config)
    pipeline.run("./sample_repo")

    kb_root = tmp_path / "KB" / "sample_repo"
    assert kb_root.exists()
    # At minimum, scope_definition.json should exist from Agent 1
    scope_files = list(kb_root.rglob("scope_definition.json"))
    assert len(scope_files) > 0

def test_pipeline_builds_graph_correctly():
    from orchestrator.pipeline import BRDPipeline
    from config_loader.config_loader import ConfigLoader
    config = ConfigLoader()
    pipeline = BRDPipeline(config)
    assert pipeline.graph is not None
```

---

## PHASE 6 — BRD Output + LangSmith Observability

### Goal
`brd_final.docx` is generated from `brd_final.json`. LangSmith traces are visible. Run metadata is complete.

### Step 6.1 — BRD Generator

Create `output/brd_generator.py`:

```python
"""
BRD Generator — produces brd_final.docx from brd_final.json.
Uses python-docx. Structure follows our architecture design.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

class BRDGenerator:

    def __init__(self):
        self.doc = Document()

    def generate(self, brd_json: Dict, output_path: str) -> str:
        """Generate Word document from BRD JSON. Returns output path."""
        self._add_cover_page(brd_json)
        self._add_section("1. Scope Definition", brd_json.get("scope", {}))
        self._add_section("2. Journey Inventory", brd_json.get("journeys", []))
        self._add_section("3. Business Rules", brd_json.get("business_rules", []))
        self._add_section("4. Gap Analysis", brd_json.get("gaps", []))
        self._add_section("5. Acceptance Criteria", brd_json.get("acceptance_criteria", []))
        self._add_section("6. Risk Register", brd_json.get("risks", []))
        self._add_metadata(brd_json)

        self.doc.save(output_path)
        return output_path

    def _add_cover_page(self, brd_json: Dict):
        self.doc.add_heading("BUSINESS REQUIREMENTS DOCUMENT", 0)
        p = self.doc.add_paragraph()
        p.add_run(f"Component: {brd_json.get('component_name', 'Unknown')}\n").bold = True
        p.add_run(f"Version: {brd_json.get('brd_version', '0.1.0-poc')}\n")
        p.add_run(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
        p.add_run(f"Confidence: {brd_json.get('overall_confidence', 0.0):.0%}\n")
        p.add_run(f"Status: {'LOCKED' if brd_json.get('locked') else 'DRAFT'}\n")
        self.doc.add_page_break()

    def _add_section(self, title: str, content: Any):
        self.doc.add_heading(title, level=1)
        if isinstance(content, dict):
            for key, value in content.items():
                self.doc.add_heading(key.replace("_", " ").title(), level=2)
                if isinstance(value, list):
                    for item in value:
                        self.doc.add_paragraph(str(item), style="List Bullet")
                else:
                    self.doc.add_paragraph(str(value))
        elif isinstance(content, list):
            for i, item in enumerate(content, 1):
                if isinstance(item, dict):
                    name = item.get("name", item.get("id", f"Item {i}"))
                    self.doc.add_heading(name, level=2)
                    for key, value in item.items():
                        if key not in ["name", "id"]:
                            p = self.doc.add_paragraph()
                            p.add_run(f"{key.replace('_', ' ').title()}: ").bold = True
                            p.add_run(str(value))
                else:
                    self.doc.add_paragraph(str(item), style="List Bullet")
        else:
            self.doc.add_paragraph(str(content))

    def _add_metadata(self, brd_json: Dict):
        self.doc.add_page_break()
        self.doc.add_heading("Document Metadata", level=1)
        meta = {
            "Run ID": brd_json.get("run_id", ""),
            "Repo": brd_json.get("repo_name", ""),
            "Generated By": "BRD Agent POC v0.1.0",
            "Warnings": len(brd_json.get("warnings", [])),
            "Open Items": len(brd_json.get("open_items", [])),
            "HITL Pending": len(brd_json.get("hitl_pending", []))
        }
        for key, value in meta.items():
            p = self.doc.add_paragraph()
            p.add_run(f"{key}: ").bold = True
            p.add_run(str(value))
```

### Step 6.2 — LangSmith Integration

In `main.py` and in each agent's `call_llm()`, ensure LangSmith tracing is active:

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "brd_agent_poc")
```

LangSmith traces automatically when `LANGCHAIN_API_KEY` is set and `LANGCHAIN_TRACING_V2=true`. No additional code needed when using LangChain wrappers. For direct `anthropic` client calls, wrap with LangChain's `ChatAnthropic` to get automatic tracing, or use LangSmith's `traceable` decorator:

```python
from langsmith import traceable

@traceable(name="agent_llm_call")
def call_llm_traced(model, system, user, max_tokens):
    # your anthropic call here
    pass
```

### Phase 6 Validation Test

Create `tests/test_phase6_output.py`:

```python
"""
Phase 6 Validation Tests
Run: pytest tests/test_phase6_output.py -v
"""
import pytest
import json
from pathlib import Path
from output.brd_generator import BRDGenerator

def test_brd_generator_produces_docx(tmp_path):
    generator = BRDGenerator()
    sample_brd = {
        "component_name": "SampleService",
        "brd_version": "0.1.0-poc",
        "overall_confidence": 0.75,
        "locked": True,
        "run_id": "test-123",
        "repo_name": "sample_repo",
        "scope": {
            "in_scope": ["processPayment", "checkEligibility"],
            "out_of_scope": ["reporting"]
        },
        "journeys": [
            {"name": "Standard Payment", "actor": "Customer",
             "confidence": "HIGH", "type": "happy"}
        ],
        "business_rules": [
            {"id": "BR-001", "name": "High Value Threshold",
             "plain_english": "Transactions over $1000 require manager approval"}
        ],
        "gaps": [],
        "acceptance_criteria": [
            {"id": "AC-001", "journey": "Standard Payment",
             "given": "Customer has valid account",
             "when": "Payment of $500 is submitted",
             "then": "Payment is processed successfully"}
        ],
        "risks": [],
        "warnings": [],
        "open_items": [],
        "hitl_pending": []
    }

    output_path = str(tmp_path / "brd_test.docx")
    result = generator.generate(sample_brd, output_path)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0

def test_brd_json_schema_valid():
    import jsonschema
    schema = {
        "type": "object",
        "required": ["component_name", "brd_version", "scope",
                    "journeys", "business_rules"],
        "properties": {
            "component_name": {"type": "string"},
            "brd_version": {"type": "string"},
            "scope": {"type": "object"},
            "journeys": {"type": "array"},
            "business_rules": {"type": "array"}
        }
    }
    sample = {
        "component_name": "Test",
        "brd_version": "0.1.0",
        "scope": {},
        "journeys": [],
        "business_rules": []
    }
    jsonschema.validate(sample, schema)  # Should not raise
```

---

## PHASE 7 — Integration Testing + Self-Correction Loop

### Goal
Full pipeline runs on sample repo. All outputs are valid. Self-correction handles common failures. Ready for demo.

### Step 7.1 — Main Entry Point

Create `main.py`:

```python
"""
BRD Agent POC — Main Entry Point
Usage:
  python main.py --repo ./path/to/repo
  python main.py --repo ./path/to/repo --component MyComponent
  python main.py --diagram   (generate architecture diagram only)
"""
import os
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.rule import Rule

load_dotenv()

# LangSmith tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

console = Console()

def main():
    parser = argparse.ArgumentParser(
        description="BRD Agent POC — Autonomous BRD Generation"
    )
    parser.add_argument("--repo", type=str, help="Path to cloned repo")
    parser.add_argument("--component", type=str, default="",
                       help="Component name (optional)")
    parser.add_argument("--config", type=str, default="config/config.yaml",
                       help="Path to config file")
    parser.add_argument("--diagram", action="store_true",
                       help="Generate architecture diagram only")
    args = parser.parse_args()

    if args.diagram:
        from visualizer.generate_diagram import main as gen_diagram
        gen_diagram()
        return

    if not args.repo:
        console.print("[red]Error: --repo is required[/red]")
        console.print("Usage: python main.py --repo ./path/to/repo")
        sys.exit(1)

    repo_path = Path(args.repo)
    if not repo_path.exists():
        console.print(f"[red]Error: Repo path not found: {repo_path}[/red]")
        sys.exit(1)

    # Validate API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY not set in .env[/red]")
        sys.exit(1)

    console.print(Rule("[bold blue]BRD Agent POC[/bold blue]"))
    console.print(f"[dim]Repo: {repo_path.absolute()}[/dim]")
    console.print(f"[dim]Config: {args.config}[/dim]\n")

    from config_loader.config_loader import ConfigLoader
    from orchestrator.pipeline import BRDPipeline

    config = ConfigLoader(args.config)
    pipeline = BRDPipeline(config)

    try:
        final_state = pipeline.run(str(repo_path), args.component)

        console.print("\n[bold green]✅ BRD Generation Complete[/bold green]")

        if final_state.get("brd_docx_path"):
            console.print(f"[green]📄 BRD Document: {final_state['brd_docx_path']}[/green]")
        if final_state.get("brd_json_path"):
            console.print(f"[green]📋 BRD JSON: {final_state['brd_json_path']}[/green]")

        kb_path = Path(config.raw["global"]["kb_output"]["root"])
        console.print(f"[green]💾 KB Output: {kb_path / final_state['repo_name']}[/green]")

        if final_state.get("hitl_pending"):
            console.print(f"\n[yellow]⚡ {len(final_state['hitl_pending'])} items pending human review[/yellow]")
            console.print("[dim]Check HITL_PENDING/ folder, fill in responses, re-run.[/dim]")

        if final_state.get("warnings"):
            console.print(f"\n[yellow]⚠️  {len(final_state['warnings'])} warnings generated[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Run interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Pipeline error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Step 7.2 — Self-Correction Instructions

When running the integration test, if failures occur apply these corrections:

**Problem: LLM returns invalid JSON**
- Solution: Add retry logic in `_parse_llm_response()` — on parse error, send the raw response back to the LLM with "The above is not valid JSON. Fix it and return ONLY valid JSON with no other text."
- Max retries: 3

**Problem: Tree-sitter fails to parse Java file**
- Solution: Fall through to javalang. If javalang also fails, use regex-based extraction as final fallback. Log the failure but do not block.

**Problem: ChromaDB index fails**
- Solution: KB indexing failure is non-fatal. Log it, continue. The JSON file is always the primary KB storage.

**Problem: Agent produces empty output**
- Solution: Check if the repo path is correct in config. Check if the API key is set. Ensure `sample_repo/` exists with the Java files created in Phase 1.

**Problem: HITL blocks in automated test**
- Solution: In tests, mock the HITL handler to auto-accept option 1. Never block on HITL in automated tests.

### Phase 7 Integration Test

Create `tests/test_phase7_integration.py`:

```python
"""
Phase 7 — Full Integration Test
Run: pytest tests/test_phase7_integration.py -v -s
WARNING: Calls Anthropic API. Set SKIP_API_TESTS=true to skip.
"""
import pytest
import os
from pathlib import Path

SKIP_API = os.getenv("SKIP_API_TESTS", "false").lower() == "true"

@pytest.mark.skipif(SKIP_API, reason="Skipping API integration tests")
def test_end_to_end_brd_generation(tmp_path):
    """Full pipeline runs and produces all expected outputs."""
    from orchestrator.pipeline import BRDPipeline
    from config_loader.config_loader import ConfigLoader

    config = ConfigLoader()
    config.raw["global"]["kb_output"]["root"] = str(tmp_path / "KB")
    config.raw["global"]["state_store"]["event_log_path"] = str(tmp_path / "events.db")
    config.raw["global"]["kb_output"]["hitl_pending"] = str(tmp_path / "HITL")

    pipeline = BRDPipeline(config)
    final_state = pipeline.run("./sample_repo", "SampleService")

    # Core outputs
    assert final_state.get("scope_definition"), "Scope definition must be produced"
    assert final_state.get("overall_confidence", 0) > 0, "Confidence must be calculated"

    # KB files
    kb_root = tmp_path / "KB" / "sample_repo"
    assert kb_root.exists(), "KB folder must be created"

    # Event log
    event_log_path = tmp_path / "events.db"
    assert event_log_path.exists(), "Event log must be created"

    from orchestrator.event_log import EventLog
    log = EventLog(str(event_log_path))
    events = log.get_events_for_run(final_state["run_id"])
    assert len(events) > 0, "Events must be logged"

    # Human feedback fields
    assert all(
        f"agent_{i}" in final_state["human_feedback"]
        for i in range(1, 8)
    ), "All human feedback fields must be present"

def test_diagram_generates_correctly():
    """Visualizer produces valid Mermaid diagram."""
    from visualizer.generate_diagram import generate_mermaid
    from config_loader.config_loader import ConfigLoader

    config = ConfigLoader()
    diagram = generate_mermaid(config)

    assert "graph TD" in diagram
    assert "ORCH" in diagram
    assert "KB" in diagram
    assert "INTAKE" in diagram

def test_config_reflects_disabled_tools():
    """Disabled tools show as disabled in diagram."""
    from visualizer.generate_diagram import generate_tool_summary
    from config_loader.config_loader import ConfigLoader

    config = ConfigLoader()
    summary = generate_tool_summary(config)

    # Jira should show as disabled
    assert "jira_loader" in summary
    assert "⚫ Disabled" in summary

def test_all_required_kb_output_keys_defined():
    """Every agent has KB output keys defined in config."""
    from config_loader.config_loader import ConfigLoader
    config = ConfigLoader()

    for agent_name in ["agent_1_discovery", "agent_2_journey", "agent_3_rules",
                       "agent_4_gap", "agent_5_synthesis", "agent_6_ac", "agent_7_risk"]:
        agent_cfg = config.get_agent_config(agent_name)
        kb_output = agent_cfg.get("kb_output", {})
        assert len(kb_output) > 0, f"{agent_name} must have kb_output defined"
```

---

## QUICK START GUIDE

After building all phases, a new developer can get started with:

```bash
# 1. Clone the repo
git clone <repo_url>
cd brd_agent_poc

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Configure paths
# Edit config/config.yaml
# Set resources.repo.path to your cloned Legacy repo path

# 5. Generate architecture diagram (optional — view current config)
python main.py --diagram
# Open architecture.md in GitHub or Mermaid viewer

# 6. Run Phase 1 tests (no API needed)
SKIP_API_TESTS=true pytest tests/test_phase1_config.py -v

# 7. Run full pipeline on sample repo
python main.py --repo ./sample_repo --component SampleService

# 8. Run full pipeline on real repo (when available)
python main.py --repo /path/to/legacy/repo --component YourComponent

# 9. Check outputs
# KB/sample_repo/   — all agent output files
# HITL_PENDING/     — any items needing human review
# architecture.md   — framework diagram
```

---

## PHASE 2 ROADMAP (For Future Development)

These items are deliberately out of scope for POC but the code should be structured to support them:

1. **Full Knowledge Layer** — Replace JSON files + ChromaDB with LightRAG. The ChromaDB index created in POC becomes the seed for LightRAG.

2. **Cross-Application Reuse** — KB query hook (currently disabled) queries across application runs to reuse journeys, rules, and decisions from prior migrations.

3. **Jira & Confluence Integration** — Enable jira_loader and confluence_loader adapters when tokens are available.

4. **NSA Spec Integration** — Enable nsa_spec_parser when NSA OpenAPI spec is available. Agent 4 gap analysis becomes much richer.

5. **Ontology Extractor** — Enable when the existing organizational tool is connected.

6. **Team UI** — Wrap config.yaml editing and run execution in a simple Streamlit or Gradio interface for non-technical team members.

7. **HITL Module** — Separate human feedback into its own LangGraph node that can pause the pipeline, accept async feedback, and resume. Remove need to re-run entire pipeline for HITL responses.

8. **Production Deployment** — Docker packaging, persistent hosting, multi-user support.

---

## NOTES FOR THE AI CODING AGENT

1. **Do not skip phases** — each phase builds on the previous. Run tests before moving forward.
2. **Config is the source of truth** — if something feels hardcoded, move it to config.yaml.
3. **Stub adapter is your friend** — if a tool import fails, fall through to stub. Never let a missing tool crash an agent.
4. **LLM prompts are critical** — the system prompts encode the BA cognitive model. Spend time making them clear, structured, and specific. The quality of the BRD depends entirely on prompt quality.
5. **JSON parsing needs error handling** — LLMs sometimes produce markdown-wrapped JSON or trailing text. Always strip, always try/except, always have a fallback.
6. **Test with sample repo first** — before touching a real Legacy repo, verify the full pipeline works on sample_repo/. This avoids expensive API calls during debugging.
7. **LangSmith is your observability** — when something goes wrong, LangSmith shows you exactly what prompt was sent, what the LLM returned, and where it failed.
8. **KB files are readable** — after running, open the JSON files in KB/ to see what each agent actually found. This is your primary debugging tool alongside LangSmith.

---

*End of BRD Agent POC Build Instructions*
*Version: 1.0 | Framework: BRD Agentic Framework POC*
