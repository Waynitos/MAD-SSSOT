# Failure Mode: Single-Model Anchoring in Sequential Role-Play

**Discovered:** 2026-10-23
**Run:** First MAD self-evaluation run (Claude, MAD PROJECT session)

## Description
When a single AI model performs the AA → DA → SSA cycle sequentially within
one context window, the DA cannot genuinely surprise itself. Having seen its
own AA output, the model is anchored — it knows the direction it argued and
must consciously override that framing to critique it. This is not true
independent multi-agent debate as described in Du et al. (ICML 2024).

## Why it matters
The primary claimed benefit of MAD — that independent agents surface gaps
the other missed — is partially compromised in single-model sequential runs.
The DA may be too polite or miss anchored assumptions entirely.

## Mitigations
- Run AA in a fresh chat session, copy output, run DA in a separate fresh
  session with zero prior context. More manual effort; significantly more
  adversarial.
- Use genuinely different models for AA and DA (e.g. Claude for AA, GPT-4o
  for DA) to reduce shared training bias.
- Explicitly instruct DA: "You have not seen how this answer was constructed.
  Approach it as a sceptic with no prior context."
- Note this limitation explicitly in any SSA output for high-stakes topics.

## Status
Open — no full mitigation yet implemented in the protocol.
