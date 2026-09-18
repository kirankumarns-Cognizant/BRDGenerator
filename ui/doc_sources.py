"""
Supporting-document sources for the sidebar: file upload plus optional external
systems (Jira, Confluence, OpenSearch).

Availability is read from environment variables, matching the rest of the project
(.env + os.getenv, loaded in app.py). A source becomes selectable only once it is
both configured and has a fetcher registered in _FETCHERS, so the UI never shows
a control that cannot do anything.
"""

import os
from pathlib import Path
from typing import Callable

import streamlit as st

# source key -> (display label, required environment variables)
_SOURCES: dict[str, tuple[str, tuple[str, ...]]] = {
    "jira": ("Jira", ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")),
    "confluence": ("Confluence", ("CONFLUENCE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN")),
    "opensearch": ("OpenSearch", ("OPENSEARCH_URL", "OPENSEARCH_USERNAME", "OPENSEARCH_PASSWORD")),
}

# Populated when real fetchers land. Each takes (repo_name, docs_dir) and writes
# documents into docs_dir.
_FETCHERS: dict[str, Callable[[str, Path], int]] = {}


def source_status() -> dict[str, tuple[bool, list[str]]]:
    """Return {source_key: (configured, missing_env_vars)}."""
    status = {}
    for key, (_, required) in _SOURCES.items():
        missing = [var for var in required if not os.environ.get(var)]
        status[key] = (not missing, missing)
    return status


def available_sources() -> list[str]:
    """Source keys that are configured and have a working fetcher."""
    return [k for k, (ok, _) in source_status().items() if ok and k in _FETCHERS]


def render_document_sources() -> None:
    """Render the uploader and the external-source status rows."""
    st.subheader("Supporting documents")
    st.caption(
        "Requirements, specs or notes to fold into the BRD. Any file type is "
        "accepted; text, PDF, Word, Excel and CSV are parsed."
    )

    uploaded = st.file_uploader(
        "Upload documents",
        accept_multiple_files=True,
        help="Confluence exports, specifications, requirement sheets, etc.",
        key="doc_uploader_main",
    )

    st.session_state.uploaded_documents = [
        {"file": doc, "name": doc.name, "type": doc.type, "size": doc.size}
        for doc in (uploaded or [])
    ]

    if uploaded:
        total_kb = sum(d.size for d in uploaded) / 1024
        st.caption(f"{len(uploaded)} file(s) staged — {total_kb:.1f} KB")

    st.caption("**External sources**")
    for key, (ok, missing) in source_status().items():
        label = _SOURCES[key][0]
        if not ok:
            st.caption(f"{label} — :gray-badge[not configured]")
            st.caption(f":small[Set {', '.join(f'`{m}`' for m in missing)} in `.env`]")
        elif key in _FETCHERS:
            st.checkbox(f"Include from {label}", key=f"_doc_source_{key}")
        else:
            st.caption(f"{label} — :orange-badge[configured, fetcher pending]")
