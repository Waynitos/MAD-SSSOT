# Topic Type: Enterprise Software Adoption

**Use for:** Evaluating whether to adopt, migrate to, or replace an enterprise platform — ERP, PDM, PLM, cloud migration, or any system that will touch core business operations. Also use when assessing vendor promises, scoping a rollout, or planning a cutover strategy.

> *"We don't just Test if it Works — We Test if it Breaks."*

---

## When To Run This MAD

Run this topic type **before** any of the following decisions are made:
- Committing to a vendor or platform
- Approving a go-live date
- Signing off on a cutover plan that retires the existing system
- Accepting a vendor's test results as your own test results

If the people who will actually use the system daily were **not** part of the scoping or testing process, stop. Run this MAD first.

---

## AA Framing

Build the strongest honest case for the proposed adoption:
- What problem does this platform genuinely solve that the current system cannot?
- What are the verified benefits — not vendor-promised, but demonstrated in comparable environments?
- What is the total cost of ownership over 3 and 5 years (licence, implementation, training, ongoing support, internal admin)?
- Who has successfully made this transition and what did their rollout look like?
- What is the realistic timeline to full operational equivalence with the current system?
- What does success look like — define it in measurable operational terms, not project milestones?

---

## DA Pressure Angles

### Implementation reality
- What is the gap between the vendor demo environment and your actual operational environment?
- Has the platform been tested at **your** transaction volumes, file sizes, and concurrent user counts — not industry averages?
- Who specifically was involved in scoping? Were end users, power users, and edge-case operators in the room — or just IT and management?
- What happens on Day 1 if the new system fails? Is the old system still running? Can you revert in under 4 hours?
- What is the implementation partner's track record with this specific platform and version — not the firm's general reputation?

### The Hall of Shame angles (apply to every adoption)
- **The FoxMeyer test:** Has the system been stress-tested at peak load? FoxMeyer Drug went bankrupt after their SAP rollout couldn't handle 420,000 nightly orders — they tested at average, not peak.
- **The National Grid test:** Has the system been tested under failure conditions and unexpected load spikes — not just normal operation? National Grid's SAP went live just as Hurricane Sandy hit; it had only ever seen fair-weather data.
- **The Nike test:** Are the specific product lines / processes / file types that drive the most business value confirmed to work correctly — not just the common cases? Nike lost ~$100M because Air Jordan orders broke while standard lines worked fine.
- **The Cover Oregon test:** Is the scope of the rollout manageable, or are multiple systems being replaced simultaneously under a deadline? Cover Oregon spent $300M and never processed a single application.
- **The ICL test:** Were the people who actually work on the shop floor / design floor / operations level involved in requirements — or was this designed by management and finance? At Israel Chemical Ltd, factory staff revolted because nobody asked them.

### Vendor claims
- Are the vendor's projected benefits independently verifiable — or taken on trust? Waste Management sued SAP for $500M because promised functionality never appeared.
- What version of the platform is being implemented? Is it current, or a version that will require another migration in 18 months?
- What customisations are required and what do they cost to maintain across future upgrades?
- What does the vendor's SLA look like for a production outage? What is the actual remediation time, not the contractual response time?

### Data and integration
- What happens to file relationships, metadata, revision history, and linked references during migration? Any broken link in a complex assembly can make the entire assembly unusable.
- What integrations exist between the old system and other tools (ERP, design tools, reporting, email)? Which are confirmed to work in the new environment and which are assumed?
- Is there a validated data migration test — not a sample migration, but a full migration of production data followed by a reconciliation audit?
- What is the backup and rollback plan if data corruption is discovered post-cutover?

### Test case adequacy

> *"We don't just Test the Software — We Test the Tester That Tests the Software."*

A test suite is only as good as the people who designed it. The edge cases live with the operators — not with IT, not with the vendor.
- Who wrote the test cases — the migration vendor, IT, or the people who use the system daily?
- Do the test cases cover your highest-risk integrations and largest real-world data — or representative samples?
- Do the test cases include failure conditions (half-completed operations, connection drops, concurrent users)?
- Were any of the test cases written or reviewed by end users — or only by the team doing the migration?

### People and process
- What is the training plan and who bears the productivity loss during the learning curve?
- What tribal knowledge exists in the current system that is not formally documented — and will it survive the migration?
- Which power users are champions and which are resistors? Have the resistors been genuinely heard — they often know the edge cases nobody else does.

### IT and security
- Does the new platform comply with corporate IT policy — data residency, access control, encryption, audit logging?
- What are the network requirements (latency, bandwidth)? For cloud-hosted systems, LAN-level latency (~1ms) is the benchmark; anything higher degrades CAD and file-intensive workflows materially.
- Who has access to production data during the migration? (PG&E's ERP migration exposed 30,000+ customer records for 70 days because a vendor copied live data without security controls.)

---

## SSA Requirements

- **Go / No-Go recommendation** with explicit conditions that must be satisfied before cutover approval
- **Strangler Fig cutover plan** — which functions migrate first, in what order, with what parallel-run period for each
- **Rollback trigger definition** — the specific measurable conditions that would require reverting to the old system
- **Unresolved risks register** — issues the DA identified that have not been answered, ranked by severity
- **End-user sign-off requirement** — names the specific operational roles that must validate each function before it is considered migrated
- **Parallel-run minimum period** — recommended time that old and new systems must run simultaneously before cutover, by function type

---

## The Strangler Fig Methodology

The only safe way to replace a mission-critical system is piece by piece, never all at once.

```
Old System ████████████████████████ 100%
              ↓ migrate Function A
              ↓ parallel run — prove equivalence
              ↓ retire Function A from old system
              ↓ migrate Function B
              ... repeat until old system is empty
New System ░░░░░░░░░░░░░░░░░░░░░░░ 100%
```

**The three rules:**
1. Never retire a function from the old system until the new system has proven it produces identical results at equivalent load
2. Migrate one function at a time — scope creep kills parallel runs
3. If the new system cannot replicate what the old system does, the old system stays

**The opposite of this is a "Big Bang" cutover** — one go-live date, everything switches at once, old system turned off. This is how FoxMeyer went bankrupt.

---

## Checklist
→ checklists/enterprise-software-adoption.md

## Environment note
Always state: the platform being evaluated, current system being replaced, version numbers of both, number of concurrent users, peak transaction/file volumes, and which third-party integrations must survive the migration.
