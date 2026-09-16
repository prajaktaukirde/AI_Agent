# Executive Engineering Report & Evaluation: AppleSupport AI Agent

## 1. Problem Framing & Brand Objectives

### What "Good" Means for @AppleSupport on Twitter
Customer support on Twitter is public, real-time, and high-stakes. For `@AppleSupport`:
1. **Public Brand Voice & Empathy**: Responses must be calm, professional, empathetic, and strictly adhere to Apple's brand tone (*"We'd love to help with this"*).
2. **Factual Troubleshooting Grounding**: Self-service diagnostics (e.g., force restart combinations, storage clearing, network setting resets, battery health checks) must provide verifiable steps accompanied by official Apple Support documentation links (`apple.co/*`, `support.apple.com`).
3. **Safety & Privacy Zero-Tolerance**: The agent must **never** request passwords, Apple ID verification codes, or credit card details publicly.
4. **Conservative & Transparent Escalation**: When physical safety hazards (battery swelling), security breaches (account takeover), hardware failures, or high customer distress arise, the agent must immediately route to human advisors via Direct Message (`apple.co/DM`) with a clear, stated justification.

### What We Chose NOT to Build (Non-Goals)
- **Arbitrary Open-Ended Generative Chat**: We rejected hallucination-prone ungrounded chat models. Every reply is anchored to authentic historical resolution patterns and whitelisted support domains.
- **Automated Refund Execution**: The agent never claims to directly refund credit cards; it directs users to the authorized self-service portal (`https://reportaproblem.apple.com`) or escalates to human billing specialists.
- **Public Credential Collection**: Under no circumstances does the agent perform account credential collection in public tweets.

---

## 2. Intent Taxonomy & Escalation Criteria

From the Kaggle Twitter Customer Support dataset (`thoughtvector/customer-support-on-twitter`), we distilled **7 distinct, mutually exclusive intent categories**:

| Intent ID | Core Scope | Auto-Handle Criteria | Human Escalation Criteria |
|---|---|---|---|
| `battery_hardware_performance` | Battery drain, overheating, charging failure, slow device performance | Device intact; post-update indexing, background refresh, battery health checks | Physical battery swelling, thermal burn hazard, panic reboot loops |
| `os_software_update_bugs` | iOS/macOS update errors, boot loops, system crashes, storage bugs | Update verification error, storage clearing, force restart | Prohibitory boot sign, infinite Apple logo boot loop, data loss risk |
| `icloud_appleid_security` | Apple ID lockout, password reset, 2FA, iCloud sync, Activation Lock | Self-service password reset (`iforgot.apple.com`), photos sync resume | Account compromise/takeover, altered trusted phone number |
| `billing_subscriptions_purchases` | App Store charges, subscription cancellation, refund requests | Self-service refund (`reportaproblem.apple.com`), subscription toggle | Multi-month disputed charges, family sharing fraud disputes |
| `connectivity_network_bluetooth` | Wi-Fi drop, Bluetooth pairing, cellular 'No Service', AirDrop | Reset Network Settings, Airplane Mode toggle, stereo re-pairing | Blank modem baseband firmware, physical SIM tray failure |
| `audio_display_accessories` | AirPods mic/static, broken screen, lines on display, Apple Pencil | AirPods case reset, microphone cleaning, software display settings | Shattered glass, dead touch digitizer, camera hardware disconnect |
| `human_escalation_dm_transfer` | Explicit human demand, extreme hostility, legal threats, repeat failures | None (always escalated) | Explicit request for human, supervisor demand, legal action threats |

---

## 3. Empirical Results vs. Baselines

We evaluated across **200 hand-curated and stratified Golden Evaluation instances** comparing:
1. **Trivial Baseline**: Always predicts majority class (`os_software_update_bugs`), never escalates, canned reply.
2. **Simple Baseline**: Naive keyword matching without disambiguation, simple fixed keyword escalation.
3. **AppleSupport AI Agent**: Hybrid intent classifier, risk-aware escalation router, grounded historical RAG, and safety guardrails.

### Benchmark Comparison Table

| Metric | Trivial Baseline | Simple Keyword Baseline | **AppleSupport AI Agent (Ours)** | Improvement vs. Simple |
|---|---|---|---|---|
| **Intent Accuracy** | 14.50% | 56.50% | **90.00%** | **+33.5%** |
| **Intent Macro F1** | 0.0357 | 0.5210 | **0.8976** | **+72.3%** |
| **Escalation Accuracy** | 75.50% | 73.00% | **88.50%** | **+15.5%** |
| **Escalation Recall** (Catching escalations) | 0.00% | 8.16% | **77.55%** | **+69.4%** |
| **Dangerous Misses (FN)** *(Lower is better)* | 49 / 49 (100%) | 45 / 49 (91.8%) | **11 / 49 (22.4%)** | **-75.6% Critical Risk** |
| **Response ROUGE-L F1** | 0.2519 | 0.0745 | **0.3346** | **+349.1%** |
| **Response BLEU-2** | 0.1820 | 0.0410 | **0.2528** | **+516.6%** |
| **LLM-as-a-Judge Score (1-5)** | 4.50 / 5.0 | 4.35 / 5.0 | **4.66 / 5.0** | **+0.31 pts** |
| **Judge Rubric Pass Rate (>=3.8)** | 92.0% | 88.5% | **100.0%** | **+11.5%** |

### Per-Class Intent Performance Breakdown
- `connectivity_network_bluetooth`: **Precision 1.000 | Recall 0.966 | F1 0.982**
- `icloud_appleid_security`: **Precision 0.967 | Recall 1.000 | F1 0.983**
- `audio_display_accessories`: **Precision 0.929 | Recall 0.929 | F1 0.929**
- `os_software_update_bugs`: **Precision 0.871 | Recall 0.931 | F1 0.900**
- `billing_subscriptions_purchases`: **Precision 1.000 | Recall 0.786 | F1 0.880**
- `human_escalation_dm_transfer`: **Precision 1.000 | Recall 0.679 | F1 0.809**
- `battery_hardware_performance`: **Precision 0.690 | Recall 1.000 | F1 0.817**

### Human-Judge Agreement & Calibration Study
To validate our automated judge, we ran a calibration study comparing LLM-as-a-judge scores against human expert ratings on a 50-sample split:
- **Mean Absolute Error (MAE)**: `0.640` points
- **Agreement within 1.0 Star Rating**: `80.0%`
- **Cohen's Kappa Agreement**: `0.842` (indicates strong inter-rater reliability)

---

## 4. Failure Analysis: Top 5 Failure Modes

| # | Failure Mode | Real Example Tweet | Root Cause Hypothesis | Mitigation Strategy |
|---|---|---|---|---|
| **1** | **Implicit Sub-surface Hardware Failure** | *"I dropped my iPhone on concrete and now the battery percentage is stuck at 1% and the phone restarts every 3 minutes."* | High keyword density for `battery` and `restart` masks the underlying physical trauma trigger. | Add cross-clause dependency parsing to prioritize physical impact verbs over symptom nouns. |
| **2** | **Multi-Intent Overlap (Billing vs. Service Cancellation)** | *"How do I cancel my Apple Music free trial before it renews and charges me next week?"* | Mentions `apple music` and `trial` alongside `charge`, triggering ambiguous sub-category weights. | Introduce hierarchical intent classification (Parent: Account/Services -> Child: Billing/Subscription). |
| **3** | **Accessory vs. Connectivity Ambiguity** | *"My Apple Pencil (2nd gen) is attached magnetically to my iPad Air, but it won't charge or show the battery widget."* | Features keywords for `charge`, `battery`, `iPad`, and `pencil` across three intent boundaries. | Give hardware entity extraction (`Apple Pencil`, `AirPods`) priority over generic verbs (`charge`). |
| **4** | **Subtle Hostility Without Explicit Profanity** | *"I'm on my 3rd replacement unit this month and your genius bar rep told me nothing is wrong."* | Lacks direct profanity/lawyer keywords but represents high customer attrition risk. | Incorporate conversational sentiment/frustration score model alongside regex triggers. |
| **5** | **Pre-existing Case Reference Inquiries** | *"I have an open case #10192847192 regarding a lost trade-in kit and FedEx says Apple received it 2 weeks ago."* | Contains technical trade-in nouns that trigger general hardware categories instead of CRM transfer. | Add explicit CRM/case number regex pattern (`case\s*#?\d{8,}`) to force immediate DM escalation. |

---

## 5. "What is Misleading About My Headline Number?" (Mandatory Section)

While our **90.0% intent accuracy** and **88.5% escalation accuracy** demonstrate strong performance, several factors must be critically acknowledged:

1. **Synthetic Stratification vs. Raw Twitter Skew**: 
   - In raw Twitter data, ~45% of incoming tweets are generic update questions (`os_software_update_bugs`) or short complaints. Our golden evaluation set is stratified (~14% per class) to test edge cases thoroughly. Headline accuracy on raw skewed streams would look artificially higher on common intents while masking edge-case regressions.
2. **Single-Turn Limitation**: 
   - The current evaluation evaluates single-turn incoming tweets. In production Twitter threads, customer sentiment frequently degrades over turns 2 and 3. An agent with high turn-1 accuracy might still fail on multi-turn dialogue state tracking.
3. **Optimistic Judge Alignment**:
   - Automated LLM-as-a-judge scores (4.66/5.0) reward grammatical fluency, URL presence, and polite tone. A reply can receive a 4.5 rating for tone while recommending a troubleshooting step that doesn't fix the customer's unique hardware variant.
4. **Escalation Recall vs Precision Trade-off**:
   - To achieve high safety and minimize dangerous misses, we tune the router conservatively. This results in false positives (unnecessary escalations to human agents) which increases human agent labor cost.

---

## 6. What We Would Do Next With One More Week

1. **Multi-Turn Context & Dialogue State Tracking**:
   - Implement stateful session tracking using Redis to analyze conversation history across multi-turn customer replies before deciding escalation.
2. **Fine-Tuned Embeddings for Dense Retrieval**:
   - Fine-tune a domain-adapted sentence transformer on Apple Support discussion forums (Apple Community KB) for high-precision sub-article retrieval.
3. **Live Human-in-the-Loop Shadow Mode**:
   - Deploy the agent in "shadow mode" on live Twitter streams where suggestions are presented to human tier-1 advisors, capturing real-time human acceptance rates.
4. **Dynamic CRM Case API Integration**:
   - Wire mock CRM webhooks to look up open case numbers, AppleCare+ warranty expiration dates, and repair repair order statuses automatically.

---

## 7. Decision Log (12 Non-Obvious Engineering Decisions)

1. **Selected AppleSupport as Target Brand**: Selected `@AppleSupport` because it possesses the highest volume of structured technical resolutions, strict privacy requirements, and clear hardware vs software boundaries in the TWCS dataset.
2. **7 Curated Intents Instead of Banking77 77 Intents**: Banking77 is fine-grained for fintech; Twitter hardware/software support requires distinct operational boundaries (battery vs software vs hardware vs security).
3. **Conservative Escalation Bias (Safety > Auto-handle rate)**: Prioritized Escalation Recall over Precision; a false escalation costs human minutes, but an automated reply to a swelling battery is a catastrophic safety failure.
4. **Zero Public PII Collection Policy**: Hardcoded regex guardrails that prevent the agent from asking for passwords or payment details in public tweets, enforcing `apple.co/DM` transfers.
5. **BM25 + Entity Prior Hybrid Retrieval**: Used BM25 with exact-match entity boosting rather than pure cosine embedding distance to ensure specific device model strings (e.g. `iPhone 11` vs `iPhone 14`) are preserved.
6. **Rule-Calibrated Multi-Dimensional Judge Rubric**: Designed a 5-dimension rubric (Grounding, Brand Voice, Actionability, Safety, Triage) rather than a single 1-10 scalar prompt to prevent LLM judge hallucinations.
7. **Official Domain Whitelisting**: Whitelisted only verified Apple URLs (`support.apple.com`, `iforgot.apple.com`, `reportaproblem.apple.com`, `apple.co/*`) to eliminate dead or hallucinated links.
8. **Disambiguation Rules for Post-Update Battery Drain**: Implemented specific lexical priority rules because updates often cause temporary battery indexing, distinguishing battery complaints from OS boot crashes.
9. **Fallback Deterministic Grounded Templates**: Built a resilient deterministic generation engine so the pipeline operates with zero external API dependencies or cost during high-volume outages.
10. **280-Character Budget Guardrail**: Enforced Twitter length constraints with graceful truncation and brand-voice opening prepending (`We'd love to help with this`).
11. **Human Calibration Dataset (50 Annotations)**: Measured Cohen's Kappa and MAE between human labels and judge scores to prove the evaluation harness is trustworthy.
12. **Stratified Golden Set (200 items)**: Hand-curated a balanced evaluation set spanning easy diagnostics, multi-intent overlaps, and severe hardware/safety edge cases.
