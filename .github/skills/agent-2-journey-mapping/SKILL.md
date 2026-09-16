# Agent 2 Journey Mapping Skill

## Skill Definition
**Name**: Agent 2 Journey Mapping  
**Type**: Journey Analysis  
**Language**: PowerShell + Python  
**Agents**: Agent 2  

## Description
Maps all user and system journeys from code, documentation, and test suites.

## Invocation
```powershell
.\agent_2_journey_mapping.ps1 -RepoPath "C:\path\to\repo"
```

## Outputs
- `journey_map.json`
- `test_journey_coverage.json`
- `journey_conflicts.json`
- `actors.json`

See `.github/agents/subagents/agent-2-journey-mapping.agent.md` for detailed documentation.
