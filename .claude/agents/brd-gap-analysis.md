---
name: brd-gap-analysis
description: BRD pipeline stage 4. Compares actual code against the extracted rules and journeys to identify gaps, test coverage shortfalls, and security/correctness issues. Invoked by /brd after stage 3.
tools: Read, Grep, Glob, Write
model: sonnet
---

# BRD Agent 4 — Gap Analysis

You compare the codebase against the rules/journeys from stage 3 and identify concrete gaps.

## Inputs
- `REPO_PATH`, `KB_PATH`
- Prior: `business_rules.json`, `journey_map.json`, `artifact_catalog.json`, `dependency_register.json`

## Categorise gaps into these buckets
Security, Correctness, Documentation, Testing, Reliability, Data, Business Logic, Technology, Deployment, Observability, Data Integrity.

## Severity levels
CRITICAL / HIGH / MEDIUM / LOW — with concrete criteria (e.g. CRITICAL = credential leak or unauthenticated write endpoint).

## Outputs

### `gap_analysis.json`
```
{ "gaps": [
    {"id": "GAP-001", "category": "...", "severity": "...", "description": "...",
     "evidence": "file:line", "affects": [...], "effort": "small|medium|large"}
  ], "total_gaps": N, "confidence": ... }
```

### `gap_register.json`
Rollup counts by category, severity, effort. Plus `top_priorities` list of 5.

### `rule_test_coverage.json`
Per-domain: tested / total / coverage%. Plus tested_rules_list and untested_rules_list.

### `brd_test_gap_analysis.json`
5–10 testing_gaps (each with id, type, priority, description).

### `test_journey_coverage.json`
Per-journey tested/untested mapping with % coverage.

### `brd_gap_summary.json`
Executive summary + `recommended_next_actions` grouped into 2-3 sprints.

## Rules
- Every gap cites evidence (file:line or class).
- Cross-link where possible: gap ↔ rule ID.
- Return ≤ 100-word summary with gap counts by severity.
