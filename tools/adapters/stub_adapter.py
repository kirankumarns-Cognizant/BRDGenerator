"""
Stub Adapter - Fallback adapter when real implementations are disabled
Returns minimal/mock data for disabled tools
"""

class StubAdapter:
    """Stub adapter that returns minimal data for disabled tools"""
    
    def __init__(self, config=None):
        self.config = config
    
    def scan_repo(self, repo_path: str):
        """Return empty repo scan results"""
        return {
            "source_files": [],
            "config_files": [],
            "documentation": [],
            "test_files": [],
            "build_files": [],
            "total_files": 0,
            "confidence": 0.5,
            "message": "Using stub adapter - tool disabled"
        }
    
    def add_document(self, *args, **kwargs):
        """Stub for adding documents"""
        pass
    
    def query_documents(self, *args, **kwargs):
        """Stub for querying documents"""
        return []
    
    def __getattr__(self, name):
        """Return a no-op function for any undefined method"""
        def stub_method(*args, **kwargs):
            return None
        return stub_method
