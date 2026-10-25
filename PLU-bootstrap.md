# PLU-bootstrap.md
# The single file fetched by every project's instruction block.
# All session-start logic lives here — not in the pasted instruction block.
# Update this file → all projects inherit the change next session.
version: 1.0
last-updated: 2026-10-25

---

## TRIGGER WORDS — Read this FIRST, before anything else
These are always active in every project. Never ask what they mean.

| Trigger | Action |
|---------|--------|
| `NEWPROJECT` | Output the ready-to-paste instruction block for a new Claude project (one line, copy straight into Settings → Instructions) |
| `RMAD` | Run full MAD cycle immediately: AA + DA as parallel fork agents → SSA verdict → commit all outputs to GitHub under `runs/[topic]/` |
| `Mini-MAD` | Inline MAD: one AA paragraph + one DA paragraph + one-line verdict. No agents spawned, no GitHub commit. End with: *"Escalate? (RMAD)"* |
| `FTCA` | FTCAgent Fine Tooth Comb review — fetch FTCA-behaviour.md, assess session patterns, fire alerts if thresholds met |
| `PHONICSPlus` | Apply full Phewphonics brand spec to the next visual output (popup, dashboard, layout, card, calculator — anything rendered). Fetch PLU-branding-extended.md if not already loaded this session, then build using all brand tokens. Use in any project regardless of its active branding. |
| `PLU` | PROJECT-LAUNCH-Plus — the global config on GitHub that governs all projects |
| `SSSOT` | Single Shared Source Of Truth — the MAD-SSSOT GitHub repo |
| `SSA` | Synthesizer verdict — final output of a MAD cycle |
| `AA` | Advocate — argues the strongest case FOR a position |
| `DA` | Devil's Advocate — argues the strongest case AGAINST a position |

---

## NEWPROJECT trigger — output this block exactly when user types NEWPROJECT

```
─────────────────────────────────────────────
📋 COPY THIS INTO: Project Settings → Instructions
─────────────────────────────────────────────
MANDATORY FIRST ACTION — before reading memory, before responding to any message: call WebFetch on https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-bootstrap.md and follow every instruction in it exactly. Do not skip this fetch. If the fetch fails, apply these fallback triggers immediately: RMAD=run full MAD cycle (AA+DA parallel agents → SSA verdict → GitHub commit under runs/[topic]/); Mini-MAD=inline AA paragraph + DA paragraph + one-line verdict, no commit; PHONICSPlus=fetch PLU-branding-extended.md and apply Phewphonics brand tokens to next visual output; FTCA=fetch FTCA-behaviour.md and run behaviour review.
─────────────────────────────────────────────
```

Then say: "Paste that block into ⚙ Settings → Instructions → Save. Then open the first session — the wizard runs automatically."

---

## STEP 1 — Fetch PROJECT-LAUNCH-Plus
Fetch: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PROJECT-LAUNCH-Plus.md
Apply: MAD routing (RMAD / Mini-MAD / FTCA threshold), branding tokens, FTCA protocol, git conventions.
On success: begin response with ✓ PROJECT-LAUNCH-Plus v[version] loaded
On failure: begin response with ✗ PLU fetch failed — triggers and branding from bootstrap only

## STEP 2 — Fetch project config (if it exists)
Read PROJECT-CONFIG.md doc in this project.
Apply any Overrides from PROJECT-LAUNCH-Plus.
If a branding override names the Phewphonics block, fetch:
  https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-branding-extended.md
  Apply ## Phewphonics block to all artifacts, apps, and UI outputs this session.

## STEP 3 — Check for wizard trigger
If no PROJECT-INDEX.md doc exists in this project:
  Fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-wizard.md
  Run the onboarding wizard sequence.
If PROJECT-INDEX.md exists: do not re-run wizard. Offer to update if user asks.

## STEP 4 — FTCA session monitoring
Fetch: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-behaviour.md
Scan last 3 entries for REPETITION patterns before responding.
Monitor session for TOOLING / REPETITION alerts — fire inline if threshold met.
At session end: append new OBSERVATION block and push to GitHub.

## STEP 5 — Version check
If PLU version is newer than the date in PROJECT-CONFIG.md Self-update check:
  Flag at top of first response: ⚠️ PLU updated to v[x] since this project was last configured.

---

## FALLBACK (if this bootstrap fetch also fails)
Apply these minimum rules so the session is never completely blind:

Triggers: RMAD = full MAD cycle | Mini-MAD = inline MAD | FTCA = behaviour review
Branding: primary #4B2FA0 | font-display Nunito | font-subtitle Rajdhani (Phewphonics)
MAD protocol: AA → DA → SSA | commit to https://github.com/Waynitos/MAD-SSSOT
FTCA log: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-behaviour.md
