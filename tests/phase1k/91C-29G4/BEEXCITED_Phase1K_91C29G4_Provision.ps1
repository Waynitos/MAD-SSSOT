# BEEXCITED Phase 1K 91C-29G-4 — controlled disposable identity lab
# Requires elevated Windows PowerShell 5.1; creates two local standard users and a lab directory.
# No changes to existing BEEXCITED source, Codex identities, or protected registry.
# Run rollback script to remove the lab and accounts after tests.
#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
$publisher = 'BEEXCITED_PubLab'
$adversary = 'BEEXCITED_AdvLab'
$root = Join-Path $env:ProgramData 'BEEXCITED-Phase1K-91C29G4-Lab'
$marker = Join-Path $root 'BEEXCITED_LAB_MARKER.txt'
$createdUsers = New-Object 'System.Collections.Generic.List[string]'
$createdRoot = $false
function Assert-Available {
    foreach ($name in @($publisher,$adversary)) {
        if (Get-LocalUser -Name $name -ErrorAction SilentlyContinue) {
            throw "Account '$name' already exists. Refusing to modify an existing identity."
        }
    }
    if (Test-Path -LiteralPath $root) { throw "Lab directory already exists: $root. Refusing to modify existing content." }
}
function New-LabUser([string]$name,[string]$description) {
    Write-Host "Enter a strong, UNIQUE temporary password for $name (not displayed)."
    $password = Read-Host -AsSecureString "Password for $name"
    if ($password.Length -lt 14) { throw 'Password must contain at least 14 characters.' }
    New-LocalUser -Name $name -Password $password -Description $description -PasswordNeverExpires:$false -AccountNeverExpires -ErrorAction Stop | Out-Null
    $createdUsers.Add($name)
    $password.Dispose()
    $user = Get-LocalUser -Name $name
    if (-not $user.Enabled) { throw "Created user $name is disabled." }
    $members = @(Get-LocalGroupMember -Group 'Administrators' -ErrorAction Stop)
    if ($members | Where-Object { $_.SID.Value -eq $user.SID.Value }) { throw "Unexpected administrator membership: $name" }
}
try {
    Assert-Available
    Write-Host '=== 91C-29G-4 PROVISIONING ==='
    Write-Host "LAB_ROOT=$root"
    New-LabUser $publisher 'BEEXCITED disposable publication authority test account'
    New-LabUser $adversary 'BEEXCITED disposable untrusted writer test account'
    New-Item -ItemType Directory -Path $root -ErrorAction Stop | Out-Null
    $createdRoot = $true
    foreach ($folder in @('store','ledger','inbox')) { New-Item -ItemType Directory -Path (Join-Path $root $folder) | Out-Null }
    "BEEXCITED 91C29G4 DISPOSABLE LAB`r`nCreated: $(Get-Date -Format o)" | Set-Content -LiteralPath $marker -Encoding UTF8
    $publisherSid = (Get-LocalUser -Name $publisher).SID
    $adversarySid = (Get-LocalUser -Name $adversary).SID
    $systemSid = New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-18'
    $adminsSid = New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-544'
    $inherit = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
    $prop = [System.Security.AccessControl.PropagationFlags]::None
    $allow = [System.Security.AccessControl.AccessControlType]::Allow
    function Set-LabAcl([string]$path,[bool]$publisherModify,[bool]$adversaryRead) {
        $acl = Get-Acl -LiteralPath $path
        $acl.SetAccessRuleProtection($true,$false)
        foreach ($rule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($rule) }
        foreach ($sid in @($systemSid,$adminsSid)) {
            $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid,[System.Security.AccessControl.FileSystemRights]::FullControl,$inherit,$prop,$allow)))
        }
        if ($publisherModify) {
            $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($publisherSid,[System.Security.AccessControl.FileSystemRights]::Modify,$inherit,$prop,$allow)))
        }
        if ($adversaryRead) {
            $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($adversarySid,[System.Security.AccessControl.FileSystemRights]'ReadAndExecute',$inherit,$prop,$allow)))
        }
        Set-Acl -LiteralPath $path -AclObject $acl
    }
    Set-LabAcl $root $true $true
    Set-LabAcl (Join-Path $root 'store') $true $true
    Set-LabAcl (Join-Path $root 'ledger') $true $true
    Set-LabAcl (Join-Path $root 'inbox') $true $true
    Write-Host '--- LAB ACLS ---'
    & icacls.exe $root (Join-Path $root 'store') (Join-Path $root 'ledger') (Join-Path $root 'inbox')
    Write-Host '--- ACCOUNT STATUS ---'
    Get-LocalUser -Name $publisher,$adversary | Select-Object Name,Enabled,SID | Format-Table -AutoSize
    Write-Host 'PASS: Two non-administrator local accounts provisioned'
    Write-Host 'PASS: Lab ACLs set (publisher Modify; adversary ReadAndExecute)'
    Write-Host 'NOTE: ACL isolation is NOT established until cross-token tests run.'
    Write-Host 'PHASE1K_STEP91C_29G4_PROVISIONED'
} catch {
    Write-Host "PROVISIONING_ERROR=$($_.Exception.Message)"
    Write-Warning 'Provisioning may be partial. Inspect lab and accounts. Run the separately supplied rollback script after checking its targets.'
    throw
}
