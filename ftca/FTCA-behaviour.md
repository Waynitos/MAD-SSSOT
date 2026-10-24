# FTCA-behaviour.md — FTCAgent Behavioural Log
# Fine Tooth Comb Agent | Central feature-usage telemetry across all Waynito Claude projects
# Auto-appended each session by Claude. Do not edit manually.
# Format: one OBSERVATION block per session, appended at the bottom.

---

## SCHEMA

Each session appends one block:

```
## [YYYY-MM-DD] | Project: [NAME] | Session: [topic/label]
features-used: [comma-separated list]
features-observed-unused: [comma-separated list or —]
patterns-flagged: [free text or —]
alerts-fired: [alert type + one-liner, or —]
tools-used: [Claude tools/capabilities observed in session]
ai-apps-active: [Claude / Grok / other]
notes: [optional free text]
```

---

## OBSERVATION LOG

## 2026-10-24 | Project: FTCAgent PROJECT (FTCA) | Session: Onboarding + Architecture
features-used: Project memory (memory_write/read), PLU fetch (WebFetch), wizard scaffold, GitHub push (gh CLI), artifact design tokens
features-observed-unused: Scheduled Tasks, Claude Design artifact, Artifact capabilities (db/sharing), morning brief skill, Claude in Chrome
patterns-flagged: Manual project setup steps currently require human to paste instruction block into Project Settings — candidate for automation
alerts-fired: —
tools-used: WebFetch, memory_write, memory_read, Bash, Write, add_repo, git clone/push
ai-apps-active: Claude (primary), Grok (parallel project noted)
notes: FTCA architecture defined this session. Weekly digest + in-session alerts both active from next session. Push-to-GitHub pipeline established.
