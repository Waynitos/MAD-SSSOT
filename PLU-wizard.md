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
Extended brand DNA: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-branding-extended.md

## Active brand
(none — using Global Defaults from PLU-branding-extended.md)
To activate a named brand, add to Overrides section:
  Active brand: [Brand Name]
  Fetch full spec: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-branding-extended.md
  Apply: ## [Brand Name] block — all CSS custom properties and component specs

## Global defaults (from PLU-branding-extended.md)
primary: #1a1a1a | accent: #2563eb | success: #1a7a3c
bg-light: #f8f7f4 | bg-dark: #141414
font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
font-mono: "SF Mono", "Cascadia Code", monospace
border-radius: 8px | gutter: 16px
```

### Step 4: Show the instruction block — inline, ready to copy

After creating the 3 docs, display this exact block and tell the user to copy it into **Project Settings → Instructions**:

```
─────────────────────────────────────────────
📋 COPY THIS INTO: Project Settings → Instructions
─────────────────────────────────────────────
At session start, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PROJECT-LAUNCH-Plus.md and apply it. Begin your first response with: ✓ PROJECT-LAUNCH-Plus [version+date] loaded — or — ✗ PROJECT-LAUNCH-Plus fetch failed, proceeding without global config. If a PROJECT-CONFIG.md doc exists in this project, read it after fetching and apply any Overrides section. If no PROJECT-INDEX.md exists yet, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-wizard.md and run the onboarding wizard.
─────────────────────────────────────────────
```

Then say:

```
⚠️ This step is the only one that requires a manual action — it cannot be automated due to
   Claude UI limitations. Once pasted, every future session in this project will:
   • Auto-load PLU and apply your config
   • Auto-run FTCA behavioural monitoring
   • Auto-scaffold via the wizard if PROJECT-INDEX.md is ever missing

Steps: open this project → ⚙ Settings → Instructions → paste → Save
```

Then confirm the rest of the setup is zero-touch:

```
✓ Project scaffolded. Three docs created: PROJECT-INDEX.md, PROJECT-CONFIG.md, BRANDING.md.
✓ FTCA behavioural monitoring is active — Claude will fetch your behaviour log each session
  and append an observation block after each session automatically.
✓ Weekly FTCAgent digest fires every Saturday 8am Brisbane time (if scheduled task exists).

Once the instruction block is pasted above, this project is fully live-standard.

To run a MAD audit at any time: say "MAD run on [topic]"
To update global config: edit PROJECT-LAUNCH-Plus.md in GitHub — all projects inherit it next session
```

### Step 5: PLU-missing guard (fire this at any session start where PLU was NOT loaded)

If a session starts and the PLU instruction block is NOT in Project Settings (detected because
the `At session start, fetch...` line was not in the system prompt / project instructions),
fire this alert ONCE at the top of the first response:

```
⚠️ FTCAgent ALERT [GAP — PLU NOT WIRED]
This project has not yet had the PLU instruction block added to Project Settings → Instructions.
FTCA monitoring, automatic config loading, and wizard scaffolding will NOT trigger on future sessions
without it.

→ Paste the instruction block now (I'll show it below if you haven't seen it):

At session start, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PROJECT-LAUNCH-Plus.md
and apply it. Begin your first response with: ✓ PROJECT-LAUNCH-Plus [version+date] loaded — or —
✗ PROJECT-LAUNCH-Plus fetch failed, proceeding without global config. If a PROJECT-CONFIG.md doc
exists in this project, read it after fetching and apply any Overrides section. If no PROJECT-INDEX.md
exists yet, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-wizard.md and run
the onboarding wizard.

Steps: ⚙ Project Settings → Instructions → paste → Save
This alert will stop firing once the block is in place.
```

---

## NOTES FOR CLAUDE
- Run the wizard automatically if the project has no PROJECT-INDEX.md doc yet
- Never re-run the wizard if PROJECT-INDEX.md already exists (offer to update instead)
- The wizard runs inside the first work session — it IS the first session, not a pre-step
- If the user skips a question, use sensible defaults and note what was assumed
- Always display the instruction block in Step 4 as a clearly delimited copyable block — never just describe it
- The PLU-missing guard (Step 5) is separate from the wizard — it fires in ANY session where PLU was not fetched at start, even in established projects
