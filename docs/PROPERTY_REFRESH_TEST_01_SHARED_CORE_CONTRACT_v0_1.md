# BEEXCITED Property Refresh 01 — Shared Core Contract v0.1 (design gate)

**Status:** SPECIFICATION ONLY. Not compiled, not Inventor-tested, not approved for APPLY.
**Branch:** feature/sweeper-v2.2.34-existing-target-repair.
**Scope:** One reusable property-refresh engine called by the standalone iLogic harness and later by Clean Sweeper / SQL editor; never copy/paste a second implementation.

## Canonical entry contract

`ExecutePropertyRefresh(request As RefreshRequest, adapter As IInventorPropertyAdapter, logger As IRefreshLogger) As RefreshReport`

`RefreshRequest` contains: mode (Preview or Apply), entryKind (AssemblyGA or DrawingGA), activeDocumentPath, newProjectPrefix, explicitProjectRoot, approvedWritableRoots, protectedExternalLibraryRoots, optional trusted Vault checkout manifest and current-user identity, approvedPropertyMapping, executionId, engineVersion.

Reject an invalid prefix unless it matches exactly `^PJ[0-9]{5}$`; normalize to uppercase before planning. Reject missing or ambiguous project roots. Never infer write ownership from filesystem writable state.

`RefreshReport` contains version, executionId, start/end timestamps, elapsed times per major phase, discovered paths, duplicate count, previewCount, savedCount, diskVerifiedCount, unchangedCount, skippedCount, failedCount, recoveryRequiredCount, and per-file `FileOutcome` records. A failure in one file does not silently count as a success.

## Components and boundaries

1. **Discovery (read-only):** `DiscoverCandidates(request, adapter)` returns unique normalized absolute paths with originating reference path, document kind, and discovery errors. For AssemblyGA include active .iam and recursive .iam/.ipt dependencies; for DrawingGA include active .idw/.dwg and all .idw/.dwg in its immediate directory, no recursive drawing search. Fail discovery before any APPLY when the candidate set cannot be trusted.
2. **Eligibility (read-only):** `ClassifyEligibility(candidate, request, adapter)` resolves canonical paths and project-root ownership; excludes external Content Center, JC and SJD library roots regardless of filename; does not exclude in-project JC/SJD copies solely by name. Validate read-only, active dirty state, Vault checkout owner, lifecycle and file locks. Vault state UNKNOWN => APPLY denied; preview may still report candidates with blocked status. Explicitly guard path traversal, mapped drive/UNC aliases, symbolic links/reparse points and case-insensitive comparison.
3. **Planning (read-only):** `PlanPropertyChanges(candidate, mapping)` yields typed `PropertyChange` records: file, property-set identifier, property name, oldValue, newValue, reason. No mutation during planning. Model mapping: Design Tracking Part Number and existing custom SPECIFICATION, replace leading `PJ[0-9]{5}` only when immediately followed by hyphen; retain entire suffix. Other fields require explicit mapping approval. Drawing mapping: only proven existing custom DRAWING_NUMBER, derived from filename's leading project prefix; never reset REVISION or issue fields.
4. **Mutation and verification (APPLY only):** `ApplyAndVerify(candidate, plan, adapter)` checks preflight ownership immediately before writing, captures original values, performs changes, saves once, closes/reopens or independently re-reads persisted file, and compares exact expected values. Return SAVED and DISK_VERIFIED as distinct states. If any operation fails, restore originals where safe and verified, otherwise quarantine and report RECOVERY_REQUIRED with file path and exact state; never silently discard dirty partial changes.
5. **Logging:** structured records for each phase, per-file old/new values, duration, Inventor/Vault API failures and recovery decisions; no message boxes inside core. Caller owns UI and explicit APPLY confirmation. Avoid logging secrets or credentials.

## iLogic packaging rule

The single core source file must be referenced through the iLogic-supported external code inclusion mechanism validated in the target Inventor version. Standalone wrapper and later integration adapter both call the same public entry point and version. Do not qualify an inline copy or a rewritten implementation as shared reuse. Compatibility must be demonstrated on Inventor 2025 and any legacy versions actually targeted, not assumed.

## Vault safety contract

A file being writable is **not** evidence of Vault checkout. Apply requires an authoritative Vault adapter confirming file identity, ownership by current user, checkout state and permitted operation, or a separately validated signed/controlled checkout manifest accepted under a documented test-only policy. If adapter unavailable, Apply is disabled. No automatic checkout. Never write directly to Vault's database.

## COM lifecycle and limitations

Inventor COM calls are synchronous. Stopwatch timings, cooperative cancellation between files, and progress logs do not provide a hard timeout for a hung COM call. Do not promise automatic recovery from a frozen Inventor process. Keep operations bounded per file where possible, persist a journal before mutation, and provide operator recovery instructions for stalled processes. Only close documents opened by this operation; do not close pre-existing user documents. Avoid modifying dirty documents.

## Minimum offline regression matrix

| Case | Expected |
|---|---|
| `PJ00201-3410-01` -> `PJ00333` | `PJ00333-3410-01` |
| `pj00201-3410-01` -> `PJ00333` | `PJ00333-3410-01` |
| `PJ00201` (no hyphen) | unchanged |
| `PJ00201X-3410` | unchanged |
| `ABC-PJ00201-3410` | unchanged |
| `PJ00201-3410-PJ00201` | `PJ00333-3410-PJ00201` |
| Already `PJ00333-3410` | unchanged (idempotent) |
| Missing SPECIFICATION | skip that property, do not create implicitly |
| External CC/JC/SJD referenced by GA | never write |
| In-project JC/SJD copy in approved root | eligible subject to ownership |
| Sibling folder inside project root | eligible if referenced |
| Drawing folder nested under project root | drawing entry sees only its own folder |
| Duplicate references | one file outcome |
| Vault state unknown or checked out by other user | APPLY blocked |
| Read-only, dirty, locked or invalid path | APPLY blocked |
| Save failure after first property mutation | rollback or RECOVERY_REQUIRED |
| Save succeeds, disk reopen fails | SAVED, not DISK_VERIFIED |
| Repeated APPLY with same prefix | no additional changes |

## Qualification gates

- **G0:** design and contracts reviewed.
- **G1:** pure planning/path rules tested offline against fixtures, source assertions executed and recorded.
- **G2:** shared core and standalone wrapper compile in Inventor; preview verified on disposable nested assemblies/drawings.
- **G3:** authorized checkout-aware APPLY, persisted readback and recovery tested on disposable Vault-managed copies.
- **G4:** regression suite passed; standalone wrapper and integration adapter confirmed to use exact same core version.

Do not announce a complete candidate until source is committed, actual static checks are executed and documented, and limitations are explicit. Do not call G1–G4 passed without evidence. Existing Target Repair work remains separate.
