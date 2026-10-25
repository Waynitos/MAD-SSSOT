# AA OUTPUT: Advocate — Autodesk Vault Professional Cloud Migration

**MAD Cycle | Topic: Vault On-Premise to Cloud Migration**
**Role: Advocate (AA) — Strongest Case FOR**
**Run date: October 2026**

---

## POSITION STATEMENT

A cloud-hosted Autodesk Vault Professional environment is the correct strategic direction for an engineering/drafting department operating with Inventor, AutoCAD Plant 3D, and AutoCAD. The migration is technically viable, operationally supported, and delivers concrete benefits that on-premise hardware cannot match — particularly around resilience, IT overhead reduction, and multi-site access. The DA will attack; this case is built to withstand it.

---

## 1. GENUINE OPERATIONAL BENEFITS

### 1a. Infrastructure Elasticity
On-premise Vault is frozen to the hardware purchased. Cloud storage expansion is a configuration change — no procurement, no downtime, no physical work. Compute can also be scaled vertically if Vault indexing or SQL query times degrade.

### 1b. Disaster Recovery and Backup Quality
Cloud providers offer native, automated backup services (AWS S3/Glacier, Azure equivalents) vastly superior to typical on-premise tape rotation or NAS backup. Point-in-time restore is achievable for a department where losing Inventor assemblies or issued drawing revisions is catastrophic.

### 1c. Reduced IT Dependency
On-premise Vault requires Windows Server licensing, SQL Server licensing, OS patch management, SQL maintenance plans, antivirus exclusion management, disk health monitoring, and UPS. In a managed cloud or IaaS model, most of this shifts to the provider. Small engineering departments with limited IT staff benefit directly.

### 1d. Global and Remote Access
Cloud-hosted Vault enables engineers working remotely or from a second office to access full Vault Professional functionality — check-in/check-out, lifecycle transitions, BOM queries — without a VPN hairpin back to a physical server room.

### 1e. Multi-Site Replication (AVFS)
Vault Professional's AVFS replication component allows on-premise replica nodes at each office with the Vault Server in the cloud. This is the canonical multi-site Vault architecture and works better with a cloud-hosted central server than a single on-premise server that gives remote sites no replica at all.

---

## 2. AUTODESK'S OFFICIAL SUPPORTED PATHWAY

Autodesk explicitly supports hosting Vault Professional on cloud infrastructure. Documented in AU class MFG229048 ("SkyVault"):
- Vault Workgroup and Vault Professional may be virtualised, subject to licensing
- Both AWS and Azure are supported hosting environments
- Supported topologies: single-server VM, distributed VMs, multi-site with AVFS replicas
- Minimum VM sizes: Azure A3 or larger, AWS m3.large or larger

Migration procedure:
1. Full backup of Vault database and file store
2. Test migration in non-production environment
3. Upgrade in steps no larger than two major versions
4. Engage an Autodesk reseller/VAR for complex migrations

The ADMS Console migration wizard handles internal path updates. Full documentation: [Vault Admin Help — Migrate a Database](https://help.autodesk.com/cloudhelp/2025/ENU/Vault-Admin/files/GUID-7C6C668C-4AC1-4199-BE04-268E5F80B949.htm)

---

## 3. FORMAT AND APPLICATION COMPATIBILITY

### .iam / .ipt / .idw (Inventor)
**Confirmed compatible.** The Vault add-in communicates with the ADMS API over TCP/IP — server location (on-premise vs cloud) is transparent to the client. Existing file relationships, revision history, properties, and lifecycle states are fully preserved through the migration. Post-migration: each workstation must reconfigure Vault client to point to the new server address.

### .dwg / .dxf (AutoCAD)
**Confirmed compatible.** DWG xref paths are resolved by Vault to the local workspace on checkout and re-mapped on check-in — identical behaviour on cloud and on-premise. DXF files are flat managed files with no dependency resolution required.

### AutoCAD Plant 3D (.xml, lock files, piping, isos)
**Compatible with known constraints — constraints are unchanged by cloud hosting.**
The safe workflow (check-IN from Plant 3D to Vault; do not check-OUT back into Plant 3D) is a Plant 3D application behaviour, not a server architecture issue. Cloud hosting does not introduce this constraint — it exists on-premise too. Cloud backup improves the protection of Plant 3D XML project data.

Caveat: Plant 3D project.xml files that reference old server hostnames will need path remediation as part of migration. Lock files (.lck) should be cleared before migration — they are transient state.

### PDF, STEP/IGES, IFC, Excel BOM exports
**All confirmed compatible as flat managed files.** Standard migration includes all. IFC and Excel BOM exports are stored as documents; cloud hosting has no impact on their management.

---

## 4. RECOMMENDED MIGRATION SEQUENCE

**Phase 0 — Pre-migration hygiene (2–4 weeks)**
- Audit all files outside Vault on network shares; check in before migration
- Clear all checked-out files; resolve orphaned check-outs
- Clear Plant 3D lock files
- Verify and finalise Vault folder structure (reorganise before migration, not after)
- Document current Vault server version; determine upgrade path if needed
- Full Vault backup (database + file store) as pre-migration baseline

**Phase 1 — Cloud environment provisioning (1–2 weeks)**
- Provision cloud VM (AWS m5.large or better / Azure D-series equivalent), Windows Server, SQL Server
- Install Vault Professional Server; configure VPN tunnel and firewall rules (TCP 25734, 25735)

**Phase 2 — Test migration (1–2 weeks)**
- Restore database backup to cloud SQL; copy file store; run ADMS Console migration wizard
- Test all client workflows (NOT Plant 3D check-out — check-in only)
- Measure performance baselines from office network over VPN

**Phase 3 — Cutover (planned downtime, target <4 hours)**
- Final incremental backup/restore; update client configurations across all workstations

**Phase 4 — Post-migration validation (1 week)**
- Monitor logs; verify Inventor xref resolution; verify Plant 3D check-in; confirm backup automation

---

## 5. WHAT SUCCESS LOOKS LIKE — MEASURABLE OPERATIONAL TERMS

| Metric | Target |
|---|---|
| Vault check-in/check-out round-trip latency | ≤ on-premise baseline (or within 10% with AVFS) |
| Inventor xref resolution time on file open | ≤ on-premise baseline |
| Vault uptime | ≥ 99.5% (cloud provider SLA-backed) |
| Backup restore test | Full restore validated within 30 days of go-live |
| Zero data loss | Full revision history, lifecycle states, and properties preserved |
| IT maintenance events per quarter | Reduced from on-premise baseline |
| Plant 3D check-in failures | Zero increase vs on-premise baseline |
| Remote worker access | Full Vault client functionality confirmed from off-site |
| Time to recover from server failure | Cloud snapshot restore < 4 hours |

---

## 6. COMPARABLE ORGANISATIONS

- **Shimano Batam (manufacturing):** Migrated Vault Professional to cloud for Japan HQ collaboration ([Autodesk case study](https://www.autodesk.com/ca-fr/support/partners/success-stories/pt-shimano-batam-advantages-in-collaborating-with-japan-hq-in-migrating-of-vault-professional/8453))
- **AU 2023 "Vault Shining on Clouded Days":** Engineering firm migrated Vault Professional to AWS in 2022–2023; session covered performance evaluation
- **IMAGINiT Managed Services client base:** Significant installed base of engineering organisations running Vault cloud under managed service agreements

---

## SUMMARY OF ADVOCATE POSITION

The migration is:
1. **Technically sound** — Vault is the same software stack on a VM as on physical hardware
2. **Officially supported** — Autodesk documents cloud VM deployment topologies and migration procedures
3. **Operationally superior** — backup/DR, scalability, IT overhead
4. **Well-precedented** — engineering organisations of comparable profile have done this
5. **Safely sequenced** — full data preservation, validated test run, defined rollback before cutover
6. **Plant 3D caveat is neutral** — the known constraint is unchanged by cloud hosting; cloud improves backup

The strongest DA objection will be latency for large CAD file operations. The counter is AVFS replication — a local file cache at the office while Vault Server lives in the cloud. This is Vault Professional's canonical multi-site architecture.

---

**Sources:**
- [Vault Upgrade/Migration Strategy — Autodesk](https://autodesk.com/support/technical/article/Strategy-and-path-for-upgrading-Vault)
- [Migrate a Database — Vault Admin Help 2025](https://help.autodesk.com/cloudhelp/2025/ENU/Vault-Admin/files/GUID-7C6C668C-4AC1-4199-BE04-268E5F80B949.htm)
- [Vault Shining on Clouded Days 2023 — Autodesk University](https://www.autodesk.com/autodesk-university/class/Vault-Shining-on-Clouded-Days-2023)
- [Vault Managed Services — IMAGINiT](https://resources.imaginit.com/data-management/vault-managed-services-simplifying-autodesk-vault-operations-in-the-cloud)
- [SkyVault class handout MFG229048 — Autodesk University](https://static.au-uw2-stg.autodesk.com/Class_Handout_MFG229048_SkyVault_The_Quantum_of_Collaboration_Irvin_Hayes.pdf)
- [Shimano Batam Case Study — Autodesk](https://www.autodesk.com/ca-fr/support/partners/success-stories/pt-shimano-batam-advantages-in-collaborating-with-japan-hq-in-migrating-of-vault-professional/8453)
- [Plant 3D and Vault Workshare — AU 2015](https://www.autodesk.com/autodesk-university/class/Workshare-AutoCAD-Plant-3D-and-Vault-Professional-Setup-Synchronization-and-Replication-2015)
