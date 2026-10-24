# MAD Run: PROJECT-LAUNCH-Plus Architecture

**Date:** 2026-10-24
**Topic:** PROJECT-LAUNCH-Plus — central config file + project structure automation
**Cycle:** AA → DA → SSA
**Session:** https://claude.ai/code/session_01TAkMGJHWx8Am8HumHMEoSx

---

## Background

User wants to eliminate manual project maintenance overhead across potentially hundreds of claude.ai Projects by:
1. A single GitHub-hosted config file (PROJECT-LAUNCH-Plus) fetched at session start in every project
2. A wizard-as-first-session to scaffold new projects to standard
3. A clear sub-project structure model
4. Automated propagation of updates across all projects

---

## SSA Verdict

**Build PROJECT-LAUNCH-Plus. Core concept is correct. Three safeguards required.**

| Decision | Recommendation |
|----------|---------------|
| Build it? | Yes — pull-from-one-file beats N-project drift |
| File size | Hard limit ≤1,500 chars; verbose content in sub-files |
| Fetch failure | Must be loud: Claude confirms fetch in first response line |
| Per-project overrides | PROJECT-CONFIG.md Overrides section; read after global fetch |
| Sub-project model | Docs within one parent Project by default; separate Project only when domain/lifecycle genuinely diverges |
| Migration | Lazy — active projects first; PLU-migration-status.md tracks progress |
| SPOF risk | draft branch for testing; main branch for production; CHANGELOG in-file |

**Rejected DA claim:** "Cognitive overhead shifts, not eliminates" — concentrating risk into one well-maintained file is strictly better than distributed unmaintained per-project risk.

---

## Build Order

1. `PROJECT-LAUNCH-Plus.md` — the core hook file
2. Standard project instruction block (exact paste text)
3. `PLU-wizard.md` — wizard sub-file for new project onboarding
4. `PLU-migration-status.md` — cross-project index / migration tracker
5. Migrate active projects (MAD PROJECT first)

---

## Win-Win Enhancements

| # | Enhancement |
|---|-------------|
| WW1 | PLU instruction doubles as MAD skill trigger ("MAD run" → auto-start AA/DA/SSA) |
| WW2 | PLU-migration-status.md doubles as cross-project discovery index |
| WW3 | Versioned branding tokens — flag when a project was built with old branding version |
| WW4 | Wizard writes self-update check into PROJECT-CONFIG.md — alerts on protocol changes since creation |

---

## Files

| File | Contents |
|------|----------|
| `AA-output.md` | Advocate: case for central config, wizard, docs-within-project model |
| `DA-output.md` | Devil's Advocate: fetch reliability, SPOF risk, scale limits |
| `SSA-output.md` | Synthesizer: verdict table, 6 architecture decisions, 4 win-wins, build order |
