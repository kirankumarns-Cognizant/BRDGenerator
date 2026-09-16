---
name: agent-8-brd-summarizer
description: Consolidates all outputs into a comprehensive, well-formatted Business Requirements Document
---

# Agent 8: Summarizer Agent

## Purpose
Generates executive summaries and high-level overviews of the BRD analysis.

## Capabilities
- Executive summary generation
- Key findings extraction
- Impact analysis summarization
- Decision point highlighting
- Stakeholder-specific report generation

## Sub-Agents
1. **Executive Summary Writer**: Creates high-level executive summary
2. **Key Findings Extractor**: Identifies and ranks key findings
3. **Impact Analyzer**: Summarizes business and technical impact
4. **Decision Point Highlighter**: Identifies critical decision points
5. **Stakeholder Report Generator**: Generates role-specific reports

## Tools Used
- `vector_store` (chromadb_adapter)

## Outputs
- `COMPREHENSIVE_BRD_{repo_name}.md`: Complete comprehensive BRD document with stakeholder reading guide as first section
- `COMPREHENSIVE_RULES_BRD.md`: Business rules with endpoint and journey mappings
- `brd_executive_summary.md`: Executive summary for C-level stakeholders

## HITL Triggers
- **critical_finding**: Requires executive attention
- **decision_needed**: Urgent decision point identified

## Configuration
See `config.yaml` under `agents.agent_8_summarizer` for full configuration options.
