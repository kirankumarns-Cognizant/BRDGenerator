"""
CLI: Ingest documents from a KB service folder.
Usage: python bin/ingest.py <service_name>
       python bin/ingest.py --all
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Must be set BEFORE any huggingface/sentence-transformers imports
# so that the library skips all network calls and fails fast when
# the model is not already cached (corporate SSL blocks HuggingFace).
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Load .env so ANTHROPIC_API_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Force UTF-8 on Windows terminals
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from kb_gen.core.config_loader import KBStoreConfig
from kb_gen.storage.registry import DocumentRegistry
from kb_gen.hypergraph.structure import DocumentHypergraph
from kb_gen.embeddings.chromadb_embedder import ChromaDBStore
from kb_gen.ingestion.ingestor import DocumentIngestor


def main():
    config = KBStoreConfig()
    registry = DocumentRegistry(str(config.registry_path))
    hypergraph = DocumentHypergraph(str(config.graph_path))
    vector_store = ChromaDBStore(db_path=str(config.embeddings_path))

    ingestor = DocumentIngestor(
        registry, hypergraph,
        kb_root=str(config.kb_root),
        model=config.anthropic_model,
        vector_store=vector_store,
        brd_chunking_enabled=True,
        json_ingestion_enabled=config.json_ingestion_enabled,
    )

    args = sys.argv[1:]
    if not args:
        print("Usage: python bin/ingest.py <service_name>  OR  --all")
        sys.exit(1)

    if args[0] == "--all":
        kb_root = config.kb_root
        services = [d.name for d in kb_root.iterdir() if d.is_dir() and d.name != "graph"]
        for svc in services:
            ingestor.ingest_service(svc)
    else:
        ingestor.ingest_service(args[0])


if __name__ == "__main__":
    main()
