"""
IntentClassifier — LLM-based intent + relevant doc prediction.

classify_query(query, document_tags) -> (intent_label, List[artifact_ids])

Sends doc name list (up to 80) to LLM; expects JSON {intent, relevant_docs, confidence}.
Maps returned doc names back to artifact IDs via name_to_id dict.
Retry logic: up to KB_RAG_INTENT_MAX_RETRIES (default 3) with exponential backoff.
"""
import json
import os
import time
from typing import Dict, List, Optional, Tuple

from kb_gen.utils.api_client import get_anthropic_client, sanitize_error


INTENT_SYSTEM = """You are an intent classifier for a knowledge base query system.
Given a user query and a list of available document names, classify the query intent
and identify which documents are most relevant.
Respond ONLY in valid JSON. No preamble. No markdown fences."""

INTENT_PROMPT = """Query: {query}

Available documents (up to 80 shown):
{doc_list}

Respond with ONLY this JSON:
{{
  "intent": "one of: requirement_lookup|rule_lookup|journey_lookup|gap_analysis|risk_lookup|scope_lookup|acceptance_criteria|general",
  "relevant_docs": ["exact document name 1", "exact document name 2"],
  "confidence": "HIGH|MEDIUM|LOW",
  "reasoning": "brief one-line explanation"
}}"""


class IntentClassifier:

    MAX_DOCS_SHOWN = 80

    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        self.model = model
        self._client = None
        self._max_retries = int(os.getenv("KB_RAG_INTENT_MAX_RETRIES", "3"))

    def _get_client(self):
        if self._client is None:
            self._client = get_anthropic_client()
        return self._client

    def classify_query(
        self,
        query: str,
        name_to_id: Dict[str, str],
    ) -> Tuple[str, List[str]]:
        """
        Returns (intent_label, list_of_artifact_ids).
        Falls back to ("general", []) on failure.
        """
        doc_names = list(name_to_id.keys())[: self.MAX_DOCS_SHOWN]
        doc_list = "\n".join(f"- {n}" for n in doc_names)

        prompt = INTENT_PROMPT.format(query=query, doc_list=doc_list)

        for attempt in range(self._max_retries):
            try:
                client = self._get_client()
                resp = client.messages.create(
                    model=self.model,
                    max_tokens=512,
                    system=INTENT_SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text.strip()
                raw = self._strip_fences(raw)
                parsed = json.loads(raw)

                intent = parsed.get("intent", "general")
                relevant_names = parsed.get("relevant_docs", [])
                artifact_ids = [
                    name_to_id[n] for n in relevant_names if n in name_to_id
                ]
                return intent, artifact_ids

            except Exception as exc:
                safe = sanitize_error(str(exc))
                if attempt < self._max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"[WARN]  IntentClassifier failed after {self._max_retries} retries: {safe}")

        return "general", []

    @staticmethod
    def _strip_fences(raw: str) -> str:
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 3:
                raw = parts[1]
                if raw.startswith("json"):
                    raw = raw[4:]
        return raw.strip()
