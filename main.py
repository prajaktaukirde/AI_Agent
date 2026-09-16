#!/usr/bin/env python3
"""
main.py - Interactive CLI for AppleSupport AI Agent
Allows testing interactive queries, running batch predictions, and verifying agent decisions.
"""

import sys
import os
import argparse
import json

# Ensure modules in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "deps")))

from src.agent import AppleSupportAgent

def main():
    parser = argparse.ArgumentParser(description="AppleSupport AI Agent CLI")
    parser.add_argument("--query", "-q", type=str, help="Customer tweet text to process")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive terminal session")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")
    
    args = parser.parse_args()
    agent = AppleSupportAgent()

    if args.query:
        result = agent.process(args.query)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_result(args.query, result)
        return

    if args.interactive or not args.query:
        print("================================================================")
        print("  🍎 AppleSupport AI Agent - Interactive Test Console           ")
        print("================================================================")
        print("Type a simulated customer tweet (or 'exit' / 'quit' to finish):\n")

        while True:
            try:
                user_input = input("Customer Tweet > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Exiting AppleSupport AI Agent console.")
                    break
                
                result = agent.process(user_input)
                print_result(user_input, result)
                print("-" * 64)
            except (KeyboardInterrupt, EOFError):
                print("\nSession ended.")
                break

def print_result(query: str, res: dict):
    triage_color = "\033[91m[ESCALATE TO HUMAN]\033[0m" if res["should_escalate"] else "\033[92m[AUTO-HANDLE]\033[0m"
    print(f"\nIncoming Tweet:     \"{query}\"")
    print(f"Classified Intent:  {res['intent']} (Confidence: {res['intent_confidence']:.2f})")
    print(f"Triage Decision:    {triage_color}")
    print(f"Decision Reason:    {res['escalation_reason']}")
    print(f"Risk Category:      {res['risk_category']}")
    print(f"Guardrails Status:  {'PASSED' if res['guardrail_passed'] else 'VIOLATION DETECTED'}")
    print(f"\nDrafted Brand Reply:\n  \"{res['reply']}\"\n")

if __name__ == "__main__":
    main()
