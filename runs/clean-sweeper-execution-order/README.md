# MAD Run — Clean Sweeper Execution Order

**Date:** 2026-11-04  
**Trigger:** RMAD  
**Question:** What is the correct execution order for TRAVERSE_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN — GA-first, drawing-first, or phased?

## Context

The Clean Sweeper rule was observed to leave the GA assembly tree with old PJ00161 sub-assembly names after a run. Root cause: the rule scans drawings to discover models, copies files, updates drawing references — but never correctly relinks the GA's internal sub-assembly references. The Traverse Rename rule that was supposed to fix this ran on the wrong file and then crashed on a double-extension `.iam.iam` file.

## Outputs

- [AA-output.md](AA-output.md) — Case FOR strict GA-authority / GA-first
- [DA-output.md](DA-output.md) — Case FOR phased hybrid (copy-atomic → relink depth-last → drawing-validate)
- [SSA-output.md](SSA-output.md) — Synthesis verdict and mandated four-phase sequence

## SSA One-Line Verdict

> **Copy first (atomic), relink assembly tree depth-last (leaves→GA), validate and update drawings last — the GA rename map is the single source of truth; any drawing ref outside it is an ORPHAN error.**

## Mandated Implementation Change

`RunDrawingCopyMode` must be refactored into four separated phases:
1. `ScanPhase()` — GA walk + drawing scan → rename map
2. `CopyPhase()` — all files, atomic, no Inventor docs open
3. `RelinkAssemblyPhase()` — depth-last (`.ipt`/`.iam` leaves first, GA last)
4. `RelinkDrawingPhase()` — drawings last, ORPHAN-ERROR for refs outside map
