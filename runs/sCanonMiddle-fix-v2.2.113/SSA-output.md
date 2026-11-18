# SSA-output.md — Synthesiser Verdict
## MAD Cycle: `DetectStringAnomalies` sCanonMiddle Fix (v2.2.113-FIRST-TOK)
**Date:** 2026-11-19  
**Rule version under review:** v2.2.113-FIRST-TOK  
**Function:** `DetectStringAnomalies` — `sCanonMiddle` extraction guard

---

## Synthesis

The AA established that the fix is mechanically correct for the confirmed real-world case (`PJ00204-PJ00190-3430-V0.iam`) and that the `.Contains("-PJ")` trigger is correctly scoped — it cannot misfire on a standard clean GA. The two-layer defence (guard + FIRST-TOK comparison) limits blast radius even if a corrupted canon slips through.

The DA established two non-trivial residual risks:

1. **Silent suppression on non-4-digit equipment numbers.** If the double-prefix GA has a 3- or 5-digit equipment number, the regex `-(\d{4})-` finds no match, `sCanonMiddle = ""`, and the suggestion engine emits nothing. The user sees a blank STRING-SUGGEST form, approves it, and the entire rename objective fails invisibly. This is strictly worse than the original bug (which produced a visible wrong suggestion the user could reject).

2. **Structural fix deferred.** `sDwgEntryPath` is already available in the function and already used for equipment-number extraction (lines 3499–3505). Deriving `sCanonMiddle` from the drawing filename — which is user-entered and structurally correct — would eliminate the double-prefix class of problem entirely without any digit-count assumption. The current fix is a targeted patch; the drawing-file derivation is the architecturally clean solution.

---

## Verdict

**Ship v2.2.113 with the current fix, subject to one mandatory addition before next live run:**

> **Add a log entry (and optionally a brief MsgBox) when the regex guard fires but finds no 4-digit token (i.e. when `sCanonMiddle` is set to `""` via the fallback path).** Something like:  
> `Logger.Log("WARN-CANON-MIDDLE: sCanonMiddle could not be recovered from GA double-prefix — STRING-SUGGEST suppressed. Check GA filename: " & sGABase)`  
> This converts the DA's silent-suppression failure into a detectable, diagnosable event.

**Follow-on TODO (log in CLEAN_SWEEPER_ROADMAP.md):**
- Migrate `sCanonMiddle` derivation to use `sDwgEntryPath` as the primary canon source (falls back to GA only if drawing path is empty), eliminating digit-count brittleness and non-PJ embedded-token edge cases entirely.

---

## Action Summary

| Item | Action | Priority |
|---|---|---|
| Regex guard (lines 3376–3384) | Retain as-is | — |
| FIRST-TOK comparison (lines 3436–3444) | Retain as-is | — |
| Silent suppression on `""` fallback | Add warning log | **Before next run** |
| `sDwgEntryPath` as canon source | Roadmap TODO | Next version |
