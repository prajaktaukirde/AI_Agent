"""
retriever.py
Historical Knowledge and Exemplar Retriever for AppleSupport AI Agent.
Indexes historical conversation pairs and official troubleshooting documentation.
"""

import os
import json
import re
import math
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
KB_FILE = os.path.join(DATA_DIR, "historical_knowledge.json")
PAIRS_FILE = os.path.join(DATA_DIR, "apple_support_pairs.json")

class HistoricalKnowledgeRetriever:
    """Retrieves relevant historical troubleshooting steps and exemplars for a customer query."""

    def __init__(self):
        self.kb = self._load_kb()
        self.historical_pairs = self._load_pairs()
        self.vocabulary = set()
        self.doc_freq = {}
        self.indexed_docs = []
        self._build_index()

    def _load_kb(self) -> Dict[str, Any]:
        if os.path.exists(KB_FILE):
            with open(KB_FILE, "r") as f:
                return json.load(f)
        return {"brand": "AppleSupport", "intents": {}, "exemplars": []}

    def _load_pairs(self) -> List[Dict[str, Any]]:
        if os.path.exists(PAIRS_FILE):
            with open(PAIRS_FILE, "r") as f:
                return json.load(f)
        return []

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [t for t in cleaned.split() if len(t) > 2]
        return tokens

    def _build_index(self):
        """Indexes knowledge base exemplars and historical pairs for fast BM25/TF-IDF retrieval."""
        docs = []

        # 1. Index KB exemplars (highest quality)
        for ex in self.kb.get("exemplars", []):
            docs.append({
                "source": "kb_exemplar",
                "intent": ex.get("intent", ""),
                "query": ex.get("customer_query", ""),
                "reply": ex.get("resolution_reply", ""),
                "url": self.kb.get("intents", {}).get(ex.get("intent", ""), {}).get("official_url", "")
            })

        # 2. Index sample of authentic pairs
        for p in self.historical_pairs[:1000]:
            docs.append({
                "source": "historical_pair",
                "intent": "general",
                "query": p.get("cleaned_customer_text", ""),
                "reply": p.get("cleaned_brand_reply", ""),
                "url": "https://support.apple.com"
            })

        self.indexed_docs = docs
        total_docs = len(docs)

        for doc in docs:
            tokens = set(self._tokenize(doc["query"] + " " + doc["reply"]))
            for t in tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1
                self.vocabulary.add(t)

        self.idf = {
            t: math.log((total_docs - freq + 0.5) / (freq + 0.5) + 1.0)
            for t, freq in self.doc_freq.items()
        }

    def retrieve(self, query: str, intent: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top_k most relevant exemplars matching the customer query."""
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scored_docs = []
        for doc in self.indexed_docs:
            # If intent is provided and matched, boost score
            intent_boost = 1.5 if (intent and doc["intent"] == intent) else 1.0

            d_tokens = self._tokenize(doc["query"])
            if not d_tokens:
                continue

            # BM25-style scoring
            score = 0.0
            doc_len = len(d_tokens)
            avg_len = 20.0
            k1 = 1.5
            b = 0.75

            for t in q_tokens:
                if t in self.idf:
                    tf = d_tokens.count(t)
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * (doc_len / avg_len))
                    score += self.idf[t] * (numerator / (denominator + 1e-6))

            # N-gram overlap boost
            q_set = set(q_tokens)
            d_set = set(d_tokens)
            jaccard = len(q_set.intersection(d_set)) / max(1, len(q_set.union(d_set)))
            score += jaccard * 5.0

            score *= intent_boost

            if score > 0.1:
                scored_docs.append({
                    "score": round(score, 3),
                    "query": doc["query"],
                    "reply": doc["reply"],
                    "intent": doc["intent"],
                    "source": doc["source"],
                    "url": doc.get("url", "")
                })

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]

    def get_intent_info(self, intent: str) -> Dict[str, Any]:
        """Returns official metadata, links, and troubleshooting actions for an intent."""
        return self.kb.get("intents", {}).get(intent, {
            "description": "General Apple device troubleshooting.",
            "official_url": "https://support.apple.com",
            "sample_action": "Ask for device model and OS version."
        })
