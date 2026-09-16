---
name: agent-1-discovery-scoping
description: Scans repository, locates artifacts, defines scope boundaries for BRD generation
tools:
  - repo_scanner
  - doc_parser
  - jira_loader
  - confluence_loader
---

# Agent 1: Discovery & Scoping Agent

## Purpose
Scans repository, locates artifacts, defines scope boundaries for BRD generation.

## Capabilities
- Repository scanning and file tree analysis
- Artifact location (specs, docs, config files)
- Dependency mapping (upstream/downstream systems)
- Scope boundary definition
- Document parsing from various sources

## Sub-Agents
1. **Intake Parser**: Extracts component name, domain, priority from run config
2. **Repo Scanner**: Scans repo file tree and structure
3. **Artifact Locator**: Finds specs, docs, config files related to component
4. **Dependency Mapper**: Maps upstream/downstream system connections
5. **Scope Boundary Writer**: Produces formal scope definition

## Tools Used
- `repo_scanner` (gitpython_adapter)
- `doc_parser` (unstructured_adapter)
- `jira_loader` (stub_adapter - optional)
- `confluence_loader` (stub_adapter - optional)
- `ontology_extractor` (stub_adapter - optional)

## Outputs
- `scope_definition.json`: Formal scope boundaries
- `artifact_catalog.json`: Catalog of all discovered artifacts
- `dependency_map.json`: System dependency mapping
- `test_case_analysis.json`: Comprehensive test case analysis combining inventory, presence, traceability, and detailed metadata in one file

## HITL Triggers
- **ambiguous_scope**: Scope boundary cannot be determined from available artifacts
- **low_confidence_artifact**: Artifact found but confidence score below threshold

## Configuration
See `config.yaml` under `agents.agent_1_discovery` for full configuration options.
