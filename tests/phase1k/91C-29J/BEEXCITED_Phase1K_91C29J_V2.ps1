param([Parameter(Mandatory=$true)][ValidateSet('Provision','Inspect','Seal','Verify','Probe','Rollback')][string]$Mode,[ValidateSet('Admin','Sealer','Publisher','Adversary')][string]$Role='Admin',[switch]$ConfirmRollback)
$ErrorActionPreference='Stop'
$root=Join-Path $env:ProgramData 'BEEXCITED-Phase1K-91C29G4-Lab'
$lab=Join-Path $root '91C29J_v2';$stage=Join-Path $lab 'stage';$vault=Join-Path $lab 'sealed'
$marker=Join-Path $lab '91C29J_V2.marker';$src=Join-Path $stage 'synthetic.bin';$copy=Join-Path $vault 'evidence.bin';$digest=Join-Path $vault 'authoritative.sha256'
$names=@{Sealer='BEEXCITED_SealLab';Publisher='BEEXCITED_PubLab';Adversary='BEEXCITED_AdvLab'}
$id=[Security.Principal.WindowsIdentity]::GetCurrent();$isAdmin=([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if($Role -eq 'Admin'){if(-not $isAdmin){throw 'ADMIN_REQUIRED'}}else{
 if($isAdmin){throw 'ELEVATED_TOKEN_REJECTED'}
 if($id.User.Value -ne (Get-LocalUser $names[$Role] -ErrorAction Stop).SID.Value){throw 'WRONG_IDENTITY'}
}
if(-not [IO.File]::Exists((Join-Path $root 'BEEXCITED_LAB_MARKER.txt'))){throw 'BASE_MARKER_MISSING'}
foreach($n in @('BEEXCITED_PubLab','BEEXCITED_AdvLab')){if(-not (Get-LocalUser $n -ErrorAction SilentlyContinue)){throw "MISSING_ACCOUNT=$n"}}
function Hash($path){
 $sha=[Security.Cryptography.SHA256]::Create()
 try{$f=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
  try{[BitConverter]::ToString($sha.ComputeHash($f)).Replace('-','')}finally{$f.Dispose()}
 }finally{$sha.Dispose()}
}
function Acl($path,$pub,$seal,$pubRead=$false){
 $a=Get-Acl -LiteralPath $path;$a.SetAccessRuleProtection($true,$false)
 foreach($r in @($a.Access)){[void]$a.RemoveAccessRuleSpecific($r)}
 $entries=@(@('S-1-5-18','FullControl'),@('S-1-5-32-544','FullControl'))
 if($pub){$entries+= ,@((Get-LocalUser BEEXCITED_PubLab).SID.Value,'Modify')}
 if($seal){$entries+= ,@((Get-LocalUser BEEXCITED_SealLab).SID.Value,'Modify')}
 if($pubRead){$entries+= ,@((Get-LocalUser BEEXCITED_PubLab).SID.Value,'ReadAndExecute')}
 foreach($e in $entries){
  $sid=New-Object Security.Principal.SecurityIdentifier($e[0])
  $rule=New-Object Security.AccessControl.FileSystemAccessRule($sid,$e[1],[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
  $a.AddAccessRule($rule)
 }
 Set-Acl -LiteralPath $path -AclObject $a
}
if($Mode -ne 'Provision'){
 if(-not [IO.File]::Exists($marker)){throw 'V2_MARKER_MISSING'}
 if([IO.File]::ReadAllText($marker).Trim() -cne 'BEEXCITED_91C29J_V2_SYNTHETIC_ONLY'){throw 'MARKER_MISMATCH'}
}
Write-Host "MODE=$Mode ROLE=$Role IDENTITY=$($id.Name)"
switch($Mode){
 Provision {
  if($Role -ne 'Admin'){throw 'ADMIN_REQUIRED'}
  if(Test-Path -LiteralPath $lab){throw 'LAB_ALREADY_EXISTS'}
  if(Get-LocalUser BEEXCITED_SealLab -ErrorAction SilentlyContinue){throw 'SEALER_ALREADY_EXISTS'}
  $pw=Read-Host -AsSecureString 'New unique sealer password (14+ characters)'
  if($pw.Length -lt 14){throw 'PASSWORD_TOO_SHORT'}
  try{New-LocalUser BEEXCITED_SealLab -Password $pw -Description '91C29J v2 independent synthetic sealer' -ErrorAction Stop|Out-Null}finally{$pw.Dispose()}
  $sid=(Get-LocalUser BEEXCITED_SealLab).SID.Value
  if(@(Get-LocalGroupMember -Group Administrators)|Where-Object {$_.SID.Value -eq $sid}){throw 'SEALER_IS_ADMIN'}
  [void][IO.Directory]::CreateDirectory($lab);[void][IO.Directory]::CreateDirectory($stage);[void][IO.Directory]::CreateDirectory($vault)
  Acl $lab $false $true $true;Acl $stage $true $true;Acl $vault $false $true
  [IO.File]::WriteAllBytes($src,[Text.Encoding]::UTF8.GetBytes('BEEXCITED 91C29J V2 SYNTHETIC EVIDENCE v1'))
  Acl $src $true $true
  [IO.File]::WriteAllText($marker,'BEEXCITED_91C29J_V2_SYNTHETIC_ONLY',[Text.Encoding]::ASCII)
  Write-Host "STAGED_SHA256=$(Hash $src)";Write-Host 'PROVISIONED=YES'
 }
 Inspect {
  if($Role -ne 'Admin'){throw 'ADMIN_REQUIRED'}
  Get-LocalUser BEEXCITED_PubLab,BEEXCITED_AdvLab,BEEXCITED_SealLab|Select-Object Name,Enabled,SID|Format-Table -AutoSize
  & icacls.exe $lab $stage $vault $src
  if($LASTEXITCODE -ne 0){throw 'ACL_INSPECTION_FAILED'}
  Write-Host "SOURCE_SHA256=$(Hash $src)"
  Write-Host "SEALED_EXISTS=$([IO.File]::Exists($copy)) DIGEST_EXISTS=$([IO.File]::Exists($digest))"
 }
 Seal {
  if($Role -ne 'Sealer'){throw 'SEALER_REQUIRED'}
  if([IO.File]::Exists($copy) -or [IO.File]::Exists($digest)){throw 'SEAL_EXISTS_NO_RESEAL'}
  $bytes=[IO.File]::ReadAllBytes($src);if($bytes.Length -gt 1048576){throw 'SOURCE_TOO_LARGE'}
  $sha=[Security.Cryptography.SHA256]::Create()
  try{$h=[BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','')}finally{$sha.Dispose()}
  $f=[IO.File]::Open($copy,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$f.Write($bytes,0,$bytes.Length)}finally{$f.Dispose()}
  if((Hash $copy) -cne $h){throw 'COPY_MISMATCH'}
  $f=[IO.File]::Open($digest,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$b=[Text.Encoding]::ASCII.GetBytes($h+[Environment]::NewLine);$f.Write($b,0,$b.Length)}finally{$f.Dispose()}
  if((Hash $src) -cne $h){throw 'SOURCE_CHANGED_DURING_SEAL'}
  Write-Host "AUTHORITATIVE_SHA256=$h";Write-Host 'SEAL_COMPLETE=YES'
 }
 Verify {
  if($Role -ne 'Sealer'){throw 'SEALER_REQUIRED'}
  $h=[IO.File]::ReadAllText($digest).Trim()
  if($h -cnotmatch '^[A-F0-9]{64}$'){throw 'INVALID_DIGEST'}
  $a=Hash $copy;$b=Hash $src
  Write-Host "REFERENCE_SHA256=$h SEALED_SHA256=$a SOURCE_SHA256=$b"
  if($a -cne $h){Write-Host 'PUBLICATION_DECISION=REJECT_PROTECTED_COPY';exit 2}
  if($b -cne $h){Write-Host 'PUBLICATION_DECISION=REJECT_SOURCE_CHANGED';exit 3}
  Write-Host 'PUBLICATION_DECISION=ELIGIBLE_FOR_FURTHER_CHECKS'
 }
 Probe {
  if($Role -notin @('Publisher','Adversary')){throw 'INVALID_PROBE_ROLE'}
  foreach($p in @($copy,$digest)){
   foreach($access in @([IO.FileAccess]::Read,[IO.FileAccess]::Write)){
    try{$f=[IO.File]::Open($p,[IO.FileMode]::Open,$access,[IO.FileShare]::None);$f.Dispose();throw "ACCESS_ALLOWED=$p $access"}
    catch [UnauthorizedAccessException]{Write-Host "PASS_DENIED=$p $access"}
   }
  }
  Write-Host 'PROBES=PASS'
 }
 Rollback {
  if($Role -ne 'Admin' -or -not $ConfirmRollback){throw 'ADMIN_AND_CONFIRMATION_REQUIRED'}
  Disable-LocalUser BEEXCITED_SealLab -ErrorAction Stop
  Write-Host 'ROLLBACK=SEALER_DISABLED;FILES_AND_ACLS_PRESERVED'
 }
}
