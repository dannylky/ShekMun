<#
.SYNOPSIS
    Continuously monitors all rooms/devices from devices.json using ICMP.

.DESCRIPTION
    Each device is checked on its own schedule:
      - First check is staggered by a random delay in [0, masterInterval],
        so devices never start at the same time.
      - After every check, the next one is scheduled at
        masterInterval +- random jitter (masterInterval * jitterFraction),
        floored at minIntervalSeconds.
      - Master interval comes from config.json and can be overridden
        with -Interval (seconds).

    Results are appended to logs\status-YYYYMMDD.csv. Failures are also
    printed to the console. The latest status of every device is kept in
    snapshot.json (in this folder, debounced to at most one write per
    second) - the dashboard reads it. At the end of every run (one-shot
    finish or Ctrl+C) a report file is written to
    logs\report-YYYYMMDD-HHmmss.txt with the summary and the full failure
    list. Old log files are pruned after logRetentionDays.

.EXAMPLE
    .\monitor.ps1
    .\monitor.ps1 -Interval 5 -OneShot
    .\monitor.ps1 -Verbose
#>
[CmdletBinding()]
param(
    [string]$ConfigPath = '',
    [string]$DevicesPath = '',
    [int]$Interval = -1,
    [switch]$OneShot
)

$ErrorActionPreference = 'Stop'

if (-not $ConfigPath) { $ConfigPath = Join-Path $PSScriptRoot 'config.json' }
if (-not $DevicesPath) { $DevicesPath = Join-Path $PSScriptRoot 'devices.json' }
if (-not (Test-Path $ConfigPath)) { throw "Config not found: $ConfigPath" }
if (-not (Test-Path $DevicesPath)) { throw "Devices not found: $DevicesPath. Run build-devices.ps1 first." }

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
if ($Interval -gt 0) { $config.masterIntervalSeconds = $Interval }

$inventory = Get-Content $DevicesPath -Raw | ConvertFrom-Json

$logDir = if ([System.IO.Path]::IsPathRooted($config.logDirectory)) { $config.logDirectory }
          else { Join-Path $PSScriptRoot $config.logDirectory }
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$rand = [System.Random]::new()

# ------------------------------------------------------------- snapshot --
$script:snapshotPath = Join-Path $PSScriptRoot 'snapshot.json'
$script:snap = @{
    version     = 1
    generatedAt = (Get-Date).ToString('o')
    updatedAt   = ''
    rooms       = [ordered]@{}
    unique      = [System.Collections.Generic.List[object]]::new()
}
foreach ($roomName in $inventory.rooms.PSObject.Properties.Name) {
    $script:snap.rooms[$roomName] = [System.Collections.Generic.List[object]]::new()
}

function Save-Snapshot {
    $script:snap.updatedAt = (Get-Date).ToString('o')
    $json = $script:snap | ConvertTo-Json -Depth 6
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($script:snapshotPath, $json, $utf8NoBom)
}

# ----------------------------------------------------------- scheduling --
$jobs = [System.Collections.Generic.List[object]]::new()
function New-Job {
    param([string]$Name, [string]$Ip, [string]$Role, [string]$Room)
    $dev = @{ name = $Name; ip = $Ip; role = $Role; status = 'unknown'; rttMs = -1; checkedAt = '' }
    if ($Room -eq 'UNIQUE') { $script:snap.unique.Add($dev) }
    else { $script:snap.rooms[$Room].Add($dev) }
    return @{
        name     = $Name
        ip       = $Ip
        role     = $Role
        room     = $Room
        interval = $config.masterIntervalSeconds
        next     = (Get-Date).AddSeconds($rand.NextDouble() * $config.masterIntervalSeconds)
        dev      = $dev
    }
}
foreach ($roomName in $inventory.rooms.PSObject.Properties.Name) {
    foreach ($d in $inventory.rooms.$roomName) {
        $jobs.Add((New-Job -Name $d.name -Ip $d.ip -Role $d.role -Room $roomName))
    }
}
foreach ($d in $inventory.unique) {
    $jobs.Add((New-Job -Name $d.name -Ip $d.ip -Role $d.role -Room 'UNIQUE'))
}

function Get-NextInterval {
    $jitter = $config.jitterFraction * $config.masterIntervalSeconds
    $next = $config.masterIntervalSeconds + ($rand.NextDouble() * 2 - 1) * $jitter
    return [Math]::Max([double]$config.minIntervalSeconds, $next)
}

# -------------------------------------------------------------- logging --
function Write-LogLine {
    param([string]$Line, [string]$File)
    Add-Content -Path $File -Value $Line -Encoding UTF8
}

function Test-Device {
    param($Job)
    try {
        $ping = [System.Net.NetworkInformation.Ping]::new()
        $reply = $ping.Send($Job.ip, [int]$config.timeoutMs)
        $ok = $reply.Status -eq [System.Net.NetworkInformation.IPStatus]::Success
        $rtt = if ($ok) { $reply.RoundtripTime } else { -1 }
        return @{ ok = $ok; rtt = $rtt }
    } catch {
        return @{ ok = $false; rtt = -1 }
    }
}

$started = Get-Date
$script:pingCount = 0
$script:failCount = 0
$script:failures = [System.Collections.Generic.List[string]]::new()
$script:seenThisRun = @{}
$script:lastSnapWrite = Get-Date
$logFile = Join-Path $logDir ("status-" + (Get-Date).ToString('yyyyMMdd') + '.csv')

if (-not (Test-Path $logFile)) {
    Write-LogLine -File $logFile -Line 'timestamp,room,device,ip,result,rttMs'
}

function Record-Result {
    param($Job, $Result)
    $status = if ($Result.ok) { 'OK' } else { 'FAIL' }
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'),$($Job.room),$($Job.name),$($Job.ip),$status,$($Result.rtt)"
    Write-LogLine -File $logFile -Line $line

    $Job.dev.status = $status.ToLower()
    $Job.dev.rttMs = $Result.rtt
    $Job.dev.checkedAt = (Get-Date).ToString('o')

    $script:pingCount++
    if ($Result.ok) {
        Write-Verbose $line
    } else {
        $script:failCount++
        Write-Host "FAIL $($Job.room) $($Job.name) $($Job.ip) (rtt $($Result.rtt))"
        if (-not $script:seenThisRun.ContainsKey($Job.ip)) {
            $script:failures.Add("$($Job.room),$($Job.name),$($Job.ip)")
            $script:seenThisRun[$Job.ip] = $true
        }
    }

    if (((Get-Date) - $script:lastSnapWrite).TotalSeconds -ge 1) {
        Save-Snapshot
        $script:lastSnapWrite = Get-Date
    }
}

Write-Host "Monitoring started: $($jobs.Count) devices, master interval $($config.masterIntervalSeconds)s, jitter $($config.jitterFraction * 100)%, timeout $($config.timeoutMs)ms"
Write-Host "Log: $logFile"

function Write-RunReport {
    param([string]$Label)
    $reportFile = Join-Path $logDir ("report-" + (Get-Date).ToString('yyyyMMdd-HHmmss') + '.txt')
    $ok = $script:pingCount - $script:failCount
    $pct = if ($script:pingCount -gt 0) { [Math]::Round(100 * $ok / $script:pingCount, 1) } else { 0 }

    $byRoom = $script:failures | ForEach-Object { ($_ -split ',')[0] } | Group-Object | Sort-Object Count -Descending
    $byRoleList = foreach ($f in $script:failures) { $room, $name, $ip = $f -split ','; $roles[$ip] }
    $byRole = $byRoleList | Group-Object | Sort-Object Count -Descending

    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add("# Shek Mun monitoring report - $Label")
    $lines.Add("generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    $lines.Add("session: $started  duration: $([Math]::Round(((Get-Date) - $started).TotalMinutes, 1)) min")
    $lines.Add("devices: $($jobs.Count)  checked: $script:pingCount  OK: $ok  FAIL: $script:failCount  (OK rate: $pct%)")
    $lines.Add('')
    $lines.Add('Failures by room:')
    if ($byRoom) { foreach ($g in $byRoom) { $lines.Add("  $($g.Name): $($g.Count)") } } else { $lines.Add('  (none)') }
    $lines.Add('')
    $lines.Add('Failures by role:')
    if ($byRole) { foreach ($g in $byRole) { $lines.Add("  $($g.Name): $($g.Count)") } } else { $lines.Add('  (none)') }
    $lines.Add('')
    $lines.Add('Failed devices:')
    if ($script:failures.Count) { foreach ($f in $script:failures) { $lines.Add("  $f") } } else { $lines.Add('  (none)') }

    Set-Content -Path $reportFile -Value $lines -Encoding UTF8
    Write-Host "Report: $reportFile"
}

$roles = @{}
foreach ($d in $inventory.unique) { $roles[$d.ip] = $d.role }
foreach ($roomName in $inventory.rooms.PSObject.Properties.Name) {
    foreach ($d in $inventory.rooms.$roomName) { $roles[$d.ip] = $d.role }
}

if ($OneShot) {
    $jobs | Sort-Object { $rand.Next() } | ForEach-Object {
        $result = Test-Device $_
        Record-Result -Job $_ -Result $result
    }
    Save-Snapshot
    Write-Host "One-shot pass complete."
    Write-RunReport -Label 'One-shot'
    exit
}

# -------------------------------------------------------------- main loop --
try {
    while ($true) {
        Start-Sleep -Milliseconds 500
        $now = Get-Date

        foreach ($job in $jobs) {
            if ($now -lt $job.next) { continue }

            $result = Test-Device $job
            Record-Result -Job $job -Result $result

            $job.next = (Get-Date).AddSeconds((Get-NextInterval))
        }

        if ($script:lastHeartbeat -eq $null -or ((Get-Date) - $script:lastHeartbeat).TotalSeconds -ge 300) {
            Write-Host "[heartbeat] $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) pings=$script:pingCount fails=$script:failCount"
            $script:lastHeartbeat = Get-Date
        }

        # prune old logs
        Get-ChildItem $logDir -Filter 'status-*.csv' |
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$config.logRetentionDays) } |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
} finally {
    Write-Host "Session ended."
    Save-Snapshot
    Write-RunReport -Label 'Continuous session'
}
