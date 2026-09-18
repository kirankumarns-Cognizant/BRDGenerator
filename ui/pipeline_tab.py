"""
Capability 1: Pipeline Execution
Allows users to select a repository, run the BRD pipeline, monitor progress,
browse generated artifacts, and download outputs as a ZIP.
"""

import io
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

# Initialize session state at module load time
if "_agents_completed" not in st.session_state:
    st.session_state._agents_completed = []
if "_agents_failed" not in st.session_state:
    st.session_state._agents_failed = []
if "_current_agent" not in st.session_state:
    st.session_state._current_agent = None
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "pipeline_log_lines" not in st.session_state:
    st.session_state.pipeline_log_lines = []

# Import model selector for displaying which model each agent uses
try:
    from config.llm_selector import LLMSelector
except ImportError:
    LLMSelector = None

_MERMAID_BLOCK = re.compile(r"```mermaid[^\S\n]*\n(.*?)```", re.DOTALL)

# Python agent scripts in execution order (LLM-powered versions)
_AGENT_SCRIPTS = [
    ("Agent 1: Discovery & Scoping",        "agent-1-discovery/agent_1_discovery_llm.py"),
    ("Agent 2: Journey Mapping",            "agent-2-journey-mapping/agent_2_journey_mapping_llm.py"),
    ("Agent 3: Business Rules",             "agent-3-business-rules/agent_3_business_rules_llm.py"),
    ("Agent 4: Gap Analysis",               "agent-4-gap-analysis/agent_4_gap_analysis_llm.py"),
    ("Agent 5: Synthesis",                  "agent-5-synthesis/agent_5_synthesis_llm.py"),
    ("Agent 6: Acceptance Criteria",        "agent-6-acceptance-criteria/agent_6_acceptance_criteria_llm.py"),
    ("Agent 7: Risk & Dependency",          "agent-7-risk-dependency/agent_7_risk_dependency_llm.py"),
    ("Agent 8: BRD Summarizer",             "agent-8-summarizer/agent_8_summarizer_llm.py"),
    ("Agent 9: KB Store Sync",              "agent-9-kb-store-sync/agent_9_kb_store_sync_llm.py"),
]


def _utf8_env() -> dict:
    """Return a copy of the current environment with PYTHONIOENCODING=utf-8.
    Prevents UnicodeEncodeError when agent scripts print emoji on Windows (cp1252)."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _start_pipeline(repo_path: str, project_root: Path) -> None:
    """Run each agent .py script sequentially in a background thread."""
    repo_name = Path(repo_path).name
    kb_output = str(project_root / "KB" / repo_name)
    skills_root = project_root / ".github" / "skills"
    st.session_state["_pending_hypergraph_regen"] = True
    st.session_state["_hypergraph_regenerated"] = False

    q: queue.Queue = queue.Queue()
    # Shared with the worker thread so Stop can reach the live subprocess.
    # Session state isn't safe to mutate from a thread without a script context.
    control = {"proc": None, "stop": threading.Event()}
    api_key = st.session_state.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")

    st.session_state._pipeline_queue = q
    st.session_state._pipeline_control = control
    st.session_state.pipeline_running = True
    st.session_state.pipeline_log_lines = []
    st.session_state._agents_completed = []
    st.session_state._agents_failed = []
    st.session_state._current_agent = None
    st.session_state["_run_finalized"] = False

    def _run_agents():
        for idx, (name, rel_script) in enumerate(_AGENT_SCRIPTS):
            if control["stop"].is_set():
                q.put("[STOPPED] Pipeline cancelled.\n")
                break

            # Get model info for this agent
            agent_num = idx + 1
            model_info = None
            if LLMSelector:
                try:
                    model_config = LLMSelector.get_model_for_agent(agent_num)
                    model_info = {
                        "model": model_config.get("model", "N/A"),
                        "provider": model_config.get("provider", "anthropic").upper(),
                        "complexity": model_config.get("complexity", "N/A"),
                    }
                except:
                    pass
            
            # Send status update via queue with model info
            q.put(json.dumps({
                "__status": "agent_start",
                "name": name,
                "index": idx,
                "model_info": model_info
            }))

            script_path = skills_root / rel_script

            if not script_path.exists():
                q.put(f"[SKIP] {name} — script not found: {script_path}\n")
                q.put(json.dumps({"__status": "agent_end", "name": name, "agent_status": "skipped"}))
                continue

            q.put(f"\n{'='*48}\n  {name}\n{'='*48}\n")
            # LLM agents use --output and --api-key (not --config)
            cmd = [
                "python", str(script_path),
                repo_path,
                "--output", kb_output,
            ]
            if api_key:
                cmd.extend(["--api-key", api_key])
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=_utf8_env(),
                    cwd=str(project_root),
                )
                control["proc"] = proc
                for line in proc.stdout:
                    q.put(line)
                proc.wait()
                control["proc"] = None
                status = "OK" if proc.returncode == 0 else f"EXIT {proc.returncode}"
                q.put(f"[{status}] {name}\n")
                agent_status = "completed" if proc.returncode == 0 else "failed"
                # Send end status BEFORE sentinel with model info
                q.put(json.dumps({
                    "__status": "agent_end",
                    "name": name,
                    "agent_status": agent_status,
                    "model_info": model_info
                }))
            except Exception as exc:
                q.put(f"[ERROR] {name}: {exc}\n")
                q.put(json.dumps({
                    "__status": "agent_end",
                    "name": name,
                    "agent_status": "error",
                    "model_info": model_info
                }))

        q.put(None)  # sentinel

    t = threading.Thread(target=_run_agents, daemon=True)
    t.start()


def _regenerate_hypergraph(project_root: Path) -> tuple[bool, str]:
    """Rebuild KB/graph/hypergraph.json from the current KB contents."""
    script = project_root / "generate_hypergraph.py"
    kb_dir = project_root / "KB"
    out = project_root / "KB" / "graph" / "hypergraph.json"
    domain_config = project_root / "domain_config.json"

    cmd = [
        sys.executable,
        str(script),
        "--kb",
        str(kb_dir),
        "--out",
        str(out),
    ]
    if domain_config.is_file():
        cmd.extend(["--domain-config", str(domain_config)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(project_root),
    )
    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, (result.stdout + result.stderr).strip()


def _drain_queue() -> bool:
    """Drain pending log lines from queue. Returns True if process still running."""
    q: queue.Queue = st.session_state.get("_pipeline_queue")
    if q is None:
        return False

    still_running = True
    batch: list[str] = []
    while True:
        try:
            item = q.get_nowait()
        except queue.Empty:
            break
        if item is None:
            still_running = False
            break

        # Check if this is a status message (JSON with __status key)
        if isinstance(item, str) and item.startswith("{") and '"__status"' in item:
            try:
                msg = json.loads(item)
                if msg.get("__status") == "agent_start":
                    st.session_state._current_agent = {
                        "index": msg.get("index"),
                        "name": msg.get("name"),
                        "status": "running",
                        "model_info": msg.get("model_info")
                    }
                elif msg.get("__status") == "agent_end":
                    agent_name = msg.get("name", "")
                    agent_status = msg.get("agent_status", "unknown")
                    if st.session_state._current_agent:
                        st.session_state._current_agent["status"] = agent_status
                        st.session_state._current_agent["model_info"] = msg.get("model_info")
                    # "completed" here means finished, not succeeded — it drives
                    # the progress bar. Failures are tracked separately so the
                    # final message can be red rather than green.
                    if agent_name not in st.session_state._agents_completed:
                        st.session_state._agents_completed.append(agent_name)
                    if agent_status in ("failed", "error") and agent_name not in st.session_state._agents_failed:
                        st.session_state._agents_failed.append(agent_name)
                continue
            except json.JSONDecodeError:
                pass

        # Also detect completion from log messages like "[OK] Agent X: ..."
        text_item = str(item).rstrip()
        if text_item.startswith("[OK] Agent "):
            # Extract agent name from "[OK] Agent X: Description"
            for agent_name, _ in _AGENT_SCRIPTS:
                if agent_name in text_item:
                    if agent_name not in st.session_state._agents_completed:
                        st.session_state._agents_completed.append(agent_name)
                    break

        batch.append(text_item)

    if batch:
        current = st.session_state.pipeline_log_lines
        current.extend(batch)
        # Cap at 500 lines
        if len(current) > 500:
            st.session_state.pipeline_log_lines = current[-500:]

    if not still_running:
        st.session_state.pipeline_running = False
        # Drop the exhausted queue. The sentinel only arrives once, so leaving it
        # in place would make every later call report "still running" again and
        # spin the page in a 0.3s rerun loop.
        st.session_state._pipeline_queue = None

    return still_running


def _render_progress_tracker() -> None:
    """Display agent progress tracker with completion status and model info."""
    completed = st.session_state.get("_agents_completed", [])
    current = st.session_state.get("_current_agent")

    total = len(_AGENT_SCRIPTS)
    completed_count = len(completed)

    # Count current running agent in progress if not yet completed
    running_count = 0
    if current and current.get("name") not in completed:
        running_count = 1

    # Total progress includes completed + currently running
    active_count = completed_count + running_count

    # Progress bar with better visibility
    # Show proportion of (completed + currently running) / total
    progress_pct = active_count / total if total > 0 else 0
    st.progress(progress_pct, text=f"**Pipeline Progress:** {active_count}/{total} agents")

    # Current agent status with model info
    if current:
        status_icon = {
            "running": "⏳",
            "completed": "✅",
            "failed": "❌",
            "skipped": "⊘",
            "error": "⚠️"
        }.get(current.get("status", "running"), "⏳")

        agent_name = current.get('name', 'Unknown')
        is_running = current.get("status") == "running"
        label = "Current Agent" if is_running else "Last Agent"

        # Display agent and model info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"{status_icon} **{label}:** {agent_name}")
        
        # Display model info if available
        model_info = current.get("model_info")
        if model_info:
            with col2:
                with st.container(border=True):
                    st.markdown("**🤖 Model Info**")
                    model = model_info.get("model", "N/A")
                    provider = model_info.get("provider", "N/A")
                    complexity = model_info.get("complexity", "N/A")
                    
                    st.caption(f"**Model:** `{model}`")
                    st.caption(f"**Provider:** {provider}")
                    st.caption(f"**Complexity:** {complexity}")

        # Add timeout warning if agent has been running too long
        if is_running:
            st.caption("⏱️ *Agent is processing... This may take several minutes with large documents*")


def _kb_repo_dir(repo_name: str, project_root: Path) -> Path | None:
    d = project_root / "KB" / repo_name
    return d if d.is_dir() else None


def _render_brd_viewer(kb_dir: Path) -> None:
    """Render the comprehensive BRD markdown and its Mermaid diagrams."""
    brd_files = sorted(kb_dir.glob("COMPREHENSIVE_BRD_*.md"))
    if not brd_files:
        st.caption("No comprehensive BRD yet. Run the pipeline to generate one.")
        return

    brd_file = brd_files[0]
    text = brd_file.read_text(encoding="utf-8", errors="replace")
    stat = brd_file.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    diagrams = _MERMAID_BLOCK.findall(text)

    st.subheader("Comprehensive BRD")
    st.caption(f"{brd_file.name} — {_format_size(stat.st_size)} — generated {mtime}")

    st.download_button(
        "⬇ Download BRD (Markdown)",
        data=text.encode("utf-8"),
        file_name=brd_file.name,
        mime="text/markdown",
        key=f"download_brd_{stat.st_mtime}",
    )

    views = ["Document", f"Diagrams ({len(diagrams)})", "Raw markdown"]
    view = st.segmented_control(
        "BRD view",
        views,
        default=views[0],
        required=True,
        label_visibility="collapsed",
        key="brd_view",
    )

    if view == views[2]:
        st.code(text, language="markdown")
    elif view == views[1]:
        if not diagrams:
            st.caption("This BRD contains no Mermaid diagrams.")
        for i, diagram in enumerate(diagrams, 1):
            st.caption(f"Diagram {i} of {len(diagrams)}")
            st.mermaid_chart(diagram.strip())
    else:
        # Fenced ```mermaid blocks render as diagrams inside st.markdown.
        st.markdown(text)


def _resolve_repo_path(repo_name: str, project_root: Path) -> str:
    """Resolve selected repo name to an existing path."""
    roots = [
        project_root / "Sample-repos",
        project_root / "Sample_Repos",
        project_root / "SampleRepos",
        project_root / "KB",
    ]

    # Exact folder match first.
    for root in roots:
        candidate = root / repo_name
        if candidate.is_dir():
            return str(candidate)

    # Case-insensitive match fallback.
    lookup = repo_name.lower()
    for root in roots:
        if not root.is_dir():
            continue
        for d in root.iterdir():
            if d.is_dir() and d.name.lower() == lookup:
                return str(d)

    return ""


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    return f"{size/1024/1024:.1f} MB"


def _save_uploaded_documents(repo_name: str, project_root: Path) -> bool:
    """Save uploaded documents to the KB repository directory."""
    uploaded_docs = st.session_state.get("uploaded_documents", [])
    if not uploaded_docs:
        return True  # No documents to save

    kb_dir = project_root / "KB" / repo_name
    kb_dir.mkdir(parents=True, exist_ok=True)

    # Create a documents subdirectory
    docs_dir = kb_dir / "_uploaded_documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    try:
        for doc_info in uploaded_docs:
            file_obj = doc_info["file"]
            file_path = docs_dir / file_obj.name
            with open(file_path, "wb") as f:
                f.write(file_obj.getbuffer())
        return True
    except Exception as e:
        st.error(f"Pipeline not started — could not save supporting documents: {e}")
        return False


def render(project_root: Path) -> None:
    # Make tab text orange (matching visualization)
    st.markdown("""
    <style>
    [data-baseweb="tab"] {
        color: #FF9500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("📄 Pipeline Execution")

    repo_name: str | None = st.session_state.get("selected_repo")
    if not repo_name:
        st.info("Select a repository from the sidebar to get started.")
        return

    # ── Resolve repo path ────────────────────────────────────────────────────
    # Priority: sample repo folders > KB/<name> > manual input.
    resolved_repo_path = _resolve_repo_path(repo_name, project_root)

    # Keep text input synced when repository selection changes.
    if st.session_state.get("_repo_path_for_selected") != repo_name:
        st.session_state["repo_path_input"] = resolved_repo_path
        st.session_state["_repo_path_for_selected"] = repo_name

    repo_path = st.session_state.get("repo_path_input", resolved_repo_path)

    repo_path = st.text_input("Repository path", value=repo_path, key="repo_path_input",
                               help="Absolute path to the repository to analyze.")

    # ── Drain pipeline output ────────────────────────────────────────────────
    # Must happen before the progress tracker renders, otherwise the tracker
    # draws last rerun's state and a finished agent still reads as running.
    streaming = st.session_state.get("pipeline_running", False) or bool(st.session_state.pipeline_log_lines)
    still_running = _drain_queue() if streaming else False

    # Nothing can be mid-flight once the pipeline stops. A stopped or crashed
    # run emits no agent_end, so clear any left-over running state.
    if not still_running:
        current_agent = st.session_state.get("_current_agent")
        if current_agent and current_agent.get("status") == "running":
            st.session_state._current_agent = None

    # ── Progress tracker (always visible when running) ──────────────────────────
    if st.session_state.get("_current_agent") or st.session_state.get("_agents_completed"):
        st.divider()
        _render_progress_tracker()
        st.divider()

    # ── Run / Stop controls ───────────────────────────────────────────────────
    running = st.session_state.get("pipeline_running", False)
    ready_for_pipeline = st.session_state.get("repo_ready_for_pipeline", False)
    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        run_button_disabled = running or not ready_for_pipeline
        run_clicked = st.button("▶ Run Pipeline", disabled=run_button_disabled, type="primary")
        if not ready_for_pipeline:
            st.caption("⏳ Complete document decision in sidebar first")
    with c2:
        stop_clicked = st.button("⏹ Stop", disabled=not running)

    if run_clicked and repo_path:
        # A save failure must block the run, and skipping st.rerun() is what
        # keeps its error message on screen.
        docs_ok = (
            _save_uploaded_documents(repo_name, project_root)
            if st.session_state.get("uploaded_documents")
            else True
        )
        if docs_ok:
            _start_pipeline(repo_path, project_root)
            st.rerun()

    if stop_clicked:
        control = st.session_state.get("_pipeline_control")
        if control:
            # Flag first so the worker won't start the next agent, then kill
            # the agent currently running.
            control["stop"].set()
            proc = control["proc"]
            if proc:
                proc.terminate()
        st.session_state.pipeline_running = False
        st.session_state._pipeline_queue = None
        st.session_state["_pending_hypergraph_regen"] = False
        st.session_state._current_agent = None
        st.rerun()

    # ── Log streaming ─────────────────────────────────────────────────────────
    if streaming:
        log_placeholder = st.empty()
        lines = st.session_state.pipeline_log_lines
        log_placeholder.code("\n".join(lines[-200:]) if lines else "Starting…", language="text")

        if still_running:
            time.sleep(0.3)
            st.rerun()
        elif lines:
            # Finalise once. This branch is re-entered on every later rerun
            # because the log lines persist, and repeating these writes would
            # keep clearing the sidebar's document decision so it never sticks.
            if not st.session_state.get("_run_finalized"):
                st.session_state["_run_finalized"] = True

                if st.session_state.get("_pending_hypergraph_regen"):
                    ok, message = _regenerate_hypergraph(project_root)
                    st.session_state["_pending_hypergraph_regen"] = False
                    st.session_state["_hypergraph_regenerated"] = True
                    st.session_state["_hypergraph_regen_ok"] = ok
                    st.session_state["_hypergraph_regen_message"] = "" if ok else message
                    st.cache_data.clear()

                # Let the RAG tab re-initialise and see collections this run created.
                st.session_state._adapter_cache = None
                st.session_state._adapter_repo = None
                # Allow another run with different documents.
                st.session_state.documents_decision_made = False
                st.session_state.repo_ready_for_pipeline = False
                st.session_state.show_document_uploader = False

            regen_note = ""
            if st.session_state.get("_hypergraph_regenerated"):
                regen_note = (
                    " Hypergraph regenerated."
                    if st.session_state.get("_hypergraph_regen_ok")
                    else " Hypergraph regeneration failed."
                )

            failed = st.session_state.get("_agents_failed", [])
            if failed:
                st.error(
                    f"Pipeline finished with {len(failed)} failed agent(s):"
                    f" {', '.join(failed)}.{regen_note}"
                    " See the log above for details."
                )
            else:
                st.success(f"Pipeline finished.{regen_note}")

            regen_message = st.session_state.get("_hypergraph_regen_message")
            if regen_message:
                st.code(regen_message, language="text")

    st.divider()

    # ── Artifact browser ──────────────────────────────────────────────────────
    kb_dir = _kb_repo_dir(repo_name, project_root)
    if kb_dir is None:
        st.caption("No KB artifacts yet. Run the pipeline above to generate outputs.")
        return

    artifact_files = sorted(f for f in kb_dir.iterdir() if f.is_file())

    if not artifact_files:
        st.caption("KB directory exists but contains no artifacts yet.")
        return

    st.subheader(f"Artifacts — {repo_name} ({len(artifact_files)} files)")

    # ZIP download
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in artifact_files:
            zf.write(f, arcname=f.name)
    buf.seek(0)
    st.download_button(
        "⬇ Download All Artifacts (ZIP)",
        data=buf,
        file_name=f"{repo_name}_artifacts.zip",
        mime="application/zip",
    )

    st.divider()

    # ── Display uploaded documents if available ──────────────────────────────────
    docs_dir = kb_dir / "_uploaded_documents"
    if docs_dir.is_dir():
        uploaded_files = sorted([f for f in docs_dir.iterdir() if f.is_file()])
        if uploaded_files:
            st.subheader(f"📎 Supporting Documents ({len(uploaded_files)} files)")

            doc_cols = st.columns([3, 1])
            with doc_cols[0]:
                st.caption("**Document**")
            with doc_cols[1]:
                st.caption("**Download**")

            for doc_file in uploaded_files:
                doc_stat = doc_file.stat()
                doc_mtime = datetime.fromtimestamp(doc_stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.text(f"{doc_file.name} — {_format_size(doc_stat.st_size)} — {doc_mtime}")

                with col2:
                    doc_content = doc_file.read_bytes()
                    st.download_button(
                        label="📥 Download",
                        data=doc_content,
                        file_name=doc_file.name,
                        mime="application/octet-stream",
                        key=f"download_doc_{doc_file.name}_{doc_stat.st_mtime}",
                    )

            st.divider()

    _render_brd_viewer(kb_dir)
