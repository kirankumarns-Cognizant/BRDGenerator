"""
FastAPI server for KB Store & RAG.
Starts on port 8081 (configurable via PORT env var).

Usage: python bin/api_server.py
"""
import os
import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    raise ImportError("FastAPI/Uvicorn not installed. Run: pip install fastapi uvicorn")

from kb_gen.core.config_loader import KBStoreConfig
from kb_gen.storage.registry import DocumentRegistry
from kb_gen.hypergraph.structure import DocumentHypergraph
from kb_gen.embeddings.chromadb_embedder import ChromaDBStore
from kb_gen.ingestion.ingestor import DocumentIngestor
from kb_gen.rag.query_engine import RAGQueryEngine

# ── Init ──────────────────────────────────────────────────────────────────────
config = KBStoreConfig()
registry = DocumentRegistry(str(config.registry_path))
hypergraph = DocumentHypergraph(str(config.graph_path))
vector_store = ChromaDBStore(db_path=str(config.embeddings_path))

rag_engine = RAGQueryEngine(
    registry=registry,
    vector_store=vector_store,
    hypergraph=hypergraph,
    model=config.anthropic_model,
    top_k=config.top_k_sources,
    use_graph_expansion=config.use_graph_expansion,
    strict_grounded=config.strict_grounded,
    enable_reranker=config.enable_reranker,
)

app = FastAPI(title="KB Store & RAG API", version="1.0.0")

# ── Request/response models ──────────────────────────────────────────────────

class IngestDocumentRequest(BaseModel):
    file_path: str
    service: str
    artifact_type: str = ""

class IngestResetRequest(BaseModel):
    service_name: str

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    use_graph_expansion: bool = True
    strict_grounded: bool = True
    bypass_cache: bool = False

class LocalQueryRequest(BaseModel):
    question: str
    top_k: int = 5

# ── Ingestion endpoints ───────────────────────────────────────────────────────

@app.post("/ingest/service/{service_name}")
def ingest_service(service_name: str):
    ingestor = DocumentIngestor(
        registry, hypergraph,
        kb_root=str(config.kb_root),
        model=config.anthropic_model,
        vector_store=vector_store,
        brd_chunking_enabled=True,
        json_ingestion_enabled=config.json_ingestion_enabled,
    )
    result = ingestor.ingest_service(service_name)
    return result

@app.post("/ingest/document")
def ingest_document(req: IngestDocumentRequest):
    ingestor = DocumentIngestor(
        registry, hypergraph,
        kb_root=str(config.kb_root),
        model=config.anthropic_model,
        vector_store=vector_store,
    )
    from pathlib import Path as P
    result = ingestor.ingest_file(P(req.file_path), service=req.service)
    return {"result": result, "file_path": req.file_path}

@app.post("/ingest/reset")
def ingest_reset(req: IngestResetRequest):
    docs = registry.get_service_documents(req.service_name)
    for doc in docs:
        aid = doc.get("artifact_id", "")
        if aid:
            registry.remove_document(aid)
            hypergraph.remove_node(aid)
            try:
                vector_store.delete(aid)
            except Exception:
                pass
    return {"service": req.service_name, "removed": len(docs)}

# ── Query endpoints ───────────────────────────────────────────────────────────

@app.post("/query")
def query(req: QueryRequest):
    rag_engine.top_k = req.top_k
    rag_engine.use_graph_expansion = req.use_graph_expansion
    rag_engine.strict_grounded = req.strict_grounded
    return rag_engine.query(req.question, bypass_cache=req.bypass_cache)


# ── Cache endpoints ───────────────────────────────────────────────────────────

@app.get("/cache/stats")
def cache_stats():
    return rag_engine.cache.stats()

@app.get("/cache/questions")
def cache_questions():
    return {"questions": rag_engine.cache.list_questions()}

@app.delete("/cache")
def cache_clear():
    count = rag_engine.cache.clear()
    return {"cleared": count}

@app.delete("/cache/question")
def cache_invalidate(question: str):
    removed = rag_engine.cache.invalidate(question)
    return {"removed": removed, "question": question}

@app.post("/cache/purge_expired")
def cache_purge_expired():
    count = rag_engine.cache.purge_expired()
    return {"purged": count}

@app.post("/query/local")
def query_local(req: LocalQueryRequest):
    from kb_gen.rag.local_rag import LocalRAG
    local = LocalRAG(registry)
    results = local.search(req.question, top_k=req.top_k)
    return {
        "results": [
            {"artifact_id": aid, "score": score, "name": meta.get("name", "")}
            for aid, score, meta in results
        ]
    }

# ── Registry endpoints ────────────────────────────────────────────────────────

@app.get("/registry/documents")
def list_documents():
    return {"documents": registry.get_all_documents(), "count": registry.count()}

@app.get("/registry/documents/{artifact_id}")
def get_document(artifact_id: str):
    doc = registry.get_document(artifact_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {artifact_id} not found")
    return doc

@app.get("/registry/services")
def list_services():
    return {"services": registry.list_services()}

@app.delete("/registry/documents/{artifact_id}")
def delete_document(artifact_id: str):
    doc = registry.get_document(artifact_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    registry.remove_document(artifact_id)
    hypergraph.remove_node(artifact_id)
    try:
        vector_store.delete(artifact_id)
    except Exception:
        pass
    return {"deleted": artifact_id}

# ── Graph endpoints ───────────────────────────────────────────────────────────

@app.get("/graph/nodes")
def graph_nodes():
    return {"nodes": hypergraph.list_nodes(), "count": hypergraph.node_count()}

@app.get("/graph/edges")
def graph_edges():
    return {"edges": hypergraph.list_edges(), "count": hypergraph.edge_count()}

@app.get("/graph/related/{artifact_id}")
def graph_related(artifact_id: str, max_depth: int = 2):
    related = hypergraph.find_related(artifact_id, max_depth=max_depth)
    return {"artifact_id": artifact_id, "related": related}

# ── Health & config ───────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "registry_count": registry.count(),
        "embeddings_count": vector_store.count(),
    }

@app.get("/config")
def get_config():
    return {
        "kb_root": str(config.kb_root),
        "registry_path": str(config.registry_path),
        "embeddings_path": str(config.embeddings_path),
        "anthropic_model": config.anthropic_model,
        "top_k_sources": config.top_k_sources,
        "use_graph_expansion": config.use_graph_expansion,
        "strict_grounded": config.strict_grounded,
    }

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8081"))
    print(f"Starting KB Store API on port {port}…")
    uvicorn.run(app, host="0.0.0.0", port=port)
