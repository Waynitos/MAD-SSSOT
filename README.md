# SIAPlus · MAD-SSSOT

> **Assume Today's Best AI Solution Is Temporary.**

A structured system for validated AI-assisted thinking — adversarial, evolving, and honest about what it doesn't know.

---

## The Four Roles

| Role | Function | What it does |
|------|----------|--------------|
| **SSSOT** | Memory | Remembers what we've learned. The living single source of truth — this repository. |
| **MAD** | Validation | Challenges what we think we know. Structured adversarial critique via AA → DA → SSA. |
| **SIAPlus** | Evolution | Finds what could be better. Continuous re-appraisal of methods, tools, and protocols. |
| **TWEPAN** | Momentum | Celebrates and communicates what we've discovered. *We don't just celebrate wins. We celebrate win-wins.* |

The guiding principle sits above all four:
**Assume Today's Best AI Solution Is Temporary.**
Every output, protocol, and tool in this system is a current best — not a permanent answer.

---

## What MAD Does

MAD (Multi-Agent Debate) improves the completeness and reliability of AI outputs by running every topic through a structured cycle of advocacy, adversarial challenge, and synthesis — using separate AI sessions to avoid single-model anchoring bias.

### The Cycle

```
AA  →  DA  →  SSA
```

- **AA** (Advocate Agent) — builds the strongest, most complete case
- **DA** (Devil's Advocate Agent) — pressure-tests every gap, risk, and failure mode
- **SSA** (Synthesizer Agent) — produces the final tested output: high-confidence findings, residual uncertainties, next-best alternatives, horizon analysis
- **SA** (Super Agent) — researches latest MAD methods and evolves the system when triggered

### Topic Types

Pre-configured MAD briefs in the `topics/` folder:

| Topic | Use for |
|-------|---------|
| `compare-items` | Products, tools, or options head-to-head |
| `price-ferret` | Best price search with hidden cost audit |
| `flight-assassin` | Full itinerary audit — fees, risk, alternatives |
| `research` | Factual or technical deep-dive with source quality audit |
| `script-audit` | Code review OR unsolved problem deep-dive (Mode A / Mode B) |
| `general-mad` | Freeform fallback — use when no other type fits |

---

## Repository Structure

```
LAUNCH.md                                     ← start here to run a MAD session
FRAMEWORK.md                                  ← the four-role framework and guiding principle
AUTOMATION.md                                 ← governance: what commits directly, what needs a PR
scripts/generate-mad-pdf.py                   ← PDF generator for any MAD run
stationery/phewphonics/mad-pdf-layout-spec.md ← LOCKED PDF layout rules (read before touching margins)
prompts/                                      ← AA, DA, SSA, SA system prompts
topics/                                       ← pre-configured topic type briefs
checklists/                                   ← evaluation checklists (Device SWAT Arsenal, etc.)
knowledge/                                    ← living failure modes, protocol updates, horizon notes
runs/                                         ← completed MAD runs — each includes PDF output
```

---

## How to Use This Repo

### Humans
1. Open `LAUNCH.md` — it walks through each step.
2. Or use the **MAD Launcher** (linked from LAUNCH.md) to generate a ready-to-paste brief for your topic type.
3. Run AA, DA, and SSA in separate fresh AI sessions to avoid anchoring bias.
4. Offer to publish useful findings back here after each run.

### AIs arriving at this repo fresh
- Read `LAUNCH.md` first — it is the operational entry point.
- Read the current system prompts from `prompts/`.
- Use `topics/` configs for domain-specific DA angles.
- Use `checklists/` when evaluating devices, code, or processes.
- Treat `knowledge/` as the living source of truth for failure modes and protocol updates.
- To propose improvements: open an Issue or submit a Pull Request per `AUTOMATION.md`.

---

## Design Principles

**Single-model anchoring is the primary failure mode.**
One AI doing AA then DA in the same context window is anchored by its own prior output. Always use separate sessions for AA and DA on anything that matters.

**Source quality is mandatory, not optional.**
The DA runs a source quality audit on every topic: recency, primary vs secondary, single-outlet claims.

**The system audits itself.**
The MAD cycle has already been run on the MAD protocol. Findings are in `knowledge/`. This will happen again.

**Win-wins, not just wins.**
Per TWEPAN: the goal is outcomes that are good for everyone involved — not just optimised for one party or one moment in time.

---

## Current Status

Living system — seeded 23 October 2026.
Prompts, checklists, topic types, and knowledge base active.
