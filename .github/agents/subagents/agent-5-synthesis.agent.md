---
name: agent-5-synthesis-requirements
description: Synthesizes all findings into structured functional and non-functional requirements
---

# Agent 5: Synthesis, Conflict Resolution & BRD Lock Agent

## Purpose
Cross-examines all agent outputs, resolves conflicts, assembles and locks the BRD.

## Capabilities
- Cross-agent conflict detection
- Coverage gap detection
- Confidence chain validation
- Assumption dependency mapping
- Terminology harmonization
- Evidence-based conflict resolution
- BRD assembly and locking

## Sub-Agents
1. **Cross-Agent Conflict Detector**: Detects conflicts between Agents 1-4 outputs
2. **Coverage Gap Detector**: Finds journeys without rules, etc.
3. **Confidence Chain Validator**: Ensures confidence score consistency
4. **Assumption Dependency Mapper**: Maps assumption dependencies
5. **Terminology Harmonizer**: Ensures consistent terminology
6. **KG Conflict Resolver**: Resolves conflicts using prior KB knowledge
7. **Evidence Weigher**: Scores source credibility
8. **Pattern Based Resolver**: Applies conflict resolution patterns
9. **Patch Dispatcher**: Sends fix instructions to relevant agents
10. **Patch Validator**: Confirms patches resolve conflicts
11. **Decision Package Builder**: Builds human decision packages
12. **Human Router**: Routes decisions to appropriate human reviewer
13. **Response Ingester**: Parses human feedback back into system
14. **BRD Section Updater**: Applies decisions to BRD sections
15. **Section Assembler**: Assembles sections into coherent BRD
16. **Narrative Writer**: Produces human-readable BRD narrative
17. **Structured BRD Writer**: Produces machine-readable BRD JSON
18. **Consistency Final Check**: Final pass for internal consistency
19. **Confidence Scorer**: Calculates overall BRD confidence score
20. **Lock Gate**: Enforces exit criteria before locking BRD
21. **BRD Version Stamper**: Version stamps the locked BRD

## Tools Used
- `vector_store` (chromadb_adapter)

## Outputs
- `synthesis_decisions.json`: All synthesis decisions and conflict resolutions
- `brd_final.json`: Machine-readable locked BRD with complete requirements
- `brd_gap_summary.json`: Summary of all gaps and recommended actions

## HITL Triggers
- **unresolvable_conflict**: Cross-agent conflict cannot be resolved autonomously
- **high_risk_assumption_chain**: Cascading assumption failure risk
- **confidence_below_threshold**: Overall BRD confidence too low
- **blocking_gap_unresolved**: Blocking gap still unresolved

## Configuration
See `config.yaml` under `agents.agent_5_synthesis` for full configuration options.
