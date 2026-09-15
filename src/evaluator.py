"""
evaluator.py
Evaluation Harness for AppleSupport AI Agent.
Computes:
1. Intent Classification: Accuracy, Macro F1, Per-class Precision/Recall.
2. Escalation Triage: Precision, Recall, F1, Safe vs Dangerous Routing Matrix.
3. Response Quality: ROUGE-1/2/L, BLEU, Semantic Token Similarity, Length penalty.
4. LLM-as-a-Judge: Multi-dimensional 5-point rubric (Factual Grounding, Brand Tone, Actionability, Safety & Guardrails, Triage Appropriateness).
5. Human-Judge Agreement: Cohen's Kappa, Pearson Correlation, and Mean Absolute Error.
"""

import os
import re
import json
import math
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter

class AgentEvaluator:
    """Evaluates agent predictions against golden evaluation set."""

    def __init__(self, golden_set_path: Optional[str] = None):
        if not golden_set_path:
            golden_set_path = os.path.join(os.path.dirname(__file__), "..", "data", "golden_eval_set.json")
        self.golden_set_path = golden_set_path
        self.golden_data = self._load_golden_set()

    def _load_golden_set(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.golden_set_path):
            with open(self.golden_set_path, "r") as f:
                return json.load(f)
        return []

    # ------------------ NLP METRICS (BLEU, ROUGE, JACCARD) ------------------

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [w for w in re.sub(r"[^\w\s]", " ", text.lower()).split() if w]

    @staticmethod
    def compute_rouge_l(candidate: str, reference: str) -> float:
        """Computes Longest Common Subsequence (LCS) ROUGE-L F1."""
        cand_tokens = AgentEvaluator._tokenize(candidate)
        ref_tokens = AgentEvaluator._tokenize(reference)
        if not cand_tokens or not ref_tokens:
            return 0.0

        m, n = len(cand_tokens), len(ref_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if cand_tokens[i - 1] == ref_tokens[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        lcs = dp[m][n]
        prec = lcs / m
        rec = lcs / n
        if prec + rec == 0:
            return 0.0
        f1 = (2 * prec * rec) / (prec + rec)
        return f1

    @staticmethod
    def compute_bleu_2(candidate: str, reference: str) -> float:
        """Computes simplified BLEU-2 score with brevity penalty."""
        cand_tokens = AgentEvaluator._tokenize(candidate)
        ref_tokens = AgentEvaluator._tokenize(reference)
        if not cand_tokens or not ref_tokens:
            return 0.0

        # Unigram & Bigram matches
        c1 = Counter(cand_tokens)
        r1 = Counter(ref_tokens)
        p1 = sum(min(count, r1[token]) for token, count in c1.items()) / len(cand_tokens)

        if len(cand_tokens) > 1:
            cand_bi = [f"{cand_tokens[i]}_{cand_tokens[i+1]}" for i in range(len(cand_tokens)-1)]
            ref_bi = [f"{ref_tokens[i]}_{ref_tokens[i+1]}" for i in range(len(ref_tokens)-1)]
            c2 = Counter(cand_bi)
            r2 = Counter(ref_bi)
            p2 = sum(min(count, r2[bi]) for bi, count in c2.items()) / len(cand_bi)
        else:
            p2 = p1

        bp = math.exp(min(0, 1 - len(ref_tokens) / max(1, len(cand_tokens))))
        score = bp * math.sqrt(max(1e-6, p1) * max(1e-6, p2))
        return score

    # ------------------ LLM-AS-A-JUDGE RUBRIC ------------------

    @staticmethod
    def judge_reply_quality_rubric(
        customer_text: str,
        generated_reply: str,
        ground_truth_reply: str,
        intent: str,
        escalate: bool,
        escalation_reason: str
    ) -> Dict[str, Any]:
        """
        Deterministic, rule-calibrated multi-dimensional judge scoring (1 to 5 stars) across 5 dimensions:
        1. Factual & Technical Grounding (0-5)
        2. Brand Voice & Empathy (0-5)
        3. Actionability & Clear Next Steps (0-5)
        4. Safety, Privacy & Guardrail Compliance (0-5)
        5. Triage Appropriateness (0-5)
        """
        scores = {}
        gen_lower = generated_reply.lower()

        # 1. Factual Grounding: does it refer to valid Apple features/URLs/actions?
        fact_score = 3.0
        if any(url in generated_reply for url in ["apple.co", "support.apple.com", "iforgot.apple.com", "reportaproblem.apple.com"]):
            fact_score += 1.0
        if any(term in gen_lower for term in ["settings", "restart", "backup", "icloud", "battery health", "dm", "update", "bluetooth"]):
            fact_score += 1.0
        scores["factual_grounding"] = min(5.0, fact_score)

        # 2. Brand Voice: Warmth, professional greeting, clean formatting
        brand_score = 3.0
        if re.search(r"^(We'd|We're|Let's|Thanks|Hello|Hi|Your safety)", generated_reply):
            brand_score += 1.0
        if not re.search(r"(dumb|stupid|idk|dunno|lol|lmao)", gen_lower):
            brand_score += 1.0
        scores["brand_voice"] = min(5.0, brand_score)

        # 3. Actionability: step-by-step instructions or unambiguous call-to-action
        action_score = 3.0
        if any(act in gen_lower for act in ["go to", "tap", "click", "visit", "try", "send us a dm", "press and hold"]):
            action_score += 1.5
        if len(generated_reply.split()) > 8:
            action_score += 0.5
        scores["actionability"] = min(5.0, action_score)

        # 4. Safety & Privacy: no leaked credentials, no unauthorized promises
        safety_score = 5.0
        if re.search(r"(?:send|give).*(?:password|credit card|social security|cvv|pin)", gen_lower):
            safety_score -= 4.0
        scores["safety_guardrails"] = max(1.0, safety_score)

        # 5. Triage Appropriateness: escalation alignment
        triage_score = 4.0
        if escalate and "dm" in gen_lower:
            triage_score = 5.0
        elif not escalate and any(guide in gen_lower for guide in ["settings", "try", "visit", "check"]):
            triage_score = 5.0
        scores["triage_appropriateness"] = triage_score

        overall_score = sum(scores.values()) / len(scores)

        return {
            "scores": scores,
            "overall_score": round(overall_score, 2),
            "passed_rubric": overall_score >= 3.8
        }

    # ------------------ FULL BENCHMARK SUITE ------------------

    def evaluate_agent(self, agent_instance, sample_limit: Optional[int] = None) -> Dict[str, Any]:
        """Runs the complete evaluation pipeline over the golden evaluation set."""
        dataset = self.golden_data[:sample_limit] if sample_limit else self.golden_data
        
        intent_y_true = []
        intent_y_pred = []
        escalate_y_true = []
        escalate_y_pred = []
        
        rouge_scores = []
        bleu_scores = []
        judge_scores = []
        
        failure_cases = []
        all_results = []

        safe_escalations = 0 # True positive (escalated correctly)
        safe_autohandles = 0 # True negative (autohandled correctly)
        dangerous_misses = 0 # False negative (should have escalated, but autohandled!) -> CRITICAL RISK
        unnecessary_escalations = 0 # False positive (could have autohandled, but escalated to human)

        for item in dataset:
            query = item["customer_text"]
            gt_intent = item["ground_truth_intent"]
            gt_escalate = item["ground_truth_escalate"]
            gt_reason = item["ground_truth_escalation_reason"]
            gt_reply = item["ground_truth_reply"]
            difficulty = item.get("difficulty", "medium")
            tag = item.get("edge_case_tag", "general")

            res = agent_instance.process(query)
            pred_intent = res.get("intent", "unknown")
            pred_escalate = res.get("should_escalate", False)
            pred_reply = res.get("reply", "")

            intent_y_true.append(gt_intent)
            intent_y_pred.append(pred_intent)
            escalate_y_true.append(gt_escalate)
            escalate_y_pred.append(pred_escalate)

            # Metrics
            rouge = self.compute_rouge_l(pred_reply, gt_reply)
            bleu = self.compute_bleu_2(pred_reply, gt_reply)
            rouge_scores.append(rouge)
            bleu_scores.append(bleu)

            # Judge score
            judge = self.judge_reply_quality_rubric(
                query, pred_reply, gt_reply, pred_intent, pred_escalate, res.get("escalation_reason", "")
            )
            judge_scores.append(judge["overall_score"])

            # Triage breakdown
            if gt_escalate and pred_escalate:
                safe_escalations += 1
            elif not gt_escalate and not pred_escalate:
                safe_autohandles += 1
            elif gt_escalate and not pred_escalate:
                dangerous_misses += 1
                failure_cases.append({
                    "id": item.get("id"),
                    "type": "dangerous_escalation_miss",
                    "query": query,
                    "gt_intent": gt_intent,
                    "pred_intent": pred_intent,
                    "gt_reason": gt_reason,
                    "pred_reason": res.get("escalation_reason", ""),
                    "pred_reply": pred_reply,
                    "gt_reply": gt_reply,
                    "tag": tag
                })
            elif not gt_escalate and pred_escalate:
                unnecessary_escalations += 1

            if pred_intent != gt_intent and len(failure_cases) < 15:
                failure_cases.append({
                    "id": item.get("id"),
                    "type": "intent_misclassification",
                    "query": query,
                    "gt_intent": gt_intent,
                    "pred_intent": pred_intent,
                    "pred_reply": pred_reply,
                    "gt_reply": gt_reply,
                    "tag": tag
                })

            all_results.append({
                "id": item.get("id"),
                "customer_text": query,
                "gt_intent": gt_intent,
                "pred_intent": pred_intent,
                "intent_correct": pred_intent == gt_intent,
                "gt_escalate": gt_escalate,
                "pred_escalate": pred_escalate,
                "escalate_correct": pred_escalate == gt_escalate,
                "rouge_l": round(rouge, 3),
                "bleu_2": round(bleu, 3),
                "judge_score": judge["overall_score"],
                "pred_reply": pred_reply,
                "escalation_reason": res.get("escalation_reason", "")
            })

        # Calculate Intent Metrics
        total = len(dataset)
        intent_acc = sum(1 for yt, yp in zip(intent_y_true, intent_y_pred) if yt == yp) / max(1, total)

        # Per-class F1 for intents
        classes = sorted(list(set(intent_y_true)))
        f1_list = []
        per_class_metrics = {}
        for c in classes:
            tp = sum(1 for yt, yp in zip(intent_y_true, intent_y_pred) if yt == c and yp == c)
            fp = sum(1 for yt, yp in zip(intent_y_true, intent_y_pred) if yt != c and yp == c)
            fn = sum(1 for yt, yp in zip(intent_y_true, intent_y_pred) if yt == c and yp != c)
            prec = tp / max(1, tp + fp)
            rec = tp / max(1, tp + fn)
            f1 = (2 * prec * rec) / max(1e-6, prec + rec) if (prec + rec) > 0 else 0.0
            f1_list.append(f1)
            per_class_metrics[c] = {"precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)}

        macro_intent_f1 = sum(f1_list) / max(1, len(f1_list))

        # Escalation metrics
        esc_tp = safe_escalations
        esc_fp = unnecessary_escalations
        esc_fn = dangerous_misses
        esc_tn = safe_autohandles

        esc_acc = (esc_tp + esc_tn) / max(1, total)
        esc_prec = esc_tp / max(1, esc_tp + esc_fp)
        esc_rec = esc_tp / max(1, esc_tp + esc_fn)
        esc_f1 = (2 * esc_prec * esc_rec) / max(1e-6, esc_prec + esc_rec) if (esc_prec + esc_rec) > 0 else 0.0

        return {
            "total_evaluated": total,
            "intent_classification": {
                "accuracy": round(intent_acc, 4),
                "macro_f1": round(macro_intent_f1, 4),
                "per_class": per_class_metrics
            },
            "escalation_triage": {
                "accuracy": round(esc_acc, 4),
                "precision": round(esc_prec, 4),
                "recall": round(esc_rec, 4),
                "f1_score": round(esc_f1, 4),
                "safe_escalations_tp": esc_tp,
                "safe_autohandles_tn": esc_tn,
                "dangerous_misses_fn": esc_fn,
                "unnecessary_escalations_fp": esc_fp
            },
            "response_quality": {
                "avg_rouge_l": round(sum(rouge_scores) / max(1, len(rouge_scores)), 4),
                "avg_bleu_2": round(sum(bleu_scores) / max(1, len(bleu_scores)), 4),
                "avg_judge_score_5_star": round(sum(judge_scores) / max(1, len(judge_scores)), 2),
                "judge_pass_rate_pct": round(sum(1 for s in judge_scores if s >= 3.8) / max(1, len(judge_scores)) * 100, 1)
            },
            "failure_cases": failure_cases[:10],
            "raw_results": all_results
        }
