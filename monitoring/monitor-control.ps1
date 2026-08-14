<#
.SYNOPSIS
    Tiny desktop controller for the Shek Mun monitoring system.

.DESCRIPTION
    WinForms app to start/stop the monitor and the dashboard server,
    showing live status (idle / running / error) and last run times.

    - Monitoring group: status + live "now checking" device (from the
      latest status-CSV row, refreshed every 1.5 s), last run + duration,
      Start / Stop buttons.
    - Temp monitor group: start/stop temp-monitor.py (Kramer KDS unit
      temperatures), status + last pass summary from temp-snapshot.json.
    - Dashboard group: server status + port, Launch Dashboard (starts
      the server if needed and opens the browser) / Stop Server.
    - Statuses are polled every 1.5 s; run state survives app restarts
      (re-detected from running processes and the port).
    - On load the app auto-starts the monitor, the temp monitor and the
      dashboard server + browser (no-op if already running).
    - Closing the window stops the monitor, temp monitor and the
      dashboard server (background processes are killed).

    .\monitor-control.ps1        # normal GUI
    .\monitor-control.ps1 -Test  # headless self-test cycle, no GUI
#>
[CmdletBinding()]
param([switch]$Test)

$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$root = $PSScriptRoot
$monitorScript = Join-Path $root 'monitor.ps1'
$serverScript = Join-Path $root 'serve-dashboard.ps1'
$snapshotPath = Join-Path $root 'snapshot.json'
$tempScript = Join-Path $root 'temp-monitor.py'
$tempSnapshotPath = Join-Path $root 'temp-snapshot.json'
$script:version = '1.5.5'

$script:monitorPid = $null
$script:monitorStopRequested = $false
$script:lastKnownPid = $null
$script:lastKnownCreation = $null
$script:monitorError = $null
$script:tempPid = $null
$script:tempStopRequested = $false
$script:lastKnownTempPid = $null
$script:tempError = $null
$script:port = 8080
$script:logBuffer = [System.Text.StringBuilder]::new()

# ------------------------------------------------------------- helpers --
function Add-Log {
    param([string]$Message)
    $script:logBuffer.AppendLine("$(Get-Date -Format 'HH:mm:ss')  $Message") | Out-Null
    if ($script:logBox) { $script:logBox.AppendText("$(Get-Date -Format 'HH:mm:ss')  $Message`r`n") }
}

function Get-MonitorProcess {
    Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" |
        Where-Object { $_.CommandLine -like '*monitor.ps1*' -and $_.CommandLine -notlike '*monitor-control.ps1*' -and $_.CommandLine -notlike '*-OneShot*' } |
        Sort-Object CreationDate -Descending | Select-Object -First 1
}

function Get-ServerProcess {
    Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" |
        Where-Object { $_.CommandLine -like '*serve-dashboard.ps1*' } |
        Sort-Object CreationDate -Descending | Select-Object -First 1
}

function Test-PortListening {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $task = $client.ConnectAsync('127.0.0.1', $Port)
        return $task.Wait(300) -and $client.Connected
    } catch { return $false }
    finally { $client.Close() }
}

function Start-Monitoring {
    if ($script:monitorError) { $script:monitorError = $null }
    if (Get-MonitorProcess) { return 'already running' }
    if (-not (Test-Path $monitorScript)) { return "monitor.ps1 not found at $monitorScript" }
    try {
        $p = Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$monitorScript`"") -WindowStyle Hidden -PassThru
        Start-Sleep -Milliseconds 800
        if ($p.HasExited) { return "monitor exited immediately (code $($p.ExitCode))" }
        $script:monitorPid = $p.Id
        $script:monitorStopRequested = $false
        return "started (PID $($p.Id))"
    } catch { return "start failed: $($_.Exception.Message)" }
}

function Stop-Monitoring {
    $mp = Get-MonitorProcess
    if (-not $mp) { return 'not running' }
    $script:monitorStopRequested = $true
    try {
        Stop-Process -Id $mp.ProcessId -Force -ErrorAction Stop
        $script:monitorPid = $null
        return "stopped (PID $($mp.ProcessId))"
    } catch {
        $script:monitorStopRequested = $false
        return "stop failed: $($_.Exception.Message)"
    }
}

function Start-Dashboard {
    param([int]$Port)
    if (Test-PortListening $Port) { return "port $Port already in use" }
    if (-not (Test-Path $serverScript)) { return "serve-dashboard.ps1 not found at $serverScript" }
    try {
        $p = Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$serverScript`"",'-Port',"$Port") -WindowStyle Hidden -PassThru
        Start-Sleep -Seconds 1
        if (Test-PortListening $Port) {
            $script:dashStopRequested = $false
            return "running on http://localhost:$Port"
        }
        if ($p.HasExited) { return "server exited (code $($p.ExitCode))" }
        return 'started but not listening yet, will retry'
    } catch { return "start failed: $($_.Exception.Message)" }
}

function Stop-Dashboard {
    $sp = Get-ServerProcess
    if (-not $sp) { return 'not running' }
    $script:dashStopRequested = $true
    try {
        Stop-Process -Id $sp.ProcessId -Force -ErrorAction Stop
        return 'stopped'
    } catch { return "stop failed: $($_.Exception.Message)" }
}

function Open-Dashboard {
    param([int]$Port)
    $result = Start-Dashboard $Port
    if ($result -like 'running*') {
        Start-Process "http://localhost:$Port/dashboard_shekmun.html"
        return $result
    } elseif ($result -like 'port*in use') {
        Start-Process "http://localhost:$Port/dashboard_shekmun.html"
        return $result
    }
    return $result
}

function Get-TempProcess {
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object { $_.CommandLine -like '*temp-monitor.py*' -and $_.CommandLine -notlike '*--one-shot*' } |
        Sort-Object CreationDate -Descending | Select-Object -First 1
}

function Start-TempMonitor {
    if ($script:tempError) { $script:tempError = $null }
    if (Get-TempProcess) { return 'already running' }
    if (-not (Test-Path $tempScript)) { return "temp-monitor.py not found at $tempScript" }
    try {
        $p = Start-Process python -ArgumentList @('-u',"`"$tempScript`"") -WindowStyle Hidden -PassThru
        Start-Sleep -Milliseconds 800
        if ($p.HasExited) { return "temp monitor exited immediately (code $($p.ExitCode))" }
        $script:tempPid = $p.Id
        $script:tempStopRequested = $false
        return "started (PID $($p.Id))"
    } catch { return "start failed: $($_.Exception.Message)" }
}

function Stop-TempMonitor {
    $tp = Get-TempProcess
    if (-not $tp) { return 'not running' }
    $script:tempStopRequested = $true
    try {
        Stop-Process -Id $tp.ProcessId -Force -ErrorAction Stop
        $script:tempPid = $null
        return "stopped (PID $($tp.ProcessId))"
    } catch {
        $script:tempStopRequested = $false
        return "stop failed: $($_.Exception.Message)"
    }
}

function Get-TempLastInfo {
    if (-not (Test-Path $tempSnapshotPath)) { return 'Never run' }
    try {
        $snap = Get-Content $tempSnapshotPath -Raw | ConvertFrom-Json
        $units = @($snap.units)
        $ok = @($units | Where-Object { $_.status -eq 'ok' }).Count
        $temps = @($units | Where-Object { $null -ne $_.tempC } | ForEach-Object { [int]$_.tempC })
        $last = $snap.updatedAt
        if ($temps.Count) {
            $min = ($temps | Measure-Object -Minimum).Minimum
            $max = ($temps | Measure-Object -Maximum).Maximum
            return "Last pass: $(([DateTime]$last).ToString('HH:mm:ss')) · $ok/$($units.Count) OK · $min-$max`C"
        }
        return "Last pass: $(([DateTime]$last).ToString('HH:mm:ss')) · $ok/$($units.Count) OK"
    } catch { return 'Never run' }
}

function Get-LastCheckLine {
    $today = "status-" + (Get-Date).ToString('yyyyMMdd') + '.csv'
    $logFile = Join-Path (Join-Path $root 'logs') $today
    if (-not (Test-Path $logFile)) { return $null }
    try {
        $line = Get-Content $logFile -Tail 1 -ErrorAction Stop
        if (-not $line) { return $null }
        $parts = $line -split ','
        if ($parts.Count -lt 6) { return $null }
        return [PSCustomObject]@{
            ts     = $parts[0]
            room   = $parts[1]
            device = $parts[2]
            ip     = $parts[3]
            result = $parts[4]
            rtt    = $parts[5]
        }
    } catch { return $null }
}

function Get-MonitorErrorTail {
    $errFile = Join-Path (Join-Path $root 'logs') 'monitor-error.log'
    if (-not (Test-Path $errFile)) { return '' }
    $lines = Get-Content $errFile -Tail 3 -ErrorAction SilentlyContinue
    if ($lines) { return "  " + ($lines -join "`r`n  ") }
    return ''
}

function Get-LastTempCheckLine {
    $today = "temp-" + (Get-Date).ToString('yyyyMMdd') + '.csv'
    $logFile = Join-Path (Join-Path $root 'logs') $today
    if (-not (Test-Path $logFile)) { return $null }
    try {
        $line = Get-Content $logFile -Tail 1 -ErrorAction Stop
        if (-not $line) { return $null }
        $parts = $line -split ','
        if ($parts.Count -lt 7) { return $null }
        return [PSCustomObject]@{
            ts     = $parts[0]
            room   = $parts[1]
            device = $parts[2]
            ip     = $parts[3]
            result = $parts[4]
            temp   = $parts[5]
            rtt    = $parts[6]
        }
    } catch { return $null }
}

function Get-LastRunInfo {
    if ($script:lastKnownCreation) { return "Last run started: $($script:lastKnownCreation.ToString('yyyy-MM-dd HH:mm:ss'))" }
    $latestReport = Get-ChildItem (Join-Path $root 'logs') -Filter 'report-*.txt' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestReport) { return "Last run ended: $($latestReport.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" }
    if (Test-Path $snapshotPath) {
        try {
            $snapTime = (Get-Content $snapshotPath -Raw | ConvertFrom-Json).updatedAt
            if ($snapTime) { return "Last check recorded: $(([DateTime]$snapTime).ToString('yyyy-MM-dd HH:mm:ss'))" }
        } catch {}
    }
    return 'Never run'
}

# ------------------------------------------------------------------ UI --
function New-Form {
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Shek Mun Monitor Control  v$script:version"
    $form.Size = New-Object System.Drawing.Size(600, 560)
    $form.FormBorderStyle = 'FixedDialog'
    $form.MaximizeBox = $false
    $form.StartPosition = 'CenterScreen'

    $layout = New-Object System.Windows.Forms.TableLayoutPanel
    $layout.Dock = 'Fill'
    $layout.Padding = New-Object System.Windows.Forms.Padding(8)
    $layout.ColumnCount = 1
    $layout.RowCount = 4
    $layout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('Percent', 32)))
    $layout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('Percent', 26)))
    $layout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('Percent', 24)))
    $layout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('Percent', 18)))

    # --- monitoring group ---
    $grpMon = New-Object System.Windows.Forms.GroupBox
    $grpMon.Text = 'Monitoring'
    $grpMon.Dock = 'Fill'
    $monLayout = New-Object System.Windows.Forms.TableLayoutPanel
    $monLayout.Dock = 'Fill'
    $monLayout.ColumnCount = 1
    $monLayout.RowCount = 4
    $monLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $monLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $monLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $monLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))

    $script:lblMonStatus = New-Object System.Windows.Forms.Label
    $script:lblMonStatus.Text = 'Status: Idle'
    $script:lblMonStatus.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
    $script:lblMonStatus.ForeColor = [System.Drawing.Color]::Gray

    $script:lblMonNow = New-Object System.Windows.Forms.Label
    $script:lblMonNow.Text = 'Now checking: -'
    $script:lblMonNow.AutoSize = $true
    $script:lblMonNow.Font = New-Object System.Drawing.Font('Segoe UI', 9)
    $script:lblMonNow.ForeColor = [System.Drawing.Color]::DimGray

    $script:lblMonLast = New-Object System.Windows.Forms.Label
    $script:lblMonLast.Text = 'Never run'
    $script:lblMonLast.ForeColor = [System.Drawing.Color]::DimGray

    $btnFlow = New-Object System.Windows.Forms.FlowLayoutPanel
    $btnFlow.Dock = 'Fill'
    $script:btnMonStart = New-Object System.Windows.Forms.Button
    $script:btnMonStart.Text = 'Start Monitoring'
    $script:btnMonStart.Width = 150
    $script:btnMonStart.Add_Click({ $script:logBuffer.Clear() -eq $null; Add-Log (Start-Monitoring) })
    $script:btnMonStop = New-Object System.Windows.Forms.Button
    $script:btnMonStop.Text = 'Stop'
    $script:btnMonStop.Width = 90
    $script:btnMonStop.Enabled = $false
    $script:btnMonStop.Add_Click({ Add-Log (Stop-Monitoring) })
    $btnFlow.Controls.Add($script:btnMonStart)
    $btnFlow.Controls.Add($script:btnMonStop)

    $monLayout.Controls.Add($script:lblMonStatus, 0, 0)
    $monLayout.Controls.Add($script:lblMonNow, 0, 1)
    $monLayout.Controls.Add($script:lblMonLast, 0, 2)
    $monLayout.Controls.Add($btnFlow, 0, 3)
    $grpMon.Controls.Add($monLayout)
    $layout.Controls.Add($grpMon, 0, 0)

    # --- temp monitor group ---
    $grpTemp = New-Object System.Windows.Forms.GroupBox
    $grpTemp.Text = 'Temp Monitor (Kramer KDS)'
    $grpTemp.Dock = 'Fill'
    $tempLayout = New-Object System.Windows.Forms.TableLayoutPanel
    $tempLayout.Dock = 'Fill'
    $tempLayout.ColumnCount = 1
    $tempLayout.RowCount = 4
    $tempLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $tempLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $tempLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $tempLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))

    $script:lblTempStatus = New-Object System.Windows.Forms.Label
    $script:lblTempStatus.Text = 'Status: Idle'
    $script:lblTempStatus.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
    $script:lblTempStatus.ForeColor = [System.Drawing.Color]::Gray

    $script:lblTempNow = New-Object System.Windows.Forms.Label
    $script:lblTempNow.Text = 'Now measuring: -'
    $script:lblTempNow.AutoSize = $true
    $script:lblTempNow.Font = New-Object System.Drawing.Font('Segoe UI', 9)
    $script:lblTempNow.ForeColor = [System.Drawing.Color]::DimGray

    $script:lblTempLast = New-Object System.Windows.Forms.Label
    $script:lblTempLast.Text = 'Never run'
    $script:lblTempLast.AutoSize = $true
    $script:lblTempLast.ForeColor = [System.Drawing.Color]::DimGray

    $tempBtnFlow = New-Object System.Windows.Forms.FlowLayoutPanel
    $tempBtnFlow.Dock = 'Fill'
    $script:btnTempStart = New-Object System.Windows.Forms.Button
    $script:btnTempStart.Text = 'Start Temp Monitor'
    $script:btnTempStart.Width = 150
    $script:btnTempStart.Add_Click({ Add-Log ("Temp monitor: " + (Start-TempMonitor)) })
    $script:btnTempStop = New-Object System.Windows.Forms.Button
    $script:btnTempStop.Text = 'Stop'
    $script:btnTempStop.Width = 90
    $script:btnTempStop.Enabled = $false
    $script:btnTempStop.Add_Click({ Add-Log ("Temp monitor: " + (Stop-TempMonitor)) })
    $tempBtnFlow.Controls.Add($script:btnTempStart)
    $tempBtnFlow.Controls.Add($script:btnTempStop)

    $tempLayout.Controls.Add($script:lblTempStatus, 0, 0)
    $tempLayout.Controls.Add($script:lblTempNow, 0, 1)
    $tempLayout.Controls.Add($script:lblTempLast, 0, 2)
    $tempLayout.Controls.Add($tempBtnFlow, 0, 3)
    $grpTemp.Controls.Add($tempLayout)
    $layout.Controls.Add($grpTemp, 0, 1)

    # --- dashboard group ---
    $grpDash = New-Object System.Windows.Forms.GroupBox
    $grpDash.Text = 'Dashboard'
    $grpDash.Dock = 'Fill'
    $dashLayout = New-Object System.Windows.Forms.TableLayoutPanel
    $dashLayout.Dock = 'Fill'
    $dashLayout.ColumnCount = 1
    $dashLayout.RowCount = 3
    $dashLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $dashLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))
    $dashLayout.RowStyles.Add((New-Object System.Windows.Forms.RowStyle('AutoSize')))

    $script:lblDashStatus = New-Object System.Windows.Forms.Label
    $script:lblDashStatus.Text = 'Server: Stopped'
    $script:lblDashStatus.Font = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)

    $portRow = New-Object System.Windows.Forms.FlowLayoutPanel
    $portRow.Dock = 'Fill'
    $portLabel = New-Object System.Windows.Forms.Label
    $portLabel.Text = 'Port:'
    $portLabel.AutoSize = $true
    $script:numPort = New-Object System.Windows.Forms.NumericUpDown
    $script:numPort.Minimum = 1024
    $script:numPort.Maximum = 65535
    $script:numPort.Value = $script:port
    $script:numPort.Width = 80
    $script:numPort.Add_ValueChanged({ $script:port = [int]$script:numPort.Value })
    $script:btnOpen = New-Object System.Windows.Forms.Button
    $script:btnOpen.Text = 'Launch Dashboard'
    $script:btnOpen.Width = 140
    $script:btnOpen.Add_Click({ Add-Log ("Dashboard: " + (Open-Dashboard $script:port)) })
    $script:btnStopDash = New-Object System.Windows.Forms.Button
    $script:btnStopDash.Text = 'Stop Server'
    $script:btnStopDash.Width = 90
    $script:btnStopDash.Enabled = $false
    $script:btnStopDash.Add_Click({ Add-Log ("Dashboard: " + (Stop-Dashboard)) })
    $portRow.Controls.Add($portLabel)
    $portRow.Controls.Add($script:numPort)
    $portRow.Controls.Add($script:btnOpen)
    $portRow.Controls.Add($script:btnStopDash)

    $script:lblDashLast = New-Object System.Windows.Forms.Label
    $script:lblDashLast.Text = ' '
    $script:lblDashLast.ForeColor = [System.Drawing.Color]::DimGray

    $dashLayout.Controls.Add($script:lblDashStatus, 0, 0)
    $dashLayout.Controls.Add($portRow, 0, 1)
    $dashLayout.Controls.Add($script:lblDashLast, 0, 2)
    $grpDash.Controls.Add($dashLayout)
    $layout.Controls.Add($grpDash, 0, 2)

    # --- log ---
    $script:logBox = New-Object System.Windows.Forms.TextBox
    $script:logBox.Multiline = $true
    $script:logBox.ReadOnly = $true
    $script:logBox.ScrollBars = 'Vertical'
    $script:logBox.Dock = 'Fill'
    $script:logBox.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 46)
    $script:logBox.ForeColor = [System.Drawing.Color]::LightGray
    $script:logBox.Font = New-Object System.Drawing.Font('Consolas', 9)
    $layout.Controls.Add($script:logBox, 0, 3)

    $form.Controls.Add($layout)

    $form.Add_FormClosing({
        Add-Log "Exiting v$script:version - stopping background processes..."
        Add-Log ("Monitoring: " + (Stop-Monitoring))
        Add-Log ("Temp:       " + (Stop-TempMonitor))
        Add-Log ("Dashboard:  " + (Stop-Dashboard))
        $script:formClosing = $true
    })

    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 1500
    $timer.Add_Tick({ Update-Status })
    return @{ form = $form; timer = $timer }
}

function Set-StatusLabel {
    param($Label, [string]$Text, [string]$Color)
    $Label.Text = $Text
    $Label.ForeColor = [System.Drawing.Color]::FromName($Color)
}

function Update-Status {
    $mp = Get-MonitorProcess
    $running = $null -ne $mp

    if ($running -and $null -eq $script:lastKnownPid) {
        $script:lastKnownPid = $mp.ProcessId
        $script:lastKnownCreation = $mp.CreationDate
        Add-Log "Monitoring detected: running (PID $($mp.ProcessId))"
    }
    if (-not $running -and $null -ne $script:lastKnownPid) {
        if ($script:monitorStopRequested) { Add-Log "Monitoring stopped (PID $script:lastKnownPid)." }
        else {
            $script:monitorError = "process ended unexpectedly"
            Add-Log "Monitoring ERROR - process ended unexpectedly (PID $script:lastKnownPid)."
            $errTail = Get-MonitorErrorTail
            if ($errTail) { Add-Log "Monitor error log tail: $errTail" }
        }
        $script:lastKnownPid = $null
        $script:monitorStopRequested = $false
    }

    if ($running) {
        if ($script:monitorError) { $script:monitorError = $null }
        $fresh = $true
        if (Test-Path $snapshotPath) {
            try {
                $snapAgeSec = ((Get-Date) - [DateTime]::Parse((Get-Content $snapshotPath -Raw | ConvertFrom-Json).updatedAt)).TotalSeconds
                $fresh = $snapAgeSec -lt 90
            } catch { $fresh = $true }
        }
        if ($fresh) { Set-StatusLabel $script:lblMonStatus 'Status: RUNNING' 'SeaGreen' }
        else { Set-StatusLabel $script:lblMonStatus 'Status: RUNNING (no recent checks)' 'DarkOrange' }
        $dur = (Get-Date) - $mp.CreationDate
        $script:lblMonLast.Text = "Last run started: $($mp.CreationDate.ToString('yyyy-MM-dd HH:mm:ss'))  (running for $([Math]::Floor($dur.TotalMinutes))m $($dur.Seconds)s)"
        $lastCheck = Get-LastCheckLine
        if ($lastCheck) {
            $clock = [DateTime]::Parse($lastCheck.ts).ToString('HH:mm:ss')
            if ($lastCheck.result -eq 'OK') {
                Set-StatusLabel $script:lblMonNow "Now checking: $($lastCheck.room) - $($lastCheck.device) (IP:$($lastCheck.ip)) - OK - $($lastCheck.rtt) ms - $clock" 'SeaGreen'
            } else {
                Set-StatusLabel $script:lblMonNow "Now checking: $($lastCheck.room) - $($lastCheck.device) (IP:$($lastCheck.ip)) - FAIL - $clock" 'Firebrick'
            }
        } else {
            Set-StatusLabel $script:lblMonNow 'Now checking: waiting for first check...' 'DimGray'
        }
    } elseif ($script:monitorError) {
        Set-StatusLabel $script:lblMonStatus 'Status: ERROR' 'Firebrick'
        $script:lblMonLast.Text = "$($script:monitorError) - " + (Get-LastRunInfo)
        Set-StatusLabel $script:lblMonNow 'Now checking: -' 'DimGray'
    } else {
        Set-StatusLabel $script:lblMonStatus 'Status: Idle' 'Gray'
        $script:lblMonLast.Text = Get-LastRunInfo
        Set-StatusLabel $script:lblMonNow 'Now checking: -' 'DimGray'
    }
    $script:btnMonStart.Enabled = -not $running
    $script:btnMonStop.Enabled = $running

    $tp = Get-TempProcess
    $tempRunning = $null -ne $tp

    if ($tempRunning -and $null -eq $script:lastKnownTempPid) {
        $script:lastKnownTempPid = $tp.ProcessId
        Add-Log "Temp monitor detected: running (PID $($tp.ProcessId))"
    }
    if (-not $tempRunning -and $null -ne $script:lastKnownTempPid) {
        if ($script:tempStopRequested) { Add-Log "Temp monitor stopped (PID $script:lastKnownTempPid)." }
        else {
            $script:tempError = "temp monitor ended unexpectedly"
            Add-Log "Temp monitor ERROR - process ended unexpectedly (PID $script:lastKnownTempPid)."
        }
        $script:lastKnownTempPid = $null
        $script:tempStopRequested = $false
    }

    if ($tempRunning) {
        if ($script:tempError) { $script:tempError = $null }
        Set-StatusLabel $script:lblTempStatus 'Status: RUNNING' 'SeaGreen'
        $lastTemp = Get-LastTempCheckLine
        if ($lastTemp) {
            $clock = [DateTime]::Parse($lastTemp.ts).ToString('HH:mm:ss')
            if ($lastTemp.result -eq 'OK') {
                Set-StatusLabel $script:lblTempNow "Now measuring: $($lastTemp.room) - $($lastTemp.device) (IP:$($lastTemp.ip)) - $($lastTemp.temp)C - OK - $clock" 'SeaGreen'
            } else {
                Set-StatusLabel $script:lblTempNow "Now measuring: $($lastTemp.room) - $($lastTemp.device) (IP:$($lastTemp.ip)) - FAIL - $clock" 'Firebrick'
            }
        } else {
            Set-StatusLabel $script:lblTempNow 'Now measuring: waiting for first reading...' 'DimGray'
        }
    } elseif ($script:tempError) {
        Set-StatusLabel $script:lblTempStatus 'Status: ERROR' 'Firebrick'
        Set-StatusLabel $script:lblTempNow 'Now measuring: -' 'DimGray'
    } else {
        Set-StatusLabel $script:lblTempStatus 'Status: Idle' 'Gray'
        Set-StatusLabel $script:lblTempNow 'Now measuring: -' 'DimGray'
    }
    $script:lblTempLast.Text = Get-TempLastInfo
    $script:btnTempStart.Enabled = -not $tempRunning
    $script:btnTempStop.Enabled = $tempRunning

    $dashRunning = Test-PortListening $script:port
    if ($dashRunning) {
        Set-StatusLabel $script:lblDashStatus "Server: RUNNING  http://localhost:$($script:port)" 'SeaGreen'
        $sp = Get-ServerProcess
        $script:lblDashLast.Text = if ($sp) { "Started: $($sp.CreationDate.ToString('HH:mm:ss'))" } else { ' ' }
    } else {
        Set-StatusLabel $script:lblDashStatus "Server: Stopped  (port $($script:port))" 'Gray'
        $script:lblDashLast.Text = ' '
    }
    $script:btnStopDash.Enabled = $dashRunning
}

# ------------------------------------------------------------ self-test --
if ($Test) {
    Write-Host '== Self test: monitoring start/stop =='
    $r1 = Start-Monitoring
    Write-Host "start: $r1"
    Start-Sleep -Seconds 5
    $detected = $null -ne (Get-MonitorProcess)
    Write-Host "detected running: $detected"
    $r2 = Stop-Monitoring
    Write-Host "stop: $r2"
    Start-Sleep -Seconds 1
    Write-Host "still running: $($null -ne (Get-MonitorProcess))"

    Write-Host '== Self test: dashboard start/stop =='
    $r3 = Start-Dashboard 8791
    Write-Host "dashboard: $r3"
    Write-Host "listening: $(Test-PortListening 8791)"
    $r4 = Stop-Dashboard
    Write-Host "stop: $r4"
    Start-Sleep -Seconds 1
    Write-Host "listening after stop: $(Test-PortListening 8791)"

    Write-Host '== Self test: temp monitor start/stop =='
    $r5 = Start-TempMonitor
    Write-Host "temp: $r5"
    Start-Sleep -Seconds 4
    Write-Host "detected running: $($null -ne (Get-TempProcess))"
    $r6 = Stop-TempMonitor
    Write-Host "stop: $r6"
    Start-Sleep -Seconds 1
    Write-Host "still running: $($null -ne (Get-TempProcess))"
    return
}

# ------------------------------------------------------------------ app --
$ui = New-Form
$ui.form.Add_Shown({
    $ui.timer.Start()
    Update-Status
    Add-Log "Auto-start: $((Start-Monitoring))"
    Add-Log "Auto-start: $((Start-TempMonitor))"
    Add-Log "Auto-start: $((Open-Dashboard $script:port))"
    Update-Status
})
[System.Windows.Forms.Application]::EnableVisualStyles()
[System.Windows.Forms.Application]::Run($ui.form)