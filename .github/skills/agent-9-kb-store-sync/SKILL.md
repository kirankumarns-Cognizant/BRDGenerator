# Agent 9 KB Store Sync Skill

## Skill Definition
**Name**: Agent 9 KB Store Sync  
**Type**: Knowledge Base Ingestion  
**Language**: PowerShell + Python  
**Agents**: Agent 9  

## Description
Ingests JSON artifacts from `KB/{repo_name}/` into a searchable vector/RAG knowledge base (`kb_store/`) for semantic search, historical pattern analysis, and cross-repository insights.

## Prerequisites
- Python 3.10+ with ChromaDB and sentence-transformers
- JSON artifacts from Agents 1-8 in `KB/{repo_name}/`
- Valid `config.yaml` with vector store configuration

## Invocation

### PowerShell
```powershell
.\agent_9_kb_store_sync.ps1 -RepoPath "C:\path\to\repo"
```

### With Custom kb_store Path
```powershell
.\agent_9_kb_store_sync.ps1 `
    -RepoPath "C:\repos\spring-petclinic" `
    -KbStorePath "D:\knowledge_base" `
    -Verbose
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| RepoPath | string | Yes | - | Path to repository |
| ConfigPath | string | No | config/config.yaml | Config file path |
| KbStorePath | string | No | kb_store/ | Vector store directory |
| Verbose | switch | No | false | Enable verbose logging |

## Dependencies
- **All Agents 1-8**: Requires JSON artifacts from `KB/{repo_name}/`
- **ChromaDB**: Vector database library
- **Sentence Transformers**: For embedding generation

## Key Distinction: KB vs kb_store

| Directory | Purpose | Format | Populated By |
|-----------|---------|--------|--------------|
| **KB/{repo_name}/** | Raw artifacts | JSON files | Agents 1-8 |
| **kb_store/** | Searchable vector DB | Embeddings + indices | Agent 9 |

**Workflow**: Agent 9 **reads** from `KB/{repo_name}/` → **writes** to `kb_store/`

## Outputs

### Files Generated
1. **ingestion_log.json** (in KB/{repo_name}/)
   ```json
   {
     "ingestion_status": "success|partial|failed",
     "source_directory": "KB/spring-petclinic/",
     "target_directory": "kb_store/chromadb/",
     "documents_ingested": 8,
     "embeddings_generated": 243,
     "collection_name": "brd_artifacts",
     "timestamp": "2026-08-12T15:30:00Z",
     "artifacts_processed": [
       {
         "file": "scope_definition.json",
         "chunks": 12,
         "embeddings": 12,
         "status": "success"
       },
       {
         "file": "functional_requirements.json",
         "chunks": 87,
         "embeddings": 87,
         "status": "success"
       }
     ],
     "errors": []
   }
   ```

2. **kb_store/chromadb/** (ChromaDB persistence directory)
   - Vector embeddings
   - Document metadata
   - Search indices

## Sub-Skills
1. **Artifact Parser**: Reads and validates JSON files
2. **Document Chunker**: Splits documents into semantic chunks
3. **Embedding Generator**: Creates vector embeddings
4. **Vector Store Manager**: Manages ChromaDB persistence
5. **Index Builder**: Builds and optimizes search indices
6. **Metadata Extractor**: Enriches embeddings with metadata

## Tools Used
- **ChromaDB** (chromadb_adapter) - Vector database at `kb_store/chromadb/`
- **Sentence Transformers** - Embedding model (all-MiniLM-L6-v2)
- **LangChain** - Text splitters for intelligent chunking

## Ingestion Process

### 1. Artifact Discovery
- Scan `KB/{repo_name}/` for JSON files
- Validate JSON structure
- Extract metadata (timestamps, agent versions, confidence)

### 2. Document Chunking
```python
# Intelligent chunking preserves JSON structure
{
  "scope_definition": {...}  # Chunk 1: Scope info
}
{
  "functional_requirements": [  # Chunks 2-N: One per requirement
    {"id": "FR001", ...},
    {"id": "FR002", ...}
  ]
}
```

**Chunking Strategy:**
- Preserve requirement/rule boundaries
- Max chunk size: 500 tokens (configurable)
- Overlap: 50 tokens (configurable)
- Keep metadata with each chunk

### 3. Embedding Generation
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(chunk_text)  # 384-dimensional vector
```

### 4. ChromaDB Storage
```python
import chromadb

client = chromadb.PersistentClient(path="kb_store/chromadb")
collection = client.get_or_create_collection("brd_artifacts")

collection.add(
    documents=[chunk_text],
    embeddings=[embedding],
    metadatas=[{
        "repo": "spring-petclinic",
        "artifact": "functional_requirements.json",
        "requirement_id": "FR001",
        "agent": "agent5",
        "timestamp": "2026-08-12T10:00:00Z"
    }],
    ids=[unique_id]
)
```

### 5. Indexing
- Build HNSW (Hierarchical Navigable Small World) index
- Optimize for fast approximate nearest neighbor search
- Configure index parameters (ef_construction, M)

## Semantic Search Examples

### Post-Ingestion Queries
```python
# Query 1: Find email validation patterns
results = collection.query(
    query_texts=["email validation requirement"],
    n_results=5,
    where={"artifact": "functional_requirements.json"}
)

# Query 2: Cross-repository pattern analysis
results = collection.query(
    query_texts=["payment gateway integration"],
    n_results=10,
    where={"$or": [
        {"repo": "ecommerce-app"},
        {"repo": "order-service"}
    ]}
)

# Query 3: Risk patterns
results = collection.query(
    query_texts=["authentication security risk"],
    n_results=5,
    where={"artifact": "risk_assessment.json"}
)
```

## Error Handling
- Invalid JSON: Logs error, skips file, continues
- Embedding failure: Retries with exponential backoff
- ChromaDB connection error: Fails with clear message
- Duplicate ingestion: Checks timestamps, updates if newer

## Performance
- Small repos (8 artifacts): ~1-3 minutes
- Medium repos (20 artifacts): ~3-7 minutes
- Large repos (50+ artifacts): ~7-15 minutes

**Performance Factors:**
- Artifact size (larger JSON = more chunks)
- Embedding model (GPU vs CPU)
- ChromaDB index build time

## Examples

### Example 1: Initial Ingestion
```powershell
.\agent_9_kb_store_sync.ps1 -RepoPath "C:\repos\spring-petclinic" -Verbose
```
**Output**: 8 artifacts → 243 chunks → 243 embeddings

### Example 2: Update Existing Knowledge Base
```powershell
# After re-running Agents 1-8 with new analysis
.\agent_9_kb_store_sync.ps1 -RepoPath "C:\repos\spring-petclinic"
```
**Output**: Updated embeddings for changed artifacts

### Example 3: Multiple Repositories
```powershell
# Ingest multiple repos into shared kb_store
.\agent_9_kb_store_sync.ps1 -RepoPath "C:\repos\app1"
.\agent_9_kb_store_sync.ps1 -RepoPath "C:\repos\app2"
.\agent_9_kb_store_sync.ps1 -RepoPath "C:\repos\app3"
```
**Result**: Cross-repository pattern analysis enabled

## Configuration

### config.yaml
```yaml
vector_store:
  provider: "chromadb"
  embedding_model: "all-MiniLM-L6-v2"
  collection_name: "brd_artifacts"
  persistence_directory: "kb_store/chromadb"
  chunk_size: 500
  chunk_overlap: 50
  distance_metric: "cosine"
  index_type: "hnsw"
  index_params:
    ef_construction: 100
    M: 16
```

### Embedding Model Options
| Model | Dimensions | Speed | Quality |
|-------|-----------|-------|---------|
| all-MiniLM-L6-v2 | 384 | Fast | Good |
| all-mpnet-base-v2 | 768 | Medium | Better |
| text-embedding-ada-002 | 1536 | API | Best |

## Metadata Schema

Each embedding includes rich metadata:
```json
{
  "repo": "spring-petclinic",
  "repo_url": "https://github.com/spring-projects/spring-petclinic",
  "artifact": "functional_requirements.json",
  "artifact_type": "requirements",
  "generated_by": "agent5",
  "generated_at": "2026-08-12T10:00:00Z",
  "requirement_id": "FR001",
  "requirement_priority": "must_have",
  "requirement_category": "user_interface",
  "confidence": 0.92,
  "chunk_index": 5,
  "total_chunks": 87
}
```

## HITL Triggers
- **ingestion_failure**: Critical artifacts failed to ingest
- **low_embedding_quality**: Embedding confidence below threshold
- **duplicate_artifacts**: Same artifact from multiple sources

## Integration

### Downstream Usage (Agent 4 Example)
```python
# Agent 4 uses kb_store for gap analysis
from tools.adapters.chromadb_adapter import ChromaDBAdapter

kb_store = ChromaDBAdapter(config_path="config/config.yaml")

# Find similar validation patterns from past projects
similar_patterns = kb_store.search(
    query="email format validation",
    k=5,
    filter={"artifact_type": "business_rules"}
)

# Use patterns to inform gap analysis
for pattern in similar_patterns:
    print(f"Similar pattern from {pattern['repo']}: {pattern['text']}")
```

## Troubleshooting

### Issue: ChromaDB not found
**Cause**: ChromaDB not installed  
**Solution**: `pip install chromadb sentence-transformers`

### Issue: Embeddings take too long
**Cause**: CPU-only computation  
**Solution**: Install GPU-accelerated PyTorch, or use smaller embedding model

### Issue: kb_store grows too large
**Cause**: Many repositories ingested  
**Solution**: Implement retention policy, archive old embeddings

### Issue: Search returns irrelevant results
**Cause**: Embeddings not capturing semantic meaning  
**Solution**: Try different embedding model, adjust chunk size

## Maintenance

### Regular Tasks
1. **Reindex**: Rebuild indices after large ingestions
2. **Cleanup**: Remove orphaned embeddings
3. **Backup**: Backup `kb_store/chromadb/` directory
4. **Monitor**: Check ingestion logs for errors

### Backup Strategy
```powershell
# Backup kb_store
$backupPath = "kb_store_backup_$(Get-Date -Format 'yyyyMMdd')"
Copy-Item -Path "kb_store" -Destination $backupPath -Recurse

# Compress backup
Compress-Archive -Path $backupPath -DestinationPath "$backupPath.zip"
```

## See Also
- `.github/agents/subagents/agent-9-kb-store-sync.agent.md`
- ChromaDB documentation: https://docs.trychroma.com/
- Sentence Transformers: https://www.sbert.net/
- `config/config.yaml` - Vector store configuration
- `kb_store/README.md` - Knowledge base structure
- `KB/README.md` - Artifact storage structure
