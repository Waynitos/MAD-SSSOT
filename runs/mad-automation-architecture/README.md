# MAD Run: Automating the MAD Workflow

**Status:** AA and DA briefs ready. Awaiting runs.
**Initiated:** October 2026
**Topic type:** General MAD
**Stakes:** High — this decision shapes the next phase of the entire SIAPlus stack

## The Question

How do we remove the human as the relay between AA → DA → SSA agents?

The current launcher generates the briefs. The user still has to paste them into three separate chats, then relay outputs between them. That's the bottleneck.

The desired end state: user enters subject, hits Go, full MAD cycle runs, synthesised result is delivered. No manual steps. Multiple scenarios in parallel.

## How to Run

1. Open `AA-brief.md` → paste into a fresh AI session → let it run
2. Copy the AA output
3. Open `DA-brief.md` → paste into a NEW fresh session → paste AA output where indicated → let it run
4. Open `prompts/ssa-prompt.md` → paste into a THIRD fresh session → paste both outputs
5. Save SSA result as `SSA-output.md` in this folder

## Why This Matters

The answer to this MAD run directly determines what we build next:
- A lightweight orchestration script (Python + API calls)?
- A hosted no-code flow (n8n, Dify, Zapier)?
- A proper app backend with a dashboard?
- Something else the AA agent surfaces that we haven't thought of?

Build nothing until the SSA output is in hand.
