# Agent 1 Discovery Skill

## Purpose
Execute Agent 1 discovery and scoping operations using PowerShell orchestration.

## Usage
```powershell
.\agent_1_discovery.ps1 -RepoPath "C:\path\to\repo" -ConfigPath "..\..\..\config\config.yaml"
```

## Parameters
- **RepoPath**: Path to the repository to analyze
- **ConfigPath**: Path to config.yaml (default: relative path to config)
- **OutputPath**: Path to write outputs (default: from config)

## What This Skill Does
1. Validates repository structure
2. Scans for artifacts (pom.xml, build.gradle, etc.)
3. Discovers documentation files
4. Maps dependencies
5. Generates scope definition
6. Writes outputs to kb_store

## Dependencies
- Python 3.10+
- GitPython
- Configured config.yaml

## Example
```powershell
# Run discovery on a local repo
.\agent_1_discovery.ps1 -RepoPath "C:\Projects\spring-petclinic"

# With custom config
.\agent_1_discovery.ps1 -RepoPath "C:\Projects\my-app" -ConfigPath ".\my-config.yaml"
```

## Outputs
- `scope_definition.json`
- `artifact_catalog.json`
- `dependency_map.json`

See `SKILL.md` for detailed documentation.
