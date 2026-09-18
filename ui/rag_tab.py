"""
Capability 2: RAG Chat
Allows users to ask questions against generated BRD artifacts via ChromaDB semantic search.
Answers are synthesised by Claude into conversational responses with source citations.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st


# ── Artifact content formatters ───────────────────────────────────────────────

_SEVERITY_ICON = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}


def _fmt_risk_register(data: dict) -> str:
    risks = data.get("risks", data)
    items = risks.get("identified_risks", []) if isinstance(risks, dict) else []
    if not items:
        return ""
    lines = ["### Risk Register\n"]
    lines.append("| # | Risk | Category | Severity | Probability |")
    lines.append("|---|------|----------|----------|-------------|")
    for r in items:
        icon = _SEVERITY_ICON.get(r.get("severity", "").upper(), "")
        lines.append(
            f"| {r.get('risk_id', '')} | {r.get('title', '')} "
            f"| {r.get('category', '')} | {icon} {r.get('severity', '')} "
            f"| {r.get('probability', '')} |"
        )
    lines.append("")
    for r in items:
        icon = _SEVERITY_ICON.get(r.get("severity", "").upper(), "")
        lines.append(f"**{r.get('risk_id', '')} — {r.get('title', '')}** {icon}")
        if r.get("description"):
            lines.append(f"> {r['description']}")
        if r.get("impact"):
            lines.append(f"- **Impact:** {r['impact']}")
        if r.get("mitigation"):
            lines.append(f"- **Mitigation:** {r['mitigation']}")
        if r.get("owner"):
            lines.append(f"- **Owner:** {r['owner']}")
        lines.append("")
    by_sev = risks.get("by_severity", {}) if isinstance(risks, dict) else {}
    if by_sev:
        summary = ", ".join(f"{k}: {v}" for k, v in by_sev.items())
        lines.append(f"_Total risks: {risks.get('total_risks', len(items))} · {summary}_")
    return "\n".join(lines)


def _fmt_business_rules(data: dict) -> str:
    rules = data.get("rules", data.get("business_rules", []))
    if isinstance(rules, dict):
        rules = rules.get("rules", [])
    if not rules:
        return ""
    lines = ["### Business Rules\n"]
    for i, r in enumerate(rules, 1):
        if isinstance(r, str):
            lines.append(f"{i}. {r}")
            continue
        title = r.get("title") or r.get("rule_id") or r.get("name") or f"Rule {i}"
        lines.append(f"**{i}. {title}**")
        for field in ("description", "condition", "action", "rationale", "category"):
            val = r.get(field)
            if val:
                lines.append(f"   - **{field.title()}:** {val}")
        lines.append("")
    return "\n".join(lines)


def _fmt_journey_map(data: dict) -> str:
    journeys = data.get("journeys", data.get("user_journeys", []))
    if not journeys:
        return ""
    lines = ["### User Journeys\n"]
    for j in journeys:
        name = j.get("journey_name") or j.get("name") or "Journey"
        actor = j.get("actor") or j.get("user_type") or ""
        lines.append(f"**{name}**" + (f" _(actor: {actor})_" if actor else ""))
        steps = j.get("steps", [])
        if steps:
            step_names = [s.get("action") or s.get("step") or str(s) for s in steps]
            lines.append("  " + " → ".join(str(s) for s in step_names[:8]))
        if j.get("goal"):
            lines.append(f"  _Goal: {j['goal']}_")
        lines.append("")
    return "\n".join(lines)


def _fmt_gap_analysis(data: dict) -> str:
    gaps = data.get("gaps", data.get("gap_analysis", []))
    if not gaps:
        return ""
    lines = ["### Gap Analysis\n"]
    for g in gaps:
        if isinstance(g, str):
            lines.append(f"- {g}")
            continue
        title = g.get("title") or g.get("gap_id") or "Gap"
        lines.append(f"**{title}**")
        for field in ("description", "impact", "recommendation", "priority"):
            val = g.get(field)
            if val:
                lines.append(f"  - **{field.title()}:** {val}")
        lines.append("")
    return "\n".join(lines)


def _fmt_actors(data: dict) -> str:
    actors = data.get("actors", [])
    if not actors:
        return ""
    lines = ["### Actors & Stakeholders\n"]
    for a in actors:
        if isinstance(a, str):
            lines.append(f"- {a}")
            continue
        name = a.get("name") or a.get("actor") or "Actor"
        role = a.get("role") or a.get("type") or ""
        lines.append(f"**{name}**" + (f" — {role}" if role else ""))
        for field in ("responsibilities", "description", "goals"):
            val = a.get(field)
            if val:
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                lines.append(f"  {val}")
        lines.append("")
    return "\n".join(lines)


def _fmt_generic(data: dict) -> str:
    """Fallback: show meaningful text fields, skip metadata."""
    _meta = {"project_name", "agent", "confidence", "timestamp", "chunk_id",
             "file_type", "source", "source_file", "artifact_type", "version"}
    lines = []
    for k, v in data.items():
        if k in _meta:
            continue
        label = k.replace("_", " ").title()
        if isinstance(v, list) and v:
            items = [str(i.get("title") or i.get("name") or i) if isinstance(i, dict) else str(i)
                     for i in v[:8]]
            lines.append(f"**{label}:** {', '.join(items)}" + ("…" if len(v) > 8 else ""))
        elif isinstance(v, dict):
            inner = ", ".join(f"{ik.replace('_', ' ').title()}: {iv}"
                               for ik, iv in v.items() if iv not in (None, "", [], {}))
            if inner:
                lines.append(f"**{label}:** {inner}")
        elif v not in (None, "", [], {}):
            lines.append(f"- **{label}:** {v}")
    return "\n".join(lines)


def _format_artifact_content(content: str, artifact_type: str = "") -> str:
    """
    Format a chunk for display.  Markdown chunks are returned as-is.
    JSON chunks are routed to the appropriate professional formatter.
    """
    stripped = content.strip()
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return stripped           # already markdown — professional as-is

    try:
        data = json.loads(stripped)
    except Exception:
        return content

    if not isinstance(data, dict):
        return content

    atype = artifact_type.lower()
    if "risk" in atype:
        result = _fmt_risk_register(data)
    elif "business_rule" in atype or "rules" in atype:
        result = _fmt_business_rules(data)
    elif "journey" in atype:
        result = _fmt_journey_map(data)
    elif "gap" in atype:
        result = _fmt_gap_analysis(data)
    elif "actor" in atype:
        result = _fmt_actors(data)
    else:
        result = _fmt_generic(data)

    return result.strip() if result.strip() else content


# ── Persistent RAG cache (session + disk) ────────────────────────────────────

_CACHE_TTL = 86400         # 24 hours


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _cache_key(collection: str, question: str) -> str:
    return f"{collection}||{question.lower().strip()}"


def _cache_file(project_root: Path) -> Path:
    p = project_root / "KB" / "cache" / "rag_ui_cache.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_disk_cache(project_root: Path) -> None:
    """Load disk cache into session state once per session."""
    if st.session_state.get("_rag_cache_loaded"):
        return
    try:
        cf = _cache_file(project_root)
        if cf.exists():
            data = json.loads(cf.read_text(encoding="utf-8"))
            st.session_state["_rag_cache"] = data if isinstance(data, dict) else {}
        else:
            st.session_state.setdefault("_rag_cache", {})
    except Exception:
        st.session_state.setdefault("_rag_cache", {})
    st.session_state["_rag_cache_loaded"] = True


def _save_disk_cache(project_root: Path) -> None:
    try:
        cf = _cache_file(project_root)
        tmp = cf.with_suffix(".tmp")
        tmp.write_text(json.dumps(st.session_state.get("_rag_cache", {}), indent=2), encoding="utf-8")
        tmp.replace(cf)
    except Exception:
        pass


def _cache_get(collection: str, question: str):
    cache = st.session_state.get("_rag_cache", {})
    entry = cache.get(_cache_key(collection, question))
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        entry["hits"] = entry.get("hits", 0) + 1
        return entry
    return None


def _cache_set(collection: str, question: str, sources, answer: str, project_root: Path) -> None:
    context_text = " ".join(s.get("content", "") for s in sources)
    input_tokens = _estimate_tokens(question + context_text) + 300
    output_tokens = _estimate_tokens(answer)
    cache = st.session_state.setdefault("_rag_cache", {})
    cache[_cache_key(collection, question)] = {
        "sources": sources,
        "answer": answer,
        "ts": time.time(),
        "hits": 0,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    _save_disk_cache(project_root)


def _render_cache_badge(entry: dict) -> None:
    in_tok = entry.get("input_tokens", 0)
    out_tok = entry.get("output_tokens", 0)
    hits = entry.get("hits", 1)
    age_min = int((time.time() - entry["ts"]) / 60)
    age_str = f"{age_min}m ago" if age_min < 60 else f"{age_min // 60}h ago"
    st.caption(
        f":green-badge[⚡ Cached] 0 LLM calls · "
        f"~{in_tok:,} input / ~{out_tok:,} output tokens saved · "
        f"hit #{hits} · cached {age_str}"
    )


# ── ChromaDB adapter (lazy, cached) ──────────────────────────────────────────

def _get_adapter(project_root_str: str, repo_name: str = ""):
    """
    Get or create ChromaDBAdapter.
    Uses session state to track which repo the adapter is for and reinitializes 
    when the repo changes (e.g., after pipeline completes with a new collection).
    """
    project_root = Path(project_root_str)
    sys.path.insert(0, str(project_root))
    
    # Initialize tracking variables if not present
    st.session_state.setdefault("_adapter_cache", None)
    st.session_state.setdefault("_adapter_repo", None)
    
    # Check if we need to reinitialize (repo changed or first time)
    if st.session_state.get("_adapter_repo") != repo_name:
        st.session_state._adapter_cache = None
        st.session_state._adapter_repo = repo_name
    
    # If adapter is cached and still valid, return it
    if st.session_state._adapter_cache is not None:
        return st.session_state._adapter_cache, None

    # Create new adapter
    try:
        from config.config_loader import ConfigLoader
        from tools.adapters.chromadb_adapter import ChromaDBAdapter
        
        with st.spinner("Connecting to vector store…"):
            config = ConfigLoader(str(project_root / "config" / "config.yaml"))
            adapter = ChromaDBAdapter(config)
            st.session_state._adapter_cache = adapter
            return adapter, None
    except ImportError as exc:
        return None, f"ChromaDB not installed: {exc}. Run `pip install chromadb`."
    except Exception as exc:
        return None, str(exc)


def _available_collections(adapter) -> list[str]:
    """Return collections matching the brd_<repo_name> naming pattern."""
    all_cols = adapter.list_collections()
    return [c for c in all_cols if c.startswith("brd_")]


def _query(adapter, collection: str, question: str, n: int = 5) -> dict:
    results = adapter.query_documents(collection, question, n_results=n)
    if not results:
        return {"docs": [], "metas": [], "distances": [], "ids": []}
    return {
        "docs":      (results.get("documents") or [[]])[0],
        "metas":     (results.get("metadatas")  or [[]])[0],
        "distances": (results.get("distances")  or [[]])[0],
        "ids":       (results.get("ids")        or [[]])[0],
    }


_RELEVANCE_THRESHOLD = 0.25   # sources below 25% are filtered out


def _distance_to_score(d: float) -> float:
    return max(0.0, 1.0 - d / 2.0)


def _format_distance(d: float) -> str:
    """Convert ChromaDB L2 distance to a 0-100 relevance score (rough)."""
    return f"{_distance_to_score(d)*100:.0f}%"


def _build_sources(docs: list, metas: list, distances: list, ids: list) -> list[dict]:
    """Build the sources list from retrieved chunks, filtering low-relevance results."""
    raw: list[dict] = []
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        doc_id = ids[i - 1] if i <= len(ids) else ""
        id_stem = doc_id.rsplit("_", 1)[0] if doc_id and "_" in doc_id else doc_id
        score = _distance_to_score(dist)
        artifact = (
            meta.get("artifact_type")
            or meta.get("source_file")
            or id_stem
            or "Unknown"
        )
        filename = (
            meta.get("filename")
            or meta.get("source")
            or (doc_id + ("." + meta["file_type"] if meta.get("file_type") else ""))
            or artifact
        )
        raw.append({
            "index": i,
            "filename": filename,
            "artifact": artifact,
            "agent": meta.get("agent") or "",
            "chunk_id": meta.get("chunk_id") or doc_id or "",
            "relevance": f"{score*100:.0f}%",
            "score": score,
            "content": doc,
        })

    # Drop sources that are below the relevance threshold
    sources = [s for s in raw if s["score"] >= _RELEVANCE_THRESHOLD]

    # Re-number after filtering
    for idx, src in enumerate(sources, 1):
        src["index"] = idx

    return sources


def _synthesize_with_llm(question: str, sources: list[dict], api_key: str, repo_name: str) -> str:
    """
    Call Claude to produce a concise, intelligent summary grounded in the retrieved chunks.
    Streams the response back as a generator for st.write_stream.
    """
    import anthropic

    if not sources:
        return

    # Build context block from retrieved chunks
    context_parts = []
    for src in sources:
        label = src["artifact"].replace("_", " ").title()
        context_parts.append(f"[Source {src['index']} — {label} (relevance: {src['relevance']})]:\n{src['content']}")
    context = "\n\n---\n\n".join(context_parts)

    system_prompt = (
        f"You are a Business Analyst assistant for **{repo_name}**. Answer questions about BRD artifacts conversationally and clearly.\n\n"
        "**CRITICAL FORMATTING RULES:**\n"
        "1. ALWAYS number items (AC 1, AC 2, Requirement 1, Risk 1, etc.)\n"
        "2. For acceptance criteria ALWAYS use: **AC #: Given [X], when [Y], then [Z]**\n"
        "3. For each item, add 1-2 sentences explaining why it matters\n"
        "4. Group related items together\n"
        "5. Use **bold** for important terms\n"
        "6. Write conversationally — as if explaining to a colleague\n"
        "7. Cite sources naturally: 'According to [source name] [1]...'\n"
        "8. Keep paragraphs short and scannable\n\n"
        "**DO NOT show raw JSON or excerpts. ALWAYS synthesize into conversational, numbered format.**\n"
        "**EXAMPLE RESPONSE:**\n"
        "Based on the BRD, here are the key acceptance criteria:\n\n"
        "**AC 1: Given** a user is logged in, **when** they submit a payment, **then** the system confirms the transaction [1].\n"
        "This ensures payment integrity and user confidence.\n\n"
        "**AC 2: Given** an order exists, **when** the user requests a refund, **then** the system processes it within 24 hours [2].\n"
        "This meets the customer service requirement for fast refunds.\n"
    )

    client = anthropic.Anthropic(api_key=api_key)
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=512,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Based on these BRD excerpts:\n\n{context}\n\n---\n\nQuestion: {question}\n\nProvide a synthesized, conversational answer.",
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            yield text


def _fallback_response(sources: list[dict]) -> str:
    """Professional summary when no API key is available."""
    if not sources:
        return "_No relevant content found in the knowledge base for this query._"

    parts = ["**Relevant excerpts from the BRD knowledge base:**\n"]
    for src in sources:
        label = src["artifact"].replace("_", " ").title()
        formatted = _format_artifact_content(src.get("content", ""), src.get("artifact", ""))
        if len(formatted) > 1200:
            formatted = formatted[:1200].rsplit("\n", 1)[0] + "\n\n_…(see Sources for full content)_"
        parts.append(f"**[{src['index']}] {label}**  —  relevance {src['relevance']}\n\n{formatted}\n")
    return "\n---\n".join(parts)


# ── Assistant response (extracted to keep render() complexity low) ────────────

def _generate_answer(prompt, sources, api_key, repo_name):
    """Return (answer_str, from_stream). Writes to Streamlit inline."""
    if not sources:
        answer = "_No relevant content found in the knowledge base for this query._"
        st.markdown(answer)
        return answer

    # Always use LLM synthesis when API key is present
    if api_key:
        try:
            with st.spinner("🤖 Synthesizing intelligent answer…"):
                answer_text = ""
                for chunk in _synthesize_with_llm(prompt, sources, api_key, repo_name):
                    answer_text += chunk
                st.markdown(answer_text)
                return answer_text
        except Exception as exc:
            st.warning(f"LLM synthesis failed: {exc}")
            st.caption("Showing extracted excerpts instead.")

    # Fallback: show raw excerpts when no API key or LLM failed
    answer = _fallback_response(sources)
    st.markdown(answer)
    return answer


def _render_assistant_response(adapter, collection, prompt, api_key, repo_name, project_root):
    """Handle cache lookup + retrieval. Returns (sources, answer, from_cache)."""
    cached = _cache_get(collection, prompt)
    if cached:
        _render_cache_badge(cached)
        st.markdown(cached["answer"])
        if cached["sources"]:
            with st.expander(f"Sources ({len(cached['sources'])})"):
                _render_sources(cached["sources"])
        return cached["sources"], cached["answer"], True

    with st.spinner("Searching knowledge base…"):
        result = _query(adapter, collection, prompt)

    sources = _build_sources(
        result["docs"], result["metas"], result["distances"], result.get("ids", [])
    )
    answer = _generate_answer(prompt, sources, api_key, repo_name)
    if sources:
        with st.expander(f"Sources ({len(sources)})"):
            _render_sources(sources)
    _cache_set(collection, prompt, sources, answer, project_root)
    return sources, answer, False


# ── Render ────────────────────────────────────────────────────────────────────

def render(project_root: Path) -> None:
    # Make tab text orange (matching visualization)
    st.markdown("""
    <style>
    [data-baseweb="tab"] {
        color: #FF9500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("💬 RAG Chat")
    st.caption("Ask questions about your generated BRD artifacts. Answers are grounded in the knowledge base.")

    # Load disk cache into session state once per session
    _load_disk_cache(project_root)

    repo_name: str | None = st.session_state.get("selected_repo")
    if not repo_name:
        st.info("Select a repository from the sidebar to begin chatting.")
        return

    # ── Connect to ChromaDB ───────────────────────────────────────────────────
    adapter, err = _get_adapter(str(project_root), repo_name)
    if err:
        st.error(err)
        return

    # ── Collection discovery ──────────────────────────────────────────────────
    target_collection = f"brd_{repo_name}"
    available = _available_collections(adapter)
    count = adapter.get_collection_count(target_collection) if target_collection in available else 0

    if target_collection not in available or count == 0:
        st.warning(
            f"No vector store found for **{repo_name}** (expected collection `{target_collection}`).\n\n"
            "Run the full pipeline first — Agent 9 (KB Store Sync) populates the vector store."
        )
        if available:
            st.caption(
                f"**Available collections:** {', '.join(available)} — if you just ran the "
                "pipeline, switch tabs and come back; the new collection is picked up automatically."
            )
        else:
            st.caption("No collections found in ChromaDB. The vector store may need initialization.")
        if st.button("▶ Run Agent 9 (KB Store Sync) now"):
            _run_agent9(repo_name, project_root)
        return

    api_key: str = st.session_state.get("anthropic_api_key", "")

    col_info, col_mode = st.columns([3, 2])
    with col_info:
        st.caption(f"Collection: `{target_collection}` — {count} document chunks indexed")
    with col_mode:
        if api_key:
            st.caption("Mode: **Conversational** (Claude)")
        else:
            st.caption("Mode: **Excerpt** — add API key in sidebar for conversational answers")

    # ── Example questions ─────────────────────────────────────────────────────
    with st.expander("Example questions"):
        examples = [
            "What are the business rules?",
            "What risks were identified?",
            "What customer journeys exist?",
            "Summarize the project scope.",
            "What are the acceptance criteria?",
            "What dependencies were found?",
            "What gaps were identified?",
        ]
        cols = st.columns(2)
        for i, ex in enumerate(examples):
            if cols[i % 2].button(ex, key=f"ex_{i}"):
                st.session_state._prefill_question = ex

    # ── Chat history display ──────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            if msg.get("from_cache") and msg.get("cache_entry"):
                _render_cache_badge(msg["cache_entry"])
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"Sources ({len(msg['sources'])})"):
                    _render_sources(msg["sources"])

    # ── Chat input ────────────────────────────────────────────────────────────
    prefill = st.session_state.pop("_prefill_question", None)
    prompt = st.chat_input("Ask about business rules, risks, user journeys…", key="rag_chat_input")
    if prefill and not prompt:
        prompt = prefill

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            sources, answer, from_cache = _render_assistant_response(
                adapter, target_collection, prompt, api_key, repo_name, project_root
            )

        cache_entry = st.session_state.get("_rag_cache", {}).get(
            _cache_key(target_collection, prompt)
        )
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "from_cache": from_cache,
            "cache_entry": cache_entry if from_cache else None,
        })

    # ── Clear history ─────────────────────────────────────────────────────────
    if st.session_state.chat_history and st.button("Clear chat history"):
        st.session_state.chat_history = []
        st.rerun()


def _render_sources(sources: list[dict]) -> None:
    for src in sources:
        rel = src.get("relevance", "")
        artifact = src.get("artifact", "").replace("_", " ").title()
        agent = f" · {src['agent']}" if src.get("agent") else ""
        with st.expander(
            f"[{src['index']}] {artifact}{agent}  —  relevance **{rel}**",
            expanded=False,
        ):
            st.caption(f"`{src['filename']}`")
            formatted = _format_artifact_content(src.get("content", ""), src.get("artifact", ""))
            st.markdown(formatted if formatted.strip() else "_No content_")


def _run_agent9(repo_name: str, project_root: Path) -> None:
    """Run Agent 9 synchronously with a progress spinner."""
    script = project_root / ".github" / "skills" / "agent-9-kb-store-sync" / "agent_9_kb_store_sync.py"
    config = str(project_root / "config" / "config.yaml")
    repo_path = str(project_root / "Sample-repos" / repo_name)
    if not Path(repo_path).is_dir():
        repo_path = str(project_root / "KB" / repo_name)
    kb_output = str(project_root / "KB" / repo_name)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    with st.spinner("Running Agent 9: KB Store Sync…"):
        result = subprocess.run(
            ["python", str(script), repo_path, "--config", config, "--output", kb_output],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(project_root),
        )

    if result.returncode == 0:
        st.success("Agent 9 completed. Refresh the page to start chatting.")
        _get_adapter.clear()
    else:
        st.error("Agent 9 failed.")
        st.code(result.stdout + result.stderr, language="text")
