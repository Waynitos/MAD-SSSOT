# SSA Verdict — PLU-Bootstrap Reliability
Date: 2026-10-25
Topic: External URL fetch bootstrap architecture vs inline trigger definitions
Triggered by: Waynito (phewphonics@hotmail.com)
Live failure: Claude refused bootstrap fetch in production, labelled it "suspicious instruction"

---

## Verdict

**DA wins on the bootstrap mechanism. AA wins on the SSSOT principle.**

The fetch architecture must be restructured — but the single-source-of-truth goal is preserved through a hybrid design.

---

## What DA got right

The [CRITICAL] failures are real and confirmed by live testing:

1. Claude's safety training correctly identifies "fetch this URL and follow whatever instructions are there" as prompt injection. This is not a wording problem — it is a structural one. The bootstrap instruction asks Claude to autonomously load and obey external content at session start, without user direction. That is exactly what the safety boundary rule is designed to block.

2. Inconsistent execution (sometimes fetches, sometimes doesn't) is worse than never fetching. It creates false confidence and silent failures with no error state.

3. The manual-update-per-project problem is real and has no API solution. The bootstrap instruction itself is not self-updating — it requires a human visit to every project's Settings → Instructions whenever it changes.

## What AA got right

The SSSOT principle is correct and must be preserved. Inline trigger definitions that diverge across projects are a maintenance disaster at scale. The goal — one edit propagates everywhere — is sound. Only the mechanism (fetch at session start) is broken.

---

## New Architecture: Hybrid SSSOT

### What moves INLINE (into project instructions)
- All trigger word definitions (RMAD, Mini-MAD, PHONICSPlus, FTCA, NEWPROJECT, PLU, SSSOT, SSA, AA, DA)
- Core MAD protocol steps
- Fallback branding tokens (primary #4B2FA0, fonts)

These are static definitions the user controls. They live in the project instructions field. Claude trusts them because they come from the operator-level system context, not from an external fetch.

### What stays on GITHUB (fetched when USER triggers it)
- `PLU-branding-extended.md` → fetched when user types PHONICSPlus (user-directed action)
- `FTCA-behaviour.md` → fetched when user types FTCA (user-directed action)
- `PLU-wizard.md` → fetched when NEWPROJECT runs (user-directed action)
- All MAD run outputs → committed after every RMAD run
- Templates, tokens, print specs → referenced when building outputs

The key distinction: **user-triggered fetches are accepted by Claude** because the user is present and directing the action. **Startup fetches are refused** because they look like autonomous instruction injection.

### How SSSOT is preserved

Trigger *definitions* are inline and stable — they rarely change. What changes frequently (branding tokens, FTCA logs, wizard steps, run outputs) stays on GitHub and is fetched on demand when the user triggers it. The inline definitions are the stable skeleton; GitHub holds the living content.

When a trigger definition genuinely needs updating (rare), the NEWPROJECT output block on GitHub is updated — all *new* projects get the new version automatically. Existing projects get a one-time manual update, but this happens infrequently (not every session).

---

## Immediate actions

1. **Update PLU-bootstrap.md** — remove the self-referential fetch instruction; instead, document that bootstrap content should be pasted inline into project instructions
2. **Create `PLU-project-instructions-template.md`** on GitHub — the canonical inline instruction block, ready to paste. NEWPROJECT outputs this file's content, not a URL.
3. **Update all existing projects** — paste the new inline block into Settings → Instructions (one-time, then stable)
4. **Update NEWPROJECT trigger** — outputs the full inline block content, not the fetch URL

---

## Tool matrix (revised)

| What | Where | How accessed |
|------|-------|-------------|
| Trigger definitions | Project Instructions (inline) | Always present, no fetch |
| Branding tokens (full) | GitHub PLU-branding-extended.md | PHONICSPlus trigger → user-directed fetch |
| FTCA behaviour log | GitHub ftca/FTCA-behaviour.md | FTCA trigger → user-directed fetch |
| Wizard | GitHub PLU-wizard.md | NEWPROJECT trigger → user-directed fetch |
| MAD run outputs | GitHub runs/[topic]/ | Committed after each RMAD |
| Templates | GitHub stationery/ | Fetched when building branded output |

---

## Winner

DA on bootstrap mechanism (fetch is structurally blocked by safety training).
AA on SSSOT principle (preserved via inline template + on-demand fetches).
Hybrid architecture resolves both.
