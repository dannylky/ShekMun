<#
.SYNOPSIS
    Serves the monitoring folder over HTTP so the dashboard can read
    snapshot.json.

.DESCRIPTION
    Serves dashboard.html, snapshot.json and any other files in this
    folder on http://localhost:<Port>. No admin rights needed. Stop
    with Ctrl+C.

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
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()

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
Write-Host "Dashboard: http://localhost:$Port/dashboard.html"
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