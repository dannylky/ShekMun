# Automation d4e5596a — Shek Mun AV audit, 19:15 slot

Runs the audit via `av_report.py` and emails the report to dannylam@hsu.edu.hk.
Full procedure lives in the `shekmun-av-audit` skill — load it first, do not improvise.

## Execution log

### 2026-09-22 19:16 (first run of this automation)
- Pipeline ok, exit 0, 56.8 s. No `cleanup=` line.
- Verdict: **Ok**. Subject: `HSUHK@Shek Mun Audit report- 2026-09-22 19:16 / Status: Ok`
- Attachments uploaded (`AV_room_audit.html`, `all_rooms_20260922_1916.jpg`) and sent;
  mail queued, quota remaining 37/50.
- Highest KDS 45 °C (SM-11-07 TV-DEC-1), under the 49 °C alarm and 46 °C warn band.
- Only SM-11-07 had notes: display idle (Windows lock, clock `7:15`) + sync NOT VERIFIED
  (1 of 2 display regions isolated). Neither is an Abnormal trigger.
- All 8 cameras online; Common Area offline (HTTP 502) as expected — scheduled down.
- Several decoders reported `unknown` (SM-11-02 #1, 03, 05, 08 both) — poller lag,
  correctly not treated as faults by v1.5.0.

### 2026-09-23 19:16
- Pipeline ok, exit 0, 60.6 s, no `RESULT skip=`. Body 10,037 B (limit 13,000) — sent fine.
- Verdict: **Ok**. Subject `HSUHK@Shek Mun Audit report- 2026-09-23 19:16 / Status: Ok`.
- Highest KDS 43 °C (SM-11-08 TV-DEC-1). All 8 cameras online; Common Area offline (502),
  scheduled down. No `unknown` storms this run.
- Idle: SM-11-02, SM-11-07 (Windows lock screen). In use: 03/04/05/06/08.
  SM-11-01 UNCONFIRMED (lum 23, content unreadable). Sync NOT VERIFIED in 01/02/07;
  08 IN SYNC. Nothing Abnormal.
- Mail queued, quota remaining 32/50.

### 2026-09-24 19:16
- Pipeline ok, exit 0, 59.1 s, no `RESULT skip=`. Body 9,896 B (limit 13,000) — sent fine.
- Verdict: **Abnormal (SM-11-01)** — first Abnormal raised by this automation.
  Subject `HSUHK@Shek Mun Audit report- 2026-09-24 19:16 / Status: Abnormal (SM-11-01)`.
- Cause: sync `out-of-sync`, confirmed on two consecutive runs (within 3 h), so not the
  1ST-RUN downgrade. 3 evidenced regions in a 4-decoder room: #1 AVoIP decoder standby
  (idle, OCR text read) vs #2/#3 active content — standby-vs-content hard mismatch,
  area ratio 1.0, ≥1 high reading. All 4 decoders online, so no reachability factor.
- Notable: room-level `display_state` reads Idle while 2 of 3 screens say Active — the
  phantom/OCR path, expected per skill. SM-11-01 lum 43 / dark 79% (OFF-PARTIAL lighting,
  informational only, never an Abnormal trigger).
- SM-11-07 UNCONFIRMED (no display detected / 0 regions isolated → sync NOT VERIFIED).
- Idle: SM-11-01 (AVoIP standby). In use: 02/03/04/05/06/08. SM-11-02 IN SYNC, 08 IN SYNC.
- Highest KDS 44 °C (SM-11-02 TV-DEC-1) — under the 46 °C warn / 49 °C alarm band.
- All 8 cameras online; Common Area offline (HTTP 502), scheduled down as expected.
- Mail queued, quota remaining 38/50.

### 2026-09-25 19:16
- Pipeline ok, exit 0, 57.5 s, no `RESULT skip=`. Body 9,734 B (+700 reserve, limit 13,000)
  — sent fine, no manual trimming needed. `cleanup=removed 2 file(s)`.
- Verdict: **Ok**. Subject `HSUHK@Shek Mun Audit report- 2026-09-25 19:16 / Status: Ok`.
- Highest KDS 45 °C (SM-11-01 TV-DEC-2) — under the 46 °C warn / 49 °C alarm band.
  Second highest 44 °C (SM-11-08).
- Idle: SM-11-07 only (Windows lock screen). In use: 01/02/03/04/05/06/08.
- Sync: 01/02/08 IN SYNC; 07 NOT VERIFIED (only 1 of 2 regions isolated); 03–06 N/A
  (single-display rooms). No out-of-sync anywhere → nothing Abnormal.
- Note: SM-11-01 has 4 decoders but only 2 evidenced display regions — both `active`,
  so IN SYNC stands. Room 06 room-level `display_state` = Active while motion is 0.00 %
  (static content = in use, by design).
- All 8 cameras online; Common Area offline (HTTP 502), scheduled down as expected.
- Mail queued, quota remaining 38/50.

### 2026-09-29 19:16
- Pipeline ok, exit 0, 66.3 s, no `RESULT skip=`. Body 9,655 B (limit 13,000) — sent first try.
- Verdict: **Ok**. Subject `HSUHK@Shek Mun Audit report- 2026-09-29 19:16 / Status: Ok`.
- Highest KDS 45 °C (SM-11-08 TV-DEC-2 and SM-11-02 TV-DEC-2 tied); then 44 °C (SM-11-01),
  43 °C (SM-11-07). All under the 46 °C warn / 49 °C alarm band.
- Idle: SM-11-06 only (AVoIP standby). In use: 01/02/03/04/05/07/08 — busiest run of the day.
- Sync: all multi-display rooms clean — 01 IN SYNC (4/4 regions isolated), 02/07/08 IN SYNC.
  No CHECK REGION, no 1ST RUN, nothing to watch next slot.
- All 8 cameras online, every decoder online (ok=dec in all rooms). Common Area offline
  (HTTP 502), scheduled down as expected.
- Mail queued, quota remaining 42/50.

## Notes for next run
- Subject timestamp comes from the run, not the slot (19:15 slot → 19:16 subject). Normal.
- Always read `.workbuddy/tmp/mail_body.html` and pass it verbatim; never a placeholder.
