# BRD Pipeline Orchestrator Agent

**Purpose:** Claude orchestrates and executes the complete BRD pipeline, coordinating all 9 agents to generate comprehensive Business Requirements Documents from Java repositories.

## Agent Capabilities

### 1. Repository Analysis
- Scans Java source code repositories
- Identifies project structure, modules, and dependencies
- Detects frameworks, patterns, and architectural styles
- Catalogs configuration files and metadata

### 2. Agent Coordination
- Executes agents sequentially (Agent 1 → Agent 9)
- Manages state transfer between agents
- Monitors execution progress and confidence scores
- Handles errors and fallback strategies

### 3. Document Processing
- Parses uploaded documents (PDF, Word, Markdown)
- Extracts business requirements and specifications
- Correlates documents with code artifacts
- Integrates document insights into BRD

### 4. BRD Generation
- Synthesizes outputs from all 9 agents
- Creates comprehensive BRD document
- Formats requirements, rules, and criteria
- Produces executive summary

### 5. Quality Assurance
- Validates BRD completeness and consistency
- Checks confidence levels across agents
- Identifies gaps and risks
- Scores overall quality

## Input Parameters

```json
{
  "repo_path": "/path/to/java/repository",
  "output_dir": "/path/to/output/KB/repo_name",
  "config_path": "config/config.yaml",
  "uploaded_documents": ["doc1.pdf", "doc2.docx"],
  "agents_to_run": [1, 2, 3, 4, 5, 6, 7, 8, 9],
  "model_config": {
    "provider": "anthropic",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "options": {
    "skip_document_parsing": false,
    "generate_summary": true,
    "store_in_kb": true,
    "confidence_threshold": 0.6
  }
}
```

## Execution Flow

### Phase 1: Setup & Validation
- Validate repo_path exists and is readable
- Load config.yaml and model settings
- Create output directory structure
- Initialize pipeline logger

### Phase 2: Repository Discovery (Agent 1)
```
Input: repo_path
Process:
  - Scan repository structure
  - Identify modules and dependencies
  - Extract architectural patterns
  - Catalog key files and configurations
Output: scope_definition, artifact_catalog, dependency_map
```

### Phase 3: Analysis Agents (Agents 2-8)
```
Agent 2: Journey Mapping
  - Map user journeys through system
  - Document interaction flows
  - Identify key business processes

Agent 3: Business Rules
  - Extract business rules from code
  - Document constraints and validations
  - Map rules to code locations

Agent 4: Gap Analysis
  - Identify missing requirements
  - Compare code to documented requirements
  - Flag ambiguities and inconsistencies

Agent 5: Synthesis
  - Combine all agent outputs
  - Create comprehensive BRD
  - Ensure consistency

Agent 6: Acceptance Criteria
  - Generate test scenarios
  - Document acceptance criteria
  - Create validation checklists

Agent 7: Risk & Dependencies
  - Identify technical risks
  - Document dependencies
  - Assess impact and mitigation

Agent 8: Summarizer
  - Create executive summary
  - Highlight key findings
  - Provide quick reference guide
```

### Phase 4: Knowledge Base Storage (Agent 9)
- Store BRD in vector database
- Index for semantic search
- Create collection for RAG queries
- Track document versions

### Phase 5: Post-Processing
- Generate final reports
- Create ZIP archive of artifacts
- Compute quality metrics
- Provide download links

## Agent Configuration

From `config/config.yaml`:

```yaml
agents:
  agent1:
    model: claude-3-opus
    provider: anthropic
    complexity: HIGH
    task: "Discovery & Scoping"
    
  agent2:
    model: claude-3-haiku
    provider: anthropic
    complexity: LOW
    task: "Journey Mapping"
    
  # ... agents 3-9 follow similar pattern
```

## Output Schema

### BRD Document
```json
{
  "metadata": {
    "version": "1.0",
    "generated_at": "2026-09-17T10:30:00Z",
    "repository": "repo_name",
    "confidence": 0.85
  },
  "executive_summary": "...",
  "scope": {
    "description": "...",
    "boundaries": "...",
    "out_of_scope": "..."
  },
  "requirements": [
    {
      "id": "REQ-001",
      "title": "...",
      "description": "...",
      "priority": "HIGH",
      "source": ["code", "document"],
      "confidence": 0.9
    }
  ],
  "business_rules": [...],
  "user_journeys": [...],
  "acceptance_criteria": [...],
  "risks_and_dependencies": [...],
  "artifacts": {
    "agent_outputs": [...],
    "supporting_documents": [...]
  }
}
```

## Error Handling

### Low Confidence Scenarios
- Return output with confidence score
- Explain reasoning for low confidence
- Suggest manual review areas
- Provide alternative interpretations

### Failed Agent Execution
- Log error with full context
- Use fallback strategy if available
- Continue with available data
- Mark affected sections as uncertain

### Invalid Input
- Validate all parameters upfront
- Provide clear error messages
- Suggest corrections
- Halt gracefully

## Performance Considerations

### Token Optimization
- Chunk large files for processing
- Summarize intermediate results
- Use targeted prompts
- Cache expensive computations

### Execution Speed
- Run independent analyses in parallel where possible
- Stream long outputs
- Reuse cached results
- Monitor token usage

### Quality vs Speed
- Adjust model complexity based on needs
- Use claude-3-haiku for simple tasks
- Use claude-3-opus for complex synthesis
- Balance thoroughness with efficiency

## Integration Points

### Streamlit UI
- Receives execution request from `pipeline_tab.py`
- Sends progress updates via queue
- Updates progress tracker in real-time
- Provides artifact download links

### Python Orchestrator
- Called by `run_all_agents.py`
- Uses `LLMSelector` for model configuration
- Logs to pipeline log file
- Returns structured state object

### Knowledge Base
- Stores outputs in ChromaDB
- Creates embeddings for semantic search
- Manages collections per repository
- Enables RAG queries

## Example Usage

### Via Claude in VS Code
```
User: "Analyze the spring-petclinic repository and generate a BRD"

Claude Action:
1. Execute BRD Pipeline Orchestrator with repo_path="KB/spring-petclinic"
2. Agents 1-9 execute sequentially
3. Generate comprehensive BRD document
4. Store in KB and create download link
5. Return summary with key insights
```

### Via Streamlit UI
1. User uploads or selects repository
2. User decides on documents (YES/NO)
3. User clicks "▶ Run Pipeline"
4. Orchestrator executes all agents
5. Progress tracker shows real-time updates with models used
6. Artifacts appear in "Artifacts" section
7. User can download BRD and supporting files

### Via Python Script
```python
from config.config_loader import ConfigLoader
from brd_orchestrator import BRDPipelineOrchestrator

config = ConfigLoader('config/config.yaml')
orchestrator = BRDPipelineOrchestrator(config)

result = orchestrator.execute(
    repo_path="KB/my-repo",
    uploaded_documents=["spec.pdf"],
    confidence_threshold=0.6
)

print(f"BRD Generated: {result['output_dir']}")
print(f"Confidence: {result['confidence']}")
```

## Monitoring & Debugging

### Enable Verbose Logging
Set in config.yaml:
```yaml
debug: true
log_level: DEBUG
verbose_prompts: true
```

### Track Agent Progress
```bash
# Watch real-time logs
tail -f logs/pipeline_execution.log

# Review individual agent logs
cat logs/agent_1_discovery.log
cat logs/agent_2_journey_mapping.log
# ... etc
```

### Validate Outputs
- Check confidence scores (expect > 0.7)
- Verify artifact generation
- Review error logs for issues
- Test BRD completeness

## Limitations

- **Token Limits:** Large repos may exceed context window
- **Tool Access:** Limited to Python/file system operations
- **Real-time Data:** Cannot fetch live API responses
- **Database:** Limited to configured KB storage
- **External Services:** Cannot directly call Jira/Confluence (disabled tools)

## Next Steps

1. Configure model preferences in `config.yaml`
2. Set up knowledge base storage
3. Prepare sample repositories for testing
4. Create custom prompts for domain-specific analysis
5. Set up monitoring and alerting

---

**Created:** 2026-09-17  
**Framework:** Claude + BRD Agent  
**Status:** Operational
