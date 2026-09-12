"""
AppleSupport AI Agent Package
A production-grade, grounded customer support AI agent for Twitter support interactions.
"""

from .intent_classifier import IntentClassifier
from .retriever import HistoricalKnowledgeRetriever
from .escalation_router import EscalationRouter
from .generator import GroundedResponseGenerator
from .agent import AppleSupportAgent
from .baselines import TrivialBaselineAgent, SimpleRetrievalBaselineAgent
from .evaluator import AgentEvaluator

__all__ = [
    "IntentClassifier",
    "HistoricalKnowledgeRetriever",
    "EscalationRouter",
    "GroundedResponseGenerator",
    "AppleSupportAgent",
    "TrivialBaselineAgent",
    "SimpleRetrievalBaselineAgent",
    "AgentEvaluator"
]
