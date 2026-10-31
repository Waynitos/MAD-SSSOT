# SESSION STARTUP PROTOCOL
_Applies to every Claude session working on any project in this repo_

---

## Rule 1 — Fetch before touching

At the start of any session that will modify code or architecture,
fetch the spec doc for the relevant project BEFORE reading any code:

| Project | Spec doc URL |
|---|---|
| Clean Sweeper — Mode 6 | https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/scripts/ilogic/CLEAN_SWEEPER_MODE6_SPEC.md |
| Daily Bible Cross-Reference Reading | https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/projects/Daily-Bible-CrossRef-Reading/SPEC.md |
| (add new projects here) | |

If no spec doc exists for a project yet, create one before writing any code.

---

## Rule 2 — Commit spec updates as you go

Whenever an architectural decision is locked in during a session
(a new flow step, a changed variable, a confirmed constraint, a
form redesign, a new function signature), commit an update to the
spec doc IN THE SAME COMMIT as the code change — not at the end,
not in a later session.

Format: one bullet per decision, dated, in the relevant spec doc.

---

## Rule 3 — Spec doc minimum content

Every project spec doc must contain:

1. **Entry point** — where/how the rule or tool is launched
2. **Step-by-step flow** — numbered, with branch conditions shown
3. **Variable table** — key variables, what they hold, where they are set
4. **Constraints** — environment limits (sandbox blocks, API gaps, etc.)
5. **Commit history** — key milestones with commit hash and one-line description

---

## Rule 4 — Project instructions block

The project instructions block (in Claude's Project settings) must
always list the spec doc URL under "Session startup — authoritative sources".
When a new spec doc is created, update the project instructions block
to include it.

---

## Rule 5 — MAD results always committed

Any MAD cycle output (AA, DA, SSA) is committed to:
`runs/[topic]/AA-output.md`, `DA-output.md`, `SSA-output.md`, `README.md`

Architectural conclusions from the SSA that affect a project's code
are also reflected in that project's spec doc — the SSA is the decision,
the spec doc is the implementation contract.

---

## Spec doc template

When creating a new spec doc, use this structure:

```markdown
# [Project Name] — [Component/Mode] Spec
_Last updated: YYYY-MM-DD_

This document is the authoritative spec for [component].
Any session working on [rule file] must read this before making changes.

---

## Entry point
[How/where this is launched]

## Step-by-step flow
[Numbered steps with branch conditions]

## Key variable notes
| Variable | What it is | Set where |
|---|---|---|

## Constraints
[Environment limits, API gaps, known sandbox blocks]

## Commit history (key milestones)
| Commit | What |
|---|---|
```

---

_This protocol file lives at the root of MAD-SSSOT and is the meta-rule
for all projects in this repo. Update it when the protocol itself changes._
