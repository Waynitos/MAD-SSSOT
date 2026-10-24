# SSA Output — PROJECT-LAUNCH-Plus MAD Cycle

**Role:** Synthesizer — verdict, decisions, win-wins, build order
**MAD Run:** project-launch-plus-architecture

---

## Verdict Table

| Claim / Weakness | Verdict | Reasoning |
|---|---|---|
| AA: Central config prevents drift | CONFIRMED | Per-project maintenance guarantees divergence at scale. Pull-from-one-file is the correct pattern. |
| AA: WebFetch on raw GitHub URL works today | CONFIRMED | Established mechanism, already proven in this MAD project. |
| AA: Wizard-as-first-session is robust | CONFIRMED | Running inside the actual work session beats a separate onboarding tool. |
| AA: Docs-within-one-project is stronger than separate projects | CONFIRMED with caveat | True for sub-projects under one PJ#####. Breaks down when domains diverge (e.g. Spanish learning vs engineering). |
| AA: Pull-based propagation is zero-infrastructure | CONFIRMED | No webhook, no API, no build step. Correct cost model. |
| AA: Migration is a known-finite task | NUANCED | Finite but non-trivial at scale. Lazy migration (active projects first) is the right mitigation. |
| DA: Fetch failure is invisible | CONFIRMED | Silent failure is worse than loud failure. Needs a guard. |
| DA: Token budget conflict if file grows large | CONFIRMED | Hard limit. PROJECT-LAUNCH-Plus must stay small by design, not by hope. |
| DA: Global change breaks per-project overrides silently | CONFIRMED | Real risk. Needs a per-project override convention. |
| DA: Wizard can't write back to project instructions | CONFIRMED | Platform constraint — wizard output lives in docs only. Accepted limitation with a workaround. |
| DA: Wizard output is a snapshot, not a live contract | NUANCED | True for scaffolded docs, but PROJECT-LAUNCH-Plus itself IS the live contract. Docs are deliberately static scaffolding; protocols are fetched live. These are different layers. |
| DA: Neither sub-project option scales to hundreds cleanly | CONFIRMED | Platform wasn't designed for this. The answer is a hybrid model with clear decision criteria. |
| DA: Single point of failure | CONFIRMED | Mitigated, not eliminated, by versioning and file discipline. Needs explicit safeguards. |
| DA: Discovery across projects has no mechanism | CONFIRMED | The MAD-SSSOT-Index.md is manually maintained and will drift. Needs a better anchor. |
| DA: Cognitive overhead shifts, not eliminates | REJECTED | Concentrating risk into one well-maintained file with version history is strictly better than distributed unmaintained per-project risk. "Shifts" is only a weakness if the new location is harder to manage — it isn't. |
| DA: Platform dependency risk | NUANCED | Real but not actionable. Any Claude workflow has platform dependency. Design for today; adapt when it changes. |

---

## Architecture Decisions

### 1. Build PROJECT-LAUNCH-Plus. Keep it under 1,500 characters.

Build it. The core insight is correct. But file size is a hard constraint, not a soft one. Use a two-layer structure:

- **PROJECT-LAUNCH-Plus.md** (the hook file, ≤1,500 chars): changelog header, MAD protocol summary (3–4 lines), branding tokens (hex values + font names), git attribution lines, and a "fetch sub-files on demand" index with URLs for extended content.
- **Sub-files** (fetched only when needed): `PLU-MAD-protocol.md`, `PLU-branding-extended.md`, `PLU-wizard.md`. These live in the same GitHub repo, fetched only in sessions that need them.

The instruction in each project's settings:
> `"At session start, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PROJECT-LAUNCH-Plus.md and apply it. Confirm fetch succeeded in your first response line."`

**What stays OUT:** wizard instructions (in PLU-wizard.md), verbose MAD protocol detail (in PLU-MAD-protocol.md), script-specific fixes (in MAD run outputs).

### 2. Make fetch failure loud, not silent.

The instruction must require Claude to confirm the fetch in its first response line:
> `"Begin your first response with: ✓ PROJECT-LAUNCH-Plus [date] loaded — or — ✗ PROJECT-LAUNCH-Plus fetch failed, proceeding without global config."`

This converts invisible failure into a visible one-line status. If the line is missing, the user knows to check.

### 3. Per-project override convention.

Add a standard section to the wizard-scaffolded `PROJECT-CONFIG.md` doc: `## Overrides from PROJECT-LAUNCH-Plus`. Any project-specific deviation (different accent colour, MAD protocol variant) lives here. The project instruction includes:
> `"If a PROJECT-CONFIG.md doc exists, read it after fetching PROJECT-LAUNCH-Plus; any Overrides section takes precedence over global config."`

### 4. Sub-project structure: hybrid model with explicit decision criteria.

**Default rule:** sub-projects are docs within one parent Project, named `PJ#####-####-[topic].md`. The flat doc list IS the structure. Use a `PROJECT-INDEX.md` doc as the navigable table of contents.

**Create a separate claude.ai Project only when ALL of the following are true:**
- The domain is genuinely different from the parent (Spanish learning vs engineering automation)
- The sub-project will have its own sustained lifecycle (months, not weeks)
- Context cross-contamination would be a real problem (different branding, different protocols)

Sub-project number variants (PJ00193-3610, PJ00193-3620) → always docs within the parent PJ00193 Project.

### 5. Migration strategy: lazy migration, not bulk migration.

Do NOT attempt to migrate all existing projects at once. Instead:
- Migrate MAD PROJECT now (active)
- For each other project: migrate the first time you open a session in it (30 seconds per project)
- Maintain `PLU-migration-status.md` in MAD-SSSOT tracking which projects have the hook
- Accept that dormant projects lag — they get migrated when next needed

### 6. Single-point-of-failure mitigation: branch + validate + changelog.

- Keep `main` branch (stable, all projects use this) and `draft` branch (test changes here first)
- Before merging to main: open one test project, confirm fetch succeeds and config applies correctly
- Add `## CHANGELOG` section at the top of PROJECT-LAUNCH-Plus.md: one line per update with date
- Never edit PROJECT-LAUNCH-Plus.md directly in GitHub's web editor mid-session

---

## Win-Win Enhancements

**WW1: PROJECT-LAUNCH-Plus as a skill trigger.**
The instruction hook fetches the config AND triggers the MAD skill if the message contains "MAD run" or "audit". One instruction line, two behaviours. Reduces the wizard to "send 'MAD run' to start."

**WW2: PLU-migration-status.md as the cross-project index.**
Instead of a separate index that drifts, use the migration tracking file as the index. Columns: Project name, migrated date, last MAD run, GitHub run folder. Maintained as a side-effect of migration (low effort) and doubles as the discovery mechanism.

**WW3: Versioned branding tokens.**
Add `branding-version: v1` to the branding section. When Claude scaffolds an artifact, it records which branding version it used. If the version in PROJECT-LAUNCH-Plus changes, Claude flags "this project was built with branding v1, current is v2 — update?" instead of silently overwriting.

**WW4: The wizard writes a self-update instruction into PROJECT-CONFIG.md.**
The last line of every wizard-scaffolded PROJECT-CONFIG.md:
> `"If PROJECT-LAUNCH-Plus changelog shows a version newer than [wizard-run-date], flag it at session start."`
This converts the "wizard output is a snapshot" weakness into a forward-looking check.

---

## What to Build First

| Priority | Deliverable | Why first |
|----------|-------------|-----------|
| 1 | `PROJECT-LAUNCH-Plus.md` (≤1,500 chars, two-layer) | Everything else depends on this |
| 2 | Standard project instruction block (exact paste text) | Apply to MAD PROJECT immediately |
| 3 | `PLU-wizard.md` (wizard sub-file) | Needed for new project onboarding |
| 4 | `PLU-migration-status.md` (cross-project index/tracker) | Start with current projects |
| 5 | Migrate existing active projects | MAD PROJECT first, then others on first use |

---

*SSA output — PROJECT-LAUNCH-Plus MAD cycle*
