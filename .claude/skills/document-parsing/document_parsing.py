#!/usr/bin/env python3
"""
Cross-Agent Skill: Document Parsing
Parses and extracts information from PDF, Word, Markdown, and text documents.
Used by multiple agents for document processing.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config_loader import ConfigLoader

# Try to import real document parser, fallback to mock if unavailable
try:
    from kb_gen.ingestion.doc_parser import DocumentParser
    REAL_PARSER_AVAILABLE = True
except ImportError:
    REAL_PARSER_AVAILABLE = False
    class DocumentParser:
        """Mock parser fallback."""
        def __init__(self, config=None):
            self.config = config


class DocumentParsingSkill:
    """Document parsing skill for cross-agent usage - Uses real kb_gen logic."""
    
    SUPPORTED_FORMATS = [".pdf", ".docx", ".doc", ".md", ".txt"]
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigLoader(config_path or "config/config.yaml")
        self.real_available = REAL_PARSER_AVAILABLE
        
        # Initialize real parser if available
        if self.real_available:
            try:
                self.parser = DocumentParser(self.config)
            except Exception as e:
                import logging
                logging.warning(f"Failed to initialize real document parser: {e}")
                self.parser = None
        else:
            self.parser = None
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """
        Parse document and extract content using real kb_gen logic.
        
        Args:
            file_path: Path to document file
        
        Returns:
            Dictionary with extracted content and metadata
        """
        # Try real parser first
        if self.parser:
            try:
                result = self.parser.parse_document(file_path)
                if result:
                    return {**result, "kb_gen_used": True}
            except Exception as e:
                import logging
                logging.error(f"Real parser failed: {e}")
        
        # Fallback to mock parsing
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            return {"error": f"Unsupported format: {file_ext}. Supported: {self.SUPPORTED_FORMATS}"}
        
        if file_ext == ".txt" or file_ext == ".md":
            return self._parse_text_file(file_path)
        elif file_ext == ".pdf":
            return self._parse_pdf(file_path)
        elif file_ext in [".docx", ".doc"]:
            return self._parse_word_doc(file_path)
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract document metadata.
        
        Args:
            file_path: Path to document
        
        Returns:
            Dictionary with metadata
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        file_stat = os.stat(file_path)
        return {
            "file": file_path,
            "size_bytes": file_stat.st_size,
            "created": file_stat.st_ctime,
            "modified": file_stat.st_mtime,
            "format": Path(file_path).suffix
        }
    
    def batch_parse_documents(self, directory: str) -> List[Dict[str, Any]]:
        """
        Parse all documents in a directory.
        
        Args:
            directory: Path to directory containing documents
        
        Returns:
            List of parsing results
        """
        if not os.path.isdir(directory):
            return [{"error": f"Directory not found: {directory}"}]
        
        results = []
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and Path(file_path).suffix.lower() in self.SUPPORTED_FORMATS:
                result = self.parse_document(file_path)
                results.append(result)
        
        return results
    
    def _parse_text_file(self, file_path: str) -> Dict[str, Any]:
        """Parse text or markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        sections = self._extract_sections(content)
        
        return {
            "file": file_path,
            "format": Path(file_path).suffix,
            "total_lines": len(lines),
            "total_chars": len(content),
            "sections": sections,
            "preview": content[:500] + "..." if len(content) > 500 else content
        }
    
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF file (basic implementation)."""
        try:
            # Attempt to use PyPDF2 if available
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                num_pages = len(pdf.pages)
                text = ""
                for page in pdf.pages[:3]:  # First 3 pages
                    text += page.extract_text()
                
                return {
                    "file": file_path,
                    "format": ".pdf",
                    "num_pages": num_pages,
                    "preview": text[:500] + "..." if len(text) > 500 else text
                }
        except ImportError:
            return {
                "file": file_path,
                "format": ".pdf",
                "error": "PyPDF2 not installed. Install with: pip install PyPDF2",
                "status": "fallback_needed"
            }
    
    def _parse_word_doc(self, file_path: str) -> Dict[str, Any]:
        """Parse Word document (basic implementation)."""
        try:
            # Attempt to use python-docx if available
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            text = "\n".join(paragraphs)
            
            return {
                "file": file_path,
                "format": Path(file_path).suffix,
                "num_paragraphs": len(paragraphs),
                "preview": text[:500] + "..." if len(text) > 500 else text
            }
        except ImportError:
            return {
                "file": file_path,
                "format": Path(file_path).suffix,
                "error": "python-docx not installed. Install with: pip install python-docx",
                "status": "fallback_needed"
            }
    
    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract sections from markdown/text content."""
        sections = []
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            if line.startswith('#'):
                # Markdown heading
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                current_section = {"level": level, "title": title}
                sections.append(current_section)
        
        return sections


def main():
    """CLI entry point for document parsing."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Document Parsing Skill")
    parser.add_argument("action", choices=["parse", "metadata", "batch-parse"])
    parser.add_argument("path", help="File or directory path")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    skill = DocumentParsingSkill(args.config)
    
    if args.action == "parse":
        result = skill.parse_document(args.path)
    elif args.action == "metadata":
        result = skill.extract_metadata(args.path)
    else:  # batch-parse
        result = skill.batch_parse_documents(args.path)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    main()
