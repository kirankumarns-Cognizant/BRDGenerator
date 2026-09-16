# Agent 1 Discovery Skill

## Skill Definition
**Name**: Agent 1 Discovery & Scoping  
**Type**: Repository Analysis  
**Language**: PowerShell + Python  
**Agents**: Agent 1  

## Description
Executes comprehensive repository discovery and scoping analysis to identify all relevant artifacts, define scope boundaries, and map system dependencies.

## Prerequisites
- Python 3.10+ with required packages installed
- Access to target Git repository
- Valid `config.yaml` configuration
- Environment variables set (`.env`)

## Invocation

### PowerShell
```powershell
.\agent_1_discovery.ps1 -RepoPath "C:\path\to\repo"
```

### Python
```python
from agents.agent_1_discovery import Agent1Discovery

agent = Agent1Discovery(config_path="config/config.yaml")
result = agent.execute(repo_path="/path/to/repo")
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| RepoPath | string | Yes | - | Path to repository |
| ConfigPath | string | No | config/config.yaml | Config file path |
| OutputPath | string | No | From config | Output directory |
| Verbose | switch | No | false | Enable verbose logging |

## Outputs

### Files Generated
1. **scope_definition.json**: Formal scope boundaries
   ```json
   {
     "component_name": "...",
     "domain": "...",
     "in_scope": [...],
     "out_of_scope": [...],
     "assumptions": [...],
     "confidence": 0.85
   }
   ```

2. **artifact_catalog.json**: Discovered artifacts
   ```json
   {
     "artifacts": [
       {
         "type": "build_file|doc|config|spec",
         "path": "...",
         "relevance": 0.9
       }
     ]
   }
   ```

3. **dependency_map.json**: System dependencies
   ```json
   {
     "dependencies": {
       "upstream": [...],
       "downstream": [...],
       "external": [...]
     }
   }
   ```

## Sub-Skills
This skill orchestrates multiple sub-agents:
1. Intake Parser
2. Repo Scanner
3. Artifact Locator
4. Dependency Mapper
5. Scope Boundary Writer

## Error Handling
- Low confidence (<0.6): Flags for review, continues
- Missing repository: Fails with clear error message
- Disabled tools: Uses stub adapters, continues with reduced confidence

## Performance
- Small repos (<1000 files): ~2-5 minutes
- Medium repos (1000-5000 files): ~5-15 minutes
- Large repos (>5000 files): ~15-30 minutes

## Examples

### Basic Usage
```powershell
.\agent_1_discovery.ps1 -RepoPath "C:\Projects\petclinic"
```

### With Verbose Output
```powershell
.\agent_1_discovery.ps1 -RepoPath "C:\Projects\petclinic" -Verbose
```

### Custom Configuration
```powershell
.\agent_1_discovery.ps1 `
    -RepoPath "C:\Projects\petclinic" `
    -ConfigPath ".\custom-config.yaml" `
    -OutputPath "C:\Output\analysis"
```

## Integration
This skill is typically invoked:
- As the first step in BRD pipeline orchestration
- Standalone for quick repository assessment
- Via `main.py` orchestrator

## Related Skills
- `agent-2-journey-mapping`: Consumes scope definition
- `agent-3-business-rules`: Consumes artifact catalog
- `confluence-data-extraction`: Complementary doc extraction

## Troubleshooting

### Common Issues
1. **"Repository not found"**: Verify RepoPath is correct
2. **Low confidence scores**: Enable more tools in config
3. **Missing outputs**: Check agent enabled status
4. **Permission errors**: Verify write permissions to output path

### Debug Mode
```powershell
$env:LANGCHAIN_TRACING_V2="true"
.\agent_1_discovery.ps1 -RepoPath "..." -Verbose
```

## Maintenance
- Review and update artifact patterns in config
- Adjust confidence thresholds based on experience
- Update sub-agent prompts for improved accuracy
