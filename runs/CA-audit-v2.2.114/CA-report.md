# CODE_ASSASSIN — Independent Source Audit
**Rule:** `TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN_ENHANCEMENT_PROPERTY_TEST.iLogicVb`  
**Version:** `v2.2.114-P3-STAB`  
**Date:** 2026-11-19  
**Review type:** Source-code only. No Inventor runtime test. Independent of ChatGPT findings (C1–C8).  
**Source file SHA256:** `bf4846e3834ac24462c22986b7cec48505b9ac5f161d84327128d4e66d35f865`

---

## CA-1 — PASS1-FILTER destroys sub-assembly renames when Drawing List contains any entries `CRITICAL`
**Lines:** 1661–1684

`oPass1Keys` is seeded with `sTopFull` plus every model path from `oDwgModels` (the Drawing List). `oPass1Map` is then built by intersecting `oPass1Keys` with `oRenameMap`. If `oPass1Map.Count > 0`, `oRenameMap.Clear()` fires and the full rename map is replaced with `oPass1Map`.

**Root cause:** Drawing List form entries are keyed by user-entered display names (e.g. `PJ00204-3430-V0-10-10-10 (Transportation).iam`). `oRenameMap` is keyed by disk filenames (`PJ00204-343-V0-10-10-10.iam`). The two never match. Only `sTopFull` (the GA path, a disk path) survives into `oPass1Map`. `oPass1Map.Count = 1`, which is `> 0`, so `oRenameMap.Clear()` fires. Every sub-assembly rename is discarded. The fallback branch (line 1682) only triggers when `oPass1Map.Count = 0` — an effectively impossible condition when any Drawing List is loaded.

**This is the direct cause of "old subs aren't being swapped out."** Phase 4 receives a map containing only the top GA; no sub-assembly replacements are attempted.

**Fix:** Remove the `oRenameMap.Clear()` / replace pattern entirely. Use `oPass1Map` only to identify priority-ordering for Phase 2 SaveAs sequencing; never use it to discard mappings. Or: resolve Drawing List keys to disk paths before seeding `oPass1Keys`.

---

## CA-2 — `CloseAll(True)` closes user documents and defeats save-failure retry `CRITICAL`
**Lines:** 2559–2566

`ThisApplication.Documents.CloseAll(True)` is called every 20 Phase 3 opens. This is not scoped to documents opened by Phase 3. It will close:

- Any user document open in Inventor at run time
- Any document that failed to save and was intentionally left open for retry (the selective close only fires when `bSaved3 AndAlso bOpened3` — a save-failed document is left open and later swept by `CloseAll`)
- Documents from iterations 1–19 of the same Phase 3 loop that were kept open

The `True` parameter's semantics (`save before close` vs `force close`) require verification against the Inventor API docs before any fix.

**Fix:** Track all Phase 3-opened documents in a list and close only those, in reverse open order, using individual `doc.Close(True)`. Never call `CloseAll` from within a rule.

---

## CA-3 — `SkipAllUnresolvedFiles=True` silently hides incomplete reference repair `HIGH`
**Lines:** 2328–2341

Phase 3 opens assemblies with `SkipAllUnresolvedFiles = True`. An assembly with unresolved children opens successfully. `ReferencedFileDescriptors` enumeration only returns descriptors for resolved references — the skipped ones are not enumerable. `ReplaceReference` is never called on them. The assembly is saved with those references still pointing at old paths. Phase 3 logs `P3-OPEN:` as normal.

**Fix:** Log the document's unresolved ref count before and after open. Treat any non-zero unresolved count as a soft failure that blocks drawing relink for that assembly. For assemblies the rule itself created (Phase 2 succeeded), consider using plain `Documents.Open` — they should resolve cleanly.

---

## CA-4 — No Phase 3 failure gate before Drawing Relink `HIGH`
**Lines:** 2573–2574 (Phase 3 complete log), 3011 (Drawing Relink entry)

`iRefFailed` is tracked across Phase 3 (incremented on save failures). The Drawing Relink block at line 3011 is gated only by `bFromDwg AndAlso sDwgEntryPath <> "" AndAlso Not bPropertyOnly`. `iRefFailed` is never checked. If Phase 3 failed to repair internal references on any assembly, Drawing Relink proceeds unconditionally, relinking official drawings to assemblies whose internal references are still broken.

**Fix:** Add `AndAlso iRefFailed = 0` to the Drawing Relink gate, or at minimum log a prominent warning and prompt the user before relinking when `iRefFailed > 0`.

---

## CA-5 — P3-DOC-FAIL swallows document-level errors with no downstream block `HIGH`
**Lines:** 2568–2570

The outer `Try...Catch exDoc3` at line 2311 catches any per-document Phase 3 failure, logs `P3-DOC-FAIL`, and continues. `iRefFailed` is not incremented in this catch — only when a `ReplaceReference` succeeds but `Save2` fails (a different path). A complete open failure, a descriptor enumeration failure, or any unhandled inner exception increments nothing and blocks nothing. Drawing Relink proceeds as if Phase 3 succeeded.

**Fix:** Increment `iRefFailed` in the outer `Catch exDoc3` block, and apply the gate from CA-4.

---

## CA-6 — PROV-SKIP files silently dropped from Phase 3 by `oCreatedThisRun` gate `MEDIUM`
**Lines:** 2292–2299, 2317–2320

`oP3Targets` is built from `oActualMap.Values` (files created this run) PLUS `oTargetByBase.Values` (all `.iam` already on disk in the target folder). The second set includes PROV-SKIP files from prior runs. At line 2317, any file not in `oCreatedThisRun` is skipped with a `P3-SKIP-NOT-CREATED` log entry.

This means old-reference assemblies in the target folder from a previous partial run are silently skipped by Phase 3 and never repaired. Phase 4 is the only remaining repair path, but Phase 4 uses `Occurrence.Replace` on the active GA — it cannot repair internal references inside closed assemblies it doesn't open.

**Fix:** Either remove PROV-SKIP files from `oP3Targets` (they shouldn't be there if they won't be processed), or extend `oCreatedThisRun` to include any file in the target folder that still has old references detectable via `oActualMap`.

---

## CA-7 — Sort by path string length fails with subfolders `MEDIUM`
**Line:** 2299

`oP3Targets.Sort(Function(a2, b2) b2.Length.CompareTo(a2.Length))` sorts by descending path length. For a flat target folder, path length correlates roughly with assembly depth. This breaks when the target folder has subdirectories: a shallow assembly in a deep subfolder can have a longer full path than a deep assembly in the flat root, reversing the repair order.

**Fix:** Sort by graph depth from `AllOccurrences` traversal of the copied GA, or use reverse BFS order from the existing WalkTree result.

---

## CA-8 — `ComputeNewName` double-prefix collapse can produce a path collision `LOW`
**Lines:** 3827–3842

For a file `PJ00204-PJ00190-3430-V0.iam` already in the target folder, the collapse logic builds a collapsed target path. No collision check is performed before `Return sCollapsedFull`. The caller receives a path that maps to an existing, potentially correct, file — which could then be overwritten by Phase 2 SaveAs.

**Fix:** Add `System.IO.File.Exists(sCollapsedFull)` check and return `""` (skip) if the target already exists and is not the same file.

---

## CA-9 — Vault read-only parent blocks Phase 4 `Occurrence.Replace` with no escalation `HIGH`
*(Confirmed in 17/11 run log — not independently line-verified in this version; requires Vault environment test)*

`ComponentOccurrence.Replace` returns `E_FAIL (0x80004005)` when the parent assembly is Vault-checked-in and read-only on disk. Phase 4 logs `P4-REPLACE-FAIL` and continues. All 10 P4-REPLACE-FAIL entries in the 17/11 run shared two Vault-locked parent assemblies.

**Fix:** Pre-Phase-4 Vault checkout gate: list all assemblies whose target files would be opened for `Replace`, check each for read-only attribute, and abort with a named list before entering Phase 4.

---

## CA-10 — SaveAs fallback `File.Copy` produces corrupt XML skeleton on partial write `HIGH`
*(Confirmed in 17/11 run log)*

When `SaveAs` fails, the code falls back to `File.Copy`. If the source file is Vault-locked or the destination write is interrupted, `File.Copy` can produce a zero-byte or partial XML file. Inventor `.iam`/`.ipt` files are XML-based; a partial write passes `File.Exists` but throws "XML document must have a top level element" on open. Phase 3 and Phase 4 then fail on that file with an opaque error.

**Fix:** After `File.Copy`, attempt `Documents.Open` as a validation step; if it fails, delete the corrupt destination and log a named failure.

---

## Comparison with ChatGPT findings (C1–C8)

| ChatGPT ID | CA ID | Status | Notes |
|---|---|---|---|
| C1 | CA-1 | **Confirmed — root cause identified** | Specific trigger: DWG display-name vs disk-filename mismatch in `oPass1Keys`; not just a generic filter issue |
| C2 | CA-4 | **Confirmed** | No `iRefFailed` gate before relink — corroborated |
| C3 | CA-2 | **Confirmed** | Control-flow contradiction with save-failure retry is real |
| C4 | CA-5 | **Confirmed + extended** | Outer catch also fails to increment `iRefFailed` |
| C5 | CA-3 | **Confirmed — severity should be CRITICAL** | Unresolved refs are actively hidden, not just missed |
| C6 | — | **Confirmed safe** | Standard COM-enumeration pattern; low risk |
| C7 | CA-8 | **Confirmed** | Subfolder collision case adds to ChatGPT's finding |
| C8 | CA-7 | **Confirmed** | Subfolder case not covered by ChatGPT |
| — | CA-6 | **New** | PROV-SKIP files silently dropped from Phase 3 |
| — | CA-9 | **New** | Vault read-only parent blocks Phase 4 (from 17/11 log) |
| — | CA-10 | **New** | SaveAs fallback → XML corruption (from 17/11 log) |

---

## Priority order for fixes

1. **CA-1** — map filter nukes all sub-assembly renames; this alone explains the core symptom
2. **CA-2** — `CloseAll` potential data loss on any run with 20+ Phase 3 files
3. **CA-4 + CA-5** — no Phase 3 failure gate before drawing relink; prevents drawing corruption
4. **CA-3** — hidden reference gaps from `SkipAllUnresolvedFiles`
5. **CA-9** — Vault lock pre-flight check (requires Vault environment)
6. **CA-10** — post-SaveAs XML validation
7. **CA-6, CA-7, CA-8** — medium/low; schedule after criticals
