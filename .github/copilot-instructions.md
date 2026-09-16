# Copilot Instructions

## Project Overview

BRD Agentic Framework - A multi-agent system for generating Business Requirements Documents from Java legacy codebases. Agent 1 (Discovery & Scoping) scans repositories, catalogs artifacts, and produces scope definitions for downstream agents (2-7).

## Project Structure

```
BRD_agent1/
├── .github/agents/          # Copilot agent definitions
│   └── Agent1.agent.md      # Discovery & Scoping agent spec
├── adapters/                 # Tool adapters (Python)
│   ├── gitpython_adapter.py  # Repo scanning (PRIMARY for Agent 1)
│   ├── unstructured_adapter.py # Doc parsing
│   └── stub_adapter.py       # Fallback for disabled tools
├── config.yaml              # All paths, thresholds, tool settings
├── config_loader.py         # Config access utility
├── agent1_runner.py         # Main entry point for Agent 1
└── requirements.txt         # Python dependencies
```

## Agent 1 Tool Chain

| Tool | Adapter | Purpose |
|------|---------|---------|
| `repo_scanner` | `gitpython_adapter.py` | Scan file tree, find configs |
| `doc_parser` | `unstructured_adapter.py` | Parse PDFs, Word docs |
| `jira_loader` | `stub_adapter.py` | (disabled) Jira integration |
| `confluence_loader` | `stub_adapter.py` | (disabled) Confluence integration |

## Key Conventions

### Config-Driven Design
- **Never hardcode paths** - all paths come from `config.yaml`
- Check `config.is_tool_enabled('agent1', 'tool_name')` before using tools
- Disabled tools route to `stub_adapter` automatically

### Confidence Scoring
- All operations return a `confidence` score (0.0-1.0)
- Threshold for low confidence: `config.get_threshold('low_confidence')` (default 0.6)
- Reduce confidence on errors, never raise exceptions

### State Contract
Agent 1 must write these fields before completing:
```python
state["scope_definition"]   # Required - downstream agents need this
state["artifact_catalog"]   # Required
state["dependency_map"]     # Required
state["overall_confidence"] # 0.0-1.0
```

### HITL Triggers
Pause for human input on:
- `ambiguous_scope` - scope boundary unclear
- `low_confidence_artifact` - artifact confidence below threshold

## Running Agent 1

```bash
# Install dependencies
pip install -r requirements.txt

# Run on a repo
python agent1_runner.py /path/to/java/repo

# Or set path in config.yaml and run
python agent1_runner.py --config config.yaml
```

## Adding New Agents

1. Create `.github/agents/Agent<N>.agent.md` with YAML frontmatter
2. Add adapter in `adapters/` if new tools needed
3. Register tools in `config.yaml` under `agents.agent<n>.tools`
4. Create `agent<n>_runner.py` following Agent 1 pattern
