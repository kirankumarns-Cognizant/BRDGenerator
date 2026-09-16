# Agent 6 Acceptance Criteria Skill

## Skill Definition
**Name**: Agent 6 Acceptance Criteria  
**Type**: Test Specification  
**Language**: PowerShell + Python  
**Agents**: Agent 6  

## Description
Generates testable acceptance criteria and test scenarios from functional and non-functional requirements using Given-When-Then format and edge case analysis.

## Prerequisites
- Python 3.10+
- Agent 5 outputs (`functional_requirements.json`, `non_functional_requirements.json`)
- Valid `config.yaml` configuration

## Invocation

### PowerShell
```powershell
.\agent_6_acceptance_criteria.ps1 -RepoPath "C:\path\to\repo"
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| RepoPath | string | Yes | - | Path to repository |
| ConfigPath | string | No | config/config.yaml | Config file path |
| OutputPath | string | No | KB/{repo_name}/ | Output directory |
| Verbose | switch | No | false | Enable verbose logging |

## Dependencies
- **Agent 5**: `functional_requirements.json`, `non_functional_requirements.json`

## Outputs

### Files Generated
1. **acceptance_criteria.json**
   ```json
   {
     "criteria": [
       {
         "id": "AC001",
         "requirement_id": "FR001",
         "title": "Valid email format accepted",
         "given": "User is on registration page",
         "when": "User enters valid email 'user@example.com'",
         "then": "Email is accepted and validation passes",
         "test_type": "functional|integration|performance|security",
         "priority": "high|medium|low",
         "automation_feasible": true
       },
       {
         "id": "AC002",
         "requirement_id": "FR001",
         "title": "Invalid email format rejected",
         "given": "User is on registration page",
         "when": "User enters invalid email 'notanemail'",
         "then": "Error message 'Invalid email format' is displayed",
         "test_type": "functional",
         "priority": "high",
         "automation_feasible": true
       }
     ],
     "total_criteria": 127,
     "requirements_covered": 45
   }
   ```

2. **test_scenarios.json**
   ```json
   {
     "scenarios": [
       {
         "id": "TS001",
         "title": "User Registration Happy Path",
         "description": "Complete user registration with valid data",
         "acceptance_criteria_ids": ["AC001", "AC003", "AC005"],
         "preconditions": [
           "Database is empty",
           "Email service is available"
         ],
         "steps": [
           {
             "step": 1,
             "action": "Navigate to registration page",
             "expected_result": "Registration form displayed"
           },
           {
             "step": 2,
             "action": "Enter valid email",
             "expected_result": "Email validation passes"
           }
         ],
         "postconditions": [
           "User record created in database",
           "Confirmation email sent"
         ],
         "test_data": {
           "email": "newuser@example.com",
           "password": "SecurePass123!"
         }
       }
     ]
   }
   ```

## Sub-Skills
1. **Criteria Generator**: Creates Given-When-Then statements
2. **Edge Case Analyzer**: Identifies boundary conditions
3. **Negative Scenario Creator**: Generates failure test cases
4. **Test Data Suggester**: Recommends test data sets
5. **Coverage Mapper**: Ensures all requirements have criteria

## Tools Used
- Template-based generation
- Boundary value analysis
- Equivalence partitioning
- LLM-based edge case discovery

## Acceptance Criteria Patterns

### Functional Testing
```gherkin
Given: {initial state/context}
When: {user action or system event}
Then: {expected outcome/behavior}
```

### Performance Testing
```gherkin
Given: {load condition}
When: {operation is performed}
Then: {performance metric meets threshold}
```

### Security Testing
```gherkin
Given: {user with specific permissions}
When: {attempts to access resource}
Then: {authorization check succeeds/fails}
```

## Edge Case Categories

1. **Boundary Values**
   - Minimum/maximum values
   - Empty/null inputs
   - Zero values

2. **Invalid Inputs**
   - Wrong data types
   - Malformed data
   - SQL injection attempts

3. **State Transitions**
   - Invalid state changes
   - Concurrent operations
   - Race conditions

4. **Integration Points**
   - External service failures
   - Timeout scenarios
   - Partial failures

## Error Handling
- Requirement without criteria: Warning logged
- Untestable criterion: Marked for manual testing
- Missing test data: Uses default values

## Performance
- Small repos: ~3-7 minutes
- Medium repos: ~7-15 minutes
- Large repos: ~15-30 minutes

## Examples

### Example 1: E-commerce Checkout
```powershell
.\agent_6_acceptance_criteria.ps1 -RepoPath "C:\repos\ecommerce" -Verbose
```
**Output**: 87 acceptance criteria, 24 test scenarios

### Example 2: Authentication Service
```powershell
.\agent_6_acceptance_criteria.ps1 -RepoPath "C:\repos\auth-service"
```
**Output**: 52 criteria (heavy on security scenarios)

## HITL Triggers
- `untestable_criterion`: Requirement cannot be translated to testable criteria
- `ambiguous_expected_result`: Multiple interpretations possible
- `missing_test_data`: Cannot determine appropriate test data

## Integration
Agent 6 outputs feed into:
- **Agent 7**: Risk assessment (test coverage analysis)
- **Agent 8**: Final BRD (acceptance criteria section)
- QA teams: Test case implementation

## Configuration
```yaml
agents:
  agent6:
    name: "Acceptance Criteria Agent"
    tools: []
    output_files:
      - acceptance_criteria.json
      - test_scenarios.json
```

## Gherkin Syntax Guide

### Basic Structure
```gherkin
Feature: User Registration
  
  Scenario: Valid email registration
    Given the user is on the registration page
    When the user enters valid email "user@example.com"
    Then the email validation should pass
    And the user should see "Email accepted"
```

### Scenario Outline (Data-Driven)
```gherkin
Scenario Outline: Email validation with various formats
  Given the user is on the registration page
  When the user enters email "<email>"
  Then the validation result should be "<result>"
  
  Examples:
    | email               | result  |
    | valid@example.com   | pass    |
    | invalid             | fail    |
    | test@               | fail    |
```

## Coverage Metrics

### Requirement Coverage
- % of requirements with acceptance criteria
- Target: 100% for must-have requirements

### Scenario Coverage
- Happy path scenarios
- Negative scenarios
- Edge case scenarios
- Target: 80%+ overall coverage

## Troubleshooting

### Issue: Acceptance criteria too vague
**Cause**: Upstream requirements lack specificity  
**Solution**: Review Agent 5 outputs, enhance requirement descriptions

### Issue: Missing edge cases
**Cause**: Edge case analyzer insufficient  
**Solution**: Manually review and add, update edge case patterns

### Issue: Untestable criteria
**Cause**: NFRs without measurable metrics  
**Solution**: Refine NFRs with specific thresholds

## Test Automation Guidance

### Automation Feasibility
- **High**: API testing, data validation, calculations
- **Medium**: UI flows, integration scenarios
- **Low**: Visual design, subjective usability

### Recommended Tools
- **Unit Tests**: JUnit, pytest, Jest
- **Integration Tests**: RestAssured, Postman, Cypress
- **E2E Tests**: Selenium, Playwright
- **Performance**: JMeter, Gatling

## See Also
- `.github/agents/subagents/agent-6-acceptance-criteria.agent.md`
- Gherkin syntax: https://cucumber.io/docs/gherkin/
- `config/config.yaml` - Agent configuration
