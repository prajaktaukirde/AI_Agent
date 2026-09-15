"""
baselines.py
Baseline Agents for Comparative Benchmarking:
1. TrivialBaselineAgent: Always predicts majority intent ('os_software_update_bugs'), never escalates, canned reply.
2. SimpleRetrievalBaselineAgent: Basic TF-IDF word count retrieval baseline, fixed confidence escalation threshold.
"""

from typing import Dict, Any, List
import re

class TrivialBaselineAgent:
    """Trivial baseline: predicts majority class, never escalates, static reply."""

    def __init__(self):
        self.majority_intent = "os_software_update_bugs"
        self.canned_reply = "We'd love to help with this! Please check https://support.apple.com for more details."

    def process(self, customer_text: str) -> Dict[str, Any]:
        return {
            "intent": self.majority_intent,
            "intent_confidence": 0.50,
            "should_escalate": False,
            "escalation_reason": "Trivial default: auto-handle all requests.",
            "reply": self.canned_reply,
            "generation_mode": "trivial_canned"
        }

class SimpleRetrievalBaselineAgent:
    """Simple baseline: naive keyword overlap without intent modeling or guardrails."""

    def __init__(self):
        self.canned_replies = {
            "battery": "Try restarting your phone and check battery settings at apple.co/battery.",
            "update": "Make sure your iPhone is backed up and try updating via computer.",
            "password": "Go to iforgot.apple.com to reset your password.",
            "charge": "Check your purchase history in the App Store.",
            "wifi": "Try turning your Wi-Fi off and on again.",
            "screen": "Visit an Apple store to get your screen looked at.",
            "human": "Please DM us for help: apple.co/DM"
        }

    def process(self, customer_text: str) -> Dict[str, Any]:
        text_lower = customer_text.lower()
        
        # Naive intent mapping
        if "battery" in text_lower or "charge" in text_lower:
            intent = "battery_hardware_performance"
            reply = self.canned_replies["battery"]
        elif "update" in text_lower or "ios" in text_lower:
            intent = "os_software_update_bugs"
            reply = self.canned_replies["update"]
        elif "password" in text_lower or "account" in text_lower or "icloud" in text_lower:
            intent = "icloud_appleid_security"
            reply = self.canned_replies["password"]
        elif "bill" in text_lower or "refund" in text_lower:
            intent = "billing_subscriptions_purchases"
            reply = self.canned_replies["charge"]
        elif "wifi" in text_lower or "bluetooth" in text_lower:
            intent = "connectivity_network_bluetooth"
            reply = self.canned_replies["wifi"]
        elif "screen" in text_lower or "audio" in text_lower:
            intent = "audio_display_accessories"
            reply = self.canned_replies["screen"]
        elif "human" in text_lower or "agent" in text_lower:
            intent = "human_escalation_dm_transfer"
            reply = self.canned_replies["human"]
        else:
            intent = "os_software_update_bugs"
            reply = "Please check https://support.apple.com for troubleshooting."

        # Simple escalation: only if 'dm' or 'human' or 'lawyer'
        should_escalate = any(w in text_lower for w in ["human", "agent", "lawyer", "manager"])
        reason = "Keyword matched escalation list." if should_escalate else "No escalation keyword found."

        return {
            "intent": intent,
            "intent_confidence": 0.60,
            "should_escalate": should_escalate,
            "escalation_reason": reason,
            "reply": reply,
            "generation_mode": "naive_keyword_lookup"
        }
