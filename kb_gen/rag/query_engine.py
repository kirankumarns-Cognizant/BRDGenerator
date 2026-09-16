"""
RAGQueryEngine — hybrid RAG orchestrator.

Full query flow:
  query(question)
    │
    ├─ IntentClassifier.classify_query(question, name_to_id)
    │    → (intent_label, relevant_artifact_ids)
    │
    ├─ vector_store.query(question, top_k)
    │    → (artifact_id, score, metadata) list
    │
    ├─ [if use_graph_expansion] GraphWalker.expand(artifact_ids)
    │    → additional related artifact_ids from hypergraph
    │
    ├─ Merge + deduplicate candidates
    │
    ├─ [if enable_reranker] CrossEncoder rerank (BAAI/bge-reranker-base)
    │    → reordered candidates
    │
    ├─ LateChunker.chunk_and_select(candidates, question)
    │    → top chunks with context sentences
    │
    ├─ [if score < use_brute_force_threshold] LocalRAG.search(question)
    │    → TF-IDF fallback results merged
    │
    ├─ Anthropic LLM: grounded answer generation
    │
    └─ Return: {answer, sources, intent, confidence, retrieval_method, telemetry}
"""
import os
import time
from typing import Dict, List, Optional, Tuple

from kb_gen.utils.api_client import get_anthropic_client, sanitize_error
from kb_gen.rag.intent_classifier import IntentClassifier
from kb_gen.rag.late_chunking import LateChunker
from kb_gen.rag.local_rag import LocalRAG
from kb_gen.rag.context_graph import ContextGraph
from kb_gen.rag.conversation_store import ConversationStore
from kb_gen.rag.query_cache import QueryCache
from kb_gen.rag.query_log import QueryLogger


ANSWER_SYSTEM = """You are a knowledgeable assistant answering questions about business requirements,
technical specifications, and project documentation. You are given relevant excerpts from a
knowledge base. Answer accurately and concisely, grounding your response in the provided sources.
When citing, use [1], [2] etc. matching the source numbers."""

GROUNDED_SYSTEM = (
    ANSWER_SYSTEM
    + "\n\nIMPORTANT: Only use information from the provided sources. "
    "If the sources don't contain enough information, say so clearly."
)


class RAGQueryEngine:

    def __init__(
        self,
        registry,
        vector_store=None,
        hypergraph=None,
        embeddings_db_path: str = "kb_store",
        model: str = "claude-haiku-4-5-20251001",
        top_k: int = 5,
        use_graph_expansion: bool = True,
        strict_grounded: bool = True,
        use_brute_force_threshold: float = 0.3,
        enable_reranker: bool = False,
        session_id: Optional[str] = None,
        cache_path: str = "KB/cache/query_cache.json",
        cache_ttl: Optional[int] = 86400,
        use_semantic_cache: bool = False,
        semantic_threshold: float = 0.92,
    ):
        self.registry = registry
        self.model = model
        self.top_k = top_k
        self.use_graph_expansion = use_graph_expansion
        self.strict_grounded = strict_grounded
        self.use_brute_force_threshold = use_brute_force_threshold
        self.enable_reranker = enable_reranker or os.getenv("KB_STORE_ENABLE_RERANKER", "false").lower() == "true"

        # Vector store — lazy init if not provided
        self._vector_store = vector_store
        self._embeddings_db_path = embeddings_db_path

        # Hypergraph — optional
        self._hypergraph = hypergraph

        # Sub-components
        self._intent = IntentClassifier(model=model)
        self._chunker = LateChunker()
        self._local_rag = LocalRAG(registry)
        self._context_graph = ContextGraph()
        self._conv_store = ConversationStore()
        self._reranker = None
        self._client = None

        self.session_id = session_id or f"session_{int(time.time())}"
        self._query_logger = QueryLogger()
        self.cache = QueryCache(
            cache_path=cache_path,
            ttl_seconds=cache_ttl,
            use_semantic_cache=use_semantic_cache,
            semantic_threshold=semantic_threshold,
        )

    def _get_vector_store(self):
        if self._vector_store is None:
            from kb_gen.embeddings.chromadb_embedder import ChromaDBStore
            self._vector_store = ChromaDBStore(db_path=self._embeddings_db_path)
        return self._vector_store

    def _get_client(self):
        if self._client is None:
            self._client = get_anthropic_client()
        return self._client

    def _get_reranker(self):
        if not self.enable_reranker:
            return None
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder("BAAI/bge-reranker-base")
            except Exception as exc:
                print(f"[WARN]  Reranker unavailable: {exc}")
                self.enable_reranker = False
        return self._reranker

    def query(self, question: str, bypass_cache: bool = False) -> Dict:
        """Run the full hybrid RAG pipeline and return a structured result.

        Parameters
        ----------
        question : str
            Natural language question.
        bypass_cache : bool
            Set True to skip cache lookup and force a fresh pipeline run
            (the fresh result still gets written back to cache).
        """
        # Cache check — return immediately on hit
        if not bypass_cache:
            cached = self.cache.get(question)
            if cached is not None:
                return cached

        t_start = time.time()
        retrieval_method = "vector"

        # Step 1 — Intent classification
        name_to_id = self.registry.get_name_to_id_map()
        try:
            intent, intent_artifact_ids = self._intent.classify_query(question, name_to_id)
        except Exception:
            intent, intent_artifact_ids = "general", []

        # Step 1b — Hypergraph alias lookup → targeted artifact set (Gap 5+6)
        alias_targeted_ids: List[str] = []
        if self._hypergraph:
            try:
                alias_targeted_ids = self._hypergraph.alias_lookup(question, max_results=20)
            except Exception as exc:
                print(f"[WARN]  Alias lookup failed: {sanitize_error(str(exc))}")

        # Step 2 — Vector search (targeted if alias hit, global fallback)
        candidates: List[Tuple[str, float, Dict]] = []
        try:
            vs = self._get_vector_store()
            if alias_targeted_ids:
                candidates = vs.query_filtered(question, alias_targeted_ids, top_k=self.top_k)
                retrieval_method = "targeted"
                if not candidates:  # alias set had no embeddings yet — fall back
                    candidates = vs.query(question, top_k=self.top_k)
                    retrieval_method = "vector"
            else:
                candidates = vs.query(question, top_k=self.top_k)
        except Exception as exc:
            print(f"[WARN]  Vector search failed: {sanitize_error(str(exc))}")

        # Merge intent-predicted docs (with a baseline score)
        candidate_ids = {c[0] for c in candidates}
        for aid in intent_artifact_ids:
            if aid not in candidate_ids:
                doc = self.registry.get_document(aid)
                if doc:
                    candidates.append((aid, 0.5, doc))
                    candidate_ids.add(aid)

        # Step 3 — Graph expansion
        if self.use_graph_expansion and self._hypergraph and candidates:
            try:
                from kb_gen.graph.graph_walker import GraphWalker
                walker = GraphWalker(self._get_vector_store(), self._hypergraph)
                seed_ids = [c[0] for c in candidates[:self.top_k]]
                expanded_ids = walker.expand(seed_ids, max_expanded=5)
                for eid in expanded_ids:
                    if eid not in candidate_ids:
                        doc = self.registry.get_document(eid)
                        if doc:
                            candidates.append((eid, 0.4, doc))
                            candidate_ids.add(eid)
                if expanded_ids:
                    retrieval_method = "hybrid"
            except Exception as exc:
                print(f"[WARN]  Graph expansion failed: {sanitize_error(str(exc))}")

        # Step 4 — CrossEncoder reranking
        if self.enable_reranker and candidates:
            reranker = self._get_reranker()
            if reranker:
                try:
                    pairs = [(question, c[2].get("text") or c[2].get("chunk_text") or c[2].get("name", "")) for c in candidates]
                    scores = reranker.predict(pairs)
                    candidates = [
                        (c[0], float(s), c[2])
                        for c, s in sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
                    ]
                except Exception:
                    pass

        # Step 5 — LateChunker: contextual chunk extraction
        top_chunks = self._chunker.chunk_and_select(candidates, question, top_n=self.top_k)

        # Step 6 — LocalRAG fallback
        max_score = max((c[1] for c in candidates), default=0.0)
        if max_score < self.use_brute_force_threshold:
            local_results = self._local_rag.search(question, top_k=self.top_k)
            local_ids = {c[0] for c in candidates}
            for aid, score, meta in local_results:
                if aid not in local_ids:
                    top_chunks.append({"artifact_id": aid, "score": score, "snippet": meta.get("description", ""), "metadata": meta})
            retrieval_method = "local" if not candidates else "hybrid"
            top_chunks = sorted(top_chunks, key=lambda x: x["score"], reverse=True)[: self.top_k]

        # Step 7 — Build sources list
        sources = self._build_sources(top_chunks)

        # Step 8 — LLM answer generation
        answer, confidence = self._generate_answer(question, sources, intent)

        # Step 9 — kb_writeback: update registry metadata for retrieved artifacts (Gap 8)
        self._kb_writeback(sources, intent, question)

        # Step 10 — Conversation history
        self._conv_store.add_turn(self.session_id, "user", question)
        self._conv_store.add_turn(
            self.session_id, "assistant", answer,
            metadata={"intent": intent, "sources": [s.get("artifact_id", "") for s in sources]},
        )

        elapsed = time.time() - t_start
        result = {
            "answer": answer,
            "sources": sources,
            "intent": intent,
            "confidence": confidence,
            "retrieval_method": retrieval_method,
            "telemetry": {
                "elapsed_sec": round(elapsed, 2),
                "candidates_found": len(candidates),
                "sources_used": len(sources),
                "vector_score_max": round(max_score, 3),
                "used_fallback": max_score < self.use_brute_force_threshold,
                "cache_hit": False,
                "alias_targeted_ids": len(alias_targeted_ids),
            },
        }

        # Write to cache (always, even on bypass_cache — refreshes the entry)
        self.cache.set(question, result)

        # Gap 11 — Query log (seeds Phase 2 FAQ cache)
        self._query_logger.log(
            query_text=question,
            intent=intent,
            sources=sources,
            answer=answer,
            elapsed_sec=elapsed,
            session_id=self.session_id,
            retrieval_method=retrieval_method,
        )

        return result

    # ── Private helpers ───────────────────────────────────────────────────────────

    def _kb_writeback(self, sources: List[Dict], intent: str, question: str) -> None:
        """Update artifact metadata after every RAG query (Gap 8).

        Per-artifact: access_count++, query_intents append, used_for append.
        Also records co-retrieval in the session context graph.
        """
        _INTENT_TO_TASK = {
            "requirement_lookup": "requirement_clarification",
            "rule_lookup": "rule_clarification",
            "journey_lookup": "journey_analysis",
            "gap_analysis": "gap_analysis",
            "risk_lookup": "risk_assessment",
            "scope_lookup": "scope_definition",
            "acceptance_criteria": "test_case_writing",
            "general": "general_query",
        }
        task_type = _INTENT_TO_TASK.get(intent, "general_query")
        artifact_ids_used = []

        for src in sources:
            aid = src.get("artifact_id", "")
            if not aid:
                continue
            artifact_ids_used.append(aid)
            # record_access handles: access_count, last_accessed, query_intents
            self.registry.record_access(aid, intent)
            # used_for accumulation (task type the artifact helped with)
            self.registry.update_used_for(aid, task_type)

        self._context_graph.record_retrieval(artifact_ids_used)

    def _build_sources(self, top_chunks: List[Dict]) -> List[Dict]:
        sources = []
        for chunk in top_chunks:
            aid = chunk.get("artifact_id", "")
            meta = chunk.get("metadata", {})
            doc = self.registry.get_document(aid) or meta
            sources.append({
                "artifact_id": aid,
                "name": doc.get("name") or meta.get("name") or aid,
                "service": doc.get("service") or meta.get("service", ""),
                "snippet": chunk.get("snippet") or meta.get("text", "")[:400],
                "score": round(chunk.get("score", 0.0), 4),
            })
        return sources

    def _generate_answer(self, question: str, sources: List[Dict], intent: str) -> Tuple[str, str]:
        if not sources:
            return "No relevant information found in the knowledge base.", "LOW"

        context_parts = []
        for i, src in enumerate(sources, 1):
            name = src.get("name", "unknown")
            snippet = src.get("snippet", "")
            context_parts.append(f"[{i}] {name}\n{snippet}")

        context = "\n\n---\n\n".join(context_parts)
        system = GROUNDED_SYSTEM if self.strict_grounded else ANSWER_SYSTEM

        try:
            client = self._get_client()
            resp = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=[{
                    "role": "user",
                    "content": f"Sources:\n\n{context}\n\n---\n\nQuestion: {question}",
                }],
            )
            answer = resp.content[0].text.strip()
            # Infer confidence from answer hedging language
            lower = answer.lower()
            if "cannot" in lower or "don't have" in lower or "not found" in lower:
                confidence = "LOW"
            elif "may" in lower or "might" in lower or "possibly" in lower:
                confidence = "MEDIUM"
            else:
                confidence = "HIGH"
            return answer, confidence
        except Exception as exc:
            return f"LLM answer generation failed: {sanitize_error(str(exc))}", "LOW"
