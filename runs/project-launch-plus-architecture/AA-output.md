# AA Output — PROJECT-LAUNCH-Plus & Project Structure

**Role:** Advocate — strongest case for the proposed system
**MAD Run:** project-launch-plus-architecture

---

## 1. PROJECT-LAUNCH-Plus as central config

This is the correct architectural pattern for the problem. The alternative — maintaining standards per-project — guarantees drift. When branding changes, when MAD protocols evolve, when a new onboarding step is added, a per-project model requires N manual updates across N projects. That's not a workflow, it's a maintenance liability that compounds with every new project.

A single GitHub-hosted file solves this with a mechanism that already works today: Claude fetches a raw GitHub URL via WebFetch in any session where the project instructions reference it. No API, no infrastructure, no build step. The propagation mechanism is the normal session start.

What belongs in PROJECT-LAUNCH-Plus:
- **MAD protocol** — AA/DA/SSA definitions, output format, commit conventions
- **Branding tokens** — primary/secondary colours (hex), font stack, button radius, panel styles, spacing units. Defined once, consumed by any artifact, app, flashcard, or prompt page Claude builds in any project
- **Doc setup instructions** — standard project doc structure (Index, Run Log, Decisions, Branding)
- **Git conventions** — attribution lines, commit message format, branch naming
- **Global updates section** — a dated changelog at the top; Claude reads the latest entry first and applies any new protocol changes before doing anything else

The versioning story is clean: the file lives at a stable URL, updates are committed with a date entry in the changelog, and every project inherits the update on its next session with zero manual intervention.

---

## 2. Wizard-as-first-session

The constraint (can't programmatically create a claude.ai Project) is real but minor. The user clicks "New Project" and pastes one instruction block containing the PROJECT-LAUNCH-Plus URL and a trigger phrase like `"Run PROJECT-LAUNCH-Plus onboarding"`. The first message in the new project kicks off the wizard.

The wizard sequence:
1. Fetch PROJECT-LAUNCH-Plus (always first — loads current protocols and branding)
2. Ask: Project name, one-line description, optional sub-project code
3. Scaffold: create the standard project docs (Index, MAD Run Log, Decisions), pre-populated with the name/description/code
4. Confirm branding applied: write a `BRANDING.md` doc with the tokens from PROJECT-LAUNCH-Plus
5. Done — project is live-standard in under 2 minutes

This is more robust than a separate tool because it runs inside the same Claude session that will do the actual work. No context-switching, no separate onboarding app to maintain. The wizard IS the first work session.

---

## 3. Sub-project model: docs within one parent Project

For Waynito's use case — engineering projects with a PJ##### code, each with sub-tasks, scripts, MAD runs — **docs within one parent Project** is the stronger model at scale, for this reason: claude.ai's project instructions are the propagation vector. If sub-projects are separate Projects, each needs its own instructions block containing the PROJECT-LAUNCH-Plus URL. That's N manual pastes, N separate projects to manage, and N separate search surfaces.

If sub-projects are docs within one parent Project:
- One set of project instructions covers all sub-projects
- All MAD runs, decisions, and branding live in one searchable space
- The MAD Run Log doc accumulates all runs for the parent project in one place
- Separate Projects make sense only when a sub-project genuinely diverges in domain, team, or lifecycle — not just because it has a different sub-number

The doc naming convention carries the structure: `PJ00193-3620-MAD-Log.md`, `PJ00193-3620-TRAVERSE-Fixes.md`. The flat doc list IS the folder structure, just without the folders.

---

## 4. One-file-updates-all propagation

The propagation model has a powerful property: it's pull-based, not push-based. Claude in each project fetches the latest PROJECT-LAUNCH-Plus at session start. There's nothing to push, no webhook to configure, no API to call. The update is available the moment the GitHub commit lands. Every project gets it on its next session.

For the one-time migration to existing projects: this is a known-finite task. The migration instruction is: open each project, add the PROJECT-LAUNCH-Plus URL to the instructions. That's it. Once done, the project is permanently on the propagation network.

At scale (hundreds of projects), new projects cost one click + one paste. Existing projects cost one paste each, once. After that, protocol changes cost one GitHub commit. That's the correct cost structure.

---

## 5. Honestly Acknowledged Weaknesses

- **WebFetch latency at session start** — keep PROJECT-LAUNCH-Plus under 2KB; put verbose reference material in linked sub-files
- **No guaranteed fetch** — relies on instruction being present and Claude following it; not a hard guarantee
- **Migration is still manual** — one-time paste-per-project for existing projects; prioritise active ones first
- **Flat doc list gets long** — naming conventions + a PROJECT-INDEX.md doc mitigate this
- **Branding in text form is approximate** — hex colours/fonts work for artifacts but don't auto-apply to the claude.ai UI

---

*AA output — PROJECT-LAUNCH-Plus MAD cycle*
