# AppleSupport AI Customer Support Agent

An end-to-end customer support triage and response system for **@AppleSupport** on Twitter, built on authentic customer interactions from the Kaggle Twitter Customer Support dataset (`thoughtvector/customer-support-on-twitter`).

The system performs three core tasks on incoming customer tweets:
1. **Intent Classification**: Classifies customer queries across 7 brand-specific support intents.
2. **Escalation Routing**: Triage engine that separates auto-handled inquiries from issues requiring human escalation, returning an explicit stated justification and risk category.
3. **Grounded Brand Response Generation**: Drafts brand-compliant replies grounded in Apple's historical resolutions and official support articles (`support.apple.com`, `apple.co/*`), bounded by Twitter's 280-character constraint and privacy guardrails.

---

## Quickstart

### 1. Requirements & Setup
- Python 3.10+
- Install dependencies:
```bash
pip install -r requirements.txt
```
*(Core dependencies: `pandas`, `scikit-learn`, `numpy`).*

### 2. Run the Agent CLI
Process a single query directly:
```bash
python main.py -q "@AppleSupport My iPhone screen is bulging and getting burning hot while charging!"
```

Start an interactive session:
```bash
python main.py
```

Get structured JSON output:
```bash
python main.py -q "@AppleSupport I was charged twice for Apple Music this month" --json
```

### 3. Run Benchmark Evaluation (< 1 minute)
Reproduces benchmark evaluation metrics across the 200-sample hand-labelled Golden Evaluation Set against both baselines:
```bash
python scripts/run_evaluation.py
```

### 4. Run Test Suite
```bash
python -m unittest discover -s tests
```

---

## Input / Output Examples

Below are representative inputs and outputs across various intents, triage decisions, and execution modes.

### Example 1: Standard Technical Troubleshooting (Auto-Handled)
**Input:**
```bash
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

### Example 2: Self-Service Billing & Subscription (Auto-Handled)
**Input:**
```bash
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

### Example 3: Critical Safety & Thermal Hazard (Escalated to Human)
**Input:**
```bash
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

### Example 4: Account Compromise & Security Alert (Escalated to Human)
**Input:**
```bash
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

### Example 5: Explicit Human Demand / Customer Frustration (Escalated to Human)
**Input:**
```bash
python main.py -q "@AppleSupport Stop giving me canned bot replies. I've been waiting 3 weeks for my repair and I need to speak with a human manager now!"
```
**Output:**
```text
Incoming Tweet:     "@AppleSupport Stop giving me canned bot replies. I've been waiting 3 weeks for my repair and I need to speak with a human manager now!"
Classified Intent:  human_escalation_dm_transfer (Confidence: 1.00)
Triage Decision:    [ESCALATE TO HUMAN]
Decision Reason:    Customer explicitly requested human intervention or expressed severe dissatisfaction.
Risk Category:      distress
Guardrails Status:  PASSED

Drafted Brand Reply:
  "We'd love to help with this. We understand your frustration. Please send us a DM with your details so a senior advisor can look into your case: apple.co/DM"
```

---

### Example 6: Structured JSON Output (`--json`)
**Input:**
```bash
python main.py -q "@AppleSupport How do I reset my Apple ID password?" --json
```
**Output:**
```json
{
  "intent": "icloud_appleid_security",
  "intent_confidence": 1.0,
  "probabilities": {
    "battery_hardware_performance": 0.0,
    "os_software_update_bugs": 0.0,
    "icloud_appleid_security": 1.0,
    "billing_subscriptions_purchases": 0.0,
    "connectivity_network_bluetooth": 0.0,
    "audio_display_accessories": 0.0,
    "human_escalation_dm_transfer": 0.0
  },
  "should_escalate": false,
  "escalation_reason": "Standard inquiry with established self-service resolution path and verified safe parameters.",
  "risk_category": "none",
  "reply": "We'd love to help with this. For security issues or password resets, you can securely recover your account at https://iforgot.apple.com.",
  "generation_mode": "grounded_retrieval_template",
  "guardrail_passed": true,
  "violations": [],
  "official_url": "https://iforgot.apple.com",
  "retrieved_exemplars_count": 2
}
```

---

### Example 7: Interactive Terminal Session
```text
$ python main.py
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

Evaluated on the **200 hand-curated and stratified Golden Evaluation Set** comparing our agent against two baselines:
1. **Trivial Baseline**: Majority-class intent predictor (`os_software_update_bugs`), never escalates, static fallback reply.
2. **Simple Baseline**: Naive keyword search without disambiguation and fixed keyword escalation.

| Metric | Trivial Baseline | Simple Keyword Baseline | **AppleSupport AI Agent** | Delta vs. Simple Baseline |
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

### Human-Judge Calibration
Evaluated on a 50-example validation split comparing human ratings against the automated judge rubric:
- **Cohen's Kappa**: `0.842` (strong inter-rater agreement)
- **Mean Absolute Error (MAE)**: `0.640` points on a 1-5 scale
- **Agreement within 1 star**: `80.0%`

---

## Architecture & Workflow

```text
               Incoming Customer Tweet
                         │
                         ▼
             ┌────────────────────────┐
             │   Intent Classifier    │
             │   (7 Brand Intents)    │
             └───────────┬────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│ Escalation Router│           │    Retriever     │
│ (Risk & Safety)  │           │  (BM25 + KB)     │
└────────┬─────────┘           └────────┬─────────┘
         │                              │
         └───────────────┬──────────────┘
                         ▼
             ┌────────────────────────┐
             │   Response Generator   │
             │ (Brand Voice & URLs)   │
             └───────────┬────────────┘
                         │
                         ▼
             ┌────────────────────────┐
             │   Safety Guardrails    │
             │ (PII & 280-char limit) │
             └───────────┬────────────┘
                         │
                         ▼
               Draft Reply + Metadata
```

---

## Project Structure

```text
Ai_agent/
├── README.md                   # Project overview, setup, and I/O examples
├── REPORT.md                   # Engineering report, failure analysis, decision log
├── requirements.txt            # Python dependencies
├── main.py                     # CLI entrypoint (single-query, interactive, JSON)
├── data/
│   ├── apple_support_pairs.json    # 4,947 authentic historical tweet-reply pairs
│   ├── historical_knowledge.json   # Structured knowledge base with exemplars
│   ├── golden_eval_set.json        # 200 hand-labelled evaluation samples
│   ├── label_guidelines.md         # Annotation protocol and taxonomy rules
│   └── eval_results.json           # Cached benchmark evaluation artifacts
├── src/
│   ├── __init__.py
│   ├── agent.py                # Full pipeline orchestrator
│   ├── intent_classifier.py    # 7-intent classification engine
│   ├── escalation_router.py    # Risk assessment and escalation rules
│   ├── retriever.py            # BM25 knowledge retriever
│   ├── generator.py            # Grounded response generator
│   ├── baselines.py            # Trivial and simple baseline agents
│   └── evaluator.py            # Automated metrics, rubric judge, calibration
├── tests/
│   └── test_pipeline.py        # Unit and integration test suite
└── scripts/
    ├── build_dataset.py            # Dataset extraction script
    ├── curate_eval_and_kb.py       # Knowledge base curation helper
    ├── generate_golden_eval_set.py # Golden set validator and generator
    └── run_evaluation.py           # Benchmark runner
```

---

## Deliverables Summary

1. **Runnable Pipeline**: Complete working pipeline with CLI in `main.py` and benchmark harness in `scripts/run_evaluation.py`.
2. **Golden Evaluation Set**: 200 hand-labelled instances in `data/golden_eval_set.json` with sampling criteria in `data/label_guidelines.md`.
3. **Evaluation Harness**: Automated metrics (Accuracy, F1, ROUGE, BLEU) + 5-dimension judge rubric with human calibration in `src/evaluator.py`.
4. **Engineering Report**: Detailed 6-page report in `REPORT.md` covering problem framing, baseline comparisons, top 5 failure modes, headline number critique, 1-week roadmap, and 12-item decision log.
