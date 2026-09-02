# Changelog

All notable changes to the Shek Mun monitoring system. Newest first.

## [1.9.2] - 2026-09-02
- Suspended-device support (suspended.js, shared by both dashboard
  pages): 12 devices (Speaker-9-USBMac in SM-11-02; 11 in Common Rm)
  are kept in the dashboard but marked "suspended" while offline -
  they are NOT counted as failures and do not trigger red room/card
  status. When a suspended device comes back online it resumes normal
  status display automatically. Counts now show "N suspended" where
  applicable.

## [1.9.1] - 2026-09-02
- PTZ and AVoIP remote-access gate password changed from "rcteacher"
  to "rcteacher1". The Passwords page (creds.html) keeps "rcteacher".
  Docs (README-RUN, INSTALLATION-GUIDE) updated to match.

## [1.9.0] - 2026-08-26
- New "Operation Guide" tab/page (ops-guide.html): Operation Rules
  (power schedule On 0700 / Off 12:01 managed by PoE Switch and PCU;
  normal AVoIP device temperature range 33-45C) and Documentations
  (5 SharePoint SOP/spec links, opened in new tabs). Tab added to all
  pages; page included in the deployment package.
- Operation Guide doc links display as short "Open" links (full URL in
  the href and shown on hover).
- Operation Guide page: larger fonts across the whole page; parts
  numbered (Part 1 Rules / Part 2 Documentations); new Part 3 FAQ
  (mic pairing, room combine/separate, mic count per room, WiFi and
  print queue issues - the latter two awaiting answers).

## [1.8.4] - 2026-08-21
- PTZ page: every room block (SM01-SM08 + Common Area) gets a
  "Control System" button opening https://172.18.2.3X/web/vtlp/.../
  index.html#!/main in a popup, alongside the existing Control
  buttons.

## [1.8.3] - 2026-08-19 (deployment)
- Deployment package rebuilt: deploy\ShekMun-Monitor-v1.8.3.zip (34.1 MB).
  Package now also includes avoip.html and dashboard_PTZ.html (the
  v1.7.0 package was missing them). All EXEs rebuilt from current
  scripts (monitor, serve-dashboard, monitor-control, temp-monitor
  incl. Audio-DEC temps).
- New INSTALLATION-GUIDE.md (repo root + included in the package):
  full install/upgrade/troubleshooting walkthrough.
- README-RUN.txt in the package updated for current tabs, password
  gates, TV-Res exclusion and temp monitoring.

## [1.8.3] - 2026-08-19
- Password gate (PTZ, AVoIP, Passwords pages): added a "Back" button
  next to Unlock - goes back in history, or to the Main page if there
  is no history.
- PTZ and AVoIP tabs show a lock symbol when accessed remotely
  (matching the password-protected state); no lock on localhost.

## [1.8.2] - 2026-08-19
- Main page (dashboard_shekmun.html) now excludes TV-Res devices too,
  matching the Dashboard page. Both pages show the same total (276 of
  287) and same per-room counts. Excluded count is shown in the Devices
  card ("11 excluded (TV-Res)").

## [1.8.1] - 2026-08-19
- Audio-DEC (KDS-DEC7 audio decoders, 172.18.22.181-189) now included in
  temperature monitoring (44 units total). Their temps appear on the
  Dashboard rows and AVoIP page Audio-DEC thumbnails automatically
  (merge is by IP). temp-monitor.exe rebuilt and restarted.

## [1.8.0] - 2026-08-19
- Version number ("v1.8.0") shown in footers/meta of all pages
  (dashboard_shekmun, dashboard, ptc, avoip, creds).
- Passwords page (creds.html): now requires password "rcteacher" on
  ALL access (localhost included). Unlock remembered per tab
  (sessionStorage).
- Passwords tab hidden when accessed remotely: every tab-bar page
  removes the creds.html link via JS unless hostname is
  localhost/127.0.0.1.

## [1.7.9] - 2026-08-18
- PTZ and AVoIP pages: remote-access password gate (password
  "rcteacher"). Prompt only appears when accessed via IP/DNS -
  localhost and 127.0.0.1 are password-free. Unlock is remembered
  per browser tab session (sessionStorage).

## [1.7.8] - 2026-08-18
- AVoIP page: each thumbnail now shows the latest KDS temperature
  badge (top-right corner), matched from snapshot.json by parsing the
  device label (11-XX-TVn-DEC7 -> TV-DEC-n, Audio-DEC7 -> Audio-DEC,
  PC-EN7 -> EN-PC-AVoIP, Laptop-EN7 -> EN-Laptop-AVoIP). Green below
  45C, red at/above 45C, "--" when no reading. Updated every 10s.

## [1.7.7] - 2026-08-18
- Bugfix: AVoIP thumbnails (e.g. 11-01-TV2-DEC7) showing persistent
  "unavailable". Root cause: the Kramer manager intermittently 404s
  snapshot requests (6/20 failed in testing), and the page (1) killed
  the img element on error so it could never recover, and (2) fired
  all ~42 refreshes in one burst every 5s, provoking the manager's
  rate limit. Now: errors are non-destructive and self-heal on the
  next retry (failed cells retry after 1.5s), and refreshes are
  staggered per cell to avoid bursts.

## [1.7.6] - 2026-08-18
- Removed the video route function (SM-11-06 dropdown, Route button
  and the /api/routing proxy) - the manager firmware (KDS-7-MNGR)
  doesn't expose the reference API endpoint.

## [1.7.5] - 2026-08-18
- AVoIP tab: video routing for SM-11-06 - a dropdown lets you route
  11-06-TV1-DEC7 from 11-06-PC-EN7 or 11-04-PC-EN7. Calls
  POST /api/control-add-signal-routing on 172.18.22.5 (signalType
  VIDEO, MACs in colon form) via a same-origin proxy
  (serve-dashboard.ps1 /api/routing) to avoid browser CORS.
- Note: the live manager returns 404 for that endpoint (its web app
  requires a login token; none of the known credentials accepted).

## [1.7.4] - 2026-08-18
- New "AVoIP" tab: avoip.html shows each room in a block view. Room 7
  (SM-11-07) has 5 live snapshots from the Kramer manager
  (172.18.22.5/snap/...) laid out as TV1 (top-left), Audio-DEC7
  (top-middle), TV2 (top-right), PC-EN7 (bottom-left),
  Laptop-EN7 (bottom-right); refreshed every 5s. Other rooms show a
  placeholder. Tab added to all pages.

## [1.7.3] - 2026-08-18
- devices.json: SW-Lectern-2 moved from SM-11-01 to SM-11-02 and its
  IP changed 172.18.22.31 -> 172.18.22.32 (172.18.22.23 was already
  taken by SM-11-03/SW-Lectern). Monitor restarted with the new
  inventory; dashboards reflect it via snapshot.json.

## [1.7.2] - 2026-08-18
- Bugfix: dashboard page-total count referenced an undefined variable
  ($total), breaking render() ("$total is not defined" + stale
  snapshot error banner). Now uses the correct total variable.

## [1.7.1] - 2026-08-18
- Dashboard: device counts added - per room next to the room name,
  per category next to the category name (Video/Audio/Control), and
  the total for all rooms next to the page title. Main page also
  shows a "By category" strip.

## [1.7.0] - 2026-08-17
- Deployment package: build-deploy.ps1 compiles the system into 4
  EXEs (monitor, serve-dashboard, monitor-control via ps2exe;
  temp-monitor via PyInstaller onefile) and zips
  ShekMun-Monitor-v1.7.0.zip (34 MB, incl. SOP docx files).
  Contents: EXEs + web pages + config + devices + creds template +
  Start Monitor Control.bat + setup-once.bat + README-RUN.txt.
  Creds.json stays out of the package (copied manually after unzip).
- EXE portability: scripts now resolve their folder via the exe path
  when $PSScriptRoot is empty (PS2EXE quirk); controller spawns and
  detects the EXE processes, falling back to scripts when no EXEs
  are present. Verified: controller self-test, temp one-shot, LAN
  serving all pass from the packaged copy.
- Repo backup taken before the build:
  C:\Work\Projects\ShekMun-Backup-20260817-085026

## [1.6.5] - 2026-08-14
- Dashboard: device last-update time turns bold red when older than
  5 minutes (devices that stopped reporting stand out).

## [1.6.4] - 2026-08-14
- Bugfix: temp monitor could die when writing temp-snapshot.json -
  os.replace fails on Windows if the controller is reading the file
  (it polls every 1.5 s). Snapshot/CSV writes now retry and the
  pass/loop never crash on I/O errors; failures go to
  logs\temp-monitor-error.log. Verified under read-hammering.

## [1.6.3] - 2026-08-13
- Tab renamed PTC -> PTZ; its iframe now loads
  http://10.107.147.121/dashboard_shekmun.html (verified HTTP 200).

## [1.6.2] - 2026-08-13
- Port 80 released for Microsoft IIS: serve-dashboard.ps1 gained a
  -SkipPort80 switch (controller uses it), the port-80 URL ACL and
  firewall rule were removed. Server now runs on 8080 only.

## [1.6.1] - 2026-08-13
- New "PTC" tab: ptc.html embeds http://localhost/dashboard_shekmun.html
  (port 80) in an iframe; tab added to all pages.

## [1.6.0] - 2026-08-13
- New main page dashboard_shekmun.html: overview with summary cards
  (devices, KDS temps, avg temp, OK rate), per-room cards with max
  KDS temp, hot-unit list (>=45C) and latest failures. All three
  pages (Main / Dashboard / Passwords) share a top tab bar.
- Server also listens on port 80, so the main page is available as
  http://localhost/dashboard_shekmun.html (plus the 8080 URL). Port
  80 URL ACL + firewall rule added (elevated). Controller opens the
  main page.

## [1.5.9] - 2026-08-13
- Bugfix: controller no longer misdetects one-shot runs (monitor
  -OneShot / temp --one-shot) as the live process - it only tracks
  continuous processes, so running one-shot passes no longer trigger
  a false "process ended unexpectedly" error.

## [1.5.8] - 2026-08-13
- Dashboard server: binds all interfaces (http://+:<port>) so other
  machines on the LAN can open the dashboard; prints LAN URLs on
  start; falls back to localhost-only with setup instructions if
  Windows denies the bind. One-time elevated setup performed
  (URL ACL + firewall rule for port 8080) and verified - HTTP 200
  via LAN IPs.

## [1.5.7] - 2026-08-13
- Temp monitor: now also monitors the AVoIP-Manager (172.18.22.5) -
  35 units total. It flows through to the dashboard automatically via
  the snapshot merge (Shared / Unique section, temp badge 27C).

## [1.5.6] - 2026-08-13
- Dashboard: temperature badge now shows the update time right beside
  the value (e.g. "36C 14:39:22", time in muted small text).

## [1.5.5] - 2026-08-13
- Desktop controller: auto-starts everything on load - monitoring,
  temp monitor and dashboard server + browser (skipped if already
  running), with each action logged.

## [1.5.4] - 2026-08-13
- Dashboard: KDS temperature update time shown in the header line
  ("KDS temps updated: HH:mm:ss", from snapshot's tempUpdatedAt) and
  in the tooltip of each temperature badge.

## [1.5.3] - 2026-08-13
- monitor.ps1 now merges the latest Kramer KDS temperatures (from
  temp-monitor.py's temp-snapshot.json) into snapshot.json per IP
  (tempC + tempAt fields).
- Dashboard: KDS units show their temperature right beside the device
  name - green below 45C, red at/above 45C.

## [1.5.2] - 2026-08-13
- Desktop controller: Temp Monitor box now shows a live "Now
  measuring" line - the latest unit read (room, device, IP, temp,
  result, time) from the temp CSV, colored green/red like the
  monitoring box.

## [1.5.1] - 2026-08-13
- Desktop controller: new "Temp Monitor (Kramer KDS)" group with
  Start/Stop for temp-monitor.py, live status (idle/running/error)
  and last-pass summary (OK count + min/max temp) from
  temp-snapshot.json; closing the app also stops the temp monitor.

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
