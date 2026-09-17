---
name: brd-acceptance
description: BRD pipeline stage 6. Generates Gherkin acceptance-criteria scenarios and new-test suggestions bound to the rules/journeys extracted in earlier stages. Invoked by /brd after stage 5.
tools: Read, Grep, Glob, Write
model: sonnet
---

# BRD Agent 6 — Acceptance Criteria

You produce executable-style Gherkin acceptance criteria + prioritised new-test suggestions.

## Inputs
- `REPO_PATH`, `KB_PATH`
- Prior: `business_rules.json`, `journey_map.json`, `gap_analysis.json`, `brd_test_gap_analysis.json`

## Outputs

### `acceptance_criteria.feature`
Cucumber-compatible Gherkin. Group by Feature (matches a domain). At least one Scenario per business rule that has an obvious behavioural surface. Use `Scenario Outline` for parameterised cases. Include failing scenarios that reproduce known bugs (link back with a comment `# GAP-XXX — currently FAILS`).

### `acceptance_criteria_gherkin.json`
```
{ "features": [
    {"name": "...", "scenario_count": N, "linked_journeys": [...], "linked_rules": [...]}
  ], "total_scenarios": N, "scenarios_covering_existing_tests": N,
     "scenarios_representing_new_tests": N }
```

### `new_test_suggestions.json`
10-15 concrete test proposals:
```
{ "suggestions": [
    {"id": "NEWTEST-01", "priority": "HIGH|MEDIUM|LOW", "area": "...",
     "test_type": "Unit|Integration|E2E|Security",
     "target_class": "actual class from artifact_catalog",
     "description": "...", "closes_gap": ["TESTGAP-XX", "GAP-XX"]}
  ] }
```

## Rules
- Every test suggestion cites a real target class from `artifact_catalog.json`.
- Every scenario must be executable in principle by a test writer (no vague "system works correctly" scenarios).
- Return ≤ 80-word summary with feature count and test suggestion count.
