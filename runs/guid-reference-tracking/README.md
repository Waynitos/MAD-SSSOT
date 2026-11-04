# MAD Run — GUID-Based Reference Tracking for Clean Sweeper

**Topic:** Use Inventor's internal file GUIDs (Document.InternalName) as the primary reference-tracking mechanism in the Clean Sweeper Suite, supplementing or replacing path/name-based matching.

**Date:** 2026-11-04
**Project:** INVENTOR - CLEAN SWEEPER SUITE

## Files

| File | Contents |
|---|---|
| `AA-output.md` | Strongest case FOR GUID-based tracking |
| `DA-output.md` | Strongest case AGAINST GUID-based tracking |
| `SSA-output.md` | Synthesis verdict |

## SSA One-Line Verdict

> **Store CS_SourceGUID on new files (zero cost, future-proofing). Use CS_SourcePath for current matching (already works). Replace File.Copy with SaveAs unconditionally (correctness fix, fresh GUID, architecturally correct). Do not implement GUID-based occurrence matching in iLogic (no practical gain over path matching in local context).**

## Key Finding

The most important outcome of this MAD is NOT about GUIDs for matching — it is that **File.Copy must be replaced with SaveAs**. File.Copy preserves the original file's GUID, creating a silent identity collision between source and copy that is architecturally wrong and will cause problems if both files ever enter the same Vault workspace or project scope. SaveAs generates a fresh GUID — this is what Vault Copy Design does and what the Clean Sweeper must do for correctness.
