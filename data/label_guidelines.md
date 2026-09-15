# Golden Evaluation Set Annotation Guidelines

## Overview
The Golden Evaluation Set contains **200 hand-curated and stratified customer support interactions** from Twitter for `@AppleSupport`.
It serves as the gold standard benchmark for evaluating intent classification, escalation routing, and grounded response generation.

## Sampling Methodology
1. **Source**: Drawn from the authentic Kaggle Twitter Customer Support dataset (`thoughtvector/customer-support-on-twitter`).
2. **Stratification**: 
   - 7 balanced intent categories (~28-30 examples per intent).
   - Balanced triage split: ~60% Auto-handled (`escalate=False`), ~40% Escalated (`escalate=True`).
   - Difficulty distribution: ~45% Easy, ~40% Medium, ~15% Hard edge cases.
3. **Filtering Criteria**:
   - Filtered out conversational fragments, pure spam, and non-English tweets.
   - Preserved authentic Twitter noise (emojis, slang, hashtags, caps, typos, mentions).

## Intent Taxonomy & Boundary Rules
| Intent ID | Definition | Typical Keywords | Key Boundary Distinctions |
|---|---|---|---|
| `battery_hardware_performance` | Battery drain, health %, overheating, slow charging, thermal limits | battery, drain, hot, charging, slow, freeze | Software battery drain vs OS update bug: if battery drain is the primary complaint, tag here. |
| `os_software_update_bugs` | iOS/macOS update installation errors, boot loops, system crashes | update, iOS, install, verifying, reboot, crash | General update failure vs specific hardware failure. |
| `icloud_appleid_security` | Apple ID lockout, password reset, 2FA, iCloud sync, Activation Lock | apple id, icloud, password, locked, 2fa, stolen | Account access issues vs billing charges. |
| `billing_subscriptions_purchases` | App Store charges, subscription cancel, refunds, payment decline | refund, subscription, charge, receipt, app store | Financial transactions vs account credential login. |
| `connectivity_network_bluetooth` | Wi-Fi drop, Bluetooth pairing, cellular 'No Service', AirDrop | wifi, bluetooth, cellular, no service, pair, airdrop | Wireless/radio network issues vs accessory audio defects. |
| `audio_display_accessories` | AirPods mic/static, broken screen, Apple Pencil, camera black screen | screen, airpods, speaker, sound, pencil, display | Physical accessory/audio/display issues vs wireless pairing. |
| `human_escalation_dm_transfer` | Explicit human demand, extreme hostility, legal threats, repeat failures | human, agent, manager, legal, sued, terrible, repeat | Sentiment hostility/explicit human agent request overrides technical intent. |

## Escalation Policy Guidelines
- **Auto-Handle (`escalate=False`)**:
  - Issue has an established self-service troubleshooting path (e.g., Reset Network Settings, iforgot.apple.com, reportaproblem.apple.com, force restart).
  - No physical hardware hazard, no compromised credentials, no disputed financial loss.
- **Escalate to Human (`escalate=True`)**:
  - **Safety Hazard**: Battery swelling, thermal burn risk, smoke.
  - **Security Breach**: Account takeover, changed 2FA credentials, stolen identity.
  - **Financial Dispute**: Multi-month unauthorized charges, disputed chargebacks.
  - **Customer Distress**: Severe frustration, repeat failed interactions, legal threats, explicit demand for live agent.
  - **Hardware Failure**: Cracked glass, broken modem baseband, failed hardware diagnostics requiring service reservation.
