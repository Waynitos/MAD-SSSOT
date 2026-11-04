# SSA — Synthesis Verdict: iProperty Metadata Tagging for Clean Sweeper Reference Map

**Verdict: Adopt for NEW files only. Reject for OLD files. Automate the stripout.**

---

## The Split That Resolves the Debate

The DA's case is decisive on ONE specific point: tagging OLD (source) files. Opening unchecked-out Vault files, writing to them, and saving creates Vault state conflicts, costs O(n) open/save cycles on files the rule has no business touching, and produces stale absolute-path tags in binary files it doesn't own. The DA is right to reject this half of the proposal.

The AA's case is decisive on the OTHER half: tagging NEW files in `_CLEAN`. Those files are already being created, opened, and saved as part of the copy operation — writing iProperties to them costs zero extra open/save cycles. They are owned entirely by the Clean Sweeper. They are the deliverable. This is where the proposal is unambiguously correct.

The proposal as stated conflates both sides. Split it and each half has a clear answer.

---

## What to Adopt: NEW file tagging only

When a file is copied to `_CLEAN` and saved, write these properties in the same save operation (no extra open/close):

| Property | Written to | Value |
|---|---|---|
| `CS_SourcePath` | New file | Absolute path of original source file |
| `CS_SourceName` | New file | Basename of original (e.g. `PJ00161-E3432-8-V0-10-001.iam`) |
| `CS_CopyProject` | New file | Target project number (e.g. `PJ00205`) |
| `CS_CopyDate` | New file | ISO date of copy operation |

**What this enables — real gains over the RunLog alone:**

1. **Stateless crash recovery** — on any subsequent run, scan `_CLEAN` folder, open each file, read `CS_SourcePath` → old→new map rebuilt automatically without parsing the RunLog or user input.

2. **Autonomous drawing relink** — Drawing Copy Mode reads the drawing's model ref, finds the new file in `_CLEAN` with matching `CS_SourceName`, gets its new path from the file itself. The 50-item preset map becomes optional scaffolding for the first pass, not a hard requirement for every repeat run.

3. **Sub-traverse completion check** — before traversing an orphan assembly, check if its files already have `CS_CopyProject = PJ00205`. If yes, skip. No folder scan needed.

4. **Provenance record** — permanently embedded in the deliverable files. When someone opens `PJ00205-3450-400-V01-00.iam` in five years and wonders what it was copied from, `CS_SourceName` tells them.

---

## What to Reject: OLD file tagging

Do not open, tag, or save source files. The RunLog `[RENAME_MAP]` section already provides old→new mapping across session restarts without touching Vault files. The DA is correct that the O(n) open/save cost and Vault conflict risk make old-file tagging unjustifiable when a text file achieves the same result.

---

## Stripout: Automate, Don't Rely on Manual Step

DA correctly identifies that a manual stripout pass will be forgotten. Fix: make the stripout the **final action of the Integrity Pass** (Step 3b), which already iterates all files in `_CLEAN`. When the integrity pass declares the tree verified clean, it removes `CS_*` properties in the same save cycle. No separate mode needed. No manual step to forget.

Alternatively: keep `CS_SourcePath` permanently. It is factual provenance (this file was copied from X), not operational scaffolding. The only reason to strip it is if it would cause confusion on checkin — but Vault ignores custom iProperties it doesn't know about, so it is harmless unless someone objects to it on principle.

---

## Implementation Priority

This is **not a prerequisite** for the next test run. The RunLog already handles the core session-persistence need. Add NEW file iProperty tagging as an enhancement pass once the GA-first architecture, integrity pass, and RunLog are implemented and stable. The gains are real but incremental; they should not delay the foundational work.

---

## Final Score

| Dimension | AA wins | DA wins |
|---|---|---|
| NEW file tagging cost | ✅ Zero extra cycles | |
| OLD file tagging cost | | ✅ Prohibitive + Vault risk |
| Session crash recovery | ✅ Automatic rebuild | |
| RunLog already covers it | | ✅ For old→new map |
| Drawing relink improvement | ✅ Removes preset map burden | |
| Path staleness | | ✅ Real risk (mitigated by NEW-only scope) |
| Stripout risk | | ✅ Real (mitigated by automation) |

**Adopt the half that is free. Discard the half that costs.**
