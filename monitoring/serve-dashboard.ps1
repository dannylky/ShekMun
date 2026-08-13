<#
.SYNOPSIS
    Serves the monitoring folder over HTTP so the dashboard can read
    snapshot.json.

.DESCRIPTION
    Serves dashboard.html, snapshot.json and any other files in this
    folder on http://localhost:<Port> and - when permissions allow -
    on all network interfaces (http://+:<Port>) so other machines on
    the LAN can open the dashboard. First-time LAN setup needs one
    elevated netsh command (printed if the all-interface bind fails).
    Stop with Ctrl+C.

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

$listener = [System.Net.HttpListener]::new()
$servingAll = $true
$listener.Prefixes.Add("http://+:$Port/")
try {
    $listener.Start()
} catch {
    $listener.Prefixes.Clear()
    $listener.Prefixes.Add("http://localhost:$Port/")
    $listener.Start()
    $servingAll = $false
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

Write-Host "Serving $root"
if ($servingAll) {
    $ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
        Select-Object -ExpandProperty IPAddress
    Write-Host "Dashboard: http://localhost:$Port/dashboard.html"
    foreach ($ip in $ips) { Write-Host "Network:   http://$ip`:$Port/dashboard.html" }
} else {
    Write-Host "Dashboard: http://localhost:$Port/dashboard.html"
    Write-Host 'WARNING: binding to all interfaces failed (permission denied).'
    Write-Host "To allow LAN access, run once as admin:"
    Write-Host "  netsh http add urlacl url=http://+:$Port/ user=$([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    Write-Host '  netsh advfirewall firewall add rule name="ShekMun dashboard" dir=in action=allow protocol=TCP localport='
    Write-Host "  (then rerun this script - no more admin needed on this machine)"
}
Write-Host "Press Ctrl+C to stop."

try {
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        $res = $ctx.Response
        try {
            $path = [System.Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath).TrimStart('/')
            if ($path -eq '') { $path = 'dashboard.html' }
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
} finally {
    $listener.Stop()
}