#!/usr/bin/env python3
"""
Cross-Agent Skill: Code Analysis
Analyzes Java code patterns, architectural designs, and business logic.
Used by multiple agents for code understanding.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config_loader import ConfigLoader

# Try to import real code analyzer, fallback to mock if unavailable
try:
    from kb_gen.analysis.code_analyzer import CodeAnalyzer
    REAL_ANALYZER_AVAILABLE = True
except ImportError:
    REAL_ANALYZER_AVAILABLE = False
    class CodeAnalyzer:
        """Mock analyzer fallback."""
        def __init__(self, config=None):
            self.config = config


class CodeAnalysisSkill:
    """Code analysis skill for cross-agent usage - Uses real kb_gen logic."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigLoader(config_path or "config/config.yaml")
        self.real_available = REAL_ANALYZER_AVAILABLE
        
        # Initialize real analyzer if available
        if self.real_available:
            try:
                self.analyzer = CodeAnalyzer(self.config)
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize real code analyzer: {e}")
                self.analyzer = None
        else:
            self.analyzer = None
    
    def analyze_patterns(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze design patterns in Java file using real kb_gen logic.
        
        Args:
            file_path: Path to Java source file
        
        Returns:
            Dictionary with pattern analysis results
        """
        # Try real analyzer first
        if self.analyzer:
            try:
                result = self.analyzer.analyze_patterns(file_path)
                if result:
                    return {**result, "kb_gen_used": True}
            except Exception as e:
                import logging
                logging.error(f"Real analyzer failed: {e}")
        
        # Fallback to mock pattern detection
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        with open(file_path) as f:
            content = f.read()
        
        patterns = self._detect_patterns(content)
        return {"file": file_path, "patterns": patterns}
    
    def analyze_architecture(self, repo_path: str) -> Dict[str, Any]:
        """
        Analyze overall architecture of repository.
        
        Args:
            repo_path: Path to Java repository
        
        Returns:
            Dictionary with architecture analysis
        """
        if not os.path.exists(repo_path):
            return {"error": f"Repository not found: {repo_path}"}
        
        architecture = self._build_architecture_map(repo_path)
        return {"repository": repo_path, "architecture": architecture}
    
    def extract_business_logic(self, file_path: str) -> Dict[str, Any]:
        """
        Extract business logic from code.
        
        Args:
            file_path: Path to Java source file
        
        Returns:
            Dictionary with business logic components
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        with open(file_path) as f:
            content = f.read()
        
        logic = self._extract_logic(content)
        return {"file": file_path, "business_logic": logic}
    
    def _detect_patterns(self, code: str) -> List[Dict[str, str]]:
        """Detect design patterns in code."""
        patterns = []
        pattern_keywords = {
            "Singleton": ["static.*instance", "synchronized.*getInstance"],
            "Factory": [".*Factory", "create.*"],
            "Observer": ["addListener", "removeListener", "notify"],
            "Decorator": ["wraps", "delegate"],
            "Strategy": [".*Strategy", "setStrategy", "execute"],
        }
        
        for pattern_name, keywords in pattern_keywords.items():
            for keyword in keywords:
                import re
                if re.search(keyword, code, re.IGNORECASE):
                    patterns.append({"pattern": pattern_name, "keyword": keyword})
        
        return patterns
    
    def _build_architecture_map(self, repo_path: str) -> Dict[str, Any]:
        """Build architecture overview."""
        layers = {"presentation": [], "business": [], "data": [], "utility": []}
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".java"):
                    path = os.path.join(root, file)
                    layer = self._classify_layer(path)
                    if layer:
                        layers[layer].append(path)
        
        return layers
    
    def _classify_layer(self, file_path: str) -> str:
        """Classify file to architecture layer."""
        path_lower = file_path.lower()
        if any(x in path_lower for x in ["controller", "action", "servlet", "view"]):
            return "presentation"
        elif any(x in path_lower for x in ["service", "business", "manager"]):
            return "business"
        elif any(x in path_lower for x in ["dao", "repository", "mapper", "entity"]):
            return "data"
        else:
            return "utility"
    
    def _extract_logic(self, code: str) -> List[Dict[str, str]]:
        """Extract business logic components."""
        logic = []
        import re
        
        # Extract methods
        method_pattern = r"public\s+\w+\s+(\w+)\s*\("
        for match in re.finditer(method_pattern, code):
            logic.append({"type": "method", "name": match.group(1)})
        
        # Extract conditional logic
        if_pattern = r"if\s*\("
        logic_count = len(re.findall(if_pattern, code))
        if logic_count > 0:
            logic.append({"type": "conditional_logic", "count": logic_count})
        
        return logic


def main():
    """CLI entry point for code analysis."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Code Analysis Skill")
    parser.add_argument("action", choices=["analyze-patterns", "analyze-architecture", "extract-logic"])
    parser.add_argument("path", help="File or repository path")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    skill = CodeAnalysisSkill(args.config)
    
    if args.action == "analyze-patterns":
        result = skill.analyze_patterns(args.path)
    elif args.action == "analyze-architecture":
        result = skill.analyze_architecture(args.path)
    else:  # extract-logic
        result = skill.extract_business_logic(args.path)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    main()
