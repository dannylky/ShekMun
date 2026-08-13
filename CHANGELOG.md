# Changelog

All notable changes to the Shek Mun monitoring system. Newest first.

## [1.5.0] - 2026-08-13
- New: temp-monitor.py - standalone process monitoring system
  temperature of all Kramer KDS-SW3-EN7 (EN-*) and KDS-DEC7
  (TV-DEC-*) units via Protocol 3000 (#HW-TEMP? 0,0, TCP 5000).
  Auto-selects units from devices.json (AVoIP subnet only), queries in
  parallel, logs to logs\temp-YYYYMMDD.csv and writes
  temp-snapshot.json for the dashboard (gitignored). Verified against
  the live units - response format "~01@HW-TEMP 0,36C" parsed.

## [1.4.7] - 2026-08-13
- Dashboard: each room header now shows a small live thumbnail from
  that room's MediaBox (http://IP/snapshot/snapshot, IP taken from
  devices.json - e.g. SM-11-01 -> 172.18.22.101), refreshed every
  60 s, hidden if unreachable, clickable to the MediaBox web UI.

## [1.4.6] - 2026-08-13
- Bugfix: monitor no longer dies on transient file-lock errors (e.g.
  Windows Search indexer briefly holding status-*.csv). CSV log and
  snapshot writes now retry 3x before giving up; per-device checks are
  guarded; all I/O/check failures go to logs\monitor-error.log.
- Controller: when the monitor ends unexpectedly it now shows the
  tail of monitor-error.log in the log box so the cause is visible.

## [1.4.5] - 2026-08-13
- Dashboard: "Device passwords" link moved from the header into the
  toolbar as a prominent pill button (right of the sort control).

## [1.4.4] - 2026-08-13
- Dashboard: new "Device passwords" page (creds.html) listing
  usernames/passwords with copy and show/hide buttons. Credentials
  live in monitoring\creds.json which is gitignored - they are never
  committed or pushed (creds.json.example is the committed template).

## [1.4.3] - 2026-08-13
- Dashboard: devices named "TV-Res*" are excluded from display and
  counts (summary shows how many are excluded); monitoring still
  pings them.

## [1.4.2] - 2026-08-13
- Dashboard: device names are now clickable links to http://IP
  (opens in a new tab, accent-colored with hover underline).

## [1.4.1] - 2026-08-13
- Desktop controller: version number in the title bar; window enlarged
  to 600x560 with the Monitoring/Dashboard boxes and log sized
  42/33/25%; closing the app now stops the monitor and the dashboard
  server (all background processes are killed).

## [1.4.0] - 2026-08-13
- Desktop controller: Monitoring box now shows a live "Now checking"
  line - current device (room, name, IP, result, RTT) from the latest
  status-CSV row, colored green/red, refreshed every 1.5 s; the
  last-run line also shows elapsed run time.

## [1.3.1] - 2026-08-13
- Dashboard: added a live "Refresh in Ns" countdown next to the page
  updated time; device names now show as "Name (IP:xxx.xxx.xxx.xxx)".

## [1.3.0] - 2026-08-13
- Dashboard: added group filtering (Video / Audio / Control chips,
  multi-select) and sorting (by group, by name, by status - failures
  first). Role-to-group mapping: display/camera/media/avoip = Video,
  dante/audio = Audio, control/switch = Control. Devices are sectioned by
  group inside each room block when sorted by group; a summary line shows
  visible/total counts.

## [1.2.0] - 2026-08-13
- Added `monitoring/monitor-control.ps1`: desktop controller app (WinForms)
  with Start/Stop monitoring buttons, live status (idle/running/error),
  last run time, and a Launch Dashboard button showing port + server status.
  State survives app restarts; includes a headless self-test mode (-Test).
- Fixed monitor.ps1 to not use `$PSScriptRoot` inside param() default
  values (empty when spawned via `powershell -File`), which broke
  programmatic start.

## [1.1.0] - 2026-08-13
- Added a live status snapshot: the monitor writes `monitoring/snapshot.json`
  (latest status per device, debounced to one write per second) for both
  one-shot and continuous runs.
- Added `monitoring/dashboard.html`: web dashboard reading the snapshot,
  auto-refreshing every 10 seconds. Room blocks arranged 4 per row, per-device
  status dot / RTT / latest check time, plus page and snapshot update times.
- Added `monitoring/serve-dashboard.ps1`: zero-dependency HTTP server for the
  dashboard (default http://localhost:8080).

## [1.0.1] - 2026-08-13
- Runs now save their results into the project folder automatically:
  every run (one-shot or continuous session end) writes
  `monitoring/logs/report-YYYYMMDD-HHmmss.txt` with summary, failures by
  room/role, and the full failure list. No manual console redirection needed.
- Continuous sessions report each failing device once per session in the
  report file.

## [1.0.0] - 2026-08-13
- Initial release of the monitoring system.
- Inventory built from the IP assignment tables in "Shek Mun SOP Short.docx".
- Devices: 9 rooms (SM-11-01..08 + Common Rm), 283 room devices + 4 unique (DSP-Ctrl, DSP-Dante, XSM4216F, AVoIP-Manager).
- Per-room IPs increment by +1 across the table columns (e.g. Speaker-3: .181, .182, ... .189).
- Correction: SM-11-05 Dock-2ch documented as 172.18.2.65 duplicates the 4ch block; corrected to 172.18.2.75.
- Naming: encoders exist on both subnets, disambiguated as EN-PC-Dante / EN-PC-AVoIP, EN-Laptop-Dante / EN-Laptop-AVoIP, EN-Mac-Dante / EN-Mac-AVoIP.
- Config: master interval 10s, jitter 50%, timeout 3s, log retention 30 days.
