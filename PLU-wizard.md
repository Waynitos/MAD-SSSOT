# PLU-wizard.md — New Project Onboarding Wizard
## Triggered by: first session in a new project, or message containing "onboard" or "setup project"

---

## WIZARD SEQUENCE

You are running the PROJECT-LAUNCH-Plus onboarding wizard. Follow these steps in order.

### Step 1: Confirm PLU loaded
State: "✓ PROJECT-LAUNCH-Plus v[x] loaded. Running onboarding wizard."

### Step 2: Ask 3 questions (all in one message)
```
Welcome! Let's set up this project. I need 3 things:

1. **Project name** — what is this project called? (e.g. "Inventor Clean Sweeper Suite")
2. **One-line description** — what does this project do?
3. **Project code** (optional) — e.g. PJ00193, or a domain tag like INVENTOR / SPANISH / HEALTH
```

### Step 3: Scaffold project docs (after user replies)

Create these docs in the project:

**PROJECT-INDEX.md**
```
# [Project Name] — Index
Code: [code] | Created: [date] | PLU: v[version]
Description: [description]

## Sessions (add a row per thread)
| Date | Thread | Topic | Status |
|------|--------|-------|--------|
| [date] | Onboarding | Project setup | ✓ |

## MAD Runs
| Date | Topic | GitHub folder | Artifact |
|------|-------|--------------|---------|
| — | — | — | — |

## Key Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| — | — | — |
```

**PROJECT-CONFIG.md**
```
# [Project Name] — Config
PLU-version: v[version]
Branding-version: v1
Created: [date]
Code: [code]

## Overrides from PROJECT-LAUNCH-Plus
(none — add project-specific overrides here if global config doesn't suit)

## Project-specific instructions
(add any instructions specific to this project's sessions here)

## Self-update check
If PROJECT-LAUNCH-Plus changelog shows a version newer than [date], flag it at session start.
```

**BRANDING.md**
```
# [Project Name] — Branding
Inherited from PROJECT-LAUNCH-Plus branding-version: v1
(see PROJECT-CONFIG.md Overrides section for any project-specific changes)

primary: #1a1a1a | accent: #2563eb | success: #1a7a3c
bg-light: #f8f7f4 | bg-dark: #141414
font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
font-mono: "SF Mono", "Cascadia Code", monospace
border-radius: 8px | gutter: 16px
```

### Step 4: Confirm and advise
After creating the 3 docs, say:

```
✓ Project scaffolded. Three docs created: PROJECT-INDEX.md, PROJECT-CONFIG.md, BRANDING.md.

Next steps:
• Paste the standard instruction block into Project Settings → Instructions (if not already done)
• Add a folder structure in the UI if you want visual organisation (MAD Runs / Scripts / Case Studies)
• Start your first work session — the project is live-standard

To run a MAD audit at any time: say "MAD run on [topic]"
To update global config: edit PROJECT-LAUNCH-Plus.md in GitHub — all projects inherit it next session
```

---

## NOTES FOR CLAUDE
- Run the wizard automatically if the project has no PROJECT-INDEX.md doc yet
- Never re-run the wizard if PROJECT-INDEX.md already exists (offer to update instead)
- The wizard runs inside the first work session — it IS the first session, not a pre-step
- If the user skips a question, use sensible defaults and note what was assumed
