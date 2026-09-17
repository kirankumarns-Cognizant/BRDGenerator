---
title: Agent 7 - Risk & Dependencies
model: claude-3-sonnet
complexity: MEDIUM
task_id: risk-dependency
description: Identify risks and document dependencies
---

# Agent 7: Risk & Dependencies

## Purpose
Assess technical risks, document critical dependencies, and provide mitigation strategies.

## Input
- Agent 1-5 outputs
- Architecture information
- Technology stack

## Process
1. Identify technical risks
2. Assess dependency impacts
3. Document critical paths
4. Create risk matrix
5. Define mitigations

## Output
- risks.json
- dependencies.md
- risk_matrix.json
- mitigation_strategies.md
- confidence_score

## Model Configuration
- Model: claude-3-sonnet
- Temperature: 0.6
- Max Tokens: 3072

## Success Criteria
- All risks identified
- Clear mitigations
- Dependencies mapped
- Confidence > 0.75
