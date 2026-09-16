"""
test_pipeline.py
Unit and Integration test suite for AppleSupport AI Agent.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deps")))

from src.intent_classifier import IntentClassifier
from src.escalation_router import EscalationRouter
from src.generator import GroundedResponseGenerator
from src.agent import AppleSupportAgent

class TestAppleSupportAgent(unittest.TestCase):

    def setUp(self):
        self.agent = AppleSupportAgent()
        self.classifier = IntentClassifier(use_llm_if_available=False)
        self.router = EscalationRouter()
        self.generator = GroundedResponseGenerator(use_llm_if_available=False)

    def test_battery_intent_classification(self):
        tweet = "@AppleSupport My iPhone 13 battery drains 40% in two hours after update. Help!"
        res = self.classifier.classify(tweet)
        self.assertEqual(res["intent"], "battery_hardware_performance")

    def test_security_intent_classification(self):
        tweet = "@AppleSupport I forgot my Apple ID password and my account is locked."
        res = self.classifier.classify(tweet)
        self.assertEqual(res["intent"], "icloud_appleid_security")

    def test_billing_intent_classification(self):
        tweet = "@AppleSupport How do I cancel my Apple Music subscription and request a refund?"
        res = self.classifier.classify(tweet)
        self.assertEqual(res["intent"], "billing_subscriptions_purchases")

    def test_safety_escalation_hazard(self):
        tweet = "@AppleSupport My battery is swollen and bulging out of the case and getting hot!"
        res = self.agent.process(tweet)
        self.assertTrue(res["should_escalate"])
        self.assertEqual(res["risk_category"], "safety")
        self.assertIn("apple.co/DM", res["reply"])

    def test_hostility_and_human_escalation(self):
        tweet = "@AppleSupport I demand to speak to a real human manager right now or I am calling my lawyer!"
        res = self.agent.process(tweet)
        self.assertTrue(res["should_escalate"])
        self.assertEqual(res["intent"], "human_escalation_dm_transfer")
        self.assertEqual(res["risk_category"], "sentiment")

    def test_safe_autohandle(self):
        tweet = "@AppleSupport My Wi-Fi keeps disconnecting from my home network."
        res = self.agent.process(tweet)
        self.assertFalse(res["should_escalate"])
        self.assertEqual(res["intent"], "connectivity_network_bluetooth")
        self.assertTrue(res["guardrail_passed"])
        self.assertIn("Reset Network Settings", res["reply"])

    def test_privacy_guardrail(self):
        risky_reply = "Please send your Apple ID password and credit card number so we can fix this."
        guard = self.generator.apply_guardrails(risky_reply)
        self.assertFalse(guard["passed"])
        self.assertTrue(any("Privacy risk" in v for v in guard["violations"]))

if __name__ == "__main__":
    unittest.main()
