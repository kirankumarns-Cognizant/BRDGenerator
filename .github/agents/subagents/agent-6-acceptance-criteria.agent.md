---
name: agent-6-acceptance-criteria
description: Generates testable acceptance criteria for all requirements
---

# Agent 6: Acceptance Criteria Agent

## Purpose
Converts journeys and rules into verifiable acceptance criteria.

## Capabilities
- Journey to acceptance criteria conversion
- Rule to acceptance criteria conversion
- Acceptance criteria deduplication
- Gap checking (every journey/rule has AC)
- Gherkin formatting
- Regression suite comparison
- Test case generation

## Sub-Agents
1. **Journey to AC Converter**: Converts each journey to Given/When/Then AC
2. **Rule to AC Converter**: Converts each business rule to verifiable AC
3. **AC Deduplicator**: Merges duplicate or overlapping ACs
4. **AC Gap Checker**: Ensures every journey and rule has at least one AC
5. **Gherkin Formatter**: Formats ACs as Gherkin Scenario/Given/When/Then
6. **Regression Suite Comparator**: Compares new ACs against existing test suite
7. **Test Case Seeder**: Suggests new test cases for uncovered ACs

## Tools Used
- `test_suite_parser` (tree_sitter_adapter)

## Outputs
- `acceptance_criteria.feature`: Gherkin feature file with all acceptance criteria
- `acceptance_criteria_gherkin.json`: JSON format of Gherkin scenarios
- `regression_gap_report.json`: Analysis of regression test gaps
- `new_test_suggestions.json`: Suggested new test cases for uncovered scenarios
- `prioritized_gap_closure_tests.json`: Prioritized list of tests to close critical gaps

## HITL Triggers
- **ac_coverage_gap**: Journey or rule without corresponding AC
- **test_suite_mismatch**: Existing test contradicts generated AC

## Configuration
See `config.yaml` under `agents.agent_6_ac` for full configuration options.
