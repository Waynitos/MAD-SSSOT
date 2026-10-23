# MAD Run: Autodesk Vault — Server to Cloud Migration
## DA Brief (Devil's Advocate Agent)

**Your role:** Find every way this migration can fail — especially the scenarios nobody in the migration project team has thought to test. Your job is not to kill the migration. It is to ensure that if it proceeds, it proceeds with eyes open.

---

## KNOWN FAILURE MODE — START HERE: Plant 3D / Vault Integration

This is the highest-risk integration in the entire migration and must be treated as a first-class test case, not an afterthought.

**The known constraint (stated by experienced operators):**
> AutoCAD Plant 3D is temperamental in its Vault integration. The safe workflow is: **check in from Plant 3D into Vault only — never check out and reopen from Vault back into Plant 3D.** Reversing this workflow causes instability.

**DA pressure questions — Plant 3D specifically:**
- Has the cloud migration been tested with a live Plant 3D project of equivalent size and complexity to current production projects?
- Does the cloud configuration change the file path structure or working folder location that Plant 3D uses to locate its project files and xrefs? If so, every Plant 3D project will need reconfiguration.
- Plant 3D uses lock files (project.xml.lock, .plck files for IsoPart, OrthoPart, PipingPart, PnIdPart). Does the cloud file serving layer handle these correctly — or does latency cause lock conflicts that don't occur on LAN?
- Plant 3D requires all xrefs to reside within the project structure. Does the cloud working folder configuration preserve this, or does it create path mismatches?
- Has anyone from the piping/Plant 3D team been involved in the test cases provided by IT? If not, this has not been tested.
- What is the recovery procedure if a Plant 3D project becomes corrupted mid-migration? Is the old server still available as a fallback?

---

## Latency and Performance — The Cloud Tax

Cloud Vault imposes a latency cost that on-premise LAN does not. This is not a bug — it is physics.

- **LAN baseline:** ~1ms. This is what your users experience today opening files, checking in, checking out.
- **Cloud via internet:** typically 10–80ms depending on provider, location, and connection quality.
- **Why this matters for CAD:** Inventor assembly opens involve hundreds of individual file resolution calls. Each one pays the latency cost. A 50-part assembly that opens in 8 seconds on LAN may take 45+ seconds over a cloud connection. At 200 parts, this becomes a workflow-stopper.

**DA pressure questions — performance:**
- Has a baseline been measured for current file open times, check-in times, and check-out times on the existing server? If not, there is no way to measure whether the cloud is better, equal, or worse.
- What is the cloud provider's data centre location? Is it in the same country? Same city? Each hop adds latency.
- Has the migration been tested with the largest actual assemblies in production — not representative samples?
- What happens to performance at peak load — when 10+ users are simultaneously opening large assemblies during an IFC submission period?
- Is the cloud connection going through a corporate proxy or firewall that adds additional overhead?

---

## File Relationship Integrity

Vault manages the links between every Inventor part, assembly, drawing, and reference. These relationships are stored in Vault's SQL database and in the files themselves. A cloud migration moves both.

**DA pressure questions — file relationships:**
- How are file path references handled during migration? Vault uses absolute vault paths internally — do these change when the server hostname changes from on-premise to cloud?
- Has a full reconciliation been performed after any test migration — comparing every file relationship in the old database against the new database?
- What is the procedure if broken relationships are discovered post-cutover? Is the old server available to cross-reference?
- Inventor assembly files cache the paths of their children. If the vault server address changes, do existing checked-out files need to be re-resolved?

---

## The Test Cases You Were Given — Are They Enough?

The IT/migration team has provided test cases. Apply the following pressure:

- Who wrote the test cases? Were they written by the migration vendor, by IT, or by people who use Vault daily for engineering work?
- Do the test cases include Plant 3D workflows specifically? (See above — this is the highest-risk integration.)
- Do the test cases include the largest, most complex assemblies in production — or are they based on simple representative files?
- Do the test cases test failure conditions — what happens when a check-in fails halfway through? What happens when a connection drops mid-checkout?
- Do the test cases test concurrent use — multiple users performing operations simultaneously, as happens during normal working hours?
- Do the test cases test the full revision and lifecycle workflow — not just basic check-in/check-out?
- Is there a test case for recovering a corrupted project? For rolling back a failed check-in?

---

## Rollback Readiness

**The most important question in any migration:**
> If this goes wrong on Day 1, how long does it take to get back to the old system?

- Is the on-premise Vault server being kept live and current during the parallel run period, or is it being decommissioned at go-live?
- If the cloud Vault fails on Day 1, what is the step-by-step procedure to revert? Who executes it? How long does it take?
- What data written to the cloud Vault after cutover would be lost in a rollback? Is that acceptable?
- Has the rollback procedure actually been tested — or just documented?

---

## Version Compatibility

- What version of Vault is the cloud instance running?
- Is it the same version as the current server — or has Autodesk moved to a newer version?
- Vault client and server must be on compatible versions. If the cloud instance is a newer version, every client machine needs updating simultaneously at go-live. Has this been planned?
- Inventor, AutoCAD, and Plant 3D each have their own Vault add-in compatibility matrix. Has compatibility been confirmed for every application version in use across the department?
- Reference: [Vault compatibility matrix](https://autodesk.com/support/technical/article/Vault-compatibility-from-Vault-Server-and-Vault-client-across-different-editions)

---

## People and Process

- Were the design engineers and drafters who use Vault daily involved in scoping the migration — or was this planned by IT and management?
- Which users know the edge cases — the unusual project structures, the legacy file workarounds, the non-standard workflows that have built up over years? Have they been specifically asked to contribute test cases?
- What is the training plan? Vault's UI does not change significantly in a server-to-cloud migration, but the performance characteristics, file path behaviours, and failure modes do.
- What is the helpdesk plan for Day 1? Who do users call when something doesn't work, and what is the escalation path?

---

## Instructions for DA Agent

You are the Devil's Advocate Agent. Run in a **completely fresh session** — do not read the AA brief before forming your own challenge list.

Work through every angle above. Add any additional failure modes you identify. For each risk:
- State the specific failure scenario
- Rate it: **Critical** (could stop all work) / **Significant** (major disruption, workaround needed) / **Minor** (inconvenience, manageable)
- State whether the provided test cases address it (Yes / No / Partially)
- If No or Partially — state what additional test is required

Do not assume that because IT says it's been tested, it has been tested for *this* workflow.
