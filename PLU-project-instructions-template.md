# PLU Project Instructions Template
version: 2.0
last-updated: 2026-10-25
status: CANONICAL — paste this content into Project Settings → Instructions

This file is the source of truth for what goes into every project's Settings → Instructions field.
It is NOT fetched at session start. It is pasted once and lives permanently in the project.
Update this file when trigger definitions change → paste updated version into any affected projects.

---

## PASTE THIS INTO: Project Settings → Instructions

```
TRIGGER WORDS — always active, no fetch required:

RMAD = Run full MAD cycle immediately: spawn AA agent (strongest case FOR) + DA agent (strongest case AGAINST) in parallel → SSA synthesiser verdict → commit all three outputs to GitHub under runs/[topic]/ as AA-output.md, DA-output.md, SSA-output.md, README.md

Mini-MAD = Inline MAD: write one AA paragraph + one DA paragraph + one-line SSA verdict in chat. No agents, no GitHub commit. End with: "Escalate? (RMAD)"

PHONICSPlus = Apply full Phewphonics brand spec to the next visual output (popup, dashboard, layout, card, calculator — anything rendered). Fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-branding-extended.md for full token set. Fallback tokens: primary #4B2FA0, accent #7B5ED4, bg-dark #1A1020, font-display Nunito 700/800, font-sub Rajdhani 600/700, buttons border-radius 999px.

FTCA = FTCAgent Fine Tooth Comb review. Fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-behaviour.md, assess session patterns, fire alerts if thresholds met.

NEWPROJECT = Output the ready-to-paste project instructions block (this template's content) for a new Claude project.

PLU = PROJECT-LAUNCH-Plus — the global config on GitHub that governs all projects (https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PROJECT-LAUNCH-Plus.md)

SSSOT = Single Shared Source Of Truth — the MAD-SSSOT GitHub repo (https://github.com/Waynitos/MAD-SSSOT)

SSA = Synthesiser verdict — final output of a MAD cycle
AA = Advocate — argues the strongest case FOR a position
DA = Devil's Advocate — argues the strongest case AGAINST a position

MAD commit target: https://github.com/Waynitos/MAD-SSSOT
MAD run folder pattern: runs/[topic]/
```
