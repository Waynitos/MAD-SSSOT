# DA OUTPUT: Devil's Advocate — Autodesk Vault Professional Cloud Migration

**MAD Cycle | Topic: Vault On-Premise to Cloud Migration**
**Role: Devil's Advocate (DA) — Find Every Way This Fails**
**Run date: October 2026**

---

## FRAMING NOTE

The AA gives you reasons to migrate. My job is to ensure you migrate knowing exactly what can kill you. The failure modes below are grounded in how Vault, Inventor, Plant 3D, and AutoCAD actually behave under the conditions this environment creates. Structured from most to least catastrophic.

---

## SECTION 1: PLANT 3D — HIGHEST RISK

### 1.1 Check-In Direction Reversal Triggered by Path/UX Change
**Scenario:** A user, after migration, navigates to a Plant 3D drawing from Vault Explorer or the Vault web client and clicks "Get Latest." This appears identical to the pre-migration workflow. However, the file is now opened directly from the Vault-controlled working folder on the cloud-hosted path — not from within Plant 3D's project environment. The user makes edits and attempts to sync back. The check-in direction is effectively reversed. Plant 3D's project linkage breaks silently.

**Why cloud-specific:** On-premise, users had muscle memory tied to a specific folder structure. Cloud migration changes the displayed server path, how mapped drives appear, and how the Vault working folder is presented. Users who previously had `V:\` now have a UNC path or a different letter. This is enough to cause someone to use the wrong workflow — not from negligence, but because the visual cues changed.

**Additional trigger:** If the Vault working folder path changes as part of migration (standard practice), any existing project.xml referencing the old path becomes invalid. A user opening that project.xml sees an error and may attempt to "fix" it by pulling files from Vault directly — reversing the direction.

**Rating:** CRITICAL
**IT test would catch this:** No — IT tests whether files transfer, not whether workflow direction is preserved
**Required test:** A Plant 3D operator must deliberately attempt the wrong workflow (get from Vault, open in Plant 3D) on a migrated project and document exactly what breaks. This test must run before go-live.

---

### 1.2 Project.xml Hostname Reference Invalidation
**Scenario:** Every Plant 3D project contains a project.xml storing absolute references to project paths, including the SQL Express data source connection string which references the server by hostname. If the cloud Vault server hostname changes from (e.g.) `ENGSERVER01` to `vault.company.cloud.com`, every project.xml in every Plant 3D project may need updating. This is not a Vault migration step — it is a Plant 3D configuration step that Vault migration tooling does not touch.

**What breaks:** When a user opens a Plant 3D project and project.xml still references the old server name, Plant 3D throws a connection error. The project opens in degraded mode. Pipe specs, line numbers, and P&ID data are inaccessible. Isometric generation fails. This is total loss of Plant 3D functionality.

**Compounding factor:** If the Plant 3D data source SQL instance did not move with Vault, Plant 3D must now reach both a cloud Vault server AND an on-premise SQL instance — a split architecture with its own failure modes.

**Rating:** CRITICAL
**IT test would catch this:** Unlikely — IT checks "can I open the file," not "can Plant 3D reach all dependent services"
**Required test:** Open every Plant 3D project on the migrated system with a Plant 3D operator. Confirm Data Manager connects, line list loads, isometric generation runs to completion. Document every project.xml path edit required.

---

### 1.3 Lock File Race Condition Under Cloud Latency
**Scenario:** Plant 3D uses `.plck` lock files to prevent concurrent editing. On LAN, lock file operations are near-instantaneous. At 50ms cloud latency:

- User A opens a P&ID drawing. A `.plck` file is written.
- User B attempts to open the same drawing 200ms later. The lock file write has not propagated. User B does not see the lock. Both users have the file open simultaneously.
- Both check in. One version silently overwrites the other. No conflict warning appears.

**Why this is worse than it sounds:** Plant 3D drawings contain embedded database references, pipe routing data, and xref chains. A silent overwrite corrupts the relational data linking P&IDs to isometrics to line lists. This corruption may not be discovered until an isometric is generated and routing doesn't match the P&ID.

**Rating:** CRITICAL
**IT test would catch this:** No — concurrent timing-sensitive testing is almost never in IT migration test plans
**Required test:** Two users simultaneously open the same Plant 3D drawing on the migrated system and both attempt to edit and check in. Repeat at peak network load. Verify lock file behaviour under each condition.

---

### 1.4 Isometric Generation Output Path Mismatch
**Scenario:** If the Vault working folder path changed post-migration, isogen may write output files to a location outside the Vault working folder. These files exist on the local machine, are never checked into Vault, and are invisible to other users. The user sees no error. Vault shows no new isometric. The next user to request that isometric re-runs generation from scratch.

**Secondary scenario:** Isogen configuration files (.ini files, spec files) reference absolute paths. If those paths changed as part of working folder migration, isogen produces incorrect output silently — incorrect line styles, incorrect spec callouts.

**Rating:** SIGNIFICANT
**IT test would catch this:** No — IT tests whether isogen runs, not whether output lands in the correct Vault location with correct content
**Required test:** Run isogen on a known P&ID on the migrated system. Confirm output appears in Vault under the correct revision. Compare output content against a known-good reference from the on-premise system. Inspect all isogen .ini files for path references before migration.

---

### 1.5 Pipe Spec and Catalog Path Invalidation
**Scenario:** Plant 3D pipe specs are stored in a shared catalog location referenced by the project. If the catalog was on the old server (e.g., `\\ENGSERVER01\PlantCatalog\`) and that path is not replicated to the cloud, every pipe spec lookup fails silently. Users can still draw pipe, but spec validation no longer runs. Non-standard components can be placed without warning. This defect can persist undetected through an entire project phase.

**Rating:** SIGNIFICANT
**IT test would catch this:** Unlikely
**Required test:** Attempt to place a restricted-spec pipe component on the migrated system. Confirm the spec validation fires correctly. Confirm the catalog path in project.xml points to an accessible location.

---

## SECTION 2: INVENTOR SPECIFICS

### 2.1 Assembly Resolution Latency — The Arithmetic Problem
**Scenario:** Inventor resolves assembly files by loading each child component individually on open — a largely sequential process with no parallelisation.

Realistic worst-case calculation:
- Cloud round-trip: 60ms (corporate proxy + firewall + cloud routing — conservative)
- Files per assembly open: 350 (300 parts + 50 xref/reference operations)
- Single user, uncongested: 350 × 60ms = **21 seconds of pure network wait added per open**
- Pre-migration assembly open time for complex assembly: ~60 seconds
- Post-migration single user: **~81 seconds**

Under concurrent deadline load (10 users simultaneously):
- Effective latency per operation: 120ms (contention)
- 350 × 120ms = **42 seconds of network wait**
- Post-migration per user: **~102 seconds per assembly open**

This is not a minor inconvenience. Engineers who wait 100 seconds to open an assembly stop opening assemblies. They work from last-known local copies. Those copies diverge from Vault. Revision control is bypassed in practice even if it works technically.

**Rating:** CRITICAL if effective latency exceeds 60ms; SIGNIFICANT at 30–60ms
**IT test would catch this:** No — IT measures "can the file be accessed," not "how long does an assembly actually take to open under load"
**Required test:** Measure actual round-trip latency from every workstation through the corporate proxy. Time the open of the three largest assemblies with 10 concurrent users simulated. Establish the acceptable threshold before declaring this a blocker.

---

### 2.2 iLogic Rules Referencing Vault Properties Returning Null
**Scenario:** iLogic rules that read Vault properties (revision, lifecycle state, custom properties) use the Vault API through the Vault add-in. If the cloud Vault server URL changes, rules instantiating `VaultConnection` or using `Vault.Application.ActiveVaultServer` may fail silently — returning null or stale data rather than throwing an error.

**Specific failure:** A rule reads the lifecycle state to determine whether to lock a dimension table. On cloud Vault, the property call returns null. The rule treats null as "not released." A released drawing has its locked dimensions silently unlocked. Edits are made. The drawing is issued with incorrect dimensions.

**Rating:** CRITICAL for drawings with iLogic-governed properties
**IT test would catch this:** No — IT does not test iLogic logic, only whether Inventor opens
**Required test:** Identify every iLogic rule that reads a Vault property. Run each rule on the migrated system. Verify returned values against the Vault database directly.

---

### 2.3 Vault Add-In Version Mismatch — Day-One Outage
**Scenario:** Cloud Vault may be provisioned at a newer version than currently on-premise. Vault client add-in for Inventor is version-locked to the server version. Cloud Vault 2025 + workstation Vault 2024 client add-in = connection refused. The user cannot access Vault from Inventor at all.

**The update cascade:** Updating the Vault client add-in requires updating Autodesk Desktop Connector or reinstalling Inventor components. In a corporate environment with limited admin rights, this requires IT involvement for every affected workstation. If this happens at go-live, all users are offline simultaneously.

**Rating:** CRITICAL
**IT test would catch this:** Only if tested on every individual workstation — rarely done; IT tests a reference machine and assumes uniformity
**Required test:** Document the exact Vault client add-in version on every workstation. Cross-reference against Autodesk's compatibility matrix for the cloud Vault server version. Confirm match before go-live.

---

### 2.4 In-Progress Checked-Out Files Orphaned by Working Folder Change
**Scenario:** If the Vault working folder path changes as part of migration, files already checked out to the old path are orphaned. An engineer with a 200-part assembly checked out mid-design cannot check it back in. Vault cannot find the files.

**Worst case:** The engineer manually moves files and re-points Inventor's working folder. During this process, Inventor may re-resolve the assembly against Vault and pull older versions of components, overwriting in-progress work.

**Rating:** SIGNIFICANT
**IT test would catch this:** No — test cases use clean checkouts, not mid-work in-progress states
**Required test:** Before migration, audit all currently checked-out files across all users. Define the explicit procedure for each engineer to resolve checked-out state. Make this a hard migration prerequisite.

---

### 2.5 Pack and Go Performance
**Scenario:** Pack and Go on cloud Vault must traverse the full assembly tree, downloading each file to the local cache, then re-uploading copies as a new Vault package. For a 300-part, 500MB assembly: 500MB download + 500MB upload = 1GB transfer. At 50Mbps effective throughput, this takes 160+ seconds. Previously on LAN: under 10 seconds.

**Rating:** MINOR to SIGNIFICANT depending on usage frequency
**IT test would catch this:** No
**Required test:** Run Pack and Go on the largest assembly in the system on the cloud environment. Measure completion time.

---

## SECTION 3: AUTOCAD SPECIFICS

### 3.1 Xref Resolution After Working Folder Change
**Scenario:** Absolute path xrefs hardcoded to `\\ENGSERVER01\drawings\` break entirely when the server changes. Relative path xrefs that traverse up directories fail if the working folder root changes.

**Silent failure:** AutoCAD opens the drawing. Xref is listed as "Not Found" in the xref palette. The drawing appears blank or partial. Under deadline pressure, the user proceeds without the xref, makes changes, checks in. The revision now has missing references — invisible in Vault, visible only when someone opens the drawing.

**Rating:** SIGNIFICANT
**IT test would catch this:** Unlikely — IT opens a drawing and checks whether it "opens," not whether all xrefs resolved
**Required test:** Open every drawing with xref checking enabled on the migrated system. Generate an xref audit report before and after migration. Any discrepancy is a migration defect.

---

### 3.2 Sheet Set Files (.dst) — Paths Break Silently
**Scenario:** Sheet set files reference individual drawings by absolute path. A sheet set for a project may reference 50 drawings at `\\ENGSERVER01\projects\PJ00193\drawings\`. Post-migration, these paths no longer resolve. The sheet set opens but shows all sheets as missing.

**This is often not discovered until a plot run:** Migration appears successful for weeks until someone attempts a batch plot for a submission. At that point, all sheet set paths fail and the batch plot produces nothing.

**Rating:** SIGNIFICANT
**IT test would catch this:** No — IT does not typically test sheet set batch plotting
**Required test:** Identify all .dst files in the Vault system. Perform a batch plot of each sheet set on the migrated system. Verify output matches pre-migration reference plots.

---

### 3.3 AutoCAD Vault Add-In Version Compatibility
Same version-lock issue as Inventor. AutoCAD 2023 workstations + Vault 2025 server = add-in will not connect. Users lose check-in/check-out from within AutoCAD and must use Vault Explorer as a fallback — slower and more error-prone.

**Rating:** SIGNIFICANT
**Required test:** Same explicit version matrix verification as Inventor, for every workstation.

---

## SECTION 4: PDF AND DOCUMENT FORMATS

### 4.1 Manually-Attached PDF Metadata Loss
**Scenario:** PDFs manually attached as standalone Vault documents (vendor datasheets, transmittals) may be migrated without their Vault property metadata — specifically "Issued To," "Transmittal Number," and custom category fields. Post-migration, searches for "all documents issued to Contractor X" return an incomplete result set. Historical transmittal integrity is compromised.

**Rating:** SIGNIFICANT — compliance risk if project is subject to document control requirements
**IT test would catch this:** No — IT verifies file count, not metadata completeness
**Required test:** Select 50 manually-attached PDFs. After migration, verify all Vault properties match pre-migration values exactly. Use a scripted comparison, not a manual spot-check.

---

### 4.2 DWF/DWFx Visualisation Attachments Dropped
**Scenario:** If migration configuration drops DWF/DWFx visualisation attachments while preserving parent drawings, users viewing drawings in Vault's web viewer see an outdated or blank visualisation — even though the drawing itself is current. Engineers using web review workflows are effectively blind.

**Rating:** MINOR to SIGNIFICANT depending on reliance on web review
**IT test would catch this:** Unlikely
**Required test:** After migration, open 20 random drawings in Vault's web viewer. Confirm the visualisation is current.

---

## SECTION 5: OTHER FORMATS

### 5.1 IFC/STEP/IGES Output Attachment Links Broken
**Scenario:** IFC, STEP, and IGES files stored as output attachments linked to native source files must preserve the parent-child link through migration. If migration breaks these links, Vault no longer knows which native file produced which IFC. Revision history of issued IFC files becomes untraceable.

**Rating:** SIGNIFICANT
**IT test would catch this:** No
**Required test:** Select 10 IFC files that are output attachments. After migration, verify the parent-child link is intact and lifecycle state is unchanged.

---

### 5.2 Excel BOM Item Numbers — If These Change, History Is Permanently Broken
**Scenario:** If the SQL database is rebuilt rather than migrated in-place and Vault item numbers change, every historical BOM export is misaligned with the Vault item master. Engineers comparing historical BOMs to the current Vault state get false differences. This is not recoverable — there is no automated way to reconcile historical Excel exports with new numbering.

**Rating:** CRITICAL if item numbers change — requires explicit pre/post confirmation
**IT test would catch this:** No
**Required test:** Export the item master for three projects before migration. After migration, export again. Compare item numbers row-by-row. Any discrepancy is a critical migration defect.

---

## SECTION 6: DATA INTEGRITY

### 6.1 SQL Relationship Graph — Staged Migration Orphaning
**Scenario:** If the Vault file store and SQL database are migrated at slightly different points in time (common in staged migrations), files checked in during the window may be in the file store but not in SQL, or referenced in SQL but absent from the file store. These orphaned records surface weeks later when someone tries to open an old revision.

**Rating:** CRITICAL
**IT test would catch this:** No — IT runs a SQL restore, confirms it restores without errors, and marks migration complete
**Required test:** Run Vault's built-in consistency check tool (AuditVault or equivalent) after migration. Check for orphaned records, missing files, broken parent-child links. Document output. Resolve all errors before go-live.

---

### 6.2 SQL Config Still Pointing to Old Server Hostname
**Scenario:** Vault's SQL database stores the server hostname in configuration tables. If the cloud server has a different hostname, clients attempting to connect via the Vault add-in may silently be redirected to the old on-premise server. Users can log into the Vault web interface but cannot check in or check out from within Inventor. The add-in falls back to read-only mode. Users assume Vault is "slow" rather than broken.

**Rating:** CRITICAL
**IT test would catch this:** Only if the test is run from a client machine after Vault server config is updated AND someone specifically checks add-in behaviour
**Required test:** After migration, verify Vault server hostname in SQL configuration tables explicitly. Then connect from a representative client machine and confirm check-in and check-out work from within Inventor, AutoCAD, and Plant 3D.

---

### 6.3 Missing Binary Files for Historical Revisions
**Scenario:** During migration, if the file store migration is interrupted and resumed, some intermediate revision versions may have their SQL pointer present but binary file missing. These are invisible in normal use — Vault shows the revision in history but returns an error when a user attempts to open that specific old version. This surfaces at audit time: "produce revision 3 of drawing 47A-P-001." Vault shows it exists. Vault cannot open it. Compliance failure.

**Rating:** CRITICAL
**IT test would catch this:** No — IT does not open old revisions during testing
**Required test:** For a sample of 100 files across all projects, open every revision in Vault history. Confirm each version opens successfully. Automate with a script if possible.

---

## SECTION 7: PERFORMANCE AND LATENCY

### 7.1 Concurrent Peak Load — Full Calculation

| Condition | Latency/op | Files/open | Added wait | Total open time |
|---|---|---|---|---|
| LAN baseline | 1ms | 350 | 0.35s | ~60s |
| Cloud, single user | 60ms | 350 | 21s | ~81s |
| Cloud, 10 concurrent users | 120ms | 350 | 42s | ~102s |

At 102 seconds per assembly open under deadline conditions, engineers stop using Vault workflows and revert to local copies. Revision control fails in practice.

**Rating:** CRITICAL if latency ≥60ms; SIGNIFICANT at 30–60ms
**IT test would catch this:** No
**Required test:** Measure actual round-trip latency from every workstation through the corporate proxy to the cloud server. Time the three largest assemblies with 10 concurrent users simulated. Establish the acceptable threshold before go-live.

---

### 7.2 Corporate Proxy SSL Inspection Overhead
**Scenario:** Vault's cloud connection may route through a corporate proxy performing SSL inspection. SSL inspection adds 20–40ms per connection establishment. Vault makes many short connections (one per file operation) — this overhead compounds multiplicatively. An apparent 30ms round-trip becomes an effective 70ms per file operation.

**Rating:** SIGNIFICANT
**IT test would catch this:** Unlikely — proxy overhead is rarely measured during application testing
**Required test:** Test Vault connection latency with and without proxy to isolate overhead. Request a proxy bypass for Vault traffic if overhead is significant and confirm security policy permits it.

---

## SECTION 8: ROLLBACK AND PARALLEL RUN

### 8.1 Two Weeks of Data Loss If Rollback Required
**Scenario:** If a critical Plant 3D workflow failure is discovered two weeks post-go-live, rollback means reverting to the on-premise server snapshot. Any data created in those two weeks exists only in the cloud Vault. Rolling back means either accepting that loss, or attempting a forward-migration from cloud back to on-premise — not a tested or documented procedure, especially if cloud Vault is a newer version.

**Nobody has planned for option (b).** The rollback plan everyone has documented says "go back to the snapshot." That is a two-week data loss event.

**Rating:** CRITICAL
**IT test would catch this:** The rollback is documented. It has almost certainly not been executed end-to-end.
**Required test:** Execute the rollback procedure in a test environment before go-live. Not document it — run it. Confirm every file is recoverable. Define maximum acceptable data loss and get management sign-off before migration.

---

### 8.2 Parallel Run Data Divergence
**Scenario:** If both on-premise and cloud Vault are live simultaneously, check-ins to one are invisible to the other. After 48 hours, the two systems diverge. Users whose Vault client still points to the old server (because IT missed reconfiguring their machine) create a split revision history. When on-premise is decommissioned, those revisions are lost.

**Rating:** SIGNIFICANT
**Required test:** Set the on-premise Vault to read-only immediately at go-live. Enforce this technically, not just by policy.

---

## SECTION 9: TEST CASE ADEQUACY

### The Single Most Important Question
**Were the IT-written test cases created with input from the engineers who use Plant 3D daily?**

If not, these gaps are structurally absent from the test cases:
- The Plant 3D check-in direction constraint (IT does not know this constraint exists)
- Isometric generation output path validation
- iLogic rule execution with Vault property reads
- Sheet set batch plotting
- Concurrent lock file behaviour under deadline load
- Opening historical revisions from Vault history

**Required action:** A Plant 3D operator and a senior Inventor user must review the test case list and sign off that their critical workflows are covered before testing begins.

**Test data must be production-size:** The largest assembly, the most complex Plant 3D project, the most heavily-xreffed AutoCAD drawing. No synthetic test data.

**Failure condition testing is required:** Mid-operation connection drop during check-in (Inventor), check-in (Plant 3D), isometric generation, and assembly open. Document recovery procedure for each.

---

## SECTION 10: VERSION COMPATIBILITY

Autodesk's compatibility matrix for Vault + Inventor + AutoCAD + Plant 3D is narrow and unforgiving. The cloud Vault version must match the exact client add-in version on every workstation.

**Plant 3D add-in specific risk:** Plant 3D's Vault add-in is the least documented and least tested of the three integrations. Version compatibility between Plant 3D updates and specific Vault server versions has sparse public documentation. Confirm directly with Autodesk before migration.

**Required action:** Document the exact application version on every workstation. Cross-reference against Autodesk's official compatibility matrix. Confirm the cloud Vault server version matches. Get this in writing from the cloud provider.

---

## SUMMARY: CRITICAL FAILURE MODES — GO/NO-GO CONDITIONS

| # | Failure Mode | Rating | IT Test Catches? |
|---|---|---|---|
| 1.1 | Plant 3D check-in direction reversal triggered by path/UX change | CRITICAL | No |
| 1.2 | Project.xml hostname reference invalidation | CRITICAL | No |
| 1.3 | Lock file race condition under cloud latency | CRITICAL | No |
| 2.1 | 300-part assembly open time at concurrent cloud latency | CRITICAL/SIG | No |
| 2.2 | iLogic Vault property reads returning null | CRITICAL | No |
| 2.3 | Vault add-in version mismatch — day-one outage | CRITICAL | Per-machine only |
| 5.2 | SQL item number change breaking BOM history | CRITICAL (if occurs) | No |
| 6.1 | SQL relationship graph orphaning in staged migration | CRITICAL | No |
| 6.2 | SQL config still pointing to old server hostname | CRITICAL | Client-test only |
| 6.3 | Missing binary files for historical revisions | CRITICAL | No |
| 7.1 | Cumulative latency under concurrent peak load | CRITICAL (≥60ms) | No |
| 8.1 | Rollback data loss — untested procedure | CRITICAL | No |
| 9.1 | Test cases written without Plant 3D operator input | CRITICAL (meta) | N/A |

---

## DA CLOSING STATEMENT

This migration is not impossible. But if it proceeds without the tests named above — without Plant 3D operator sign-off on test cases, without a confirmed version compatibility matrix for every workstation, and without a tested rollback — it is a high-probability partial failure that will manifest as a Plant 3D workflow crisis within the first week of live operation.

The failure will not announce itself clearly. It will look like files being slow, then like files being wrong, then like an isometric that doesn't match a P&ID, at which point the root cause will be three migration steps back and very difficult to unwind.

A **conditional Go** is defensible. An **unconditional Go** is not.
