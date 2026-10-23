# Checklist: Enterprise Software Adoption MAD Run

Use this checklist alongside `topics/enterprise-software-adoption.md`. Work through it with your DA output in hand. Every "No" or "Unknown" is a blocking issue before go-live approval.

> *"We don't just Test if it Works — We Test if it Breaks."*

---

## PRE-RUN: Baseline Definition

Before running any MAD session, confirm these have been measured and documented:

- [ ] Current system baseline performance captured (open times, check-in/out round-trips, query speeds)
- [ ] Peak concurrent user count confirmed (normal day AND worst-case deadline period)
- [ ] Full inventory of integrations with the current system documented
- [ ] All file/data types in production catalogued (including edge-case formats and legacy data)
- [ ] Version numbers confirmed: current system + replacement system

---

## AA AGENT: Advocate Check

After AA output, verify the case for adoption meets this bar:

- [ ] Benefits are verified against comparable real-world implementations — not vendor-only claims
- [ ] Total Cost of Ownership over 3 years calculated (licence + implementation + training + ongoing admin + migration)
- [ ] Official vendor migration pathway confirmed as supported for your version and configuration
- [ ] Features in current use confirmed as available in new system (not future roadmap — available now)
- [ ] Success defined in measurable operational terms (times, counts, zero broken items) — not project milestones
- [ ] Realistic time to full operational equivalence stated (not vendor's minimum estimate)

---

## DA AGENT: Devil's Advocate Pressure Test

After DA output, confirm every angle was addressed:

### Implementation Reality
- [ ] Gap between vendor demo environment and actual production environment is documented
- [ ] System tested at **your** actual transaction volumes / file sizes / concurrent user counts
- [ ] End users and power users (not just IT and management) were involved in scoping
- [ ] Day-1 failure scenario has a tested rollback procedure (not just a documented one)
- [ ] Implementation partner's track record with this specific platform version is verified

### The Hall of Shame Tests
- [ ] **FoxMeyer test passed:** System stress-tested at peak load, not average load
- [ ] **National Grid test passed:** System tested under failure conditions and unexpected load spikes
- [ ] **Nike test passed:** The highest-value specific workflows/file types confirmed working (not just common cases)
- [ ] **Cover Oregon test passed:** Scope is manageable — not multiple simultaneous replacements under a deadline
- [ ] **ICL test passed:** Operational staff (not just management) involved in requirements and testing

### Vendor Claims
- [ ] Vendor-promised benefits independently verifiable (not taken on trust)
- [ ] Platform version being implemented is current (not requiring another migration in 18 months)
- [ ] Customisation costs to maintain across future upgrades are quantified
- [ ] Vendor SLA for production outage — actual remediation time confirmed (not just contractual response)

### Data and Integration
- [ ] File/data relationships, metadata, revision history survive migration — tested with production data
- [ ] All integrations with other tools confirmed working in new environment (not assumed)
- [ ] Full migration of production data followed by reconciliation audit completed (not a sample migration)
- [ ] Backup and rollback plan confirmed if data corruption discovered post-cutover

### People and Process
- [ ] Training plan exists with named responsible party and timeline
- [ ] Tribal knowledge in current system identified and documented before migration
- [ ] Resistors specifically consulted — their edge-case knowledge captured

### IT and Security
- [ ] Platform complies with corporate data residency, access control, encryption, and audit logging requirements
- [ ] Network requirements (latency, bandwidth) confirmed — for cloud: latency impact on file-intensive workflows tested
- [ ] Data access controls during migration confirmed (who can see production data during migration window)

---

## INTEGRATION-SPECIFIC: Known High-Risk Integrations

Complete this section for each integration that touches the platform:

| Integration | Tested? | By whom? | Failure mode documented? | Recovery procedure? |
|---|---|---|---|---|
| [e.g. Plant 3D → Vault] | Y/N | [role] | Y/N | Y/N |
| [e.g. Inventor assembly open] | Y/N | [role] | Y/N | Y/N |
| [add rows] | | | | |

**All integrations must be tested by the people who use them daily — not by IT using a sample file.**

---

## TEST CASE ADEQUACY

- [ ] Test cases written or reviewed by end users (not only migration vendor or IT)
- [ ] Test cases include the largest, most complex real production data — not representative samples
- [ ] Test cases include failure conditions (half-completed operations, connection drops mid-process)
- [ ] Test cases include concurrent use (multiple users simultaneously during peak)
- [ ] Test cases include full revision and lifecycle workflows — not just basic operations
- [ ] Test cases include recovery from a corrupted or failed operation
- [ ] All critical, highest-risk integrations have dedicated test cases

---

## ROLLBACK READINESS

- [ ] Old system remains live and current during the full parallel-run period
- [ ] Step-by-step rollback procedure documented, named responsible person, timed
- [ ] Rollback procedure has been **executed in a test environment** — not just documented
- [ ] Data loss window in a rollback scenario is defined and accepted by management
- [ ] Go/No-Go decision maker and sign-off authority are named before go-live

---

## END-USER SIGN-OFF

The following operational roles must validate their workflows before cutover is approved:

| Role | Workflow validated | Sign-off | Date |
|---|---|---|---|
| [e.g. Piping designer — Plant 3D] | Check-in/check-out from Plant 3D | [ ] | |
| [e.g. Senior Inventor user] | Complex assembly open (largest assembly) | [ ] | |
| [e.g. CAD manager] | Admin functions, user management | [ ] | |
| [add rows as needed] | | | |

**Cutover does not proceed until all sign-off boxes are ticked.**

---

## STRANGLER FIG SIGN-OFF: Per-Function Migration

For each function being migrated, record parallel-run period and sign-off:

| Function | Old system retired? | Parallel-run period | Equivalence confirmed? | By whom? |
|---|---|---|---|---|
| [Function A] | [ ] | [X weeks] | [ ] | [role] |
| [Function B] | [ ] | [X weeks] | [ ] | [role] |
| [add rows] | | | | |

**A function is not migrated until its equivalence box is ticked. The old system does not close until every function row is complete.**

---

## SSA OUTPUT REQUIREMENTS

The SSA must produce:

- [ ] Go / No-Go recommendation with explicit stated conditions
- [ ] Strangler Fig cutover plan — function order, parallel-run period per function, cutover trigger per function
- [ ] Rollback trigger definition — specific measurable conditions that require reverting
- [ ] Unresolved risks register — DA issues not answered, ranked Critical / Significant / Minor
- [ ] Named end-user validators per function (this checklist's sign-off table)
- [ ] Recommended minimum parallel-run period per function type

---

*Checklist version: October 2026. Update when new Hall of Shame lessons are added to the topic file.*
