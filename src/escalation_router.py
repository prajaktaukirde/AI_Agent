"""
escalation_router.py
Triage Decision Engine for AppleSupport AI Agent.
Decides whether an incoming customer tweet can be auto-handled or must be escalated
to a human advisor, along with a transparent, structured reason.
"""

import re
from typing import Dict, Any, Tuple

# Critical safety / hardware hazard keywords
SAFETY_TRIGGERS = [
    r"\bswollen\b", r"\bswelling\b", r"\bbulging\b", r"\bsmoke\b", r"\bsmoking\b",
    r"\bcatch(?:es|ing)?\s+fire\b", r"\bexploded?\b", r"\bburn(?:ed|ing|t)?\b",
    r"\bsparking?\b", r"\belectric\s+shock\b"
]

# Physical hardware damage triggers
HARDWARE_DAMAGE_TRIGGERS = [
    r"\bshatter(?:ed)?\b", r"\bcracked\s+screen\b", r"\bsmashed\b", r"\bliquid\s+damage\b",
    r"\bdropped\s+(?:on|in|into|onto)\b", r"\bdrop(?:ped)?\s+my\s+iphone\b",
    r"\bdropped\s+(?:in|into)\s+water\b", r"\bsubmerged\b", r"\bdead\s+pixels?\b",
    r"\bgreen\s+lines?\b", r"\bblank\s+modem\b", r"\bbent\b",
    r"\bprohibitory\s+sign\b", r"\bcircle\s+with\s+a\s+slash\b", r"\bpitch\s+black\b",
    r"\btouch\s+is\s+completely\s+dead\b", r"\brestarts?\s+every\s+\d+\s+minutes?\b",
    r"\bsend\s+it\s+for\s+repair\b", r"\bhardware\s+repair\b"
]

# Account security & compromise triggers
SECURITY_TRIGGERS = [
    r"\bhacked\b", r"\bcompromised\b", r"\bunauthorized\s+(?:access|login|charge)\b",
    r"\bstolen\b", r"\bidentity\s+theft\b", r"\bchanged\s+my\s+(?:phone|email|password|trusted)\b",
    r"\bactivation\s+lock\b", r"\bblacklisted\b", r"\bsomeone\s+in\s+another\s+country\b",
    r"\blogged\s+into\s+my\s+apple\s+id\b"
]

# Frustration / legal / human demand triggers
HOSTILITY_TRIGGERS = [
    r"\blawyer\b", r"\bsue\b", r"\bsuing\b", r"\blegal\s+action\b", r"\bcourt\b",
    r"\bformal\s+complaint\b", r"\bhuman\b", r"\breal\s+person\b", r"\blive\s+agent\b",
    r"\bmanager\b", r"\bsupervisor\b", r"\bunacceptable\b", r"\bworst\s+customer\s+service\b",
    r"(?:3rd|4th|5th|several)\s+times?\b", r"\bwaiting\s+for\s+(?:weeks|months)\b",
    r"\bopen\s+case\s+#\b", r"\bcase\s+#\d+\b", r"\btrade-in\b"
]

# High-stakes billing triggers
DISPUTED_BILLING_TRIGGERS = [
    r"\bcharged\s+without\s+permission\b", r"\bfraudulent\s+charge\b",
    r"\bbank\s+dispute\b", r"\bcharged\s+\$\d{2,}\b", r"\bcharged\s+every\s+month\b",
    r"\bcharging\s+my\s+credit\s+card\b", r"\bcanceled\s+\d+\s+months\s+ago\b",
    r"\bfull\s+refund\b"
]

class EscalationRouter:
    """Evaluates customer message risk, intent, and complexity to decide auto-handle vs escalation."""

    def __init__(self, confidence_threshold: float = 0.55):
        self.confidence_threshold = confidence_threshold

    def evaluate(self, customer_text: str, intent: str, intent_confidence: float) -> Dict[str, Any]:
        """
        Evaluates triage decision:
        Returns:
            should_escalate: bool
            escalation_reason: str
            risk_category: str (safety, security, hardware, sentiment, ambiguity, or none)
            confidence: float
        """
        text_lower = customer_text.lower()

        # 1. Critical Physical Safety Risk (Highest Priority)
        for pattern in SAFETY_TRIGGERS:
            if re.search(pattern, text_lower):
                return {
                    "should_escalate": True,
                    "escalation_reason": "Critical physical safety/thermal hazard detected; immediate in-person service required.",
                    "risk_category": "safety",
                    "triage_confidence": 0.99
                }

        # 2. Account Security & Compromise Risk
        for pattern in SECURITY_TRIGGERS:
            if re.search(pattern, text_lower):
                return {
                    "should_escalate": True,
                    "escalation_reason": "Account compromise or unauthorized security alteration requires authenticated specialist verification.",
                    "risk_category": "security",
                    "triage_confidence": 0.95
                }

        # 3. Explicit Human Demand / Extreme Hostility / Legal Threat
        if intent == "human_escalation_dm_transfer":
            return {
                "should_escalate": True,
                "escalation_reason": "Customer explicitly requested human agent or expressed extreme dissatisfaction/escalation.",
                "risk_category": "sentiment",
                "triage_confidence": 0.98
            }

        for pattern in HOSTILITY_TRIGGERS:
            if re.search(pattern, text_lower):
                return {
                    "should_escalate": True,
                    "escalation_reason": "High customer distress, repeat issue failure, or supervisor request detected.",
                    "risk_category": "sentiment",
                    "triage_confidence": 0.92
                }

        # 4. Physical Hardware Damage
        for pattern in HARDWARE_DAMAGE_TRIGGERS:
            if re.search(pattern, text_lower):
                return {
                    "should_escalate": True,
                    "escalation_reason": "Physical hardware damage requires authorized repair reservation.",
                    "risk_category": "hardware",
                    "triage_confidence": 0.90
                }

        # 5. Disputed Billing Multi-Charge
        for pattern in DISPUTED_BILLING_TRIGGERS:
            if re.search(pattern, text_lower):
                return {
                    "should_escalate": True,
                    "escalation_reason": "Disputed monetary charge or subscription fraud requires private account audit via DM.",
                    "risk_category": "financial",
                    "triage_confidence": 0.88
                }

        # 6. Intent Ambiguity / Low Model Confidence
        if intent_confidence < self.confidence_threshold:
            return {
                "should_escalate": True,
                "escalation_reason": f"Low intent confidence ({intent_confidence:.2f} < threshold {self.confidence_threshold}); routing to human to avoid incorrect resolution.",
                "risk_category": "ambiguity",
                "triage_confidence": 0.85
            }

        # 7. Safe for Automated Handling
        return {
            "should_escalate": False,
            "escalation_reason": "Standard inquiry with established self-service resolution path and verified safe parameters.",
            "risk_category": "none",
            "triage_confidence": 0.90
        }
