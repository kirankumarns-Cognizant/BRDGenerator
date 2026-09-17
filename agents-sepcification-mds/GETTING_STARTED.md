# Getting Started — Backlog Grooming and Jira Story Agent

Agent 2 of the SDLC Agentic Framework. Takes a BRD (or any requirements document)
and produces a granular developer-ready backlog (epics → user stories → tasks) plus
Jira-ready records.

---

## 1. Prerequisites

- **Python 3.9+**
- Dependencies already installed (verify with `pip3 show langgraph`)
- A BRD file in Word (`.docx`), PDF, Markdown, or plain text format

If not installed:
```bash
pip3 install -r requirements.txt
```

---

## 2. LLM Setup — choose one

### Option A: Claude (Anthropic API key)

Open `.env` in the project root and paste your key:
```
ANTHROPIC_API_KEY=your_key_here
```
No other changes needed. At startup the agent will ask which LLM to use — choose **2 (Claude)**.

### Option B: Copilot (via VS Code gateway — no API key)

1. Open VS Code
2. Open Command Palette (`Cmd+Shift+P`) → **Copilot API: Controls**
3. Enable the server (it runs on port 3030)
4. At startup choose **1 (Copilot proxy)**

---

## 3. One-time initialization

```bash
cd /Users/agraga5/Desktop/Garima/Story/requirement-breakdown-agent
python3 main.py init
```

Creates all required folders under `data/`.

---

## 4. Place your BRD

Copy your BRD file into the BRD store:
```bash
cp /path/to/YourBRD.docx data/brd_store/
```

Supported formats: `.docx`, `.pdf`, `.md`, `.txt`, `.xlsx`, `.csv`

---

## 5. Running the agent

### All commands at a glance

```
python3 main.py {init,run,list,jira-meta,latest}
```

| Command | What it does |
|---|---|
| `init` | Create data folders |
| `run` | Run grooming and/or Jira breakdown |
| `list` | List all sessions |
| `jira-meta` | Show Jira field profile and unmapped custom-field IDs |
| `latest` | Show workspace status, latest paths, and quick-use commands |

---

### `run` — main command

```bash
python3 main.py run "Feature Name" [options]
```

**Positional:**

| Argument | Description |
|---|---|
| `feature` | Short label for the feature (e.g. `"WCF WFM"`) |

**Options:**

| Flag | Description |
|---|---|
| `--brd FILENAME` | BRD filename from `data/brd_store/` to use (repeatable) |
| `--mode {groom,jira,both}` | What to run. Asked interactively if omitted |
| `--no-resume` | Force a fresh session even if one exists for this BRD |
| `--stage {brd,breakdown}` | `brd` = start from BRD (default); `breakdown` = ingest existing breakdown |
| `--breakdown FILE` | Path to grooming JSON (for `--mode jira`) or existing breakdown doc (for `--stage breakdown`) |
| `--feature-key KEY` | Explicit workspace key (auto-derived from BRD name if omitted) |
| `--jira-project KEY` | Jira project key, default `VNQE` |

---

### Typical workflows

#### Full run from a BRD (grooming → Jira)

```bash
python3 main.py run "WCF WFM" --mode groom --brd WCF_WFM_Comprehensive_BRD_V3.docx
```

The agent will ask:
1. **LLM choice** — `1` Copilot or `2` Claude
2. **Grooming review** — type change requests or `approve` to sign off
3. **Continue to Jira?** — `yes` to generate Jira records, `no` to finish

#### Groom only (no Jira step)

```bash
python3 main.py run "WCF WFM" --mode groom --brd WCF_WFM_Comprehensive_BRD_V3.docx
```
Reply `approve` when satisfied. Saves `grooming_v1.json` and `grooming_v1.md` under
`data/breakdowns/<feature>/`.

#### Jira breakdown only (from a previous grooming run)

```bash
# Use the always-current latest link:
python3 main.py run "WCF WFM" --mode jira --breakdown data/breakdowns/wcf-wfm/grooming_latest.json

# Or target a specific version:
python3 main.py run "WCF WFM" --mode jira --breakdown data/breakdowns/wcf-wfm/grooming_v1.json
```
Important: the folder segment after `data/breakdowns/` is workspace-dependent and
can change (for example `wcf-wfm` vs `wcf-wfm-comprehensive-brd-v3`) based on BRD
name/feature key and session history. If unsure, run `python3 main.py latest` and
copy the exact path shown there.

Reply `push` to create issues in Jira or `skip` to finish without pushing.

#### Force a fresh run (ignore existing session)

```bash
python3 main.py run "WCF WFM" --no-resume --mode groom --brd WCF_WFM_Comprehensive_BRD_V3.docx
```

#### Resume an existing in-progress session

```bash
# Without --no-resume the agent detects the prior session and asks:
# 1. Continue existing session
# 2. Start a new run in the same workspace
python3 main.py run "WCF WFM" --brd WCF_WFM_Comprehensive_BRD_V3.docx
```

#### Ingest an existing breakdown document

```bash
python3 main.py run "WCF WFM" --stage breakdown --breakdown ./existing_backlog.md
```
Agent assesses granularity and asks permission before decomposing further.

---

### `latest` — workspace status

Shows all sessions, grooming paths, Jira paths, and ready-to-paste quick commands.
Use this whenever a previously used path no longer works; it prints the current
canonical paths for each workspace.

```bash
# All workspaces
python3 main.py latest

# One specific workspace
python3 main.py latest --feature-key wcf-wfm
```

Example output:
```
============================================================
  Workspace: wcf-wfm
============================================================
  Session ID : sess-abc123
  Title      : WCF WFM
  Phase      : signoff
  Updated    : 2026-07-30T18:00:00Z
  BRD(s)     : WCF_WFM_Comprehensive_BRD_V3.docx
  Grooming files:
    Latest JSON : data/breakdowns/wcf-wfm/grooming_latest.json
    Latest MD   : data/breakdowns/wcf-wfm/grooming_latest.md
    Versions    : grooming_v1.json
    Signed      : wcf-wfm_v1_signed.md
  Jira files:
    Latest combined : data/jira/wcf-wfm/combined_latest.json
    Latest preview  : data/jira/wcf-wfm/jira_preview_latest.md
    Run folders     : run_v1
  Workspace archive: data/workspaces/wcf-wfm
  Quick commands:
    Jira-only run  : python3 main.py run 'wcf-wfm' --mode jira --breakdown data/breakdowns/wcf-wfm/grooming_latest.json
    New groom run  : python3 main.py run 'wcf-wfm' --no-resume --mode groom
```

---

### `list` — session list

```bash
python3 main.py list
```

### `jira-meta` — Jira field mapping

```bash
python3 main.py jira-meta
```
Shows which Jira custom field IDs still need to be mapped in `config.yaml` before a
real REST/MCP push.

---

## 6. What the agent produces

Note: `<feature>` below is the computed workspace key, not always your display
title, so output paths can change between BRDs/runs.

| Output | Location |
|---|---|
| Grooming JSON (all runs) | `data/breakdowns/<feature>/grooming_v1.json`, `grooming_v2.json`, … |
| Grooming Markdown (all runs) | `data/breakdowns/<feature>/grooming_v1.md`, … |
| Latest grooming (always current) | `data/breakdowns/<feature>/grooming_latest.json` / `.md` |
| Signed breakdown | `data/breakdowns/<feature>_v1_signed.md` |
| Jira records per run | `data/jira/<feature>/run_v1/` (per-item JSON + combined + preview) |
| Latest Jira combined | `data/jira/<feature>/combined_latest.json` |
| Latest Jira preview | `data/jira/<feature>/jira_preview_latest.md` |
| Full run archive | `data/workspaces/<feature>/run_v1/` (BRD + breakdown + Jira) |
| Agent traces | `data/traces/<session_id>/` |

---

## 7. Multiple BRDs / workspaces

Each BRD automatically gets its own workspace keyed from the BRD filename. For example:

```bash
# BRD 1
python3 main.py run "WCF WFM" --brd WCF_WFM_Comprehensive_BRD_V3.docx
# → workspace: wcf-wfm-comprehensive-brd-v3

# BRD 2
python3 main.py run "My Other Feature" --brd OtherFeature_BRD.docx
# → workspace: otherfeature-brd
```

Use `python3 main.py latest` to see all workspaces side by side.

---

## 8. Review prompts during a run

| What you type | Effect |
|---|---|
| Any text | Revision request — agent regenerates with your feedback |
| `approve` | Sign off the current output and advance |
| `yes` | Continue to Jira breakdown (after grooming sign-off, in BOTH mode) |
| `no` | Finish without Jira breakdown |
| `push` | Create issues in Jira (dry-run by default unless publisher changed) |
| `skip` | Finish without pushing to Jira |
| `/exit` or `/quit` | Exit the session (work is auto-saved) |
| `/attach path` | Attach a file inline: `some text /attach ./file.md` |

---

## 9. Config reference

Key settings in `config.yaml`:

```yaml
llm:
  provider: openai          # openai (local Copilot gateway) | anthropic | mock
  model: gpt-5.4            # or claude-sonnet-4.6
  proxy_url: http://127.0.0.1:3030/v1   # Copilot gateway port

brd:
  store_dir: data/brd_store  # drop BRD files here
  glob_patterns:
    - "**/*.docx"
    - "**/*.pdf"
    - "**/*.md"
    - "**/*.txt"

planning:
  velocity_points_per_iteration: 13
  days_per_iteration: 10
  default_story_points: 3

jira:
  publisher: dryrun          # dryrun | rest | mcp
  base_url: https://onejira.verizon.com
  profile:
    project_key: VNQE
```

Environment variables in `.env` override `config.yaml` at runtime:

```
ANTHROPIC_API_KEY=sk-...       # Claude API key
RBK_LLM_PROVIDER=anthropic     # override provider
RBK_LLM_MODEL=claude-sonnet-4.6
```

---

## 10. Web UI (optional)

```bash
python3 main.py serve
# Open http://127.0.0.1:8081
```
