# BEEXCITED Phase 1K 91C-29G-4 — deliberate rollback
#Requires -RunAsAdministrator
$ErrorActionPreference='Stop'
$root = Join-Path $env:ProgramData 'BEEXCITED-Phase1K-91C29G4-Lab'
$marker = Join-Path $root 'BEEXCITED_LAB_MARKER.txt'
$users = @('BEEXCITED_PubLab','BEEXCITED_AdvLab')
Write-Host '=== BEEXCITED 91C-29G-4 ROLLBACK PREVIEW ==='
Write-Host "Lab folder: $root"
foreach($u in $users) { Get-LocalUser -Name $u -ErrorAction SilentlyContinue | Select-Object Name,Enabled,SID | Format-List }
if(Test-Path -LiteralPath $root) {
    if(-not (Test-Path -LiteralPath $marker)) { throw 'Lab marker missing: refusing directory removal.' }
    Get-Content -LiteralPath $marker | Select-Object -First 2
    Get-ChildItem -LiteralPath $root -Force | Select-Object Name,Mode | Format-Table
}
$answer = Read-Host 'Type REMOVE-BEEXCITED-LAB to delete this disposable folder and the two named accounts'
if($answer -cne 'REMOVE-BEEXCITED-LAB') { Write-Host 'CANCELLED: No changes made.'; exit 0 }
if(Test-Path -LiteralPath $root) {
    if(-not (Test-Path -LiteralPath $marker)) { throw 'Lab marker missing: refusing removal.' }
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
    Write-Host 'PASS: Disposable lab directory removed'
}
foreach($u in $users) {
    $account=Get-LocalUser -Name $u -ErrorAction SilentlyContinue
    if($account) {
        Remove-LocalUser -Name $u -ErrorAction Stop
        Write-Host "PASS: Removed $u"
    }
}
Write-Host 'PHASE1K_STEP91C_29G4_ROLLBACK_COMPLETE'
