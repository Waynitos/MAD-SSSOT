# 91C-29J — Independent Sealing Authority (candidate; NOT PASS)
Purpose: protect synthetic evidence and its authoritative SHA-256 with a third standard-user SID and a separate NTFS ACL boundary. Existing 91C-29G4/H/I assets are never deleted or modified by these scripts.
## Preconditions
Windows 10 Home, NTFS, elevated Windows PowerShell 5.1 for setup only; use distinct non-elevated tokens for probes. Existing 91C29I source may already be tampered; seal that current state as a fresh synthetic baseline, not as proof of original content. Confirm source access for SealLab: the existing source store ACL does not grant SealLab read. **Before Seal**, the administrator must stage a NEW synthetic copy into a sealer-readable input or explicitly grant source read; do not change the 91C29I frozen artifact ACL. The current role script reads the 91C29I source directly and will therefore fail closed until this dependency is resolved. Do not relax protected-store ACLs to work around it.
## Run (first stage)
Elevated: .\BEEXCITED_Phase1K_91C29J_Setup.ps1 -Mode Provision
Elevated: .\BEEXCITED_Phase1K_91C29J_Setup.ps1 -Mode Inspect
Non-elevated Publisher and Adversary: .\BEEXCITED_Phase1K_91C29J_Role.ps1 -Mode Probe -Role Publisher (or Adversary)
## Stop condition
**Do not run Seal yet** until input staging is separately reviewed and implemented. This initial candidate deliberately fails closed rather than weakening existing 91C29I ACLs. No PASS without Windows transcript evidence and recovery review.
## Recovery
Provision refuses pre-existing account or folder. If partial provisioning occurs, inspect and preserve artifacts; do not rerun blindly. Rollback with -Mode Rollback -ConfirmRollback only disables SealLab and preserves all files, accounts, ACLs and previous milestones. To re-enable after inspection: Enable-LocalUser -Name BEEXCITED_SealLab (elevated). Rollback does not restore ACLs or remove anything.
## MAD
AA: third SID and protected digest separate authority from publisher.
DA: administrator remains trusted; sealer can overwrite if malicious; source access missing; no durable append-only external trust anchor; no authenticated time or anti-replay; backup and crash recovery incomplete.
SSA: candidate only, NOT PASS. Test test and tester: validate denied probes, then deliberately introduce a safe known failure in disposable input and verify REJECT; audit tokens and ACLs independently.
