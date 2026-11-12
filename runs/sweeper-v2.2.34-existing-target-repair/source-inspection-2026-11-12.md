# v2.2.34 Existing Target Repair — source inspection checkpoint (2026-11-12)

**Status: INVESTIGATING / BLOCKED for release**. This is not a complete candidate and is not Inventor-tested.

## Inspected baseline
- `diagnostic/sweeper-v2.2.33-profiler`, `scripts/ilogic/TRAVERSE_CLEAN_SUPER_CLEAN_SWEEPER_NEW_DWG_COPY_DESIGN.iLogicVb`, blob `a45cc8d0bbc5ff47792f565d02aca6076e651f2b` (221,256 characters).
- Feature branch source currently resolves to the same blob. Do not assume prior candidate code is present.
- Existing v2.2.32 source comments claim safe non-overwriting fallback, but safety and reference-integrity need independent validation.

## Source-level findings
1. **High-risk: P4 save helper clears filesystem ReadOnly attributes.** Immediately before `oDoc.Save2(False)`, the helper calls `System.IO.File.SetAttributes(sThisFull, oFA And Not System.IO.FileAttributes.ReadOnly)`. This contradicts the requirement never to bypass Vault checkout or modify protected file attributes. Existing Target Repair must *not* reuse this path without a fail-closed preflight and removal of the attribute mutation.
2. **High-risk: SaveAs failure falls back to `System.IO.File.Copy(sOldFull2, sNewFull2, False)`.** Raw copy does not perform Inventor reference rewrites and must never count as validated target repair. Destination-exists checks protect against overwrite but are insufficient for document identity, reference integrity, and Vault safety.
3. **Existing-target provenance guard:** source comments say `ResolveTarget` reuses a file only when `CS_SourcePath` matches and otherwise suffixes it; Phase 3 skips files not created this run. A repair mode must introduce a separate explicit, previewed, authorised transaction instead of weakening these guards.
4. **Frame Generator:** local frame logs previously showed replacements succeeded but `P4-SAVE-FAIL` and `P4-GA-SAVE-FAIL` returned `0x80004005`. Successful occurrence replacement alone is not proof of persisted reference integrity.
5. **Profiler:** search for `Stopwatch` in the inspected source returned no match; locate actual profiler implementation and confirm preservation before claiming profiler retention.

## Required next implementation gate
- Fetch full target-resolution, phase-2/3/4, provenance and profiling regions, plus project launch and shared architecture.
- Design explicit preview/commit modes with a deterministic plan and per-file provenance/reference validation.
- No mutation on collisions, checked-in/read-only/unverified Vault state, dirty production documents, missing skeleton/member references or ambiguous targets.
- Journal every attempted mutation and backup only user-authorised disposable test targets. Fail closed on partial save and re-open/re-read to verify all intended references.
- Frame processing must be independently testable and deferred after standard subassemblies as proposed in PWTP.
- Add source-level test fixtures/checks for preview, collision, readonly, rollback and profiling; run checks and record their exact outputs.
- No release notification until complete candidate is committed and statically tested; Inventor testing remains required.

No production/main or Inventor files changed.
