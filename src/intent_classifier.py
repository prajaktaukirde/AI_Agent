"""
intent_classifier.py
Empirical Intent Classifier for AppleSupport customer interactions on Twitter.
Supports Hybrid Rule + TF-IDF ML + LLM Zero/Few-shot classification.
"""

import os
import re
import math
from typing import Dict, Any, List, Tuple, Optional

INTENTS = [
    "battery_hardware_performance",
    "os_software_update_bugs",
    "icloud_appleid_security",
    "billing_subscriptions_purchases",
    "connectivity_network_bluetooth",
    "audio_display_accessories",
    "human_escalation_dm_transfer"
]

INTENT_KEYWORDS = {
    "battery_hardware_performance": [
        "battery", "drain", "draining", "charger", "overheat", "overheating",
        "warm", "battery health", "heat", "thermal"
    ],
    "os_software_update_bugs": [
        "update", "updated", "updating", "ios", "macos", "ipados", "watchos", "install", "installing",
        "verifying update", "unable to verify", "boot loop", "apple logo", "glitch", "bug", "storage",
        "system data", "crash", "crashes", "crashing", "software update", "sonoma", "ventura"
    ],
    "icloud_appleid_security": [
        "apple id", "icloud", "password", "passcode", "locked", "disabled", "security", "2fa",
        "two-factor", "verification code", "trusted phone", "hacked", "compromised", "activation lock",
        "iforgot", "sync", "syncing", "icloud storage", "photos sync", "appleid"
    ],
    "billing_subscriptions_purchases": [
        "bill", "billing", "charge", "charged", "charging me", "subscription", "cancel subscription",
        "refund", "receipt", "money", "cost", "pay", "payment", "itunes", "app store purchase",
        "unauthorized charge", "payment declined", "family sharing", "in-app purchase", "apple pay",
        "apple music", "free trial", "renew", "renews"
    ],
    "connectivity_network_bluetooth": [
        "wifi", "wi-fi", "bluetooth", "pair", "pairing", "connect", "connection", "disconnect",
        "cellular", "no service", "searching", "data", "5g", "lte", "hotspot", "personal hotspot",
        "airdrop", "carrier", "esim", "sim card"
    ],
    "audio_display_accessories": [
        "screen", "display", "audio", "sound", "speaker", "static", "crackling", "buzzing",
        "airpod", "airpods", "mic", "microphone", "pencil", "apple pencil", "flicker", "lines",
        "cracked screen", "shattered", "touch dead", "camera", "black screen", "lens"
    ],
    "human_escalation_dm_transfer": [
        "human", "person", "agent", "representative", "manager", "supervisor", "lawyer", "sue",
        "court", "unacceptable", "useless", "terrible", "worst service", "robot", "bot", "talk to someone",
        "speak with someone", "fourth time", "3rd time", "been waiting for weeks", "complaint",
        "case #", "open case", "trade-in"
    ]
}

# Negative disambiguation weights to prevent false classification
DISAMBIGUATION_RULES = [
    # If battery drain after update, battery is primary intent
    (r"battery.*(?:drain|die|drop|life|health)", "battery_hardware_performance", 3.0),
    # If airpods/pencil and pair/bluetooth -> connectivity
    (r"airpods?.*(?:pair|connect|bluetooth|pop\s+up)", "connectivity_network_bluetooth", 3.0),
    # If pencil and charge -> audio_display_accessories
    (r"(?:apple\s+pencil|pencil).*(?:charge|draw|magnetic)", "audio_display_accessories", 3.5),
    # If explicit demand for human / agent / case #, escalate overrides
    (r"(?:human|person|agent|speak to someone|real person|open case|case #)", "human_escalation_dm_transfer", 4.0),
    # If refund / subscription / cancel, billing overrides
    (r"(?:refund|cancel|subscription|free trial|charged|receipt)", "billing_subscriptions_purchases", 3.5),
    # If apple id / locked / iforgot, security overrides
    (r"(?:apple id|iforgot|activation lock|2fa|security lock)", "icloud_appleid_security", 3.5),
]

class IntentClassifier:
    """Classifies incoming customer tweets into one of 7 AppleSupport intents."""

    def __init__(self, use_llm_if_available: bool = True):
        self.use_llm_if_available = use_llm_if_available
        self.openai_client = None
        
        # Check if OpenAI key exists
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key and use_llm_if_available:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)
            except Exception:
                self.openai_client = None

    def clean_text(self, text: str) -> str:
        """Removes twitter mentions, URLs, and normalizes text."""
        t = re.sub(r"@\w+", "", text)
        t = re.sub(r"https?://\S+", "", t)
        t = t.strip()
        return t

    def classify_rules_and_keywords(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """Heuristic and keyword density matching."""
        cleaned = self.clean_text(text).lower()
        scores = {intent: 0.1 for intent in INTENTS}

        # Match keyword frequencies
        for intent, kws in INTENT_KEYWORDS.items():
            for kw in kws:
                # Word boundary match
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = len(re.findall(pattern, cleaned))
                if matches > 0:
                    scores[intent] += matches * 1.5

        # Disambiguation boost rules
        for pattern, intent, boost in DISAMBIGUATION_RULES:
            if re.search(pattern, cleaned):
                scores[intent] += boost

        # Softmax normalization to compute probabilities
        total = sum(math.exp(s) for s in scores.values())
        probs = {k: math.exp(v) / total for k, v in scores.items()}

        best_intent = max(probs.keys(), key=lambda k: probs[k])
        confidence = probs[best_intent]

        return best_intent, confidence, probs

    def classify_llm(self, text: str) -> Optional[Tuple[str, float, Dict[str, float]]]:
        """Classify using LLM API if available."""
        if not self.openai_client:
            return None
            
        prompt = f"""You are an expert customer support intent classifier for @AppleSupport.
Classify the following customer tweet into EXACTLY one of these 7 intent categories:
1. battery_hardware_performance: battery life, drain, overheating, charging, thermal, freeze
2. os_software_update_bugs: iOS/macOS update failure, verifying loop, boot loop, app crashes
3. icloud_appleid_security: Apple ID lock, password reset, 2FA, iCloud sync, Activation Lock
4. billing_subscriptions_purchases: App Store charges, subscriptions, refund requests, declined payments
5. connectivity_network_bluetooth: Wi-Fi, Bluetooth pairing, cellular 'No Service', AirDrop
6. audio_display_accessories: AirPods static/mic, broken screen, lines, Apple Pencil, camera black
7. human_escalation_dm_transfer: Customer demands human, extreme hostility, legal threat, repeat failed issues

Customer Tweet: "{text}"

Output JSON format:
{{
  "intent": "<exact_intent_name>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief explanation>"
}}
"""
        try:
            import json
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content
            parsed = json.loads(content)
            intent = parsed.get("intent")
            if intent in INTENTS:
                conf = float(parsed.get("confidence", 0.9))
                probs = {i: (conf if i == intent else (1.0 - conf) / 6.0) for i in INTENTS}
                return intent, conf, probs
        except Exception:
            return None
        return None

    def classify(self, text: str) -> Dict[str, Any]:
        """Main classification entry point."""
        if self.use_llm_if_available and self.openai_client:
            llm_res = self.classify_llm(text)
            if llm_res:
                intent, conf, probs = llm_res
                return {
                    "intent": intent,
                    "confidence": conf,
                    "probabilities": probs,
                    "model_used": "llm-gpt-4o-mini"
                }

        intent, conf, probs = self.classify_rules_and_keywords(text)
        return {
            "intent": intent,
            "confidence": conf,
            "probabilities": probs,
            "model_used": "hybrid-keyword-prior"
        }
