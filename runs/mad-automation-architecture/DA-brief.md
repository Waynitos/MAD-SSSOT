# MAD Brief · General MAD
## Subject: Automating the MAD multi-agent workflow — Devil's Advocate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## STEP 2 — DA (Devil's Advocate Agent)

You are the Devil's Advocate Agent (DA). Find every gap, weakness, omission, risk, and failure mode. Be rigorous — do not lightly qualify.

**Context:**
The AA agent has built the case for fully automating a MAD (Multi-Agent Debate) pipeline: AA → DA → SSA, run automatically with no human relay. The user wants to enter a subject, hit Go, and receive a synthesised result while running multiple scenarios in parallel. They are technical (Python, PowerShell, JS) and want this to eventually power background services and apps.

**Pressure angles — attack every one:**

### The automation trap
- Does automating the MAD cycle break the very thing that makes it work? MAD's value comes from genuine cognitive isolation between agents. If the orchestrator feeds Agent 2 the output of Agent 1 automatically, is that still "fresh context" — or is it just a pipeline with extra steps?
- Is there a risk that automation optimises for throughput at the expense of quality? A human pasting between sessions at least reads the output. An automated relay doesn't.
- What happens when an agent produces low-quality output? In a manual flow the human catches it. In an automated flow it propagates to SSA unchecked.

### Technical reality
- API rate limits: running multiple parallel MAD scenarios means 3× the API calls per scenario. What are the actual limits on Anthropic, OpenAI, Grok APIs and what happens when they're hit mid-run?
- Context isolation: most orchestration frameworks share state by default. How hard is it to guarantee genuinely fresh context for each agent — not just a new session object but zero bleed from prior runs?
- Latency: a full AA → DA → SSA cycle may take 3–10 minutes if models are large and prompts are rich. Is "set it and forget it" realistic, or does the user end up checking in anyway?
- Cost: parallel runs multiply API costs. What does 5 simultaneous MAD scenarios cost per day at current API pricing?

### Platform and vendor risks
- xAI (Grok) API: what is the actual production-readiness of the Grok API today? Rate limits, reliability, pricing?
- Open-source orchestration (CrewAI, AutoGen, LangGraph, n8n): what is the real maintenance burden? These frameworks move fast and break things between versions.
- Vendor lock-in: if the whole MAD stack is built on one provider's API and they change pricing, limits, or model behaviour, what's the fallback?

### The UX illusion
- "Zero friction" is harder than it looks. What are all the ways a "set and forget" system creates NEW friction — failed runs with no feedback, results delivered when the user isn't ready, no way to steer mid-run?
- Push notifications and async delivery solve the waiting problem but introduce a new one: context-switching back into a result when you've moved on. How does the UX handle that?
- What does "multiple simultaneous scenarios" look like when 3 of them return at the same time? Is there a dashboard problem — too many results, not enough attention?

### The app-building vision
- The user says they eventually want apps powered by MAD in the background. What are the real architectural requirements for that — it's a different problem than a personal workflow tool.
- What compliance, security, and data residency issues arise when MAD results (which may include sensitive business context) are stored, relayed, or processed by third-party orchestration services?

### Source Quality Audit (mandatory)
- Flag any AA claims about specific API capabilities, rate limits, or framework maturity that may be outdated or unverified
- Flag any single-source claims about orchestration framework quality
- Flag any AA claims about "zero friction" UX that don't account for failure modes

**AA output:** [PASTE AA OUTPUT HERE]
**Original subject:** Automating the MAD multi-agent workflow — zero manual relay, parallel runs, background-powered apps
