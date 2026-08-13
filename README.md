# Shek Mun AV Monitoring

Continuous ICMP monitoring of the Shek Mun AV systems, one check scheduler per device
with randomized timing so devices are never all tested at the same instant.

## Desktop controller

`monitoring\monitor-control.ps1` - tiny WinForms app to control everything:

```powershell
.\monitoring\monitor-control.ps1
```

- Start / Stop the monitoring run, with live status (**Idle / Running / Error**)
  and the last run time (polled every 1.5 s)
- Launch Dashboard button - starts the dashboard server on the chosen port
  (default 8080) and opens the browser; shows server status and port
- State survives app restarts: a monitor/server already running is detected
  on load
- Headless self-test: `.\monitoring\monitor-control.ps1 -Test`

## Dashboard

The latest status of every device is kept in `monitoring/snapshot.json`
(written by the monitor, at most once per second, updated by both
one-shot and continuous runs).

```powershell
# terminal 1 - monitoring (any mode)
.\monitoring\monitor.ps1

# terminal 2 - web dashboard
.\monitoring\serve-dashboard.ps1          # default port 8080, use -Port to change
```

Open http://localhost:8080/dashboard.html

- Room blocks arranged 4 per row (by room ID), one row per device
- Each device shows its connection status dot, RTT and its own latest
  check time
- The header shows when the page last refreshed and when the snapshot
  was last updated
- The page auto-refreshes every 10 seconds

## Layout

```
monitoring/
  config.json          master interval + tuning (versioned)
  devices.json         device inventory, built from the SOP IP tables (versioned)
  monitor.ps1          the monitoring loop
  build-devices.ps1    regenerates devices.json when the SOP changes
  update-config.ps1    versioned config changes + changelog + git commit
  logs/                per-day CSV status logs (gitignored)
CHANGELOG.md           change history
```

## Quick start

```powershell
# 1. Generate the inventory (already committed - rerun only if SOP changed)
.\monitoring\build-devices.ps1

# 2. Run the monitor (Ctrl+C to stop)
.\monitoring\monitor.ps1
```

Run once without a loop: `.\monitoring\monitor.ps1 -OneShot`

## How scheduling works

- Each device's first check starts at a random offset in `[0, masterInterval]`,
  so devices are staggered at startup.
- After every check the next one is scheduled at
  `masterInterval +- random jitter` where `jitter = masterInterval * jitterFraction`,
  floored at `minIntervalSeconds`.
- Master interval is configurable and defaults to **10 seconds**; the per-device
  interval is randomized around it.

## Config

| Key | Default | Meaning |
|---|---|---|
| `masterIntervalSeconds` | 10 | base interval between checks per device |
| `jitterFraction` | 0.5 | random jitter as a fraction of the master interval (+-50%) |
| `minIntervalSeconds` | 2 | floor on the randomized interval |
| `timeoutMs` | 3000 | ICMP timeout per device |
| `logRetentionDays` | 30 | days to keep `logs/status-*.csv` |

Change it through the versioned helper (never edit by hand):

```powershell
.\monitoring\update-config.ps1 -Property masterIntervalSeconds -Value 15 -Message "Switch to 15s master interval"
```

This bumps the config version, appends a CHANGELOG.md entry, and commits to git.

## Change workflow

1. **Config change** -> `update-config.ps1` (version bump + changelog + git commit).
2. **Device inventory change** (SOP IP tables updated) -> edit the spec at the top of
   `build-devices.ps1`, then run it (version bump + changelog + git commit).
3. Every change lands in git; runtime logs stay local.

## Logs

- `logs/status-YYYYMMDD.csv` - one line per check: `timestamp,room,device,ip,result,rttMs`
- `logs/report-YYYYMMDD-HHmmss.txt` - written automatically at the end of every
  run (one-shot finish or Ctrl+C on a continuous session): summary, failures by
  room and role, and the full failure list
- Old CSV logs are pruned automatically after `logRetentionDays`
