# MAD Brief · General MAD
## Subject: Automating the MAD multi-agent workflow — removing the human relay

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## STEP 1 — AA (Advocate Agent)

You are the Advocate Agent (AA). Build the strongest, most complete case possible for the subject below. Be thorough — do not balance preemptively.

**Topic framing:**
Build the strongest case for how the MAD (Multi-Agent Debate) workflow — AA → DA → SSA across three fresh AI sessions — can be fully automated so the user never manually copies/pastes between sessions. Cover every viable architectural approach, what each enables, and what the best-in-class implementations look like today.

**Context:**
- Current state: A web launcher (HTML artifact) generates formatted briefs for 7 topic types. The user must copy each step into a separate AI chat manually.
- Desired state: User enters a subject, hits Go, and the full AA → DA → SSA cycle runs automatically and returns a synthesised result — with zero manual relay steps.
- The user wants to run multiple MAD scenarios simultaneously (code audit, product research, flight search, etc.) without babysitting any of them.
- Eventually: these MAD cycles should power apps and services in the background — the user never sees the prompt machinery.
- Platform context: The user is technical (Python, PowerShell, JavaScript, AutoIt) and can deploy simple backends. Budget is not the primary constraint — elegance, reliability, and zero-friction UX are.

**Build the strongest case for:**
1. What is technically possible TODAY for automating multi-agent AI workflows at this scale?
2. Which platforms/APIs (Anthropic, OpenAI, Grok/xAI, Google, open-source) have the best primitives for this — parallel agent runs, fresh context isolation, result aggregation?
3. What does a best-in-class MAD automation stack look like — frontend, orchestration layer, API calls, result delivery?
4. What are the most elegant UX patterns for "set it and forget it" multi-agent runs? (Push notifications, shared dashboard, email digest, artifact that auto-updates?)
5. What open-source orchestration frameworks (LangGraph, CrewAI, AutoGen, Dify, n8n, etc.) are best suited to this pattern?
6. What is the minimum viable implementation that removes ALL manual relay steps?

**Subject:** Automating the MAD multi-agent workflow so the user sets a subject, hits Go, and receives a synthesised AA+DA+SSA result with zero manual steps — while being able to run multiple scenarios in parallel.
