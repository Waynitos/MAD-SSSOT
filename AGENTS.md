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
