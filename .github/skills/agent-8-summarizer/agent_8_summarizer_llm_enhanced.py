#!/usr/bin/env python3
"""
Agent 8: BRD Summarizer (LLM-ENHANCED VERSION)
Generates comprehensive, repo-specific BRD markdown with actual API endpoints,
domain-specific diagrams, and intelligent synthesis.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kb_gen.utils.agent_llm import AgentLLM
from kb_gen.utils.comprehensive_brd_builder_llm import ComprehensiveBRDBuilderLLM


class LLMEnhancedSummarizerAgent:
    """LLM-enhanced BRD summarizer that generates repo-specific comprehensive BRDs."""

    def __init__(self, repo_path: str, output_path: Optional[str] = None, api_key: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.agent_llm = AgentLLM(self.repo_path, api_key, kb_path=self.output_path)
        self.signals = self.agent_llm.repo_signals.get_all_signals()
        self.timestamp = datetime.now().isoformat()

    def run(self) -> Dict[str, Any]:
        """Execute comprehensive BRD generation."""
        print(f"\n{'='*60}")
        print("Agent 8: LLM-Enhanced Comprehensive BRD Generator")
        print(f"{'='*60}")
        print(f"Repository: {self.repo_name}")
        print(f"API Available: {self.agent_llm.has_api()}")

        outputs = {}

        try:
            print("\n[1/3] Generating comprehensive BRD...")
            outputs["comprehensive_brd"] = self._generate_comprehensive_brd()

            print("[2/3] Generating executive summary JSON...")
            outputs["executive_summary_json"] = self._generate_executive_summary_json()

            print("[3/3] Generating synthesis decisions...")
            outputs["synthesis_decisions"] = self._generate_synthesis_decisions()

            self._write_outputs(outputs)

            print(f"\n{'='*60}")
            print("[OK] Comprehensive BRD Generation Complete!")
            print(f"{'='*60}\n")

            return {
                "status": "success",
                "outputs_generated": len(outputs),
                "confidence": 0.9 if self.agent_llm.has_api() else 0.7,
                "repo": self.repo_name,
                "domain": self._infer_domain(),
            }

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def _infer_domain(self) -> str:
        """Infer business domain from package names."""
        domain_keywords = {
            'banking': ['bank', 'finance', 'transaction', 'transfer', 'payment', 'account', 'lending'],
            'ecommerce': ['store', 'shop', 'product', 'cart', 'order', 'purchase', 'catalog'],
            'healthcare': ['patient', 'doctor', 'appointment', 'medical', 'health'],
            'library': ['book', 'library', 'member', 'lending'],
            'inventory': ['inventory', 'stock', 'warehouse', 'sku'],
        }

        package_text = ' '.join(self.signals.get('main_packages', [])).lower()

        for domain, keywords in domain_keywords.items():
            if any(kw in package_text for kw in keywords):
                return domain

        return 'general-application'

    def _generate_comprehensive_brd(self) -> Dict[str, Any]:
        """Generate comprehensive BRD JSON with metadata."""
        print("  Generating repo-specific comprehensive BRD...")

        # Add metadata to signals for BRD builder
        signals_with_meta = {
            **self.signals,
            'timestamp': self.timestamp,
            'confidence': 0.9 if self.agent_llm.has_api() else 0.7,
        }

        # Use LLM-powered BRD builder with KB path for artifact loading
        brd_builder = ComprehensiveBRDBuilderLLM(
            self.repo_name,
            str(self.repo_path),
            signals_with_meta,
            api_key=self.agent_llm.client,
            kb_path=self.output_path
        )

        brd_content = brd_builder.build()

        return {
            "repository": self.repo_name,
            "generated_at": self.timestamp,
            "domain": self._infer_domain(),
            "llm_powered": self.agent_llm.has_api(),
            "confidence": 0.9 if self.agent_llm.has_api() else 0.7,
            "content": brd_content,
            "metadata": {
                "controllers": self.signals['java_class_patterns'].get('Controller', 0),
                "services": self.signals['java_class_patterns'].get('Service', 0),
                "repositories": self.signals['java_class_patterns'].get('Repository', 0),
                "frameworks": self.signals.get('frameworks', []),
                "loc": self.signals.get('loc', 0),
            }
        }

    def _generate_executive_summary_json(self) -> Dict[str, Any]:
        """Generate executive summary as JSON."""
        if not self.agent_llm.has_api():
            return self._fallback_executive_summary_json()

        domain = self._infer_domain()
        patterns = self.signals['java_class_patterns']

        prompt = f"""
Generate a detailed executive summary JSON for this {domain} application.

Repository: {self.repo_name}
Components: {patterns.get('Controller', 0)} controllers, {patterns.get('Service', 0)} services
LOC: {self.signals.get('loc', 0):,}
Frameworks: {', '.join(self.signals.get('frameworks', []))}

Return JSON with these fields:
{{
  "application_name": "...",
  "business_domain": "{domain}",
  "description": "2-3 sentences describing what the app does",
  "key_features": ["feature1", "feature2", ...],
  "business_value": "What value does it provide?",
  "target_users": ["user type 1", "user type 2"],
  "technology_summary": "Brief tech stack description",
  "development_status": "Active/Production/Maintenance",
  "next_steps": ["action 1", "action 2"]
}}"""

        result = self.agent_llm.generate_json_output(prompt)

        if result and isinstance(result, dict):
            return {
                "repository": self.repo_name,
                "generated_at": self.timestamp,
                "llm_generated": True,
                **result
            }

        return self._fallback_executive_summary_json()

    def _fallback_executive_summary_json(self) -> Dict[str, Any]:
        """Fallback executive summary."""
        domain = self._infer_domain()
        patterns = self.signals['java_class_patterns']

        return {
            "repository": self.repo_name,
            "generated_at": self.timestamp,
            "llm_generated": False,
            "application_name": self.repo_name,
            "business_domain": domain,
            "description": f"Java {domain} application with {patterns.get('Service', 0)} services",
            "key_features": [
                "Core business operations",
                "Data management",
                "API services",
                "User management"
            ],
            "technology_summary": f"Built with {', '.join(self.signals.get('frameworks', []))}",
            "development_status": "Active",
            "next_steps": [
                "Complete testing",
                "Production deployment",
                "Monitoring setup"
            ]
        }

    def _generate_synthesis_decisions(self) -> Dict[str, Any]:
        """Generate synthesis decisions (architectural decisions)."""
        if not self.agent_llm.has_api():
            return self._fallback_synthesis_decisions()

        domain = self._infer_domain()
        patterns = self.signals['java_class_patterns']

        prompt = f"""
Generate 5-7 key architectural decisions for this {domain} application.

Architecture:
- {patterns.get('Controller', 0)} Controllers
- {patterns.get('Service', 0)} Services
- {patterns.get('Repository', 0)} Repositories
- Frameworks: {', '.join(self.signals.get('frameworks', []))}

For each decision, provide JSON object with:
{{
  "id": "AD001",
  "title": "Decision Title",
  "context": "Why this decision was needed",
  "decision": "What was decided",
  "rationale": "Why this approach",
  "consequences": "Positive and negative impacts"
}}

Return array of decisions."""

        result = self.agent_llm.generate_json_output(prompt)

        if result and isinstance(result, (list, dict)):
            decisions = result if isinstance(result, list) else result.get('decisions', [])
            return {
                "repository": self.repo_name,
                "generated_at": self.timestamp,
                "llm_generated": True,
                "total_decisions": len(decisions),
                "decisions": decisions
            }

        return self._fallback_synthesis_decisions()

    def _fallback_synthesis_decisions(self) -> Dict[str, Any]:
        """Fallback synthesis decisions."""
        domain = self._infer_domain()

        decisions = [
            {
                "id": "AD001",
                "title": "Layered Architecture",
                "context": "Need for separation of concerns",
                "decision": "Implemented controller-service-repository pattern",
                "rationale": "Proven pattern for maintainability and testability",
                "consequences": "Added complexity but improved code organization"
            },
            {
                "id": "AD002",
                "title": f"{domain.title()} Domain Model",
                "context": f"Need for {domain} specific business logic",
                "decision": "Designed domain entities reflecting business concepts",
                "rationale": "Better representation of business requirements",
                "consequences": "Easier to understand and maintain business logic"
            },
            {
                "id": "AD003",
                "title": "REST API for Integration",
                "context": "External system integration requirements",
                "decision": "Exposed REST endpoints for core operations",
                "rationale": "Standard, widely supported API style",
                "consequences": "Easy integration but requires API versioning strategy"
            }
        ]

        return {
            "repository": self.repo_name,
            "generated_at": self.timestamp,
            "llm_generated": False,
            "total_decisions": len(decisions),
            "decisions": decisions
        }

    def _write_outputs(self, outputs: Dict[str, Any]):
        """Write outputs to JSON files."""
        for name, data in outputs.items():
            filepath = self.output_path / f"{name}.json"
            filepath.write_text(json.dumps(data, indent=2))
            print(f"  [OK] Wrote {filepath.name}")

            # Also write BRD content as markdown if it exists
            if name == "comprehensive_brd" and isinstance(data, dict) and "content" in data:
                brd_filepath = self.output_path / f"{name}.md"
                brd_filepath.write_text(data["content"])
                print(f"  [OK] Wrote {brd_filepath.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent 8: LLM-Enhanced BRD Summarizer")
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument("--output", help="Output path for artifacts", default=None)
    parser.add_argument("--api-key", help="Anthropic API key", default=None)

    args = parser.parse_args()

    agent = LLMEnhancedSummarizerAgent(args.repo_path, args.output, args.api_key)
    result = agent.run()

    sys.exit(0 if result.get("status") == "success" else 1)
