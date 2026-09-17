# Claude Quick Reference Guide

## 🚀 Quick Start for Claude

### 1. Generate Full BRD in One Command

```
"Analyze the spring-petclinic repository and generate a complete BRD"
```

Claude will:
1. ✅ Execute all 9 agents sequentially
2. ✅ Track execution with models used
3. ✅ Generate comprehensive BRD document
4. ✅ Store results in knowledge base
5. ✅ Provide download links

### 2. View Model Configuration

Each agent uses optimal LLM model:

```
Agent 1: Discovery & Scoping        → claude-3-opus      (HIGH)
Agent 2: Journey Mapping             → claude-3-haiku     (LOW)
Agent 3: Business Rules              → claude-3-haiku     (LOW)
Agent 4: Gap Analysis                → claude-3-haiku     (LOW)
Agent 5: Synthesis                   → claude-3-opus      (HIGH)
Agent 6: Acceptance Criteria         → claude-3-haiku     (LOW)
Agent 7: Risk & Dependencies         → claude-3-sonnet    (MEDIUM)
Agent 8: Summarizer                  → claude-3-opus      (HIGH)
Agent 9: KB Sync                     → claude-3-haiku     (LOW)
```

### 3. Execute in Python

```python
from .claude.claude_runner import execute_pipeline

# Full pipeline execution
result = execute_pipeline("KB/spring-petclinic", ["spec.pdf"])

# Check result
if result["status"] == "SUCCESS":
    print(f"✅ BRD generated: {result['output_dir']}")
    print(f"   Artifacts: {len(result['artifacts'])} files")
    print(f"   Confidence: {result.get('confidence', 'N/A')}")
```

### 4. Execute Individual Agent

```python
from .claude.claude_runner import execute_single_agent

# Run Agent 1 only
result = execute_single_agent(1, "KB/spring-petclinic")

# Run Agent 3 (Business Rules)
result = execute_single_agent(3, "KB/spring-petclinic")
```

---

## 📋 Common Claude Requests

### Request 1: Full BRD Analysis
```
"I need a comprehensive Business Requirements Document for my 
spring-petclinic application. Please analyze the code and generate 
a complete BRD with all requirements, business rules, user journeys, 
acceptance criteria, and risk assessment."
```

**Claude will:**
- Execute Agents 1-9 in sequence
- Generate 25+ artifacts
- Produce professional BRD document
- Store in knowledge base
- **Time: 15-30 minutes**
- **Confidence: Target > 0.85**

### Request 2: Specific Domain Analysis
```
"Focus on the payment processing module in my repository. 
What are the key business rules, acceptance criteria, 
and what gaps might exist compared to industry standards?"
```

**Claude will:**
- Run focused Agent 3 (Business Rules)
- Run focused Agent 4 (Gap Analysis)
- Run focused Agent 6 (Acceptance Criteria)
- Synthesize findings
- **Time: 5-10 minutes**

### Request 3: Document-Informed Analysis
```
"We have a requirements specification document and legacy code. 
Compare them and identify what's implemented, what's missing, 
and any inconsistencies between spec and code."
```

**Claude will:**
- Parse specification document
- Scan legacy codebase
- Run Agent 4 (Gap Analysis)
- Document all findings
- **Time: 10-15 minutes**

### Request 4: Risk & Security Analysis
```
"Analyze the architecture and identify technical risks, 
security concerns, and critical dependencies. What should 
development teams be aware of?"
```

**Claude will:**
- Run Agent 7 (Risk & Dependencies)
- Identify vulnerabilities
- Document critical dependencies
- Provide mitigation strategies
- **Time: 5-8 minutes**

---

## 🔍 Monitoring Pipeline Execution

### Real-Time Progress (Streamlit UI)
```
📄 Pipeline Execution
├─ ✅ Agent 1: Discovery & Scoping
│  └─ Model: claude-3-opus | Time: 4m 23s
├─ ✅ Agent 2: Journey Mapping
│  └─ Model: claude-3-haiku | Time: 2m 15s
├─ ⏳ Agent 3: Business Rules
│  └─ Model: claude-3-haiku | Progress: 45%
└─ ⏱️ Agents 4-9: Pending
```

### Command Line Logs
```bash
# Watch real-time logs
tail -f logs/pipeline_execution.log

# Search for specific agent
grep "Agent 3" logs/pipeline_execution.log

# Check confidence scores
grep "confidence" logs/pipeline_execution.log
```

### Python Status Check
```python
from .claude.claude_runner import ClaudeRunner

runner = ClaudeRunner()
status = runner.get_pipeline_status()
print(f"Current Status: {status['status']}")
print(f"Current Agent: {status.get('current_agent', 'N/A')}")
```

---

## 📊 Expected Output

### Final BRD Contains
- ✅ Executive Summary
- ✅ Scope Definition
- ✅ 50-200+ Requirements
- ✅ 30-100+ Business Rules
- ✅ 5-15 User Journeys
- ✅ Acceptance Criteria for all features
- ✅ Risk Assessment with mitigation
- ✅ Technical Dependencies
- ✅ Implementation Roadmap
- ✅ Quality Metrics

### Artifacts Generated
```
KB/repo_name/artifacts/
├── agent_1_scope_definition.json
├── agent_2_journeys.json
├── agent_3_business_rules.json
├── agent_4_gaps_and_analysis.json
├── agent_5_comprehensive_brd.md
├── agent_6_acceptance_criteria.json
├── agent_7_risks_dependencies.json
├── agent_8_executive_summary.md
├── agent_9_kb_index.json
├── pipeline_summary.md
├── BRD_final.pdf
└── All_Artifacts.zip
```

---

## ⚙️ Configuration Management

### View Current Configuration
```bash
cat config/config.yaml
```

### Verify Models Available
```bash
python verify_agent_models.py
```

### Example Config Extract
```yaml
llm:
  providers:
    anthropic:
      available_models:
        - claude-3-opus
        - claude-3-sonnet
        - claude-3-haiku
        - claude-3.5-sonnet
        - claude-3.5-haiku

agents:
  agent1:
    model: claude-3-opus
    provider: anthropic
    complexity: HIGH
    task: "Discovery & Scoping"
```

---

## 🛠️ Troubleshooting

### Issue: Pipeline Times Out (>60 min)
```
Solution:
1. Check repository size: ls -lR KB/repo_name | wc -l
2. If > 10K files, use haiku models for analysis
3. Split into focused analyses instead of full pipeline
```

### Issue: Low Confidence Scores (<0.6)
```
Solution:
1. Add supporting documents with requirements specs
2. Provide manual clarifications for ambiguous code
3. Re-run with refined inputs
4. Check logs for specific issues
```

### Issue: Knowledge Base Storage Fails
```
Solution:
1. Verify ChromaDB running: ps aux | grep chroma
2. Check KB permissions: ls -ld kb_store
3. Clear cache: rm -rf kb_store/cache
4. Restart storage service
```

---

## 📞 Support Commands

### Check Pipeline Health
```bash
# Validate configuration
python -c "from .claude.claude_runner import ClaudeRunner; ClaudeRunner().validate_config()"

# View model mappings
python verify_agent_models.py

# Check recent logs
tail -20 logs/pipeline_*.log
```

### Debug Information
```bash
# Get detailed execution info
grep -E "Agent|Model|Confidence|Time" logs/pipeline_execution.log

# Extract metrics
python -c "
import json
with open('KB/repo/artifacts/pipeline_metrics.json') as f:
    metrics = json.load(f)
    print(f'Confidence: {metrics[\"overall_confidence\"]:.2%}')
    print(f'Execution Time: {metrics[\"total_time_seconds\"]}s')
"
```

### Reset and Restart
```bash
# Clear previous execution
rm -rf KB/repo_name/artifacts/*

# Re-run pipeline
from .claude.claude_runner import execute_pipeline
execute_pipeline("KB/repo_name")
```

---

## 💡 Best Practices

1. **Start Simple**
   - Begin with small repositories
   - Add documents gradually
   - Test one agent at a time

2. **Monitor Progress**
   - Watch confidence scores
   - Review logs regularly
   - Check artifact generation

3. **Validate Results**
   - Review BRD completeness
   - Check for inconsistencies
   - Share with stakeholders

4. **Optimize Performance**
   - Use haiku for simple tasks
   - Reuse Agent 1 outputs
   - Cache expensive operations

5. **Maintain Quality**
   - Set confidence threshold > 0.6
   - Escalate low-confidence items
   - Document assumptions

---

## 📚 Resource Links

| Resource | Location |
|----------|----------|
| **Main Instructions** | `.claude/claude-instructions.md` |
| **Full Workflow** | `.claude/workflows/full-pipeline.workflow.md` |
| **System Prompt** | `.claude/prompts/system-prompts/brd-orchestration-system.prompt` |
| **Configuration** | `config/config.yaml` |
| **Python Runner** | `.claude/claude_runner.py` |
| **Logs** | `logs/pipeline_*.log` |
| **Outputs** | `KB/{repo_name}/artifacts/` |

---

## 🎯 Next Actions

### For Immediate Use
1. ✅ Copy system prompt to Claude context
2. ✅ Request: "Analyze [repo] and generate BRD"
3. ✅ Monitor progress and logs
4. ✅ Download artifacts when complete

### For Advanced Usage
1. ✅ Review `claude-instructions.md`
2. ✅ Study workflow documentation
3. ✅ Customize prompts for your domain
4. ✅ Integrate with CI/CD pipeline

### For Production Deployment
1. ✅ Set up monitoring and alerts
2. ✅ Configure knowledge base persistence
3. ✅ Create backup strategy
4. ✅ Document team workflows

---

**Ready to generate your first BRD!** 🚀

```
Claude: "Analyze spring-petclinic and generate a complete BRD"
```

---

**Version:** 1.0  
**Created:** 2026-09-17  
**Status:** Production Ready
