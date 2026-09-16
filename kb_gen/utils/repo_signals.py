"""
Repository signal extractor — analyzes repo structure without LLM.
Builds rich context: frameworks, file statistics, dependencies, technologies.
Used by all 9 agents to differentiate outputs per repository.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter


class RepoSignals:
    """Extracts repo-specific signals for context-aware agent outputs."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self._cache: Dict[str, Any] = {}

    # ──────────────────────────────────────────────────────────────────────────────
    # File Statistics
    # ──────────────────────────────────────────────────────────────────────────────

    def get_file_stats(self) -> Dict[str, int]:
        """Count files by extension."""
        stats: Dict[str, int] = {}
        try:
            if not self.repo_path.exists():
                return stats
            for fpath in self.repo_path.rglob("*"):
                if fpath.is_file() and not self._is_ignored(fpath):
                    ext = fpath.suffix or "no-ext"
                    stats[ext] = stats.get(ext, 0) + 1
        except Exception:
            pass
        return stats

    def count_lines_of_code(self, extensions: Optional[List[str]] = None) -> int:
        """Count lines in source files. Defaults to common langs."""
        if extensions is None:
            extensions = [".java", ".py", ".js", ".ts", ".go", ".rs", ".cpp", ".c", ".rb"]

        total = 0
        for fpath in self.repo_path.rglob("*"):
            if (
                fpath.is_file()
                and fpath.suffix in extensions
                and not self._is_ignored(fpath)
            ):
                try:
                    total += len(fpath.read_text(encoding="utf-8", errors="ignore").splitlines())
                except Exception:
                    pass
        return total

    # ──────────────────────────────────────────────────────────────────────────────
    # Framework Detection (without LLM)
    # ──────────────────────────────────────────────────────────────────────────────

    def detect_frameworks(self) -> List[str]:
        """Detect frameworks from pom.xml, package.json, go.mod, Cargo.toml, etc."""
        frameworks = set()

        # Maven (Java)
        pom_path = self.repo_path / "pom.xml"
        if pom_path.exists():
            pom_text = pom_path.read_text(errors="ignore")
            if "org.springframework" in pom_text:
                frameworks.add("Spring Framework")
            if "net.sourceforge.stripes" in pom_text:
                frameworks.add("Stripes MVC")
            if "org.mybatis" in pom_text or "org.apache.ibatis" in pom_text:
                frameworks.add("MyBatis")
            if "org.hibernate" in pom_text:
                frameworks.add("Hibernate")
            if "javax.persistence" in pom_text or "jakarta.persistence" in pom_text:
                frameworks.add("JPA")

        # Gradle (Java)
        gradle_path = self.repo_path / "build.gradle"
        if gradle_path.exists():
            gradle_text = gradle_path.read_text(errors="ignore")
            if "org.springframework" in gradle_text:
                frameworks.add("Spring Framework")
            if "react" in gradle_text or "redux" in gradle_text:
                frameworks.add("React/Redux")

        # npm (JavaScript/TypeScript)
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            pkg_text = package_json.read_text(errors="ignore")
            if "react" in pkg_text:
                frameworks.add("React")
            if "vue" in pkg_text:
                frameworks.add("Vue.js")
            if "angular" in pkg_text:
                frameworks.add("Angular")
            if "express" in pkg_text:
                frameworks.add("Express.js")
            if "next" in pkg_text:
                frameworks.add("Next.js")
            if "typescript" in pkg_text:
                frameworks.add("TypeScript")

        # Python
        requirements = self.repo_path / "requirements.txt"
        if requirements.exists():
            req_text = requirements.read_text(errors="ignore")
            if "django" in req_text:
                frameworks.add("Django")
            if "flask" in req_text:
                frameworks.add("Flask")
            if "fastapi" in req_text:
                frameworks.add("FastAPI")

        # Go
        go_mod = self.repo_path / "go.mod"
        if go_mod.exists():
            frameworks.add("Go")

        # Rust
        cargo_toml = self.repo_path / "Cargo.toml"
        if cargo_toml.exists():
            frameworks.add("Rust")

        # PHP
        composer_json = self.repo_path / "composer.json"
        if composer_json.exists():
            comp_text = composer_json.read_text(errors="ignore")
            if "laravel" in comp_text:
                frameworks.add("Laravel")
            if "symfony" in comp_text:
                frameworks.add("Symfony")

        return sorted(list(frameworks))

    # ──────────────────────────────────────────────────────────────────────────────
    # Dependency Detection
    # ──────────────────────────────────────────────────────────────────────────────

    def extract_dependencies(self) -> Dict[str, List[str]]:
        """Extract dependencies from various package managers."""
        deps = {}

        # Maven
        pom_path = self.repo_path / "pom.xml"
        if pom_path.exists():
            try:
                pom_text = pom_path.read_text(errors="ignore")
                artifact_ids = re.findall(r"<artifactId>([^<]+)</artifactId>", pom_text)
                deps["maven"] = list(set(artifact_ids))[:15]
            except Exception:
                pass

        # npm
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            try:
                pkg = json.loads(package_json.read_text())
                npm_deps = list(pkg.get("dependencies", {}).keys())[:15]
                deps["npm"] = npm_deps
            except Exception:
                pass

        # Python
        requirements = self.repo_path / "requirements.txt"
        if requirements.exists():
            try:
                py_deps = [
                    line.split("==")[0].split(">")[0].split("<")[0]
                    for line in requirements.read_text().splitlines()
                    if line.strip() and not line.startswith("#")
                ]
                deps["pip"] = py_deps[:15]
            except Exception:
                pass

        return deps

    # ──────────────────────────────────────────────────────────────────────────────
    # Source Code Patterns (Java-specific)
    # ──────────────────────────────────────────────────────────────────────────────

    def count_java_classes_by_pattern(
        self, patterns: Optional[Dict[str, str]] = None
    ) -> Dict[str, int]:
        """Count Java classes matching naming patterns (Controllers, Services, etc)."""
        if patterns is None:
            patterns = {
                "Controller": r".*Controller\.java$",
                "Service": r".*Service\.java$",
                "Repository": r".*Repository\.java$",
                "Mapper": r".*Mapper\.java$",
                "Entity": r".*Entity\.java$",
                "DTO": r".*DTO\.java$",
            }

        counts: Dict[str, int] = {}
        for pattern_name, pattern in patterns.items():
            for fpath in self.repo_path.rglob("*.java"):
                if not self._is_ignored(fpath) and re.search(pattern, str(fpath)):
                    counts[pattern_name] = counts.get(pattern_name, 0) + 1

        return counts

    def extract_imports_summary(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Extract top N imports across all Java files."""
        imports: Dict[str, int] = {}

        for fpath in self.repo_path.rglob("*.java"):
            if self._is_ignored(fpath):
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                found_imports = re.findall(r"import\s+([\w.]+);", content)
                for imp in found_imports:
                    imports[imp] = imports.get(imp, 0) + 1
            except Exception:
                pass

        return sorted(imports.items(), key=lambda x: x[1], reverse=True)[:limit]

    def list_java_files(self, limit: int = 50) -> List[str]:
        """List Java files with their package structure."""
        java_files = []
        for fpath in self.repo_path.rglob("*.java"):
            if not self._is_ignored(fpath):
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    match = re.search(r"package\s+([\w.]+);", content)
                    pkg = match.group(1) if match else "default"
                    class_name = fpath.stem
                    java_files.append(f"{pkg}.{class_name}")
                except Exception:
                    pass
        return sorted(java_files)[:limit]

    # ──────────────────────────────────────────────────────────────────────────────
    # Directory Structure
    # ──────────────────────────────────────────────────────────────────────────────

    def get_main_packages(self, max_depth: int = 3) -> List[str]:
        """Extract main Java packages from source structure."""
        packages = set()

        for fpath in self.repo_path.rglob("*.java"):
            if self._is_ignored(fpath):
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                match = re.search(r"package\s+([\w.]+);", content)
                if match:
                    pkg = match.group(1)
                    parts = pkg.split(".")[:max_depth]
                    packages.add(".".join(parts))
            except Exception:
                pass

        return sorted(list(packages))

    # ──────────────────────────────────────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────────────────────────────────────

    def _is_ignored(self, fpath: Path) -> bool:
        """Check if file should be ignored."""
        ignored_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            "target",
            "build",
            "dist",
            ".idea",
            ".vscode",
        }
        ignored_files = {".DS_Store", "Thumbs.db"}

        if fpath.name in ignored_files:
            return True

        for part in fpath.parts:
            if part in ignored_dirs:
                return True

        return False

    def get_all_signals(self) -> Dict[str, Any]:
        """Return comprehensive repo signal summary."""
        return {
            "repo_path": str(self.repo_path),
            "frameworks": self.detect_frameworks(),
            "file_stats": self.get_file_stats(),
            "loc": self.count_lines_of_code(),
            "dependencies": self.extract_dependencies(),
            "java_class_patterns": self.count_java_classes_by_pattern(),
            "main_packages": self.get_main_packages(),
            "top_imports": self.extract_imports_summary(10),
            "java_files": self.list_java_files(30),
        }
