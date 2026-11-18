# Rules for AI agents working in MAD-SSSOT

This repo (https://github.com/Waynitos/MAD-SSSOT, branch `main`) is the single
source of truth for iLogic scripts, Python scripts, prompts, and project
instructions. Every AI agent (Claude, Grok Bot, Cursor, others) follows these rules.

## 1. Work from a real checkout, not raw links
- Edit files in a git checkout of this repo (local clone, Claude Code, Cursor, etc.).
- Do NOT rely on raw.githubusercontent.com fetches or pasted fragments as the
  "current" file. They can be rate-limited, stale, or truncated.
- Pull (`git pull`) before starting any change so you work on the latest version.

## 2. Full files only
- Before editing a script, read the WHOLE file.
- Write back the COMPLETE updated file. Never commit a stub, a summary,
  a "placement" line, "...rest unchanged...", or "see attached" in place of code.
- Before committing, check `git diff --stat`. If a script shrinks to a few
  lines or bytes, stop: something was truncated.
- Keep each file's existing line endings (some `.iLogicVb` files are CRLF).

## 3. One file per script, always the latest
- Update the existing file in place. Do NOT create dated or versioned copies
  (e.g. `Script_2112026.iLogicVb`, `Script_v2.iLogicVb`, `Script_final.iLogicVb`).
- Older versions live in git history and tags. To roll back, restore from
  history as a new commit; never rewrite history or force-push.
- Known-good versions are marked with tags (e.g. `baseline-2026-11-02`).
  Add a tag when the user confirms a script works in Inventor.

## 4. Commits
- One logical change per commit, with a clear message, e.g.
  `ilogic: TRAVERSE Mode 6 skips Content Centre parts`.
- Push to `main` unless the user asks for a branch or pull request.

## 5. Push rejected? Pull, re-apply, push again
- If `git push` is rejected (non-fast-forward), do NOT force-push.
- Run `git pull --rebase origin main` to bring in the other agent's commit.
- Re-apply your change to the updated file (re-read it first — it may have
  changed), then commit and push again.
- If the rebase produces a conflict on a full-file script, yours wins: write
  your complete intended version, `git add` it, `git rebase --continue`, push.
- Never use `--force` or `--force-with-lease`. History is append-only.

## 6. If you cannot push
- If you have no write access (e.g. a chat-only session), give the user the
  COMPLETE updated file, never a partial diff or snippet, and say which path
  it replaces. Do not invent a new filename.

## Where things live
- `scripts/ilogic/`   iLogic rules (`.iLogicVb`)
- `scripts/`, `scripts/<domain>/`   Python scripts
- `prompts/`          MAD agent prompts (AA, DA, SA, SSA)
- repo root `*.md`    project instructions and protocols
- `runs/`             MAD run outputs


## 7. BEEXCITED Codex routing and isolated-branch override (2026-11-14)
- These instructions override the general `main` push default in section 4 for all PROPERTY REFRESH TEST 01 / Clean Sweeper work. **Never edit, push, merge or deploy `main` for this assignment.** Work only on `feature/sweeper-v2.2.34-existing-target-repair`, or a child task branch with an explicitly approved PR targeting that feature branch. Never resolve conflicts by automatically preferring the agent's version; preserve both sides and seek review when uncertain.
- Before coding, read `docs/BEEXCITED_CODEX_HANDOVER_PROPERTY_REFRESH_01.md`, `docs/BEEXCITED_CODEX_ROUTING_PROTOCOL.md`, `docs/PROPERTY_REFRESH_TEST_01_SHARED_CORE_CONTRACT_v0_1.md` and the qualification blockers audit. Verify actual repository state; the handover is a snapshot, not proof of current code.
- The first assignment is PROPERTY REFRESH TEST 01 only. Build one canonical shared execution core with separate read-only discovery, root/library classification, property planning, logging and thin GA assembly/drawing wrappers. Reuse the same source without copy/paste for later Clean Sweeper integration. Do not expand into Existing Target Repair.
- Dry-run first. APPLY must stay fail-closed until authoritative Vault checkout ownership, project-root resolution, dirty/read-only guards, persisted-file verification, partial-write recovery and target-Inventor runtime tests are qualified. Never auto-checkout or alter original/source/external library files.
- Keep original successful iLogic scripts intact. Do not delete, rename or shrink scripts without explicit approval. Respect current repository's historical versioned experiments; do not proliferate new dated clones.
- For every task: read complete relevant source files; state the proposed scope and acceptance criteria; run actual available offline tests; record command, exit code, and outcomes; separate static evidence from Inventor/Vault runtime evidence; produce a reviewable diff and report limitations. Do not claim Inventor compilation or testing from a cloud Linux sandbox.
- Routing decision: use ChatGPT/MAD for requirements and design; Codex for implementation, refactoring, codebase inspection and offline testing; use both plus human approval for high-risk Vault/file mutation. Never imply a Codex job has been started merely because a handover was prepared.
- Do not auto-merge or change production. Stop and ask for approval if the task requires external credentials, repository permission escalation, destructive changes, or modifying actual engineering project files.

## 8. Mandatory reuse-first gate (2026-11-15)
- **Before implementing or modifying ANY code**, follow `docs/BEEXCITED_CODE_REUSE_FIRST_DIRECTIVE.md`. This applies to all agents, Code Assassin/iLogic Assassin, Codex, all languages and all projects, not just Property Refresh.
- Recover prior user-provided working code and repository history first; research vendor documentation, accepted community solutions and existing implementations next. Record URLs, compatibility and licensing. Compare working vs failing implementations and document the smallest justified change **before** coding. Do not write another rule merely because a known working one was not searched for.
- The implementation handoff/PR must contain a reuse-evidence section: exact previously working file or explicit retrieval gap, source links, difference analysis, reuse decision, actual static tests and host-runtime validation status. Missing evidence means the coding gate FAILED; return to research, not speculative implementation.
- For Inventor Property Refresh, specifically inspect the user's prior successful drawing/title-block property update rules and direct `PropertySets` setter/save pattern. Do not assume `DRAWING_NUMBER` is the correct drawing field or claim a rule works until tested in Inventor. This directive does not authorize APPLY, Vault writes, or modification of main/production.

## 9. Automatic capability routing — BEEXCITED default (2026-11-18)
- Treat selection of the best available ChatGPT-native capability as the agent's responsibility, not the user's. At task intake, assess whether Codex is needed for substantial repository coding, multi-file refactoring, debugging, test execution, or review of implementation diffs. If so, route to Codex by default; do not wait for the user to ask "are we using Codex?".
- Before implementation, perform the mandatory reuse-first / iLogic Assassin research gate in section 8. Codex must receive the exact repository, approved branch, relevant current source, contracts, acceptance tests, known blockers and safety boundaries. Use the canonical handover, updating it if stale. Avoid duplicate agents rewriting the same implementation.
- Check whether an actual Codex execution capability/session is available. When available, initiate the Codex workflow using supported tools and confirm its job/session identifier or concrete output. If unavailable, say so plainly and provide an actionable handoff; **never claim a Codex run was triggered solely because instructions were written, a handover exists, or GitHub was accessed**. Do not invent integrations or silently substitute manual GitHub edits while reporting them as Codex work.
- ChatGPT/MAD owns requirements, architecture, research coordination, risk review and acceptance; Codex owns eligible implementation, codebase inspection, offline tests and reviewable commits; Inventor/Vault runtime validation remains on an authorized Windows host. Prefer the appropriate available native capability for other tasks too, subject to permissions and user approval.
- Preserve the user-approved scope, branch, isolation and safety gates. For Clean Sweeper PROPERTY REFRESH TEST 01, only `feature/sweeper-v2.2.34-existing-target-repair` may be changed, APPLY remains blocked until qualified, and Existing Target Repair remains separate. No automatic main/production modifications, merges, credentials, Vault checkouts or source-model edits.
- Completion reporting must distinguish (a) routing decision, (b) actual Codex session launched, (c) code committed and static tests executed, and (d) Inventor/Vault host validation. For PROPERTY REFRESH TEST 01, notify the user only after a complete candidate is committed with link and actual static-check evidence; otherwise do not send recurring incomplete-status notifications.
- This policy is a persistent repository instruction for future agent sessions that read this branch. It does not itself create a background Codex job, alter ChatGPT account-wide settings, or guarantee that every future session has Codex access.

## 10. Tool-first, evidence-driven escalation (2026-11-18)
- For each engineering or software task, inventory the relevant available native ChatGPT features, connected tools, external apps, proven vendor utilities and open-source frameworks. Proactively discover suitable integrations; recommend installation/connection when needed, but never install, authorize, spend money or share repository/project data without user approval.
- Choose the toolchain by the actual bottleneck: documentation/API uncertainty -> verified vendor references or documentation retrieval; implementation -> Codex or suitable coding agent; offline reproducibility -> executable unit/integration tests and CI; Windows Inventor/Vault-specific behavior -> disposable Windows host, Inventor API diagnostics and authorized Vault test environment. Linux static checks never substitute for Inventor runtime evidence.
- Enforce an anti-loop escalation trigger: after two unsuccessful attempts against the same failure mode, or when a required capability is missing, stop speculative code changes; record the exact failure, compare prior working implementation, search for existing solutions/tools, change the diagnostic approach, and define a discriminating test before retrying.
- Keep a compact evidence ledger: hypothesis, source/proven precedent, selected tool, test environment, reproducible steps, observed result, commit and next decision. Distinguish proposed, connected, running, executed, and verified. Never claim an external agent, connector or test ran unless there is a real execution result.
- Prefer the smallest viable toolchain and fastest safe path to an observable result. Parallelize independent research and diagnostics only; do not allow competing agents to modify the same implementation concurrently. Respect feature-branch isolation, read-only default, source protection, and explicit approval for external data transfer, Vault actions, paid tools or production changes.
- For PROPERTY REFRESH TEST 01, continue to suppress incomplete-candidate notifications as requested; do not confuse tool discovery or documentation with delivery.
