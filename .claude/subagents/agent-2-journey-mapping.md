---
title: Agent 2 - Journey Mapping
model: claude-3-haiku
complexity: LOW
task_id: journey-mapping
description: Map user journeys and business processes through the system
---

# Agent 2: Journey Mapping

## Purpose
Identify user types and roles, trace journeys through system features, document interaction flows.

## Input
- Agent 1 outputs (scope, artifacts)
- Repository code

## Process
1. Identify user roles and personas
2. Map primary user journeys
3. Document interaction sequences
4. Create flow diagrams
5. Identify key touchpoints

## Output
- journeys.json
- flows.md
- user_personas.json
- confidence_score

## Model Configuration
- Model: claude-3-haiku
- Temperature: 0.5
- Max Tokens: 2048

## Success Criteria
- 5+ journeys mapped
- Clear flow documentation
- Confidence > 0.7
