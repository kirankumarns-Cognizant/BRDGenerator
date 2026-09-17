---
name: brd
description: Generate a comprehensive Business Requirements Document (BRD) for a source repository by dispatching 8 specialised subagents (discovery → summarisation) via the Agent tool. Writes 33 artifacts to a KB folder. Does NOT run the legacy Python pipeline.
---

# `/brd` — Multi-agent BRD generation

Usage:

```
/brd generate <ABSOLUTE_REPO_PATH> [<ABSOLUTE_KB_OUTPUT_PATH>]
```

If `KB_OUTPUT_PATH` is omitted, default to `<CWD>/KB/<basename of repo path>/`.

## What this skill does

This skill orchestrates a real multi-agent BRD generation by dispatching to 8 registered subagents via the Agent tool. Each subagent produces a subset of the 33 KB artifacts.

**Do NOT** invoke `run_all_agents.py`, `brd_orchestrator.py`, or any file under `kb_gen/`. The Python pipeline runs in signal-based fallback when no `ANTHROPIC_API_KEY` is set and produces low-quality placeholders.

## Execution protocol

Follow these steps **in order**. Do not skip.

### Step 1 — Parse args and validate
- Read `<REPO_PATH>`; assert it exists and contains source files (Java `pom.xml`, Python `pyproject.toml`, Node `package.json`, or similar).
- Compute `<KB>` = argument-2 or `<CWD>/KB/<basename>`. Create the directory if missing.
- Announce to the user: "Generating BRD for `<repo>` → `<KB>`. Will dispatch 8 subagents."

### Step 2 — Initialise TodoWrite
Create 8 todos, one per subagent (see stage table below). Mark stage 1 `in_progress`.

### Step 3 — Dispatch subagents sequentially
For each of the 8 stages, call the Agent tool with:

- `subagent_type` = the stage's subagent name (see table)
- `description` = 3-5 word summary
- `prompt` = a self-contained brief that:
  1. States the repo path and KB output path
  2. Names the exact artifact filenames the subagent must produce
  3. Instructs the subagent to Read/Grep the source itself — no placeholders, real content
  4. Passes forward any prior-stage artifact filenames the subagent should read for context

After each Agent call returns, mark that todo `completed` and the next `in_progress`.

### Stage table

| Stage | subagent_type | Artifacts to produce |
|---|---|---|
| 1 | `brd-discovery` | scope_definition.json, actors.json, artifact_catalog.json |
| 2 | `brd-dependencies` | dependency_map.json, dependency_register.json |
| 3 | `brd-journey-rules` | journey_map.json, journey_conflicts.json, business_rules.json, orphaned_rules.json, comprehensive_rules.md |
| 4 | `brd-gap-analysis` | gap_analysis.json, gap_register.json, rule_test_coverage.json, brd_gap_summary.json, brd_test_gap_analysis.json, test_journey_coverage.json |
| 5 | `brd-synthesis` | brd_final.json, synthesis_decisions.json, openapi_spec.json |
| 6 | `brd-acceptance` | acceptance_criteria.feature, acceptance_criteria_gherkin.json, new_test_suggestions.json |
| 7 | `brd-risk` | risk_register.json, regulatory_flags.json, regulatory_unresolved.json, regression_gap_report.json, test_gap_risk_register.json, prioritized_gap_closure_tests.json |
| 8 | `brd-summarizer` | COMPREHENSIVE_BRD_<repo>.md, brd_executive_summary.md, executive_summary.md, coverage_summary.json, COMPREHENSIVE_RULES_BRD.md, test_case_analysis.json |

### Step 4 — Validation
After stage 8, list `<KB>` and confirm all 33 artifacts exist. If any are missing, re-dispatch that stage's subagent with a shorter brief targeting only the missing files.

### Step 5 — Final report
Give the user a ≤ 6-line summary:
- Total artifacts written
- Rule coverage %, journey coverage %
- Top 3 critical items from `gap_analysis.json`
- Links to `COMPREHENSIVE_BRD_<repo>.md` and `brd_executive_summary.md`

## Cross-stage rules

- Every gap, risk, and rule MUST reference a real file path or class in the target repo.
- Cross-link IDs: RISK-XXX ↔ GAP-XXX ↔ DEC-XXX ↔ TESTGAP-XXX ↔ NEWTEST-XXX.
- Confidence scores in the range 0.85–0.95 based on evidence strength.
- Timestamps in ISO-8601 UTC.

## Anti-patterns (do not do these)

- Do NOT call `python`, `run_all_agents.py`, or `kb_gen/*`.
- Do NOT invent classes, methods, or endpoints. Every artifact claim must trace to a Read/Grep.
- Do NOT skip TodoWrite updates between stages.
- Do NOT batch-dispatch subagents in parallel — they have prior-stage dependencies. Sequential only.
