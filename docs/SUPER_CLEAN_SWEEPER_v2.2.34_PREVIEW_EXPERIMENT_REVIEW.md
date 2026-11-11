# v2.2.34 preview experiment — source review (2026-11-11)

Commit: 9f059135405647780c9096210ba513a08561fa6c, branch feature/sweeper-v2.2.34-existing-target-repair. Base profiler branch remains unchanged.

## Scope
Standalone experimental iLogic file; prompts for target folder and up to five basename substitutions, enumerates .iam/.ipt/.idw/.dwg/.ipn recursively, writes text report under system TEMP. No Inventor document writes, no file moves, no Vault calls, no reference replacement. This is **not** a complete repair candidate and must not be deployed.

## Static review
- Source checked against parent mode dialog and string-replacement flow (parent lines 480–550 and 620–735); experiment is deliberately independent.
- Preserves extensions and directories in proposed destination; case-insensitive literal find uses Regex.Escape and MatchEvaluator.
- Detects basic invalid names, occupied destinations, duplicate destinations, read-only source; logs blocking reasons. A single reason can mask additional blockers, and case-only collisions are not fully handled.
- Preview report is outside target root (TEMP), but filesystem enumeration can fail on access denied or long paths; no exception recovery yet.
- Critical **missing** checks: reference graph, Frame Generator skeleton ownership, externally referenced models, Vault status, path canonicalisation/reparse-point traversal, assembly/drawing integrity, filename length, transaction/rollback, and Inventor-side verification.
- **No compilation, Inventor execution, Vault test or performance benchmark performed.** No mutation code exists.

## Next gate
Implement Inventor-aware recursive reference graph with out-of-root and unresolved dependency blockers, then review against real Frame Generator sample before any mutation design. The experiment is not approved as a v2.2.34 release.
