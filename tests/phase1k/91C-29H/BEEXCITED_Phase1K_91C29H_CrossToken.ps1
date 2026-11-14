param([Parameter(Mandatory=$true)][ValidateSet('Seed','Adversary','Publisher')] [string]$Role)
$ErrorActionPreference='Stop'
$root=Join-Path $env:ProgramData 'BEEXCITED-Phase1K-91C29G4-Lab'
$store=Join-Path $root 'store'
$ledger=Join-Path $root 'ledger'
$inbox=Join-Path $root 'inbox'
$seed=Join-Path $store '91C29H_synthetic_evidence.txt'
$db=Join-Path $ledger '91C29H_synthetic_ledger.txt'
$expected='BEEXCITED_91C29H_SYNTHETIC_ONLY'
$actual=[System.Security.Principal.WindowsIdentity]::GetCurrent()
$who=$actual.Name
$expectedAccount=if($Role -eq 'Adversary'){'BEEXCITED_AdvLab'}else{'BEEXCITED_PubLab'}
if(-not $who.EndsWith("\$expectedAccount",[StringComparison]::OrdinalIgnoreCase)) {throw "WRONG_IDENTITY: $who; expected $expectedAccount"}
Write-Host "=== BEEXCITED 91C-29H $Role ==="
Write-Host "IDENTITY=$who"
Write-Host "SID=$($actual.User.Value)"
Write-Host "ELEVATED=$(([Security.Principal.WindowsPrincipal]$actual).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"
Write-Host 'SCOPE=DISPOSABLE_SYNTHETIC_ONLY'
function Check([string]$label,[scriptblock]$operation,[bool]$shouldSucceed) {
  try {
    & $operation
    if($shouldSucceed) { Write-Host "PASS: $label allowed" }
    else { Write-Host "FAIL: $label unexpectedly allowed" }
  } catch {
    if($shouldSucceed) { Write-Host "FAIL: $label blocked: $($_.Exception.Message)" }
    else { Write-Host "PASS: $label denied ($($_.Exception.GetType().Name))" }
  }
}
if($Role -eq 'Seed') {
  Check 'seed synthetic evidence' { [IO.File]::WriteAllText($seed,$expected) } $true
  Check 'seed synthetic ledger' { [IO.File]::WriteAllText($db,$expected) } $true
  Write-Host 'PHASE1K_91C29H_SEED_COMPLETE'
} elseif($Role -eq 'Adversary') {
  Check 'read evidence' {if([IO.File]::ReadAllText($seed) -cne $expected){throw 'Unexpected evidence content'}} $true
  Check 'read ledger' {if([IO.File]::ReadAllText($db) -cne $expected){throw 'Unexpected ledger content'}} $true
  Check 'overwrite evidence' {[IO.File]::WriteAllText($seed,'TAMPER')} $false
  Check 'overwrite ledger' {[IO.File]::WriteAllText($db,'TAMPER')} $false
  Check 'create store file' {[IO.File]::WriteAllText((Join-Path $store '91C29H_unauthorised.txt'),'TAMPER')} $false
  Check 'create ledger file' {[IO.File]::WriteAllText((Join-Path $ledger '91C29H_unauthorised.txt'),'TAMPER')} $false
  Check 'create inbox file' {[IO.File]::WriteAllText((Join-Path $inbox '91C29H_unauthorised.txt'),'TAMPER')} $false
  Check 'rename evidence' {[IO.File]::Move($seed,(Join-Path $store '91C29H_renamed.txt'))} $false
  Check 'delete evidence' {[IO.File]::Delete($seed); if(-not (Test-Path -LiteralPath $seed)){throw 'DELETE_SUCCEEDED'}} $false
  Write-Host 'PHASE1K_91C29H_ADVERSARY_COMPLETE'
} else {
  Check 'publisher evidence intact' {if([IO.File]::ReadAllText($seed) -cne $expected){throw 'Evidence altered'}} $true
  Check 'publisher ledger intact' {if([IO.File]::ReadAllText($db) -cne $expected){throw 'Ledger altered'}} $true
  Check 'publisher create store file' {$p=Join-Path $store '91C29H_pub_control.txt';[IO.File]::WriteAllText($p,$expected);[IO.File]::Delete($p)} $true
  Write-Host 'PHASE1K_91C29H_PUBLISHER_COMPLETE'
}
