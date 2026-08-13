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
    printed to the console. Old log files are pruned after
    logRetentionDays.

.EXAMPLE
    .\monitor.ps1
    .\monitor.ps1 -Interval 5 -OneShot
    .\monitor.ps1 -Verbose
#>
[CmdletBinding()]
param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot 'config.json'),
    [string]$DevicesPath = (Join-Path $PSScriptRoot 'devices.json'),
    [int]$Interval = -1,
    [switch]$OneShot
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ConfigPath)) { throw "Config not found: $ConfigPath" }
if (-not (Test-Path $DevicesPath)) { throw "Devices not found: $DevicesPath. Run build-devices.ps1 first." }

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
if ($Interval -gt 0) { $config.masterIntervalSeconds = $Interval }

$inventory = Get-Content $DevicesPath -Raw | ConvertFrom-Json

$logDir = if ([System.IO.Path]::IsPathRooted($config.logDirectory)) { $config.logDirectory }
          else { Join-Path $PSScriptRoot $config.logDirectory }
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$rand = [System.Random]::new()

# ----------------------------------------------------------- scheduling --
$jobs = [System.Collections.Generic.List[object]]::new()
foreach ($roomName in $inventory.rooms.PSObject.Properties.Name) {
    foreach ($d in $inventory.rooms.$roomName) {
        $jobs.Add(@{
            name     = $d.name
            ip       = $d.ip
            role     = $d.role
            room     = $roomName
            interval = $config.masterIntervalSeconds
            next     = (Get-Date).AddSeconds($rand.NextDouble() * $config.masterIntervalSeconds)
        })
    }
}
foreach ($d in $inventory.unique) {
    $jobs.Add(@{
        name     = $d.name
        ip       = $d.ip
        role     = $d.role
        room     = 'UNIQUE'
        interval = $config.masterIntervalSeconds
        next     = (Get-Date).AddSeconds($rand.NextDouble() * $config.masterIntervalSeconds)
    })
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
$pingCount = 0
$failCount = 0
$logFile = Join-Path $logDir ("status-" + (Get-Date).ToString('yyyyMMdd') + '.csv')

if (-not (Test-Path $logFile)) {
    Write-LogLine -File $logFile -Line 'timestamp,room,device,ip,result,rttMs'
}

Write-Host "Monitoring started: $($jobs.Count) devices, master interval $($config.masterIntervalSeconds)s, jitter $($config.jitterFraction * 100)%, timeout $($config.timeoutMs)ms"
Write-Host "Log: $logFile"

if ($OneShot) {
    $jobs | Sort-Object { $rand.Next() } | ForEach-Object {
        $result = Test-Device $_
        $status = if ($result.ok) { 'OK' } else { 'FAIL' }
        $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'),$($_.room),$($_.name),$($_.ip),$status,$($result.rtt)"
        Write-LogLine -File $logFile -Line $line
        if ($result.ok) { Write-Verbose $line } else { Write-Host "FAIL $($_.room) $($_.name) $($_.ip)" }
    }
    Write-Host "One-shot pass complete."
    exit
}

# -------------------------------------------------------------- main loop --
while ($true) {
    Start-Sleep -Milliseconds 500
    $now = Get-Date

    foreach ($job in $jobs) {
        if ($now -lt $job.next) { continue }

        $result = Test-Device $job
        $pingCount++
        if (-not $result.ok) { $failCount++ }

        $status = if ($result.ok) { 'OK' } else { 'FAIL' }
        $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'),$($job.room),$($job.name),$($job.ip),$status,$($result.rtt)"
        Write-LogLine -File $logFile -Line $line
        if ($result.ok) { Write-Verbose $line } else { Write-Host "FAIL $($job.room) $($job.name) $($job.ip) (rtt -1)" }

        $job.next = (Get-Date).AddSeconds((Get-NextInterval))
    }

    if ($script:lastHeartbeat -eq $null -or ((Get-Date) - $script:lastHeartbeat).TotalSeconds -ge 300) {
        Write-Host "[heartbeat] $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) pings=$pingCount fails=$failCount"
        $script:lastHeartbeat = Get-Date
    }

    # prune old logs
    Get-ChildItem $logDir -Filter 'status-*.csv' |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$config.logRetentionDays) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}
