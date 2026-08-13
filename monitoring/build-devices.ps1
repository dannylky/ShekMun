<#
.SYNOPSIS
    Regenerates devices.json from the IP assignment tables in
    "Shek Mun SOP Short.docx". Bumps the inventory version and appends
    a CHANGELOG.md entry, then commits to git.

.DESCRIPTION
    The device spec below mirrors the IP tables (Subnet 1: 172.18.2.0/23,
    Subnet 2: 172.18.22.0/24). Edit this spec when the SOP changes, then
    re-run this script to rebuild the inventory with a new version.

.PARAMETER Message
    Changelog description for the inventory change.

.PARAMETER Minor
    Bump minor version instead of patch.

.PARAMETER Major
    Bump major version instead of patch.

.PARAMETER Version
    Explicit version for this generation (overrides auto-bump). Use for the
    first generation (e.g. -Version 1.0.0).

.PARAMETER NoCommit
    Regenerate devices.json without committing to git.
#>
[CmdletBinding()]
param(
    [string]$Message = "Inventory regenerated",
    [string]$Version = '',
    [switch]$Minor,
    [switch]$Major,
    [switch]$NoCommit
)

$ErrorActionPreference = 'Stop'
$scriptDir = $PSScriptRoot
$rootDir = Split-Path $scriptDir -Parent

# ---------------------------------------------------------------- spec ----
$rooms = @('SM-11-01','SM-11-02','SM-11-03','SM-11-04','SM-11-05','SM-11-06','SM-11-07','SM-11-08','Common Rm')
$roomCount = $rooms.Count

$roomDevices = @{}
foreach ($r in $rooms) { $roomDevices[$r] = [System.Collections.Generic.List[object]]::new() }

function Add-Seq {
    param([string]$Name, [string]$Prefix, [int]$Start, [string]$Role)
    for ($i = 0; $i -lt $roomCount; $i++) {
        $roomDevices[$rooms[$i]].Add(@{ name = $Name; ip = "$Prefix$($Start + $i)"; role = $Role })
    }
}

function Add-Map {
    param([string]$Name, [hashtable]$Map, [string]$Prefix, [string]$Role)
    foreach ($key in $Map.Keys) {
        $roomDevices[$rooms[$key - 1]].Add(@{ name = $Name; ip = "$Prefix$($Map[$key])"; role = $Role })
    }
}

# Subnet 1 - Control (all rooms, sequential)
Add-Seq 'PCU-AVRack'      '172.18.2.' 11 'control'
Add-Seq 'PCU-Lectern'     '172.18.2.' 21 'control'
Add-Seq 'AVProc-Extron'   '172.18.2.' 31 'control'
Add-Seq 'HardKey'         '172.18.2.' 41 'control'
Add-Seq 'AVProc-Pi5'      '172.18.2.' 51 'control'
Add-Seq 'Dock-4ch'        '172.18.2.' 61 'control'
Add-Seq 'Dock-2ch'        '172.18.2.' 71 'control'   # SM-11-05: doc says .65 (dup of 4ch) - corrected to .75
Add-Seq 'Antenna-Ctrl'    '172.18.2.' 81 'control'
Add-Seq 'Mixer-Ctrl'      '172.18.2.' 91 'control'

# Subnet 1 - Dante
Add-Seq 'USB-PC'          '172.18.2.' 101 'dante'
Add-Seq 'EN-PC-Dante'     '172.18.2.' 111 'dante'
Add-Seq 'EN-Laptop-Dante' '172.18.2.' 121 'dante'
Add-Map 'EN-Mac-Dante'    @{ 2 = 132 }                 '172.18.2.' 'dante'
Add-Seq 'Antenna-Dante'   '172.18.2.' 141 'dante'
Add-Seq 'Mixer-Dante'     '172.18.2.' 151 'dante'
Add-Seq 'Speaker-1'       '172.18.2.' 161 'audio'
Add-Seq 'Speaker-2'       '172.18.2.' 171 'audio'
Add-Seq 'Speaker-3'       '172.18.2.' 181 'audio'
Add-Seq 'Speaker-4'       '172.18.2.' 191 'audio'
Add-Seq 'Speaker-5'       '172.18.2.' 201 'audio'
Add-Seq 'Speaker-6'       '172.18.2.' 211 'audio'
Add-Map 'Speaker-7'       @{ 1 = 221; 8 = 228; 9 = 229 } '172.18.2.' 'audio'
Add-Map 'Speaker-8'       @{ 1 = 231; 8 = 238; 9 = 239 } '172.18.2.' 'audio'
Add-Map 'Speaker-9-USBMac' @{ 2 = 242; 8 = 248 }      '172.18.2.' 'dante'

# Subnet 2 - Switches + AVoIP
Add-Seq 'SW-Rack'         '172.18.22.' 11 'switch'
Add-Seq 'SW-Lectern'      '172.18.22.' 21 'switch'
Add-Map 'SW-Lectern-2'    @{ 1 = 31 }                  '172.18.22.' 'switch'
Add-Seq 'TV-DEC-1'        '172.18.22.' 41 'display'
Add-Map 'TV-DEC-2'        @{ 1 = 51; 2 = 52; 7 = 57; 8 = 58 } '172.18.22.' 'display'
Add-Map 'TV-DEC-3'        @{ 1 = 61 }                  '172.18.22.' 'display'
Add-Map 'TV-DEC-4'        @{ 1 = 71 }                  '172.18.22.' 'display'
Add-Seq 'Cam-1'           '172.18.22.' 81 'camera'
Add-Map 'Cam-2'           @{ 1 = 91; 3 = 93; 5 = 95 }  '172.18.22.' 'camera'
Add-Seq 'MediaBox'        '172.18.22.' 101 'media'
Add-Seq 'EN-PC-AVoIP'     '172.18.22.' 111 'avoip'
Add-Seq 'EN-Laptop-AVoIP' '172.18.22.' 121 'avoip'
Add-Map 'EN-Mac-AVoIP'    @{ 2 = 132 }                 '172.18.22.' 'avoip'
Add-Map 'TV-Res-1'        @{ 1 = 141; 2 = 142; 7 = 147; 8 = 148; 9 = 149 } '172.18.22.' 'display'
Add-Map 'TV-Res-2'        @{ 1 = 151; 2 = 152; 7 = 157; 8 = 158 } '172.18.22.' 'display'
Add-Map 'TV-Res-3'        @{ 1 = 161 }                 '172.18.22.' 'display'
Add-Map 'TV-Res-4'        @{ 1 = 171 }                 '172.18.22.' 'display'
Add-Seq 'Audio-DEC'       '172.18.22.' 181 'audio'

# Unique / shared equipment (not per-room)
$unique = @(
    @{ name = 'DSP-Ctrl';      ip = '172.18.2.6';   role = 'control' },
    @{ name = 'DSP-Dante';     ip = '172.18.2.7';   role = 'dante' },
    @{ name = 'XSM4216F';      ip = '172.18.22.2';  role = 'switch' },
    @{ name = 'AVoIP-Manager'; ip = '172.18.22.5';  role = 'avoip' }
)

# ---------------------------------------------------------- versioning ----
$inventoryFile = Join-Path $scriptDir 'devices.json'
$changelogFile = Join-Path $rootDir 'CHANGELOG.md'

$oldVersion = '0.0.0'
if (Test-Path $inventoryFile) {
    $old = Get-Content $inventoryFile -Raw | ConvertFrom-Json
    $oldVersion = $old.inventoryVersion
}
if ($Version) { $newVersion = $Version }
else {
    $parts = $oldVersion -split '\.'
    if ($Major) { $newVersion = "$([int]$parts[0] + 1).0.0" }
    elseif ($Minor) { $newVersion = "$($parts[0]).$([int]$parts[1] + 1).0" }
    else { $newVersion = "$($parts[0]).$($parts[1]).$([int]$parts[2] + 1)" }
}

# ------------------------------------------------------------- output ----
$inventory = @{
    inventoryVersion = $newVersion
    source           = 'Shek Mun SOP Short.docx (IP assignment tables)'
    generatedAt      = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    unique           = $unique
    rooms            = [ordered]@{}
}
foreach ($r in $rooms) {
    $inventory.rooms[$r] = @($roomDevices[$r] | Sort-Object ip)
}

$json = $inventory | ConvertTo-Json -Depth 5
Set-Content -Path $inventoryFile -Value $json -Encoding UTF8

$deviceCount = ($inventory.rooms.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
Write-Host "devices.json written: $newVersion ($deviceCount room devices + $($unique.Count) unique)"

if (-not $NoCommit) {
    $entry = @"

## [$newVersion] - $(Get-Date -Format 'yyyy-MM-dd')
- $Message (device count: $deviceCount)

"@
    if (Test-Path $changelogFile) {
        $content = Get-Content $changelogFile -Raw
        $content = $content.Replace("`n## [", "$entry`n## [")
        Set-Content -Path $changelogFile -Value $content -Encoding UTF8
    } else {
        Set-Content -Path $changelogFile -Value "# Changelog`n$entry" -Encoding UTF8
    }

    git -C $rootDir add "monitoring/devices.json" CHANGELOG.md
    git -C $rootDir commit -m "inventory: v$oldVersion -> v$newVersion - $Message"
    Write-Host "Committed inventory v$newVersion"
}

