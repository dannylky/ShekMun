# Shek Mun AV Monitoring - Development Notes

Compacted session history. Latest first. Repo: https://github.com/dannylky/ShekMun (private, branch `master`).

## Current state (HEAD: 1.7.8, `a92c6e4`)

System: monitors 287 AV devices across 9 rooms (SM-11-01..08 + Common Rm) over 2 VLANs, plus Kramer KDS unit temperatures, with web dashboards and a Windows desktop controller. Runs as 4 EXEs (deployment package) or scripts.

## Architecture

- **monitor.ps1** - ICMP loop, 287 devices from devices.json. Randomized intervals (master 10s +- 50% jitter, min 2s, timeout 3s). Writes logs/status-YYYYMMDD.csv, snapshot.json (debounced 1s), report files at end. Retry-protected I/O (survives file locks), errors -> logs/monitor-error.log.
- **temp-monitor.py** - Kramer KDS-SW3-EN7 (EN-*) + KDS-DEC7 (TV-DEC-*) + AVoIP-Manager temperatures via Protocol 3000 `#HW-TEMP? 0,0\r` on TCP 5000. 35 units, parallel (16 workers). Response format: `~01@HW-TEMP 0,36C` (not the reference code's 3-field format). Writes logs/temp-*.csv + temp-snapshot.json. Retry-protected (os.replace fails if file open - controller polls every 1.5s).
- **serve-dashboard.ps1** - HttpListener on 8080 (+port 80 unless -SkipPort80; port 80 released for IIS). Multi-listener loop via GetContextAsync/WaitAny. Serves all pages + snapshot.json.
- **monitor-control.ps1** - WinForms controller: Monitoring / Temp Monitor / Dashboard groups, auto-starts all on load, kills all on close, 1.5s polling, "Now checking"/"Now measuring" live lines, version in title.
- **build-deploy.ps1** - builds 4 EXEs (ps2exe x3, PyInstaller x1) and zips ShekMun-Monitor-v1.7.1.zip (34 MB incl. SOP docx). EXEs/dev deploy/ gitignored. creds.json never committed (gitignored; creds.json.example is the template).

### Key data
- Subnet 1: 172.18.2.0/23 (VLAN-1802 Control+Dante); Subnet 2: 172.18.22.0/24 (VLAN-1822)
- KDS manager: 172.18.22.5 (KDS-7-MNGR, Vue SPA, API needs login token - all creds rejected; snapshots at https://172.18.22.5/snap/<MAC>)
- MediaBox per room: 172.18.22.10x, snapshot at http://172.18.22.10x/snapshot/snapshot
- AVProc per room: 172.18.2.5x, tablet UI at http://172.18.2.5x:8000/tablet?max_col=4&max_row=2&min_col=0&pages=1|2 (Bitfocus Companion)
- PTZ cameras (OBSBOT): 172.18.22.8x web UI, 172.18.22.9x = Cam2
- dev IPs: TV-DEC-n = 172.18.22.(4n-3)..; EN-PC/Laptop-AVoIP = 172.18.22.1xx; SW-Lectern-2 moved to SM-11-02 @ .32 (was .31)

## Pages (tab bar: Main | Dashboard | PTZ | AVoIP | Passwords)

- **dashboard_shekmun.html** (Main) - overview: summary cards (devices/KDS/avg temp/OK rate), by-category strip, per-room cards with counts + max KDS temp, hot units list (>=45C), latest failures. Total count next to title.
- **dashboard.html** (Dashboard) - full device table, group chips (Video/Audio/Control), sort, room/category/page counts, device links http://IP (AVProc-Pi5 -> :8000), temp badges w/ update time, red last-update when stale >5min, TV-Res* excluded (11 devices), mediabox thumbnails (CAM_ENABLED=false).
- **ptc.html** (PTZ) - iframe -> dashboard_PTZ.html
- **dashboard_PTZ.html** - 9-block camera grid (SM01-SM08+Common Area, mediabox snapshots @0.1s, maximize/disable/URL edit). Control buttons (640x480 popup): SM02/04/06/07/08/Common single "Control"; SM01/03/05 dual "Control 1/2" (pages=1|2).
- **avoip.html** (AVoIP) - per-room Output(TV1/2/3/4,Audio)/Input(PC,Laptop) snapshot layouts from KDS manager MACs, 5s refresh staggered (self-healing errors, 1.5s retry), KDS temp badges (green <45C / red >=45C), device-name captions centered.
- **creds.html** (Passwords) - creds.json entries w/ copy + show/hide. Has: Control Processor, PTZ Camera, Media box, PCU, AVoIP Manager (admin/@Rcteacher1).
- **ptc.html + dashboard_PTZ.html** embed live views; old iframe target 10.107.147.121 (IIS, stale Aug-11 copy) was replaced by our repo copy.

## Version history (abridged)

- 1.0.0 - monitor system: monitor.ps1, config.json, devices.json, update-config.ps1, CHANGELOG, README
- 1.0.1 - auto report files; 1.1.0 - snapshot.json + dashboard.html + serve-dashboard.ps1
- 1.2.0 - desktop controller (WinForms); 1.3.0 - group filter/sort UI; 1.3.1 - refresh countdown + "Name (IP:...)"
- 1.4.0 - live "Now checking"; 1.4.1 - version in title, bigger boxes, kill procs on exit
- 1.4.2 - device links http://IP; 1.4.3 - exclude TV-Res; 1.4.4 - passwords page (creds.json gitignored); 1.4.5 - passwords link to toolbar
- 1.4.6 - monitor survives file-lock errors (SearchIndexer), error log; 1.4.7 - mediabox thumbnails (later disabled: 0.1s refresh too heavy)
- 1.5.0 - temp-monitor.py (KDS temps); 1.5.1 - temp control in controller; 1.5.2 - live "Now measuring"
- 1.5.3 - temps merged into snapshot by IP + colored badges; 1.5.4 - temp update time; 1.5.5 - controller auto-start all
- 1.5.6 - temp time beside value; 1.5.7 - AVoIP-Manager in temp monitor (35 units)
- 1.5.8 - LAN access: bind all interfaces + urlacl/firewall 8080 (elevated setup)
- 1.5.9 - controller ignores one-shot runs in process detection
- 1.6.0 - main page dashboard_shekmun.html + tab bar + port 80; 1.6.1 - PTC tab (iframe); 1.6.2 - port 80 released for IIS (-SkipPort80); 1.6.3 - PTC->PTZ tab, iframe -> 10.107.147.121
- 1.6.4 - temp monitor survives os.replace race (snapshot polled every 1.5s); 1.6.5 - red stale time >5min
- 1.7.0 - deployment package: EXEs (ps2exe+PyInstaller), build-deploy.ps1, $PSScriptRoot fallback for EXEs, backup taken first
- 1.7.1 - device counts per room/category/page; 1.7.2 - fix undefined $total; 1.7.3 - SW-Lectern-2 -> SM-11-02 @ .32
- 1.7.4 - AVoIP tab (SM-11-07 5-snap layout); 1.7.5 - video routing for SM-11-06 (removed in 1.7.6 - endpoint 404s, manager auth rejected)
- 1.7.7 - AVoIP self-healing thumbnails (manager intermittently 404s; burst refresh provoked rate limit)
- 1.7.8 - AVoIP temp badges + color var fix (--ok/--fail were missing)

## Known issues / gotchas

- KDS manager login (admin/@Rcteacher1 etc.) all rejected (code "1"); its routing API /api/control-add-signal-routing 404s - preset-based API (/presets/*) behind Bearer token. Video routing feature removed.
- KDS manager intermittently 404s snapshot requests (6/20 failed in test) - stagger + self-heal implemented.
- 11-02-PC-EN7 / Laptop-EN7 MACs return identical dark placeholder (units offline or wrong MAC).
- PS 5.1 gotchas: $PSScriptRoot empty in ps2exe EXEs; UTF8 BOM breaks ConvertFrom-Json (use utf-8-sig in python); CIM command-line queries can match the query process itself (exclude $PID); native stderr + ErrorActionPreference Stop kills scripts.
- Dashboard server died several times during builds (build-deploy kills running EXEs) - restart after builds; restart: Start-Process serve-dashboard.exe/ps1 -Port 8080 -SkipPort80.
- 10.107.147.121 (IIS) served a stale Aug-11 copy + 404s snapshot.json - our repo copy now used.
- Port 80: IIS owns it (503 until IIS serves); urlacl+firewall for 8080 done once (elevated); new ports need same setup.

## Backups
- C:\Work\Projects\ShekMun-Backup-20260817-085026 (pre-build)
- C:\Work\Projects\ShekMun-Backup-20260818-094739
- C:\Work\Projects\ShekMun-Backup-20260818-130002

## Pending / next

- Rebuild deployment package when needed: .\build-deploy.ps1 (stops running EXEs first; restart services after).
- Done: password gate (v1.7.9) - PTZ + AVoIP ask "rcteacher" only via IP/DNS; localhost free; sessionStorage unlock.
