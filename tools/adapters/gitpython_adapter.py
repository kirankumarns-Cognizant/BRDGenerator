"""
GitPython Adapter for Repository Scanning
Scans Git repositories and extracts file information with multi-language support.
"""

import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Set
import time


class GitPythonAdapter:
    def __init__(self, config=None):
        self.config = config or {}
        self._load_language_configs()
        self._load_retry_config()
    
    def _load_language_configs(self):
        """Load language configurations from config."""
        self.supported_languages = self.config.get('supported_languages', {})
        
        # Build unified sets from all languages
        self.all_source_extensions = set()
        self.all_config_extensions = set()
        self.all_framework_indicators = set()
        
        for lang_config in self.supported_languages.values():
            self.all_source_extensions.update(lang_config.get('source_extensions', []))
            self.all_config_extensions.update(lang_config.get('config_extensions', []))
            self.all_framework_indicators.update(lang_config.get('framework_indicators', []))
    
    def _load_retry_config(self):
        """Load retry configuration."""
        retry_config = self.config.get('adapter_retry', {})
        self.max_attempts = retry_config.get('max_attempts', 3)
        self.backoff_multiplier = retry_config.get('backoff_multiplier', 2)
        self.initial_delay = retry_config.get('initial_delay_seconds', 1)
        self.max_delay = retry_config.get('max_delay_seconds', 30)
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        delay = self.initial_delay
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    time.sleep(min(delay, self.max_delay))
                    delay *= self.backoff_multiplier
                else:
                    raise last_exception
    
    def _detect_primary_language(self, source_files: List[str]) -> str:
        """Detect primary programming language based on file counts."""
        if not source_files:
            return "unknown"
        
        lang_counts = {}
        for lang_name, lang_config in self.supported_languages.items():
            extensions = lang_config.get('source_extensions', [])
            count = sum(1 for f in source_files if any(f.endswith(ext) for ext in extensions))
            if count > 0:
                lang_counts[lang_name] = count
        
        if not lang_counts:
            return "unknown"
        
        return max(lang_counts.items(), key=lambda x: x[1])[0]
    
    def _matches_test_pattern(self, file_path: str, lang_config: Dict) -> bool:
        """Check if file matches test patterns for a language."""
        test_patterns = lang_config.get('test_patterns', [])
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in test_patterns)
    
    def _scan_repo_internal(self, repo_path: Path) -> Dict:
        """Internal scan method (for retry wrapper)."""
        # Validate path security
        repo_path = repo_path.resolve()
        if not self._is_safe_path(repo_path):
            raise ValueError(f"Unsafe repository path: {repo_path}")
        
        if not repo_path.exists():
            return {
                "source_files": [],
                "config_files": [],
                "documentation": [],
                "test_files": [],
                "build_files": [],
                "framework_indicators": [],
                "detected_languages": [],
                "primary_language": "unknown",
                "total_files": 0,
                "confidence": 0.0,
                "error": f"Repository path not found: {repo_path}"
            }
        
        source_files = []
        config_files = []
        documentation = []
        test_files = []
        build_files = []
        framework_indicators = []
        
        # Documentation extensions
        doc_extensions = {'.md', '.txt', '.rst', '.adoc', '.markdown'}
        
        # Directories to skip (security and performance)
        skip_dirs = {'.git', '.svn', 'node_modules', 'target', 'build', 'dist', 
                    '.venv', 'venv', '__pycache__', '.idea', '.vscode', 'vendor',
                    'bin', 'obj', '.gradle', '.mvn'}
        
        for root, dirs, files in os.walk(repo_path):
            # Remove skip directories from dirs to prevent walking into them
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(repo_path)
                rel_path_str = str(rel_path).replace('\\', '/')  # Normalize path separators
                
                # Check framework indicators
                if file in self.all_framework_indicators or any(fnmatch.fnmatch(file, pattern) for pattern in self.all_framework_indicators):
                    framework_indicators.append(rel_path_str)
                    build_files.append(rel_path_str)
                    continue
                
                # Check if it's a test file (check all language patterns)
                is_test = False
                for lang_config in self.supported_languages.values():
                    if self._matches_test_pattern(rel_path_str, lang_config):
                        test_files.append(rel_path_str)
                        is_test = True
                        break
                
                if is_test:
                    continue
                
                # Check source files
                if file_path.suffix in self.all_source_extensions:
                    source_files.append(rel_path_str)
                # Check config files
                elif file_path.suffix in self.all_config_extensions:
                    config_files.append(rel_path_str)
                # Check documentation
                elif file_path.suffix in doc_extensions:
                    documentation.append(rel_path_str)
        
        total_files = len(source_files) + len(config_files) + len(documentation) + len(test_files) + len(build_files)
        
        # Detect languages
        detected_languages = []
        for lang_name, lang_config in self.supported_languages.items():
            extensions = lang_config.get('source_extensions', [])
            indicators = lang_config.get('framework_indicators', [])
            
            has_source = any(f.endswith(tuple(extensions)) for f in source_files)
            has_indicator = any(ind in framework_indicators for ind in indicators)
            
            if has_source or has_indicator:
                detected_languages.append(lang_name)
        
        primary_language = self._detect_primary_language(source_files)
        
        # Calculate confidence based on findings
        confidence = 0.9
        if len(source_files) == 0:
            confidence *= 0.4
        if len(framework_indicators) == 0:
            confidence *= 0.7
        if primary_language == "unknown" and len(source_files) > 0:
            confidence *= 0.8
        
        return {
            "source_files": source_files,
            "config_files": config_files,
            "documentation": documentation,
            "test_files": test_files,
            "build_files": build_files,
            "framework_indicators": framework_indicators,
            "detected_languages": detected_languages,
            "primary_language": primary_language,
            "total_files": total_files,
            "confidence": round(confidence, 2)
        }
    
    def _is_safe_path(self, path: Path) -> bool:
        """Validate path for security (prevent directory traversal)."""
        try:
            # Resolve to absolute path
            resolved = path.resolve()
            
            # Check for suspicious patterns
            path_str = str(resolved)
            suspicious = ['..', '~', '$', '`', ';', '|', '&', '<', '>']
            
            return not any(sus in path_str for sus in suspicious)
        except Exception:
            return False
    
    def scan_repo(self, repo_path: str) -> Dict:
        """
        Scan repository and return file information with retry logic.
        
        Args:
            repo_path: Path to repository to scan
            
        Returns:
            dict: {
                "source_files": List[str],
                "config_files": List[str],
                "documentation": List[str],
                "test_files": List[str],
                "build_files": List[str],
                "framework_indicators": List[str],
                "detected_languages": List[str],
                "primary_language": str,
                "total_files": int,
                "confidence": float,
                "error": str (optional)
            }
        """
        repo_path = Path(repo_path)
        
        try:
            return self._retry_with_backoff(self._scan_repo_internal, repo_path)
        except Exception as e:
            return {
                "source_files": [],
                "config_files": [],
                "documentation": [],
                "test_files": [],
                "build_files": [],
                "framework_indicators": [],
                "detected_languages": [],
                "primary_language": "unknown",
                "total_files": 0,
                "confidence": 0.3,
                "error": f"Scan failed after {self.max_attempts} attempts: {str(e)}"
            }

