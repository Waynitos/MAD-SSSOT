# PROJECT-LAUNCH-Plus v1.1
## CHANGELOG
- 2026-10-24 v1.1: Added FTCA protocol — behavioural telemetry, in-session alerts, weekly digest
- 2026-10-24 v1.0: Initial release — MAD protocol, branding tokens, git conventions, sub-file index

---

## MAD PROTOCOL
Cycle: AA (Advocate) → DA (Devil's Advocate) → SSA (Synthesizer)
Run AA and DA as parallel fork agents. SSA reads both, produces verdict table + fixes + win-wins.
Commit all outputs to MAD-SSSOT: `runs/[topic]/AA-output.md`, `DA-output.md`, `SSA-output.md`, `README.md`
Repo: https://github.com/Waynitos/MAD-SSSOT

## BRANDING TOKENS
branding-version: v1
primary: #1a1a1a | accent: #2563eb | success: #1a7a3c | warning: #b07d00 | danger: #c0392b
bg-light: #f8f7f4 | bg-dark: #141414 | card: #ffffff | card-dark: #1e1e1e
font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
font-mono: "SF Mono", "Cascadia Code", monospace
border-radius: 8px | spacing-unit: 8px | gutter: 16px
Buttons: rounded-8px, accent fill, white text, hover darken 10%
Panels/cards: 1px border card-border, 8px radius, 16px padding

## GIT CONVENTIONS
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
Claude-Session: [current session URL]
Commit format: type(scope): description

## FTCA PROTOCOL
FTCAgent (Fine Tooth Comb Agent) monitors AI usage across all projects and fires alerts + weekly digests.

### Every session — Claude must:
1. Fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-behaviour.md
2. Scan last 3 entries for REPETITION patterns before responding
3. Monitor session for TOOLING / REPETITION alerts — fire inline if threshold met
4. Append new OBSERVATION block and push to GitHub at session end

### In-session alert format:
```
🔍 FTCAgent ALERT [TYPE]
Observation: [what was detected]
→ Suggestion: [specific redirect]
→ Effort: [Low / Medium / High]
Action: [ Log to FTCA | Run MAD on this | Dismiss ]
```

### Alert types: REPETITION | TOOLING | ADVANCEMENT | GAP | MAD-TRIGGER
Full definitions: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-alerts.md
Behaviour log: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-behaviour.md

### Weekly digest (Saturdays, Brisbane time):
Champion call-outs + enhancement suggestions + AI advancements + open alerts + feature usage summary.

---

## SUB-FILES (fetch on demand)
MAD protocol detail: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-MAD-protocol.md
Wizard (new project onboarding): https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-wizard.md
Branding extended: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-branding-extended.md
Migration tracker: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-migration-status.md
FTCA alerts definition: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-alerts.md
FTCA behaviour log: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/ftca/FTCA-behaviour.md
