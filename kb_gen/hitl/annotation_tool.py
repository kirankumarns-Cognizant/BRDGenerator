"""
AnnotationTool — interactive CLI for reviewing retrieval results.
Prompts user for y/n rating per source and delegates to FeedbackStore.
"""
from typing import Dict, List

from kb_gen.hitl.feedback_store import FeedbackStore


class AnnotationTool:

    def __init__(self, feedback_store: FeedbackStore, registry=None):
        self.feedback_store = feedback_store
        self.registry = registry

    def annotate_query(self, query: str, results: List[Dict], intent: str = "") -> Dict:
        """
        Present ranked results and prompt user for y/n rating per source.

        Args:
            query: The original query.
            results: List of source dicts with keys: artifact_id, name, snippet, score.
            intent: Intent label from IntentClassifier.

        Returns:
            Dict with annotation summary.
        """
        print("\n" + "═" * 60)
        print(f"QUERY: {query}")
        if intent:
            print(f"INTENT: {intent}")
        print("═" * 60)

        annotated = []
        for i, src in enumerate(results, 1):
            name = src.get("name") or src.get("artifact_id", "unknown")
            score = src.get("score", 0)
            snippet = (src.get("snippet") or "")[:300]

            print(f"\n[{i}] {name}  (score: {score:.3f})")
            if snippet:
                print(f"    {snippet[:200]}…")

            while True:
                try:
                    answer = input("    Useful? [y/n/s=skip all]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    answer = "s"

                if answer == "s":
                    print("  Skipping remaining sources.")
                    return {"query": query, "annotated": annotated, "skipped": True}
                if answer in ("y", "n"):
                    break
                print("    Please enter y or n (or s to skip all).")

            useful = answer == "y"
            note_prompt = "    Note (optional, press Enter to skip): "
            try:
                note = input(note_prompt).strip()
            except (EOFError, KeyboardInterrupt):
                note = ""

            self.feedback_store.record_feedback(
                artifact_id=src.get("artifact_id", ""),
                query=query,
                useful=useful,
                note=note,
                registry=self.registry,
                intent=intent,
            )
            annotated.append({
                "artifact_id": src.get("artifact_id", ""),
                "name": name,
                "useful": useful,
                "note": note,
            })

        print("\n[OK] Annotation complete.")
        return {"query": query, "annotated": annotated, "skipped": False}
