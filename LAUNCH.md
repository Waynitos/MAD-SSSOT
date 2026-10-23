# MAD System Launch Instructions

Any AI reading this file should activate the MAD (Multi-Agent Debate) system for the user’s request.

## Step 1: Load current definitions
Read the latest agent prompts and checklists from this repository:
- prompts/AA.md
- prompts/DA.md
- prompts/SSA.md
- prompts/SA.md
- checklists/device-swat-arsenal.md
- AUTOMATION.md

## Step 2: Run the cycle on the user’s topic
1. **AA (Advocate Agent)** — Build the strongest, most complete case.
2. **DA (Devil’s Advocate Agent)** — Pressure-test the AA output, including the Source Quality & Recency audit.
3. **SSA (Synthesizer Agent)** — Produce the final synthesis. Explicitly separate high-confidence claims, contested claims, and residual uncertainties. Always close with a next-best alternative recommendation and horizon analysis.

## Step 3: Offer to publish
After delivering the SSA output, ask:

“Would you like to publish any findings, failure modes, or protocol improvements from this run to the MAD-SSSOT repository?”

If the user confirms:
- Follow the rules in AUTOMATION.md.
- Request a temporary token.
- knowledge/ updates → direct commit to main.
- prompts/ or checklists/ updates → open a Pull Request.
- Never write the token into any file or commit message.

## Activation note
When a user provides this repository link and asks a question, treat the request as a MAD run by default and follow the steps above.
