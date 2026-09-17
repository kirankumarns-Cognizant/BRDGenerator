"""
Agent LLM helper — calls Claude with repo context.
All 9 agents use this to generate repo-specific, LLM-powered outputs.
Supports multi-provider fallback: Claude API → OpenAI → Gemini → GitHub Copilot → Claude Code → Static Analysis
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

from .multi_provider_llm import get_multi_provider_llm, get_active_provider
from .repo_signals import RepoSignals
from .document_processor import DocumentProcessor


class AgentLLM:
    """Wrapper for multi-provider LLM calls with repo context awareness."""

    def __init__(self, repo_path: Path, api_key: Optional[str] = None, kb_path: Optional[Path] = None):
        self.repo_path = Path(repo_path)
        self.api_key = api_key
        self.repo_signals = RepoSignals(repo_path)

        # Initialize document processor
        if kb_path:
            self.doc_processor = DocumentProcessor(kb_path)
            # Log if documents are available
            if self.doc_processor.has_documents():
                doc_count = len(self.doc_processor.get_all_documents())
                print(f"\n📎 Document Integration Enabled: Found {doc_count} supporting document(s)")
                print(f"   Location: {self.doc_processor.docs_dir}")
                print(f"   ✅ Documents will be incorporated into BRD analysis")
        else:
            self.doc_processor = None

        # Initialize multi-provider LLM
        self.llm = get_multi_provider_llm()
        self.provider_info = self.llm.get_provider_info()

    def has_api(self) -> bool:
        """Check if any LLM provider with API is available (not static analysis)."""
        return self.llm.has_api()

    def get_repo_context(self) -> str:
        """Build a rich text summary of repo signals for Claude context."""
        signals = self.repo_signals.get_all_signals()

        context = f"""
# Repository Analysis Context

**Repository**: {self.repo_path.name}
**Location**: {signals['repo_path']}

## Detected Technologies
- **Frameworks**: {', '.join(signals['frameworks']) or 'None detected'}
- **Total LOC**: {signals['loc']:,}
- **Main Packages**: {', '.join(signals['main_packages'][:5]) or 'None detected'}

## File Distribution
{self._format_file_stats(signals['file_stats'])}

## Component Patterns (Java classes)
{self._format_class_patterns(signals['java_class_patterns'])}

## Top Dependencies
{self._format_dependencies(signals['dependencies'])}

## Common Imports
{self._format_imports(signals['top_imports'])}

## Sample Java Files
{self._format_java_files(signals['java_files'])}
"""
        # Add document context if available
        doc_context = self.get_document_context()
        if doc_context:
            context += f"\n{doc_context}"

        return context

    def get_document_context(self) -> str:
        """Get context from uploaded supporting documents."""
        if not self.doc_processor or not self.doc_processor.has_documents():
            return ""

        doc_summary = self.doc_processor.get_documents_summary()
        docs_context = f"\n## 📎 IMPORTANT: Supporting Documents (User-Provided Context)\n"
        docs_context += f"**⭐ These documents MUST be analyzed and incorporated into the BRD**\n"
        docs_context += f"**Document Count**: {doc_summary['document_count']} document(s)\n\n"

        # Add document details
        docs_context += "### Documents Provided:\n"
        for doc in doc_summary['documents']:
            docs_context += f"- **{doc['name']}** ({doc['size_kb']} KB)\n"

        # Add full document content with emphasis
        docs_context += "\n### Full Document Content:\n"
        docs_context += "⚠️ CRITICAL: Use the following document content to enhance and customize the BRD analysis:\n"
        docs_context += self.doc_processor.get_documents_context()

        return docs_context

    def call_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
    ) -> str:
        """Call multi-provider LLM with repo context prepended to prompt."""
        if not self.has_api():
            return ""

        try:
            # Build full prompt with repo context
            repo_context = self.get_repo_context()

            # Add document emphasis instruction if documents exist
            doc_emphasis = ""
            if self.doc_processor and self.doc_processor.has_documents():
                doc_count = len(self.doc_processor.get_all_documents())
                doc_emphasis = f"\n⭐ Note: {doc_count} supporting document(s) provided below - incorporate relevant insights into analysis\n"

            full_prompt = f"{doc_emphasis}{repo_context}\n\n## Task\n{prompt}"

            # Build system message
            if system_prompt is None:
                doc_note = ""
                if self.doc_processor and self.doc_processor.has_documents():
                    doc_note = (
                        "\n\n⭐ CRITICAL INSTRUCTIONS FOR DOCUMENT INTEGRATION:\n"
                        "1. Supporting documents have been PROVIDED by the user below in the context\n"
                        "2. You MUST read and analyze these documents thoroughly\n"
                        "3. Incorporate insights, requirements, and specifications from these documents INTO the BRD\n"
                        "4. Cross-reference repository code with document requirements\n"
                        "5. Highlight document-based requirements and business rules\n"
                        "6. If documents conflict with code, note both and explain\n"
                        "7. Make the output MORE comprehensive by combining document requirements with code analysis\n"
                    )

                system_prompt = (
                    "You are a Business Requirements Document (BRD) analysis expert. "
                    "Generate comprehensive, repo-specific outputs based on the repository context AND supporting documents provided. "
                    f"{doc_note}"
                    "\n\nReturn valid JSON when requested. Be thorough, detailed, and ensure all document insights are reflected in the output."
                )

            # Use multi-provider LLM
            response = self.llm.complete(
                prompt=full_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )
            
            return response if response else ""
        except Exception as e:
            # Return error message instead of empty string
            return f"Error: {str(e)}"

    def generate_json_output(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """Call Claude and parse JSON response."""
        response_text = self.call_claude(prompt, system_prompt, max_tokens)

        if not response_text:
            return {}

        # Try to extract JSON from response
        try:
            # Look for JSON block
            import re

            json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try parsing entire response as JSON
                json_str = response_text

            return json.loads(json_str)
        except json.JSONDecodeError:
            # Return empty dict if parsing fails
            return {}

    # ──────────────────────────────────────────────────────────────────────────────
    # Formatting Helpers
    # ──────────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _format_file_stats(stats: Dict[str, int]) -> str:
        """Format file statistics as readable text."""
        lines = []
        for ext, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"- {ext}: {count}")
        return "\n".join(lines) if lines else "- No files found"

    @staticmethod
    def _format_class_patterns(patterns: Dict[str, int]) -> str:
        """Format Java class patterns."""
        lines = []
        for pattern, count in patterns.items():
            if count > 0:
                lines.append(f"- {pattern}: {count}")
        return "\n".join(lines) if lines else "- No patterns detected"

    @staticmethod
    def _format_dependencies(deps: Dict[str, list]) -> str:
        """Format dependencies by package manager."""
        lines = []
        for manager, dep_list in deps.items():
            if dep_list:
                lines.append(f"- {manager}: {', '.join(dep_list[:10])}")
        return "\n".join(lines) if lines else "- No dependencies found"

    @staticmethod
    def _format_imports(imports: list) -> str:
        """Format top imports."""
        lines = []
        for imp, count in imports[:10]:
            lines.append(f"- {imp} ({count} files)")
        return "\n".join(lines) if lines else "- No imports found"

    @staticmethod
    def _format_java_files(files: list) -> str:
        """Format Java file list."""
        lines = [f"- {f}" for f in files[:20]]
        return "\n".join(lines) if lines else "- No Java files found"
