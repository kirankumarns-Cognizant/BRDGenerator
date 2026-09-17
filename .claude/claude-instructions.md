# Claude Instructions for BRD Agent Execution

## Overview

This directory contains Claude-specific instructions, configurations, and workflows for executing the BRD (Business Requirements Document) Agent pipeline. Claude can orchestrate and execute BRD generation tasks using the skills and prompts defined here.

## Directory Structure

```
.claude/
├── claude-instructions.md        # This file - main instructions for Claude
├── agents/                       # Claude agent definitions & workflows
│   ├── brd-pipeline-orchestrator.md
│   ├── agent-executor.md
│   └── repository-analyzer.md
├── skills/                       # Reusable Claude skills
│   ├── repo-discovery/
│   ├── code-analysis/
│   ├── document-parsing/
│   ├── brd-generation/
│   └── quality-validation/
├── prompts/                      # Claude prompt templates
│   ├── system-prompts/
│   ├── task-prompts/
│   └── analysis-prompts/
└── workflows/                    # Execution workflows
    ├── full-pipeline.workflow.md
    ├── agent-by-agent.workflow.md
    └── custom-analysis.workflow.md
```

## Core Capabilities

Claude can execute the following BRD operations:

### 1. Repository Discovery & Analysis
- Scan Java repositories for code structure
- Identify microservices, modules, and dependencies
- Detect configuration files and frameworks
- Extract key architectural patterns

### 2. Code Understanding
- Analyze Java source code for business logic
- Map code to business processes
- Identify entity relationships and data flows
- Document API endpoints and integrations

### 3. Document Processing
- Parse uploaded documents (PDF, Word, Markdown)
- Extract requirements from specification documents
- Identify business rules and constraints
- Map document sections to code components

### 4. BRD Generation
- Generate Business Requirements Documents from code analysis
- Create user journey mappings
- Document business rules and constraints
- Produce acceptance criteria
- Identify gaps and risks

### 5. Quality Validation
- Verify BRD completeness
- Check requirement coverage
- Validate consistency across sections
- Score confidence levels

## Configuration

### Environment Variables
```bash
ANTHROPIC_API_KEY          # Claude API key
PROJECT_ROOT               # Path to BRD_agent project
REPO_PATH                  # Path to repository being analyzed
KB_ROOT                    # Knowledge base output directory
```

### Config File
All pipeline configuration is in `config/config.yaml`:
- `llm.providers` - LLM model configuration
- `agents[agent1-9]` - Individual agent settings
- `tools` - Tool availability and settings
- `thresholds` - Confidence scoring thresholds

## Usage Patterns

### Pattern 1: Full Pipeline Execution
Claude executes all 9 agents sequentially to generate a complete BRD:

```
1. Agent 1: Discovery & Scoping (claude-3-opus)
   └─ Scans repo, catalogs artifacts, defines scope

2. Agent 2: Journey Mapping (claude-3-haiku)
   └─ Maps user journeys through code

3. Agent 3: Business Rules (claude-3-haiku)
   └─ Extracts and documents rules

4. Agent 4: Gap Analysis (claude-3-haiku)
   └─ Identifies missing requirements

5. Agent 5: Synthesis (claude-3-opus)
   └─ Creates comprehensive BRD

6. Agent 6: Acceptance Criteria (claude-3-haiku)
   └─ Generates test scenarios

7. Agent 7: Risk & Dependencies (claude-3-sonnet)
   └─ Documents risks and dependencies

8. Agent 8: Summarizer (claude-3-opus)
   └─ Creates executive summary

9. Agent 9: KB Store Sync (claude-3-haiku)
   └─ Stores results in knowledge base
```

### Pattern 2: Agent-by-Agent Execution
Claude executes individual agents for targeted analysis:
- Single agent for specific analysis type
- Reuse outputs from previous runs
- Focus on specific code sections

### Pattern 3: Custom Analysis
Claude performs specialized analysis beyond standard agents:
- Microservices mapping
- Technology stack analysis
- Performance implications
- Security analysis

## Agent Execution Interface

### Starting an Agent
```python
# Claude invokes via subagent orchestration
from config.llm_selector import LLMSelector

agent_num = 1  # Agent 1-9
model_config = LLMSelector.get_model_for_agent(agent_num)
# {
#   "model": "claude-3-opus",
#   "provider": "anthropic",
#   "complexity": "HIGH",
#   "task": "Discovery & Scoping"
# }
```

### Input Parameters
- `repo_path`: Path to source repository
- `output_dir`: Where to write artifacts
- `config_path`: Path to config.yaml
- `documents`: List of uploaded document paths

### Output Artifacts
Each agent produces:
- `agent_<N>_output.json` - Structured output
- `agent_<N>_report.md` - Markdown report
- `agent_<N>_state.pkl` - Pickle state file

## Best Practices

### 1. Respect Configuration
- Always load settings from `config/config.yaml`
- Never hardcode paths - use PROJECT_ROOT
- Check tool availability before using
- Use configured LLM models per agent

### 2. Confidence Scoring
- Every operation returns `confidence: 0.0-1.0`
- Flag results below `config.get_threshold('low_confidence')` (default 0.6)
- Provide reasoning for low confidence scores
- Escalate ambiguous cases for human review

### 3. Error Handling
- Log all errors to pipeline log
- Never raise exceptions - return error in output with low confidence
- Attempt fallback strategies
- Provide clear error messages for debugging

### 4. Output Quality
- Follow output schema exactly
- Include required fields in all outputs
- Document assumptions and limitations
- Provide intermediate results for debugging

### 5. Performance
- Cache expensive operations (file reads, parsing)
- Batch similar analyses together
- Stream long outputs to avoid token limits
- Clear session state between agents

## File References

### Main Execution Files
- `run_all_agents.py` - Orchestrates all 9 agents
- `app.py` - Streamlit UI entry point
- `config/config.yaml` - Central configuration
- `config/llm_selector.py` - Model selection logic

### Key Directories
- `KB/` - Knowledge base storage
- `kb_gen/` - Knowledge generation code
- `.github/skills/` - Python skill implementations
- `logs/` - Execution logs

## Integration Points

### With Streamlit UI
Claude can trigger pipeline execution through:
- `ui/pipeline_tab.py` - Pipeline execution tab
- Status updates via queue (`_pipeline_queue`)
- Real-time progress tracking

### With Python Orchestrator
Claude executes via:
- `run_all_agents.py` - Sequential agent execution
- Individual `agent_<N>_runner.py` files
- Direct Python invocation with repo path

### With Knowledge Base
Claude stores/retrieves via:
- `kb_gen/storage/` - KB storage adapters
- Chroma vector database (`kb_store/`)
- ChromaDB for semantic search

## Common Tasks

### Task: Analyze a Java Repository
```
1. Read repository structure from repo_path
2. Run Agent 1 (Discovery) to catalog artifacts
3. Agents 2-8 analyze specific aspects
4. Agent 9 stores results in KB
5. Return summary and artifact locations
```

### Task: Process Uploaded Documents
```
1. Parse documents via doc_parser tool
2. Extract requirements and specifications
3. Pass to relevant agents for correlation
4. Update BRD with document-derived requirements
5. Track document sources in outputs
```

### Task: Generate Custom Report
```
1. Specify analysis type (microservices, security, etc.)
2. Run targeted agent or custom analysis
3. Format output per requirement
4. Store in KB if needed
5. Provide download link
```

## Limitations & Constraints

### Token Limits
- Claude has context window limits
- Large repositories may need chunking
- Stream long outputs to avoid truncation
- Save intermediate results regularly

### Tool Availability
- Some tools may be disabled in config
- Fallback adapters provided (stub_adapter.py)
- Check tool enabled status before use
- Document tool dependencies

### Knowledge Base
- ChromaDB has collection limits
- Semantic search works best with embeddings
- Manual cleanup needed periodically
- Backup before large operations

## Support & Debugging

### Enable Debug Mode
Set in config.yaml:
```yaml
debug: true
log_level: DEBUG
```

### Check Logs
```bash
# Tail execution logs
tail -f logs/pipeline_*.log

# Review agent-specific logs
cat logs/agent_<N>_*.log
```

### Validate Configuration
```bash
# Test config loading
python -c "from config.config_loader import ConfigLoader; c = ConfigLoader('config/config.yaml'); print(c.get_all())"

# Verify LLM models
python verify_agent_models.py
```

## Next Steps

1. **Review Skills** - Check `.claude/skills/` for available capabilities
2. **Understand Workflows** - Read `.claude/workflows/` for execution patterns
3. **Start Simple** - Begin with single-agent execution
4. **Iterate** - Refine prompts and agents based on results
5. **Monitor** - Track confidence scores and error rates

## Version History

- **v1.0** (2026-09-17) - Initial Claude Instructions
  - Full pipeline support (Agents 1-9)
  - Multi-provider LLM configuration
  - Real-time Streamlit integration
  - Knowledge base storage

---

**Last Updated:** 2026-09-17  
**Maintainer:** BRD Agent Team  
**Claude Version:** 3.5+ (Sonnet, Opus, Haiku)
