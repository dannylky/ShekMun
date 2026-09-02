<#
.SYNOPSIS
    Builds the Shek Mun Monitor deployment package (EXEs + web pages +
    config + SOP docs) and zips it.

.DESCRIPTION
    Prereqs (one-time on the build machine):
      Install-Module ps2exe -Scope CurrentUser
      pip install pyinstaller

    The EXEs are rebuilt here from the scripts in monitoring\. Then the
    package folder ShekMun-Monitor-v<version>\ is assembled and zipped
    to ShekMun-Monitor-v<version>.zip.

    Deliberately EXCLUDED from the package:
      - monitoring\creds.json (real passwords - copy it manually after
        unzipping; creds.json.example is included as a template)
      - snapshot.json / temp-snapshot.json (regenerated at runtime)
      - logs\ contents (runtime data)
      - .git, dev-only scripts (build-devices.ps1, update-config.ps1)

.EXAMPLE
    .\build-deploy.ps1
#>
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$mon = Join-Path $repo 'monitoring'
$version = '1.9.0'
$pkgName = "ShekMun-Monitor-v$version"
$pkgRoot = Join-Path $repo 'deploy'
$pkgDir = Join-Path $pkgRoot $pkgName
$zipPath = Join-Path $pkgRoot "$pkgName.zip"

if (-not (Get-Module -ListAvailable ps2exe)) { throw 'ps2exe module missing - Install-Module ps2exe -Scope CurrentUser' }
if (-not (python -m PyInstaller --version 2>$null)) { throw 'PyInstaller missing - pip install pyinstaller' }

Write-Host "== Building $pkgName =="

# ---- 0. stop any running instances so the EXEs can be overwritten ----
foreach ($exeName in @('monitor.exe', 'serve-dashboard.exe', 'temp-monitor.exe', 'monitor-control.exe')) {
    Get-CimInstance Win32_Process -Filter "Name = '$exeName'" -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 1
Write-Host "  (stopped running instances; restart services after the build if needed)"

# ---- 1. rebuild the EXEs from the current scripts ----
Import-Module ps2exe
foreach ($f in @('monitor', 'serve-dashboard', 'monitor-control')) {
    Invoke-PS2EXE -InputFile (Join-Path $mon "$f.ps1") -OutputFile (Join-Path $mon "$f.exe") | Out-Null
    Write-Host "  built $f.exe"
}
$oldEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$pyLog = Join-Path $env:TEMP 'shekmun-pyinstaller.log'
python -m PyInstaller --onefile --name temp-monitor --distpath $mon `
    --workpath (Join-Path $env:TEMP 'shekmun-pybuild') `
    --specpath (Join-Path $env:TEMP 'shekmun-pybuild') `
    (Join-Path $mon 'temp-monitor.py') *> $pyLog
$ErrorActionPreference = $oldEAP
if ($LASTEXITCODE -ne 0) { Get-Content $pyLog | Select-Object -Last 20; throw "PyInstaller failed (exit $LASTEXITCODE)" }
if (-not (Test-Path (Join-Path $mon 'temp-monitor.exe'))) { throw 'temp-monitor.exe build failed' }
Write-Host "  built temp-monitor.exe"

# ---- 2. assemble the package folder ----
if (Test-Path $pkgDir) { Remove-Item $pkgDir -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $pkgDir 'monitoring\logs') -Force | Out-Null

$files = @(
    'monitor.exe', 'serve-dashboard.exe', 'monitor-control.exe', 'temp-monitor.exe',
    'dashboard_shekmun.html', 'dashboard.html', 'creds.html', 'ptc.html',
    'avoip.html', 'dashboard_PTZ.html', 'ops-guide.html',
    'config.json', 'devices.json', 'creds.json.example'
)
foreach ($f in $files) { Copy-Item (Join-Path $mon $f) (Join-Path $pkgDir "monitoring\$f") }
Copy-Item (Join-Path $repo 'Shek Mun SOP Original.docx') $pkgDir
Copy-Item (Join-Path $repo 'Shek Mun SOP Short.docx') $pkgDir
Copy-Item (Join-Path $repo 'INSTALLATION-GUIDE.md') $pkgDir

# ---- 3. launcher + one-time setup + runbook ----
@'
@echo off
title Shek Mun Monitor Control
start "" "%~dp0monitoring\monitor-control.exe"
'@ | Set-Content -Path (Join-Path $pkgDir 'Start Monitor Control.bat') -Encoding ASCII

@'
@echo off
REM ============================================================
REM  Shek Mun Monitor - one-time setup. Run as Administrator.
REM ============================================================
title Shek Mun Monitor - Setup
netsh http add urlacl url=http://+:8080/ user=%USERDOMAIN%\%USERNAME%
netsh advfirewall firewall add rule name="ShekMun dashboard 8080" dir=in action=allow protocol=TCP localport=8080

REM desktop shortcut
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Shek Mun Monitor Control.lnk'); $s.TargetPath='%~dp0Start Monitor Control.bat'; $s.WorkingDirectory='%~dp0'; $s.Save()"
echo.
echo Setup complete. Close this window.
pause
'@ | Set-Content -Path (Join-Path $pkgDir 'setup-once.bat') -Encoding ASCII

@"
Shek Mun Monitor - v$version
============================

WHAT THIS IS
  Continuous monitoring of the Shek Mun AV network (287 devices, 9 rooms)
  plus Kramer KDS unit temperatures (44 units incl. AVoIP manager and
  Audio-DEC decoders) and a web dashboard with Main / Dashboard / PTZ /
  AVoIP / Passwords tabs.

SETUP (one time, 2 minutes)
  1. Copy this whole folder to the target PC (any location).
  2. Copy your monitoring\creds.json into monitoring\ (real passwords
     are kept out of the package on purpose; creds.json.example shows
     the format).
  3. Right-click setup-once.bat -> Run as administrator (adds the
     port-8080 URL ACL, firewall rule, and a desktop shortcut).
  4. Make sure the PC can reach the AV network (172.18.2.x / 172.18.22.x).

RUNNING
  Double-click "Start Monitor Control" (or the desktop shortcut).
  The controller auto-starts:
    - device monitor     (monitor.exe)
    - temp monitor       (temp-monitor.exe, incl. Audio-DEC temps)
    - dashboard server   (serve-dashboard.exe, port 8080)
  and opens the main page http://localhost:8080/dashboard_shekmun.html
  in the browser.

  Closing the controller window stops all three background processes.

URLS
  Main page:     http://localhost:8080/dashboard_shekmun.html
  Device list:   http://localhost:8080/dashboard.html
  PTZ grid:      http://localhost:8080/ptc.html
  AVoIP view:    http://localhost:8080/avoip.html
  Passwords:     http://localhost:8080/creds.html
  LAN access:    http://<this-pc-ip>:8080/... (after setup-once.bat)

  On localhost the PTZ / AVoIP / Passwords pages need NO password.
  Accessed remotely (IP/DNS), PTZ and AVoIP ask for password
  "rcteacher1" (remembered per browser tab); the Passwords tab is
  hidden remotely and the creds page itself is always password
  protected.

DATA & LOGS
  monitoring\logs\    status CSVs, reports, temp CSVs, error logs
  monitoring\snapshot.json / temp-snapshot.json   (regenerated)

TROUBLESHOOTING
  - Controller shows ERROR: check monitoring\logs\monitor-error.log
    and temp-monitor-error.log.
  - Port 8080 conflict: stop whatever owns it, or change the port in
    the controller (Port box) - then rerun setup-once.bat for that
    port.
  - Dashboard unreachable: firewall/URL ACL - rerun setup-once.bat.
  - TV-Res* display resolvers are shown as "excluded" on the pages
    (they are monitored but not displayed).

See INSTALLATION-GUIDE.md for the full walkthrough.
"@ | Set-Content -Path (Join-Path $pkgDir 'README-RUN.txt') -Encoding UTF8

# ---- 4. zip it ----
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $pkgRoot "$pkgName\*") -DestinationPath $zipPath
$mb = [Math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Host ""
Write-Host "Package: $zipPath ($mb MB)"
Write-Host "Contents:"
Get-ChildItem $pkgDir -Recurse -File | ForEach-Object { Write-Host "  $($_.FullName.Replace($pkgDir, '.'))" }
