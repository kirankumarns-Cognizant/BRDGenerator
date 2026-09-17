# Full BRD Pipeline Workflow

**Objective:** Execute the complete BRD generation pipeline using Claude orchestration across all 9 agents.

**Duration:** 15-30 minutes (depending on repository size)  
**Complexity:** Advanced  
**Prerequisites:** Repository uploaded, documents optional

---

## Workflow Steps

### Step 1: Initiate Pipeline Execution
**Who:** User (via Streamlit UI) or Claude (via command)  
**Action:** Click "▶ Run Pipeline" button

**Expected:**
- Pipeline status changes to "RUNNING"
- Progress tracker appears
- Agent 1 begins execution
- Real-time logs stream to console

**Claude Command:**
```
User: "Analyze the spring-petclinic repository with BRD pipeline"

Claude: "I'll execute the full BRD pipeline for spring-petclinic using all 9 agents."
```

### Step 2: Agent 1 - Discovery & Scoping (claude-3-opus)
**Duration:** 3-5 minutes  
**Task:** Scan repository, catalog artifacts, define scope

**Agent Actions:**
1. Read repository structure from `KB/spring-petclinic/`
2. Identify all Java files, configuration files, and dependencies
3. Extract project metadata (Maven/Gradle, Spring versions, etc.)
4. Document module hierarchy and key components
5. Create dependency graph

**Outputs:**
- `agent_1_scope_definition.json` - Scope, boundaries, out-of-scope items
- `agent_1_artifact_catalog.md` - Complete artifact catalog
- `agent_1_dependency_map.json` - Module dependencies
- `agent_1_output.json` - Complete structured output

**Confidence Tracking:**
- Overall scope confidence: Expected 0.85-0.95
- Flag if < 0.70 for manual review

**Progress Indicator:**
```
🤖 Agent 1: Discovery & Scoping
📊 Model: claude-3-opus | Provider: ANTHROPIC | Complexity: HIGH
⏳ Status: In Progress...
```

### Step 3: Agent 2 - Journey Mapping (claude-3-haiku)
**Duration:** 2-3 minutes  
**Task:** Map user journeys and business processes

**Dependencies:** Requires Agent 1 output (scope_definition, artifact_catalog)

**Agent Actions:**
1. Identify user types and roles from code
2. Trace user journeys through main features
3. Document interaction flows and sequences
4. Create journey maps for key use cases
5. Identify touchpoints and integrations

**Inputs from Agent 1:**
- Scope definition (to understand context)
- Artifact catalog (to locate key components)
- Dependency map (to understand interactions)

**Outputs:**
- `agent_2_journeys.json` - User journey definitions
- `agent_2_flows.md` - Interaction flows and sequences
- `agent_2_output.json` - Complete structured output

**Progress Indicator:**
```
🤖 Agent 2: Journey Mapping
📊 Model: claude-3-haiku | Provider: ANTHROPIC | Complexity: LOW
✅ Completed (2m 34s)
```

### Step 4: Agent 3 - Business Rules (claude-3-haiku)
**Duration:** 2-3 minutes  
**Task:** Extract and document business rules

**Agent Actions:**
1. Identify business logic in code
2. Extract validation rules
3. Document constraints and conditions
4. Map rules to code locations
5. Categorize by business domain

**Outputs:**
- `agent_3_business_rules.json` - Extracted rules
- `agent_3_constraints.md` - Constraints and validations
- `agent_3_output.json` - Complete structured output

### Step 5: Agent 4 - Gap Analysis (claude-3-haiku)
**Duration:** 2-3 minutes  
**Task:** Identify missing requirements and inconsistencies

**Agent Actions:**
1. Compare code to initial requirements
2. Identify undocumented features
3. Flag ambiguous implementations
4. Document gaps and inconsistencies
5. Assess coverage completeness

**Outputs:**
- `agent_4_gaps.json` - Identified gaps
- `agent_4_recommendations.md` - Recommendations
- `agent_4_output.json` - Complete structured output

### Step 6: Agent 5 - Synthesis (claude-3-opus)
**Duration:** 3-5 minutes  
**Task:** Synthesize all outputs into comprehensive BRD

**Complexity:** HIGH - This agent combines all previous outputs

**Agent Actions:**
1. Read outputs from Agents 1-4
2. Synthesize into unified BRD structure
3. Resolve conflicts and overlaps
4. Ensure consistency across sections
5. Create comprehensive narrative

**All Inputs Combined:**
- Scope and artifacts (Agent 1)
- User journeys (Agent 2)
- Business rules (Agent 3)
- Gap analysis (Agent 4)
- Uploaded documents (if provided)

**Outputs:**
- `agent_5_comprehensive_brd.md` - Full BRD document
- `agent_5_brd.json` - Structured BRD data
- `agent_5_output.json` - Complete structured output

### Step 7: Agent 6 - Acceptance Criteria (claude-3-haiku)
**Duration:** 2-3 minutes  
**Task:** Generate test scenarios and acceptance criteria

**Agent Actions:**
1. Derive acceptance criteria from requirements
2. Create test scenarios for each feature
3. Define validation checkpoints
4. Document success criteria
5. Create test matrices

**Outputs:**
- `agent_6_acceptance_criteria.json` - Detailed criteria
- `agent_6_test_scenarios.md` - Test scenarios
- `agent_6_output.json` - Complete structured output

### Step 8: Agent 7 - Risk & Dependencies (claude-3-sonnet)
**Duration:** 2-3 minutes  
**Task:** Identify risks and document dependencies

**Complexity:** MEDIUM - Requires deep analysis

**Agent Actions:**
1. Identify technical risks
2. Assess dependency impacts
3. Document mitigation strategies
4. Create risk matrix
5. Flag critical dependencies

**Outputs:**
- `agent_7_risks.json` - Risk assessment
- `agent_7_dependencies.md` - Dependency documentation
- `agent_7_output.json` - Complete structured output

### Step 9: Agent 8 - Summarizer (claude-3-opus)
**Duration:** 2-3 minutes  
**Task:** Create executive summary and quick reference

**Complexity:** HIGH - Final synthesis

**Agent Actions:**
1. Read comprehensive BRD from Agent 5
2. Extract key points and highlights
3. Create executive summary
4. Generate quick reference guide
5. Highlight critical decisions

**Outputs:**
- `agent_8_executive_summary.md` - Summary document
- `agent_8_quick_reference.json` - Quick reference
- `agent_8_output.json` - Complete structured output

### Step 10: Agent 9 - Knowledge Base Sync (claude-3-haiku)
**Duration:** 1-2 minutes  
**Task:** Store and index all outputs in knowledge base

**Agent Actions:**
1. Store BRD in vector database (ChromaDB)
2. Create embeddings for semantic search
3. Index all artifacts
4. Create KB collections
5. Track document versions

**Outputs:**
- `agent_9_kb_index.json` - KB index
- `agent_9_collections.md` - Collection info
- `agent_9_output.json` - Complete structured output

---

## Monitoring & Tracking

### Real-Time Progress
Watch in Streamlit UI:
```
┌─────────────────────────────────────┐
│  🕐 Pipeline Progress               │
├─────────────────────────────────────┤
│ ✅ Agent 1: Discovery & Scoping     │
│    Model: claude-3-opus             │
│                                     │
│ ✅ Agent 2: Journey Mapping         │
│    Model: claude-3-haiku            │
│                                     │
│ ⏳ Agent 3: Business Rules          │
│    Model: claude-3-haiku            │
│    [████████░░░░░░░░░░] 40%        │
│                                     │
│ ⏱️  Agent 4-9: Pending              │
└─────────────────────────────────────┘
```

### Log Monitoring
```bash
# Watch logs in real-time
tail -f logs/pipeline_execution.log

# Search for specific agent
grep "Agent 3" logs/pipeline_execution.log

# Check for errors
grep "ERROR\|WARN" logs/pipeline_execution.log
```

### Confidence Tracking
```json
{
  "agent_1_confidence": 0.92,
  "agent_2_confidence": 0.88,
  "agent_3_confidence": 0.85,
  "agent_4_confidence": 0.79,
  "agent_5_confidence": 0.90,
  "agent_6_confidence": 0.87,
  "agent_7_confidence": 0.82,
  "agent_8_confidence": 0.91,
  "agent_9_confidence": 0.95,
  "overall_confidence": 0.88
}
```

---

## Post-Pipeline Actions

### Step 11: Artifact Generation
After all agents complete:

1. **Collect Outputs**
   - Combine all agent outputs
   - Create artifact index
   - Generate summary statistics

2. **Create Archives**
   - ZIP all artifacts
   - Create markdown compilation
   - Generate PDF report (if configured)

3. **Upload Results**
   - Store in KB
   - Create download links
   - Update Streamlit UI

### Step 12: Quality Validation
```
Quality Checks:
✅ All agents executed successfully
✅ Overall confidence > 0.7
✅ No critical errors or blockers
✅ All required fields populated
✅ Cross-references validated
✅ KB storage confirmed
```

### Step 13: User Notification
```
Pipeline Completed Successfully!

📊 Summary:
  ├─ Repository: spring-petclinic
  ├─ Execution Time: 18m 45s
  ├─ Overall Confidence: 0.88
  ├─ Total Artifacts: 27
  └─ Status: ✅ SUCCESS

📦 Download Options:
  ├─ BRD_spring-petclinic.pdf
  ├─ All_Artifacts.zip
  └─ Executive_Summary.md

🎯 Key Metrics:
  ├─ Requirements Identified: 143
  ├─ Business Rules Documented: 89
  ├─ User Journeys Mapped: 12
  ├─ Risks Identified: 8
  └─ Coverage Score: 92%
```

---

## Troubleshooting

### Agent Execution Failures

**Issue: Agent times out (> 5 minutes)**
- **Cause:** Repository too large or complex
- **Solution:** 
  1. Check logs for specific error
  2. Retry with smaller repository subset
  3. Increase timeout in config.yaml

**Issue: Low confidence score (< 0.6)**
- **Cause:** Insufficient data or ambiguity
- **Solution:**
  1. Add supporting documents
  2. Manual review and clarification
  3. Re-run with additional context

**Issue: KB storage failure**
- **Cause:** ChromaDB connection or storage issue
- **Solution:**
  1. Verify ChromaDB is running
  2. Check KB directory permissions
  3. Clear cache and retry

### Token/Cost Management

**Monitor Token Usage:**
```python
# Check token usage per agent
python -c "from logs import parse_pipeline_log; print(parse_pipeline_log('logs/pipeline_*.log'))"
```

**Optimize for Cost:**
- Use claude-3-haiku for simple analysis
- Cache intermediate results
- Reuse Agent 1 output for multiple runs

---

## Workflow Completion

**Pipeline Finished:** ✅ All 9 agents executed successfully

**Final Deliverables:**
- ✅ Comprehensive BRD document
- ✅ Business rules and constraints
- ✅ User journey maps
- ✅ Acceptance criteria
- ✅ Risk and dependency analysis
- ✅ Executive summary
- ✅ All artifacts indexed in KB
- ✅ Download packages ready

**Next Steps:**
1. Download and review BRD
2. Share with stakeholders
3. Provide feedback for refinement
4. Use for requirements tracking
5. Reference for development

---

**Workflow Version:** 1.0  
**Created:** 2026-09-17  
**Status:** Operational  
**Maintenance:** Quarterly review recommended
