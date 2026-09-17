# System Specification & Architecture Blueprint

## 1. Project Overview & System Goals

This repository implements Agent 2 of the SDLC Agentic Framework: a local, multi-agent requirement breakdown system that consumes a signed BRD or an existing breakdown document and produces a structured delivery backlog plus Jira-ready records.

Primary goals:
- Load signed BRDs from Agent 1 or ingest uploaded documents in common business formats.
- Extract atomic requirements from BRDs.
- Convert requirements into epics, user stories, and tasks with stable IDs.
- Produce a deterministic delivery plan, dependency graph, and rendered Markdown breakdown.
- Support a sign-off loop so users can request revisions before finalization.
- Generate Jira-ready records for Epics, Stories, and Tasks and optionally push them through a pluggable publisher.
- Persist sessions, traces, context graphs, and artifact outputs for replay and audit.

Target runtime:
- Python 3.10+.
- Local execution on Windows, macOS, or Linux.
- CLI mode via `python main.py ...`.
- API/UI mode via FastAPI + Uvicorn at `http://127.0.0.1:8081`.
- Optional LLM backends: VS Code Copilot gateway, Anthropic, OpenAI-compatible, Gemini, or offline mock.

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
Defined in [requirements.txt](requirements.txt):
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
Defined in [requirements-optional.txt](requirements-optional.txt):
- `anthropic`
- `openai`
- `google-generativeai`
- `pytesseract`
- `Pillow`

### Configuration files
- [pyproject.toml](pyproject.toml): project metadata, Ruff, pytest, setuptools package discovery.
- [config.example.yaml](config.example.yaml): canonical config template.
- [config.yaml](config.yaml): active runtime config.
- [.env](.env): local secrets and environment overrides.
- [.env.example](.env.example): sample environment file.

### Runtime prerequisites and environment variables
- Python 3.10 or newer.
- A BRD store in `data/brd_store` or uploaded documents.
- Optional VS Code Copilot proxy service when using `provider: vscode_copilot`.
- Optional API keys for cloud providers:
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- Jira credentials when using non-dry-run publishing:
  - `JIRA_TOKEN`
  - `JIRA_USER`
- Config overrides supported by code:
  - `RBK_LLM_PROVIDER`
  - `RBK_LLM_MODEL`
  - `RBK_PROXY_URL`
  - `RBK_LLM_TEMPERATURE`
  - `RBK_LLM_TOP_P`
  - `RBK_LLM_MAX_TOKENS`
  - `RBK_LLM_REQUEST_TIMEOUT`
- Shared fallback overrides also accepted via `RBA_*` names.

Implementation note:
- The CLI currently maps the Copilot shortcut to `openai` provider with `gpt-5.4` and `http://127.0.0.1:3030/v1`, while the config default provider is `vscode_copilot` with `http://127.0.0.1:3100`. Recreate both behaviors if you need CLI parity with the current code.

## 3. Project Directory Structure

### Top level
- [main.py](main.py): entrypoint that dispatches to CLI or Uvicorn.
- [README.md](README.md): human-facing overview and usage.
- [GETTING_STARTED.md](GETTING_STARTED.md): setup and workflow guide.
- [pyproject.toml](pyproject.toml): package metadata and tooling.
- [requirements.txt](requirements.txt): mandatory dependencies.
- [requirements-optional.txt](requirements-optional.txt): optional provider/OCR dependencies.
- [config.example.yaml](config.example.yaml): config template.
- [config.yaml](config.yaml): active config.
- [.env](.env): local environment variables.
- [.env.example](.env.example): example environment file.
- [.gitignore](.gitignore): ignores generated outputs and local state.
- [scripts/](scripts/): helper scripts.
- [docs/](docs/): architecture and understanding docs.
- [tests/](tests/): offline test suite.
- [ui/](ui/): static single-page web UI.
- [app/](app/): all application code.
- [data/](data/): generated runtime artifacts and stores.

### Application package: app/

#### [app/__init__.py](app/__init__.py)
- Package export surface: `BreakdownAgent`, `AppConfig`, `load_config`, `__version__`.

#### [app/agent.py](app/agent.py)
- High-level facade over the orchestrator.
- Owns session bootstrap, resume logic, upload ingestion, usage aggregation, and per-turn result shaping.

#### [app/config.py](app/config.py)
- Loads config from defaults, YAML, `.env`, and environment overrides.
- Defines config models and resolved path helpers.

#### [app/cli.py](app/cli.py)
- Interactive terminal workflow and command dispatch.
- Provides `init`, `run`, `list`, `latest`, and `jira-meta` behaviors.

#### [app/artifacts.py](app/artifacts.py)
- Multi-format artifact ingestion into plain text.

#### [app/retrieval.py](app/retrieval.py)
- Lightweight TF-IDF ranking for BRD/document chunk selection.

#### [app/brd/](app/brd/)
- BRD discovery, matching, and versioning.

#### [app/graph/](app/graph/)
- Persisted context graph for feature knowledge.

#### [app/jira/](app/jira/)
- Jira record construction and publishing.

#### [app/llm/](app/llm/)
- Provider abstraction, pricing, usage metering, and vision helpers.

#### [app/memory/](app/memory/)
- Session persistence and feature-key indexing.

#### [app/orchestrator/](app/orchestrator/)
- Shared state definition and LangGraph orchestration logic.

#### [app/prompts/](app/prompts/)
- Per-agent prompt modules and render helper.

#### [app/tools/](app/tools/)
- Deterministic helpers for BRD loading, planning, rendering, and Jira mapping.

#### [app/trace/](app/trace/)
- Execution tracing and replay index.

#### [app/api/](app/api/)
- FastAPI server and request/response schemas.

#### [app/agents/](app/agents/)
- Single-responsibility sub-agents used by the orchestrator.

### Documentation
- [docs/agent-understanding/](docs/agent-understanding/): currently empty placeholder folder.
- [docs/Agent2_Requirement_Breakdown_Agent.md](docs/Agent2_Requirement_Breakdown_Agent.md): agent-facing design doc.

### Scripts
- [scripts/generate_wcf_jira_backlog.py](scripts/generate_wcf_jira_backlog.py): helper script for WCF/Jira backlog generation.

### Tests
- [tests/conftest.py](tests/conftest.py): shared fixtures and mock BRD setup.
- [tests/test_units.py](tests/test_units.py): deterministic tool tests.
- [tests/test_modes.py](tests/test_modes.py): grooming/Jira mode tests.
- [tests/test_jira_and_stages.py](tests/test_jira_and_stages.py): Jira mapping, publishers, stage handling.
- [tests/test_agent_flow.py](tests/test_agent_flow.py): end-to-end offline flow tests.
- [tests/test_agents_trace.py](tests/test_agents_trace.py): prompt, trace, and sign-off trace tests.
- [tests/__init__.py](tests/__init__.py): test package marker.

### UI
- [ui/index.html](ui/index.html): lightweight single-page chat-style interface for session review and trace inspection.

### Generated data tree
The `data/` folder is runtime state, not source code. The code expects these subtrees:
- `data/brd_store/`: BRD source store and uploaded BRDs; signed revisions live in `revisions/`.
- `data/breakdowns/`: versioned grooming outputs and signed markdown breakdowns.
- `data/graph/`: serialized context graph JSON.
- `data/jira/`: Jira-ready records, previews, and run folders.
- `data/sessions/`: persisted sessions and feature index.
- `data/traces/`: per-session agent trace directories.
- `data/workspaces/`: archived per-feature run folders.

### Package-internal file inventory

#### app/agents/
- [app/agents/base.py](app/agents/base.py): base class, agent context, trace wrapper, LLM helpers.
- [app/agents/brd_loader_agent.py](app/agents/brd_loader_agent.py): deterministic BRD loading and graph seeding.
- [app/agents/requirement_extractor_agent.py](app/agents/requirement_extractor_agent.py): requirement extraction.
- [app/agents/story_builder_agent.py](app/agents/story_builder_agent.py): epic/story generation and ID remapping.
- [app/agents/task_planner_agent.py](app/agents/task_planner_agent.py): task decomposition and owner tagging.
- [app/agents/analysis_agent.py](app/agents/analysis_agent.py): decisions/conflicts/gaps analysis.
- [app/agents/plan_composer_agent.py](app/agents/plan_composer_agent.py): dependency graph and iteration planning.
- [app/agents/breakdown_writer_agent.py](app/agents/breakdown_writer_agent.py): rendered Markdown output.
- [app/agents/signoff_agent.py](app/agents/signoff_agent.py): approval vs revise classification.
- [app/agents/breakdown_ingest_agent.py](app/agents/breakdown_ingest_agent.py): ingest existing breakdown docs.
- [app/agents/granularity_assessor_agent.py](app/agents/granularity_assessor_agent.py): split-worthiness assessment.
- [app/agents/jira_mapping_agent.py](app/agents/jira_mapping_agent.py): Jira record creation and artifact writing.
- [app/agents/_format.py](app/agents/_format.py): compact prompt formatting helpers.
- [app/agents/__init__.py](app/agents/__init__.py): public agent exports.

#### app/api/
- [app/api/server.py](app/api/server.py): FastAPI app, endpoints, static UI mount.
- [app/api/schemas.py](app/api/schemas.py): Pydantic request/response models.
- [app/api/__init__.py](app/api/__init__.py): exports `app`.

#### app/brd/
- [app/brd/repository.py](app/brd/repository.py): BRD repository, discovery, relevance matching, versioning.
- [app/brd/__init__.py](app/brd/__init__.py): exports repository types.

#### app/graph/
- [app/graph/context_graph.py](app/graph/context_graph.py): persisted directed graph with Mermaid export.
- [app/graph/__init__.py](app/graph/__init__.py): exports `ContextGraph`.

#### app/jira/
- [app/jira/publisher.py](app/jira/publisher.py): publisher base class and DryRun/REST/MCP implementations.
- [app/jira/__init__.py](app/jira/__init__.py): exports publisher surface.

#### app/llm/
- [app/llm/base.py](app/llm/base.py): LLM interface, token estimation, JSON extraction.
- [app/llm/providers.py](app/llm/providers.py): concrete providers and `build_llm` factory.
- [app/llm/usage.py](app/llm/usage.py): usage metering and formatting.
- [app/llm/pricing.py](app/llm/pricing.py): model price table.
- [app/llm/vision.py](app/llm/vision.py): image transcription / OCR helper.
- [app/llm/__init__.py](app/llm/__init__.py): exports provider and usage surface.

#### app/memory/
- [app/memory/session_store.py](app/memory/session_store.py): session persistence and feature index.
- [app/memory/__init__.py](app/memory/__init__.py): exports session store surface.

#### app/orchestrator/
- [app/orchestrator/state.py](app/orchestrator/state.py): `BreakdownState` typed dict and `new_state` factory.
- [app/orchestrator/graph.py](app/orchestrator/graph.py): orchestration node methods and turn flow.
- [app/orchestrator/__init__.py](app/orchestrator/__init__.py): exports orchestration surface.

#### app/prompts/
- [app/prompts/render.py](app/prompts/render.py): `{{variable}}` renderer.
- [app/prompts/requirement_extractor_agent.py](app/prompts/requirement_extractor_agent.py): extractor prompt.
- [app/prompts/story_builder_agent.py](app/prompts/story_builder_agent.py): story prompt.
- [app/prompts/task_planner_agent.py](app/prompts/task_planner_agent.py): task prompt.
- [app/prompts/analysis_agent.py](app/prompts/analysis_agent.py): analysis prompt.
- [app/prompts/breakdown_ingest_agent.py](app/prompts/breakdown_ingest_agent.py): ingest prompt.
- [app/prompts/granularity_assessor_agent.py](app/prompts/granularity_assessor_agent.py): granularity prompt.
- [app/prompts/__init__.py](app/prompts/__init__.py): prompt registry.

#### app/tools/
- [app/tools/brd_loader.py](app/tools/brd_loader.py): deterministic BRD loading and Markdown section splitting.
- [app/tools/planning.py](app/tools/planning.py): stable ID assignment, owner tag normalization, dependency graph, cycle detection, iteration planning.
- [app/tools/renderer.py](app/tools/renderer.py): Markdown breakdown renderer.
- [app/tools/jira_mapping.py](app/tools/jira_mapping.py): Jira record mapping, validation, preview rendering.
- [app/tools/__init__.py](app/tools/__init__.py): aggregated exports.

#### app/trace/
- [app/trace/tracer.py](app/trace/tracer.py): trace records, session trace files, index management.
- [app/trace/__init__.py](app/trace/__init__.py): exports tracing surface.

#### app/retrieval.py
- `tokenize(text)`
- `chunk_text(text, source, target_chars=1200, overlap=150)`
- `rank_chunks(query, chunks, top_k=5)`
- `top_snippets(query, text, source, top_k=4, max_chars=4000)`

## 4. Data Schemas, Interfaces & State

### Configuration models

#### `LLMConfig`
- `provider: str` default `vscode_copilot`
- `model: str` default `gpt-4o`
- `proxy_url: str` default `http://127.0.0.1:3100`
- `temperature: float`
- `top_p: float`
- `max_tokens: int`
- `request_timeout: int`
- `deterministic_labels: list[str]`
- `phase_temperatures: dict[str, float]`
- `phase_top_p: dict[str, float]`
- `phase_timeouts: dict[str, int]`
- `phase_max_tokens: dict[str, int]`
- `input_price_per_mtok: float | None`
- `output_price_per_mtok: float | None`

#### `BRDConfig`
- `store_dir: str`
- `extra_source_dirs: list[str]`
- `glob_patterns: list[str]`
- `brd_filename_markers: list[str]`

#### `PlanningConfig`
- `velocity_points_per_iteration: int`
- `days_per_iteration: int`
- `default_story_points: int`
- `story_chunk_size: int`
- `task_chunk_size: int`
- `jira_mapping_chunk_size: int`
- `max_consecutive_chunk_errors: int`

#### `StorageConfig`
- `sessions_dir: str`
- `graph_dir: str`
- `traces_dir: str`
- `breakdowns_dir: str`
- `jira_dir: str`

#### `JiraFieldProfile`
- `project_key: str`
- `epic_type_default: str`
- `user_story_type_default: str`
- `work_owner_default: str`
- `default_assignee: str`
- `default_priority: str`
- `product_domain: str`
- `product_group: str`
- `product_area: str`
- `sub_domain_vcg: str`
- `vzagile_program: str`
- `default_component: str`
- `default_labels: list[str]`
- `custom_field_ids: dict[str, str]`

#### `JiraConfig`
- `base_url: str`
- `publisher: str` (`dryrun`, `rest`, `mcp`)
- `push_requires_approval: bool`
- `token_env: str`
- `user_env: str`
- `mcp_server: str`
- `profile: JiraFieldProfile`

#### `AppConfig`
- Aggregates all config models and exposes resolved path helpers:
  - `brd_store_path`
  - `sessions_path`
  - `graph_path`
  - `traces_path`
  - `breakdowns_path`
  - `jira_path`

### Session and orchestrator state

#### `Session`
- `session_id: str`
- `feature_key: str`
- `title: str`
- `created_at: str`
- `updated_at: str`
- `state: dict[str, Any]`

#### `BreakdownState`
Important fields:
- Identity: `feature_key`, `feature_title`, `phase`, `mode`, `start_stage`
- Conversation: `messages`, `user_input`, `reviewer_feedback`
- Inputs: `brd_names`, `brd_paths`, `breakdown_paths`, `artifacts`
- Loaded docs: `brd_docs`
- Structured breakdown: `requirements`, `epics`, `stories`, `tasks`, `bau_reference`, `analysis`, `plan`
- Existing-breakdown stage: `granularity_analysis`, `decompose_approved`
- Rendered artifacts: `breakdown_doc`, `grooming`
- Jira state: `jira`, `jira_preview`, `jira_push`, `jira_push_approved`
- Control: `decision`, `awaiting`, `pending_question`, `result_message`, `signed`, `finalized_paths`
- Accounting: `usage`, `turn_usage`

### BRD / artifact schema

#### `Artifact`
- `name`, `path`, `kind`, `fmt`, `text`, `meta`

#### `BRDDoc`
- `name`, `path`, `text`, `sections`

#### `BRDMatch`
- `name`, `path`, `score`, `snippet`, `text`

#### Section split format
- `sections` is a list of dicts with at least `heading` and `text`.

### Requirements and backlog schemas

#### Requirement extraction output
- `requirements`: list of
  - `ref`
  - `text`
  - `type` (`functional` or `nonfunctional`)
  - `source_section`

#### Epic schema
- `ref`, `key`, `title`, `description`, `classification`, `epic_type`, `source_sections`

#### Story schema
- `ref`, `key`, `epic`, `role`, `want`, `benefit`, `acceptance_criteria`, `classification`, `owner_tag`, `blocked`, `open_decisions`, `source_sections`, `points`, `requirements`, `depends_on`

#### Task schema
- `ref`, `id`, `story`, `title`, `kind`, `owner_tag`, `classification`, `description`, `implementation_notes`, `acceptance_criteria`, `dependencies`, `source_requirements`, `source_sections`, `estimate_hours`

#### Analysis schema
- Keys: `decisions`, `conflicts`, `action_items`, `open_items`, `gaps`, `risks`, `assumptions`, `dependencies`

#### Plan schema
- `dependency_graph: dict[str, list[str]]`
- `cycles: list[list[str]]`
- `order: list[str]`
- `iterations: list[dict]`
- `totals: {epics, stories, points, iterations}`
- `timeline: {iteration_count, days_per_iteration, estimated_days}`

### Jira record schema

#### Jira record object
Each generated record contains:
- `internal_id`
- `entity` (`epic`, `story`, `task`)
- `issue_type`
- `project_key`
- `classification`
- `parent_internal_id`
- `fields`
- `labels`
- `source_requirements`
- `source_sections`
- `dependencies`
- `blocked` on story records

#### Jira `fields` content
- Epic fields: `Epic Name`, `Epic Type`, `Summary`, `Labels`, `Work Owner VCG/VBG`, `Product Domain`, `Product Group`, `Product Area`, `Sub-Domain VCG`, `Parent Link`, `Description`
- Story fields: `User Story Type`, `Epic Link`, `Labels`, `Summary`, `Description`, `Acceptance Criteria`, `Work Owner VCG/VBG`
- Task fields: `Summary`, `Component/s`, `Priority`, `Assignee`, `Work Owner VCG/VBG`, `VzAgile Program`, `Description`, `Labels`

### API schemas

#### `StartRequest`
- `feature`, `feature_key`, `title`, `brd_names`, `uploads`, `resume`, `start_stage`, `mode`, `jira_project_key`

#### `MessageRequest`
- `message`, `uploads`

#### `TurnResponse`
- `session_id`, `feature_key`, `phase`, `awaiting`, `message`, `pending_question`, `feature_title`, `brd_docs`, `epics`, `stories`, `tasks`, `analysis`, `plan`, `breakdown_doc`, `grooming`, `finalized_paths`, `start_stage`, `mode`, `bau_reference`, `granularity_analysis`, `jira`, `jira_preview`, `jira_push`, `turn_usage`, `session_usage`, `context_graph`, `trace`

#### `UploadResponse`
- `paths`, `names`

### LLM schema and usage tracking

#### `Message`
- A dict shaped as `{role: system|user|assistant, content: str}`.

#### `LLMResponse`
- `content`, `input_tokens`, `output_tokens`, `model`, `raw`

#### `UsageRecord`
- `label`, `model`, `input_tokens`, `output_tokens`, `cost_usd`

#### `UsageMeter`
- Accumulates usage records and produces totals, summaries, and serialized state.

### Tracing schema

#### `AgentTrace`
- `seq`, `agent`, `session_id`, `phase`, `started_at`, `ended_at`, `duration_ms`, `used_llm`, `messages`, `raw_output`, `output`, `usage`, `ok`, `error`

#### Trace index entry
- `seq`, `agent`, `phase`, `ok`, `used_llm`, `decision`, `total_tokens`, `cost_usd`, `at`, `file`

## 5. Functional Modules & Implementation Details

### 5.1 Entrypoint and CLI

#### [main.py](main.py)
- Configures warning filters to suppress noisy environment warnings.
- `serve(host="127.0.0.1", port=8081)`: runs `uvicorn.run("app.api.server:app", ...)`.
- `main()`: dispatches `serve` directly or forwards to `app.cli.main(argv)`.

Error handling:
- Invalid port values in `--port=` are converted with `int()` and will raise `ValueError`.

#### [app/cli.py](app/cli.py)
- `run(...)` wires the user flow.
- Prompts for LLM choice unless a provider is supplied.
- Prompts for mode unless passed via `--mode`.
- Supports interactive revisions, sign-off, Jira push, and early exit with `/exit` or `/quit`.
- `list_sessions()`: prints session summaries.
- `show_latest(feature_key=None)`: prints latest artifact paths and quick commands per workspace.
- `init()`: creates the data folders required by the agent.
- `jira_meta()`: prints Jira field mappings and unmapped fields.
- `main(argv=None)`: parses subcommands `init`, `run`, `list`, `jira-meta`, `latest`.

Error handling:
- EOF/KeyboardInterrupt on prompts falls back to defaults or exits cleanly.
- Invalid mode/provider input re-prompts.

### 5.2 Configuration

#### [app/config.py](app/config.py)
- `_load_dotenv(path=DEFAULT_ENV_PATH)`: loads simple `KEY=VALUE` pairs without overriding existing env vars.
- `_env_overrides()`: reads `RBK_*` and `RBA_*` overrides for LLM settings.
- `_deep_merge(base, override)`: recursive merge for nested config.
- `load_config(path=None)`: loads YAML if present, merges env overrides, validates with Pydantic.

Error handling:
- Raises `ValueError` if YAML is not a mapping.
- Ignores malformed numeric environment overrides rather than failing the load.

### 5.3 Orchestrator and shared state

#### [app/orchestrator/state.py](app/orchestrator/state.py)
- Defines the mutable workflow state used across all nodes.
- `new_state(...)` seeds all expected fields and defaults.

#### [app/orchestrator/graph.py](app/orchestrator/graph.py)
- `Orchestrator.__init__(...)` creates the shared `AgentContext` and all sub-agent instances.
- Node methods delegate to sub-agents:
  - `node_load`
  - `node_extract`
  - `node_stories`
  - `node_tasks`
  - `node_analyze`
  - `node_plan`
  - `node_compose`
  - `node_signoff`
  - `node_ingest`
  - `node_assess`
  - `node_jira_map`
- Control methods:
  - `node_groom_save()`: writes `grooming_vN.json`, `grooming_vN.md`, and latest copies.
  - `_archive_workspace_run(...)`: copies source BRDs and outputs into `data/workspaces/<feature>/run_vN/`.
  - `node_post_groom_prompt()`: asks whether to continue to Jira in `both` mode.
  - `node_load_grooming()`: loads saved grooming JSON for Jira-only mode.
  - `node_incorporate()`: appends user feedback into transcript and reviewer feedback.
  - `node_present()`: presents sign-off preview for grooming flow.
  - `node_decompose_present()`: presents permission gate for existing-breakdown mode.
  - `node_jira_present()`: presents Jira-ready records and validation warnings.
  - `node_jira_push()`: pushes through the configured publisher.
  - `node_finalize()`: writes the signed breakdown and workspace archive.

Behavioral flow:
- `start_stage="brd"` runs BRD loading -> extraction -> story build -> task planning -> analysis -> planning -> rendering -> sign-off.
- `start_stage="breakdown"` loads an existing breakdown doc, assesses granularity, waits for permission, optionally decomposes further, then proceeds to Jira review.
- `mode="groom"` stops after grooming sign-off.
- `mode="jira"` consumes a saved grooming JSON and skips grooming generation.
- `mode="both"` runs grooming and then Jira review after sign-off.

Error handling and guards:
- Existing breakdown mode never decomposes automatically; user permission is required.
- Jira push is gated behind explicit approval and may be skipped.
- Finalization writes a signed markdown file even when Jira push is skipped.

### 5.4 Sub-agents

#### [app/agents/base.py](app/agents/base.py)
- `AgentContext`: shared dependencies for all agents.
- `BaseAgent.run(state)`: wraps `_run` in trace creation, closure, and error capture.
- `_llm_text(...)` and `_llm_json(...)`: execute prompt/response calls with phase-specific temperature, top-p, timeout, and max-token overrides.
- Deterministic label matching uses prefix matching; the longest matching deterministic prefix wins.

Error handling:
- Exceptions are recorded in the trace and re-raised.
- JSON extraction failures surface as `ValueError` from `extract_json()`.

#### [app/agents/brd_loader_agent.py](app/agents/brd_loader_agent.py)
- Calls `load_brds(...)`.
- Sets `feature_title` from the first BRD filename when missing.
- Adds `feature:` and `BRD` nodes to the context graph.

#### [app/agents/requirement_extractor_agent.py](app/agents/requirement_extractor_agent.py)
- Renders BRD sections with `brd_sections_text`.
- Calls the LLM with `label="extract"`.
- Retries once with `label="extract_retry"` if the extracted requirement count is too low relative to BRD section count.
- Canonicalizes requirement IDs as `R1`, `R2`, ...

Error handling:
- On invalid JSON, falls back to an empty requirement list.

#### [app/agents/story_builder_agent.py](app/agents/story_builder_agent.py)
- Chunks requirements according to `planning.story_chunk_size`.
- Calls the LLM with `label="stories"` or chunk-specific labels.
- Retries under-produced chunks with `stories_retry`.
- Prefixes temporary refs so chunk output can be remapped safely.
- Calls `assign_epic_story_ids(...)` for canonical IDs.
- Normalizes `owner_tag` and classification defaults.
- Adds epic/story nodes and `CONTAINS` / `DEPENDS_ON` edges.

Error handling:
- Empty or failing chunk responses increment a consecutive error counter and may stop generation after `max_consecutive_chunk_errors`.

#### [app/agents/task_planner_agent.py](app/agents/task_planner_agent.py)
- Chunks stories using `planning.task_chunk_size`.
- Calls the LLM with `label="tasks"` or chunk-specific task labels.
- Retries under-covered chunks with `tasks_retry` labels.
- Assigns canonical `TASK-n` IDs.
- Normalizes owner tags and fills missing task classification from the parent story.
- Adds `HAS_TASK` edges and task nodes.

Error handling:
- Stops after too many consecutive empty chunks.

#### [app/agents/analysis_agent.py](app/agents/analysis_agent.py)
- Renders requirements, story summaries, and BRD context into a prompt.
- Returns normalized lists for the analysis keys.
- Adds an analysis summary node with counts.

#### [app/agents/plan_composer_agent.py](app/agents/plan_composer_agent.py)
- Builds the story dependency graph.
- Detects cycles.
- Produces topological order.
- Buckets stories into iterations and computes totals/timeline.

#### [app/agents/breakdown_writer_agent.py](app/agents/breakdown_writer_agent.py)
- Renders the entire breakdown document via `render_breakdown`.
- Stores only a preview in trace output to avoid bloating trace files.

#### [app/agents/signoff_agent.py](app/agents/signoff_agent.py)
- Classifies user feedback as `approve` vs `revise` by keyword matching.

#### [app/agents/breakdown_ingest_agent.py](app/agents/breakdown_ingest_agent.py)
- Parses an existing breakdown document into structured epics/stories/tasks.
- Canonicalizes IDs using the same deterministic assignment helpers.
- Remaps task story refs to canonical US keys.

#### [app/agents/granularity_assessor_agent.py](app/agents/granularity_assessor_agent.py)
- Evaluates whether the existing breakdown can be decomposed further.
- Returns `can_decompose`, `rationale`, and `suggestions`.

#### [app/agents/jira_mapping_agent.py](app/agents/jira_mapping_agent.py)
- Builds Jira records using `build_jira_records(...)`.
- Validates records with `validate_jira_records(...)`.
- Renders preview with `render_jira_preview(...)`.
- Writes per-item JSON files, `combined.json`, and `jira_preview.md` into `data/jira/<feature>/run_vN/`.
- Copies latest outputs to `combined_latest.json` and `jira_preview_latest.md`.
- Supports chunking for very large outputs.

### 5.5 Deterministic tools

#### [app/tools/brd_loader.py](app/tools/brd_loader.py)
- `split_sections(text)`: splits Markdown into heading-based sections, skipping HTML comment metadata.
- `load_brds(cfg, names=None, paths=None)`: source precedence is explicit paths, then names, then signed revisions, then BRD-looking files.
- Supports `.md`, `.txt`, `.docx`, `.pdf`, `.xlsx`, `.xls`, `.csv` via `ingest_file(...)`.

Error handling:
- Non-text formats fall back to optional artifact parsers.
- Missing optional parser dependencies produce placeholder text instead of exceptions.

#### [app/tools/planning.py](app/tools/planning.py)
- `assign_epic_story_ids(epics, stories)`: assigns canonical `EPIC-n` and `US-n` keys and remaps references.
- `assign_task_ids(tasks)`: assigns canonical `TASK-n` IDs and remaps task dependencies.
- `normalize_owner_tags(stories, tasks)`: ensures valid owner tags and defaults classification to `NEW`.
- `build_dependency_graph(stories)`: produces prerequisite adjacency.
- `detect_cycles(graph)`: DFS cycle detection.
- `topological_order(graph)`: Kahn-style ordering with cycle fallback.
- `plan_iterations(...)`: computes iterations, totals, and timeline.

#### [app/tools/renderer.py](app/tools/renderer.py)
- `render_breakdown(state)`: deterministic Markdown rendering of the backlog.
- Includes delivery plan, epics, stories, tasks, BAU reference, requirements traceability, and analysis sections.

#### [app/tools/jira_mapping.py](app/tools/jira_mapping.py)
- `build_jira_records(state, profile)`: creates normalized per-item Jira records for epics, stories, and tasks.
- `validate_jira_records(records)`: checks required fields and parent/link consistency.
- `render_jira_preview(records)`: human-readable Markdown preview.

Important mapping rules:
- Stories receive `Epic Link` as the internal epic key; publishers resolve it to real Jira keys at push time.
- Tasks are linked through `parent_internal_id` and the publisher resolves the parent key.
- Labels include base labels, classification, and `layer-<owner_tag>`.

#### [app/retrieval.py](app/retrieval.py)
- Dependency-free keyword/TF-IDF ranking for document slices.
- Used by the BRD repository to return relevant snippets.

#### [app/artifacts.py](app/artifacts.py)
- `ingest_file(path, llm=None, kind=None)`: converts known file types to text.
- File type handlers:
  - Markdown/text/JSON/YAML: read directly.
  - DOCX: `python-docx`.
  - XLS/XLSX: `openpyxl`.
  - CSV/TSV: Python `csv`.
  - PDF: `pypdf`.
  - Images: vision-capable LLM or OCR fallback.
- `guess_kind(...)` infers `brd`, `requirement`, `scope`, `test_suite`, `diagram`, or `other`.

Error handling:
- Missing optional dependencies return placeholder strings.
- Unsupported formats fall back to plain text read or an unsupported-format placeholder.

### 5.6 BRD repository

#### [app/brd/repository.py](app/brd/repository.py)
- Manages BRD discovery and matching from the configured store and extra source directories.
- `list_brd_files()`: collects candidate BRD files.
- `load_all()`: ingests all discovered BRDs as artifacts.
- `find_relevant(query, top_k=3)`: ranks BRDs by TF-IDF and returns snippets.
- `get(name)`: loads a named BRD artifact.
- `add_upload(src_path, kind="brd")`: copies an upload into the BRD store and ingests it.
- `next_version(base_name)`: computes the next revision number.
- `save_revision(base_name, content, feature, signed=False)`: writes a versioned revision file to `revisions/`.

### 5.7 Context graph

#### [app/graph/context_graph.py](app/graph/context_graph.py)
- JSON-persisted feature graph with nodes and edges.
- `add_node(...)` upserts metadata.
- `add_edge(...)` deduplicates identical edges.
- `neighbors(node_id)` returns undirected adjacent nodes.
- `summary()` returns counts by node type.
- `save(directory)` writes `context_graph_<feature>.json`.
- `load(directory, feature_key)` restores or creates an empty graph.
- `to_mermaid()` emits Mermaid syntax for visualization.

### 5.8 Session persistence

#### [app/memory/session_store.py](app/memory/session_store.py)
- `feature_key_from_text(text)`: derives a stable hyphenated key from the feature text.
- `SessionStore.create(feature_key, title="")`: creates a new session file.
- `SessionStore.save(session)`: updates the session file and feature index.
- `SessionStore.load(session_id)`: loads a session by ID.
- `SessionStore.list_sessions()`: lists sessions newest-first.
- `SessionStore.latest_for_feature(feature_key)`: returns the most recently updated session for a feature.

Error handling:
- Missing session files return `None` rather than raising.

### 5.9 LLM providers and usage

#### [app/llm/base.py](app/llm/base.py)
- `estimate_tokens(text)` tries `tiktoken` and falls back to a character heuristic.
- `extract_json(text)` extracts JSON from raw model output, including fenced code blocks and balanced braces.
- `BaseLLM.complete(...)` records usage for every call.
- `BaseLLM.complete_json(...)` is a convenience wrapper for JSON responses.

#### [app/llm/providers.py](app/llm/providers.py)
- `VSCodeCopilotLLM`: calls a local `vscode-lm-proxy` endpoint.
- `AnthropicLLM`: uses Anthropic SDK.
- `OpenAILLM`: uses OpenAI-compatible chat completions.
- `GeminiLLM`: uses `google-generativeai`.
- `MockLLM`: deterministic offline test provider.
- `build_llm(cfg, meter)`: provider factory.

Error handling:
- Network failures raise runtime errors with actionable messages.
- Missing optional SDKs raise runtime errors that tell the user what to install.
- Non-200 HTTP responses raise runtime errors with truncated response text.

#### [app/llm/usage.py](app/llm/usage.py)
- `UsageMeter.record(...)` captures per-call usage and cost.
- `totals(...)` aggregates calls.
- `summary()` returns totals plus per-call breakdown.
- `to_state()` / `from_state()` serialize session state.
- `format_usage(totals)` formats a single-line summary.

#### [app/llm/pricing.py](app/llm/pricing.py)
- Price table for approximate token-cost reporting.
- `price_for(model)` returns `(input_per_mtok, output_per_mtok)`.

#### [app/llm/vision.py](app/llm/vision.py)
- `describe_image(llm, path)` attempts provider vision, then OCR, then a readable fallback message.

### 5.10 Jira publishing

#### [app/jira/publisher.py](app/jira/publisher.py)
- `PushResult`: publishing result with `mode`, `status`, `created`, `mapping`, and `errors`.
- `JiraPublisher.push(records, mapping=None)`: orders epics -> stories -> tasks, resolves parent links, and preserves idempotency.
- `DryRunPublisher`: simulates creation with synthetic keys.
- `RestPublisher`: posts to Jira REST API and maps configured custom fields.
- `McpPublisher`: delegates issue creation to an injected MCP client callable.
- `build_publisher(cfg, mcp_call=None)`: publisher factory.

Error handling:
- REST publisher raises if Jira token is missing or Jira returns a non-2xx response.
- MCP publisher raises if no MCP callable is wired.
- Failed creation marks the result as `partial` or `error` depending on whether earlier issues were created.

### 5.11 API and UI

#### [app/api/server.py](app/api/server.py)
Endpoints:
- `GET /health`: returns status and active LLM settings.
- `POST /api/uploads`: accepts multipart uploads and returns stored server paths.
- `POST /api/sessions/start`: starts or resumes a session.
- `POST /api/sessions/{session_id}/message`: sends a follow-up message or approval.
- `GET /api/sessions`: lists sessions.
- `GET /api/sessions/{session_id}/transcript`: returns the transcript.
- `GET /api/sessions/{session_id}/usage`: returns usage totals and calls.
- `GET /api/sessions/{session_id}/trace`: returns trace index.
- `GET /api/sessions/{session_id}/trace/{seq}`: returns full trace detail.
- `GET /api/sessions/{session_id}/jira`: returns Jira records, preview, and push state.
- `GET /api/sessions/{session_id}/graph`: returns graph summary, Mermaid, and JSON.
- `GET /`: serves the static UI if present.

Static assets:
- Mounts `/ui` on the `ui/` directory.

Error handling:
- Missing sessions return HTTP 404.
- Missing UI returns a JSON 404 response.

#### [app/api/schemas.py](app/api/schemas.py)
- Pydantic models define request and response payloads for the API.

#### [ui/index.html](ui/index.html)
- Single-file interface with:
  - message composer
  - file attachment picker
  - session list
  - trace browser modal
  - usage summary
  - Jira preview display
- Uses fetch calls to the API endpoints above.

### 5.12 Prompt modules

All prompt modules share the same pattern:
- module-level `SYSTEM` string
- module-level `USER_TEMPLATE` string
- `render_user(**variables)` wrapper using `app.prompts.render.render`

Files:
- [app/prompts/requirement_extractor_agent.py](app/prompts/requirement_extractor_agent.py)
- [app/prompts/story_builder_agent.py](app/prompts/story_builder_agent.py)
- [app/prompts/task_planner_agent.py](app/prompts/task_planner_agent.py)
- [app/prompts/analysis_agent.py](app/prompts/analysis_agent.py)
- [app/prompts/breakdown_ingest_agent.py](app/prompts/breakdown_ingest_agent.py)
- [app/prompts/granularity_assessor_agent.py](app/prompts/granularity_assessor_agent.py)

### 5.13 Tests

#### [tests/conftest.py](tests/conftest.py)
- Creates a temporary BRD store and config fixture with `provider: mock`.

#### [tests/test_units.py](tests/test_units.py)
- Validates section splitting, BRD loading, ID assignment, cycle detection, iteration planning, and markdown rendering.

#### [tests/test_modes.py](tests/test_modes.py)
- Verifies grooming-only, Jira-only, and combined mode behavior.
- Checks saved grooming artifacts and Jira review/push gating.

#### [tests/test_jira_and_stages.py](tests/test_jira_and_stages.py)
- Verifies owner/classification tagging, BAU reference handling, Jira record mapping, validation, publishers, and existing-breakdown stage behavior.

#### [tests/test_agent_flow.py](tests/test_agent_flow.py)
- End-to-end offline flow coverage from BRD to sign-off to Jira review to finalize.

#### [tests/test_agents_trace.py](tests/test_agents_trace.py)
- Verifies prompt rendering, trace creation, trace detail content, and signoff trace inclusion.

## 6. Delivery Sequence

Build the repository in this order:

1. Create the project root and metadata files.
2. Add [pyproject.toml](pyproject.toml), [requirements.txt](requirements.txt), [requirements-optional.txt](requirements-optional.txt), [config.example.yaml](config.example.yaml), [README.md](README.md), [GETTING_STARTED.md](GETTING_STARTED.md), [main.py](main.py), [ui/index.html](ui/index.html), and the `.env` templates.
3. Create the package layout under [app/](app/): `agents`, `api`, `brd`, `graph`, `jira`, `llm`, `memory`, `orchestrator`, `prompts`, `tools`, `trace`.
4. Implement configuration loading in [app/config.py](app/config.py) before any runtime code so all modules can resolve paths consistently.
5. Implement artifact ingestion and retrieval helpers in [app/artifacts.py](app/artifacts.py) and [app/retrieval.py](app/retrieval.py).
6. Implement persistence primitives in [app/memory/session_store.py](app/memory/session_store.py) and [app/graph/context_graph.py](app/graph/context_graph.py).
7. Implement LLM abstractions in [app/llm/base.py](app/llm/base.py), [app/llm/usage.py](app/llm/usage.py), [app/llm/pricing.py](app/llm/pricing.py), [app/llm/vision.py](app/llm/vision.py), and [app/llm/providers.py](app/llm/providers.py).
8. Implement deterministic tools in [app/tools/brd_loader.py](app/tools/brd_loader.py), [app/tools/planning.py](app/tools/planning.py), [app/tools/renderer.py](app/tools/renderer.py), and [app/tools/jira_mapping.py](app/tools/jira_mapping.py).
9. Implement the prompt registry in [app/prompts/](app/prompts/) and the small renderer in [app/prompts/render.py](app/prompts/render.py).
10. Implement the shared agent base in [app/agents/base.py](app/agents/base.py).
11. Implement the sub-agents in this order:
    - BRD loader
    - requirement extractor
    - story builder
    - task planner
    - analysis
    - plan composer
    - breakdown writer
    - signoff
    - breakdown ingest
    - granularity assessor
    - Jira mapping
12. Implement the orchestrator state and routing in [app/orchestrator/state.py](app/orchestrator/state.py) and [app/orchestrator/graph.py](app/orchestrator/graph.py).
13. Implement Jira publishing in [app/jira/publisher.py](app/jira/publisher.py).
14. Implement the high-level facade in [app/agent.py](app/agent.py) to connect sessions, traces, uploads, usage, and orchestration.
15. Implement the CLI in [app/cli.py](app/cli.py) and wire [main.py](main.py) to it.
16. Implement the API models and server in [app/api/schemas.py](app/api/schemas.py) and [app/api/server.py](app/api/server.py).
17. Implement the static UI in [ui/index.html](ui/index.html).
18. Add tests in [tests/](tests/) for deterministic tools first, then modes, then Jira/stage behavior, then end-to-end flow, then tracing.
19. Create the runtime folders with `python main.py init` or an equivalent bootstrap script:
    - `data/brd_store/revisions`
    - `data/sessions`
    - `data/graph`
    - `data/traces`
    - `data/breakdowns`
    - `data/jira`
    - `data/workspaces`
20. Verify the build and runtime with these commands:

```bash
pip install -r requirements.txt
pytest
ruff check .
python main.py init
RBK_LLM_PROVIDER=mock python main.py run "Checkout" --mode groom
python main.py serve
```

### Plan Dependencies
- Deterministic helpers must exist before sub-agents use them.
- The orchestrator must exist before the facade and API can call it.
- The CLI and API depend on the facade.
- The UI depends on the API contract.
- The tests should be written last so they can validate the assembled system.

### Verification criteria
- A mock-provider run should complete offline.
- Grooming mode should persist versioned JSON and Markdown outputs.
- Combined mode should reach Jira review after sign-off.
- Jira-only mode should accept a saved grooming JSON and skip re-grooming.
- Existing-breakdown mode should pause for decomposition permission.
- Trace files should be written for every agent invocation.
- The context graph and session store should persist across runs.

---

## 7. BreakdownState Field Types

Full typed definition of `BreakdownState` (TypedDict):

```python
class BreakdownState(TypedDict, total=False):
    # Identity
    feature_key: str                        # stable hyphenated identifier
    feature_title: str                      # human-readable feature name
    phase: str                              # "load" | "extract" | "stories" | "tasks"
                                            # | "analyze" | "plan" | "compose"
                                            # | "signoff" | "ingest" | "assess"
                                            # | "jira_map" | "done"
    mode: str                               # "groom" | "jira" | "both"
    start_stage: str                        # "brd" | "breakdown"

    # Conversation
    messages: List[Dict[str, str]]          # [{role, content}] full transcript
    user_input: str                         # latest raw user message
    reviewer_feedback: str                  # accumulated revision notes

    # Inputs
    brd_names: List[str]                    # named BRD files to load
    brd_paths: List[str]                    # explicit BRD file paths
    breakdown_paths: List[str]              # existing breakdown doc paths
    artifacts: List[Dict[str, Any]]         # ingested upload artifacts

    # Loaded docs
    brd_docs: List[BRDDoc]                  # parsed BRD content with sections

    # Structured breakdown
    requirements: List[Dict[str, Any]]      # extracted requirement objects
    epics: List[Dict[str, Any]]             # generated epic objects
    stories: List[Dict[str, Any]]           # generated story objects
    tasks: List[Dict[str, Any]]             # generated task objects
    bau_reference: str                      # BAU/existing-work reference text
    analysis: Dict[str, List[Any]]          # decisions/conflicts/risks/gaps etc.
    plan: Dict[str, Any]                    # dependency graph + iterations + timeline

    # Existing-breakdown stage
    granularity_analysis: Dict[str, Any]    # {can_decompose, rationale, suggestions}
    decompose_approved: bool                # user approval to decompose further

    # Rendered artifacts
    breakdown_doc: str                      # full Markdown breakdown
    grooming: Dict[str, Any]                # grooming JSON artifact

    # Jira state
    jira: List[Dict[str, Any]]              # Jira record objects
    jira_preview: str                       # rendered Markdown Jira preview
    jira_push: PushResult                   # publisher result after push
    jira_push_approved: bool                # user approval to push

    # Control
    decision: str                           # "approve" | "revise"
    awaiting: bool                          # True when paused for user input
    pending_question: str                   # prompt to surface to user
    result_message: str                     # message to return this turn
    signed: bool                            # True after finalization
    finalized_paths: List[str]              # paths of written signed artifacts

    # Accounting
    usage: Dict[str, Any]                   # cumulative session UsageMeter state
    turn_usage: Dict[str, Any]              # per-turn usage snapshot
```

---

## 8. Error Handling

### 8.1 LLM call failures

All LLM calls go through `BaseAgent._llm_text()` / `BaseAgent._llm_json()`:
- Exceptions are recorded in the `AgentTrace` with `ok=False` and `error=<message>`, then re-raised.
- The API handler returns HTTP 500; the CLI prints the error.
- Session state is saved after every successful turn, so the user can resume from the last good point.

### 8.2 Per-agent JSON failure fallbacks

| Agent | JSON failure fallback |
|---|---|
| `RequirementExtractorAgent` | Falls back to empty requirements list; logs warning in trace. |
| `StoryBuilderAgent` | Increments consecutive error counter; stops generation after `max_consecutive_chunk_errors` (default from `PlanningConfig`). |
| `TaskPlannerAgent` | Same consecutive-error guard as story builder. |
| `AnalysisAgent` | Falls back to empty analysis dict (all keys → empty lists). |
| `GranularityAssessorAgent` | Falls back to `{can_decompose: false, rationale: "parse error", suggestions: []}`. |
| `JiraMappingAgent` | Raises `ValueError` — Jira mapping failure is surfaced to the user. |

### 8.3 Jira publisher error handling

`JiraPublisher.push()` processes records in order (epics → stories → tasks). On failure:
- If an epic creation fails, child stories/tasks for that epic are skipped.
- If a story creation fails, child tasks for that story are skipped.
- All successfully created issues are included in `PushResult.created`.
- `PushResult.status` is set to `"partial"` when some issues were created and `"error"` when none were.
- Errors are accumulated in `PushResult.errors` and reported to the user after the push attempt completes.

### 8.4 BRD loading failures

`BRDLoaderAgent` uses `load_brds()` which:
- Tries explicit paths, then named lookups, then signed revisions, then BRD-pattern files.
- Unsupported file formats return placeholder text instead of raising.
- If no BRDs are found, `brd_docs` is an empty list and subsequent agents produce empty output. The user is notified via the orchestrator result message.

### 8.5 CLI and EOF handling

`app/cli.py` wraps all `input()` prompts in `try/except (EOFError, KeyboardInterrupt)`:
- EOF (e.g. piped input ending) falls back to a default value or exits cleanly.
- Keyboard interrupt exits with a goodbye message, no stack trace.
- Invalid mode or provider input re-prompts rather than raising.
