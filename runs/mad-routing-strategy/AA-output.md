# AA Output — MAD Should Auto-Trigger on Eligible Queries

*MAD Run: mad-routing-strategy | Role: Advocate | Date: 2026-10-24*

---

## The Core Problem with Manual-Only Triggering

Decisions don't announce themselves as decisions. When Waynito asks "should I store this Vault data in SQLite or flat files?" — that's a MAD-worthy architectural choice disguised as a quick question. When he asks "is AutoIt or PowerShell better for this file-watcher?" — that's a tool-choice debate that deserves adversarial scrutiny. Under a manual-only system, both get answered with a single perspective in 30 seconds, and the "wrong" choice only surfaces three projects later as technical debt.

The fundamental flaw of wait-and-see MAD is that the person who needs MAD most is the person who doesn't yet know they need it. If Waynito already knew a decision was complex and contested, he'd ask for debate. The auto-router exists precisely for the decisions he doesn't flag.

## Query Types That Clearly Warrant Auto-MAD

A lightweight classifier in PLU needs to catch only a few high-signal patterns:

- **Tool/platform selection** — "should I use X or Y", "what's better for Z"
- **Architecture decisions** — how to structure a system, file layout, data model choices
- **Process design** — workflow design, automation approach, integration strategy
- **Tradeoff questions** — anything with "pros and cons", "worth it?", "is this a good idea?"
- **Reversal risk** — decisions that are expensive or painful to undo (migration paths, naming conventions, schema choices)

These are identifiable by keyword pattern and sentence structure. The classifier doesn't need to be intelligent — it needs to be *adequate*. A PLU instruction block with 15 trigger phrases catches 80% of the cases that matter.

## How the Router Works Without Killing Every Interaction

The objection — "it'll make every session slow" — assumes MAD runs synchronously and fully every time. It doesn't have to.

**Lightweight auto-MAD options:**
1. **Flag and ask** — Router detects an eligible query, fires a one-line prompt: *"This looks like a tradeoff decision — run MAD on it? [Yes / Quick take / Skip]"*. Zero extra time if skipped.
2. **Async MAD** — Router answers immediately with a direct take, then queues a background MAD run. SSA output arrives at session end or next session as an amendment.
3. **Mini-MAD** — Abbreviated AA/DA/SSA inline (no GitHub commit, no full agents) for lower-stakes decisions. Full MAD reserved for flagged high-stakes topics.

Any of these routes more decisions through adversarial scrutiny without blocking the interaction.

## The Real Cost of Skipping MAD

FTCA's behaviour log already shows the pattern: topics that should have been debated once get revisited across 3, 4, 5 sessions. Each revisit costs context reconstruction, re-explaining, re-deciding. One 8-minute MAD run on session 1 eliminates four 20-minute "wait, I thought we decided this" conversations later.

For Waynito specifically — building automation tools across CAD, scripting, and AI frameworks — the decisions compound. A bad architectural call in a Vault automation script doesn't just waste that session; it shapes every script built on top of it.

## Rebutting "Slow and Overkill"

**Slow:** Only if MAD is synchronous and mandatory. With the flag-and-ask or async patterns above, the overhead is one extra line in the response. The user controls the depth.

**Overkill:** The classifier filters out factual questions, how-to requests, and implementation tasks. It targets decision points only. "How do I write a LISP loop?" — straight answer. "Should my LISP automation write to Vault or bypass it?" — MAD candidate.

The overkill objection proves too much: by that logic, we'd never run MAD at all. The question isn't whether some queries don't need MAD — it's whether the ones that do are currently getting it. Under manual-only triggering, most aren't.

## Conclusion

Build the router. Keep it lightweight. Give the user a fast opt-out. The cost of over-triggering is one skipped prompt. The cost of under-triggering is a decision made with one eye open.
