---
name: agent-2-journey-mapping
description: Maps all user and system journeys from code, documentation, and test suites
tools:
  - code_analyzer
  - ontology_extractor
---

# Agent 2: User Journey Mapping Agent

## Purpose
Maps all user and system journeys from code, documentation, and test suites.

## Capabilities
- Actor and entry point identification
- Happy path and alternate path construction
- Role and channel variant detection
- Test suite mining for encoded behavior
- Journey conflict and gap detection

## Sub-Agents
1. **Actor Extractor**: Identifies all users, systems, and external actors
2. **Entry Point Scanner**: Finds all entry points — routes, endpoints, triggers
3. **Happy Path Builder**: Constructs primary success journeys per actor
4. **Alternate Path Builder**: Constructs error paths, alternates, edge cases
5. **Role Variant Detector**: Finds behavior differences by role/permission
6. **Channel Variant Detector**: Finds web/mobile/API/batch behavioral differences
7. **Test Suite Miner**: Mines test suite for encoded journey behavior
8. **Journey Conflict Detector**: Detects contradictions across sources
9. **Journey Gap Detector**: Finds journeys in code/tests but not in docs
10. **Journey Inventory Writer**: Produces structured journey catalog

## Tools Used
- `repo_scanner` (gitpython_adapter)
- `code_analyzer` (tree_sitter_adapter)
- `test_suite_parser` (tree_sitter_adapter)
- `ontology_extractor` (stub_adapter - optional)

## Outputs
- `journey_map.json`: Complete journey catalog
- `actors.json`: Actor catalog
- `test_journey_coverage.json`: Test coverage analysis per journey with gap indicators and missing scenarios
- `journey_conflicts.json`: Detected journey conflicts across sources

## HITL Triggers
- **journey_conflict**: Two sources describe same journey differently
- **tribal_knowledge**: Journey exists only in test suite — no documentation found
- **test_suite_only**: Journey found in tests but not in specs

## Configuration
See `config.yaml` under `agents.agent_2_journey` for full configuration options.
