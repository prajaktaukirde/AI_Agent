"""
generator.py
Grounded Response Generator for AppleSupport AI Agent.
Enforces authentic Apple brand voice, factual grounding from historical exemplars,
and strict safety/privacy guardrails.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional

OFFICIAL_URL_WHITELIST = [
    "https://support.apple.com",
    "https://iforgot.apple.com",
    "https://reportaproblem.apple.com",
    "https://icloud.com",
    "apple.co/DM",
    "apple.co/ForceRestart",
    "apple.co/Temp",
    "apple.co/PaymentDecline",
    "apple.co/WiFiHelp",
    "apple.co/AirPodsService",
    "apple.co/CancelSub"
]

class GroundedResponseGenerator:
    """Generates grounded, brand-aligned customer support replies with guardrail verification."""

    def __init__(self, use_llm_if_available: bool = True):
        self.use_llm_if_available = use_llm_if_available
        self.openai_client = None

        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key and use_llm_if_available:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)
            except Exception:
                self.openai_client = None

    def apply_guardrails(self, reply: str) -> Dict[str, Any]:
        """Validates generated reply against privacy, brand safety, and length constraints."""
        violations = []
        clean_reply = reply.strip()

        # 1. Privacy guardrail
        pii_patterns = [
            r"password", r"passcode", r"credit\s+card", r"cvv", r"social\s+security", r"pin\s+code"
        ]
        for p in pii_patterns:
            if re.search(r"(?:send|provide|give|share).*(?:your|the)?\s*" + p, clean_reply, re.IGNORECASE):
                violations.append(f"Privacy risk: public request for sensitive credential ({p})")
            elif re.search(p, clean_reply, re.IGNORECASE) and "password" in p:
                violations.append(f"Privacy risk: public mention/request for sensitive credential ({p})")

        # 2. Length check (Twitter 280-char preference)
        if len(clean_reply) > 350:
            # Truncate gracefully or split
            clean_reply = clean_reply[:340] + "..."
            violations.append("Length warning: reply exceeded 280-character target, truncated.")

        # 3. Tone opening check
        has_warm_opening = bool(re.search(r"^(We'd|We're|Let's|Thanks|Hello|Hi|Your safety)", clean_reply, re.IGNORECASE))
        if not has_warm_opening:
            clean_reply = f"We'd love to help with this. {clean_reply}"

        return {
            "sanitized_reply": clean_reply,
            "passed": len([v for v in violations if "Privacy risk" in v]) == 0,
            "violations": violations
        }

    def generate_llm(
        self,
        customer_query: str,
        intent: str,
        should_escalate: bool,
        escalation_reason: str,
        exemplars: List[Dict[str, Any]],
        intent_info: Dict[str, Any]
    ) -> Optional[str]:
        """Generates response using LLM grounded on historical exemplars and policy."""
        if not self.openai_client:
            return None

        exemplar_context = "\n".join([
            f"- Customer: {ex['query']}\n  AppleSupport: {ex['reply']}"
            for ex in exemplars[:2]
        ])

        system_prompt = """You are the official @AppleSupport AI assistant on Twitter.
Your goal is to draft a helpful, concise, empathetic reply grounded in authentic Apple Support historical practices.

Brand Guidelines:
1. Empathy & Tone: Warm, professional ('We'd love to help with this', 'We understand how important this is').
2. Ask for missing details: Device model and OS version when troubleshooting technical glitches.
3. Escalation: If escalated, guide the user to DM (apple.co/DM) for private assistance or authorized service.
4. Privacy: NEVER ask for passwords, credit card numbers, or 2FA codes in a public tweet.
5. Conciseness: Keep the reply under 250 characters if possible (max 280).
"""

        user_prompt = f"""Incoming Customer Tweet: "{customer_query}"
Classified Intent: {intent}
Triage Decision: {"ESCALATE TO HUMAN" if should_escalate else "AUTO-HANDLE"}
Reason for Decision: {escalation_reason}
Official URL: {intent_info.get('official_url', 'https://support.apple.com')}

Historical Exemplars from similar cases:
{exemplar_context}

Draft the exact tweet reply for @AppleSupport:"""

        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            reply = resp.choices[0].message.content.strip()
            # Remove quotes if LLM added them
            if reply.startswith('"') and reply.endswith('"'):
                reply = reply[1:-1].strip()
            return reply
        except Exception:
            return None

    def generate_deterministic_grounded(
        self,
        customer_query: str,
        intent: str,
        should_escalate: bool,
        escalation_reason: str,
        exemplars: List[Dict[str, Any]],
        intent_info: Dict[str, Any]
    ) -> str:
        """Deterministic grounded fallback synthesis using intent KB and top exemplar."""
        url = intent_info.get("official_url", "https://support.apple.com")

        if should_escalate:
            if "safety" in escalation_reason.lower() or "swelling" in escalation_reason.lower():
                return "Your safety is our top priority. Please stop using and charging the device. Send us a DM with your location so we can arrange an urgent service reservation: apple.co/DM"
            elif "compromise" in escalation_reason.lower() or "security" in escalation_reason.lower():
                return "We take account security very seriously. Please reach out to us via DM immediately so our account security team can assist you securely: apple.co/DM"
            elif "dispute" in escalation_reason.lower() or "billing" in escalation_reason.lower():
                return "We want to ensure your account is accurate. Please send us a DM with your Apple ID email so our billing team can review this securely: apple.co/DM"
            else:
                return "We understand this is frustrating and we want to help. Please click here to send us a DM so a specialist can assist you directly: apple.co/DM"

        # Auto-handled responses grounded in best exemplar or intent action
        if exemplars and exemplars[0].get("score", 0) > 3.0 and exemplars[0].get("intent") == intent:
            top_reply = exemplars[0]["reply"]
            # Clean reply
            top_reply = re.sub(r"^@\w+\s*", "", top_reply).strip()
            if len(top_reply) > 20:
                if not top_reply.startswith(("We'd", "We're", "Let's", "Thanks", "Hello", "Hi", "You can")):
                    top_reply = f"We'd love to help with this. {top_reply}"
                return top_reply

        # Intent-specific structured troubleshooting templates
        templates = {
            "battery_hardware_performance": f"We'd love to help with your battery performance. Check Settings > Battery > Battery Health and ensure your device is running the latest iOS update. More tips here: {url}",
            "os_software_update_bugs": f"We'd be glad to help with this update. Try force restarting your device and ensuring you have at least 10GB of available storage in Settings > General > iPhone Storage: {url}",
            "icloud_appleid_security": f"We can help you regain access. You can reset your Apple ID password directly at https://iforgot.apple.com or manage iCloud sync settings in Settings > [Your Name] > iCloud.",
            "billing_subscriptions_purchases": f"We can help with your purchases. You can review your charges, cancel subscriptions, or request a refund directly at https://reportaproblem.apple.com.",
            "connectivity_network_bluetooth": f"Let's get your connection working. Try resetting network settings in Settings > General > Transfer or Reset iPhone > Reset > Reset Network Settings, or toggle Airplane Mode: {url}",
            "audio_display_accessories": f"We'd like to help troubleshoot your accessory. Try resetting your AirPods or cleaning the speaker ports with a dry cloth. Learn more here: {url}",
            "human_escalation_dm_transfer": "We hear you and want to help right away. Please send us a DM so an advisor can look into your case directly: apple.co/DM"
        }

        return templates.get(intent, f"We'd love to help resolve this. Please check our official guide at {url} or let us know your exact device model and OS version.")

    def generate(
        self,
        customer_query: str,
        intent: str,
        should_escalate: bool,
        escalation_reason: str,
        exemplars: List[Dict[str, Any]],
        intent_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Main generation pipeline with guardrails."""
        reply = None
        generation_mode = "deterministic_grounded_template"

        if self.use_llm_if_available and self.openai_client:
            reply = self.generate_llm(
                customer_query, intent, should_escalate, escalation_reason, exemplars, intent_info
            )
            if reply:
                generation_mode = "llm_few_shot_grounded"

        if not reply:
            reply = self.generate_deterministic_grounded(
                customer_query, intent, should_escalate, escalation_reason, exemplars, intent_info
            )

        guardrail_result = self.apply_guardrails(reply)

        return {
            "reply": guardrail_result["sanitized_reply"],
            "generation_mode": generation_mode,
            "guardrail_passed": guardrail_result["passed"],
            "violations": guardrail_result["violations"]
        }
