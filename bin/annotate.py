"""
CLI: HITL annotation after a RAG query session.
Usage: python bin/annotate.py --query "What are the business rules?"
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from kb_gen.core.config_loader import KBStoreConfig
from kb_gen.storage.registry import DocumentRegistry
from kb_gen.hypergraph.structure import DocumentHypergraph
from kb_gen.embeddings.chromadb_embedder import ChromaDBStore
from kb_gen.rag.query_engine import RAGQueryEngine
from kb_gen.hitl.feedback_store import FeedbackStore
from kb_gen.hitl.annotation_tool import AnnotationTool


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HITL annotation for RAG results")
    parser.add_argument("--query", required=True, help="Query to annotate")
    args = parser.parse_args()

    config = KBStoreConfig()
    registry = DocumentRegistry(str(config.registry_path))
    hypergraph = DocumentHypergraph(str(config.graph_path))
    vector_store = ChromaDBStore(db_path=str(config.embeddings_path))

    engine = RAGQueryEngine(
        registry=registry,
        vector_store=vector_store,
        hypergraph=hypergraph,
        model=config.anthropic_model,
    )

    result = engine.query(args.query)
    print(f"\nAnswer: {result['answer'][:300]}...")

    feedback_store = FeedbackStore()
    tool = AnnotationTool(feedback_store, registry=registry)
    tool.annotate_query(args.query, result["sources"], intent=result["intent"])


if __name__ == "__main__":
    main()
