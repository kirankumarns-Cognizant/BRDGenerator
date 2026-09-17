# System Specification & Architecture Blueprint

## 1. Project Overview & System Goals

This module implements the BRD Agent Framework, an autonomous code quality enforcement layer within the SDLC Agentic Framework. It deploys four specialized agents using the ReAct (Reasoning + Acting) pattern to continuously monitor and improve code quality after features are built. It is position-3 in the pipeline: requirements are created (Agent 1) and broken down (Agent 2), code is produced, and then the BRD Agent provides automated review, testing, and documentation on that code.

Primary goals:
- Analyse repository structure, complexity metrics, code smells, and dependencies for any configured repo.
- Perform automated PR review: retrieve diff, check code quality, verify test coverage, suggest refactoring, and post a review comment on the PR.
- Measure test coverage, identify untested code paths, suggest missing test cases, and generate test stubs.
- Generate and maintain documentation: extract docstrings, generate usage examples, produce README and API docs.
- Execute each goal as an autonomous ReAct loop: Think (LLM reasoning) → Act (run a tool) → Observe (record result) → iterate.
- Capture every reasoning step as a `ReasoningStep` trace for full auditability.
- Output structured JSON reports and Markdown artifacts to `outputs/`.
- Optionally register outputs as typed artifacts in the KB Store.

Target runtime:
- Python 3.10+.
- Local execution on Windows, macOS, or Linux.
- CLI mode via `python main.py --repo <path> --event <type>`.
- LLM backend: Claude 3.5 Sonnet (primary), Claude 3.5 Haiku (secondary).
- Triggered by: `push`, `pull_request`, `schedule` (cron), or `manual`.

---

## 2. Tech Stack & Dependencies

### Core stack
- Language: Python.
- Orchestration: LangGraph (state-based agent graph).
- LLM: Anthropic Claude (`anthropic>=0.7.0`).
- Config: PyYAML.
- Data models: Pydantic v2.
- CLI: Click + Rich.
- Repo operations: GitPython (`>=3.1.0`), pygit2 (`>=1.13.0`).

### Code analysis tools
- `radon>=6.0.0`: cyclomatic complexity metrics.
- `pylint>=3.0.0`: code quality linting.
- `pycodestyle>=2.10.0`: PEP 8 compliance.
- `bandit>=1.7.5`: security scanning.

### Testing tools
- `pytest>=7.0.0`, `coverage>=7.0.0`, `pytest-cov>=4.0.0`.

### Documentation tools
- `sphinx>=5.0.0`, `sphinx-rtd-theme>=1.0.0`.

### Required Python packages (`requirements.txt`)
- `anthropic>=0.7.0`
- `PyYAML>=6.0`
- `pydantic>=2.0.0`
- `langgraph>=0.0.1`
- `pygit2>=1.13.0`, `GitPython>=3.1.0`
- `radon>=6.0.0`, `pylint>=3.0.0`, `pycodestyle>=2.10.0`, `bandit>=1.7.5`
- `pytest>=7.0.0`, `coverage>=7.0.0`, `pytest-cov>=4.0.0`
- `sphinx>=5.0.0`, `sphinx-rtd-theme>=1.0.0`
- `click>=8.0.0`, `rich>=13.0.0`

### Configuration (`services/config.yaml`)
Key sections:
- `global.repo_path`: path to the target repository (required).
- `global.repo_name`: repository name (used in KB Store artifact registration).
- `global.llm_primary` / `global.llm_secondary`: model names.
- `global.max_iterations`: ReAct loop iteration cap (default 5).
- `global.confidence_threshold`: minimum confidence to consider task complete (default 0.5).
- `global.output.dir` / `global.output.format`.
- `agents.<agent-id>.enabled`: enable/disable individual agents.
- `agents.<agent-id>.model`: per-agent model override.
- `agents.<agent-id>.max_iterations`: per-agent iteration cap.
- `agents.<agent-id>.tools`: list of allowed tools for this agent.
- `agents.<agent-id>.thresholds`: quality/coverage thresholds.
- `agents.<agent-id>.triggers`: list of `{event, cron?}` that activate the agent.

---

## 3. Project Directory Structure

### `brd/brd_agent/`
- `main.py`: CLI entrypoint (Click). Parses `--repo`, `--event`, `--pr`, `--agent`, `--config`, `--verbose`.
- `requirements.txt`: Python dependencies.
- `README.md`: overview and quick start.
- `STRUCTURE.md`: architecture guide.
- `__init__.py`: package marker.

### `services/`
- `main_process.py`: `MainAgentService` — orchestrates agent execution, state lifecycle, output writing, KB Store registration.
- `config.yaml`: complete agent configuration.
- `__init__.py`.

### `services/agents/`
- `base_agent.py`: `BaseGitHubAgent` — abstract base implementing ReAct pattern (`think`, `act`, `observe`, `run` loop).
- `code_analysis_agent.py`: `CodeAnalysisAgent`.
- `code_review_agent.py`: `CodeReviewAgent`.
- `testing_agent.py`: `TestingAgent`.
- `documentation_agent.py`: `DocumentationAgent`.
- `__init__.py`: exports `get_agent_class`, `get_all_agents`, all four agent classes.

### `services/models/`
- `state_model.py`: `BrdAgentState`, `ReasoningStep`, `ToolResult`, `AgentOutput`.
- `agent_models.py`: `AgentExecutionRequest`, `AgentExecutionResponse`, `CodeAnalysisOutput`, `CodeReviewOutput`, `TestingOutput`, `DocumentationOutput`, `ToolDefinition`.
- `__init__.py`: aggregated exports.

### `services/tools/`
- `code_analysis_tools.py`: tool implementations for `CodeAnalysisAgent`.
- `code_review_tools.py`: tool implementations for `CodeReviewAgent`.
- `testing_tools.py`: tool implementations for `TestingAgent`.
- `documentation_tools.py`: tool implementations for `DocumentationAgent`.

### `services/observability/`
- LangSmith integration for ReAct trace export and monitoring.

### `outputs/`
- Runtime-generated JSON reports and Markdown artifacts. One folder per run (UUID).

---

## 4. Data Schemas, Interfaces & State

### `BrdAgentState`
Shared mutable state passed between all agents.

**Input fields:**
- `repo_path: str` — path to the repository being analysed.
- `repo_name: str` — display name.
- `trigger_event: str` — `push` | `pull_request` | `schedule` | `manual`.
- `pr_number: Optional[int]` — PR number (for `pull_request` events).
- `commit_sha: Optional[str]` — commit hash.

**Result fields (one per agent):**
- `code_analysis_results: Dict[str, Any]` — written by `CodeAnalysisAgent`.
- `code_review_results: Dict[str, Any]` — written by `CodeReviewAgent`.
- `testing_results: Dict[str, Any]` — written by `TestingAgent`.
- `documentation_results: Dict[str, Any]` — written by `DocumentationAgent`.

### `ReasoningStep`
Records one iteration of the ReAct loop:
- `step_num: int`
- `thought: str` — LLM reasoning text.
- `action: str` — tool name executed.
- `observation: str` — tool result summary.
- `timestamp: str` — ISO datetime.
- `to_dict() -> Dict`

### `ToolResult`
Returned by every `act()` call:
- `tool_name: str`
- `status: str` — `✅ Success` | `⚠️ Warning` | `❌ Error`
- `data: Dict[str, Any]`
- `error: Optional[str]`

### `AgentOutput`
Final output of one agent execution:
- `agent_name: str`
- `reasoning_steps: List[Dict]`
- `final_result: Dict[str, Any]`
- `status: str` — `completed` | `failed` | `requires_review`
- `iteration_count: int`
- `timestamp: str`
- KB Store fields: `domain`, `artifact_type`, `artifact_id`, `lineage`

### `ToolDefinition`
Registered capability of an agent:
- `name: str`, `description: str`, `parameters: Dict[str, str]`

### `AgentExecutionRequest`
- `repo_path`, `repo_name`, `trigger_event`
- `pr_number: Optional[int]`
- `commit_sha: Optional[str]`
- `agent_name: Optional[str]` — if `None`, run all applicable agents.
- `config: Dict[str, Any]`

### `AgentExecutionResponse`
- `run_id: str` (UUID)
- `agents_executed: List[str]`
- `status: str` — `success` | `partial_success` | `failed`
- `results: Dict[str, Any]`
- `warnings: List[str]`, `errors: List[str]`
- `artifacts: Dict[str, str]` — `artifact_type → file_path`
- `execution_time_seconds: float`
- KB Store fields: `domain`, `artifact_ids`, `lineage`

### Per-agent output models

#### `CodeAnalysisOutput`
- `repository`, `total_files`, `file_types: Dict[str, int]`
- `complexity_metrics: Dict[str, float]`
- `code_smells: List[Dict]`
- `dependencies: Dict`
- `health_score: float`
- `recommendations: List[str]`, `warnings: List[str]`
- KB fields: `artifact_id`, `domain`, `artifact_type="code_review"`, `lineage`

#### `CodeReviewOutput`
- Review verdicts, issue list, coverage assessment, refactoring suggestions.
- `artifact_type="code_review"`

#### `TestingOutput`
- `coverage_percentage: float`
- `untested_files: List[str]`
- `suggested_tests: List[Dict]`
- `test_templates: List[str]`
- `artifact_type="test_cases"`

#### `DocumentationOutput`
- `readme_content: str`
- `api_docs: Dict[str, str]`
- `docstring_coverage: float`
- `artifact_type="api_spec"`

### KB Store artifact type mapping
| Agent | `artifact_type` |
|---|---|
| `code-analysis` | `code_review` |
| `code-review` | `code_review` |
| `testing` | `test_cases` |
| `documentation` | `api_spec` |

---

## 5. Functional Modules & Implementation Details

### 5.1 CLI entrypoint

#### `main.py`
Click commands/options:
- `--repo <path>`: repository path (default `.`).
- `--event <type>`: `push` | `pull_request` | `schedule` | `manual`.
- `--pr <number>`: PR number for `pull_request` events.
- `--agent <name>`: run only the named agent.
- `--config <path>`: path to config YAML (default `services/config.yaml`).
- `--verbose`: enable debug output.

Flow:
1. Load config from YAML.
2. Build `AgentExecutionRequest`.
3. Call `MainAgentService.execute_agents(request)`.
4. Print `AgentExecutionResponse` summary.

### 5.2 Orchestrator

#### `services/main_process.py` — `MainAgentService`

`execute_agents(request) -> AgentExecutionResponse` (async):
1. Generate `run_id` (UUID).
2. Initialise `BrdAgentState` from request.
3. Determine which agents apply to the trigger event (from config triggers).
4. If `request.agent_name` is set, run only that agent.
5. For each selected agent: instantiate, call `agent.run(state)`, collect `AgentOutput`.
6. Write outputs to `outputs/<run_id>/`.
7. If KB Store is configured, register each output as an artifact (`AGENT_ARTIFACT_TYPE_MAP`).
8. Return `AgentExecutionResponse`.

`_infer_domain(repo_name)`: maps repo name keywords to KB Store domain strings.

`_new_artifact_id()`: `<UTC_timestamp>_<8-char UUID hex>`.

### 5.3 Base Agent

#### `services/agents/base_agent.py` — `BaseGitHubAgent`

`run(state) -> AgentOutput`:
1. `context = ""`
2. `for i in range(max_iterations):`
   - `thought = self.think(state, context)` — LLM call.
   - `tool_name = self._select_tool(thought, available_tools)` — picks next tool in fixed workflow order.
   - `result = self.act(tool_name, params)` — calls `_get_tool_executor(tool_name)()`.
   - Record `ReasoningStep(i, thought, tool_name, result.status)`.
   - `context += observation`
   - If `_is_complete(result)`: break.
3. Return `AgentOutput(agent_name, reasoning_steps, final_result, status, iteration_count)`.

`think(state, context) -> str`: abstract — LLM call using `system_prompt` + `user_prompt`.

`_get_tool_executor(tool_name) -> Callable`: abstract — returns tool implementation function.

`act(tool_name, parameters) -> ToolResult`: looks up tool in `self.tools`, calls executor, wraps result.

`register_tool(tool_def)`: adds `ToolDefinition` to `self.tools`.

### 5.4 Code Analysis Agent

#### `services/agents/code_analysis_agent.py`

Tools (executed in fixed order):
1. `scan_repo_structure`: walk repo dirs (excluding `.git`, `__pycache__`, `node_modules`, etc.), count files by extension, count directories.
2. `analyze_complexity`: parse Python files with `ast`, compute cyclomatic complexity per function, flag functions exceeding `cyclomatic_complexity_warning` (10) or `_critical` (15).
3. `detect_code_smells`: detect anti-patterns (long methods, duplicate code, magic numbers, missing docstrings) via regex + AST.
4. `analyze_dependencies`: map import graph between modules.
5. `generate_metrics_report`: aggregate all findings into `CodeAnalysisOutput` with `health_score` (0–10 float).

Writes `state.code_analysis_results`.

### 5.5 Code Review Agent

#### `services/agents/code_review_agent.py`

Tools (executed in fixed order):
1. `get_pr_diff`: retrieve changed files list and diff stats (files, additions, deletions).
2. `check_code_quality`: run quality checks on changed files.
3. `check_test_coverage`: verify tests exist for changed code.
4. `suggest_refactoring`: produce per-file improvement suggestions.
5. `post_pr_comment`: compose and post review comment to the PR.

Writes `state.code_review_results`.
Requires `pr_number` in state (only runs on `pull_request` events).

### 5.6 Testing Agent

#### `services/agents/testing_agent.py`

Tools (executed in fixed order):
1. `measure_coverage`: run `coverage` / `pytest-cov` and parse report.
2. `identify_coverage_gaps`: find source files with coverage below threshold.
3. `suggest_tests`: generate test-case descriptions for uncovered functions.
4. `generate_test_templates`: write pytest stub functions for suggested cases.
5. `analyze_test_quality`: assess test effectiveness (assertion density, fixture usage, parametrization).

Writes `state.testing_results`.

### 5.7 Documentation Agent

#### `services/agents/documentation_agent.py`

Tools (executed in fixed order):
1. `parse_code`: traverse AST, extract public classes, functions, and modules.
2. `extract_docstrings`: collect existing docstrings; measure docstring coverage.
3. `generate_examples`: create usage code snippets per public function.
4. `generate_readme`: produce or update `README.md` (project overview, installation, usage, API summary).
5. `generate_api_docs`: produce Sphinx-compatible API reference.

Writes `state.documentation_results`.

---

## 6. Entry Points & Execution Flow

```
python main.py --repo ./my-service --event push
  │
  ├─ load_config(services/config.yaml)
  ├─ AgentExecutionRequest{repo_path, trigger_event="push"}
  ├─ MainAgentService.execute_agents()
  │   ├─ BrdAgentState initialized
  │   ├─ Agents selected for "push": CodeAnalysisAgent, TestingAgent, DocumentationAgent
  │   │
  │   ├─ CodeAnalysisAgent.run(state)
  │   │   ├─ scan_repo_structure → analyze_complexity → detect_code_smells
  │   │   ├─ analyze_dependencies → generate_metrics_report
  │   │   └─ state.code_analysis_results = {health_score, complexity, smells, ...}
  │   │
  │   ├─ TestingAgent.run(state)
  │   │   ├─ measure_coverage → identify_coverage_gaps → suggest_tests
  │   │   ├─ generate_test_templates → analyze_test_quality
  │   │   └─ state.testing_results = {coverage_pct, gaps, templates, ...}
  │   │
  │   ├─ DocumentationAgent.run(state)
  │   │   ├─ parse_code → extract_docstrings → generate_examples
  │   │   ├─ generate_readme → generate_api_docs
  │   │   └─ state.documentation_results = {readme, api_docs, coverage, ...}
  │   │
  │   └─ Write outputs/ + optional KB Store registration
  │
  └─ AgentExecutionResponse printed to console

python main.py --repo ./my-service --pr 42 --event pull_request
  └─ Runs CodeReviewAgent only → posts review comment to PR #42
```

---

## 7. Testing

### Test files
- `tests/` — unit tests for individual tools and agent ReAct loop.
- `test_langsmith.py` — LangSmith integration trace tests.

### Running tests
```bash
pytest tests/ -v
pytest test_langsmith.py -v  # requires LANGSMITH_API_KEY
```

All tests run with mock LLM responses — no API key required for tool-level tests.

---

## 8. Trigger Event to Agent Mapping

The following table defines which agents are activated for each trigger event type, as configured in `services/config.yaml` under `agents.<agent-id>.triggers`:

| Trigger event | Agents activated |
|---|---|
| `push` | `CodeAnalysisAgent`, `TestingAgent`, `DocumentationAgent` |
| `pull_request` | `CodeReviewAgent`, `TestingAgent` |
| `schedule` (cron) | `CodeAnalysisAgent`, `TestingAgent`, `DocumentationAgent` |
| `manual` | All enabled agents (respects `agents.<id>.enabled` flag) |

If `--agent <name>` is provided on the CLI, only the named agent runs regardless of trigger type.

Agent enablement is controlled per-agent in config:
```yaml
agents:
  code-analysis:
    enabled: true
    triggers:
      - event: push
      - event: schedule
        cron: "0 2 * * 1"   # every Monday at 2 AM
  code-review:
    enabled: true
    triggers:
      - event: pull_request
  testing:
    enabled: true
    triggers:
      - event: push
      - event: pull_request
  documentation:
    enabled: true
    triggers:
      - event: push
      - event: manual
```

---

## 9. Tool Failure & Error Handling Strategy

### 9.1 Per-tool error handling in the ReAct loop

Each call to `act(tool_name, parameters)` wraps the tool executor in a try/except:
- On success: returns `ToolResult(status="✅ Success", data={...})`.
- On warning (e.g. partial result): returns `ToolResult(status="⚠️ Warning", data={...}, error=<detail>)`.
- On hard failure: returns `ToolResult(status="❌ Error", data={}, error=<exception_message>)`.

The `ToolResult` is always returned — tool failures do not raise exceptions out of `act()`. This allows the ReAct loop to observe the failure and reason about it in the next `think()` step.

### 9.2 ReAct loop behavior on tool failure

When `act()` returns a `ToolResult` with status `"❌ Error"`:
- The error is appended to `context` as an observation: `"Tool <name> failed: <error>"`.
- `_is_complete()` returns `False` for error results.
- The loop continues to the next iteration, allowing the LLM to attempt a different approach or skip the failing tool.
- If the same tool fails on every iteration until `max_iterations` is reached, the loop exits and `AgentOutput.status` is set to `"requires_review"` instead of `"completed"`.

### 9.3 Agent-specific tool failure behavior

| Agent | Tool failure behavior |
|---|---|
| `CodeAnalysisAgent` | If `analyze_complexity` fails (non-Python repo), the loop continues to `detect_code_smells` using file-level heuristics only. `health_score` is computed from available data. |
| `CodeReviewAgent` | If `get_pr_diff` fails (no PR number in state), the entire agent short-circuits and returns `status="requires_review"` without running further tools. |
| `TestingAgent` | If `measure_coverage` fails (no test suite), subsequent tools (`identify_coverage_gaps`, `suggest_tests`) are skipped; the agent returns `coverage_percentage=0`. |
| `DocumentationAgent` | If `parse_code` fails (non-Python or unreadable files), subsequent tools use empty AST data; `docstring_coverage=0` and generated docs are skeleton-only. |

### 9.4 KB Store registration failure

If KB Store artifact registration fails in `MainAgentService.execute_agents()`:
- The failure is logged as a warning.
- The `AgentExecutionResponse.warnings` list receives an entry describing which artifact was not registered.
- The overall response `status` is downgraded to `"partial_success"` if at least one agent succeeded.
- Outputs are still written to `outputs/<run_id>/` — local file output is always attempted regardless of KB Store availability.

### 9.5 LLM API failures in `think()`

If the LLM call in `think()` raises an exception:
- The exception propagates out of the ReAct loop.
- `BaseGitHubAgent.run()` does not catch it.
- `MainAgentService.execute_agents()` catches it, records it in `AgentExecutionResponse.errors`, and marks that agent's run as `"failed"`.
- Other agents in the run are still executed if they are not dependent on the failed agent's state fields.
