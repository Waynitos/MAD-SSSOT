# AA Output — TRAVERSE iLogic Audit

**Role:** Advocate (strongest case for current implementation)  
**MAD Run:** traverse-ilogic-audit  
**File audited:** TRAVERSE_fixed.iLogicVb (8052 lines)

---

## 1. Architecture

### Bottom-up traversal is categorically correct

Processing children before parents is the only safe order for an assembly rename operation. If a part inside a sub-assembly gets renamed, the sub-assembly's internal references must already point at the new file before the sub-assembly itself is saved. Bottom-up guarantees this invariant. Top-down would require a second pass to fix broken parent refs — or produce permanently broken assemblies.

### Mode 2's multi-phase engine solves the core problem definitively

The old approach (copy file → repoint parent → delete old) had a fundamental flaw: it never rewrote internal references *inside* newly-copied assemblies. A copied sub-assembly's internal FileDescriptors still pointed at the old file names of its children. The result was that sibling assemblies sharing a child had broken references after the first parent was repointed, forcing repeated re-runs to "catch misses."

The 5-phase Vault Copy Design approach solves this correctly:

- **Phase 1** (map building, no disk writes): Complete old→new map established before anything is touched
- **Phase 2** (copy all files, olds kept): All new copies exist on disk before any references are rewritten
- **Phase 3** (fix internal FDs in new assemblies): Each new assembly's FileDescriptors are rewritten to point at the other new files in the map — this is the step the old approach skipped
- **Phase 4** (repoint live session occurrences): Live Inventor session brought in sync with the new file set
- **Phase 5** (save everything; olds remain): Safe exit state — originals never deleted during the run

This is the same strategy Autodesk Vault's Copy Design uses, for the same reason. Reaching it independently and encoding it in an iLogic rule is the right architectural call.

Phase 3 further applies a dual-strategy fix for each new assembly: first `FileDescriptor.ReplaceReference()` (lightweight, no force-load of target), then falls back to `Occurrence.Replace()` for adaptive/pattern/DA-managed assemblies where FD alone is insufficient. The fallback is correctly scoped only to assembly documents (`kAssemblyDocumentObject` check) where occurrences exist. This two-tier approach is more resilient than either method alone.

Phase 4 builds an O(1) filename fallback map (`oNameToNew`) that allows matching by filename alone when the full path in the live session differs from the path used to build the Phase 1 map — a real scenario when the active session has an assembly open from a slightly different resolved path. Entries where old filename == new filename are explicitly excluded from this map to avoid useless ReplaceReference calls on no-op entries. This is careful, targeted engineering.

The explicit `Do NOT call oNewDoc.Update()` comment in Phase 3 (lines 1052–1058) shows deep Inventor API knowledge: calling Update() during Phase 3 asks Inventor to rebuild the assembly graph while sibling files still have old names on disk, producing unresolved references that corrupt the subsequent Save2. The comment explains exactly why Save2 alone is the correct call here.

### Mode separation reflects genuinely different operations

The distinction between Mode 1 (prefix swap, starts-with) and Mode 2 (segment replace, contains-anywhere) is not cosmetic. Conflating them into a single "starts with" rule is documented in the header as the cause of a real runaway-naming incident. The separation forces the user to be explicit about which operation they intend, which is the correct UX choice for a destructive file operation.

Mode 3 (consolidate without rename), Mode 4 (batch scan), Mode 5 (verify-only), and Mode 6 (composite) each address a real, distinct workflow need. None are redundant; all have documented production use cases.

### Mode 6 as the composition layer

Mode 6's key architectural insight is that it builds one comprehensive rename map covering prefix swap + segment replacements + non-std localization, then injects it via `GetSetPrebuiltMode2Map()` into the Mode 2 multi-phase engine. This reuses the most correct and complete implementation (Mode 2's engine) without duplicating it. Mode 6 skips Phase 1 (map already built) and proceeds directly to Phase 2 — a clean separation of map construction from map execution.

### AllReferencedDocuments + ReferencedFileDescriptors double scan

Phase 1 scans both `AllReferencedDocuments` (the live session's occurrence tree) and every document's `File.ReferencedFileDescriptors` (which catches derived sources, xlsx parameter tables, and fasteners that are referenced by file but not placed as component occurrences). This double coverage is why Mode 6 catches cases that individual modes miss — the map is comprehensive before any disk operation begins.

### Pre-Phase 4 memory flush

Between Phase 3 and Phase 4, the script performs a targeted flush: it closes every document NOT in the initial session snapshot (and not the top assembly, and not dirty). This directly prevents the Inventor RAM growth problem (documented 800MB → 3.5GB on large assemblies) from reaching a critical state before Phase 4 begins walking all open assemblies. Critically, dirty documents are exempted from the flush — they represent in-progress Phase 3 work that must not be discarded.

### Safety guard on Phase 4 mutations

Phase 4 calls `IsDocSafeToMutate(sWalkPath, sTargetFolder, sTopAssemblyFullName)` before repointing any assembly. This belt-and-braces check ensures that source/original assemblies open in the live session (which Phase 4 did not open, but which may be in the session because they were open when the rule started) are never marked dirty or repointed. The check is applied twice: once before any FD/occurrence work, and again in the save loop after Phase 4 — two independent guards so no future code path can accidentally save a source assembly.

---

## 2. Safety Mechanisms

### Fix 2: Current-path cycle guard (not global visited set)

This is the most architecturally significant safety decision in the script. A global visited set would incorrectly skip a shared component on its second encounter from a different branch — but that second encounter is not a cycle, it's a legitimate reuse. The shared component's subtree may contain things that need renaming, and skipping it would silently miss them.

The current-path guard correctly distinguishes: a document is only flagged as a cycle if it appears on the *active path from root to current node* — i.e., it is its own ancestor. The marker is removed when backing out of a branch (`oVisitedLevels.Remove()`), so the same document can be freely re-entered from a sibling branch. This is the correct behaviour.

### Fix 6: Self-match guard

The runaway-naming incident (PJ00195-3610-3610-3610...) is documented as a real production event. The guard correctly catches the two forms: REPLACE starts with FIND (Mode 1) and REPLACE contains FIND (Mode 2). The exemption for identical Find/Replace (the localize-without-rename case) is explicitly reasoned: since the name never changes, there is nothing to compound on a re-run.

### Fix 4: Exclusion list

Content Centre files being renamed is not a theoretical risk — the header notes it happened. The exclusion list is comprehensive: Vault Library path, Content Centre Files\en-US folder, a company-specific standard folder, the `IsContentCenter` membership flag (catches CC parts regardless of where their file physically lives), and the Non Std Parts sibling folder. The last exemption is scoped correctly: only the Non Std Parts folder *directly under the current assembly* is excluded; a same-named folder in another project is deliberately NOT exempt.

### Fix 3: Top-assembly self-reference check

Every renamed file lands in the top assembly's folder, so a sub's computed new name can coincidentally match the top assembly's own filename. Without this check, the occurrence would be repointed to its own ancestor — a silent circular reference that Inventor would not immediately reject. The check explicitly refuses this case with a log entry.

### Fix 9: Read-only handling

The upfront check before any work begins is the critical one — it prevents the "ran the entire traversal, then failed to save at the end" failure mode. The per-file check before in-place saves adds a second layer: a checked-in intermediate sub-assembly is skipped with a log entry rather than triggering Inventor's native error dialog (which Try/Catch cannot suppress).

---

## 3. Operational Robustness

### Dual logging — timing log + decisions log

The timing log (written during the run to Desktop) solves the problem of "Inventor crashed and I don't know where it stopped." The decisions log (`_Decisions.txt`) solves the complementary problem: "the run finished but I don't know why X wasn't renamed." Together they cover both failure modes. Both are written incrementally during the run, not at the end — so they're available even on a mid-run crash.

### Phase 4b verification scan

After Phase 4 completes, the script runs a verification pass (`Phase 4b`) that walks all open assembly documents looking for any remaining references to old-segment filenames. This converts an invisible failure (Phase 4 missed an occurrence) into a visible, logged discrepancy. The user sees "X remaining old refs" rather than discovering broken assemblies later. This is the iLogic equivalent of a post-migration assertion.

### Pre-scan (Mode 3)

The Mode 3 pre-scan is a read-only walk that produces a full tree report before any disk writes. It shows every distinct file, why it will or won't be consolidated, and a summary count of each category. This is the correct way to handle a destructive consolidation operation — show the user exactly what will happen, get implicit confirmation (click OK to proceed), then execute.

### Memory management

The `SnapshotInitiallyOpenDocuments()` / `OpenDocTracked()` / `CloseIfOpenedHere()` trio directly addresses the documented failure mode of Inventor going from 800MB to 3.5GB RAM during a run. Documents opened during the rule are tracked and closed when no longer needed, rather than accumulating in the session for the duration of the run. `PeriodicGcTick()` calls `GC.Collect()` + `GC.WaitForPendingFinalizers()` at regular intervals through all phases to prevent COM object handle accumulation in Inventor's process space.

### Original state snapshot

Written once per assembly (never overwritten by subsequent runs), this preserves the TRUE starting file layout — even after multiple partial or sequential runs have changed some files. Since `SaveAs(newName, True)` never deletes the original, the files recorded in the snapshot still exist on disk and can be used for manual recovery.

### Excel alerts suppression

Inventor's parameter tables can be xlsx-linked. If Excel is open and alerts are enabled, a SaveAs or reference update can trigger a dialog that blocks the rule indefinitely. Suppressing DisplayAlerts during the run (and restoring on exit) prevents this without affecting the user's regular Excel session.

---

## 4. Mode 6 as the Gold Path

The user's own observation confirms this: "it didn't have any major issues if all modes ran as a batch in mode 6." This is architecturally expected.

When individual modes are run in sequence (e.g. Mode 1, then Mode 2, then Mode 3), each run starts fresh. The performance cache (`oProcessedResults`) is populated during the run but doesn't persist across runs. The assembly's live session state reflects the most recently saved state, but the performance cache of a prior run is gone.

The issue the user notes ("cached versions of historic subs missed the renaming of define pass runs") is most likely the case where Mode 2's Phase 1 map scan uses `AllReferencedDocuments`, which reflects the live session's *current* resolved document set — not the on-disk state if some files have been renamed in a prior pass but the assembly hasn't been fully reloaded. Mode 6's single-run approach avoids this because the entire map is built at the start of a fresh session before any renames have occurred, then executed in one continuous operation.

Mode 6 is the correct default for production use. The individual modes are correctly retained as tools for specific single-operation needs.

---

## 5. Honestly Acknowledged Weaknesses

### GoTo control flow

The script uses `GoTo AfterSingleTraversal`, `GoTo SkipBatchMode`, and `GoTo Mode2Phase2` to jump between logical sections of `Main()`. These are functional but make the control flow non-obvious. A reader following Mode 6's path must track: ShowRenameModeForm → ShowCopyDesignConfigForm → BuildCopyDesignRenameMap → GetSetPrebuiltMode2Map → GoTo SkipBatchMode → bUseContainsMode = True → [falls into Mode 2 block] → GoTo Mode2Phase2. Refactoring to subroutines would improve maintainability.

### Phase 3 depth ordering heuristic

Phase 3 sorts new assembly targets by path length (descending) as a proxy for "deepest-first" order. Path length and tree depth are not the same: a deeply nested component with a short path name would be processed before a shallow component with a long path name. In practice this is unlikely to cause problems (Phase 4's live repointing corrects the session state regardless), but it's an approximation, not a guarantee.

### Single-file architecture

8052 lines in one file with all mode logic in `Main()` makes the script difficult to navigate and test in isolation. iLogic's VB.NET environment doesn't support `#Include` or module imports within a rule, which limits what's possible here — but the structure is as good as the environment allows.

### "Define pass" cache issue in individual modes

The user's noted behaviour — "sometimes due to the cached versions of historic subs it missed the renaming of define pass runs" — is a real edge case when individual modes are chained in a multi-run workflow. Mode 6 avoids it, but the root cause (`AllReferencedDocuments` reflecting session state, not on-disk state) is not explicitly documented or guarded against in the individual modes.

### No dry-run for Modes 1, 2, 4

Mode 3 has a pre-scan (read-only walk + summary before execution). Modes 1, 2, and 4 do not — they proceed directly to disk operations after the form confirmation. Given that Mode 2's Phase 1 now builds a complete map before any copies, displaying that map (with a confirm/cancel step) before Phase 2 begins would give the same pre-scan value that Mode 3 already provides.

---

*AA output — TRAVERSE iLogic audit MAD cycle*
