# MAD Run: Autodesk Vault — Server to Cloud Migration
## AA Brief (Advocate Agent)

**Topic type:** Enterprise Software Adoption  
**Date initiated:** October 2026  
**Environment:** Autodesk Vault Professional (server-based) → Cloud-hosted Vault  
**Concurrent users:** [confirm with IT]  
**Integrations in scope:** Autodesk Inventor, AutoCAD Plant 3D, AutoCAD (general), [add others]  
**Peak load period:** [confirm — project deadlines, IFC submissions]  

---

## What the Migration Is Trying to Achieve

Build the strongest honest case for the server-to-cloud migration:

- **Accessibility:** Cloud hosting removes the dependency on VPN or physical network presence. Remote and multi-site users get consistent access without performance degradation tied to VPN tunnel quality.
- **IT overhead reduction:** On-premise Vault server requires dedicated Windows Server infrastructure, SQL Server licensing, backup management, OS patching, and internal IT resource to maintain. Cloud hosting offloads this.
- **Disaster recovery:** Cloud providers offer automated backup, geographic redundancy, and faster recovery time objectives than a single on-premise server.
- **Scalability:** Storage and compute can scale without physical hardware procurement cycles.
- **Version currency:** Cloud-managed instances are typically easier to keep on current Vault versions, reducing the version drift risk that compounds compatibility problems over time.

## What Success Looks Like (Define Before Starting)

Success is **not** "migration complete." Success is:
- Every Vault workflow that exists today works identically post-migration
- Check-in / check-out round-trip time ≤ [current baseline — measure before migration]
- File open times from Vault for Inventor assemblies ≤ [current baseline]
- Plant 3D check-in workflow confirmed stable (see DA brief for detail)
- Zero broken file relationships post-migration, confirmed by reconciliation audit
- All users operational within [X] days with no unresolved blocking issues

---

## Instructions for AA Agent

You are the Advocate Agent. Your job is to build the strongest, most complete case FOR this migration proceeding. Cover:

1. Confirm and expand the benefits above with any additional operational advantages
2. Identify comparable organisations (engineering/manufacturing/design) who have successfully completed this migration and what their experience was
3. Document Autodesk's official migration pathway and supported configurations
4. Confirm which Vault features are fully supported in the cloud configuration vs on-premise
5. State the realistic timeline for a design department of this size to reach full operational equivalence
6. Identify what Autodesk support, documentation, and migration tooling is available

Be thorough and honest. Do not oversell. The DA will challenge every claim — give it clean targets.
