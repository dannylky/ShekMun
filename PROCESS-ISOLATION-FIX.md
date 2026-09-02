# Process Isolation Fix — MPlus & Shek Mun monitor apps

Date: 2026-09-02 · Applies to: `monitoring\monitor-control.ps1` in BOTH
`C:\Work\Projects\MPlus` and `C:\Work\Projects\ShekMun` (identical change).

---

## 1. Problem

MPlus and Shek Mun are two similar desktop monitor apps. Each is a
controller window that starts/stops three background services:

- `monitor.exe` (device ping monitor)
- `temp-monitor.exe` (Kramer KDS temperatures)
- `serve-dashboard.exe` (web dashboard server; MPlus uses port 8081,
  Shek Mun uses port 8080)

**Observed failure:** when both apps run at the same time, the FIRST
app's monitoring stops — the SECOND app owns the process. I.e. starting
the second controller kills the first controller's background processes
(and on window close each controller would kill the other's processes
too).

## 2. Root cause

The controller detected its background processes **by process name
only**, with no check that the process actually belongs to its own
application folder:

```powershell
# OLD - name-only matching (matches ANY monitor.exe on the machine)
function Get-MonitorProcess {
    Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'monitor.exe'" |
        Where-Object { ($_.CommandLine -like '*monitor.ps1*' -or $_.Name -eq 'monitor.exe') ... } |
        Sort-Object CreationDate -Descending | Select-Object -First 1
}
```

Because both apps use the SAME generic executable names
(`monitor.exe`, `serve-dashboard.exe`, `temp-monitor.exe`), the second
app's controller:

1. saw the first app's `monitor.exe` as "the monitor process" and
   reported it as its own ("already running"), and
2. on start/stop/close, killed the matched process — i.e. the other
   app's process. Hence "the first monitoring stops, the 2nd owns the
   process".

The same applied to `Stop-Monitoring` / `Stop-TempMonitor` /
`Stop-Dashboard`, which kill whatever `Get-*Process` returned.

## 3. The fix

Every process lookup is now scoped to **this application's own folder**
(`$root`, the directory containing the app). A helper decides whether a
process belongs to us:

```powershell
# NEW - a process is ours only if its executable or command line
# references THIS app's folder ($root)
function Test-IsOurs {
    param($Proc)
    if (-not $Proc) { return $false }
    if ($Proc.ExecutablePath) {
        return $Proc.ExecutablePath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)
    }
    return $Proc.CommandLine -like "*$root*"
}
```

- **Our EXEs** (`monitor.exe` etc.) run from `$root` → `ExecutablePath`
  starts with `$root` → ours.
- **Script runs** (`powershell -File ...\monitor.ps1`, `python
  ...\temp-monitor.py`) expose the script path in `CommandLine` → ours.
- **The other app's processes** (or any other program with the same
  generic names) live in a different folder → NOT ours.

Changes in `monitor-control.ps1`:

| Function | Change |
|---|---|
| `Get-MonitorProcess` | added `-and (Test-IsOurs $_)` to the filter |
| `Get-ServerProcess` | added `-and (Test-IsOurs $_)` to the filter |
| `Get-TempProcess` | added `-and (Test-IsOurs $_)` to the filter |
| `Stop-Monitoring` | refuses to kill if `Test-IsOurs` fails |
| `Stop-TempMonitor` | refuses to kill if `Test-IsOurs` fails |
| `Stop-Dashboard` | refuses to kill if `Test-IsOurs` fails |
| new `Test-IsOurs` helper | added after `Get-LaunchTarget` |

Ports were already distinct (MPlus 8081 / Shek Mun 8080), so no port
changes were needed.

## 4. Result

- Each app only ever detects, claims, starts and stops **its own**
  processes.
- Starting the second app no longer stops the first app's monitoring.
- Closing a controller window only stops its own `monitor.exe`,
  `temp-monitor.exe` and `serve-dashboard.exe`.
- Both apps can run simultaneously, each monitoring its own network and
  serving its own dashboard on its own port.

## 5. Verification procedure

1. Start the Shek Mun controller
   (`C:\Work\Projects\ShekMun\monitoring\monitor-control.exe`): its
   monitor, temp monitor and dashboard (port 8080) come up.
2. Start the MPlus controller
   (`C:\Work\Projects\Mplus\monitoring\monitor-control.exe`): its
   monitor, temp monitor and dashboard (port 8081) come up as well.
3. Confirm BOTH `monitor.exe` processes are running (one per folder)
   and both ports answer (`http://localhost:8080` and
   `http://localhost:8081`).
4. Gracefully close the MPlus controller → MPlus services stop, the
   Shek Mun services keep running.
5. Restart MPlus, then gracefully close the Shek Mun controller →
   Shek Mun services stop, MPlus services keep running.
6. The Start/Stop buttons in each controller affect only its own
   processes.

## 6. Version

- MPlus `monitor-control.ps1`: `$script:version` 1.0.0 → 1.1.0
- Shek Mun `monitor-control.ps1`: `$script:version` 1.7.0 → 1.8.0
- `monitor-control.exe` rebuilt in both projects.
- MPlus `build-deploy.ps1` package version corrected 1.0.4 → 1.0.5
  (was stale vs CHANGELOG).