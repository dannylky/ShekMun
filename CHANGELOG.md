# Changelog

All notable changes to the Shek Mun monitoring system. Newest first.

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
