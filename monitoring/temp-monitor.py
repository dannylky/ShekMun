#!/usr/bin/env python3
"""
temp-monitor.py - monitors system temperature of Kramer KDS-SW3-EN7 and
KDS-DEC7 units via Kramer Protocol 3000.

Queries every unit with "#HW-TEMP? 0,0\r" over TCP port 5000 and parses
the "~01@HW-TEMP 0,0,<temp>" response.

Devices are auto-selected from devices.json by name pattern:
  - EN-*         -> KDS-SW3-EN7 encoders (e.g. EN-PC-AVoIP)
  - TV-DEC-*     -> KDS-DEC7 decoders    (e.g. TV-DEC-1)
  - AVoIP-Manager -> KDS AVoIP manager   (172.18.22.5)
Only units on the AVoIP subnet (172.18.22.x) are included, so Dante
endpoints named EN-* are skipped. Adjust DEVICE_FILTER if needed.

Results are appended to logs\\temp-YYYYMMDD.csv. The latest readings are
kept in temp-snapshot.json (gitignored, for the dashboard). Press
Ctrl+C to stop.

Usage:
  python temp-monitor.py                # continuous loop, 10s interval
  python temp-monitor.py --interval 30  # custom interval (seconds)
  python temp-monitor.py --one-shot     # single pass, then exit
  python temp-monitor.py --timeout 8    # per-query socket timeout (s)
"""

import argparse
import concurrent.futures
import json
import os
import re
import socket
import sys
import time
from datetime import datetime

if getattr(sys, "frozen", False):
    # running as a PyInstaller onefile EXE - use the EXE's own directory
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICES_JSON = os.path.join(SCRIPT_DIR, "devices.json")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
SNAPSHOT_JSON = os.path.join(SCRIPT_DIR, "temp-snapshot.json")
ERROR_LOG = os.path.join(LOG_DIR, "temp-monitor-error.log")
PORT = 5000
COMMAND = b"#HW-TEMP? 0,0\r"
RESPONSE_RE = re.compile(r"@HW-TEMP\s*\d+,(\d+)C?")


def err_log(message):
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}  {message}\n")
    except Exception:
        pass

DEVICE_FILTER = {
    "name_re": r"^(EN|TV-DEC)-|^AVoIP-Manager$",
    "subnet": "172.18.22.",  # AVoIP VLAN only
}


def load_devices():
    with open(DEVICES_JSON, "r", encoding="utf-8-sig") as f:
        inv = json.load(f)
    devices = []
    for room_name, room_devices in inv.get("rooms", {}).items():
        for d in room_devices:
            devices.append((room_name, d))
    for d in inv.get("unique", []):
        devices.append(("UNIQUE", d))
    return devices


def select_devices():
    pattern = re.compile(DEVICE_FILTER["name_re"])
    return [
        (room, d)
        for room, d in load_devices()
        if pattern.match(d.get("name", ""))
        and d.get("ip", "").startswith(DEVICE_FILTER["subnet"])
    ]


def query_temperature(ip, port=PORT, timeout=5.0):
    """Returns (temp_c, rtt_ms) or (None, rtt_ms) on failure."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            t0 = time.perf_counter()
            s.connect((ip, port))
            s.sendall(COMMAND)
            data = b""
            while b"\r" not in data:
                chunk = s.recv(1024)
                if not chunk:
                    break
                data += chunk
            rtt_ms = round((time.perf_counter() - t0) * 1000, 1)
            text = data.decode("ascii", errors="replace").strip()
            m = RESPONSE_RE.search(text)
            if m:
                return int(m.group(1)), rtt_ms
            return None, rtt_ms
    except socket.timeout:
        return None, None
    except (ConnectionRefusedError, OSError):
        return None, None
    except Exception:
        return None, None


def log_line(csv_path, room, name, ip, temp, rtt, status):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    temp_s = temp if temp is not None else ""
    rtt_s = rtt if rtt is not None else ""
    line = f"{ts},{room},{name},{ip},{status},{temp_s},{rtt_s}\n"
    for attempt in range(3):
        try:
            with open(csv_path, "a", encoding="utf-8") as f:
                f.write(line)
            return
        except Exception as e:
            if attempt < 2:
                time.sleep(0.25)
            else:
                err_log(f"log write failed: {csv_path} ({e})")


def save_snapshot(entries):
    snap = {
        "version": 1,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "updatedAt": datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "units": entries,
    }
    tmp = SNAPSHOT_JSON + ".tmp"
    for attempt in range(5):
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(snap, f)
            # os.replace fails on Windows if another process holds the
            # destination open (the controller reads it every 1.5 s)
            os.replace(tmp, SNAPSHOT_JSON)
            return
        except Exception as e:
            if attempt < 4:
                time.sleep(0.5)
            else:
                err_log(f"snapshot write failed: {e}")


def run_pass(selected, csv_path, timeout):
    entries = []
    now = datetime.now().strftime("%H:%M:%S")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
            futures = {
                ex.submit(query_temperature, d["ip"], PORT, timeout): (room, d)
                for room, d in selected
            }
            for fut in concurrent.futures.as_completed(futures):
                room, d = futures[fut]
                try:
                    temp, rtt = fut.result()
                except Exception as e:
                    err_log(f"query task failed for {room}/{d['name']}: {e}")
                    temp, rtt = None, None
                status = "OK" if temp is not None else "FAIL"
                log_line(csv_path, room, d["name"], d["ip"], temp, rtt, status)
                entries.append({
                    "room": room,
                    "name": d["name"],
                    "ip": d["ip"],
                    "tempC": temp,
                    "status": status.lower(),
                    "checkedAt": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                })
    except Exception as e:
        err_log(f"pass failed: {e}")
    save_snapshot(entries)
    oks = sum(1 for e in entries if e["status"] == "ok")
    print(
        f"[{now}] temp pass: {oks}/{len(entries)} units OK "
        f"({_describe_temps(entries)})",
        flush=True,
    )


def _describe_temps(entries):
    vals = [e["tempC"] for e in entries if e["tempC"] is not None]
    if not vals:
        return "no readings"
    return f"min {min(vals)}C max {max(vals)}C avg {round(sum(vals) / len(vals), 1)}C"


def main():
    ap = argparse.ArgumentParser(description="Kramer KDS unit temperature monitor")
    ap.add_argument("--interval", type=float, default=10.0, help="loop interval in seconds (default 10)")
    ap.add_argument("--timeout", type=float, default=5.0, help="per-query socket timeout (default 5)")
    ap.add_argument("--one-shot", action="store_true", help="run a single pass and exit")
    args = ap.parse_args()

    os.makedirs(LOG_DIR, exist_ok=True)
    csv_path = os.path.join(LOG_DIR, "temp-" + datetime.now().strftime("%Y%m%d") + ".csv")
    if not os.path.exists(csv_path):
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("timestamp,room,device,ip,result,tempC,rttMs\n")

    selected = select_devices()
    if not selected:
        print("No matching devices found in devices.json (check DEVICE_FILTER).")
        sys.exit(1)
    print(
        f"Temp monitor: {len(selected)} units "
        f"({sum(1 for _, d in selected if d['name'].startswith('EN-'))} EN encoders, "
        f"{sum(1 for _, d in selected if d['name'].startswith('TV-DEC-'))} TV-DEC decoders, "
        f"{sum(1 for _, d in selected if not d['name'].startswith(('EN-', 'TV-DEC-')))} other)"
    )
    print(f"Log: {csv_path}")

    try:
        while True:
            run_pass(selected, csv_path, args.timeout)
            if args.one_shot:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Temp monitor stopped by user.", flush=True)
    except Exception as e:
        err_log(f"monitor crashed: {e}")
        print(f"Temp monitor crashed: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
