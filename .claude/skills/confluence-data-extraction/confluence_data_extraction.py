#!/usr/bin/env python3
"""
Cross-Agent Skill: Confluence Data Extraction
Extracts data from Confluence spaces and pages for knowledge enrichment.
Used by multiple agents for external data integration.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config_loader import ConfigLoader

# Try to import real confluence loader, fallback to mock if unavailable
try:
    from kb_gen.ingestion.confluence_loader import ConfluenceLoader
    REAL_LOADER_AVAILABLE = True
except ImportError:
    REAL_LOADER_AVAILABLE = False
    class ConfluenceLoader:
        """Mock loader fallback."""
        def __init__(self, config=None):
            self.config = config


class ConfluenceDataExtractionSkill:
    """Confluence data extraction skill for cross-agent usage - Uses real kb_gen logic."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigLoader(config_path or "config/config.yaml")
        self.real_available = REAL_LOADER_AVAILABLE
        self.confluence_enabled = self.config.is_tool_enabled("agents", "confluence_loader") if hasattr(self.config, 'is_tool_enabled') else False
        self.api_token = self.config.get("confluence", {}).get("api_token") if hasattr(self.config, 'get') else None
        self.space_url = self.config.get("confluence", {}).get("space_url") if hasattr(self.config, 'get') else None
        
        # Initialize real loader if available
        if self.real_available and self.confluence_enabled:
            try:
                self.loader = ConfluenceLoader(self.config)
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize real Confluence loader: {e}")
                self.loader = None
        else:
            self.loader = None
    
    def extract_from_space(self, space_key: str) -> Dict[str, Any]:
        """
        Extract all pages from a Confluence space using real kb_gen logic.
        
        Args:
            space_key: Confluence space key (e.g., "BRD")
        
        Returns:
            Dictionary with space content and metadata
        """
        # Try real loader first
        if self.loader:
            try:
                result = self.loader.extract_from_space(space_key)
                if result:
                    return {**result, "kb_gen_used": True}
            except Exception as e:
                import logging
                logging.error(f"Real Confluence loader failed: {e}")
        
        # Fallback to mock response
        if not self.confluence_enabled:
            return {
                "status": "disabled",
                "message": "Confluence integration is disabled in config",
                "suggestion": "Enable in config.yaml: confluence.enabled: true"
            }
        
        if not self.api_token or not self.space_url:
            return {
                "status": "error",
                "message": "Confluence credentials not configured",
                "suggestion": "Configure in config.yaml: confluence.api_token and confluence.space_url"
            }
        
        # Mock implementation
        return {
            "space_key": space_key,
            "status": "ok",
            "pages": [],
            "page_count": 0,
            "last_updated": None,
            "note": "To use real Confluence API, install: pip install atlassian-python-api"
        }
    
    def search_confluence(self, query: str, space_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Search Confluence for content.
        
        Args:
            query: Search query
            space_key: Optional space key to limit search
        
        Returns:
            Dictionary with search results
        """
        if not self.confluence_enabled:
            return {
                "status": "disabled",
                "query": query,
                "results": []
            }
        
        # Mock implementation
        return {
            "query": query,
            "space_key": space_key,
            "results": [],
            "total_results": 0,
            "note": "Real Confluence search requires API credentials"
        }
    
    def extract_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Extract content from a specific Confluence page.
        
        Args:
            page_id: Confluence page ID
        
        Returns:
            Dictionary with page content
        """
        if not self.confluence_enabled:
            return {
                "status": "disabled",
                "page_id": page_id,
                "content": None
            }
        
        # Mock implementation
        return {
            "page_id": page_id,
            "title": None,
            "content": None,
            "metadata": {},
            "note": "Real Confluence extraction requires API credentials"
        }
    
    def extract_page_hierarchy(self, space_key: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract page hierarchy from Confluence space.
        
        Args:
            space_key: Confluence space key
            parent_id: Optional parent page ID
        
        Returns:
            Dictionary with page hierarchy
        """
        if not self.confluence_enabled:
            return {
                "status": "disabled",
                "space_key": space_key,
                "hierarchy": []
            }
        
        # Mock implementation
        return {
            "space_key": space_key,
            "parent_id": parent_id,
            "pages": [],
            "depth": 0,
            "note": "Real hierarchy extraction requires API credentials"
        }
    
    def batch_extract_pages(self, page_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Extract content from multiple pages.
        
        Args:
            page_ids: List of Confluence page IDs
        
        Returns:
            List of page content dictionaries
        """
        if not self.confluence_enabled:
            return [{"status": "disabled"} for _ in page_ids]
        
        results = []
        for page_id in page_ids:
            result = self.extract_page_content(page_id)
            results.append(result)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get Confluence integration status."""
        return {
            "enabled": self.confluence_enabled,
            "configured": bool(self.api_token and self.space_url),
            "space_url": self.space_url if self.space_url else "Not configured",
            "note": "Credentials are not exposed for security reasons"
        }


def main():
    """CLI entry point for Confluence extraction."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Confluence Data Extraction Skill")
    parser.add_argument("action", choices=["extract-space", "search", "extract-page", "status"])
    parser.add_argument("--space-key", help="Confluence space key")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--page-id", help="Confluence page ID")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    skill = ConfluenceDataExtractionSkill(args.config)
    
    if args.action == "extract-space":
        if not args.space_key:
            print("Error: --space-key required for extract-space action")
            return
        result = skill.extract_from_space(args.space_key)
    elif args.action == "search":
        if not args.query:
            print("Error: --query required for search action")
            return
        result = skill.search_confluence(args.query, args.space_key)
    elif args.action == "extract-page":
        if not args.page_id:
            print("Error: --page-id required for extract-page action")
            return
        result = skill.extract_page_content(args.page_id)
    else:  # status
        result = skill.get_status()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    main()
