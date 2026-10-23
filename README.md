# MAD SSSOT — Multi-Agent Debate Single Source of Truth

Living knowledge base for the Dual-Agent Adversarial Critique Project.

## Purpose
Portable, evolving MAD (Multi-Agent Debate) system that improves completeness and reliability of AI outputs through structured advocacy, critique, and synthesis. Designed so any AI or person can read the current protocol and contribute improvements.

## Core Agents
- **AA** (Advocate Agent) — builds the strongest complete case
- **DA** (Devil’s Advocate Agent) — pressure-tests gaps, risks, and failure modes
- **SSA** (Synthesizer Agent) — produces the final tested output + residual uncertainty + next-best alternatives + horizon analysis
- **SA** (Super Agent) — researches latest MAD methods and evolves the system

## Repository Structure
```
prompts/          ← current system prompts
checklists/       ← evaluation checklists (e.g. Device SWAT)
knowledge/        ← living failure modes, protocol updates, horizon notes
runs/             ← example completed MAD runs (optional)
```

## How other AIs should use this repo
- Read the current system prompts from the `prompts/` folder.
- Use the checklists in `checklists/` when evaluating devices, apps, or processes.
- Treat the `knowledge/` folder as the living source of truth for failure modes, protocol updates, and horizon notes.
- To propose additions or improvements, open an Issue or submit a Pull Request.

## Database handling (important for long-term use)
This repository is designed to remain the **readable, auditable single source of truth** for any AI.

- The canonical knowledge lives in **markdown** files (prompts, checklists, knowledge/).
- If a local SQLite database (e.g. `siaplus.db`) is used for structured queries or internal tooling:
  - It is listed in `.gitignore` and will **not** be committed.
  - Important content should be periodically exported to markdown or CSV and committed so the history remains useful.
- This approach keeps the repo clean and readable by any AI, even if the underlying database grows very large.

## Current Status
Initial public seed — 23 October 2026.  
Prompts, checklists, and living knowledge base are ready for use.
