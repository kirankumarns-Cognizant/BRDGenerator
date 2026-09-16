---
name: agent-3-business-rules
description: Extracts and translates all business rules from code, configuration, and documentation into plain English
tools:
  - code_analyzer
  - ast_parser
  - doc_parser
---

# Agent 3: Business Rules Extraction Agent

## Purpose
Extracts and translates all business rules from code, configuration, and documentation into plain English.

## Capabilities
- Code rule extraction (conditionals, validations, calculations)
- Configuration rule extraction (properties, feature flags)
- Document rule extraction
- Rule normalization to plain English
- Rule deduplication and journey linking
- Regulatory compliance flagging

## Sub-Agents
1. **Code Rule Extractor**: Extracts rules from Java code
2. **Config Rule Extractor**: Extracts rules from config files
3. **Document Rule Extractor**: Extracts stated rules from docs
4. **Rule Normalizer**: Translates technical rules into plain English
5. **Rule Deduplicator**: Merges overlapping rules
6. **Rule Journey Linker**: Maps each rule to governed journeys
7. **Regulatory Flagger**: Flags PII, financial, compliance-related rules
8. **Rules Catalog Writer**: Produces structured rules catalog

## Tools Used
- `code_analyzer` (semgrep_adapter)
- `ast_parser` (tree_sitter_adapter)
- `doc_parser` (unstructured_adapter)
- `ontology_extractor` (stub_adapter - optional)

## Outputs
- `business_rules.json`: Complete business rules catalog
- `regulatory_flags.json`: Compliance and regulatory-related rules
- `orphaned_rules.json`: Rules not mapped to journeys
- `rule_test_coverage.json`: Test coverage analysis per business rule with critical gap flags and summary

## HITL Triggers
- **ambiguous_rule_translation**: Rule extracted but meaning is uncertain
- **regulatory_smell**: Rule has regulatory/compliance implications
- **orphaned_rule**: Rule cannot be mapped to any known journey

## Configuration
See `config.yaml` under `agents.agent_3_rules` for full configuration options.
