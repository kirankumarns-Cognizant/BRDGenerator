"""
ChromaDB Adapter for Vector Store Operations
Provides interface to ChromaDB for document storage and retrieval.
"""

from typing import Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

class ChromaDBAdapter:
    def __init__(self, config=None):
        self.config = config
        self.client = None
        
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is not installed. Install with: pip install chromadb")
        
        # Initialize ChromaDB client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client"""
        if self.config:
            kb_store_path = self.config.get_kb_store_dir()
            persist_directory = kb_store_path
        else:
            persist_directory = "./kb_store"
        
        self.client = chromadb.PersistentClient(path=persist_directory)
    
    def add_document(self, collection_name: str, document: str, metadata: Dict, doc_id: str):
        """
        Add a document to ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            document: Document text content
            metadata: Document metadata
            doc_id: Unique document ID
        """
        collection = self.client.get_or_create_collection(name=collection_name)
        
        collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
    
    def query_documents(self, collection_name: str, query_text: str, n_results: int = 5) -> List[Dict]:
        """
        Query documents from ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            query_text: Query text
            n_results: Number of results to return
            
        Returns:
            List of matching documents with metadata
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            return results
        except Exception as e:
            print(f"Error querying documents: {e}")
            return []
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get count of documents in collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            return collection.count()
        except:
            return 0
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except:
            return []
