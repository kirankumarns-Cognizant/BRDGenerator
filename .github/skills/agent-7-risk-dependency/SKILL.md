# Agent 7 Risk & Dependency Analysis Skill

## Skill Definition
**Name**: Agent 7 Risk & Dependency Analysis  
**Type**: Risk Management  
**Language**: PowerShell + Python  
**Agents**: Agent 7  

## Description
Identifies technical, implementation, and business risks while mapping dependencies between requirements, systems, and external components. Provides mitigation strategies and impact analysis.

## Prerequisites
- Python 3.10+ with code analysis tools
- Outputs from Agents 1, 4, 5, and 6
- Valid `config.yaml` configuration

## Invocation

### PowerShell
```powershell
.\agent_7_risk_dependency.ps1 -RepoPath "C:\path\to\repo"
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| RepoPath | string | Yes | - | Path to repository |
| ConfigPath | string | No | config/config.yaml | Config file path |
| OutputPath | string | No | KB/{repo_name}/ | Output directory |
| Verbose | switch | No | false | Enable verbose logging |

## Dependencies
- **Agent 1**: `dependency_map.json`, `scope_definition.json`
- **Agent 4**: `gap_analysis.json`
- **Agent 5**: `functional_requirements.json`, `non_functional_requirements.json`
- **Agent 6**: `acceptance_criteria.json`

## Outputs

### Files Generated
1. **risk_assessment.json**
   ```json
   {
     "risks": [
       {
         "id": "RISK001",
         "category": "technical|implementation|business|security|operational",
         "severity": "critical|high|medium|low",
         "probability": "very_likely|likely|possible|unlikely|rare",
         "title": "Third-party API dependency failure",
         "description": "Payment gateway API may be unavailable during checkout",
         "impact": "Complete loss of payment processing capability",
         "affected_requirements": ["FR023", "FR024"],
         "affected_components": ["PaymentService", "CheckoutController"],
         "mitigation_strategy": {
           "approach": "Implement circuit breaker pattern with fallback",
           "effort": "medium",
           "cost_estimate": "5-8 days",
           "residual_risk": "low"
         },
         "contingency_plan": "Queue payments for retry, notify users of delay",
         "owner": "DevOps Team",
         "priority": 1
       }
     ],
     "risk_summary": {
       "total_risks": 23,
       "critical": 2,
       "high": 7,
       "medium": 10,
       "low": 4
     }
   }
   ```

2. **dependency_analysis.json**
   ```json
   {
     "requirement_dependencies": [
       {
         "requirement_id": "FR023",
         "depends_on": ["FR001", "FR015"],
         "dependency_type": "sequential|parallel|conditional",
         "criticality": "blocking|non-blocking",
         "description": "Payment processing requires user authentication and cart validation"
       }
     ],
     "system_dependencies": [
       {
         "component": "PaymentService",
         "type": "external_api|database|internal_service|library",
         "name": "Stripe API",
         "version": "2023-10-16",
         "criticality": "critical",
         "sla": "99.95% uptime",
         "failure_impact": "Complete payment functionality loss",
         "alternatives": ["PayPal", "Square"]
       }
     ],
     "library_dependencies": [
       {
         "name": "spring-boot-starter-security",
         "version": "3.1.5",
         "vulnerabilities": [],
         "end_of_life": "2025-11-24",
         "upgrade_risk": "low"
       }
     ]
   }
   ```

## Sub-Skills
1. **Risk Identifier**: Discovers potential risks
2. **Impact Analyzer**: Assesses risk impact and probability
3. **Dependency Mapper**: Maps requirement and system dependencies
4. **Vulnerability Scanner**: Checks for security vulnerabilities
5. **Mitigation Strategist**: Generates risk mitigation plans

## Tools Used
- `code_analyzer` (semgrep_adapter) - Code complexity analysis
- Dependency checkers (npm audit, pip-audit, OWASP)
- CVE databases for vulnerability lookup

## Risk Categories

### 1. Technical Risks
- Legacy code complexity
- Technology stack obsolescence
- Performance bottlenecks
- Scalability constraints

### 2. Implementation Risks
- High complexity requirements
- Ambiguous specifications
- Missing expertise
- Tool/framework limitations

### 3. Business Risks
- Scope creep
- Budget overruns
- Schedule delays
- Stakeholder misalignment

### 4. Security Risks
- Authentication/authorization gaps
- Data exposure vulnerabilities
- Dependency vulnerabilities (CVEs)
- Compliance violations

### 5. Operational Risks
- Deployment complexity
- Monitoring gaps
- Disaster recovery weaknesses
- Maintenance burden

## Risk Scoring

### Severity Levels
- **Critical**: System-wide failure, data loss, security breach
- **High**: Major functionality impaired, significant user impact
- **Medium**: Moderate impact, workarounds available
- **Low**: Minor inconvenience, cosmetic issues

### Probability Levels
- **Very Likely (>75%)**: Almost certain to occur
- **Likely (50-75%)**: Probable occurrence
- **Possible (25-50%)**: May occur
- **Unlikely (10-25%)**: Low probability
- **Rare (<10%)**: Highly improbable

### Risk Priority = Severity × Probability

## Dependency Types

### Requirement Dependencies
- **Sequential**: Must be implemented in order
- **Parallel**: Can be implemented simultaneously
- **Conditional**: Implementation depends on decision/outcome

### System Dependencies
- **External APIs**: Third-party services
- **Internal Services**: Microservices, modules
- **Databases**: Data persistence layers
- **Libraries**: Third-party packages

## Error Handling
- Vulnerability data unavailable: Uses cached CVE database
- Missing dependency info: Extracts from build files
- Ambiguous risks: Flags for HITL review

## Performance
- Small repos: ~5-10 minutes
- Medium repos: ~10-20 minutes
- Large repos: ~20-35 minutes
- +5-10 minutes for vulnerability scanning

## Examples

### Example 1: E-commerce Platform
```powershell
.\agent_7_risk_dependency.ps1 -RepoPath "C:\repos\ecommerce" -Verbose
```
**Risks Found**: 2 critical (payment/security), 8 high, 15 medium

### Example 2: Healthcare System
```powershell
.\agent_7_risk_dependency.ps1 -RepoPath "C:\repos\patient-portal"
```
**Risks Found**: 3 critical (HIPAA compliance), 12 high (security/privacy)

## HITL Triggers
- `critical_risk_identified`: Severity=critical requires immediate review
- `unmitigated_high_risk`: High-severity risk without clear mitigation
- `circular_dependency`: Requirements have circular dependencies
- `vulnerable_dependency`: Critical CVE found in dependencies

## Integration
Agent 7 outputs feed into:
- **Agent 8**: Final BRD (risk section, dependency diagrams)
- Project managers: Risk register, mitigation planning
- DevOps: Deployment planning, dependency management

## Configuration
```yaml
agents:
  agent7:
    name: "Risk & Dependency Agent"
    tools:
      - code_analyzer
    enabled_tools:
      code_analyzer: true
    output_files:
      - risk_assessment.json
      - dependency_analysis.json
```

## Mitigation Strategy Template

```json
{
  "approach": "{specific mitigation technique}",
  "actions": [
    "Step 1: {action}",
    "Step 2: {action}"
  ],
  "effort": "low|medium|high",
  "cost_estimate": "{time or budget}",
  "timeline": "{when to implement}",
  "owner": "{responsible team/person}",
  "residual_risk": "low|medium|high",
  "success_criteria": "{how to measure effectiveness}"
}
```

## Common Mitigation Strategies

### For External Dependency Risks
- Circuit breaker patterns
- Fallback mechanisms
- Caching strategies
- Alternative providers

### For Security Risks
- Input validation
- Authentication/authorization enforcement
- Encryption at rest and in transit
- Security audits and penetration testing

### For Performance Risks
- Caching strategies
- Database optimization
- Load balancing
- Horizontal scaling

### For Implementation Risks
- Proof of concepts
- Spike solutions
- Expert consultation
- Training programs

## Troubleshooting

### Issue: No risks identified
**Cause**: Analysis too shallow or overly optimistic  
**Solution**: Review Agent 4 gaps, manually assess high-complexity requirements

### Issue: All risks marked critical
**Cause**: Severity scoring too aggressive  
**Solution**: Recalibrate severity thresholds based on business context

### Issue: Dependency graph too complex
**Cause**: Monolithic architecture or tight coupling  
**Solution**: Recommend architectural refactoring, focus on critical paths

## Visualization Recommendations

### Risk Heat Map
```
Probability
    ^
    |  L   M   H   C
VL  |  □   □   ■   ■
 L  |  □   ■   ■   ■
 P  |  ■   ■   ■   ■
 U  |  ■   ■   ■   ■
    +-----------------> Severity
```

### Dependency Graph
Use Graphviz or Mermaid for visualizing:
- Requirement dependencies (directed graph)
- System dependencies (architecture diagram)
- Library dependency tree

## See Also
- `.github/agents/subagents/agent-7-risk-dependency.agent.md`
- OWASP Dependency-Check: https://owasp.org/www-project-dependency-check/
- CVE Database: https://cve.mitre.org/
- `config/config.yaml` - Agent configuration
