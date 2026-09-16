# Agent 4 Gap Analysis Skill

## Skill Definition
**Name**: Agent 4 Gap Analysis  
**Type**: Comparative Analysis  
**Language**: PowerShell + Python  
**Agents**: Agent 4  

## Description
Identifies gaps between current implementation and expected functionality by comparing user journeys, business rules, and historical patterns from the knowledge base.

## Prerequisites
- Python 3.10+ with ChromaDB/vector store dependencies
- Agent 1, 2, and 3 outputs available
- kb_store populated (for historical comparisons)
- Valid `config.yaml` configuration

## Invocation

### PowerShell
```powershell
.\agent_4_gap_analysis.ps1 -RepoPath "C:\path\to\repo"
```

### With Options
```powershell
.\agent_4_gap_analysis.ps1 `
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
- **Agent 1**: `scope_definition.json`, `artifact_catalog.json`
- **Agent 2**: `user_journeys.json`, `touchpoints.json`
- **Agent 3**: `business_rules.json`, `validation_logic.json`
- **kb_store**: Historical patterns from previous projects

## Outputs

### Files Generated
1. **gap_analysis.json**: Identified gaps
   ```json
   {
     "gaps": [
       {
         "id": "GAP001",
         "type": "missing_functionality|undocumented_feature|incomplete_journey|missing_validation",
         "severity": "critical|high|medium|low",
         "description": "No validation rule for email format in registration journey",
         "affected_journey": "user_registration",
         "recommendation": "Add email format validation",
         "confidence": 0.88,
         "evidence": [
           "Journey step 'email input' has no corresponding validation rule",
           "Similar projects have email validation at this step"
         ]
       }
     ],
     "total_gaps": 12,
     "critical_gaps": 2,
     "overall_confidence": 0.85
   }
   ```

2. **recommendations.json**: Remediation recommendations
   ```json
   {
     "recommendations": [
       {
         "gap_id": "GAP001",
         "priority": 1,
         "action": "Implement email format validation",
         "rationale": "Required for data integrity",
         "effort_estimate": "low|medium|high",
         "similar_implementations": [
           "spring-petclinic: EmailValidator.java",
           "microservice-auth: EmailValidationRule.java"
         ]
       }
     ]
   }
   ```

## Sub-Skills
This skill orchestrates:
1. **Journey-Rule Matcher**: Maps journeys to business rules
2. **Coverage Analyzer**: Identifies uncovered journeys
3. **Historical Comparator**: Queries kb_store for similar patterns
4. **Gap Classifier**: Categorizes and prioritizes gaps
5. **Recommendation Generator**: Suggests remediation actions

## Tools Used
- `vector_store` (chromadb_adapter) - Historical pattern matching
- JSON parsing - Analyzing upstream outputs
- Semantic similarity - Comparing journeys and rules

## Analysis Types

### 1. Missing Functionality
- Journeys without corresponding code implementation
- Business rules not enforced in code
- Expected features from similar systems

### 2. Undocumented Features
- Code functionality not reflected in journeys
- Business rules without documentation
- Shadow functionality (implemented but not specified)

### 3. Incomplete Journeys
- Journeys missing error handling
- Incomplete user flows
- Missing edge cases

### 4. Validation Gaps
- Business rules without validation code
- Input fields without validation
- Missing authorization checks

## Error Handling
- Low confidence (<0.6): Flags for HITL review
- Ambiguous gaps: Marked for human interpretation
- Missing dependencies: Fails with clear error message
- Empty kb_store: Proceeds without historical comparison (reduced confidence)

## Performance
- Small repos: ~2-5 minutes
- Medium repos: ~5-12 minutes
- Large repos: ~12-25 minutes
- +2-5 minutes for kb_store queries

## Examples

### Example 1: E-commerce Application
```powershell
.\agent_4_gap_analysis.ps1 -RepoPath "C:\repos\ecommerce-app" -Verbose
```
**Gaps Found**: 8 missing validations, 3 incomplete journeys, 2 undocumented features

### Example 2: Healthcare System
```powershell
.\agent_4_gap_analysis.ps1 -RepoPath "C:\repos\patient-portal"
```
**Gaps Found**: 12 critical security gaps, 5 missing audit trails

## HITL Triggers
- `ambiguous_gap`: Gap identification requires human judgment
- `low_confidence_gap`: Gap confidence below 0.6
- `critical_gap_found`: Severity=critical requires immediate review
- `conflicting_evidence`: Evidence points to contradictory conclusions

## Integration
Agent 4 outputs feed into:
- **Agent 5**: Requirements synthesis (gaps become new requirements)
- **Agent 6**: Acceptance criteria (gap remediation becomes test cases)
- **Agent 7**: Risk assessment (gaps inform risk analysis)

## Configuration
See `config.yaml` under `agents.agent4`:
```yaml
agents:
  agent4:
    name: "Gap Analysis Agent"
    tools:
      - vector_store
    enabled_tools:
      vector_store: true
    output_files:
      - gap_analysis.json
      - recommendations.json
```

## RAG Query Examples
Agent 4 uses kb_store for historical comparisons:

```python
# Find similar validation patterns
kb_store.search("email validation in registration flow", k=5)

# Find missing functionality patterns
kb_store.search("payment processing error handling", k=3)

# Cross-repository pattern analysis
kb_store.search("authentication flow implementation", filter={"domain": "healthcare"})
```

## Troubleshooting

### Issue: No historical patterns found
**Cause**: kb_store empty or not populated  
**Solution**: Run Agent 9 to ingest historical artifacts, or proceed without historical comparison

### Issue: Too many false positive gaps
**Cause**: Confidence threshold too low  
**Solution**: Adjust `thresholds.low_confidence` in config.yaml

### Issue: Missing critical gaps
**Cause**: Insufficient coverage in Agent 2 or Agent 3  
**Solution**: Review upstream agent outputs, re-run with verbose logging

## See Also
- `.github/agents/subagents/agent-4-gap-analysis.agent.md` - Full agent specification
- `tools/adapters/chromadb_adapter.py` - Vector store implementation
- `config/config.yaml` - Agent configuration
- `kb_store/README.md` - Knowledge base structure
