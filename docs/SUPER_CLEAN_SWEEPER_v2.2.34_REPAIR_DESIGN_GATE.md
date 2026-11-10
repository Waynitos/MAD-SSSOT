# SUPER CLEAN SWEEPER v2.2.34 — Existing Target Repair: engineering gate

Status: **DESIGN / NOT READY FOR INVENTOR TESTING** (2026-11-10). Parent baseline: diagnostic/sweeper-v2.2.33-profiler. Production main remains untouched.

## Verified source observations
- Mode dialog currently offers Full sweep and Relink only; no existing-target repair selection (around lines 493–536).
- String replacements are gathered before Phase 1 (around lines 625–734) and applied to mapped destination names, not existing target files.
- Phase 1 can yield zero files on an already-copied GA; provenance recovery (around lines 1483–1538) only enumerates top-level target-folder .iam/.ipt files and reconstructs a reference map, not rename operations.
- A rename-only operation cannot be safely implemented as System.IO.File.Move: it would break Inventor assembly/drawing references and can affect Frame Generator skeletons and frame members.
- v2.2.33 profiling checkpoints are present and should be retained.

## Required acceptance gates before executable release
1. **Explicit mode**: Existing Target Repair must be separate from Full Sweep and Relink. Source GA must be inside selected target root. No implicit prefix SaveAs or fallback copy.
2. **Discovery**: recursively traverse target GA references, including nested .iam/.ipt, Frame Generator members and skeletons; include drawings only with explicit discovery and handling. Report unresolved references and out-of-root dependencies. Never silently rename outside target.
3. **Preview**: apply up to five case-insensitive string replacements to basename only (not directories/extensions); show full old/new paths, per-file counts, no-ops, unresolved/blocked entries and collision groups. Allow cancel before mutation.
4. **Safety**: abort mutation on any collision, read-only file, missing target, destination already exists, duplicate destination, external reference, unresolved reference, or Vault-controlled/checked-out ownership uncertainty. Do not deactivate Vault add-in. Require controlled local test copies.
5. **Inventor-aware update**: use Inventor-supported rename/reference-replacement lifecycle (not bare filesystem rename). Establish dependency order, document ownership, and saved state. Update *every* affected assembly and drawing reference, including Frame Generator skeleton references. Do not change source files. Log exact before/after reference paths.
6. **Verification**: reopen copied top GA from disk after closing only documents opened by the rule; walk all descendants and compare to approved map; validate drawings and Frame Generator relationships. Treat any mismatch as failed release; preserve backups and report manual recovery.
7. **Profiling**: record discovery, preview, mutation, reference repair, verification and per-file slow operations; keep raw-copy risk register.
8. **Testing**: compile in target Inventor iLogic version, then dry-run on an isolated GA containing double-dash filenames, nested frame skeletons, drawings, collisions, read-only and unresolved references. Compare baseline 10–15 minute Copy Design workflow separately; repair mode is not the same benchmark.

## Non-goals
- No bulk Explorer rename.
- No Vault add-in suppression.
- No 416-document keep-open workaround.
- No production deployment before Inventor-side tests.

## Next implementation
Build a *preview-only* first gate (no mutation), then a separate mutation/verification stage after Inventor API semantics and Frame Generator constraints are reviewed. A partial preview must not be represented as a complete v2.2.34 candidate.
