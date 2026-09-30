# Automation: Shek Mun AV audit — fixed 07:15 slot

## 2026-09-23 08:17 (first recorded run)
- Pipeline ran clean in 58 s. Status **Ok**, no anomalies raised.
- Email sent to dannylam@hsu.edu.hk with `AV_room_audit.html` + `all_rooms_20260923_0817.jpg`.
- Quota remaining after send: 47/50.
- Notes for next time:
  - Common Area (172.18.22.109) offline / HTTP 502 — scheduled down, expected, never a fault.
  - SM-11-02 picture sync NOT VERIFIED (only 1 display region isolated) — informational only.
  - Max KDS 42 °C (SM-11-08 TV-DEC-2), well under the 49 °C alarm.

## 2026-09-24 08:18
- Throttle hit: `RESULT skip=last run was 4 min ago` — catch-up replay absorbed, nothing sent.
- No upload, no email (per guard rule).

- Flow that worked: skill → `av_report.py` → upload 2 attachments → read
  `.workbuddy/tmp/mail_body.html` verbatim → SendMessage (body_format HTML, skip_confirmation true).

## 2026-09-25 08:31
- Throttle hit again: `RESULT skip=last run was 4 min ago` (a run had completed at ~08:27).
- No upload, no email (per guard rule). Nothing to fix — throttle working as designed.

## 2026-09-28 08:14
- Throttle hit: `RESULT skip=last run was 4 min ago` — a run had already completed at ~08:09
  (all_rooms_20260928_0809.jpg in the workspace confirms it).
- No upload, no email (per guard rule). Third consecutive catch-up absorbed; throttle healthy.

## 2026-09-30 08:17
- Throttle hit: `RESULT skip=last run was 4 min ago` — the 08:12 run had already completed
  (all_rooms_20260930_0812.jpg present in workspace).
- No upload, no email (per guard rule). Throttle healthy; no action needed.
