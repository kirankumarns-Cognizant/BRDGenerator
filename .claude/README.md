# Claude BRD Agent Directory

This directory contains Claude-specific configurations, instructions, and workflows for executing the BRD (Business Requirements Document) Agent pipeline.

## Quick Start

### For Claude Users in VS Code

1. **Copy the System Prompt**
   - Open `.claude/prompts/system-prompts/brd-orchestration-system.prompt`
   - Use this as your Claude system context

2. **Request Pipeline Execution**
   ```
   "Analyze the spring-petclinic repository and generate a complete BRD using the 9-agent pipeline"
   ```

3. **Monitor Execution**
   - Claude will execute agents 1-9 sequentially
   - Real-time progress updates in terminal
   - Check logs at `logs/pipeline_execution.log`

### For Streamlit UI Users

1. **Upload or select repository** in sidebar
2. **Answer document question** (YES/NO)
3. **Click "▶ Run Pipeline"** button
4. **Watch progress tracker** showing models used per agent
5. **Download BRD artifacts** when complete

## Directory Contents

```
.claude/
├── README.md                           # This file
├── claude-instructions.md              # Main instructions for Claude
│
├── agents/                             # Claude agent definitions
│   ├── brd-pipeline-orchestrator.md    # Main orchestrator agent
│   └── [other agent specs]
│
├── skills/                             # Reusable Claude skills
│   ├── repo-discovery/                 # Repository scanning
│   ├── code-analysis/                  # Code understanding
│   ├── document-parsing/               # Document processing
│   ├── brd-generation/                 # BRD synthesis
│   └── quality-validation/             # QA and validation
│
├── prompts/                            # Claude prompts
│   ├── system-prompts/
│   │   └── brd-orchestration-system.prompt   # Main system prompt
│   ├── task-prompts/                   # Task-specific prompts
│   └── analysis-prompts/               # Analysis templates
│
└── workflows/                          # Execution workflows
    ├── full-pipeline.workflow.md       # Complete 9-agent pipeline
    ├── agent-by-agent.workflow.md      # Individual agent execution
    └── custom-analysis.workflow.md     # Custom analysis workflows
```

## Key Features

✅ **Full Pipeline Support** - All 9 agents coordinated  
✅ **Multi-Provider LLMs** - Claude, OpenAI models available  
✅ **Real-Time Tracking** - Model and progress visibility  
✅ **Quality Validation** - Confidence scoring for all outputs  
✅ **Knowledge Base Integration** - Automatic KB storage and indexing  
✅ **Error Handling** - Graceful degradation with fallbacks  
✅ **Comprehensive Logging** - Full audit trail  

## Supported Operations

### 1. Full BRD Generation
Generate a complete, professional Business Requirements Document from a Java repository:
- **Input:** Repository path, optional documents
- **Output:** Complete BRD with all required sections
- **Time:** 15-30 minutes
- **Confidence:** Target > 0.85

### 2. Targeted Analysis
Analyze specific aspects of a codebase:
- **User Journeys:** Journey mapping for key features
- **Business Rules:** Extraction and documentation
- **Risks & Dependencies:** Technical analysis
- **Gap Analysis:** Compare code to requirements

### 3. Document Integration
Combine code analysis with uploaded documents:
- **Parse Documents:** PDF, Word, Markdown support
- **Correlate Requirements:** Map docs to code
- **Enrich Analysis:** Document-informed BRD generation

### 4. Quality Assurance
Validate generated BRD:
- **Completeness Check:** All sections present
- **Consistency Validation:** Cross-reference checks
- **Confidence Scoring:** Per-agent and overall scores

## Configuration

### LLM Models Used

The pipeline uses optimal models for each task complexity:

```
Complexity     Model               Use Cases
───────────────────────────────────────────────────
HIGH           claude-3-opus       Complex synthesis (Agents 1, 5, 8)
MEDIUM         claude-3-sonnet     Analytical tasks (Agent 7)
LOW            claude-3-haiku      Simple extraction (Agents 2, 3, 4, 6, 9)
```

All settings loaded from `config/config.yaml`.

### Environment Setup

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Set project root (optional)
export PROJECT_ROOT=/path/to/BRD_agent

# Run via Streamlit
python -m streamlit run app.py

# Or run via Claude command
python -c "from .claude.claude_runner import execute_pipeline; execute_pipeline('repo_path')"
```

## Usage Examples

### Example 1: Generate BRD for Spring Boot App

**User Request:**
```
"I have a Spring Boot microservices application in KB/my-app. 
Generate a complete BRD with all requirements, business rules, 
and acceptance criteria. Analyze both the code and this specification document."
```

**Claude Action:**
```
1. ✅ Load project configuration
2. ✅ Scan KB/my-app repository
3. ✅ Parse specification document
4. ✅ Execute Agent 1: Discovery & Scoping
   └─ Model: claude-3-opus
   └─ Time: 4m 23s
   └─ Confidence: 0.93
5. ✅ Execute Agent 2: Journey Mapping
   └─ Model: claude-3-haiku
   └─ Time: 2m 15s
   └─ Confidence: 0.88
6. ✅ [Agents 3-8 execute]
7. ✅ Execute Agent 9: KB Sync
   └─ Store in knowledge base
   └─ Create embeddings
   └─ Enable semantic search
8. ✅ Generate final BRD document
9. ✅ Create download packages
```

**Output:**
- Complete BRD document (markdown + PDF)
- 27 detailed artifacts
- Business rules catalog
- Risk and dependency analysis
- Quality score: 0.88

### Example 2: Analyze Specific Module

**User Request:**
```
"Focus on the payment processing module in my repository. 
What are the key business rules and acceptance criteria?"
```

**Claude Action:**
1. Identify payment processing module
2. Run focused Agent 3 (Business Rules)
3. Run focused Agent 6 (Acceptance Criteria)
4. Synthesize findings
5. Return focused analysis

### Example 3: Gap Analysis

**User Request:**
```
"We have a requirements spec and legacy code. 
Identify what's implemented, what's missing, and inconsistencies."
```

**Claude Action:**
1. Parse requirements document
2. Scan legacy codebase
3. Run Agent 4 (Gap Analysis)
4. Document findings
5. Recommend actions

## Integration Points

### With Streamlit UI (`app.py`)
- Receive execution requests from pipeline tab
- Send progress updates via queue
- Display model info in progress tracker
- Provide artifact download links

### With Python Orchestrator (`run_all_agents.py`)
- Execute agents sequentially
- Track execution metrics
- Handle errors and fallbacks
- Generate comprehensive reports

### With Knowledge Base (`kb_gen/`)
- Store BRD in ChromaDB
- Create embeddings for search
- Manage collections per repository
- Enable RAG queries

## Monitoring & Debugging

### View Execution Logs
```bash
# Real-time pipeline logs
tail -f logs/pipeline_execution.log

# Specific agent logs
tail -f logs/agent_1_discovery.log

# Search for errors
grep "ERROR" logs/*.log

# View model usage
grep "Model:" logs/pipeline_execution.log
```

### Check Confidence Scores
```bash
# Extract confidence metrics
python -c "
import json
with open('KB/repo_name/artifacts/pipeline_metrics.json') as f:
    metrics = json.load(f)
    for agent, score in metrics['confidence_per_agent'].items():
        print(f'{agent}: {score:.2%}')
"
```

### Validate Outputs
```bash
# Check artifact generation
ls -lah KB/repo_name/artifacts/

# Verify KB storage
python -c "from kb_gen.storage import ChromaAdapter; print(ChromaAdapter.list_collections())"
```

## Troubleshooting

### Pipeline Timeout
**Issue:** Execution takes > 60 minutes  
**Solution:**
1. Check repository size
2. Reduce model complexity for large repos
3. Skip optional analysis steps
4. Split into multiple focused analyses

### Low Confidence Scores
**Issue:** Confidence < 0.6 after execution  
**Solution:**
1. Add supporting documents for context
2. Provide manual clarifications
3. Increase model complexity for synthesis steps
4. Re-run with refined inputs

### KB Storage Errors
**Issue:** Knowledge base sync fails  
**Solution:**
1. Verify ChromaDB running: `ps aux | grep chroma`
2. Check KB directory permissions: `chmod 755 kb_store`
3. Clear cache: `rm -rf kb_store/cache`
4. Restart service: `systemctl restart chromadb`

## Performance Tips

- **Optimize for Speed:** Use haiku models for simple tasks
- **Optimize for Quality:** Use opus models for synthesis
- **Parallel Processing:** Run independent agents in parallel (where applicable)
- **Caching:** Reuse Agent 1 outputs across multiple analyses
- **Chunking:** Process large repos in logical sections

## Best Practices

1. ✅ **Always validate configuration** before execution
2. ✅ **Review confidence scores** - escalate low scores
3. ✅ **Provide context documents** for complex requirements
4. ✅ **Monitor token usage** for cost optimization
5. ✅ **Archive results regularly** for audit trail
6. ✅ **Test on sample repos first** before production
7. ✅ **Review BRD with stakeholders** before finalization

## Limitations

- **Large Repositories:** 100K+ files may exceed token limits
- **Language Support:** Optimized for Java, other languages supported but limited
- **Real-time Data:** Cannot fetch live API responses or current databases
- **External Services:** Jira/Confluence integration disabled by default
- **Execution Time:** Complex analyses may require 30+ minutes

## Next Steps

1. **Review Configuration**
   - Check `config/config.yaml` settings
   - Verify LLM model preferences
   - Confirm tool availability

2. **Prepare Repository**
   - Upload or select target repository
   - Prepare supporting documents
   - Set output directory

3. **Execute Pipeline**
   - Request Claude to analyze
   - Monitor progress and logs
   - Review artifacts when complete

4. **Validate Results**
   - Check confidence scores
   - Review BRD completeness
   - Share with stakeholders

5. **Iterate & Refine**
   - Provide feedback for improvements
   - Re-run with additional context
   - Customize analysis as needed

## Support & Documentation

**Main Instructions:** `claude-instructions.md`  
**Workflow Guide:** `workflows/full-pipeline.workflow.md`  
**System Prompt:** `prompts/system-prompts/brd-orchestration-system.prompt`  
**Config Reference:** `../config/config.yaml`  
**Logs:** `../logs/pipeline_*.log`

## Feedback & Improvements

Help us improve the Claude BRD Agent:
- Report issues or bugs
- Suggest new capabilities
- Share workflow improvements
- Document lessons learned

---

**Version:** 1.0  
**Created:** 2026-09-17  
**Status:** Production Ready  
**Maintainer:** BRD Agent Team  

**Ready to generate your first BRD with Claude!** 🚀
