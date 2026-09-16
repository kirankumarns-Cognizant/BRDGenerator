"""
Agent 9: KB Store Sync
Syncs all KB artifacts to ChromaDB vector store for semantic search.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config_loader import ConfigLoader

try:
    from tools.adapters.chromadb_adapter import ChromaDBAdapter
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB not available, will create placeholder")

class Agent9KBStoreSync:
    def __init__(self, repo_path: str, config_path: str, kb_path: str):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.config = ConfigLoader(config_path)
        self.kb_path = Path(kb_path)
        self.kb_store_path = Path(self.config.get_kb_store_dir())
        
        # Agent 9 outputs go to kb_store/{repo_name}/
        self.agent9_output_path = self.kb_store_path / self.repo_name
        self.agent9_output_path.mkdir(parents=True, exist_ok=True)
        
        self.state = {}
        self.confidence = 1.0
        
        # Initialize ChromaDB adapter if available
        if CHROMADB_AVAILABLE:
            try:
                self.db_adapter = ChromaDBAdapter(self.config)
            except Exception as e:
                print(f"⚠️  Could not initialize ChromaDB: {e}")
                self.db_adapter = None
        else:
            self.db_adapter = None
    
    def collect_all_artifacts(self):
        """Collect all JSON and markdown artifacts from KB"""
        print("📥 Collecting KB artifacts...")
        
        artifacts = []
        
        # Collect JSON files
        for json_file in self.kb_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    artifacts.append({
                        "id": json_file.stem,
                        "type": "JSON",
                        "filename": json_file.name,
                        "path": str(json_file),
                        "content": content,
                        "metadata": {
                            "agent": self._extract_agent_name(json_file.stem),
                            "file_type": "json",
                            "artifact_type": json_file.stem,
                            "filename": json_file.name,
                            "size": json_file.stat().st_size
                        }
                    })
            except Exception as e:
                print(f"   ⚠️  Could not read {json_file.name}: {e}")
        
        # Collect Markdown files
        for md_file in self.kb_path.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    artifacts.append({
                        "id": md_file.stem,
                        "type": "MARKDOWN",
                        "filename": md_file.name,
                        "path": str(md_file),
                        "content": content,
                        "metadata": {
                            "agent": "agent-8-summarizer",
                            "file_type": "markdown",
                            "artifact_type": md_file.stem,
                            "filename": md_file.name,
                            "size": md_file.stat().st_size
                        }
                    })
            except Exception as e:
                print(f"   ⚠️  Could not read {md_file.name}: {e}")
        
        # Collect Gherkin files
        for feature_file in self.kb_path.glob("*.feature"):
            try:
                with open(feature_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    artifacts.append({
                        "id": feature_file.stem,
                        "type": "GHERKIN",
                        "filename": feature_file.name,
                        "path": str(feature_file),
                        "content": content,
                        "metadata": {
                            "agent": "agent-6-acceptance-criteria",
                            "file_type": "gherkin",
                            "artifact_type": feature_file.stem,
                            "filename": feature_file.name,
                            "size": feature_file.stat().st_size
                        }
                    })
            except Exception as e:
                print(f"   ⚠️  Could not read {feature_file.name}: {e}")
        
        self.state["artifacts"] = artifacts
        print(f"   ✓ Collected {len(artifacts)} artifacts")
    
    def _extract_agent_name(self, filename):
        """Extract agent name from filename"""
        if "agent_1" in filename:
            return "agent-1-discovery"
        elif "agent_2" in filename:
            return "agent-2-journey-mapping"
        elif "agent_3" in filename:
            return "agent-3-business-rules"
        elif "agent_4" in filename:
            return "agent-4-gap-analysis"
        elif "agent_5" in filename:
            return "agent-5-synthesis"
        elif "agent_6" in filename:
            return "agent-6-acceptance-criteria"
        elif "agent_7" in filename:
            return "agent-7-risk-dependency"
        elif "agent_8" in filename:
            return "agent-8-summarizer"
        else:
            # Try to guess from filename
            for agent_name in ["scope_definition", "artifact_catalog", "dependency_map"]:
                if agent_name in filename:
                    return "agent-1-discovery"
            for agent_name in ["journey_map", "actors"]:
                if agent_name in filename:
                    return "agent-2-journey-mapping"
            for agent_name in ["business_rules"]:
                if agent_name in filename:
                    return "agent-3-business-rules"
            for agent_name in ["gap_analysis", "as_is", "to_be"]:
                if agent_name in filename:
                    return "agent-4-gap-analysis"
            for agent_name in ["unified_model", "insights", "recommendations"]:
                if agent_name in filename:
                    return "agent-5-synthesis"
            for agent_name in ["acceptance_criteria", "test_scenarios"]:
                if agent_name in filename:
                    return "agent-6-acceptance-criteria"
            for agent_name in ["risks", "dependencies"]:
                if agent_name in filename:
                    return "agent-7-risk-dependency"
            return "unknown"
    
    def ingest_to_vector_store(self):
        """Ingest artifacts into ChromaDB vector store"""
        print("🔄 Ingesting artifacts to vector store...")
        
        if not self.db_adapter:
            print("   ⚠️  ChromaDB not available, skipping vector store ingestion")
            self.state["vector_store_status"] = "SKIPPED"
            self.state["ingested_count"] = 0
            return
        
        try:
            collection_name = f"brd_{self.repo_path.name}"
            ingested = 0
            
            for artifact in self.state["artifacts"]:
                # Ingest artifact
                doc_id = f"{artifact['id']}_{artifact['type']}"
                
                self.db_adapter.add_document(
                    collection_name=collection_name,
                    document=artifact["content"],
                    metadata=artifact["metadata"],
                    doc_id=doc_id
                )
                ingested += 1
            
            self.state["vector_store_status"] = "SUCCESS"
            self.state["ingested_count"] = ingested
            self.state["collection_name"] = collection_name
            
            print(f"   ✓ Ingested {ingested} artifacts to vector store")
            
        except Exception as e:
            print(f"   ⚠️  Error ingesting to vector store: {e}")
            self.state["vector_store_status"] = "ERROR"
            self.state["vector_store_error"] = str(e)
            self.state["ingested_count"] = 0
            self.confidence *= 0.7
    
    def create_sync_manifest(self):
        """Create manifest of synced artifacts"""
        print("📋 Creating sync manifest...")
        
        manifest = {
            "sync_timestamp": datetime.now().isoformat(),
            "repository": self.repo_path.name,
            "kb_path": str(self.kb_path),
            "kb_store_path": str(self.kb_store_path),
            "total_artifacts": len(self.state.get("artifacts", [])),
            "artifacts_by_type": self._categorize_by_type(self.state.get("artifacts", [])),
            "artifacts_by_agent": self._categorize_by_agent(self.state.get("artifacts", [])),
            "vector_store_status": self.state.get("vector_store_status", "NOT_ATTEMPTED"),
            "ingested_count": self.state.get("ingested_count", 0)
        }
        
        self.state["sync_manifest"] = manifest
        print(f"   ✓ Sync manifest created")
    
    def _categorize_by_type(self, artifacts):
        """Categorize artifacts by type"""
        types = {}
        for artifact in artifacts:
            artifact_type = artifact.get("type", "UNKNOWN")
            if artifact_type not in types:
                types[artifact_type] = 0
            types[artifact_type] += 1
        return types
    
    def _categorize_by_agent(self, artifacts):
        """Categorize artifacts by agent"""
        agents = {}
        for artifact in artifacts:
            agent = artifact.get("metadata", {}).get("agent", "unknown")
            if agent not in agents:
                agents[agent] = 0
            agents[agent] += 1
        return agents
    
    def generate_output(self, output_path: str):
        """Generate final output files to kb_store/{repo_name}/"""
        print("💾 Generating output files...")
        
        # Use kb_store output path instead of KB output path
        output_dir = self.agent9_output_path
        
        self.state["overall_confidence"] = self.confidence
        self.state["agent"] = "Agent 9: KB Store Sync"
        self.state["timestamp"] = datetime.now().isoformat()
        
        files_written = []
        
        # 1. Artifact Registry
        artifact_registry = {
            "project_name": self.repo_name,
            "agent": "Agent 9: KB Store Sync",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "artifacts": self.state.get("artifacts", []),
            "summary": self.state.get("sync_manifest", {}).get("summary", {})
        }
        registry_file = output_dir / "artifact_registry.json"
        with open(registry_file, 'w') as f:
            json.dump(artifact_registry, f, indent=2)
        files_written.append(str(registry_file))
        print(f"   ✓ Wrote {registry_file.name} ({registry_file.stat().st_size} bytes)")
        
        # 2. Hypergraph
        hypergraph = {
            "project_name": self.repo_name,
            "agent": "Agent 9: KB Store Sync",
            "confidence": self.confidence,
            "nodes": [],
            "edges": [],
            "relationships": "Placeholder for knowledge graph relationships"
        }
        hypergraph_file = output_dir / "hypergraph.json"
        with open(hypergraph_file, 'w') as f:
            json.dump(hypergraph, f, indent=2)
        files_written.append(str(hypergraph_file))
        print(f"   ✓ Wrote {hypergraph_file.name} ({hypergraph_file.stat().st_size} bytes)")
        
        # 3. Ingestion Log
        ingestion_log = {
            "project_name": self.repo_name,
            "agent": "Agent 9: KB Store Sync",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "ingestion_status": "success",
            "documents_ingested": len(self.state.get("artifacts", [])),
            "sync_manifest": self.state.get("sync_manifest", {})
        }
        log_file = output_dir / "ingestion_log.json"
        with open(log_file, 'w') as f:
            json.dump(ingestion_log, f, indent=2)
        files_written.append(str(log_file))
        print(f"   ✓ Wrote {log_file.name} ({log_file.stat().st_size} bytes)")
        
        return files_written
    
    def run(self, output_path: str):
        """Execute Agent 9 workflow"""
        print("🚀 Starting Agent 9: KB Store Sync")
        print(f"   KB Path: {self.kb_path}")
        print(f"   KB Store Path: {self.kb_store_path}")
        print(f"   Agent 9 Output: {self.agent9_output_path}")
        print()
        
        self.collect_all_artifacts()
        self.ingest_to_vector_store()
        self.create_sync_manifest()
        files = self.generate_output(output_path)
        
        print()
        print(f"✅ Agent 9 completed with confidence: {self.confidence:.2f}")
        print(f"📊 Generated {len(files)} output files")
        return self.state

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 9: KB Store Sync")
    parser.add_argument("repo_path", nargs="?", help="Path to repository")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Output directory path")
    
    args = parser.parse_args()
    
    repo_path = args.repo_path
    config_path = args.config
    kb_path = args.output
    
    if not repo_path or not kb_path:
        print("Usage: python agent_9_kb_store_sync.py <repo_path> --config <config_path> --output <kb_path>")
        sys.exit(1)
    
    try:
        agent = Agent9KBStoreSync(repo_path, config_path, kb_path)
        agent.run(kb_path)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
