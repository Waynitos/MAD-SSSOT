# DA Output — PLU Sync Architecture
MAD Run: plu-bootstrap-sync | Date: 2026-10-25

## Position challenged
The claim that the current PLU GitHub-fetch architecture solves the "projects go stale" problem.

## Argument
The GitHub-fetch architecture does not solve the staleness problem — it relocates it. The claim that projects "auto-update" is only true for the *content* of PROJECT-LAUNCH-Plus.md. The instruction block sitting in Project Settings across every project is static the moment it's pasted. If that block ever needs to change its fetch URL, add a second fetch, or modify the bootstrap sequence, every single project requires a manual re-paste.

The fetch-on-demand model for sub-files is a hidden dependency that breaks silently. When Claude starts a session, it fetches PLU. PLU lists sub-files as "fetch on demand." But "on demand" means Claude must know to fetch them. If PLU is updated to add a new required sub-file, sessions in established projects will miss it entirely until the user stumbles into the right keyword.

Trigger word amnesia is not an edge case — it is the default state at the start of every session. If the user's opening message contains RMAD, Claude has not yet loaded PLU and has no definition for that term. The response will either be a question, an incorrect inference, or a fabricated interpretation.

Instruction block drift across 10+ projects is inevitable. Different projects set up at different PLU versions will have subtly different wording. Some will have the old `?MAD` trigger. Some won't have FTCA. There is no audit trail, no version stamp, and no way to query which projects have which version.

## Real failure modes (ranked by likelihood)
- [NEAR-CERTAIN] Instruction block version drift — silent, accumulates over time. Severity: HIGH
- [HIGH] Trigger word amnesia on opening message — breaks flow, recoverable. Severity: MEDIUM
- [HIGH] Sub-file miss on new required behaviour — silent data gap. Severity: HIGH
- [MEDIUM] GitHub/proxy fetch failure — full protocol degradation, no retry. Severity: HIGH
- [MEDIUM] Structural PLU change requiring instruction block update — manual at scale. Severity: HIGH

## Structural fix required
The instruction block must be minimised to a SINGLE stable URL fetch. Everything else — what to fetch next, in what order, with what fallback — lives in a bootstrap file on GitHub. The instruction block then never needs to change again, regardless of PLU evolution.

Currently the instruction block contains logic that should live in GitHub, not in a pasted static string.
