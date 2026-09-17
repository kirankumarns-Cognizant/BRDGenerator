---
title: Agent 8 - Summarizer
model: claude-3-opus
complexity: HIGH
task_id: summarizer
description: Create executive summary and quick reference
---

# Agent 8: Summarizer

## Purpose
Create executive summary, highlights, and quick reference guide from comprehensive BRD.

## Input
- Agent 5 comprehensive BRD
- All previous agent outputs

## Process
1. Extract key findings
2. Identify highlights
3. Create summary
4. Build quick reference
5. Prioritize critical items

## Output
- executive_summary.md
- quick_reference.json
- highlights.md
- key_decisions.json
- confidence_score

## Model Configuration
- Model: claude-3-opus
- Temperature: 0.7
- Max Tokens: 2048

## Success Criteria
- Concise summary
- All key points covered
- Clear highlights
- Confidence > 0.8
