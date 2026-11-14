#Requires -RunAsAdministrator
param([ValidateSet('Provision','Inspect','Rollback')][string]$Mode='Inspect',[switch]$ConfirmRollback)
$ErrorActionPreference='Stop'
$root=Join-Path $env:ProgramData 'BEEXCITED-Phase1K-91C29G4-Lab'
$lab=Join-Path $root '91C29J_seal'
$marker=Join-Path $lab '91C29J_CREATED_BY_SETUP.marker'
$user='BEEXCITED_SealLab'
function Assert-Base {
 if(-not (Test-Path -LiteralPath (Join-Path $root 'BEEXCITED_LAB_MARKER.txt') -PathType Leaf)){throw 'BASE_MARKER_MISSING'}
 foreach($u in @('BEEXCITED_PubLab','BEEXCITED_AdvLab')){if(-not (Get-LocalUser $u -ErrorAction SilentlyContinue)){throw "MISSING_ACCOUNT: $u"}}
}
function Acl($path,$ownerSid,$pubRead){
 $acl=Get-Acl -LiteralPath $path
 $acl.SetAccessRuleProtection($true,$false)
 foreach($r in @($acl.Access)){[void]$acl.RemoveAccessRuleSpecific($r)}
 $inh=[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit'
 $prop=[Security.AccessControl.PropagationFlags]::None
 $allow=[Security.AccessControl.AccessControlType]::Allow
 foreach($s in @('S-1-5-18','S-1-5-32-544')){
  $sid=New-Object Security.Principal.SecurityIdentifier($s)
  $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl',$inh,$prop,$allow)))
 }
 $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($ownerSid,'Modify',$inh,$prop,$allow)))
 if($pubRead){
  $pub=(Get-LocalUser 'BEEXCITED_PubLab').SID
  $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($pub,'ReadAndExecute',$inh,$prop,$allow)))
 }
 Set-Acl -LiteralPath $path -AclObject $acl
}
Assert-Base
if($Mode -eq 'Provision'){
 if(Test-Path -LiteralPath $lab){throw '91C29J_PATH_EXISTS: preserve existing content'}
 if(Get-LocalUser $user -ErrorAction SilentlyContinue){throw 'SEAL_ACCOUNT_EXISTS: preserve existing identity'}
 $password=Read-Host -AsSecureString 'New unique SealLab password (14+ chars)'
 if($password.Length -lt 14){throw 'PASSWORD_TOO_SHORT'}
 New-LocalUser -Name $user -Password $password -Description 'BEEXCITED 91C29J independent synthetic sealing lab' -ErrorAction Stop | Out-Null
 $password.Dispose()
 $sid=(Get-LocalUser $user).SID
 if(@(Get-LocalGroupMember -Group 'Administrators') | Where-Object {$_.SID.Value -eq $sid.Value}){throw 'SEALER_IS_ADMIN'}
 New-Item -ItemType Directory -Path $lab -ErrorAction Stop | Out-Null
 foreach($d in @('sealed','results')){New-Item -ItemType Directory -Path (Join-Path $lab $d) | Out-Null}
 Set-Content -LiteralPath $marker -Value "BEEXCITED 91C29J;SID=$($sid.Value)" -Encoding ASCII
 Acl $lab $sid $false
 Acl (Join-Path $lab 'sealed') $sid $false
 Acl (Join-Path $lab 'results') $sid $false
 Write-Host 'PROVISION_COMPLETE=YES'
}elseif($Mode -eq 'Inspect'){
 if(-not (Test-Path -LiteralPath $marker)){throw '91C29J_MARKER_MISSING'}
 Get-LocalUser $user | Select-Object Name,Enabled,SID
 & icacls.exe $lab (Join-Path $lab 'sealed') (Join-Path $lab 'results')
}elseif($Mode -eq 'Rollback'){
 if(-not $ConfirmRollback){throw 'ROLLBACK_REQUIRES_ConfirmRollback'}
 if(-not (Test-Path -LiteralPath $marker)){throw 'MARKER_MISSING: no changes'}
 # Preserve all evidence and identities. Disable sealer only; manual archival/removal requires separate review.
 Disable-LocalUser -Name $user -ErrorAction Stop
 Write-Host 'ROLLBACK=SEALER_DISABLED; ALL_FILES_PRESERVED; NO_ACL_RESTORE'
}
