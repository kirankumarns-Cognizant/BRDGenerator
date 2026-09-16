"""
Capability 1: Pipeline Execution
Allows users to select a repository, run the BRD pipeline, monitor progress,
browse generated artifacts, and download outputs as a ZIP.
"""

import io
import json
import os
import queue
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
if "_current_agent" not in st.session_state:
    st.session_state._current_agent = None
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "pipeline_log_lines" not in st.session_state:
    st.session_state.pipeline_log_lines = []

# Artifact display order by agent (stem prefix)
_AGENT_ORDER = [
    "scope_definition", "artifact_catalog", "dependency_map", "actors",
    "journey_map", "user_journey_map", "journey_conflicts",
    "business_rules", "validation_logic",
    "gap_analysis", "gap_register",
    "functional_requirements", "non_functional_requirements", "synthesis_decisions",
    "acceptance_criteria", "acceptance_criteria_gherkin", "test_scenarios",
    "risk_assessment", "risk_register", "dependency_analysis", "dependency_register",
    "brd_final", "brd_executive_summary", "executive_summary",
    "ingestion_log", "embedding_stats",
]

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


def _sort_key(filename: str) -> int:
    stem = Path(filename).stem
    try:
        return _AGENT_ORDER.index(stem)
    except ValueError:
        return len(_AGENT_ORDER)


def _utf8_env() -> dict:
    """Return a copy of the current environment with PYTHONIOENCODING=utf-8.
    Prevents UnicodeEncodeError when agent scripts print emoji on Windows (cp1252)."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _stream_process(proc: subprocess.Popen, q: queue.Queue) -> None:
    """Background thread: read process stdout/stderr and push lines to queue."""
    for line in proc.stdout:
        q.put(line)
    q.put(None)  # sentinel — process finished


def _start_powershell_pipeline(repo_path: str, project_root: Path) -> None:
    config_path = str(project_root / "config" / "config.yaml")
    script_path = str(project_root / "run_brd_pipeline.ps1")
    st.session_state["_pending_hypergraph_regen"] = True
    st.session_state["_hypergraph_regenerated"] = False
    cmd = [
        "powershell.exe",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", script_path,
        "-RepoPath", repo_path,
        "-ConfigPath", config_path,
    ]
    _launch(cmd)


def _start_python_pipeline(repo_path: str, project_root: Path) -> None:
    """Python orchestrator: run each agent .py script sequentially in a thread."""
    repo_name = Path(repo_path).name
    kb_output = str(project_root / "KB" / repo_name)
    skills_root = project_root / ".github" / "skills"
    st.session_state["_pending_hypergraph_regen"] = True
    st.session_state["_hypergraph_regenerated"] = False

    q: queue.Queue = queue.Queue()
    st.session_state._pipeline_queue = q
    st.session_state.pipeline_running = True
    st.session_state.pipeline_log_lines = []
    st.session_state._pipeline_proc = None  # no single process for Python mode
    st.session_state._agents_completed = []
    st.session_state._current_agent = None

    def _run_agents():
        for idx, (name, rel_script) in enumerate(_AGENT_SCRIPTS):
            # Send status update via queue (main thread will parse this)
            q.put(json.dumps({"__status": "agent_start", "name": name, "index": idx}))

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
            # Add API key if available in session state
            api_key = st.session_state.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
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
                for line in proc.stdout:
                    q.put(line)
                proc.wait()
                status = "OK" if proc.returncode == 0 else f"EXIT {proc.returncode}"
                q.put(f"[{status}] {name}\n")
                agent_status = "completed" if proc.returncode == 0 else "failed"
                # Send end status BEFORE sentinel
                q.put(json.dumps({"__status": "agent_end", "name": name, "agent_status": agent_status}))
            except Exception as exc:
                q.put(f"[ERROR] {name}: {exc}\n")
                q.put(json.dumps({"__status": "agent_end", "name": name, "agent_status": "error"}))

        q.put(None)  # sentinel

    t = threading.Thread(target=_run_agents, daemon=True)
    t.start()


def _launch(cmd: list) -> None:
    q: queue.Queue = queue.Queue()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_utf8_env(),
    )
    t = threading.Thread(target=_stream_process, args=(proc, q), daemon=True)
    t.start()
    st.session_state._pipeline_proc = proc
    st.session_state._pipeline_queue = q
    st.session_state.pipeline_running = True
    st.session_state.pipeline_log_lines = []


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
                        "status": "running"
                    }
                elif msg.get("__status") == "agent_end":
                    agent_name = msg.get("name", "")
                    agent_status = msg.get("agent_status", "unknown")
                    if st.session_state._current_agent:
                        st.session_state._current_agent["status"] = agent_status
                    # Ensure agent is added to completed list (avoid duplicates)
                    if agent_name not in st.session_state._agents_completed:
                        st.session_state._agents_completed.append(agent_name)
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

    return still_running


def _render_progress_tracker() -> None:
    """Display agent progress tracker with completion status."""
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

    # Current agent status
    if current:
        status_icon = {
            "running": "⏳",
            "completed": "✅",
            "failed": "❌",
            "skipped": "⊘",
            "error": "⚠️"
        }.get(current.get("status", "running"), "⏳")

        agent_name = current.get('name', 'Unknown')
        st.info(f"{status_icon} **Current Agent:** {agent_name}")

        # Add timeout warning if agent has been running too long
        if current.get("status") == "running":
            st.caption("⏱️ *Agent is processing... This may take several minutes with large documents*")


def _kb_repo_dir(repo_name: str, project_root: Path) -> Path | None:
    d = project_root / "KB" / repo_name
    return d if d.is_dir() else None


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
            st.success(f"✅ Saved: {file_obj.name} to repository documents folder")
        return True
    except Exception as e:
        st.error(f"❌ Error saving documents: {e}")
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

    col1, col2 = st.columns([3, 1])
    with col1:
        repo_path = st.text_input("Repository path", value=repo_path, key="repo_path_input",
                                   help="Absolute path to the repository to analyze.")
    with col2:
        use_python = st.checkbox("Use Python orchestrator", value=False,
                                  help="Bypass PowerShell and call each agent .py directly.")

    # ── Progress tracker (always visible when running) ──────────────────────────
    if st.session_state.get("_current_agent") or st.session_state.get("_agents_completed"):
        st.divider()
        _render_progress_tracker()
        st.divider()

    # ── Run / Stop controls ───────────────────────────────────────────────────
    running = st.session_state.get("pipeline_running", False)
    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        run_clicked = st.button("▶ Run Pipeline", disabled=running, type="primary")
    with c2:
        stop_clicked = st.button("⏹ Stop", disabled=not running)

    if run_clicked and repo_path:
        # Save uploaded documents before starting pipeline
        if st.session_state.get("uploaded_documents"):
            st.info("📎 Saving uploaded documents to repository...")
            if _save_uploaded_documents(repo_name, project_root):
                doc_count = len(st.session_state.get("uploaded_documents", []))
                st.success("✅ Documents saved successfully!")
                st.info(f"💡 **Document Integration:** {doc_count} document(s) will be analyzed and incorporated into the BRD generation.")
                st.warning(f"⏱️ **Note:** Processing {doc_count} document(s) may take **5-10 minutes or more** depending on document size. Please be patient while Agent 1 analyzes the content.")
                st.divider()
            else:
                st.warning("⚠️ Some documents may not have been saved.")
        else:
            st.info("📊 Starting BRD pipeline analysis...")

        # Clear the document and pipeline ready flags
        st.session_state.show_document_uploader = False
        st.session_state.just_uploaded_repo = False
        st.session_state.repo_ready_for_pipeline = False
        st.session_state.documents_decision_made = False

        if use_python:
            _start_python_pipeline(repo_path, project_root)
        else:
            _start_powershell_pipeline(repo_path, project_root)
        st.rerun()

    if stop_clicked:
        proc = st.session_state.get("_pipeline_proc")
        if proc:
            proc.terminate()
        st.session_state.pipeline_running = False
        st.session_state._pipeline_queue = None
        st.session_state["_pending_hypergraph_regen"] = False

    # ── Log streaming ─────────────────────────────────────────────────────────
    if running or st.session_state.pipeline_log_lines:
        still_running = _drain_queue()

        log_placeholder = st.empty()
        lines = st.session_state.pipeline_log_lines
        log_placeholder.code("\n".join(lines[-200:]) if lines else "Starting…", language="text")

        if still_running:
            time.sleep(0.3)
            st.rerun()
        elif lines:
            if st.session_state.get("_pending_hypergraph_regen") and not st.session_state.get("_hypergraph_regenerated"):
                ok, message = _regenerate_hypergraph(project_root)
                st.session_state["_pending_hypergraph_regen"] = False
                st.session_state["_hypergraph_regenerated"] = True
                st.cache_data.clear()
                if ok:
                    st.success("Pipeline finished. Hypergraph regenerated.")
                else:
                    st.warning("Pipeline finished, but hypergraph regeneration failed.")
                    if message:
                        st.code(message, language="text")
            else:
                st.success("Pipeline finished.")
            # Clear the RAG adapter cache so it will reinitialize and see new collections
            st.session_state._adapter_cache = None
            st.session_state._adapter_repo = None
            # Reset document decision flag so user can run pipeline again with new documents if desired
            st.session_state.documents_decision_made = False

    st.divider()

    # ── Artifact browser ──────────────────────────────────────────────────────
    kb_dir = _kb_repo_dir(repo_name, project_root)
    if kb_dir is None:
        st.info("No KB artifacts yet. Run the pipeline above to generate outputs.")
        return

    artifact_files = sorted(
        [f for f in kb_dir.iterdir() if f.is_file()],
        key=lambda f: _sort_key(f.name),
    )

    if not artifact_files:
        st.info("KB directory exists but contains no artifacts yet.")
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

    st.divider()

    for f in artifact_files:
        stat = f.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

        # Create expander header with download button
        col1, col2 = st.columns([4, 1])

        with col1:
            with st.expander(f"{f.name}  —  {_format_size(stat.st_size)}  —  {mtime}"):
                suffix = f.suffix.lower()
                try:
                    if suffix == ".json":
                        data = json.loads(f.read_text(encoding="utf-8", errors="replace"))
                        st.json(data)
                    elif suffix == ".md":
                        st.markdown(f.read_text(encoding="utf-8", errors="replace"))
                    elif suffix in {".feature", ".gherkin"}:
                        st.code(f.read_text(encoding="utf-8", errors="replace"), language="gherkin")
                    else:
                        st.code(f.read_text(encoding="utf-8", errors="replace"), language="text")
                except Exception as exc:
                    st.error(f"Could not read file: {exc}")

        with col2:
            file_content = f.read_bytes()
            st.download_button(
                label="📥 Download",
                data=file_content,
                file_name=f.name,
                mime="application/octet-stream",
                key=f"download_{f.name}_{stat.st_mtime}",
            )
