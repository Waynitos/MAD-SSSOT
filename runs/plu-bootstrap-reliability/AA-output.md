# AA Position — Preserve the URL Fetch Bootstrap Architecture
Date: 2026-10-25
Agent: Advocate (AA)

## Core argument

The fetch architecture is not broken — it is correct in design and broken only in its surface wording.

## Key points

**The single-update problem is real and large.**
Inline definitions in project instructions are static. The moment you update a trigger definition, rename a protocol step, or add a new trigger word (as we did with PHONICSPlus), every project with inline text is immediately out of date. With 10 projects that's a nuisance. With 50 it's unmanageable. With 100+ it's a maintenance disaster that will never be fully resolved. The fetch architecture means one edit to PLU-bootstrap.md propagates to every project on the next session start — zero manual intervention. That leverage is the entire point of a SSSOT.

**The fetch itself works when framed correctly.**
The failure was not the architecture — it was the instruction wording. "MANDATORY FIRST ACTION… follow whatever instructions are there" is exactly what a prompt injection attack looks like to Claude's safety classifier. But Claude fetches external URLs constantly when instructed to do so by legitimate system-level context. The word "MANDATORY" plus "follow whatever is there" triggered the flag. The right fix is to reframe the instruction as a specific, bounded action with a known purpose.

**PHONICSPlus and FTCA already depend on external fetches** and those work because they are user-triggered, purpose-specific actions. The bootstrap fetch is structurally identical — it just needs to be worded the same way: specific URL, specific purpose, bounded scope.

**Real-world conditions where it works:** Claude Code sessions, any session where the instruction is framed as "fetch this specific file to load protocol definitions" rather than "follow whatever you find there."

## Top 3 reasons to preserve the fetch architecture

1. **Single-update propagation** — one GitHub edit reaches every project. Inline text is immediately a fork the moment it's written.
2. **The failure is in wording, not architecture** — fix the instruction frame, not the mechanism.
3. **Abandoning it sets a ceiling on scale** — inline definitions make the system unmaintainable beyond ~10 projects and eliminate the SSSOT guarantee entirely.
