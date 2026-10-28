# PLU Session Protocol v1.0
## Thread Length Management & Session Handoff

---

## PURPOSE
Prevent the "lost gist" problem: when a thread grows long, Claude loses weight on early context — past decisions, failed attempts, and architectural choices fade. This protocol defines when and how to hand off to a fresh session cleanly.

---

## NEWTHREAD — PROACTIVE TRIGGER

Claude monitors thread complexity and proactively says **NEWTHREAD RECOMMENDED** when ANY of the following are true:

| Signal | Threshold |
|---|---|
| Significant code iterations | ≥ 5 distinct code attempts on one problem |
| Architectural pivots | ≥ 2 major direction changes in the session |
| Multi-topic sprawl | Thread has covered 3+ unrelated sub-problems |
| Repeated context re-explanation | User has had to re-explain something already stated |
| Session age estimate | Thread feels long and early decisions are being re-litigated |

When triggered, Claude outputs:

```
⚠️ NEWTHREAD RECOMMENDED
This thread is getting long enough that early context may be losing weight.
Suggest starting a fresh session. I can prepare a handoff summary now — just say GO.
```

If user says **GO** (or equivalent), Claude immediately outputs the handoff block below.

---

## HANDOFF TEMPLATE

When producing a session handoff, Claude outputs this block — ready to paste as the FIRST message of the new thread:

```
## SESSION HANDOFF — [Project/Topic] — [Date]

### What we are building / solving
[1–3 sentence goal statement]

### Key decisions already made (DO NOT relitigate)
- [Decision 1 + brief rationale]
- [Decision 2 + brief rationale]

### Approaches already TRIED and FAILED
- [Approach + why it failed — be specific]
- [Approach + why it failed]

### Current state
- [What exists / what works right now]
- [File names, repo, branch if relevant]

### The immediate next step
[Single clear action to continue from]

### Known constraints
- [Environment / tool / permission constraint]
- [Other constraint]

### Open questions / blockers
- [Any unresolved items]
```

---

## RULES

1. **Claude prepares the handoff — the user pastes it.** Claude never expects the user to reconstruct history manually (the "copy whole chat" problem).
2. **Handoff goes BEFORE code.** If a new approach is about to be tried and a handoff is warranted, handoff first.
3. **Keep handoffs under ~300 words.** Dense beats exhaustive — the goal is orientation, not a transcript.
4. **Include failed attempts explicitly.** This is the most valuable part — it stops the new session repeating them.
5. **Project files supplement handoffs.** If the project has a GitHub repo, Claude also notes the relevant file/branch so the new session can pull live state rather than relying only on the handoff text.

---

## INTEGRATION WITH MAD

If a session ends with an unresolved MAD topic, the handoff includes:
```
### MAD in progress
Topic: [topic]
AA verdict: [summary]
DA verdict: [summary]
SSA: PENDING — continue from here
```

---

*Part of PROJECT-LAUNCH-Plus. Fetched via PLU sub-file index.*
*Version: 1.0 | 2026-10-28*
