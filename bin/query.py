"""
CLI: Interactive RAG query.
Usage: python bin/query.py "What are the acceptance criteria?"
       python bin/query.py  (launches interactive mode)
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from kb_gen.core.config_loader import KBStoreConfig
from kb_gen.storage.registry import DocumentRegistry
from kb_gen.hypergraph.structure import DocumentHypergraph
from kb_gen.embeddings.chromadb_embedder import ChromaDBStore
from kb_gen.rag.query_engine import RAGQueryEngine


def main():
    config = KBStoreConfig()
    registry = DocumentRegistry(str(config.registry_path))
    hypergraph = DocumentHypergraph(str(config.graph_path))
    vector_store = ChromaDBStore(db_path=str(config.embeddings_path))

    engine = RAGQueryEngine(
        registry=registry,
        vector_store=vector_store,
        hypergraph=hypergraph,
        model=config.anthropic_model,
        top_k=config.top_k_sources,
        use_graph_expansion=config.use_graph_expansion,
        strict_grounded=config.strict_grounded,
    )

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        _run_query(engine, question)
        return

    print("KB RAG Query — interactive mode (Ctrl+C to exit)")
    while True:
        try:
            question = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not question:
            continue
        _run_query(engine, question)


def _run_query(engine, question: str):
    print(f"\nQuerying: {question}")
    result = engine.query(question)
    print(f"\nIntent: {result['intent']}  |  Confidence: {result['confidence']}")
    print(f"Method: {result['retrieval_method']}  |  Sources: {len(result['sources'])}")
    print("\n" + "-" * 60)
    print(result["answer"])
    print("-" * 60)
    if result["sources"]:
        print("\nSources:")
        for i, src in enumerate(result["sources"], 1):
            print(f"  [{i}] {src['name']} (score: {src['score']})")


if __name__ == "__main__":
    main()
