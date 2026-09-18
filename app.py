"""
BRD Agent — Streamlit UI
Entry point: provides Pipeline Execution, RAG Chat, and Hypergraph Explorer tabs.
"""

import sys
from pathlib import Path

import streamlit as st

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure project root is on sys.path for config/tools imports
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui import pipeline_tab, rag_tab, hypergraph_tab, repo_source, doc_sources
from ui_model_display import ModelDisplayUI, initialize_session_state

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BRD Agent",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
st.session_state.setdefault("selected_repo", None)
st.session_state.setdefault("previous_selected_repo", None)
st.session_state.setdefault("pipeline_log_lines", [])
st.session_state.setdefault("pipeline_running", False)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("_pipeline_queue", None)
st.session_state.setdefault("show_document_uploader", False)
st.session_state.setdefault("uploaded_documents", [])
st.session_state.setdefault("just_uploaded_repo", False)
st.session_state.setdefault("repo_ready_for_pipeline", False)
st.session_state.setdefault("documents_decision_made", False)

# Initialize model tracking
initialize_session_state()


# ── Sidebar: global repo selector ────────────────────────────────────────────
def _detect_repos(root: Path) -> list[str]:
    """Return repo names found in KB/ and sample repository folders."""
    repos: list[str] = []

    kb_dir = root / "KB"
    if kb_dir.is_dir():
        for d in sorted(kb_dir.iterdir()):
            if d.is_dir() and d.name not in ("graph", "cache"):
                repos.append(d.name)

    sample_dirs = [
        root / "Sample-repos",
        root / "Sample_Repos",
        root / "SampleRepos",
    ]
    for sample_dir in sample_dirs:
        if sample_dir.is_dir():
            for d in sorted(sample_dir.iterdir()):
                if d.is_dir() and d.name not in repos:
                    repos.append(d.name)

    return repos


with st.sidebar:
    st.title("BRD Agent")
    st.caption("Business Requirements Document Pipeline")
    
    # Display active LLM provider
    try:
        from kb_gen.utils.multi_provider_llm import get_multi_provider_llm
        llm = get_multi_provider_llm()
        provider_info = llm.get_provider_info()
        
        provider_labels = {
            "claude_api": "Claude API",
            "openai": "OpenAI (GPT)",
            "gemini": "Google Gemini",
            "github_copilot": "GitHub Copilot Chat",
            "claude_code": "Claude Code (VS Code)",
        }
        provider = provider_info["provider"]
        if provider in provider_labels:
            st.caption(f"**Provider:** :green-badge[{provider_labels[provider]}]")
        else:
            st.caption("**Provider:** :orange-badge[Static analysis fallback]")
            st.caption("Set an API key or authenticate the VS Code extension for enhanced analysis.")

        st.divider()
    except Exception as e:
        st.error(f"Provider detection error: {e}")
        st.divider()
    
    # Dark mode toggle
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    st.toggle("🌙 Dark Mode", value=True, disabled=True, help="Dark mode enabled by default")
    
    st.divider()

    # ── Repository source: existing / upload / git URL ───────────────────────────
    uploaded_repo_name = repo_source.render_repo_source(PROJECT_ROOT, _detect_repos)

    # ── Conditional Document Upload ──────────────────────────────────────────────
    selected_repo = st.session_state.get("selected_repo")    
    # If repo selection changed, reset document decision so user is asked again
    previous_repo = st.session_state.get("previous_selected_repo")
    if selected_repo != previous_repo and selected_repo:
        st.session_state.documents_decision_made = False
        st.session_state.repo_ready_for_pipeline = False
        st.session_state.show_document_uploader = False
        # Without this, documents staged for the previous repo would be written
        # into the newly selected repo's KB folder.
        st.session_state.uploaded_documents = []
        st.session_state.previous_selected_repo = selected_repo
    # Only show document decision buttons if:
    # 1. No decision has been made yet, AND
    # 2. Pipeline is NOT running AND
    # 3. A repo is selected
    if not st.session_state.get("documents_decision_made") and not st.session_state.get("pipeline_running") and selected_repo:
        # User has selected a repo (either from dropdown or uploaded) - ask if they want to add documents
        st.divider()
        st.subheader("📎 Add Supporting Documents?")
        st.caption("Choose whether to add additional documents (requirements, specs, etc.) before running the pipeline.")

        col1, col2 = st.columns(2)
        with col1:
            btn_key = "add_docs_yes" if uploaded_repo_name else "add_docs_dropdown_yes"
            if st.button("✅ YES - Add Documents", key=btn_key, use_container_width=True):
                st.session_state.show_document_uploader = True
                st.session_state.just_uploaded_repo = False
                st.session_state.documents_decision_made = True
                st.rerun()
        with col2:
            btn_key = "add_docs_no" if uploaded_repo_name else "add_docs_dropdown_no"
            if st.button("❌ NO - Skip Documents", key=btn_key, use_container_width=True):
                st.session_state.show_document_uploader = False
                st.session_state.just_uploaded_repo = False
                st.session_state.documents_decision_made = True
                st.session_state.repo_ready_for_pipeline = True
                st.rerun()

    # Show document sources only if explicitly enabled and pipeline NOT running
    if st.session_state.get("show_document_uploader") and not st.session_state.get("pipeline_running"):
        st.divider()
        doc_sources.render_document_sources()

        st.divider()
        if st.button("Documents ready — proceed to pipeline", key="docs_ready_button"):
            st.session_state.repo_ready_for_pipeline = True
            st.rerun()

    # Show "ready for pipeline" message only when pipeline NOT running
    if st.session_state.get("repo_ready_for_pipeline") and not st.session_state.get("pipeline_running"):
        st.divider()
        st.caption(
            f"**{selected_repo}** is ready — open **Generate BRD** and click **▶ Run Pipeline**."
        )

    st.divider()

    # ── Load Anthropic API key from environment ──────────────────────────────────
    import os
    existing_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if existing_key:
        st.session_state.setdefault("anthropic_api_key", existing_key)

    st.divider()
    st.caption(f"Root: `{PROJECT_ROOT}`")

# ── Tabs ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Tab text styling - large, bold, orange */
    [data-baseweb="tab"] {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: #f0883e !important;
    }

    /* Hover state */
    [data-baseweb="tab"]:hover {
        background-color: rgba(240, 136, 62, 0.1) !important;
        color: #f0883e !important;
    }

    /* Active/selected tab */
    [data-baseweb="tab"][aria-selected="true"] {
        color: #f0883e !important;
    }

    /* Orange bottom border indicator for active tab */
    [role="tablist"] [aria-selected="true"] {
        border-bottom: 3px solid #f0883e !important;
        padding-bottom: 12px !important;
    }

    /* Ensure all tab elements have orange styling */
    [role="tab"] {
        color: #f0883e !important;
    }

    [role="tab"][aria-selected="true"] {
        color: #f0883e !important;
        border-bottom-color: #f0883e !important;
    }
</style>
""", unsafe_allow_html=True)

# on_change="rerun" makes the tabs dynamic so .open is meaningful. Without it
# Streamlit executes every tab body on every rerun, which during a pipeline run
# meant rebuilding the hypergraph viewer and the RAG adapter several times a
# second and pushing all of it over the websocket.
tab1, tab2, tab3 = st.tabs(
    ["📄 Generate BRD", "💬 RAG Chat", "🕸️ Hypergraph"], on_change="rerun"
)

if tab1.open:
    with tab1:
        pipeline_tab.render(PROJECT_ROOT)

if tab2.open:
    with tab2:
        rag_tab.render(PROJECT_ROOT)

if tab3.open:
    with tab3:
        hypergraph_tab.render(PROJECT_ROOT)
