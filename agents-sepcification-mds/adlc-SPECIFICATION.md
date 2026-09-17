# System Specification & Architecture Blueprint

## 1. Project Overview & System Goals

This module implements the ADLC (Agile Development Lifecycle Coordinator) Orchestration layer within the KnowledgebaseVegas platform. It is an event-driven workflow engine that manages a 5-phase, 20-agent release lifecycle from requirement intake through post-deployment verification. The ADLC orchestrator coordinates agents across phases, enforces dependency ordering, manages human approval gates, and passes artifacts between agents.

Primary goals:
- Manage a complete release lifecycle: PLAN → BUILD → FREEZE → TEST → RELEASE.
- Maintain an agent registry that records every agent's phase, implementation status, input/output artifacts, dependencies, and whether a human gate is required.
- Run an event bus that triggers agents based on events published by preceding agents, not by direct calls.
- Enforce dependency ordering: an agent only becomes executable when all of its declared dependencies have completed.
- Pause the workflow at human gate points and resume when approval is received.
- Track all artifacts in a shared `WorkflowState` dict passed between agents.
- Integrate with Agent 2 (Requirement Breakdown Agent) for the PLAN phase via `ReleasePlanningAgent` and `StoryGenerationAgent`.
- Integrate with the Forward Engineering Defect Pipeline for defect resolution in the TEST phase.
- Persist workflow state for resumability.

Target runtime:
- Python 3.10+.
- Library / module consumed by higher-level runners (no standalone CLI entry point).
- All agents callable programmatically via `ADLCOrchestrator.execute_agent(agent_id, artifacts)`.

---

## 2. Tech Stack & Dependencies

### Core stack
- Language: Python.
- Orchestration: Custom event-driven state machine (not LangGraph at the ADLC layer).
- Data structures: Python `dataclasses` and `TypedDict`-style patterns.
- UI: Rich (used by individual agent implementations for progress display).
- Agent 2 integration: Optional import of `requirement-breakdown-agent` package.
- Forward Engineering integration: Reuses `forward_engineering.agents.*` for defect fix and code gen.

### Agent-specific packages (used by individual agent implementations)
- `anthropic`, `openai` — LLM calls in build agents.
- `rich` — terminal UI.
- `networkx` — dependency graph traversal (impact graph).
- `subprocess` — git operations in freeze agents.

### No additional `requirements.txt` at the ADLC layer
Individual agent modules (`build_agents.py`, `freeze_agents.py`, etc.) have their own imports; the orchestration layer itself uses only the Python standard library plus the above.

---

## 3. Project Directory Structure

### `adlc/` package
- `orchestrator.py`: `ADLCOrchestrator` — main state machine and event-driven workflow engine.
- `agent_registry.py`: `AGENT_REGISTRY` dict, `Agent` dataclass, `AgentStatus` enum, all 20 agent definitions.
- `events.py`: `EventType` enum (35 event types), `Event` dataclass, `WorkflowState` dataclass, `EventBus` class.
- `plan_agents.py`: `ReleasePlanningAgent`, `StoryGenerationAgent` — PLAN phase; wraps Requirement Breakdown Agent.
- `build_agents.py`: `CodePlanAgent`, `FeatureCodeGenerationCompleteAgent`, `CodeReviewAgent`, `MRGovernanceGate`, `MRTestAgent`, `MRReqAgent` — BUILD phase.
- `freeze_agents.py`: `ChangeDiscoveryAgent`, `ImpactGraphAgent`, `PlanReconciliationAgent` — FREEZE phase.
- `test_agents.py`: `DefectAnalysisResolutionAgent`, `DefectFixAgent` — TEST phase.
- `diagrams.py`: Mermaid diagram generation for workflow visualization.
- `integration.py`: Integration helpers for connecting ADLC with external systems.
- `viewer.py`: CLI/UI for workflow state inspection.
- `examples.py`: Example workflow invocations.
- `README.md`, `OVERVIEW.md`, `IMPLEMENTATION_SUMMARY.md`: documentation.
- `__init__.py`: package marker.

---

## 4. Data Schemas, Interfaces & State

### `Agent` (dataclass)
```python
@dataclass
class Agent:
    id: str                    # unique agent ID, e.g. "release-planning"
    name: str                  # human-readable name
    phase: str                 # "PLAN" | "BUILD" | "FREEZE" | "TEST" | "RELEASE"
    status: AgentStatus        # IMPLEMENTED | PARTIAL | NOT_IMPLEMENTED
    description: str
    inputs: List[str]          # required artifact/event names
    outputs: List[str]         # artifact/event names produced
    dependencies: List[str]    # agent IDs that must complete first
    location: Optional[str]    # file path in codebase
    human_gate_required: bool  # whether to pause for human approval
```

### `AgentStatus` (enum)
- `IMPLEMENTED`: fully working in codebase.
- `PARTIAL`: partially implemented.
- `NOT_IMPLEMENTED`: not yet built.

### `Event` (dataclass)
```python
@dataclass
class Event:
    event_type: EventType
    agent_id: str
    timestamp: datetime
    data: Dict[str, Any]   # artifacts and metadata
    correlat_id: str       # release ID or defect ID
    human_approved: bool
    approved_by: Optional[str]
```

### `WorkflowState` (dataclass)
```python
@dataclass
class WorkflowState:
    release_id: str
    current_phase: str
    current_agent: Optional[str]
    completed_agents: List[str]
    failed_agents: List[str]
    events: List[Event]
    artifacts: Dict[str, Any]  # shared artifact storage passed between agents
    paused: bool
    pause_reason: Optional[str]
```

### `EventType` enum — all 35 event types

**PLAN phase:**
- `RELEASE_PLAN_DRAFTED`, `RELEASE_PLAN_APPROVED`
- `STORIES_GENERATED`, `STORIES_APPROVED`

**BUILD phase:**
- `CODE_PLAN_DRAFTED`, `CODE_PLAN_APPROVED`
- `FEATURE_CODE_GENERATED`, `MR_CREATED`, `MR_GOVERNANCE_PASSED`
- `MR_TEST_COMPLETE`, `PR_APPROVED`

**FREEZE phase:**
- `CHANGES_DISCOVERED`, `IMPACT_GRAPH_BUILT`
- `PLAN_RECONCILED`, `PLAN_RECONCILIATION_APPROVED`

**TEST phase:**
- `REGRESSION_COMPLETE`, `FAILURES_TRIAGED`, `DEFECTS_FILED`
- `DEFECT_ANALYSIS_COMPLETE`, `DEFECT_FIX_SUBMITTED`, `DEFECT_FIX_APPROVED`

**RELEASE phase:**
- `PLAN_REFRESHED`, `DEPLOYMENT_MANIFEST_READY`
- `EVIDENCE_PACK_READY`, `RELEASE_GO_NO_GO_APPROVED`
- `DEPLOYMENT_COMPLETE`, `POST_DEPLOY_VERIFICATION_COMPLETE`

**Errors:**
- `AGENT_EXECUTION_FAILED`, `HUMAN_ESCALATION_REQUIRED`, `WORKFLOW_PAUSED`

---

## 5. Complete Agent Registry — All 20 Agents

### Phase 1: PLAN (2 agents)

| ID | Name | Status | Human Gate | Dependencies |
|---|---|---|---|---|
| `release-planning` | Release Planning Agent | IMPLEMENTED | yes | — |
| `story-generation` | Story Generation Agent | IMPLEMENTED | yes | `release-planning` |

**Release Planning Agent** (`plan_agents.py::ReleasePlanningAgent`)
- Inputs: `brd_documents`, `uploads`, `jira_project_key`
- Outputs: `release_plan`, `requirements`, `epics`, `stories`, `tasks`, `analysis`, `delivery_plan`
- Implementation: delegates to `BreakdownAgent` façade from requirement-breakdown-agent package. Falls back to deterministic BRD-parser + story-generator when package is absent.

**Story Generation Agent** (`plan_agents.py::StoryGenerationAgent`)
- Inputs: `release_plan`, `epics`, `stories`, `tasks`
- Outputs: `jira_records`, `jira_preview`, `story_breakdown`
- Implementation: delegates to `JiraMappingAgent` from requirement-breakdown-agent. Falls back to deterministic field-assembly mapper.

---

### Phase 2: BUILD (6 agents)

| ID | Name | Status | Human Gate | Dependencies |
|---|---|---|---|---|
| `code-plan` | Code Plan Agent | IMPLEMENTED | yes | `story-generation` |
| `feature-code-gen` | Feature Code Generation Agent | IMPLEMENTED | no | `code-plan` |
| `code-review` | Code Review Agent | IMPLEMENTED | yes | `feature-code-gen` |
| `mr-governance` | MR Governance & Traceability Gate | IMPLEMENTED | no | `code-review` |
| `mr-test` | MR-Test Agent | IMPLEMENTED | no | `code-review` |
| `mr-req` | MR-Req Agent | IMPLEMENTED | no | `feature-code-gen` |

**Code Plan Agent** (`build_agents.py::CodePlanAgent`)
- Inputs: `jira_story`, `brd_documents`
- Outputs: `code_plan_hld`, `code_plan_lld`, `affected_files`
- Flags stale BRDs (>6 months old). Produces HLD and LLD.

**Feature Code Generation Agent** (`build_agents.py::FeatureCodeGenerationCompleteAgent`)
- Inputs: `code_plan_lld`, `brd_requirements`, `acceptance_criteria`
- Outputs: `generated_code`, `feature_flag_definition`
- Wraps every feature in a feature flag with owner and expiry date.

**Code Review Agent** (build_agents.py + forward_engineering)
- Inputs: `generated_code`
- Outputs: `mr_created`
- Creates merge request.

**MR Governance & Traceability Gate** (`build_agents.py::MRGovernanceGate`)
- Validates: real Jira key (no `0000`), in approved scope, brand-appropriate, feature flag registered and owned.

**MR-Test Agent** (build_agents.py + forward_engineering)
- Inputs: `generated_code`, `impact_graph`
- Selects from existing test suite; generates missing test cases for impacted paths only.

**MR-Req Agent** (`build_agents.py::MRReqAgent`)
- Verifies code change against requirements and ACs at MR time.

---

### Phase 3: FREEZE (3 agents)

| ID | Name | Status | Human Gate | Dependencies |
|---|---|---|---|---|
| `change-discovery` | Change Discovery Agent | IMPLEMENTED | no | — |
| `impact-graph` | Impact Graph | IMPLEMENTED | no | `change-discovery` |
| `plan-reconciliation` | Plan Reconciliation Agent | IMPLEMENTED | yes | `impact-graph` |

**Change Discovery Agent** (`freeze_agents.py::ChangeDiscoveryAgent`)
- Inputs: `git_last_deployed_tag`, `git_current_head`
- Outputs: `discovered_commits`, `undocumented_changes`
- `git diff <last_tag>..HEAD` — discovers what actually changed, including commits never in the plan.

**Impact Graph Agent** (`freeze_agents.py::ImpactGraphAgent`)
- Inputs: `jira_stories`, `discovered_commits`, `service_map`, `consumer_map`
- Outputs: `impact_graph_json`
- Builds spine: Jira keys → commits → repos → services → downstream consumers → test paths.

**Plan Reconciliation Agent** (`freeze_agents.py::PlanReconciliationAgent`)
- Inputs: `release_plan`, `discovered_commits`, `impact_graph_json`
- Outputs: `plan_reconciliation_delta`, `updated_release_plan`
- Maps actual commits back to plan; produces plan-vs-actual delta.

---

### Phase 4: TEST (4 agents)

| ID | Name | Status | Human Gate | Dependencies |
|---|---|---|---|---|
| `selective-regression` | QE Selective Regression | NOT_IMPLEMENTED | no | `impact-graph` |
| `failure-triage` | Tapsium Failure Triage Agent | NOT_IMPLEMENTED | no | `selective-regression` |
| `defect-analysis` | Defect Analysis & Resolution Agent | IMPLEMENTED | no | `failure-triage` |
| `defect-fix` | Defect Fix Agent | IMPLEMENTED | yes | `defect-analysis` |

**QE Selective Regression** — not yet implemented. Regression only on impacted paths, tiered by change complexity.

**Tapsium Failure Triage Agent** — not yet implemented. Classifies every failure (data-setup, environment, flake, or code defect), routes to owning team, files Jira.

**Defect Analysis & Resolution Agent** (`test_agents.py::DefectAnalysisResolutionAgent`)
- Three-stage pipeline: Intake & Brief → Repo Intelligence → Fix Planning.
- Delegates to `forward_engineering.agents.*` pipeline.
- Outputs: `defect_resolution_plan`, `defect_fix_plan_json`, `hld_doc`, `lld_doc`.

**Defect Fix Agent** (build_agents.py + forward_engineering)
- Turns resolution into coding plan against BRD; makes flagged fix; raises PR.

---

### Phase 5: RELEASE (5 agents)

| ID | Name | Status | Human Gate | Dependencies |
|---|---|---|---|---|
| `plan-refresh` | Plan Refresh | NOT_IMPLEMENTED | no | `defect-fix` |
| `pointed-sync-scope` | Pointed-Sync Scope Agent | NOT_IMPLEMENTED | no | `plan-refresh` |
| `evidence-pack` | Release Evidence Pack | NOT_IMPLEMENTED | no | `pointed-sync-scope` |
| `release-gate` | Release Gate / Go–No-Go | NOT_IMPLEMENTED | yes | `evidence-pack` |
| `pointed-sync-deploy` | Pointed Sync Deploy | NOT_IMPLEMENTED | no | `release-gate` |
| `post-deploy-verify` | Post-deploy Verification | NOT_IMPLEMENTED | no | `pointed-sync-deploy` |

None of the RELEASE phase agents are implemented yet. The intended flow:
1. Refresh plan to reflect what actually landed after fix cycle.
2. Scope deployment: impact graph → deployment manifest (~75 services → ~17 impacted).
3. Assemble evidence pack: scope, plan-vs-actual delta, test results, triage summary, flag state.
4. Go/No-Go gate: human approval required.
5. Deploy only impacted services.
6. Per-service smoke test; verify every flag is in intended state.

---

## 6. Functional Modules & Implementation Details

### 6.1 Orchestrator

#### `orchestrator.py` — `ADLCOrchestrator`

`__init__(release_id, storage_path)`:
- Initialises `WorkflowState`, `EventBus`, and registers event handlers.
- `_agent_executors: Dict[str, Callable]` — per-agent executor functions registered externally.

`register_agent_executor(agent_id, executor)`:
- Registers a callable that will be invoked by `execute_agent`.

`get_next_executable_agents() -> List[Agent]`:
- Returns agents whose dependencies are all in `state.completed_agents` and whose phase is not paused.

`execute_agent(agent_id, input_artifacts) -> Optional[Event]`:
- Calls registered executor or falls back to placeholder event for unimplemented agents.
- After execution, if `agent.human_gate_required`: sets `state.paused = True` and `state.pause_reason`.
- Publishes the resulting event to the event bus.

`approve_and_resume(gate_event_type, approved_by)`:
- Sets `human_approved=True` on the pending event, unpauses state, resumes workflow.

Event handler methods (`_on_plan_approved`, `_on_stories_approved`, etc.):
- Each advances `state.completed_agents` and calls the next agent in sequence.

### 6.2 Event Bus

#### `events.py` — `EventBus`
- `subscribe(event_type, handler)`: registers a handler function for an event type.
- `publish(event)`: calls all handlers subscribed to `event.event_type`.
- Handler signature: `handler(event: Event) -> None`.

### 6.3 Agent Registry

#### `agent_registry.py`
- `AGENT_REGISTRY: Dict[str, Agent]` — all 20 agents keyed by `agent_id`.
- `get_agent(agent_id) -> Optional[Agent]`
- `get_agents_by_phase(phase) -> List[Agent]`
- `get_implemented_agents() -> List[Agent]`

### 6.4 PLAN phase agents

#### `plan_agents.py`

**`ReleasePlanningAgent`**:
- Tries to import `BreakdownAgent` from requirement-breakdown-agent package at `../../requirement-breakdown-agent`.
- If available: runs full BRD → breakdown pipeline via `BreakdownAgent.start()` / `BreakdownAgent.turn()`.
- If unavailable: deterministic BRD-parser — regex heading/bullet extraction → story generation without LLM.
- Publishes `RELEASE_PLAN_DRAFTED` event on completion. Requires human approval.

**`StoryGenerationAgent`**:
- Tries to import `JiraMappingAgent` from requirement-breakdown-agent.
- If available: calls full Jira mapping pipeline.
- If unavailable: deterministic field-assembly mapper builds Jira records from epic/story/task dicts.
- Publishes `STORIES_GENERATED` event. Requires human approval.

### 6.5 BUILD phase agents

#### `build_agents.py`

**`CodePlanAgent`**:
- Reads Jira story + finds BRD for affected services.
- Checks BRD staleness (flags if >6 months).
- Drafts HLD (architecture/design) and LLD (implementation details).
- Returns `CodePlan` dataclass.

**`FeatureCodeGenerationCompleteAgent`**:
- Generates `FeatureFlag` definition (name, owner, `config_profile`, `expiry_days`, `helper_method`, `constant_name`).
- Writes code wrapped in feature flag guard.

**`MRGovernanceGate`**:
- Validates `MRMetadata` (title, description, jira_key, branch_name, commits).
- Checks: real Jira key, approved scope, feature flag in registry, brand-appropriate naming.

**`MRReqAgent`**:
- Verifies generated code meets AC from the original Jira story.

### 6.6 FREEZE phase agents

#### `freeze_agents.py`

**`ChangeDiscoveryAgent`**:
- `run(git_tag, current_head)`: executes `git diff <tag>..<head> --name-only` and `git log` in configured repos.
- Extracts Jira keys from commit messages.
- Returns: `List[Commit]`, `undocumented_changes: List[str]`.

**`ImpactGraphAgent`**:
- Builds `ImpactNode` / `ImpactEdge` graph:
  `commit → file → repo → service → consumer → test_path`.
- Serializes to `impact_graph_json`.

**`PlanReconciliationAgent`**:
- Compares `discovered_commits` Jira keys against `release_plan` story keys.
- Produces delta: missing stories, extra commits, scope drift.
- Updates release plan. Requires human approval.

---

## 7. Entry Points & Execution Flow

```python
# Programmatic usage
orchestrator = ADLCOrchestrator(release_id="REL-2026-Q3")

# Register executors for implemented agents
orchestrator.register_agent_executor("release-planning", my_planning_func)
orchestrator.register_agent_executor("story-generation", my_story_func)

# Start execution — get ready agents
ready = orchestrator.get_next_executable_agents()
# → [release-planning]

# Execute each ready agent
event = orchestrator.execute_agent("release-planning", {"brd_documents": [...]})
# → paused (human gate)

# Human approves
orchestrator.approve_and_resume(EventType.RELEASE_PLAN_APPROVED, approved_by="alice")
# → story-generation now executable
```

### Dependency chain (full pipeline in order)
```
release-planning → story-generation
story-generation → code-plan
code-plan        → feature-code-gen → code-review → mr-governance
                                                    → mr-test
                 → mr-req
code-review      → (PR approved) → change-discovery (FREEZE phase starts independently)
change-discovery → impact-graph → plan-reconciliation
impact-graph     → selective-regression → failure-triage → defect-analysis → defect-fix
defect-fix       → plan-refresh → pointed-sync-scope → evidence-pack → release-gate
release-gate     → pointed-sync-deploy → post-deploy-verify
```

---

## 8. Implementation Status Summary

| Phase | Total | Implemented | Partial | Not Implemented |
|---|---|---|---|---|
| PLAN | 2 | 2 | 0 | 0 |
| BUILD | 6 | 6 | 0 | 0 |
| FREEZE | 3 | 3 | 0 | 0 |
| TEST | 4 | 2 | 0 | 2 |
| RELEASE | 6 | 0 | 0 | 6 |
| **Total** | **21** | **13** | **0** | **8** |

The 8 unimplemented agents are: `selective-regression`, `failure-triage` (TEST phase), and all 6 RELEASE phase agents. The orchestrator supports `NOT_IMPLEMENTED` agents gracefully — it publishes placeholder events so the workflow can still advance in simulation mode.

---

## 9. Error Recovery & Retry Behavior

### 9.1 Agent execution failure

When `execute_agent(agent_id, input_artifacts)` raises an exception or the executor returns an error event:
1. The agent ID is added to `state.failed_agents`.
2. An `AGENT_EXECUTION_FAILED` event is published to the event bus with `data["error"]` containing the exception message.
3. `state.paused` is set to `True` and `state.pause_reason` is set to `"agent_failure:<agent_id>"`.
4. The orchestrator stops advancing the pipeline until a human explicitly calls `approve_and_resume` or `retry_agent`.

### 9.2 Retry policy

The orchestrator does **not** automatically retry failed agents. Retry is always a human-initiated action:
- `retry_agent(agent_id)`: clears the agent from `state.failed_agents`, resets `state.paused`, and re-queues the agent for execution by re-publishing the triggering event.
- Callers are responsible for fixing the underlying cause (e.g. missing config, unavailable service) before calling `retry_agent`.

### 9.3 Partial pipeline continuation

If an agent with no human gate fails, downstream agents that depend on it are blocked (their dependency is not in `state.completed_agents`). Agents on independent branches that share no dependency on the failed agent continue to execute normally.

Example: if `mr-test` fails but `mr-req` has no dependency on it, `mr-req` is still executable and will run.

### 9.4 Unimplemented agent handling

For agents with `status == NOT_IMPLEMENTED`:
- `execute_agent` publishes a synthetic placeholder event (e.g. `REGRESSION_COMPLETE` with an empty data payload).
- The agent ID is added to `state.completed_agents` as if it succeeded.
- A warning is logged but execution is not paused.
- This allows the pipeline to run end-to-end in simulation mode without blocking on unbuilt agents.

### 9.5 Human escalation

If any agent sets `HUMAN_ESCALATION_REQUIRED` on its output event:
- A `HUMAN_ESCALATION_REQUIRED` event is published in addition to the normal completion event.
- The workflow pauses with `pause_reason = "human_escalation:<agent_id>:<reason>"`.
- The human must review the escalation details in `state.artifacts["escalation_<agent_id>"]` and then call `approve_and_resume` to continue or `abort_workflow` to terminate.

### 9.6 Workflow state persistence

`WorkflowState` is serialized to `<storage_path>/<release_id>/workflow_state.json` after every event publication. On restart, `ADLCOrchestrator` can be re-constructed with the same `release_id` and `storage_path` and will reload the persisted state, allowing the pipeline to resume from the exact point of failure without re-running completed agents.
