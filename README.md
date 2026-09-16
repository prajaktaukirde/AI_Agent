# AppleSupport AI Customer Support Agent

An AI customer support triage and response agent for **@AppleSupport** on Twitter, built using the Kaggle Twitter Customer Support dataset (`thoughtvector/customer-support-on-twitter`).

The system performs three core tasks:
1. **Classifies intent** across 7 brand categories (battery, software update, security, billing, network, hardware/accessories, and escalation).
2. **Triages risk & decides escalation** (auto-handle vs. human escalation with an explicit stated reason).
3. **Drafts grounded replies** using historical Apple resolutions and official documentation links (`support.apple.com`, `apple.co/*`), while enforcing Twitter's 280-character limit and privacy guardrails.

---

## Quickstart (< 2 Minutes)

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run single query test
python main.py -q "@AppleSupport My iPhone screen is bulging and getting burning hot while charging!"

# 3. Run interactive CLI
python main.py

# 4. Run benchmarks on 200-sample Golden Evaluation Set
python scripts/run_evaluation.py

# 5. Run test suite
python -m unittest discover -s tests
```

---

## Examples & Output

### 1. Safety Hazard — Escalation to Human
```powershell
python main.py -q "@AppleSupport My iPhone screen is bulging and getting burning hot while charging!"
```
**Output:**
```text
Incoming Tweet:     "@AppleSupport My iPhone screen is bulging and getting burning hot while charging!"
Classified Intent:  audio_display_accessories (Confidence: 0.43)
Triage Decision:    [ESCALATE TO HUMAN]
Decision Reason:    Critical physical safety/thermal hazard detected; immediate in-person service required.
Risk Category:      safety
Guardrails Status:  PASSED

Drafted Brand Reply:
  "Your safety is our top priority. Please stop using and charging the device. Send us a DM with your location so we can arrange an urgent service reservation: apple.co/DM"
```

---

### 2. Standard Troubleshooting — Auto-Handled
```powershell
python main.py -q "@AppleSupport My iPhone Wi-Fi keeps disconnecting every few minutes after waking from sleep."
```
**Output:**
```text
Incoming Tweet:     "@AppleSupport My iPhone Wi-Fi keeps disconnecting every few minutes after waking from sleep."
Classified Intent:  connectivity_network_bluetooth (Confidence: 1.00)
Triage Decision:    [AUTO-HANDLE]
Decision Reason:    Standard inquiry with established self-service resolution path and verified safe parameters.
Risk Category:      none
Guardrails Status:  PASSED

Drafted Brand Reply:
  "We'd love to help with this. Let's get your connection working. Try toggling Wi-Fi off and back on in Settings > Wi-Fi, or reset your network settings: https://support.apple.com/HT204051"
```

---

### 3. Billing & Refund Request — Auto-Handled
```powershell
python main.py -q "@AppleSupport I was charged twice for my Apple Music subscription this month. Can I get a refund?"
```
**Output:**
```text
Incoming Tweet:     "@AppleSupport I was charged twice for my Apple Music subscription this month. Can I get a refund?"
Classified Intent:  billing_subscriptions_purchases (Confidence: 1.00)
Triage Decision:    [AUTO-HANDLE]
Decision Reason:    Standard inquiry with established self-service resolution path and verified safe parameters.
Risk Category:      none
Guardrails Status:  PASSED

Drafted Brand Reply:
  "We'd love to help with this. We can help with your purchases. You can review your charges, cancel subscriptions, or request a refund directly at https://reportaproblem.apple.com."
```

---

### 4. Account Security Compromise — Escalation to Human
```powershell
python main.py -q "@AppleSupport Someone hacked into my Apple ID, I keep getting two-factor verification codes I never requested!"
```
**Output:**
```text
Incoming Tweet:     "@AppleSupport Someone hacked into my Apple ID, I keep getting two-factor verification codes I never requested!"
Classified Intent:  icloud_appleid_security (Confidence: 1.00)
Triage Decision:    [ESCALATE TO HUMAN]
Decision Reason:    Account compromise or unauthorized security alteration requires authenticated specialist verification.
Risk Category:      security
Guardrails Status:  PASSED

Drafted Brand Reply:
  "We'd love to help with this. We take account security very seriously. Please reach out to us via DM immediately so our account security team can assist you securely: apple.co/DM"
```

---

### 5. Structured JSON Output (`--json`)
```powershell
python main.py -q "@AppleSupport How do I reset my Apple ID password?" --json
```
**Output:**
```json
{
  "intent": "icloud_appleid_security",
  "intent_confidence": 1.0,
  "should_escalate": false,
  "escalation_reason": "Standard inquiry with established self-service resolution path and verified safe parameters.",
  "risk_category": "none",
  "reply": "We'd love to help with this. For security issues or password resets, you can securely recover your account at https://iforgot.apple.com.",
  "guardrail_passed": true,
  "official_url": "https://iforgot.apple.com"
}
```

---

### 6. Interactive Session
```powershell
python main.py
```
**Output:**
```text
================================================================
  AppleSupport AI Agent - Interactive Test Console           
================================================================
Type a simulated customer tweet (or 'exit' / 'quit' to finish):

Customer Tweet > @AppleSupport My AirPods crackle in my left ear
Classified Intent:  audio_display_accessories (Confidence: 1.00)
Triage Decision:    [AUTO-HANDLE]
Decision Reason:    Standard inquiry with established self-service resolution path and verified safe parameters.
Risk Category:      none
Guardrails Status:  PASSED

Drafted Brand Reply:
  "We'd love to help with this. Let's get your audio sorted out. Clean the mesh with a dry cotton swab and test with another app: https://support.apple.com/HT211157"
----------------------------------------------------------------
Customer Tweet > exit
Exiting AppleSupport AI Agent console.
```

---

## Headline Benchmark Results

Evaluated across the **200-sample hand-labelled Golden Evaluation Set** (`data/golden_eval_set.json`):

| Metric | Trivial Baseline | Simple Keyword Baseline | **AppleSupport AI Agent** | Improvement |
|---|---|---|---|---|
| **Intent Accuracy** | 14.50% | 56.50% | **90.00%** | **+33.5%** |
| **Intent Macro F1** | 0.0357 | 0.5210 | **0.8976** | **+72.3%** |
| **Escalation Accuracy** | 75.50% | 73.00% | **88.50%** | **+15.5%** |
| **Escalation Recall** *(Catching Risks)* | 0.00% | 8.16% | **77.55%** | **+69.4%** |
| **Dangerous Misses (FN)** *(Lower is better)* | 49 / 49 (100%) | 45 / 49 (91.8%) | **11 / 49 (22.4%)** | **-75.6% Critical Risk** |
| **Response ROUGE-L F1** | 0.2519 | 0.0745 | **0.3346** | **+349.1%** |
| **Response BLEU-2** | 0.1820 | 0.0410 | **0.2528** | **+516.6%** |
| **LLM-as-a-Judge Score (1-5)** | 4.50 / 5.0 | 4.35 / 5.0 | **4.66 / 5.0** | **+0.31 pts** |
| **Judge Rubric Pass Rate (>=3.8)** | 92.0% | 88.5% | **100.0%** | **+11.5%** |

**Human-Judge Calibration (50 Samples):**
- Cohen's Kappa = **0.842** (strong agreement)
- Mean Absolute Error = **0.640** points
- 80.0% within 1 star rating

---

## Deliverables & Repository Map

- **Full Engineering Report**: [`REPORT.md`](REPORT.md) — 6-page report covering problem framing, failure analysis (top 5 failure modes), "What is misleading about my headline number?", 1-week roadmap, and 12-item decision log.
- **Golden Evaluation Set**: [`data/golden_eval_set.json`](data/golden_eval_set.json) (200 hand-labelled test cases) and [`data/label_guidelines.md`](data/label_guidelines.md).
- **Core Pipeline Modules**:
  - [`src/intent_classifier.py`](src/intent_classifier.py) — 7-intent classification
  - [`src/escalation_router.py`](src/escalation_router.py) — Risk assessment & triage
  - [`src/retriever.py`](src/retriever.py) — BM25 historical & KB retriever
  - [`src/generator.py`](src/generator.py) — Grounded reply generation & guardrails
  - [`src/evaluator.py`](src/evaluator.py) — Metrics, judge rubric & calibration
  - [`main.py`](main.py) — Interactive & single-query CLI
