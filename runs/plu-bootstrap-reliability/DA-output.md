# DA Position — Abandon the URL Fetch Bootstrap Architecture
Date: 2026-10-25
Agent: Devil's Advocate (DA)

## Core argument

The external URL fetch bootstrap is architecturally unsound and should be abandoned.

## Failure modes

**[CRITICAL] The architecture depends on Claude violating its own safety training.**
Claude's instruction-source boundary rule exists precisely to prevent prompt injection: content that claims authority over Claude's behaviour by directing it to fetch and obey external instructions. The PLU-bootstrap design is structurally indistinguishable from an attack vector. Claude correctly identified it as such in live testing. No amount of wording change fixes this — "MANDATORY FIRST ACTION" made it worse because urgency-signalling is itself a red flag in safety-trained models. You cannot reliably instruct Claude to override a safety heuristic from a user-facing instruction field.

**[CRITICAL] Inconsistent execution makes the system untrustworthy.**
Live testing showed Claude sometimes fetches, sometimes refuses, sometimes reads memory first and answers without fetching. A workflow trigger system that fires 60% of the time is worse than one that never fires — it creates false confidence. In the thousand-projects scenario, some projects will silently not load the bootstrap, users will type RMAD expecting a full MAD cycle, and get a confused response or a hallucinated procedure. There is no error state — just silent non-compliance.

**[HIGH] Every session start adds latency and a network dependency.**
Each project session requires a successful HTTP fetch before Claude can function as designed. Network failures, GitHub downtime, proxy restrictions, or CDN issues silently degrade every session. There is no reliable fallback signal to the user that the bootstrap was skipped.

**[HIGH] The architecture cannot scale without manual intervention.**
Each project requires the instruction to be manually pasted into Settings → Instructions. There is no API to automate this. If the bootstrap instruction needs updating (it already has twice this session), every existing project requires a manual visit. At scale this is not a maintenance burden — it is a structural blocker.

**[MEDIUM] GitHub as an instruction source creates a single point of compromise.**
If the MAD-SSSOT repo is compromised or the bootstrap file is modified maliciously, every project that successfully fetches it will follow the injected instructions. A stolen token or accidental push could propagate bad instructions to every project simultaneously.

## Architectural recommendation

Abandon the URL fetch bootstrap entirely. Trigger definitions belong in the project instructions field as inline text — static, trusted, always present. GitHub remains the SSSOT for MAD run *outputs*, not session *inputs*. Triggered fetches (PHONICSPlus fetching branding, FTCA fetching behaviour log) are user-directed actions, not autonomous instruction-following — Claude accepts these because the user is present and directing the action, not because a startup instruction told it to obey a URL.
