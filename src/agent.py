"""
agent.py
Complete End-to-End AppleSupport AI Agent pipeline.
Connects Classifier -> Router -> Retriever -> Generator -> Guardrail.
"""

from typing import Dict, Any, Optional
from .intent_classifier import IntentClassifier
from .retriever import HistoricalKnowledgeRetriever
from .escalation_router import EscalationRouter
from .generator import GroundedResponseGenerator

class AppleSupportAgent:
    """Production customer support agent for @AppleSupport."""

    def __init__(self, use_llm_if_available: bool = True):
        self.classifier = IntentClassifier(use_llm_if_available=use_llm_if_available)
        self.retriever = HistoricalKnowledgeRetriever()
        self.router = EscalationRouter(confidence_threshold=0.30)
        self.generator = GroundedResponseGenerator(use_llm_if_available=use_llm_if_available)

    def process(self, customer_text: str) -> Dict[str, Any]:
        """
        Executes full agent workflow:
        1. Classify intent
        2. Evaluate escalation decision & risk
        3. Retrieve grounded exemplars & official support docs
        4. Generate brand-voice compliant reply
        5. Verify guardrails
        """
        # Step 1: Intent Classification
        clf_result = self.classifier.classify(customer_text)
        intent = clf_result["intent"]
        confidence = clf_result["confidence"]

        # Step 2: Escalation Routing
        triage = self.router.evaluate(customer_text, intent, confidence)
        should_escalate = triage["should_escalate"]
        escalation_reason = triage["escalation_reason"]

        # Step 3: Retrieval of Grounded Context
        exemplars = self.retriever.retrieve(customer_text, intent=intent, top_k=2)
        intent_info = self.retriever.get_intent_info(intent)

        # Step 4: Generation with Guardrails
        gen_result = self.generator.generate(
            customer_query=customer_text,
            intent=intent,
            should_escalate=should_escalate,
            escalation_reason=escalation_reason,
            exemplars=exemplars,
            intent_info=intent_info
        )

        return {
            "intent": intent,
            "intent_confidence": confidence,
            "probabilities": clf_result.get("probabilities", {}),
            "should_escalate": should_escalate,
            "escalation_reason": escalation_reason,
            "risk_category": triage.get("risk_category", "none"),
            "reply": gen_result["reply"],
            "generation_mode": gen_result["generation_mode"],
            "guardrail_passed": gen_result["guardrail_passed"],
            "violations": gen_result["violations"],
            "official_url": intent_info.get("official_url", "https://support.apple.com"),
            "retrieved_exemplars_count": len(exemplars)
        }
