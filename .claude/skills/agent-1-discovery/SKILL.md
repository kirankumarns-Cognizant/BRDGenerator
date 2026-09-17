---
name: Repository Discovery
agent: 1
model: claude-3-opus
skill_id: repo-discovery
description: Scan and analyze Java repositories for artifacts, dependencies, and project structure
---

# Repository Discovery Skill

## Overview
Scans Java repositories to identify project structure, dependencies, configuration files, and key artifacts.

## Capabilities
- Directory tree analysis
- Java file identification
- Dependency detection (Maven, Gradle, etc.)
- Configuration file parsing
- Framework detection
- Module identification

## When to Use
- Initial repository analysis
- Project structure understanding
- Dependency mapping
- Artifact cataloging

## Inputs
- Repository path
- Configuration filter

## Outputs
- artifact_catalog.md
- dependency_map.json
- scope_definition.json

## Usage
```
"Scan the repository in KB/spring-petclinic and create an artifact catalog"
```

## Success Metrics
- All files identified
- Dependencies mapped
- Confidence > 0.8
