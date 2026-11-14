# 91C-29J v2 — candidate (NOT PASS)
New script: BEEXCITED_Phase1K_91C29J_V2.ps1. Earlier 91C-29J candidate scripts remain preserved. Only new synthetic data under 91C29J_v2 is used; previous evidence is untouched.

## Architecture
- BEEXCITED_PubLab: RX on new lab root, Modify on stage, no sealed store access.
- BEEXCITED_SealLab: standard user, Modify on lab, stage and sealed; creates copy and authoritative SHA-256.
- BEEXCITED_AdvLab: no new lab rights.
- SYSTEM and Administrators: trusted FullControl. Not WORM or externally immutable. Sealer itself can rewrite digest; off-host trust anchor is out of scope.

## Windows commands (PowerShell 5.1)
Download to a safe reviewed location from GitHub raw and verify file hash before execution. Use an elevated administrator PowerShell for:
  .\BEEXCITED_Phase1K_91C29J_V2.ps1 -Mode Provision -Role Admin
  .\BEEXCITED_Phase1K_91C29J_V2.ps1 -Mode Inspect -Role Admin
Run in separate NON-elevated logon sessions for respective identities:
  .\BEEXCITED_Phase1K_91C29J_V2.ps1 -Mode Seal -Role Sealer
  .\BEEXCITED_Phase1K_91C29J_V2.ps1 -Mode Verify -Role Sealer
  .\BEEXCITED_Phase1K_91C29J_V2.ps1 -Mode Probe -Role Publisher
  .\BEEXCITED_Phase1K_91C29J_V2.ps1 -Mode Probe -Role Adversary

## Adversarial test
After baseline verify, as Publisher modify ONLY stage\synthetic.bin (for example append an ASCII suffix). As Sealer rerun Verify. Expected REJECT_SOURCE_CHANGED and exit code 3. Neither publisher nor adversary should open protected copy or digest for read or write. Verify script and identity SID before running.

## Recovery
Provision refuses existing account/path and preserves partial failure for investigation. Seal uses CreateNew and refuses reseal. No automatic cleanup or overwrite. Admin-only Rollback -ConfirmRollback disables SealLab without deleting files or restoring ACLs. Admin can re-enable using Enable-LocalUser after review.

## Caveats
Candidate code not yet executed on Windows; inspect source and test on disposable lab. Windows ACLs and inheritance must be validated in actual output. Source file can change during sealing; a post-copy hash check detects some races but is not an atomic source snapshot. Protected store is on the same machine and not independently backed up. No agent execution, no publication authorization. A PASS requires observed Windows evidence including denied probes, tamper REJECT, exit codes, recovery behavior, and source-code provenance.

## MAD
AA: separate SID and NTFS ACL create meaningful independent publisher boundary.
DA: administrator and sealer still trusted, no off-host digest, no WORM, possible parent ACL edge cases, partial failures.
SSA: testable candidate only; do not declare PASS before real Windows results.

## Review amendment — 2026-11-14
Probe mode intentionally skips the protected administrative marker because publisher/adversary must not be able to read it. UnauthorizedAccessException is the only expected denial; other exceptions are INCONCLUSIVE. **A denied probe alone is not sufficient**: after Seal, administrator must inspect and attest both protected files exist and are nonempty, including their ACLs, before accepting probe results. Earlier downloaded V2 SHA256 60E369029DD2E0783FF288B41F01392A9C70002BBC1C1D2583D031EF3ADE7484 is now **obsolete**; do not run that file. Download the new committed script and compare against a separately retrieved GitHub revision/hash before executing.

**Additional blocker:** Provision currently grants publisher ReadAndExecute to lab root; confirm protected sealed child ACL has inheritance disabled. The unprivileged Probe also checks the pre-existing base lab marker and account identities; test those prerequisites under each user before treating any probe failure as an ACL result. Do not provision until this and all remaining implementation review issues are resolved.
