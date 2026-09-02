# Shek Mun Monitor - Installation Guide (v1.8.3)

Deployment package: `deploy\ShekMun-Monitor-v1.8.3.zip`

This guide installs the Shek Mun AV monitoring system on a Windows PC
running as the monitoring station.

---

## 1. What the package contains

```
ShekMun-Monitor-v1.8.3\
|-- Start Monitor Control.bat   <- launcher (double-click to run)
|-- setup-once.bat              <- one-time setup (run as admin)
|-- README-RUN.txt              <- quick reference
|-- INSTALLATION-GUIDE.md       <- this file
|-- Shek Mun SOP Original.docx
|-- Shek Mun SOP Short.docx
`-- monitoring\
    |-- monitor.exe             <- 287-device ping monitor
    |-- temp-monitor.exe        <- Kramer KDS temperatures (44 units)
    |-- serve-dashboard.exe     <- web server (port 8080)
    |-- monitor-control.exe     <- desktop controller (starts/stops all)
    |-- dashboard_shekmun.html  <- Main overview page
    |-- dashboard.html          <- full device list
    |-- ptc.html                <- PTZ tab (embeds dashboard_PTZ.html)
    |-- dashboard_PTZ.html      <- 9-room PTZ camera grid
    |-- avoip.html              <- AVoIP room layouts + temp badges
    |-- creds.html              <- Password vault page
    |-- config.json             <- monitor settings
    |-- devices.json            <- device inventory (287 devices)
    |-- creds.json.example      <- password file template
    `-- logs\                   <- created at runtime
```

## 2. Prerequisites

- Windows 10/11 (any edition), 64-bit. No extra software required -
  all three background services are self-contained EXEs.
- The monitoring PC must be able to reach the AV network:
  - `172.18.2.0/23` (VLAN-1802, Control + Dante)
  - `172.18.22.0/24` (VLAN-1822, AVoIP)
- You must have the real `creds.json` (containing the device passwords)
  available from the build machine. It is intentionally NOT shipped in
  the zip for security.

## 3. Installation (one time, ~2 minutes)

1. **Copy the folder** - unzip the package to any location on the
   target PC, e.g. `C:\ShekMun-Monitor`.

2. **Install the real password file** - copy `creds.json` from the
   build machine into `C:\ShekMun-Monitor\monitoring\`.
   (Without it, the Passwords page shows an error, but monitoring still
   works.)

3. **Run setup-once.bat as Administrator** - right-click
   `setup-once.bat` -> "Run as administrator". It:
   - grants the port-8080 URL reservation to your user
     (`netsh http add urlacl`)
   - opens the firewall for TCP 8080
   - creates a "Shek Mun Monitor Control" shortcut on the desktop

4. **Verify network reachability** (optional but recommended):
   `ping 172.18.22.5` (KDS manager) and `ping 172.18.2.51` (AVProc-Pi5).

## 4. First run

1. Double-click `Start Monitor Control.bat` (or the new desktop
   shortcut). The controller window opens and auto-starts all three
   services:
   - **device monitor** - pings all 287 devices continuously
   - **temp monitor** - queries 44 Kramer KDS units (incl. AVoIP
     manager and Audio-DEC decoders) every ~10s
   - **dashboard server** - serves the web pages on port 8080

2. Your browser opens `http://localhost:8080/dashboard_shekmun.html`.

3. The Main page shows: total devices (276 shown / 287 monitored, 11
   TV-Res excluded), ok/fail counts, OK rate, average/max KDS
   temperature, per-room status, hot units and latest failures.
   It refreshes every 10 seconds.

4. Closing the controller window stops all three background services.
   Re-open it anytime to restart everything.

## 5. The web pages

| Tab | URL | What it shows |
|-----|-----|---------------|
| Main | `dashboard_shekmun.html` | overview cards, per-room status, hot KDS units, latest failures |
| Dashboard | `dashboard.html` | full device table with group filter / sort, per-device temp badges |
| PTZ | `ptc.html` | 9-room camera grid (mediabox snapshots + Cam/Control popups) |
| AVoIP | `avoip.html` | per-room AVoIP input/output layouts with live temp badges |
| Passwords | `creds.html` | device passwords (copy / show-hide) |

### Password behaviour
- **Localhost** (`http://localhost:8080`): PTZ, AVoIP and Passwords
  pages are open with no password.
- **Remote / LAN** (`http://<ip>:8080`): PTZ and AVoIP ask for the
  password `rcteacher1` (remembered per browser tab). The **Passwords
  tab is hidden** on remote access, and `creds.html` itself always
  requires `rcteacher`. Lock symbols appear on the PTZ/AVoIP tabs.

### Temperature badges
- Green below 45 °C, red at/above 45 °C.
- Units: KDS encoders (EN-*), decoders (TV-DEC-*), Audio-DEC, and the
  AVoIP manager. Temperatures update every ~10s.

## 6. LAN access from other PCs

1. On the monitoring PC find its LAN IP, e.g. `ipconfig` ->
   `10.107.147.64`.
2. On any other PC on the same network open:
   `http://10.107.147.64:8080/`
3. The PTZ / AVoIP pages will prompt for the password (`rcteacher1`);
   the Passwords tab is not shown remotely.
4. If unreachable, re-run `setup-once.bat` (firewall/URL ACL) and
   confirm the dashboard server is running in the controller window.

## 7. Data & logs

All runtime data lives under `monitoring\logs\`:

- `status-YYYYMMDD.csv` - per-device ping results, one row per pass
- `report-*.txt` - end-of-day summaries
- `temp-YYYYMMDD.csv` - temperature readings
- `monitor-error.log` / `temp-monitor-error.log` - errors (if any)

Live JSON for the pages:
- `monitoring\snapshot.json` - device status + merged KDS temps
- `monitoring\temp-snapshot.json` - raw temperature readings

## 8. Upgrading an existing install

1. Take a backup of the old folder (especially `monitoring\creds.json`
   and any `logs\` you want to keep).
2. Stop the controller (close its window) to stop all services.
3. Replace the whole package folder with the new one.
4. Copy `creds.json` into the new `monitoring\`.
5. Re-run `setup-once.bat` as admin (port/firewall rules are idempotent).
6. Start via `Start Monitor Control.bat`.

## 9. Troubleshooting

- **Controller shows ERROR** - check
  `monitoring\logs\monitor-error.log` and `temp-monitor-error.log`.
- **Port 8080 in use** - change the port in the controller's Port box,
  then re-run `setup-once.bat` for that port.
- **Dashboard unreachable from LAN** - firewall/URL ACL: re-run
  `setup-once.bat`.
- **Temperatures show "--"** - temp-monitor may not be running (start
  it in the controller) or the unit is offline.
- **AVoIP thumbnails flicker between image/error** - the Kramer manager
  rate-limits snapshot requests; the page self-heals within seconds,
  no action needed.

## 10. Version history

See `CHANGELOG.md` in the repository for the full history. Current
release: **v1.8.3** - includes password gates (PTZ/AVoIP/Passwords),
lock symbols on remote tabs, TV-Res exclusion, Audio-DEC temperature
monitoring, and the self-healing AVoIP view.