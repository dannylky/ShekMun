<#
.SYNOPSIS
    Serves the monitoring folder over HTTP so the dashboards can read
    snapshot.json.

.DESCRIPTION
    Serves the monitoring folder on http://localhost:<Port> (default
    8080) and - when permissions allow - on all network interfaces
    (http://+:<Port>) so other machines on the LAN can open it. When
    the main port is not 80, the server also listens on port 80 so the
    main page is available as http://localhost/dashboard_shekmun.html.

    Main page:     /dashboard_shekmun.html
    Device list:   /dashboard.html
    Passwords:     /creds.html

    First-time LAN / port-80 setup needs elevated netsh commands
    (printed if a bind fails). Stop with Ctrl+C.

.EXAMPLE
    .\serve-dashboard.ps1
    .\serve-dashboard.ps1 -Port 9000
#>
[CmdletBinding()]
param(
    [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

function New-Listener {
    param([int]$LPort, [switch]$AllInterfaces)
    $l = [System.Net.HttpListener]::new()
    if ($AllInterfaces) { $l.Prefixes.Add("http://+:$LPort/") }
    else { $l.Prefixes.Add("http://localhost:$LPort/") }
    return $l
}

$listeners = [System.Collections.Generic.List[object]]::new()

$primary = New-Listener $Port -AllInterfaces
try {
    $primary.Start()
    $listeners.Add($primary)
} catch {
    $primary = New-Listener $Port
    $primary.Start()
    $listeners.Add($primary)
    $script:primaryLocalOnly = $true
}

if ($Port -ne 80) {
    $extra = New-Listener 80 -AllInterfaces
    try {
        $extra.Start()
        $listeners.Add($extra)
    } catch {
        $extra = New-Listener 80
        try {
            $extra.Start()
            $listeners.Add($extra)
        } catch {
            $extra.Stop()
            $script:port80Failed = $true
        }
    }
}

$mime = @{
    '.html' = 'text/html; charset=utf-8'
    '.json' = 'application/json; charset=utf-8'
    '.css'  = 'text/css'
    '.js'   = 'text/javascript'
    '.csv'  = 'text/csv'
    '.txt'  = 'text/plain'
    '.png'  = 'image/png'
}

$ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object -ExpandProperty IPAddress

Write-Host "Serving $root"
if ($script:primaryLocalOnly) {
    Write-Host "Main page: http://localhost:$Port/dashboard_shekmun.html (local only)"
    Write-Host 'WARNING: all-interface bind failed (permission denied).'
    Write-Host "Run once as admin, then rerun this script:"
    Write-Host "  netsh http add urlacl url=http://+:$Port/ user=$([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    Write-Host '  netsh advfirewall firewall add rule name="ShekMun dashboard" dir=in action=allow protocol=TCP localport='
} else {
    Write-Host "Main page: http://localhost:$Port/dashboard_shekmun.html"
    foreach ($ip in $ips) { Write-Host "Network:   http://$ip`:$Port/dashboard_shekmun.html" }
}
if ($listeners.Count -gt 1) {
    Write-Host "Port 80:   http://localhost/dashboard_shekmun.html"
} elseif ($script:port80Failed) {
    Write-Host 'WARNING: port 80 bind failed. Run once as admin for the port-80 URL:'
    Write-Host "  netsh http add urlacl url=http://+:80/ user=$([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    Write-Host '  netsh advfirewall firewall add rule name="ShekMun dashboard 80" dir=in action=allow protocol=TCP localport=80'
}
Write-Host "Press Ctrl+C to stop."

function Send-Response {
    param($Ctx)
    $res = $Ctx.Response
    try {
        $path = [System.Uri]::UnescapeDataString($Ctx.Request.Url.AbsolutePath).TrimStart('/')
        if ($path -eq '') { $path = 'dashboard_shekmun.html' }
        $full = [System.IO.Path]::GetFullPath((Join-Path $root $path))

        if (-not $full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
            $res.StatusCode = 403
        } elseif (Test-Path -LiteralPath $full -PathType Leaf) {
            $bytes = [System.IO.File]::ReadAllBytes($full)
            $ext = [System.IO.Path]::GetExtension($full).ToLowerInvariant()
            $res.ContentType = if ($mime.ContainsKey($ext)) { $mime[$ext] } else { 'application/octet-stream' }
            $res.ContentLength64 = $bytes.Length
            $res.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $res.StatusCode = 404
            $msg = "Not found: $path"
            $data = [System.Text.Encoding]::UTF8.GetBytes($msg)
            $res.ContentLength64 = $data.Length
            $res.OutputStream.Write($data, 0, $data.Length)
        }
    } finally {
        $res.Close()
    }
}

$pairs = [System.Collections.Generic.List[object]]::new()
foreach ($l in $listeners) { $pairs.Add(@{ l = $l; t = $l.GetContextAsync() }) }

try {
    while ($pairs.Count -gt 0) {
        $arr = @($pairs | ForEach-Object { $_.t })
        $idx = [System.Threading.Tasks.Task]::WaitAny($arr)
        if ($idx -ge 0) {
            $done = $pairs[$idx]
            $pairs.RemoveAt($idx)
            $ctx = $done.t.Result
            Send-Response $ctx
            if ($done.l.IsListening) { $pairs.Add(@{ l = $done.l; t = $done.l.GetContextAsync() }) }
        }
        if ($pairs.Count) {
            $kept = @($pairs | Where-Object { $_.l.IsListening })
            $pairs = [System.Collections.Generic.List[object]]::new()
            foreach ($x in $kept) { $pairs.Add($x) }
        }
    }
} finally {
    foreach ($pair in $pairs) { $pair.l.Stop() }
}
