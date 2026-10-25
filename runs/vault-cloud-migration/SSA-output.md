# SSA OUTPUT: Synthesiser Verdict — Autodesk Vault Professional Cloud Migration

**MAD Cycle | Topic: Vault On-Premise to Cloud Migration**
**Role: Synthesiser (SSA) — Final Verdict**
**Run date: October 2026**
**AA output:** AA-output.md | **DA output:** DA-output.md

---

## VERDICT: CONDITIONAL GO

**The migration is technically viable and operationally justified — but not yet ready to execute.**

Thirteen critical failure modes have been identified that standard IT migration testing will not catch. Nine of these are specific to Plant 3D and Inventor workflows. Until six named conditions are met, go-live carries unacceptable operational risk.

This is not a "stop and review" verdict. It is a structured set of conditions that, once met, make this migration safe to execute. The conditions are achievable within a defined preparation window.

---

## WHAT BOTH SIDES AGREE ON

| Point | Agreed |
|---|---|
| Vault Professional runs legitimately on cloud VMs | Yes — Autodesk-supported, documented |
| The migration procedure exists and is understood | Yes — ADMS Console wizard, backup/restore |
| All file formats are technically preserved through migration | Yes — SQL + file store both migrate |
| Plant 3D check-in direction constraint exists | Yes — but AA and DA disagree on whether it becomes harder to get right post-migration |
| Latency affects assembly open performance | Yes — the disagreement is on whether AVFS mitigates it sufficiently |
| IT's standard test cases are insufficient for this environment | Yes — both agree on this |

---

## THE CORE DISPUTE: WHERE AA AND DA DIVERGE

### Plant 3D UX Risk (1.1)
**AA position:** The check-in constraint is unchanged; cloud doesn't make it worse.
**DA position:** A working folder path change post-migration changes the visual cues users rely on. Engineers who have muscle memory for a specific flow will encounter a new path presentation and some will attempt the wrong workflow — not from error, from a changed interface.

**SSA finding:** DA is correct on the mechanism; AA is correct that the constraint itself doesn't change. The risk is transitional — highest in the first four weeks post-go-live. Mitigation is explicit: user briefing + a tested "wrong workflow" scenario that confirms what actually happens.

### Latency and Assembly Performance (2.1)
**AA position:** AVFS cache nodes resolve the latency problem — this is the canonical multi-site architecture.
**DA position:** AVFS has not been provisioned. At 60ms round-trip without AVFS, large assembly open times become operationally disruptive.

**SSA finding:** AA's AVFS answer is correct but it is future-tense. The current proposed migration does not include AVFS — it is a straight cloud lift. Without AVFS, the DA calculation is accurate. AVFS must be scoped into the architecture before go-live if latency measurements confirm it is needed.

---

## THE SIX GO/NO-GO CONDITIONS

These are binary — each is either met or it is not. All six must be met before go-live.

---

### CONDITION 1: Latency Measured and Within Threshold

**What:** Measure actual round-trip latency from every workstation through the corporate proxy to the cloud Vault server. Time the three largest assemblies opening with 10 concurrent users simulated.

**Threshold for Go:** Effective latency ≤ 40ms. If latency is 40–70ms: AVFS must be added to the architecture before go-live. If latency > 70ms: escalate to engineering leadership before proceeding — this is a blocker.

**Why IT won't do this by default:** Standard connectivity testing confirms a connection exists, not whether it performs adequately for CAD operations under load.

**Owner:** IT (measurement) + Engineering Lead (threshold sign-off)

---

### CONDITION 2: Plant 3D Test Cases Written and Signed Off by a Plant 3D Operator

**What:** An engineer who uses Plant 3D daily — not IT, not a project manager — must review the full test case list and confirm these scenarios are covered:
- Check-in direction test (attempt the wrong workflow; document what breaks)
- Project.xml path resolution after working folder change
- Lock file behaviour with two users simultaneously editing the same drawing
- Isometric generation output landing in correct Vault location
- Data Manager connection to Plant 3D SQL instance from cloud environment
- Pipe spec catalog path resolution

**Why this condition exists:** DA finding 9.1 — test cases written without Plant 3D operator input structurally miss the failure modes that matter most. This is the meta-risk that makes all other risks harder to catch.

**Owner:** Named Plant 3D operator (sign-off) + IT (execution)

---

### CONDITION 3: Version Compatibility Matrix Confirmed for Every Workstation

**What:** Document the exact Vault client add-in version on every workstation. Cross-reference against Autodesk's official compatibility matrix for the cloud Vault server version. Confirm match. Get confirmation in writing from the cloud provider or Autodesk VAR.

**Why this condition exists:** A version mismatch is a day-one outage for every user simultaneously. This is not a partial failure — it prevents all Vault access from Inventor, AutoCAD, and Plant 3D.

**Owner:** IT

---

### CONDITION 4: Project.xml and Working Folder Path Remediation Plan Documented and Tested

**What:** Before migration:
1. Identify whether the Vault working folder path will change post-migration
2. If yes: identify every project.xml file in every Plant 3D project that references the old path or old server hostname
3. Document the exact remediation steps (which files to edit, what to change, who does it)
4. Execute this remediation in the test migration environment and confirm Plant 3D opens every project successfully

**Why this condition exists:** If project.xml files still reference the old server hostname post-go-live, every Plant 3D project opens in degraded mode. This is total loss of Plant 3D functionality.

**Owner:** IT (path change confirmation) + Plant 3D operator (project.xml audit)

---

### CONDITION 5: Rollback Procedure Executed in Test Environment

**What:** The rollback plan must be run — not documented, not read, run — in a test environment before go-live. Confirm: (a) every file is recoverable from the pre-migration snapshot, (b) the maximum data loss window is defined and accepted in writing by engineering leadership, (c) the procedure for handling files that exist only in cloud Vault during the parallel run is defined.

**Why this condition exists:** An undocumented rollback is a recovery plan. An untested rollback is not. DA finding 8.1 — two weeks of data loss if rollback is required and the procedure has never been rehearsed.

**Owner:** IT (execution) + Engineering Manager (written sign-off on data loss window)

---

### CONDITION 6: Checked-Out Files Cleared Before Migration

**What:** Audit every currently checked-out file across all users. Define the explicit procedure for each engineer to resolve their checked-out state. Make this a hard technical prerequisite — Vault migration begins only after all files are checked in.

**Why this condition exists:** Files checked out to the old working folder path at migration time are orphaned. Inventors with 200-part assemblies checked out mid-design cannot check back in without a complex manual resolution procedure that risks overwriting in-progress work.

**Owner:** Engineering Lead (communication) + IT (audit)

---

## UNRESOLVED RISKS REGISTER

Issues that remain open after conditions are met and must be monitored post-go-live.

| Risk | Rating | Monitoring |
|---|---|---|
| Lock file race under concurrent load | SIGNIFICANT | Track any Plant 3D data conflicts in first 4 weeks |
| iLogic Vault property reads on cloud | SIGNIFICANT | Test all iLogic rules in test environment before go-live |
| Sheet set (.dst) absolute path failures | SIGNIFICANT | Audit and test-plot all sheet sets before go-live |
| DWF/DWFx visualisation currency | MINOR | Spot-check web viewer after migration |
| Isogen output path accuracy | SIGNIFICANT | Run isogen on 5 known P&IDs post-migration; compare to reference |
| Excel BOM item number continuity | CRITICAL (if SQL rebuilt) | Export item master pre/post; compare row by row |
| Historical revision binary file integrity | CRITICAL | Script-test open of old revisions across 100 sample files |
| Plant 3D pipe spec catalog path | SIGNIFICANT | Test spec validation on restricted component placement |
| IFC parent-child link integrity | SIGNIFICANT | Verify 10 IFC output attachments post-migration |

---

## STRANGLER FIG CUTOVER PLAN

Recommended approach: **phased cutover by application, not by project.**

**Week 0 (Preparation):** All six conditions met. Communicate to all engineers. All files checked in. Version compatibility confirmed.

**Week 1–2 (AutoCAD users):** AutoCAD users cut over first. Lowest migration risk, fastest to verify xref resolution. AutoCAD Vault add-in is better-documented than Plant 3D. Any path issues surface here at lowest cost.

**Week 3–4 (Inventor users):** Inventor cut over. Latency monitoring active. Assembly open times tracked. iLogic rules tested. AVFS in place if latency tests required it.

**Week 5–6 (Plant 3D — last):** Plant 3D cut over last. All project.xml remediation complete. Plant 3D operator on site for day-one support. Lock file behaviour monitored actively.

**On-premise Vault:** Set to read-only immediately at each application's cutover, not at go-live of the full system. This prevents divergence without requiring simultaneous cutover of all users.

**Decommission:** 60 days after final Plant 3D cutover, with no open rollback issues, on-premise decommissioned.

---

## ROLLBACK TRIGGERS

If any of the following occur, pause and escalate immediately:

| Trigger | Action |
|---|---|
| Plant 3D check-in fails for any user post-go-live | Pause Plant 3D cutover; investigate path/hostname before proceeding |
| Assembly open time > 90 seconds for any user | Activate AVFS evaluation immediately; do not proceed with Inventor cutover until resolved |
| Any Vault add-in reports "cannot connect to server" from client machine | Full stop; verify SQL hostname config and version matrix |
| Any SQL consistency check error post-migration | Full stop; resolve before any user check-ins |
| Historical revision opens with "file not found" | Log immediately; do not proceed with decommission until all instances resolved |
| Two concurrent Plant 3D check-ins to same file both succeed | Treat as critical data integrity event; audit both versions |

---

## WHAT WAYNITO SHOULD BRING TO TESTING

You are walking into testing to find problems before go-live. Use the DA output as your testing checklist. The highest-value scenarios to test, in priority order:

1. **Plant 3D wrong-direction test:** Open a Plant 3D drawing from Vault Explorer (not from within Plant 3D). Edit it. Try to check in. Document exactly what happens.

2. **Concurrent Plant 3D editing:** Two users open the same drawing simultaneously. Both edit and check in. Does the second user see the first user's lock? What happens to the overwritten version?

3. **Large assembly open timing:** Open the three largest assemblies with 5–10 people simultaneously doing other Vault operations. Record the time from click to fully loaded.

4. **iLogic rule execution:** Find a drawing with an iLogic rule that reads a Vault property. Run the rule on the cloud system. Verify the returned value matches what Vault actually shows.

5. **Isometric generation path:** Run isogen on a P&ID. Confirm the output appears in Vault under the correct revision. Compare content to a known-good reference.

6. **Historical revision open:** Find a drawing with 5+ revisions. Open each old revision from Vault history. Confirm all open successfully.

7. **Sheet set batch plot:** Locate a sheet set (.dst) file. Run batch plot. Confirm all sheets plot successfully.

8. **Version matrix check (before testing begins):** Confirm the cloud Vault server version matches the Vault client add-in on your test machine. If not, stop and escalate before testing anything else.

---

## SSA SUMMARY

| Question | Answer |
|---|---|
| Is this migration technically possible? | Yes |
| Is it officially supported by Autodesk? | Yes |
| Is it ready to execute right now? | No — six conditions not yet met |
| What is the highest single risk? | Plant 3D test cases not written by a Plant 3D operator (Condition 2) |
| What is the right sequencing? | AutoCAD → Inventor → Plant 3D (not simultaneous) |
| Is Plant 3D safe with cloud Vault? | Yes, with correct workflow — but the transition period requires active monitoring |
| Does AVFS resolve the latency problem? | Yes — if it is in scope. Current plan does not include it. |
| What should Waynito do in testing? | Run the 8 scenarios above; document every deviation from on-premise behaviour |

**Final position:** Conditional Go. The migration should proceed — after the six conditions are met, in the application sequence defined above, with rollback triggers defined and plant 3D operator sign-off on test cases.
