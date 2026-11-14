param([Parameter(Mandatory=$true)][ValidateSet('Seal','Verify','Probe')][string]$Mode,
 [ValidateSet('Sealer','Publisher','Adversary')][string]$Role='Sealer')
$ErrorActionPreference='Stop'
$root=Join-Path $env:ProgramData 'BEEXCITED-Phase1K-91C29G4-Lab'
$lab=Join-Path $root '91C29J_seal'
$source=Join-Path $root 'store\91C29I_synthetic\sealed_candidate.bin'
$sealed=Join-Path $lab 'sealed\evidence.bin'
$digest=Join-Path $lab 'sealed\authoritative.sha256'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$names=@{Sealer='BEEXCITED_SealLab';Publisher='BEEXCITED_PubLab';Adversary='BEEXCITED_AdvLab'}
$expected=(Get-LocalUser -Name $names[$Role] -ErrorAction Stop).SID.Value
if($identity.User.Value -ne $expected){throw "WRONG_IDENTITY: $($identity.Name)"}
if(([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ELEVATED_TOKEN_REJECTED'}
if(-not (Test-Path -LiteralPath (Join-Path $root 'BEEXCITED_LAB_MARKER.txt'))){throw 'BASE_MARKER_MISSING'}
function Hash($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256 -ErrorAction Stop).Hash}
if($Mode -eq 'Seal'){
 if($Role -ne 'Sealer'){throw 'SEALER_REQUIRED'}
 if((Test-Path -LiteralPath $sealed) -or (Test-Path -LiteralPath $digest)){throw 'SEAL_EXISTS: NO_OVERWRITE'}
 if(-not (Test-Path -LiteralPath $source -PathType Leaf)){throw 'SOURCE_MISSING'}
 $bytes=[IO.File]::ReadAllBytes($source)
 if($bytes.Length -gt 1048576){throw 'SOURCE_TOO_LARGE'}
 $sha=[Security.Cryptography.SHA256]::Create()
 try{$hash=[BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','')}finally{$sha.Dispose()}
 # CreateNew avoids silent replacement; partial failure requires manual investigation, never automatic reseal.
 $stream=[IO.File]::Open($sealed,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
 if((Hash $sealed) -cne $hash){throw 'SEALED_COPY_HASH_MISMATCH'}
 $stream=[IO.File]::Open($digest,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$b=[Text.Encoding]::ASCII.GetBytes($hash+"\r\n");$stream.Write($b,0,$b.Length)}finally{$stream.Dispose()}
 Write-Host "AUTHORITATIVE_SHA256=$hash"
 Write-Host 'SEAL_CREATED=YES'
}elseif($Mode -eq 'Verify'){
 if($Role -ne 'Sealer'){throw 'SEALER_REQUIRED'}
 $expectedHash=[IO.File]::ReadAllText($digest).Trim()
 if($expectedHash -cnotmatch '^[A-F0-9]{64}$'){throw 'INVALID_DIGEST'}
 $sealedHash=Hash $sealed
 $sourceHash=Hash $source
 Write-Host "AUTHORITATIVE_SHA256=$expectedHash"
 Write-Host "SEALED_SHA256=$sealedHash"
 Write-Host "SOURCE_SHA256=$sourceHash"
 if($sealedHash -cne $expectedHash){Write-Host 'PUBLICATION_DECISION=REJECT_SEALED_STORE_INTEGRITY';exit 2}
 if($sourceHash -cne $expectedHash){Write-Host 'PUBLICATION_DECISION=REJECT_SOURCE_CHANGED';exit 3}
 Write-Host 'PUBLICATION_DECISION=ELIGIBLE_FOR_FURTHER_CHECKS'
 Write-Host 'NOTE=NOT_A_PUBLICATION_AUTHORISATION'
}elseif($Mode -eq 'Probe'){
 if($Role -eq 'Sealer'){throw 'PROBE_REQUIRES_PUBLISHER_OR_ADVERSARY'}
 # Read and write probes must be independently denied. Never alter a protected file even if ACL fails.
 foreach($p in @($sealed,$digest)){
  $name=Split-Path $p -Leaf
  try{$null=[IO.File]::ReadAllBytes($p);Write-Host "FAIL_READ_ALLOWED=$name"}catch [UnauthorizedAccessException]{Write-Host "PASS_READ_DENIED=$name"}
  # Open existing for write without writing bytes; no mutation occurs.
  try{$s=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::None);$s.Dispose();Write-Host "FAIL_WRITE_HANDLE_ALLOWED=$name"}catch [UnauthorizedAccessException]{Write-Host "PASS_WRITE_DENIED=$name"}
 }
}
