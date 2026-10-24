# DA Output — PROJECT-LAUNCH-Plus MAD Cycle

**Role:** Devil's Advocate — strongest case against the proposed system
**MAD Run:** project-launch-plus-architecture

---

## 1. Failure Modes of PROJECT-LAUNCH-Plus

### 1.1 The fetch is not guaranteed — and failure is invisible

PROJECT-LAUNCH-Plus only works if Claude actually fetches the URL at session start. This depends on:
- Claude interpreting the instruction as "fetch this now" rather than "this is a reference link"
- WebFetch succeeding (GitHub raw URLs are normally accessible, but the proxy allowlist in cloud sessions may refuse them)
- The file being syntactically parseable after fetch — a mid-edit save that leaves the file malformed means every project silently gets no global config that session

There is no confirmation mechanism. If the fetch fails, Claude proceeds with no global config and no error.

### 1.2 Instruction token budget conflict

claude.ai project instructions have a size limit. Adding a fetch-and-apply directive for a large PROJECT-LAUNCH-Plus file eats into that budget — and if the file grows (branding + MAD protocols + doc setup + onboarding + wizard instructions), the fetched content may compete with the project's own instructions for the context window. Claude may summarise rather than apply it precisely.

### 1.3 Global changes break project-specific overrides silently

When PROJECT-LAUNCH-Plus is updated, the change applies to ALL projects simultaneously on next session. If a project had been working around a quirk in the old global config, the update silently overwrites that workaround. There is no per-project override mechanism — it's all-or-nothing inheritance.

### 1.4 Version history is on GitHub, not visible in claude.ai

If a project starts behaving differently after a PROJECT-LAUNCH-Plus update, the user must go to GitHub to diff the file. At scale (hundreds of projects, multiple updates per month), this becomes a debugging burden.

---

## 2. The Wizard-as-First-Session Gap

### 2.1 The hardest step is still manual

The user still must: open claude.ai, click New Project, type the project name, paste the PROJECT-LAUNCH-Plus instruction URL, then start the first session. That's 4–5 manual steps before the wizard even starts.

### 2.2 The wizard can't write back to project instructions

The wizard runs in a conversation. It can create project docs, but it cannot update the project's own instructions field (requires the user to go to Project Settings). Any project-specific config lives in a doc, not in the instructions — meaning subsequent sessions need an additional instruction to "read the project config doc at session start." Another manual step that can be forgotten.

### 2.3 Wizard output is a snapshot, not a live contract

The wizard runs once at project creation. If MAD protocols change six months later, the scaffolded docs are not automatically updated. The user must either re-run the wizard (creating version conflicts) or manually update project docs.

---

## 3. The Sub-Project Modelling Problem

### Option A: Separate claude.ai Projects per sub-project

- At hundreds of sub-projects, the claude.ai project list becomes unnavigable — no folder, tag, or search-by-prefix in the UI
- Each sub-project needs its own PROJECT-LAUNCH-Plus instruction pasted manually
- Context is siloed: a sub-project session has no awareness of its siblings
- If a parent project's scope changes, updating 15 sub-project instructions is 15 manual edits

### Option B: Docs/tabs within one parent Project

- A single Project's doc list becomes unwieldy at scale — docs are flat, no folders within a Project
- All sub-projects share the same instruction set — no per-sub-project config
- Sessions in a large multi-sub-project Project carry context from all sub-project docs, creating cross-contamination (Claude may apply TRAVERSE logic to a Spanish-learning task)
- The Project's knowledge size limit caps total doc content

**Neither option scales cleanly to hundreds. The platform wasn't designed for this use case.**

---

## 4. Hidden Assumptions in "One File Updates All"

For the propagation model to actually work, ALL of the following must be true simultaneously:

1. **Every project has the fetch instruction** — any project missed during migration is permanently out of sync with no warning
2. **Claude executes the fetch on every session start** — not guaranteed; depends on instruction wording
3. **The fetch succeeds** — GitHub availability, proxy allowlist, network conditions
4. **The file is always in a valid, parseable state** — a bad push leaves all projects broken simultaneously
5. **Updates are backwards-compatible** — a breaking change breaks every project at once
6. **The file stays small enough** — as it grows, Claude starts summarising rather than applying precisely

**The single point of failure risk is the inverse of the benefit:** "one file updates all" means "one bad file breaks all."

---

## 5. Scale Risks at Hundreds of Projects

### 5.1 The migration problem compounds

Every new project requires manually pasting the PROJECT-LAUNCH-Plus URL. At project 200, it's 200 manual pastes with no mechanism to bootstrap new projects with the URL already present.

### 5.2 No discovery mechanism across projects

With hundreds of projects, finding "which project has the TRAVERSE audit" requires opening each one. The MAD-SSSOT-Index.md is manually maintained and will drift.

### 5.3 Cognitive overhead shifts, not eliminates

The current problem: "I have to manually update each project." The proposed solution: "I have to maintain PROJECT-LAUNCH-Plus correctly, ensure every project has the hook, and debug silently-failed fetches." Human dependency isn't eliminated — it's concentrated into one critical file. When something goes wrong at scale, it goes wrong everywhere simultaneously.

### 5.4 Platform dependency risk

This entire architecture depends on claude.ai's Projects feature behaving as it does today. Any of these could change with a platform update: instructions fetched per-session, WebFetch available in project sessions, no rate limit on fetching the same URL across hundreds of sessions.

---

*DA output — PROJECT-LAUNCH-Plus MAD cycle*
