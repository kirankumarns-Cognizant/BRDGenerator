---
title: Agent 3 - Business Rules Extraction
model: claude-3-haiku
complexity: LOW
task_id: business-rules
description: Extract and document business rules from code
---

# Agent 3: Business Rules Extraction

## Purpose
Identify business logic, validation rules, constraints, and business domain rules from codebase.

## Input
- Agent 1 outputs
- Source code
- Optional: Business documentation

## Process
1. Analyze code for business logic
2. Extract validation rules
3. Identify constraints
4. Map rules to code locations
5. Categorize by domain

## Output
- business_rules.json
- constraints.md
- rules_mapping.json
- confidence_score

## Model Configuration
- Model: claude-3-haiku
- Temperature: 0.5
- Max Tokens: 2048

## Success Criteria
- 30+ rules extracted
- Clear categorization
- Code references provided
- Confidence > 0.7
