# Agent 5 Synthesis & Requirements Skill

## Skill Definition
**Name**: Agent 5 Synthesis & Requirements  
**Type**: Requirements Generation  
**Language**: PowerShell + Python  
**Agents**: Agent 5  

## Description
Synthesizes all upstream analysis into structured functional and non-functional requirements, resolving conflicts and prioritizing based on business value.

## Prerequisites
- Python 3.10+
- Outputs from Agents 1-4 available in KB/{repo_name}/
- Valid `config.yaml` configuration

## Invocation

### PowerShell
```powershell
.\agent_5_synthesis.ps1 -RepoPath "C:\path\to\repo"
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| RepoPath | string | Yes | - | Path to repository |
| ConfigPath | string | No | config/config.yaml | Config file path |
| OutputPath | string | No | KB/{repo_name}/ | Output directory |
| Verbose | switch | No | false | Enable verbose logging |

## Dependencies
- **Agent 1**: Scope definition
- **Agent 2**: User journeys
- **Agent 3**: Business rules
- **Agent 4**: Gap analysis

## Outputs

### Files Generated
1. **functional_requirements.json**
   ```json
   {
     "requirements": [
       {
         "id": "FR001",
         "category": "user_interface|data_processing|integration|reporting",
         "title": "Email validation on registration",
         "description": "System shall validate email format during user registration",
         "priority": "must_have|should_have|could_have|wont_have",
         "source": ["business_rules.BR023", "gap_analysis.GAP001"],
         "acceptance_criteria_ids": ["AC001", "AC002"],
         "complexity": "low|medium|high",
         "confidence": 0.92
       }
     ],
     "total_requirements": 45,
     "must_have": 20,
     "should_have": 15,
     "could_have": 10
   }
   ```

2. **non_functional_requirements.json**
   ```json
   {
     "requirements": [
       {
         "id": "NFR001",
         "category": "performance|security|scalability|usability|maintainability",
         "title": "Response time under 2 seconds",
         "description": "90% of API requests shall respond within 2 seconds",
         "measurable_criterion": "Response time <= 2000ms for p90",
         "priority": "must_have",
         "source": ["journey_touchpoint.TP015"],
         "confidence": 0.85
       }
     ]
   }
   ```

## Sub-Skills
1. **Requirement Consolidator**: Merges similar requirements
2. **Conflict Resolver**: Resolves contradictory requirements
3. **Priority Ranker**: Assigns MoSCoW priorities
4. **NFR Deriver**: Extracts non-functional requirements from journeys
5. **Traceability Mapper**: Links requirements to sources

## Tools Used
- LLM-based synthesis (GPT-4/Claude)
- Similarity matching for deduplication
- Priority ranking algorithms

## Synthesis Process

### 1. Consolidation
- Merge duplicate or overlapping requirements
- Group related requirements
- Remove redundancies

### 2. Conflict Resolution
- Identify contradictory requirements
- Apply business priority rules
- Flag unresolvable conflicts for HITL

### 3. Prioritization (MoSCoW)
- **Must Have**: Critical for MVP/release
- **Should Have**: Important but not critical
- **Could Have**: Desirable if resources allow
- **Won't Have**: Out of scope for this release

### 4. NFR Derivation
- Performance: From journey response time expectations
- Security: From authentication/authorization rules
- Scalability: From expected load patterns
- Usability: From UI/UX touchpoints
- Maintainability: From code quality analysis

## Error Handling
- Conflicting requirements: Flags for HITL review
- Low confidence (<0.6): Marked for human verification
- Missing source traceability: Warning logged

## Performance
- Small repos: ~5-10 minutes
- Medium repos: ~10-20 minutes
- Large repos: ~20-35 minutes

## Examples

### Example 1: Spring Boot App
```powershell
.\agent_5_synthesis.ps1 -RepoPath "C:\repos\spring-petclinic" -Verbose
```
**Output**: 45 FRs (20 must-have), 12 NFRs

### Example 2: Microservice
```powershell
.\agent_5_synthesis.ps1 -RepoPath "C:\repos\payment-service"
```
**Output**: 28 FRs, 15 NFRs (heavy on security/performance)

## HITL Triggers
- `conflicting_requirements`: Unresolvable contradictions
- `low_confidence_requirement`: Requirement confidence < 0.6
- `ambiguous_priority`: Cannot determine MoSCoW priority
- `missing_source`: Requirement without clear source

## Integration
Agent 5 outputs feed into:
- **Agent 6**: Acceptance criteria generation
- **Agent 7**: Risk assessment (based on complexity/dependencies)
- **Agent 8**: Final BRD synthesis

## Configuration
```yaml
agents:
  agent5:
    name: "Synthesis & Requirements Agent"
    tools: []
    output_files:
      - functional_requirements.json
      - non_functional_requirements.json
```

## Requirement Template

### Functional Requirement
```
ID: FR{number}
Title: {brief descriptive title}
Category: {user_interface|data_processing|integration|reporting}
Description: System shall {action} {object} {condition}
Priority: {must_have|should_have|could_have|wont_have}
Source: {upstream artifact references}
Acceptance Criteria: {list of AC IDs}
Complexity: {low|medium|high}
```

### Non-Functional Requirement
```
ID: NFR{number}
Title: {brief descriptive title}
Category: {performance|security|scalability|usability|maintainability}
Description: {clear statement of quality attribute}
Measurable Criterion: {specific, testable metric}
Priority: {must_have|should_have|could_have}
```

## Troubleshooting

### Issue: Too many conflicting requirements
**Cause**: Upstream agents found contradictory patterns  
**Solution**: Review Agent 3 (business rules) and Agent 4 (gaps) outputs

### Issue: All requirements marked "must-have"
**Cause**: Priority ranking failed  
**Solution**: Adjust priority thresholds in config, involve HITL

### Issue: Missing NFRs
**Cause**: Agent 2 journeys lack performance/quality annotations  
**Solution**: Re-run Agent 2 with enhanced touchpoint analysis

## See Also
- `.github/agents/subagents/agent-5-synthesis.agent.md`
- MoSCoW prioritization: https://en.wikipedia.org/wiki/MoSCoW_method
- `config/config.yaml` - Agent configuration
