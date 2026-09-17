# System Specification & Architecture Blueprint

## 1. Project Overview & System Goals

This repository implements Agent 1 of the SDLC Agentic Framework: a local, multi-agent requirement brainstorming system that accepts a new requirement, grounds it in existing BRDs and code, conducts an open-ended back-and-forth conversation with a stakeholder until the requirement is fully understood, and produces a revised, signed BRD for sign-off. Agent 2 (Requirement Breakdown Agent) consumes the signed BRD that this agent writes.

Primary goals:
- Accept a raw requirement as text or as an uploaded document in common business formats (Markdown, plain text, DOCX, XLSX/CSV, PDF, images).
- Fetch the most relevant existing BRDs from a local KB store using TF-IDF matching.
- Scan configured code repositories for pre-existing or similar implementations.
- Build and maintain a persistent context graph linking the requirement to BRDs, code findings, entities, and decisions.
- Drive a two-way brainstorming conversation: one focused clarifying question at a time, adapting to user answers, until both sides agree the requirement is understood.
- Generate a complete revised BRD in Markdown for each impacted BRD/repo, multi-BRD/multi-repo aware.
- Support a sign-off loop so users can approve or request revisions before finalization.
- Write a signed, versioned BRD to the KB on approval.
- Trace every agent invocation to disk for full replay and audit.
- Report token usage and estimated cost per turn, per session, and at finalization.

Target runtime:
- Python 3.10+.
- Local execution on Windows, macOS, or Linux.
- CLI mode via `python main.py`.
- API/UI mode via FastAPI + Uvicorn at `http://127.0.0.1:8100`.
- Optional LLM backends: VS Code Copilot gateway, Anthropic, OpenAI-compatible, Gemini, or offline mock.

---

## 2. Tech Stack & Dependencies

### Core stack
- Language: Python.
- Orchestration: LangGraph.
- API layer: FastAPI.
- Server: Uvicorn.
- Data validation: Pydantic.
- Configuration: YAML plus `.env` fallback.
- HTTP: Requests.
- Terminal UI: Rich.

### Required Python packages
Defined in `requirements.txt`:
- `langgraph`
- `langchain-core`
- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `python-multipart`
- `pyyaml`
- `requests`
- `rich`
- `python-docx`
- `openpyxl`
- `pypdf`
- `tiktoken`

### Optional packages
Defined in `requirements-optional.txt`:
- `anthropic`
- `openai`
- `google-generativeai`
- `pytesseract`
- `Pillow`

### Configuration files
- `pyproject.toml`: project metadata, Ruff, pytest, setuptools package discovery.
- `config.example.yaml`: canonical config template.
- `config.yaml`: active runtime config.
- `.env`: local secrets and environment overrides.
- `.env.example`: sample environment file.

### Runtime prerequisites and environment variables
- Python 3.10 or newer.
- A BRD store in `data/brd_store` or uploaded documents.
- Optional VS Code Copilot proxy service when using `provider: vscode_copilot`.
- Optional API keys for cloud providers:
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY` or `GOOGLE_API_KEY`

---

## 3. Project Directory Structure

### Top level
- `main.py`: entrypoint that dispatches to CLI or Uvicorn.
- `README.md`: human-facing overview and usage.
- `pyproject.toml`: package metadata and tooling.
- `requirements.txt`: mandatory dependencies.
- `requirements-optional.txt`: optional provider/OCR dependencies.
- `config.example.yaml`: config template.
- `config.yaml`: active config.
- `.env`: local environment variables.
- `.env.example`: example environment file.
- `tests/`: offline test suite.
- `ui/`: static single-page web UI.
- `app/`: all application code.
- `data/`: generated runtime artifacts and stores.

### Application package: app/

#### `app/__init__.py`
- Package export surface: `BrainstormAgent`, `AppConfig`, `load_config`.

#### `app/agent.py`
- High-level facade over the orchestrator.
- Owns session bootstrap, resume logic, upload ingestion, usage aggregation, and per-turn result shaping.

#### `app/config.py`
- Loads config from defaults, YAML, `.env`, and environment overrides.
- Defines `LLMConfig`, `BRDConfig`, `CodeScanConfig`, `StorageConfig`, `AppConfig`.
- Exposes resolved path helpers (`brd_store_path`, `sessions_path`, `graph_path`, `traces_path`).

#### `app/cli.py`
- Interactive terminal workflow and command dispatch.
- Provides `init`, `run`, `list`, and `latest` behaviors.

#### `app/artifacts.py`
- Multi-format artifact ingestion into plain text.
- Supports `.md`, `.txt`, `.docx`, `.xlsx`, `.csv`, `.pdf`, and image (OCR / vision).

#### `app/retrieval.py`
- Lightweight TF-IDF ranking for BRD/document chunk selection.
- Functions: `tokenize`, `chunk_text`, `rank_chunks`, `top_snippets`.

#### `app/brd/`
- BRD discovery, TF-IDF matching, versioning, and signed-revision writing.

#### `app/graph/`
- Persisted directed context graph.
- Supports `add_node`, `add_edge`, Mermaid export, JSON serialization.

#### `app/llm/`
- Provider abstraction, pricing, usage metering, and vision/OCR helpers.
- Factory: `build_llm(cfg)`.

#### `app/memory/`
- Session persistence and feature-key indexing.

#### `app/orchestrator/`
- Shared state definition and LangGraph orchestration logic.
- `state.py`: `BrainstormState` TypedDict and `new_state()` factory.
- `graph.py`: all node methods and `run_turn()` entry point.

#### `app/prompts/`
- Per-agent prompt modules (`SYSTEM` + `USER_TEMPLATE` variables).
- `render.py`: `{{ }}` variable renderer.
- `__init__.py`: `PromptLibrary` class that loads and renders prompts by agent name.

#### `app/tools/`
- `code_tools.py`: `scan_repos()` (keyword scan) and `summarize_hits()`.

#### `app/trace/`
- `AgentTrace` dataclass, `Tracer` class, and `index.json` management.
- One JSON file per agent invocation, named `NNNN_<agent>.json`.

#### `app/api/`
- FastAPI server with endpoints for session start, turn processing, uploads, trace inspection.
- Pydantic request/response schemas in `schemas.py`.

#### `app/agents/`
- Single-responsibility sub-agents: `IntakeAgent`, `BRDFetchAgent`, `CodeScanAgent`, `ContextGraphAgent`, `ConversationAgent`, `BRDWriterAgent`, `SignoffAgent`.
- `base.py`: `BaseAgent`, `AgentContext`, trace wrapper, LLM helpers.

### Package-internal file inventory

#### app/agents/
- `base.py`: `BaseAgent`, `AgentContext` dataclass, trace wrapper, `_llm_json`, `_llm_text` helpers.
- `intake_agent.py`: normalize raw requirement into structured `intake_summary`; seed context graph.
- `brd_fetch_agent.py`: TF-IDF BRD retrieval; populate `brd_matches`; add BRD nodes to graph.
- `code_scan_agent.py`: keyword repo scan; populate `code_hits`, `code_findings`; add code-finding node.
- `context_graph_agent.py`: LLM-driven entity/relationship extraction into graph under `kg:` namespace.
- `conversation_agent.py`: two-way brainstorming; decide `ask` vs `ready`; track `understanding`; surface conflicts.
- `brd_writer_agent.py`: write revised BRD Markdown for each target in `impacted_brds`; populate `draft_brds`.
- `signoff_agent.py`: keyword-based `approve` vs `revise` classification.
- `__init__.py`: public agent exports.

#### app/orchestrator/
- `state.py`: `BrainstormState` TypedDict (all shared fields) and `new_state()` factory.
- `graph.py`: `Orchestrator` class — agent nodes (`node_intake`, `node_brd_fetch`, `node_code_scan`, `node_context_graph`, `node_analyze`, `node_generate`, `node_signoff`), control nodes (`node_incorporate`, `node_ask`, `node_propose`, `node_present`, `node_finalize`), routing logic, `run_turn()`.
- `__init__.py`: exports orchestration surface.

#### app/prompts/
- `render.py`: `{{ variable }}` template renderer.
- `intake_agent.py`: `SYSTEM` + `USER_TEMPLATE` for intake.
- `conversation_agent.py`: `SYSTEM` + `USER_TEMPLATE` for brainstorming.
- `brd_writer_agent.py`: `SYSTEM` + `USER_TEMPLATE` for BRD writing.
- `context_graph_agent.py`: `SYSTEM` + `USER_TEMPLATE` for graph extraction.
- `__init__.py`: `PromptLibrary` that loads modules and exposes `system(name)` / `render_user(name, **kwargs)`.

#### app/llm/
- `base.py`: `BaseLLM` abstract class, `Message` dict type, `LLMResponse` dataclass, `extract_json()`.
- `providers.py`: concrete providers (`VsCodeCopilotLLM`, `AnthropicLLM`, `OpenAILLM`, `GeminiLLM`, `MockLLM`) and `build_llm(cfg)` factory.
- `usage.py`: `UsageRecord` dataclass, `UsageMeter` accumulator.
- `pricing.py`: model price table (USD per 1M tokens).
- `vision.py`: image-to-text helper (OCR / vision model).

#### app/brd/
- `repository.py`: `BRDRepository` — file discovery, TF-IDF matching (`find_relevant`), signed-revision writing (`save_revision`).
- `template.py`: `BRD_SECTIONS` list used by `BRDWriterAgent`.

#### app/graph/
- `context_graph.py`: `ContextGraph` — `add_node`, `add_edge`, JSON persistence, Mermaid export, cycle-safe traversal.

#### app/memory/
- `session_store.py`: `SessionStore` — session persistence (JSON), feature-key index, `list_sessions`, `get_session`, `save_session`.

#### app/trace/
- `tracer.py`: `AgentTrace` dataclass, `Tracer` — `new_trace`, `close` (writes JSON), `load_index`, `load_trace`.

#### app/api/
- `server.py`: FastAPI app; endpoints `/api/start`, `/api/turn`, `/api/upload`, `/api/sessions`, `/api/sessions/{id}/trace`, `/trace/{seq}`; static UI mount.
- `schemas.py`: `StartRequest`, `TurnRequest`, `TurnResponse`, `UploadResponse` Pydantic models.

### Generated data tree
The `data/` folder is runtime state, not source code:
- `data/brd_store/`: existing BRDs scanned by `BRDFetchAgent`. Signed revisions live in `revisions/`.
- `data/sessions/`: persisted `BrainstormState` snapshots (one JSON per session).
- `data/graph/`: serialized context graph JSON (one file per feature).
- `data/traces/<session_id>/`: one JSON file per agent invocation, plus `index.json`.

---

## 4. Data Schemas, Interfaces & State

### Configuration models

#### `LLMConfig`
- `provider: str` default `vscode_copilot`
- `model: str` default `gpt-4o`
- `proxy_url: str` default `http://127.0.0.1:3100`
- `temperature: float` default `0.2`
- `max_tokens: int` default `4096`
- `request_timeout: int` default `120`
- `input_price_per_mtok: float | None`
- `output_price_per_mtok: float | None`

#### `BRDConfig`
- `store_dir: str` default `data/brd_store`
- `extra_source_dirs: list[str]`
- `glob_patterns: list[str]` default `["**/*.md"]`
- `brd_filename_markers: list[str]` default `["brd", "requirement", "prd"]`

#### `CodeScanConfig`
- `repo_paths: list[str]`
- `max_files_per_repo: int`
- `max_snippet_chars: int`
- `code_extensions: list[str]`
- `ignore_dirs: list[str]`

#### `StorageConfig`
- `sessions_dir: str` default `data/sessions`
- `graph_dir: str` default `data/graph`
- `traces_dir: str` default `data/traces`

#### `AppConfig`
- Aggregates `llm`, `brd`, `code`, `storage`.
- Path helpers: `brd_store_path`, `sessions_path`, `graph_path`, `traces_path`.

### Orchestrator state

#### `BrainstormState` (TypedDict, all fields optional)
- Identity: `feature_key`, `feature_title`, `phase`
- Conversation: `messages`, `user_input`, `new_requirement`
- Retrieved context: `artifacts`, `brd_matches`, `code_hits`, `code_findings`
- Structured context: `intake_summary`, `graph_delta`, `understanding`
- Orchestrator reasoning: `round`, `existing_impl`, `impacted_repos`, `impacted_brds`
- Transient turn control: `decision`, `analyst_message`
- Turn output: `pending_question`, `awaiting`, `result_message`
- Generation: `draft_brds`
- Finalization: `signed`, `finalized_paths`
- Accounting: `usage`, `turn_usage`

#### `new_state(feature_key, feature_title, requirement)`
Factory that returns a fully initialized `BrainstormState` with all fields at safe defaults.

### BRD / artifact schema

#### `Artifact`
- `name`, `path`, `kind`, `fmt`, `text`, `meta`

#### `BRDMatch`
- `name`, `path`, `score`, `snippet`, `text`

#### BRD draft object
- `name`: target BRD filename.
- `content`: full revised BRD Markdown text.

### LLM schema and usage tracking

#### `Message`
- A dict shaped as `{role: system|user|assistant, content: str}`.

#### `LLMResponse`
- `content`, `input_tokens`, `output_tokens`, `model`, `raw`

#### `UsageRecord`
- `label`, `model`, `input_tokens`, `output_tokens`, `cost_usd`

#### `UsageMeter`
- Accumulates usage records; produces totals, summaries, and serialized state.

### Tracing schema

#### `AgentTrace`
- `seq`, `agent`, `session_id`, `phase`, `started_at`, `ended_at`, `duration_ms`
- `used_llm`, `messages`, `raw_output`, `output`, `usage`, `ok`, `error`

#### Trace index entry
- `seq`, `agent`, `phase`, `ok`, `used_llm`, `total_tokens`, `cost_usd`, `at`, `file`

### Context graph node types
- `requirement`: the raw incoming requirement.
- `requirement_summary`: normalized intake output.
- `BRD`: a matched existing BRD.
- `code_finding`: repo scan result.
- `decision`: per-round `ConversationAgent` decision.
- `BRD_draft`: a generated draft BRD.
- `BRD_signed`: the finalized signed revision.
- `entity` (under `kg:` namespace): domain entities extracted by `ContextGraphAgent`.

### API schemas

#### `StartRequest`
- `feature`, `feature_key`, `title`, `brd_names`, `uploads`, `resume`

#### `TurnRequest`
- `message`, `uploads`

#### `TurnResponse`
- `session_id`, `feature_key`, `phase`, `awaiting`, `message`, `pending_question`
- `feature_title`, `brd_matches`, `draft_brds`, `finalized_paths`
- `turn_usage`, `session_usage`, `context_graph`, `trace`

#### `UploadResponse`
- `paths`, `names`

---

## 5. Functional Modules & Implementation Details

### 5.1 Entrypoint and CLI

#### `main.py`
- `serve(host, port)`: runs `uvicorn.run("app.api.server:app", ...)`.
- `main()`: dispatches `serve` or forwards to `app.cli.main(argv)`.

#### `app/cli.py`
- Prompts user for requirement text, LLM choice, and optional uploads.
- Iterates `run_turn` until `awaiting=False` (done).
- Supports `/exit` or `/quit` for early exit.
- `init()`: creates data folders.
- `list()`: prints session summaries.
- `latest()`: prints latest artifact paths.
- `main(argv)`: parses subcommands `init`, `run`, `list`, `latest`.

### 5.2 Orchestrator and graph

#### `app/orchestrator/graph.py` — `Orchestrator`
**Agent nodes** (each delegates to the named sub-agent):
- `node_intake` → `IntakeAgent.run(state)`
- `node_brd_fetch` → `BRDFetchAgent.run(state)`
- `node_code_scan` → `CodeScanAgent.run(state)`
- `node_context_graph` → `ContextGraphAgent.run(state)`
- `node_analyze` → `ConversationAgent.run(state)`
- `node_generate` → `BRDWriterAgent.run(state)`
- `node_signoff` → `SignoffAgent.run(state)`

**Control nodes** (no LLM reasoning):
- `node_incorporate`: folds `user_input` into `messages` transcript.
- `node_ask`: composes clarifying question message, sets `awaiting=True`, increments `round`.
- `node_propose`: offers to generate BRD; sets `phase=awaiting_generate`, `awaiting=True`.
- `node_present`: previews `draft_brds`; sets `phase=signoff`, `awaiting=True`.
- `node_finalize`: calls `brd_repo.save_revision` for each draft; writes signed BRDs; sets `phase=done`, `signed=True`.

**Routing logic**:
- After `node_analyze`: if `decision == "ask"` → `node_ask`, else → `node_propose`.
- After `node_propose` (next turn): if user reply contains confirm word → `node_generate`, else → `node_incorporate` → `node_analyze`.
- After `node_signoff`: if `decision == "approve"` → `node_finalize`, else → `node_generate`.

**`run_turn(state, user_message)`**:
- Merges `user_message` into state, advances the graph until `awaiting=True` or `phase=done`.
- Returns updated state with `result_message` and `awaiting` flag.

### 5.3 Sub-agents

#### `IntakeAgent`
- Reads `new_requirement` + `artifacts` from state.
- Sets `feature_title` if not present.
- Calls LLM with `intake_agent` prompts to produce `intake_summary` JSON (`summary`, `confidence`, `greenfield`).
- Adds `req:<feature_key>` and `intake:<feature_key>` nodes to context graph.

#### `BRDFetchAgent`
- Calls `brd_repo.find_relevant(query, top_k=3)` (TF-IDF matching).
- Populates `brd_matches` list.
- Adds `brd:<name>` nodes to context graph with `GROUNDED_IN` edges from `req:`.

#### `CodeScanAgent`
- Calls `scan_repos(cfg, query)` — keyword grep over configured `code.repo_paths`.
- Populates `code_hits` list and `code_findings` summary text.
- Adds `code:<feature_key>` node to context graph with `MAY_OVERLAP` edge.

#### `ContextGraphAgent`
- Calls LLM with `context_graph_agent` prompts to extract JSON `{nodes: [...], edges: [...]}`.
- Merges nodes (under `kg:` namespace) and edges into the persistent context graph.
- Updates `graph_delta`.

#### `ConversationAgent`
- Builds prompt from last 14 messages, `intake_summary`, `brd_context`, `code_findings`, `understanding`.
- Calls LLM; expects JSON with `decision` (`ask`/`ready`), `message`, `question`, `understanding`, `existing_implementation`, `impacted_brds`, `impacted_repos`.
- Adds a `decision:<feature_key>:<round>` node to graph.
- Returns `decision`, `analyst_message`, `pending_question`, `understanding`, `existing_impl`, `impacted_brds`, `impacted_repos`.

#### `BRDWriterAgent`
- Iterates over `impacted_brds` (or `brd_matches` names, or a new BRD name).
- For each target, calls LLM with `brd_writer_agent` prompts, passing the full transcript, `understanding`, code findings, and original BRD text.
- Appends a dict `{name, content}` to `draft_brds`.
- Adds `draft:<name>` nodes with `PRODUCES` edges to context graph.

#### `SignoffAgent`
- Keyword check: if `user_input` contains any `_APPROVE_WORDS` word → `decision=approve`, else `decision=revise`.
- No LLM call.

### 5.4 BRD repository

#### `app/brd/repository.py` — `BRDRepository`
- `find_relevant(query, top_k)`: scans `brd_store_dir` + `extra_source_dirs` for `*.md` files; TF-IDF ranks them; returns `BRDMatch` list.
- `save_revision(base_name, content, feature, signed)`: writes versioned file to `data/brd_store/revisions/<feature>/` with a timestamp suffix.

#### `app/brd/template.py`
- `BRD_SECTIONS`: ordered list of standard BRD section headings passed to `BRDWriterAgent` for structured generation.

### 5.5 Context graph

#### `app/graph/context_graph.py` — `ContextGraph`
- `add_node(node_id, type, label, **meta)`: upsert a node.
- `add_edge(src, dst, relationship, strength)`: add a directed edge.
- `save()` / `load()`: JSON persistence to `data/graph/<feature_key>.json`.
- `to_mermaid()`: exports graph as a Mermaid flowchart string.

### 5.6 LLM providers

#### `app/llm/providers.py`
- `VsCodeCopilotLLM`: calls VS Code Copilot proxy at `proxy_url` using OpenAI-compatible `/v1/chat/completions`.
- `AnthropicLLM`: calls `anthropic.Anthropic` client.
- `OpenAILLM`: calls OpenAI-compatible endpoint.
- `GeminiLLM`: calls Google Generative AI.
- `MockLLM`: returns canned JSON for offline testing.
- `build_llm(cfg)`: factory that instantiates the correct provider from `cfg.llm.provider`.

### 5.7 Tracing

#### `app/trace/tracer.py`
- `Tracer.__init__(traces_dir, session_id)`: creates `data/traces/<session_id>/`.
- `new_trace(agent, phase)`: returns a new `AgentTrace` with an auto-incremented `seq`.
- `close(trace)`: finalizes timing, writes `NNNN_<agent>.json`, updates `index.json`.
- `load_index()`: reads `index.json` as a list of trace index entries.
- `load_trace(seq)`: reads a specific trace file by sequence number.

### 5.8 Retrieval

#### `app/retrieval.py`
- `tokenize(text)`: lowercased word tokenizer.
- `chunk_text(text, source, target_chars=1200, overlap=150)`: splits long text into overlapping chunks.
- `rank_chunks(query, chunks, top_k=5)`: TF-IDF cosine similarity ranking.
- `top_snippets(query, text, source, top_k=4, max_chars=4000)`: convenience wrapper that chunks then ranks.

### 5.9 Artifact ingestion

#### `app/artifacts.py`
- `ingest(path_or_bytes, name, kind)`: dispatches to format-specific readers.
- Supports `.md`, `.txt` (plain read), `.docx` (python-docx), `.pdf` (pypdf), `.xlsx`/`.csv` (openpyxl/csv), images (pytesseract OCR or vision model).

### 5.10 Session memory

#### `app/memory/session_store.py` — `SessionStore`
- `save_session(feature_key, state)`: serializes and writes session JSON.
- `get_session(session_id)`: loads session by ID.
- `list_sessions()`: returns list of session metadata dicts.
- `find_by_feature(feature_key)`: returns the latest session for a feature key.

---

## 6. Entry Points & Execution Flow

### CLI flow
```
python main.py
  └─ app/cli.py::main()
       └─ app/cli.py::run()
            ├─ BrainstormAgent.__init__()   ← builds Orchestrator + sub-agents
            ├─ agent.start(requirement)     ← first turn: runs intake → brd_fetch → code_scan → context_graph → analyze → ask/propose
            └─ loop:
                 user_reply = input()
                 agent.turn(user_reply)      ← subsequent turns
                 until phase == done
```

### API flow
```
POST /api/start  {feature, requirement, ...}
  └─ agent.start()  → TurnResponse (awaiting=True, message=first_question)

POST /api/turn   {message: "user reply"}
  └─ agent.turn()   → TurnResponse (awaiting=True|False, ...)

POST /api/upload {files}
  └─ ingest() → UploadResponse {paths, names}
```

### Turn execution (`Orchestrator.run_turn`)
1. Merge `user_message` into state (`user_input`).
2. If `phase == intake`: run `node_intake` → `node_brd_fetch` → `node_code_scan` → `node_context_graph` → `node_analyze`.
3. If `phase == brainstorm`: run `node_incorporate` → `node_analyze`.
4. After `node_analyze`: route to `node_ask` (awaiting) or `node_propose` (awaiting).
5. On confirm: run `node_generate`.
6. After `node_generate`: run `node_present` (awaiting).
7. On approve: run `node_signoff` → `node_finalize` (done).
8. On revise: loop back to `node_generate`.

---

## 7. Testing

### Test files
- `tests/conftest.py`: shared fixtures (mock config, temp BRD store, mock LLM).
- `tests/test_units.py`: deterministic unit tests for `retrieval.py`, `artifacts.py`, `brd/repository.py`.
- `tests/test_flow.py`: end-to-end offline flow test using `MockLLM`.

### Running tests
```bash
pytest tests/ -v
```
All tests run offline with `MockLLM` — no LLM API key required.

---

## 8. BrainstormState Field Types

Full typed definition of `BrainstormState` (TypedDict):

```python
class BrainstormState(TypedDict, total=False):
    # Identity
    feature_key: str                        # stable hyphenated identifier
    feature_title: str                      # human-readable feature name
    phase: str                              # "intake" | "brainstorm" | "awaiting_generate"
                                            # | "signoff" | "done"

    # Conversation
    messages: List[Dict[str, str]]          # [{role, content}] full transcript
    user_input: str                         # latest raw user message
    new_requirement: str                    # original requirement text submitted at start
    round: int                              # clarifying-question round counter

    # Retrieved context
    artifacts: List[Dict[str, Any]]         # ingested upload artifacts
    brd_matches: List[BRDMatch]             # TF-IDF matched BRDs from store
    code_hits: List[Dict[str, Any]]         # raw repo scan hits
    code_findings: str                      # summarized code scan text

    # Structured context
    intake_summary: Dict[str, Any]          # {summary, confidence, greenfield}
    graph_delta: Dict[str, Any]             # nodes/edges added in last ContextGraphAgent run
    understanding: str                      # ConversationAgent's running understanding text

    # Orchestrator reasoning
    existing_impl: str                      # whether similar implementation exists
    impacted_repos: List[str]               # repo names ConversationAgent identified
    impacted_brds: List[str]                # BRD names ConversationAgent identified

    # Transient turn control
    decision: str                           # "ask" | "ready"
    analyst_message: str                    # ConversationAgent response text

    # Turn output
    pending_question: str                   # clarifying question to surface to user
    awaiting: bool                          # True when pipeline is paused for user input
    result_message: str                     # message to return to caller this turn

    # Generation
    draft_brds: List[Dict[str, str]]        # [{name, content}] generated BRD drafts

    # Finalization
    signed: bool                            # True after node_finalize runs
    finalized_paths: List[str]              # file paths of written signed BRDs

    # Accounting
    usage: Dict[str, Any]                   # cumulative session UsageMeter state
    turn_usage: Dict[str, Any]              # per-turn usage snapshot
```

---

## 9. Error Handling

### 9.1 LLM call failures

All LLM calls in sub-agents go through `BaseAgent._llm_text()` / `BaseAgent._llm_json()`:
- Network or provider errors are caught and recorded in the `AgentTrace` with `ok=False` and `error=<message>`.
- The exception is re-raised after trace closure, propagating up to `Orchestrator.run_turn()`.
- `run_turn()` does not catch agent exceptions — they propagate to the API handler or CLI loop.
- The CLI prints the error and exits; the API returns an HTTP 500 with the error message.
- Sessions are saved before each agent runs, so the session state at the last successful turn is preserved and the user can resume.

### 9.2 JSON extraction failures

`BaseAgent._llm_json()` calls `extract_json()` on the raw model output:
- If no valid JSON is found, `extract_json()` raises `ValueError`.
- Individual agents catch `ValueError` and apply agent-specific fallbacks:
  - `IntakeAgent`: falls back to a minimal `{summary: "", confidence: 0.0, greenfield: false}` dict.
  - `ContextGraphAgent`: falls back to `{nodes: [], edges: []}` — no graph update.
  - `ConversationAgent`: falls back to `decision="ask"` with a generic clarifying message.
  - `SignoffAgent`: does not use JSON — keyword match only, no failure mode.

### 9.3 BRD store access failures

If `BRDRepository.find_relevant()` raises (e.g. missing store dir):
- `BRDFetchAgent` catches the error, sets `brd_matches = []`, and logs a warning in the trace.
- Execution continues without grounded BRD context.

### 9.4 Code scan failures

If `scan_repos()` raises (e.g. configured repo path does not exist):
- `CodeScanAgent` catches the error, sets `code_hits = []` and `code_findings = "Repo scan unavailable."`.
- Execution continues without code grounding.

### 9.5 Upload / artifact ingestion failures

`app/artifacts.py::ingest()` handles per-format failures gracefully:
- Missing optional dependencies (e.g. `pytesseract` for OCR) return a human-readable placeholder string instead of raising.
- Unsupported file extensions return a placeholder string.
- These placeholder strings are included as artifacts so the agent is aware something was uploaded but unreadable.
