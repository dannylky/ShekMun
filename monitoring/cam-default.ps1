# cam-default.ps1 - resets all room cameras to their default position.
# Called silently by the "Cam default" button in monitor-control and by
# its daily 07:02 schedule. Results are recorded in logs\cam-default.log.
#
# Usage:
#   powershell -File cam-default.ps1                    # manual run
#   powershell -File cam-default.ps1 -Reason scheduled  # daily schedule
#   powershell -File cam-default.ps1 -DryRun            # log only, no calls

param(
    [string]$Reason = 'manual',
    [switch]$DryRun
)

$root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$logDir = Join-Path $root 'logs'
$logFile = Join-Path $logDir 'cam-default.log'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

$rooms = @(
    @{ name = 'SM01'; url = 'http://172.18.2.51:8000/api/location/1/2/4/press' },
    @{ name = 'SM02'; url = 'http://172.18.2.52:8000/api/location/1/0/4/press' },
    @{ name = 'SM03'; url = 'http://172.18.2.53:8000/api/location/1/0/4/press' },
    @{ name = 'SM04'; url = 'http://172.18.2.54:8000/api/location/1/0/4/press' },
    @{ name = 'SM05'; url = 'http://172.18.2.55:8000/api/location/1/0/4/press' },
    @{ name = 'SM06'; url = 'http://172.18.2.56:8000/api/location/1/0/4/press' },
    @{ name = 'SM07'; url = 'http://172.18.2.57:8000/api/location/1/0/4/press' },
    @{ name = 'SM08'; url = 'http://172.18.2.58:8000/api/location/1/0/4/press' }
)

$results = @()
foreach ($room in $rooms) {
    if ($DryRun) {
        $results += "$($room.name) DRY-RUN"
        continue
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        Invoke-RestMethod -Uri $room.url -Method Post -TimeoutSec 5 | Out-Null
        $results += "$($room.name) OK ($($sw.ElapsedMilliseconds) ms)"
    } catch {
        $results += "$($room.name) FAIL ($($_.Exception.Message))"
    }
}

$ok = @($results | Where-Object { $_ -like '* OK*' -or $_ -like '* DRY-RUN' }).Count
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$line = "$stamp  [$Reason]  $ok/$($rooms.Count) OK  |  " + ($results -join '; ')
Add-Content -Path $logFile -Value $line -Encoding UTF8