---
name: agent-4-gap-analysis
description: Identifies gaps between current implementation and expected functionality
tools:
  - vector_store
---

# Agent 4: Gap Analysis Agent

## Purpose
Compares Legacy behavior against NSA capabilities, classifies every gap.

## Capabilities
- NSA specification parsing
- Journey to NSA mapping
- Data field mapping
- Rule compatibility checking
- Gap classification (CLEAN_MAP / TRANSFORM / MISSING / DEFERRED)
- Risk scoring

## Sub-Agents
1. **NSA Spec Parser**: Parses NSA API contracts and capability registry
2. **Journey to NSA Mapper**: Maps each Legacy journey to NSA equivalent
3. **Data Field Mapper**: Maps Legacy data fields to NSA schema
4. **Rule Compatibility Checker**: Checks NSA native rule enforcement
5. **Gap Classifier**: Classifies gaps by type
6. **Risk Scorer**: Scores gaps by likelihood × business impact
7. **Gap Register Writer**: Produces structured gap register

## Tools Used
- `nsa_spec_parser` (stub_adapter - optional)
- `code_analyzer` (tree_sitter_adapter)

## Outputs
- `gap_analysis.json`: Complete gap analysis including blocking gaps flagged by severity
- `brd_test_gap_analysis.json`: BRD requirements vs test coverage gaps
- `gap_register.json`: Structured gap register with remediation tracking
- `coverage_summary.json`: Overall test coverage summary with detailed gap breakdown

## HITL Triggers
- **uncertain_gap_classification**: Cannot determine if gap is TRANSFORM or MISSING
- **blocking_gap**: Gap will prevent migration without resolution

## Configuration
See `config.yaml` under `agents.agent_4_gap` for full configuration options.
