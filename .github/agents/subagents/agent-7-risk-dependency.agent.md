---
name: agent-7-risk-dependency
description: Identifies technical and business risks, maps dependencies between requirements and systems
tools:
  - code_analyzer
---

# Agent 7: Risk & Dependency Agent

## Purpose
Identifies risks, dependencies, and constraints that could impact migration success.

## Capabilities
- Technical debt detection
- Architecture risk identification
- Data migration risk analysis
- Integration dependency mapping
- Timeline and resource constraint analysis
- Mitigation strategy recommendation

## Sub-Agents
1. **Technical Debt Detector**: Identifies code quality and architecture issues
2. **Architecture Risk Analyzer**: Evaluates architectural risks
3. **Data Migration Risk Analyzer**: Assesses data migration challenges
4. **Integration Dependency Mapper**: Maps external system dependencies
5. **Constraint Analyzer**: Identifies timeline and resource constraints
6. **Mitigation Strategy Generator**: Recommends risk mitigation strategies
7. **Risk Register Writer**: Produces structured risk register

## Tools Used
- `code_analyzer` (tree_sitter_adapter)
- `repo_scanner` (gitpython_adapter)

## Outputs
- `risk_register.json`: Complete risk catalog with severity and mitigation
- `dependency_register.json`: System and requirement dependency mapping
- `regulatory_unresolved.json`: Unresolved regulatory compliance risks
- `test_gap_risk_register.json`: Risks specifically related to test coverage gaps

## HITL Triggers
- **critical_risk**: High-severity risk requiring escalation
- **unknown_dependency**: External dependency with unclear migration path

## Configuration
See `config.yaml` under `agents.agent_7_risk` for full configuration options.
