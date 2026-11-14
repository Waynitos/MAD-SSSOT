param([Parameter(Mandatory=$true)][ValidateSet('Baseline','Tamper','Verify')] [string]$Mode)
$ErrorActionPreference='Stop'
$root=Join-Path $env:ProgramData 'BEEXCITED-Phase1K-91C29G4-Lab'
$store=Join-Path $root 'store'
$lab=Join-Path $store '91C29I_synthetic'
$evidence=Join-Path $lab 'sealed_candidate.bin'
$manifest=Join-Path $lab 'baseline.sha256'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$publisher=(Get-LocalUser -Name 'BEEXCITED_PubLab' -ErrorAction Stop).SID.Value
if($identity.User.Value -ne $publisher){throw "WRONG_IDENTITY: $($identity.Name). Must run as BEEXCITED_PubLab"}
if(([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ELEVATED_TOKEN_REJECTED'}
Write-Host "=== BEEXCITED 91C-29I $Mode ==="
Write-Host "IDENTITY=$($identity.Name)"
Write-Host "SID=$($identity.User.Value)"
Write-Host 'SCOPE=DISPOSABLE_SYNTHETIC_ONLY'
Write-Host 'DESIGN=BASELINE_CAPABILITY_TEST_NOT_IMMUTABILITY_PROOF'
function Hash([string]$p){ $sha=[Security.Cryptography.SHA256]::Create(); try { $stream=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read); try { [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','') } finally { $stream.Dispose() } } finally { $sha.Dispose() } }
if($Mode -eq 'Baseline'){
 if(Test-Path -LiteralPath $lab){
   if((Test-Path -LiteralPath $evidence) -and -not (Test-Path -LiteralPath $manifest) -and ([IO.File]::ReadAllText($evidence) -ceq 'BEEXCITED 91C29I SYNTHETIC SEALED CANDIDATE v1')){
     Write-Host 'RECOVERY: Exact synthetic evidence found without manifest; resuming interrupted baseline'
   }else{throw 'LAB_ALREADY_EXISTS: Refusing to overwrite or trust unexpected prior experiment'}
 }else{
   New-Item -ItemType Directory -Path $lab -ErrorAction Stop | Out-Null
   $payload=[Text.Encoding]::UTF8.GetBytes('BEEXCITED 91C29I SYNTHETIC SEALED CANDIDATE v1')
   [IO.File]::WriteAllBytes($evidence,$payload)
 }
 $digest=Hash $evidence
 [IO.File]::WriteAllText($manifest,$digest,[Text.Encoding]::ASCII)
 Write-Host "BASELINE_SHA256=$digest"
 Write-Host 'PASS: New synthetic evidence and baseline digest created'
 Write-Host 'NOTE: Digest manifest shares the publisher-writable store and is NOT an independent trust anchor'
 Write-Host 'PHASE1K_91C29I_BASELINE_COMPLETE'
}elseif($Mode -eq 'Tamper'){
 if(-not (Test-Path -LiteralPath $evidence) -or -not (Test-Path -LiteralPath $manifest)){throw 'BASELINE_MISSING'}
 $before=Hash $evidence
 $expected=[IO.File]::ReadAllText($manifest).Trim()
 if($before -cne $expected){throw 'BASELINE_ALREADY_MISMATCHED: Stop and investigate'}
 try{
  [IO.File]::AppendAllText($evidence,' | PUBLISHER_POST_SEAL_TAMPER')
  Write-Host 'REVIEW: AUTHORISED_PUBLISHER_CAN_MODIFY_POST_SEAL_EVIDENCE'
 }catch{
  Write-Host "PASS: PUBLISHER_TAMPER_DENIED ($($_.Exception.GetType().Name))"
 }
 Write-Host "CURRENT_SHA256=$(Hash $evidence)"
 Write-Host 'PHASE1K_91C29I_TAMPER_COMPLETE'
}else{
 if(-not (Test-Path -LiteralPath $evidence) -or -not (Test-Path -LiteralPath $manifest)){throw 'BASELINE_MISSING'}
 $expected=[IO.File]::ReadAllText($manifest).Trim()
 $actual=Hash $evidence
 Write-Host "BASELINE_SHA256=$expected"
 Write-Host "ACTUAL_SHA256=$actual"
 if($expected -cne $actual){
   Write-Host 'PASS: DIGEST_MISMATCH_DETECTED'
   Write-Host 'PUBLICATION_DECISION=REJECT'
 }else{
   Write-Host 'REVIEW: NO_DIGEST_MISMATCH'
   Write-Host 'PUBLICATION_DECISION=NOT_AUTHORISED_BY_THIS_TEST'
 }
 Write-Host 'WARNING: Publisher can also edit this manifest; verification against it is not a secure independent seal'
 Write-Host 'QUEUE_SUBMISSION=DISABLED'
 Write-Host 'AGENT_EXECUTION=DISABLED'
 Write-Host 'PHASE1K_91C29I_VERIFY_COMPLETE'
}
