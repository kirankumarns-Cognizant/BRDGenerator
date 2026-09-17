# System Specification & Architecture Blueprint

## 1. Project Overview & System Goals

This module implements the Forward Engineering Defect Resolution Pipeline within the KnowledgebaseVegas platform. It is a 5-stage sequential agent pipeline that takes a defect (from Jira or a requirements file) and autonomously produces: a structured brief, a repository analysis, a human-reviewed fix plan, patched source files, and a committed Git branch.

Primary goals:
- Accept a Jira defect ID or a local requirements file as the defect source.
- Normalize the defect into a structured `defect_brief.json` including functional requirements, acceptance criteria, affected repos, and defect classification.
- Scan actual source code repositories to identify which specific files and methods need to change, and detect the codebase's coding patterns.
- Produce a human-readable and machine-readable fix plan (HLD, LLD, `defect_fix_plan.json`) with method-level granularity, traceable to FRs and ACs.
- Generate complete patched source files (not diffs) with AC self-check validation.
- Create a Git branch, commit the patches, and optionally push for review.
- Support resumable execution: each stage is checkpointed so the pipeline can be restarted from any failed step.
- Enforce HITL gates at plan approval, commit approval, and push approval.
- Enforce NSA/VXP architecture constraints (reactive code, service-type call restrictions, feature-flag patterns) at both the planning and code-generation stages.

Target runtime:
- Python 3.10+.
- Local execution on Windows, macOS, or Linux.
- CLI mode via `python defect_agent.py run --jira-id <ID>`.
- LLM backends: VS Code Copilot proxy, Anthropic SDK, GitHub Copilot REST.

---

## 2. Tech Stack & Dependencies

### Core stack
- Language: Python.
- CLI framework: Click.
- Terminal UI: Rich (console, panels, tables, prompts, syntax highlighting).
- LLM providers: VS Code Copilot proxy (port 3100), Anthropic SDK, GitHub Copilot REST.
- Jira integration: MCP service bridge (via `MCPServiceBridge`) or direct REST.
- Git operations: subprocess (`git` CLI).
- Configuration: YAML plus `.env`.

### Required Python packages (`requirements.txt`)
- `anthropic>=0.28.0`
- `openai>=1.30.0`
- `python-dotenv>=1.0.0`
- `pyyaml>=6.0.1`
- `requests>=2.32.0`
- `click>=8.1.7`
- `rich>=13.7.0`
- `jsonschema>=4.22.0`
- `pytest>=8.2.0`
- `pytest-cov>=5.0.0`

### Configuration (`config.template.yaml`)
Key fields:
- `llm_provider`: `vscode_copilot` | `anthropic` | `copilot`
- `llm_model`: model name string
- `kb_root_path`: path to KB store root
- `jira_url`, `jira_project_key`, `jira_auth_type`: Jira connection
- `gitlab_url`, `gitlab_namespace`, `auto_clone`, `clone_base_path`: repo auto-clone
- `repo_path`, `repo_folder_path`: local repo paths
- `git_enabled`, `git_default_branch`, `git_branch_prefix`
- `hitl_mode`: `wait_for_input` | `skip`
- `code_gen_mode`: `full` | `md_only`
- `enable_brd_context`, `manual_brd_path`, `brd_chunk_size`
- `timeout_llm_sec`, `timeout_mcp_sec`, `max_llm_retries`
- `log_level`: `debug` | `info` | `warn` | `error`

### Runtime prerequisites
- Python 3.10+.
- `git` CLI available on PATH.
- VS Code LM Proxy service running at port 3100 when using `vscode_copilot`.
- `ANTHROPIC_API_KEY` in `.env` when using `anthropic` provider.
- `GITHUB_TOKEN` in `.env` when using `copilot` provider.
- Jira credentials in `.env` (bearer token or basic auth) when using Jira intake.

---

## 3. Project Directory Structure

### Top level (`forward_engineering/`)
- `defect_agent.py`: CLI entrypoint (Click commands `run`, `run-step`, `resume`, `status`).
- `README.md`: usage documentation.
- `requirements.txt`: Python dependencies.
- `config.template.yaml`: config template.
- `__init__.py`: package marker.

### `agents/`
- `defect_intake_agent.py`: Stage 1 — normalize defect into `defect_brief.json`.
- `defect_repo_scan_agent.py`: Stage 2 — scan repos, produce `repo_analysis.json`.
- `defect_plan_agent.py`: Stage 3 — generate fix plan (`defect_fix_plan.md`, `defect_fix_plan.json`, HLD, LLD).
- `defect_code_agent.py`: Stage 4 — generate patched files with AC self-check.
- `defect_git_agent.py`: Stage 5 — create branch, commit, optionally push.
- `defect_orchestrator.py`: `DefectOrchestrator` — controls pipeline execution, HITL gates, resume logic, control-plane stop checks.
- `__init__.py`: agent package marker.

### `utils/`
- `config_loader.py`: `DefectConfig` dataclass and `load_config()` factory; validates required fields and known values.
- `state_manager.py`: `StateManager` — JSON-persisted run state; tracks step completion, HITL decisions, per-stage outputs.
- `kb_store.py`: `KBStore` — defect folder initialization and artifact file management under the KB root.
- `llm_client.py`: `LLMClient` — multi-provider LLM call with retry, token tracking, and cost calculation.
- `logger.py`: `DefectLogger` — structured per-agent logging to files.
- `mcp_services.py`: `MCPServiceBridge` — Jira ticket fetch via MCP or direct REST.
- `memory_loader.py`: `load_workspace_memories()` — loads workspace-level memory files for LLM context injection.
- `requirements_parser.py`: `RequirementsParser` — parses local requirements YAML/Markdown files.
- `git_cloner.py`: GitLab auto-clone helper.
- `__init__.py`: utils package marker.

### KB output structure (under `kb_root_path/<project_key>/<defect_id>/`)
```
<defect_id>/
  defect_brief.json           ← Stage 1 output
  repo_analysis.json          ← Stage 2 output
  defect_fix_plan.md          ← Stage 3 human-readable plan
  defect_fix_plan.json        ← Stage 3 machine-readable plan
  defect_hld_<id>.md          ← Stage 3 HLD
  defect_lld_<id>.md          ← Stage 3 LLD
  defect_code_plan.md         ← Stage 4 plan (md_only mode)
  run_state.json              ← StateManager checkpoint file
  logs/                       ← per-agent log files
```

---

## 4. Data Schemas, Interfaces & State

### Configuration model: `DefectConfig`
Dynamic attributes from YAML/env, validated against `DEFAULTS` and `VALID_VALUES` maps. Key attributes:
- `llm_provider`, `llm_model`, `max_llm_retries`, `timeout_llm_sec`, `timeout_mcp_sec`
- `kb_root_path`, `jira_url`, `jira_project_key`, `jira_auth_type`
- `repo_path`, `clone_base_path`, `auto_clone`, `gitlab_url`, `gitlab_namespace`
- `git_enabled`, `git_default_branch`, `git_branch_prefix`
- `hitl_mode`, `code_gen_mode`, `log_level`
- `enable_brd_context`, `manual_brd_path`, `brd_chunk_size`
- `sdlc_kb_path`, `mcp_config_path`

### Run state: `StateManager`

Persisted to `run_state.json`. Tracks:

**Pipeline control:**
- `run_id`, `created_at`, `updated_at`, `status`, `current_step`
- `completed_steps: list[str]`, `failed_steps: list[str]`, `hitl_decisions: list`

**Stage 1 (intake) outputs:**
- `defect_id`, `intake_source` (`jira | requirements_file | both`)
- `requirements_file_path`, `defect_brief_path`
- `jira_summary`, `jira_status`, `jira_priority`, `jira_components`
- `defect_type`, `defect_severity`
- `functional_requirements: list[{id, title, repository, requirements}]`
- `acceptance_criteria: list[{id, title, given, when, then}]`
- `affected_repos: list[{repo, priority}]`

**Stage 2 (repo scan) outputs:**
- `repo_analysis_path`, `affected_files: list`, `code_patterns: dict`

**Stage 3 (plan) outputs:**
- `defect_fix_plan_path`, `defect_fix_plan_json_path`, `fix_plan_approved: bool`

**Stage 4 (code) outputs:**
- `defect_code_plan_path`, `files_patched: list`
- `ac_check_results: dict[ac_id, {result, reasoning}]`

**Stage 5 (git) outputs:**
- `defect_branch_name`, `defect_committed: bool`

### `defect_brief.json` schema
```json
{
  "defect_id": "PROJ-1234",
  "summary": "...",
  "description": "...",
  "status": "...", "priority": "...",
  "components": [], "labels": [],
  "defect_type": "bug|regression|performance|security|data",
  "defect_severity": "critical|high|medium|low",
  "intake_source": "jira|requirements_file|both",
  "functional_requirements": [{"id", "title", "repository", "requirements"}],
  "acceptance_criteria": [{"id", "title", "given", "when", "then"}],
  "affected_repos": [{"repo", "priority"}],
  "test_requirements": {"unit": bool, "integration": bool, "regression": bool},
  "recent_comments": [],
  "raw_requirements_text": "..."
}
```

### `repo_analysis.json` schema
```json
{
  "affected_files": [{
    "file_path": "src/.../Controller.java",
    "language": "java",
    "relevant_classes": [],
    "relevant_methods": [],
    "current_snippet": "...",
    "change_needed": "...",
    "change_type": "modify|create",
    "fr_references": [],
    "confidence": 0.9
  }],
  "new_files_needed": [{
    "suggested_path": "...",
    "purpose": "...",
    "fr_references": []
  }],
  "code_patterns": {
    "error_handling_style": "...",
    "logging_framework": "...",
    "test_framework": "...",
    "validation_library": "...",
    "http_response_format": "..."
  }
}
```

### `defect_fix_plan.json` schema
```json
{
  "defect_id": "...",
  "changes": [{
    "file_path": "...",
    "change_type": "modify|create",
    "class_name": "...",
    "method_name": "...",
    "description": "...",
    "satisfies_ac": [],
    "satisfies_fr": [],
    "code_hint": "2-5 lines of pseudocode"
  }],
  "new_files": [{"file_path", "class_name", "description", "satisfies_fr"}],
  "test_changes": [{"file_path", "description", "test_type", "satisfies_ac"}]
}
```

### LLM client: `LLMClient`
- `provider: str` — `vscode_copilot` | `anthropic` | `copilot`
- `model: str`
- `total_tokens_used: int`
- `_usage: dict[agent_name, {calls, tokens_in, tokens_out, cost_usd}]`
- `call(system_prompt, user_prompt, max_tokens, temperature, agent_name) -> str`

---

## 5. Functional Modules & Implementation Details

### 5.1 CLI entrypoint

#### `defect_agent.py`
Commands (Click):
- `run --jira-id <ID>`: full pipeline from scratch.
- `run --requirements-file <PATH>`: intake from local file instead of Jira.
- `run-step --jira-id <ID> --step <STEP>`: run a single named step.
- `resume --jira-id <ID> --from-step <STEP>`: resume from a named step.
- `status --jira-id <ID>`: print current run state.

`_init_utils(config, defect_id, run_id)`: constructs shared utilities dict (`config`, `kb`, `logger`, `state`, `llm`, `defect_folder`).

`_run_id(defect_id)`: generates `<defect_id>_<UTC_timestamp>` run ID.

### 5.2 Orchestrator

#### `agents/defect_orchestrator.py` — `DefectOrchestrator`

`STAGE_MAP`: human-readable stage labels for display.

`__init__`: builds control plane (`ControlPlane.from_defaults("forward_engineering")`), stores shared utils.

`_check_global_stop(action, metadata)`: calls `ControlPlane.should_halt()` — if true, logs and exits.

`hitl_confirm(gate_label, message)`: if `hitl_mode == "skip"` auto-approves; otherwise renders a Rich `Confirm.ask` prompt and logs the decision to state.

`_get_agent(step_name)`: lazy-imports and returns the appropriate agent class instance.

`_should_skip_step(step)`: returns `True` for `defect_code` when `skip_code_generation=true` in state.

`run_full_pipeline()`: iterates `StateManager.PIPELINE_STEPS` in order, skips completed steps, calls `agent.run()`, marks step complete or failed. On failure prints resume command and exits.

`run_step(step_name)`: run a single named step.

`run_from_step(start_step)`: slice `PIPELINE_STEPS` from `start_step` and run remaining.

### 5.3 Agents

#### `DefectIntakeAgent` (Stage 1)
- Sources: Jira (via `MCPServiceBridge`) or local requirements file (via `RequirementsParser`), or both.
- Calls LLM (system: triage analyst) to classify `defect_type` and `defect_severity` from combined context.
- Derives `affected_repos` from `components` in the Jira ticket if not explicitly provided.
- Writes `defect_brief.json` to the KB defect folder.
- Presents summary table via Rich; waits for HITL confirm to proceed.

#### `DefectRepoScanAgent` (Stage 2)
- Reads `defect_brief.json` from state.
- For each `affected_repo`, clones or locates the repo. Reads relevant source files.
- Calls LLM (system: Senior Software Architect) to identify:
  - Files to modify (with class/method names and `change_needed` descriptions).
  - New files to create.
  - Coding patterns (`error_handling_style`, `logging_framework`, etc.).
  - Feature flag infrastructure (FeatureFlagHelper, FeatureFlagConstants, K8s YAML configs).
- Writes `repo_analysis.json`.
- Presents file table and HITL confirm.

#### `DefectPlanAgent` (Stage 3)
- Reads `defect_brief.json` + `repo_analysis.json`.
- Calls LLM twice: once for machine-readable `defect_fix_plan.json`, once for human-readable plan + HLD + LLD.
- Applies `load_workspace_memories()` for LLM context.
- Enforces NSA architecture compliance rules in the system prompt (service-type restrictions, reactive code, CXPController pattern, DTO placement).
- Writes `defect_fix_plan.json`, `defect_fix_plan.md`, `defect_hld_<id>.md`, `defect_lld_<id>.md`.
- Presents plan for HITL approve/reject.

#### `DefectCodeAgent` (Stage 4)
- Reads `defect_fix_plan.json` from state.
- For each change entry:
  1. Reads current file content from repo.
  2. Calls LLM (system: Senior Developer) to generate the complete patched file.
  3. AC self-check: calls LLM again to verify the patch satisfies the referenced ACs.
  4. If self-check fails, one revision attempt before writing.
  5. Backs up original file, writes patched file.
- Generates new files and test files similarly.
- In `md_only` mode: writes `defect_code_plan.md` only, no files modified.
- Enforces NSA rules in system prompt (blocking prohibition, service-type call restrictions, NSA controller pattern, DTO annotations).

#### `DefectGitAgent` (Stage 5)
- Reads `files_patched` from state.
- Groups patched files by `repo_path` for multi-repo commits.
- For each repo:
  1. Runs build validation (`mvn compile` or equivalent).
  2. Shows diff via Rich `Syntax` for human review.
  3. HITL confirm before committing.
  4. Creates/switches to branch `<git_branch_prefix>/<defect_id>`.
  5. `git add` + `git commit` with Jira-linked message.
  6. Optionally `git push` (HITL confirm).

### 5.4 Utilities

#### `LLMClient`
Three providers:
- `vscode_copilot`: HTTP POST to `http://127.0.0.1:<port>/chat`; no API key.
- `anthropic`: Anthropic SDK `messages.create()`.
- `copilot`: OpenAI SDK pointed at `https://api.githubcopilot.com`.

Retry: up to `max_llm_retries` with `RETRY_DELAY` seconds between attempts.

Usage tracking: per-agent `{calls, tokens_in, tokens_out, cost_usd}` dict.

#### `StateManager`
- `PIPELINE_STEPS = ["defect_intake", "defect_repo_scan", "defect_plan", "defect_code", "defect_git"]`
- `is_step_complete(step)` / `mark_step_complete(step)` / `mark_step_failed(step, reason)`
- `get(key)` / `set(key, value)`: typed key access to `_state` dict.
- `log_hitl_decision(gate, decision, note)`: appends to `hitl_decisions` list.
- Auto-saves to `run_state.json` on every mutation.

#### `KBStore`
- `init_defect_folder(project_key, defect_id)`: creates `<kb_root>/<project_key>/<defect_id>/` and returns its path.
- Provides path helpers for all standard artifact files.

#### `MCPServiceBridge`
- Fetches Jira ticket fields (summary, description, status, priority, components, labels, comments) via MCP protocol or falls back to direct Jira REST API.

---

## 6. Entry Points & Execution Flow

```
python defect_agent.py run --jira-id PROJ-1234
  │
  ├─ load_config(config.yaml)
  ├─ _init_utils()      ← builds KBStore, DefectLogger, StateManager, LLMClient
  ├─ DefectOrchestrator.run_full_pipeline()
  │   ├─ Stage 1: DefectIntakeAgent.run()    → defect_brief.json
  │   │   └─ HITL confirm
  │   ├─ Stage 2: DefectRepoScanAgent.run()  → repo_analysis.json
  │   │   └─ HITL confirm
  │   ├─ Stage 3: DefectPlanAgent.run()      → defect_fix_plan.json + md + HLD + LLD
  │   │   └─ HITL approve plan
  │   ├─ Stage 4: DefectCodeAgent.run()      → patched source files
  │   │   └─ HITL confirm commit
  │   └─ Stage 5: DefectGitAgent.run()       → git branch + commit
  │       └─ HITL confirm push
  └─ _print_summary()
```

Resume from failed step:
```
python defect_agent.py resume --jira-id PROJ-1234 --from-step defect_plan
```

Single step execution:
```
python defect_agent.py run-step --jira-id PROJ-1234 --step defect_code
```

---

## 7. Architecture Constraints Enforced by the System

The system prompts for Stages 2, 3, and 4 embed hard-coded NSA/VXP architecture rules that every planned or generated change must follow:

- **No blocking calls**: `RestTemplate`, `block()`, `blockFirst()`, `blockLast()`, `toFuture().get()` are forbidden.
- **Service-type call restrictions**: Aggregate → domain/adapter/vendor only. Domain → PNO/adapter/vendor only.
- **CXPController pattern**: Controllers implement `CXPController<T>`, REST endpoints + `validateRequest()` only, no business logic.
- **DTO placement**: All new/modified DTOs go in `vxp-data-model`. Never in `vxp-type-defs`.
- **pno-vxp is read-only**: Never generate changes to `pno-vxp` files.
- **Feature flag pattern**: Reuse existing `FeatureFlagHelper` + `FeatureFlagConstants`. Never introduce a second pattern.
- **Reactive error handling**: Use `Mono.error(new CXPException(...))` — never synchronous `throw`.
- **BRD as source of truth**: Every planned change must be traceable to BRD scope when a BRD is provided.
- **Call chain first**: Only modify files confirmed on the actual HTTP call chain (controller → service interface → impl).

---

## 8. Failure Handling & Rollback Behavior

### 8.1 Per-stage failure tracking

`StateManager` tracks failure at the stage level. When a stage raises an unhandled exception:
1. `mark_step_failed(step, reason)` records the failure and reason in `run_state.json`.
2. `DefectOrchestrator.run_full_pipeline()` catches the exception, prints a Rich error panel with the failure message and a `resume` command hint, then exits with a non-zero code.
3. Stages that completed successfully before the failure are preserved — the pipeline does not re-run them on resume.

### 8.2 LLM retry on transient failure

`LLMClient.call()` retries up to `max_llm_retries` times (default 3) with `RETRY_DELAY` seconds between attempts for:
- HTTP connection errors.
- Non-2xx HTTP responses from any provider.
- `anthropic.APIStatusError` with status 529 (overloaded) or 500.

After exhausting retries the exception is propagated to the calling agent, which marks the stage as failed.

### 8.3 Patched file backup and restore

`DefectCodeAgent` backs up each original source file before writing a patch:
- Backup path: `<original_file>.bak_<run_id>`.
- If the stage fails mid-way (e.g. LLM error on file N while files 1..N-1 are already written), the backup files remain on disk.
- To restore: copy each `*.bak_<run_id>` file back over its original.
- Manual restore is required — the pipeline does not auto-rollback partially written patches.

### 8.4 Git branch cleanup on failure

`DefectGitAgent` does not roll back committed changes automatically. If the stage fails after some files are committed:
- The branch `<git_branch_prefix>/<defect_id>` may exist in a partially committed state.
- To clean up: run `git checkout <default_branch> && git branch -D <branch_name>` in each affected repo.
- The `run_state.json` field `defect_committed` (per-repo) indicates which repos received commits.

### 8.5 HITL rejection handling

At any HITL gate, if the user rejects (answers `n` to a `Confirm.ask`):
- For Stage 3 (plan approval): the pipeline pauses and the `hitl_decisions` log records the rejection. The user must re-run from Stage 3 (`resume --from-step defect_plan`) after manually editing `defect_fix_plan.json` or re-running Stage 1/2.
- For Stage 5 (commit / push): rejection skips the git operation; the stage is still marked complete so the pipeline finishes without committing. The HITL decision is logged.

### 8.6 Resuming from a specific step

```bash
# Resume after any mid-pipeline failure
python defect_agent.py resume --jira-id PROJ-1234 --from-step defect_plan

# Re-run only code generation (e.g. after manually editing the fix plan)
python defect_agent.py run-step --jira-id PROJ-1234 --step defect_code
```

On resume, `StateManager` skips all steps recorded as completed and begins execution from the specified step. The `LLMClient` usage counters reset for the new run but the `run_state.json` preserves the full history of prior HITL decisions.
