---
title: Agent 1 - Discovery & Scoping
model: claude-3-opus
complexity: HIGH
task_id: discovery-scoping
description: Scan repository, catalog artifacts, and define project scope
---

# Agent 1: Discovery & Scoping

## Purpose
Analyze Java repository structure, identify modules, dependencies, and project artifacts to create comprehensive scope definition.

## Input
- Repository path
- Configuration file
- Optional: Supporting documents

## Process
1. Scan repository directory tree
2. Identify all Java files and dependencies
3. Extract project configuration (Maven/Gradle)
4. Catalog key artifacts and frameworks
5. Create dependency map

## Output
- scope_definition.json
- artifact_catalog.md
- dependency_map.json
- confidence_score (0.0-1.0)

## Model Configuration
- Model: claude-3-opus
- Temperature: 0.7
- Max Tokens: 4096

## Success Criteria
- All files cataloged
- Dependencies mapped
- Confidence > 0.8
