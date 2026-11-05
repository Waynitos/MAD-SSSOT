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
