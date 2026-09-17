---
title: Agent 4 - Gap Analysis
model: claude-3-haiku
complexity: LOW
task_id: gap-analysis
description: Identify gaps between code and requirements
---

# Agent 4: Gap Analysis

## Purpose
Compare code implementation with requirements, identify missing features, inconsistencies, and ambiguities.

## Input
- Agent 1-3 outputs
- Requirements documentation
- Source code

## Process
1. Identify documented requirements
2. Compare with code implementation
3. Find undocumented features
4. Flag inconsistencies
5. Assess coverage

## Output
- gaps.json
- missing_requirements.md
- inconsistencies.json
- coverage_score
- confidence_score

## Model Configuration
- Model: claude-3-haiku
- Temperature: 0.5
- Max Tokens: 2048

## Success Criteria
- All gaps identified
- Clear recommendations
- Coverage score computed
- Confidence > 0.7
