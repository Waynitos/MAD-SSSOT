# BEEXCITED — Codex Routing Protocol
Status: proposed operating procedure; no autonomous Codex delegation configured.

## Purpose
Route coding work to the right agent while preserving MAD-SSSOT as the authoritative engineering record.

## Decision rules
- ChatGPT/MAD: ambiguous requirements, feasibility, architecture, engineering trade-offs, acceptance criteria and approval.
- Codex: defined code implementation, multi-file refactoring, shared-function extraction, regression suites, static analysis, reproducible defects, source reviews and offline test execution.
- Joint Codex + MAD + operator: Autodesk Inventor/Vault API changes, COM lifecycle, checkout/ownership, file mutation, recovery, production release and security-sensitive changes.
- Mandatory Codex escalation recommendation: repeated source-only audits with no implementation progress; multiple interconnected source files; repeated regressions; significant test infrastructure needed.
- Never infer that Codex has received a task. A handoff is a recommendation until the user explicitly starts a Codex task or an approved integration confirms launch.

## Routing record fields
Project; objective; code scope; risk tier (low/medium/high); target repository and branch; source-of-truth files; current blockers; Codex recommended?; reason; approvals needed; acceptance tests; evidence links; result; next owner.

## Handoff process
1. Confirm repo and branch, read AGENTS.md and current project docs.
2. Create/update a concise handover describing verified state, goals, non-goals, risks and acceptance.
3. Start Codex manually using the prepared prompt and connected repository environment.
4. Codex performs read-only preflight, proposes a bounded plan, implements only approved scope, runs available tests and returns a reviewable diff/PR.
5. MAD reviews results, separates source/static results from actual Inventor/Vault tests; user approves any integration.
6. Record test outcomes and next action in GitHub. Do not merge to main automatically.

## Property Refresh pilot
Priority: one canonical reusable core and two thin GA wrappers; default preview; APPLY fail-closed. No Copy Design integration or unrelated Existing Target Repair changes. Read the dedicated handover and shared-core contract.

## Future automation
A later SQL-based controller may create routing records and approved Codex tasks via supported integrations, but this file does not create a running agent, schedule, Codex connection or automatic context synchronization.
