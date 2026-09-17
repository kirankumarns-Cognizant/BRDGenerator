"""
BRD Agent — Streamlit UI
Entry point: provides Pipeline Execution, RAG Chat, and Hypergraph Explorer tabs.
"""

import sys
import time
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

from ui import pipeline_tab, rag_tab, hypergraph_tab
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
st.session_state.setdefault("_pipeline_proc", None)
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
        
        # Display provider status
        if provider_info["provider"] == "claude_api":
            st.success(f"🤖 **Provider:** Claude API")
        elif provider_info["provider"] == "openai":
            st.success(f"🤖 **Provider:** OpenAI (GPT)")
        elif provider_info["provider"] == "gemini":
            st.success(f"🤖 **Provider:** Google Gemini")
        elif provider_info["provider"] == "github_copilot":
            st.info(f"🤖 **Provider:** GitHub Copilot Chat")
        elif provider_info["provider"] == "claude_code":
            st.info(f"🤖 **Provider:** Claude Code (VS Code)")
        else:
            st.warning(f"⚠️ **Provider:** Static Analysis (Fallback)")
            st.caption("💡 Set an API key or authenticate VS Code extension for enhanced analysis")
        
        st.divider()
    except Exception as e:
        st.error(f"Provider detection error: {e}")
        st.divider()
    
    # Dark mode toggle
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    st.toggle("🌙 Dark Mode", value=True, disabled=True, help="Dark mode enabled by default")
    
    st.divider()

    # ── Upload Repository (process before selectbox to avoid widget key issues) ────
    st.subheader("📤 Upload Repository")

    uploaded_file = st.file_uploader(
        "Upload a .zip file containing your repository",
        type=["zip"],
        help="Upload a zipped Java repository to analyze with BRD pipeline"
    )

    uploaded_repo_name = None
    if uploaded_file is not None:
        import zipfile
        import tempfile
        import shutil

        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        zip_path = Path(temp_dir) / uploaded_file.name

        # Save uploaded file
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract zip
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find repo folder
        extracted_items = list(Path(temp_dir).iterdir())
        repo_folder = None
        for item in extracted_items:
            if item.is_dir() and item.name != "__MACOSX":
                repo_folder = item
                break

        if repo_folder:
            uploaded_repo_name = repo_folder.name

            # Store in both Sample_Repos and KB directories
            sample_repos_dir = PROJECT_ROOT / "Sample_Repos" / uploaded_repo_name
            kb_dir = PROJECT_ROOT / "KB" / uploaded_repo_name

            try:
                # Create directories
                sample_repos_dir.parent.mkdir(parents=True, exist_ok=True)
                kb_dir.parent.mkdir(parents=True, exist_ok=True)

                # Replace existing repo if it exists
                if sample_repos_dir.exists():
                    st.info(f"🔄 Replacing existing repository '{uploaded_repo_name}'...")

                    # Try multiple strategies to delete old directory
                    deleted = False

                    # Strategy 1: Direct removal with ignore_errors
                    try:
                        shutil.rmtree(sample_repos_dir, ignore_errors=False)
                        deleted = True
                    except (PermissionError, OSError):
                        # Strategy 2: Move to temporary location first
                        try:
                            import tempfile
                            temp_location = Path(tempfile.gettempdir()) / f"{uploaded_repo_name}_old_{int(time.time())}"
                            shutil.move(str(sample_repos_dir), str(temp_location))
                            deleted = True
                        except Exception:
                            # Strategy 3: Just proceed and overwrite what we can
                            pass

                # Copy new repo (will overwrite existing files if dir still exists)
                try:
                    shutil.copytree(repo_folder, sample_repos_dir, dirs_exist_ok=True)
                except TypeError:
                    # Fallback for older Python versions without dirs_exist_ok
                    if not sample_repos_dir.exists():
                        shutil.copytree(repo_folder, sample_repos_dir)
                    else:
                        # Manually copy files
                        for item in repo_folder.iterdir():
                            src_path = repo_folder / item.name
                            dst_path = sample_repos_dir / item.name
                            if src_path.is_dir():
                                if dst_path.exists():
                                    shutil.rmtree(dst_path, ignore_errors=True)
                                shutil.copytree(src_path, dst_path)
                            else:
                                dst_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src_path, dst_path)

                # Create KB directory structure
                kb_dir.mkdir(parents=True, exist_ok=True)

                st.session_state.uploaded_repo_path = str(sample_repos_dir)
                st.session_state.selected_repo = uploaded_repo_name
                st.success(f"✅ Repository '{uploaded_repo_name}' extracted successfully!")
                st.info(f"📁 Stored in: `Sample_Repos/{uploaded_repo_name}` and `KB/{uploaded_repo_name}`")
            except Exception as e:
                st.error(f"❌ Error storing repository: {str(e)}")
                # Still allow using the repo from temp location
                st.session_state.uploaded_repo_path = str(repo_folder)
                st.session_state.selected_repo = uploaded_repo_name

            # Set flag to trigger document upload question below
            st.session_state.just_uploaded_repo = True
        else:
            st.error("❌ Could not find repository folder in uploaded zip")

    st.divider()

    # ── Repository Selection ─────────────────────────────────────────────────────
    repos = _detect_repos(PROJECT_ROOT)
    
    # If we have an uploaded repo, use it as the default
    if uploaded_repo_name:
        default_repo = uploaded_repo_name
        st.info(f"Using uploaded repository: **{uploaded_repo_name}**")
    else:
        default_repo = st.session_state.get("selected_repo")
    
    if repos:
        default_idx = repos.index(default_repo) if default_repo in repos else 0
        st.selectbox(
            "Repository",
            repos,
            index=default_idx,
            key="selected_repo",
            help="Choose the repository to analyze or query.",
        )
    else:
        st.info("No repositories found in KB/ or sample repository folders.")
        st.text_input("Custom repo name", key="selected_repo")

    # ── Conditional Document Upload ──────────────────────────────────────────────
    selected_repo = st.session_state.get("selected_repo")    
    # If repo selection changed, reset document decision so user is asked again
    previous_repo = st.session_state.get("previous_selected_repo")
    if selected_repo != previous_repo and selected_repo:
        st.session_state.documents_decision_made = False
        st.session_state.repo_ready_for_pipeline = False
        st.session_state.show_document_uploader = False
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

    # Show document uploader only if explicitly enabled and pipeline NOT running
    if st.session_state.get("show_document_uploader") and not st.session_state.get("pipeline_running"):
        st.divider()
        st.subheader("📎 Add Supporting Documents")
        st.caption("📌 Documents will be **analyzed** and **incorporated** into the BRD generation by all pipeline agents.")

        uploaded_docs = st.file_uploader(
            "Upload supporting documents (.csv, .md, .pdf)",
            type=["csv", "md", "pdf"],
            accept_multiple_files=True,
            help="Confluence docs, specifications, requirements, etc.",
            key="doc_uploader_main"
        )

        if uploaded_docs:
            # Store document metadata
            st.session_state.uploaded_documents = []
            docs_info = []

            for doc in uploaded_docs:
                doc_info = {
                    "name": doc.name,
                    "size": doc.size,
                    "type": doc.type
                }
                docs_info.append(doc_info)
                st.session_state.uploaded_documents.append({
                    "file": doc,
                    "name": doc.name,
                    "type": doc.type,
                    "size": doc.size
                })

            st.success(f"✅ Uploaded {len(uploaded_docs)} document(s)")

            # Display uploaded documents info
            doc_cols = st.columns([2, 1, 1])
            with doc_cols[0]:
                st.caption("**Document**")
            with doc_cols[1]:
                st.caption("**Type**")
            with doc_cols[2]:
                st.caption("**Size**")

            for doc_info in docs_info:
                doc_cols = st.columns([2, 1, 1])
                with doc_cols[0]:
                    st.text(doc_info["name"][:40] + "..." if len(doc_info["name"]) > 40 else doc_info["name"])
                with doc_cols[1]:
                    st.text(doc_info["type"].upper() if doc_info["type"] else "Unknown")
                with doc_cols[2]:
                    size_kb = doc_info["size"] / 1024
                    st.text(f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB")
            
            # Add button to proceed with pipeline after documents uploaded
            st.divider()
            if st.button("✅ Documents Ready - Proceed to Pipeline", use_container_width=True, key="docs_ready_button"):
                st.session_state.repo_ready_for_pipeline = True
                st.rerun()

    # Show "ready for pipeline" message only when pipeline NOT running
    if st.session_state.get("repo_ready_for_pipeline") and not st.session_state.get("pipeline_running"):
        st.divider()
        st.success(f"✅ Repository '{selected_repo}' is ready for BRD Pipeline execution!")
        st.info("📊 Go to **'Generate BRD'** tab and click **'▶ Run Pipeline'** to start analyzing.")

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

# Check if repo is selected but document decision not made
selected_repo = st.session_state.get("selected_repo")
documents_decision_made = st.session_state.get("documents_decision_made")

if selected_repo and not documents_decision_made:
    # Repo selected but user hasn't answered the document question yet
    st.info(
        "👈 **Please answer the document question in the sidebar first:**\n\n"
        "Choose whether to add supporting documents before proceeding."
    )
else:
    # Either no repo selected, or decision has been made - show tabs
    tab1, tab2, tab3 = st.tabs(["📄 Generate BRD", "💬 RAG Chat", "🕸️ Hypergraph"])

    with tab1:
        pipeline_tab.render(PROJECT_ROOT)

    with tab2:
        rag_tab.render(PROJECT_ROOT)

    with tab3:
        hypergraph_tab.render(PROJECT_ROOT)
