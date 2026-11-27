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

## 2026-10-24 | Project: FTCAgent PROJECT (FTCA) | Session: Full build — FTCA + MAD routing
features-used: Project memory, PLU fetch, GitHub push, git clone, fork agents (MAD AA/DA/SSA), Scheduled Tasks, WebFetch, Write, Edit, Bash, add_repo, register_repo_root
features-observed-unused: Claude Design artifact, Artifact capabilities, morning brief skill, Claude in Chrome, Sheets artifact
patterns-flagged: —
alerts-fired: —
tools-used: WebFetch, memory_write/read, Bash, Write, Edit, Agent (fork ×2), create_trigger, git push
ai-apps-active: Claude (primary), Grok (parallel project noted)
notes: Full FTCA architecture built and shipped. PLU updated to v1.2 with MAD routing (three-layer model). Weekly digest scheduled. MAD run on routing strategy completed — SSA verdict implemented same session. Repo push pipeline confirmed working.

## 2026-10-24 | Project: FTCAgent PROJECT (FTCA) | Session: RMAD test — cobre en el agua (ES)
features-used: RMAD trigger (Layer 1 manual MAD), fork agents (AA+DA parallel), SSA synthesis, GitHub push, Spanish-language query handling
features-observed-unused: Claude Design artifact, Artifact capabilities, Claude in Chrome
patterns-flagged: —
alerts-fired: —
tools-used: Agent (fork ×2), Write, Bash, git push
ai-apps-active: Claude (primary)
notes: First RMAD test in Spanish. Full MAD cycle completed — AA + DA parallel forks, SSA inline synthesis. Committed to runs/cobre-en-el-agua/. RMAD trigger confirmed working end-to-end. MAD pipeline language-agnostic — no issues with Spanish input.

## OBSERVATION 2026-11-13
- Patterns flagged: Claude Design artifact unused across all sessions; Artifact capabilities (db/sharing) consistently unused; Morning brief skill never triggered; Manual project setup still requires human paste step
- Wins noted: Full FTCA architecture built and shipped in first sessions; PLU v1.2 with three-layer MAD routing live; RMAD trigger confirmed working end-to-end including Spanish-language query; Scheduled Tasks activated — weekly digest confirmed functional
- Recommendation issued: Trigger PHONICSPlus + Claude Design artifact together next week to exercise two consistently unused features in one task and produce a reusable branded template

## 2026-11-13 | Project: FTCAgent PROJECT (FTCA) | Session: Weekly FTCA Digest (auto — Scheduled Task)
features-used: GitHub file read (mcp__github__get_file_contents), WebSearch (AI advancement news), Artifact (HTML digest publish), Scheduled Tasks (session triggered by schedule)
features-observed-unused: Claude Design artifact, Artifact database (db), Claude in Chrome, Morning brief skill, Sheets artifact, Artifact sharing/publish
patterns-flagged: Claude Design artifact unused across all 4 logged sessions (3+ weeks); Artifact database capability never used (3+ weeks); Manual project setup step still unautomated; Morning brief skill never triggered (3+ weeks)
alerts-fired: GAP/Claude Design artifact (3+ weeks, HIGH relevance); GAP/Morning brief skill (3+ weeks, HIGH relevance); GAP/Artifact database capability (3+ weeks, MEDIUM relevance)
tools-used: mcp__github__get_file_contents, WebSearch, Artifact (HTML publish), mcp__github__push_files
ai-apps-active: Claude (primary)
notes: Weekly digest auto-fired by Scheduled Task. Digest artifact published at https://claude.ai/artifact/CAbLdkavhreijsdZTLiBZV using PLU branding tokens. Champion calls: FTCA+PLU shipped in one session; first RMAD in Spanish confirmed language-agnostic pipeline; Scheduled Tasks confirmed live (this session is proof). Enhancement recommendations: PHONICSPlus + Design artifact together next session; automate project setup paste step; Sheets artifact for MAD verdict tables. AI advancements sourced this week: Claude Meetings (launched Nov 10 2026), Claude shared spreadsheets/whiteboards (office suite expansion), AI CAD agents for Autodesk parametric design. Push notification sent to Waynito.

## 2026-11-20 | Project: FTCAgent PROJECT (FTCA) | Session: Weekly FTCA Review (auto — Scheduled Task)
features-used: GitHub file read (mcp__github__get_file_contents), GitHub file update (mcp__github__create_or_update_file), Artifact (HTML popup publish), PHONICSPlus tokens applied, Scheduled Tasks (session triggered by schedule)
features-observed-unused: Claude Design artifact, Artifact database (db), Claude in Chrome, Morning brief skill, Sheets artifact
patterns-flagged: Claude Design artifact unused 5 consecutive weeks (HIGH); Morning brief skill unused 5 consecutive weeks (HIGH); Artifact db capability unused 5 consecutive weeks (MED); Manual project setup step still unautomated (MED); PHONICSPlus recommendation from 2026-11-13 not actioned in intervening sessions
alerts-fired: GAP/Claude Design artifact (5 weeks, HIGH — ESCALATED); GAP/Morning brief skill (5 weeks, HIGH — ESCALATED); GAP/Artifact database capability (5 weeks, MED); GAP/PHONICSPlus+Design combo (carry-over recommendation, now week 2)
tools-used: mcp__github__get_file_contents, mcp__github__create_or_update_file, Artifact (HTML publish), TaskCreate, TaskUpdate
ai-apps-active: Claude (primary)
notes: Weekly FTCA auto-fired by Scheduled Task. Branded popup report published as Artifact using PHONICSPlus tokens. Trend assessed as plateauing — core pipeline solid but feature adoption stalled. Push notification sent to Waynito.

## OBSERVATION 2026-11-20
- Patterns flagged: Claude Design artifact unused (5 weeks, HIGH — ESCALATED from last week); Morning brief skill never triggered (5 weeks, HIGH — ESCALATED); Artifact database capability unused (5 weeks, MED); Manual project setup step unautomated (ongoing); PHONICSPlus + Design combo recommendation carried over for second consecutive week without action
- Wins noted: Scheduled Tasks auto-fired correctly two consecutive weeks; RMAD pipeline confirmed language-agnostic; PHONICSPlus tokens correctly applied to both Nov 13 and Nov 20 artifacts; GitHub push pipeline stable; PLU v1.2 three-layer routing live
- Recommendation issued: This week use PHONICSPlus + Claude Design artifact in one real task (any visual output) to close two HIGH-priority gaps in a single session — if Design artifact type is not listed, raise as feedback

## 2026-11-21 | Project: FTCAgent PROJECT (FTCA) | Session: Weekly FTCA Digest (auto — Scheduled Task)
features-used: GitHub file read (mcp__github__get_file_contents), GitHub file update (mcp__github__create_or_update_file), WebSearch (AI advancement news), Artifact (HTML digest publish), Scheduled Tasks (session triggered by schedule)
features-observed-unused: Claude Design artifact, Artifact database (db), Claude in Chrome, Morning brief skill, Sheets artifact
patterns-flagged: Claude Design artifact unused 6 consecutive weeks (HIGH — ESCALATED week 2); Morning brief skill unused 6 consecutive weeks (HIGH — ESCALATED week 2); Artifact database capability unused 6 weeks (MED); PHONICSPlus + Design combo recommendation carried over third consecutive week without action
alerts-fired: GAP/Claude Design artifact (6 weeks, HIGH — ESCALATED week 2); GAP/Morning brief skill (6 weeks, HIGH — ESCALATED week 2); GAP/Artifact database capability (6 weeks, MED)
tools-used: mcp__github__get_file_contents, mcp__github__create_or_update_file, WebSearch, Artifact (HTML publish)
ai-apps-active: Claude (primary)
notes: Weekly digest auto-fired by Scheduled Task (3rd consecutive week — 3-week auto-fire streak confirmed). Digest artifact published at https://claude.ai/artifact/QHhcyuQ3Zc79N4usatY17H using PLU branding tokens. Champion calls: 3-week Scheduled Task auto-fire streak; PHONICSPlus tokens applied to Nov 20 artifact (branding recommendation partially actioned); GitHub pipeline stable. AI advancements: Claude Meetings (workplace discussions→plans, Nov 10), Autodesk Assistant in Inventor 2027.2, Luminary agent-led physics automation (Nov 18), AI CAD agents paper (1000+ params). Push notification sent to Waynito.

## OBSERVATION 2026-11-21
- Patterns flagged: Claude Design artifact unused (6 weeks, HIGH — ESCALATED week 2); Morning brief skill never triggered (6 weeks, HIGH — ESCALATED week 2); Artifact database capability unused (6 weeks, MED); Manual project setup step still unautomated (ongoing); PHONICSPlus + Design combo recommendation carried over third consecutive week without action
- Wins noted: Scheduled Tasks auto-fired correctly three consecutive weeks (3-week streak); PHONICSPlus tokens applied to Nov 20 artifact (branding recommendation partially actioned); GitHub pipeline stable (read + create_or_update_file both working); MAD pipeline language-agnostic confirmed
- Recommendation issued: Close both HIGH alerts in one move — use Claude Design artifact with PHONICSPlus tokens for any visual output this week; also invoke morning brief skill once to establish the habit

## 2026-11-27 | Project: FTCAgent PROJECT (FTCA) | Session: Weekly FTCA Review (auto — Scheduled Task)
features-used: GitHub file read (mcp__github__get_file_contents), GitHub file update (mcp__github__create_or_update_file), Artifact (HTML popup publish), PHONICSPlus tokens applied, Scheduled Tasks (session triggered by schedule)
features-observed-unused: Claude Design artifact, Artifact database (db), Claude in Chrome, Morning brief skill, Sheets artifact
patterns-flagged: Claude Design artifact unused 7 consecutive weeks (HIGH — ESCALATED week 3); Morning brief skill unused 7 consecutive weeks (HIGH — ESCALATED week 3); Artifact database capability unused 7 weeks (MED); PHONICSPlus + Design combo recommendation carried over fourth consecutive week without action
alerts-fired: GAP/Claude Design artifact (7 weeks, HIGH — ESCALATED week 3); GAP/Morning brief skill (7 weeks, HIGH — ESCALATED week 3); GAP/Artifact database capability (7 weeks, MED)
tools-used: mcp__github__get_file_contents, mcp__github__create_or_update_file, Artifact (HTML publish), TaskCreate
ai-apps-active: Claude (primary)
notes: Weekly FTCA auto-fired by Scheduled Task (4th consecutive week — 4-week auto-fire streak confirmed). Branded popup report published as Artifact using PHONICSPlus tokens. Trend assessed as plateauing — core pipeline solid but feature adoption stalled on same 3 features for 7 consecutive weeks. Push notification sent to Waynito.

## OBSERVATION 2026-11-27
- Patterns flagged: Claude Design artifact unused (7 weeks, HIGH — ESCALATED week 3); Morning brief skill never triggered (7 weeks, HIGH — ESCALATED week 3); Artifact database capability unused (7 weeks, MED); Manual project setup step still unautomated (ongoing); PHONICSPlus + Design combo recommendation carried over fourth consecutive week without action
- Wins noted: Scheduled Tasks auto-fired correctly four consecutive weeks (4-week streak — longest streak to date); PHONICSPlus tokens correctly applied to Nov 20 and Nov 21 artifacts (branding pipeline functional); GitHub pipeline stable (read + create_or_update_file both working); MAD pipeline language-agnostic confirmed; RMAD pipeline end-to-end confirmed
- Recommendation issued: Close both HIGH alerts in one move — use Claude Design artifact with PHONICSPlus tokens for any visual output this session; also invoke morning brief skill once to break the 7-week gap — if Design artifact is not listed, raise as explicit feedback to Anthropic

## 2026-11-28 | Project: FTCAgent PROJECT (FTCA) | Session: Weekly FTCA Digest (auto — Scheduled Task)
features-used: GitHub file read (mcp__github__get_file_contents), GitHub file update (mcp__github__create_or_update_file), WebSearch (AI advancement news), Artifact (HTML digest publish), Scheduled Tasks (session triggered by schedule)
features-observed-unused: Claude Design artifact, Artifact database (db), Claude in Chrome, Morning brief skill, Sheets artifact
patterns-flagged: Claude Design artifact unused 8 consecutive weeks (HIGH — ESCALATED week 4); Morning brief skill unused 8 consecutive weeks (HIGH — ESCALATED week 4); Artifact database capability unused 8 weeks (MED); PHONICSPlus + Design combo recommendation carried over fifth consecutive week without action
alerts-fired: GAP/Claude Design artifact (8 weeks, HIGH — ESCALATED week 4); GAP/Morning brief skill (8 weeks, HIGH — ESCALATED week 4); GAP/Artifact database capability (8 weeks, MED)
tools-used: mcp__github__get_file_contents, mcp__github__create_or_update_file, WebSearch, Artifact (HTML publish)
ai-apps-active: Claude (primary)
notes: Weekly digest auto-fired by Scheduled Task (5th consecutive week — 5-week auto-fire streak confirmed, new record). Digest artifact published at https://claude.ai/artifact/Dgyv1WM44vjaBhazW7SQsB using PLU branding tokens. Champion calls: 5-week FTCA auto-fire streak (new record); GitHub pipeline stable across all recent sessions; PHONICSPlus tokens correctly applied to Nov 20 and Nov 21 artifacts. AI advancements: Claude Fable 5.2 flagship model upgrade (Nov 9 2026, improved reasoning/code); Claude Meetings (workplace discussions→plans, launched Nov 10); AI Design Copilot tools expanding in CAD platforms; Claude 3 new built-in tools (spreadsheet/whiteboard/meetings, Nov 2026). Push notification sent to Waynito.

## OBSERVATION 2026-11-28
- Patterns flagged: Claude Design artifact unused (8 weeks, HIGH — ESCALATED week 4); Morning brief skill never triggered (8 weeks, HIGH — ESCALATED week 4); Artifact database capability unused (8 weeks, MED); Manual project setup step still unautomated (ongoing); PHONICSPlus + Design combo recommendation carried over fifth consecutive week without action
- Wins noted: Scheduled Tasks auto-fired correctly five consecutive weeks (5-week streak — new record); GitHub pipeline stable across all recent sessions (read + create_or_update_file both working); PLU branding tokens correctly applied; MAD pipeline language-agnostic confirmed; RMAD pipeline end-to-end confirmed
- Recommendation issued: Claude Design artifact gap has now escalated to week 4 — if Design type is not listed in next session, raise as formal feedback to Anthropic; morning brief skill: trigger once this week to establish habit or remove from watch list; PHONICSPlus + Design combo: combine both in the next visual output task
