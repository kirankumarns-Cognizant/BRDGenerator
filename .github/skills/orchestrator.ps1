# Orchestrator Skill

## Skill Definition
**Name**: BRD Pipeline Orchestrator  
**Type**: Orchestration  
**Language**: PowerShell  

## Description
Orchestrates the complete BRD generation pipeline, executing all agents in the correct sequence.

## Invocation
```powershell
.\orchestrator.ps1 -RepoPath "C:\path\to\repo" -ConfigPath "..\config\config.yaml"
```

## Parameters
| Parameter | Required | Description |
|-----------|----------|-------------|
| RepoPath | Yes | Path to repository to analyze |
| ConfigPath | No | Path to config.yaml |
| EnabledAgents | No | Comma-separated list of agents to run |
| SkipAgents | No | Comma-separated list of agents to skip |

## Execution Flow
1. Validate configuration and environment
2. Execute Agent 1 (Discovery)
3. Execute Agents 2 & 3 in parallel (Journey, Rules)
4. Execute Agent 4 (Gap Analysis)
5. Execute Agent 5 (Synthesis)
6. Execute Agents 6 & 7 in parallel (AC, Risk)
7. Execute Agent 8 (Summarizer)
8. Execute Agent 9 (KB Sync)

## Examples
```powershell
# Full pipeline
.\orchestrator.ps1 -RepoPath "C:\Projects\petclinic"

# Only Agent 1
.\orchestrator.ps1 -RepoPath "C:\Projects\petclinic" -EnabledAgents "agent_1"

# Skip Agent 8
.\orchestrator.ps1 -RepoPath "C:\Projects\petclinic" -SkipAgents "agent_8"
```

## Integration
This is the main entry point for BRD pipeline execution via PowerShell.
