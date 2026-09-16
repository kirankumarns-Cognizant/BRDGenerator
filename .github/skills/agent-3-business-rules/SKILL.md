# Agent 3 Business Rules Extraction Skill

## Skill Definition
**Name**: Agent 3 Business Rules Extraction  
**Type**: Code Analysis  
**Language**: PowerShell + Python  
**Agents**: Agent 3  

## Description
Extracts business rules, validation logic, decision rules, and constraints from source code using static analysis and pattern matching.

## Prerequisites
- Python 3.10+ with Semgrep installed
- Agent 1 (Discovery) outputs available
- Agent 2 (Journey Mapping) outputs available
- Valid `config.yaml` configuration

## Invocation

### PowerShell
```powershell
.\agent_3_business_rules.ps1 -RepoPath "C:\path\to\repo"
```

### With Options
```powershell
.\agent_3_business_rules.ps1 `
    -RepoPath "C:\repos\spring-petclinic" `
    -ConfigPath "..\..\..\config\config.yaml" `
    -OutputPath "C:\output" `
    -Verbose
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| RepoPath | string | Yes | - | Path to repository |
| ConfigPath | string | No | config/config.yaml | Config file path |
| OutputPath | string | No | KB/{repo_name}/ | Output directory |
| Verbose | switch | No | false | Enable verbose logging |

## Dependencies
- **Agent 1**: Requires `scope_definition.json`, `artifact_catalog.json`
- **Agent 2**: Requires `user_journeys.json`, `touchpoints.json`

## Outputs

### Files Generated
1. **business_rules.json**: Extracted business rules
   ```json
   {
     "rules": [
       {
         "id": "BR001",
         "category": "validation|calculation|workflow|authorization",
         "description": "Pet age must be positive integer",
         "source_location": "src/main/java/Pet.java:45",
         "severity": "critical|high|medium|low",
         "confidence": 0.92
       }
     ],
     "total_rules": 47,
     "confidence": 0.85
   }
   ```

2. **validation_logic.json**: Validation patterns
   ```json
   {
     "validations": [
       {
         "field": "email",
         "type": "format|range|required|custom",
         "rule": "Email format validation",
         "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
         "location": "Validator.java:23"
       }
     ]
   }
   ```

## Sub-Skills
This skill orchestrates:
1. **Validation Extractor**: Finds validation patterns
2. **Constraint Analyzer**: Identifies business constraints
3. **Decision Rule Mapper**: Maps decision logic
4. **Workflow Rule Extractor**: Extracts workflow rules
5. **Authorization Rule Analyzer**: Analyzes access control

## Tools Used
- `code_analyzer` (semgrep_adapter) - Pattern-based code analysis
- `tree_sitter` - AST parsing for complex logic
- Regex patterns for validation extraction

## Extraction Patterns

### Validation Rules
- Annotation-based (`@NotNull`, `@Size`, `@Pattern`)
- Method-level validation (`if (age < 0) throw...`)
- Framework validators (Spring, Hibernate Validator)

### Business Constraints
- Database constraints (`@Column(nullable=false)`)
- Enum restrictions
- State machine transitions

### Decision Rules
- If-else logic trees
- Switch statements with business meaning
- Strategy pattern implementations

## Error Handling
- Low confidence (<0.6): Flags for HITL review
- Ambiguous rules: Marked for human clarification
- Missing dependencies: Fails with clear error message

## Performance
- Small repos: ~3-7 minutes
- Medium repos: ~7-20 minutes
- Large repos: ~20-40 minutes

## Examples

### Example 1: Spring Boot Application
```powershell
.\agent_3_business_rules.ps1 -RepoPath "C:\repos\spring-petclinic" -Verbose
```
**Output**: 47 business rules, 23 validation patterns

### Example 2: Microservice
```powershell
.\agent_3_business_rules.ps1 -RepoPath "C:\repos\order-service"
```
**Output**: 18 business rules focused on order processing

## HITL Triggers
- `ambiguous_rule`: Business logic requires interpretation
- `low_confidence_rule`: Rule extraction confidence below 0.6
- `conflicting_constraints`: Multiple contradictory rules found

## Integration
Agent 3 outputs feed into:
- **Agent 4**: Gap analysis (compares rules against journeys)
- **Agent 5**: Requirements synthesis (converts rules to requirements)
- **Agent 6**: Acceptance criteria (derives test cases from rules)

## Configuration
See `config.yaml` under `agents.agent3`:
```yaml
agents:
  agent3:
    name: "Business Rules Extraction Agent"
    tools:
      - code_analyzer
    enabled_tools:
      code_analyzer: true
    output_files:
      - business_rules.json
      - validation_logic.json
```

## Troubleshooting

### Issue: No rules extracted
**Cause**: Repository language not supported by Semgrep  
**Solution**: Check `tools/adapters/semgrep_adapter.py` for language support

### Issue: Low confidence scores
**Cause**: Complex or obfuscated business logic  
**Solution**: Review flagged rules manually, add custom patterns

### Issue: Missing dependencies
**Cause**: Agent 1 or 2 not run yet  
**Solution**: Execute `.\orchestrator.ps1` to run full pipeline

## See Also
- `.github/agents/subagents/agent-3-business-rules.agent.md` - Full agent specification
- `tools/adapters/semgrep_adapter.py` - Code analyzer implementation
- `config/config.yaml` - Agent configuration
