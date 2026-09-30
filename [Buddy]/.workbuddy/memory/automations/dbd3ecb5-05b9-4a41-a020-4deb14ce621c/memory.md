# Automation memory — Shek Mun AV audit, fixed 13:15 slot

## 2026-09-22 13:15 (first recorded run)
- Pipeline ran clean (60.8 s, exit 0). Verdict **Ok**.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260922_1316.jpg
  (subject verbatim from `RESULT subject=`). Daily quota: 43/50 left.
- Only noteworthy item: SM-11-07 sync = NOT VERIFIED (just 1 display region isolated);
  not a fault. Common Area offline but on `scheduled_down`, excluded from verdict.
- No time guard needed — this automation only fires at 13:15.

## 2026-09-23 13:15
- Pipeline ran clean (57.8 s, exit 0), no throttle skip. Verdict **Ok**.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260923_1316.jpg.
  Quota after send: 39/50.
- No Abnormal triggers: max KDS 45 °C (SM-11-02 TV-DEC-2), no device fail, no sync
  mismatch. SM-11-02 sync = NOT VERIFIED (only 1 region isolated) — not a fault.
  Common Area offline but on `scheduled_down`, excluded.

## 2026-09-24 13:15
- Pipeline clean (63.9 s, exit 0), no throttle skip. Verdict **Ok**.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260924_1316.jpg.
  Quota after send: 44/50. Engine now v2.1.0 (wall-only display_filter live).
- No Abnormal triggers. Max KDS 44 °C (SM-11-01 TV-DEC-2). SM-11-02 idle (AVoIP standby),
  SM-11-04 idle (AVoIP standby), rest in use. Sync: 01/07 IN SYNC, 02/08 NOT VERIFIED
  (only 1–2 regions isolated). Common Area offline but scheduled_down → excluded.

## 2026-09-25 13:15
- Pipeline clean (58.1 s, exit 0), no throttle skip. Verdict **Ok**.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260925_1316.jpg.
  Quota after send: 44/50. Body 9,677 B (well under the 13,000 limit).
- No Abnormal triggers. Max KDS 46 °C (SM-11-07 TV-DEC-1) — inside the 46 warn band but
  below the 49 alarm. Idle: SM-11-03 / 05 (AVoIP standby). SM-11-08 UNCONFIRMED with sync
  NOT VERIFIED (0 wall regions isolated this run — wall filter dropped them all); not a fault.
  Common Area offline but scheduled_down → excluded.

## 2026-09-28 13:19
- Pipeline clean (68.4 s, exit 0), no throttle skip. Verdict **Ok**.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260928_1319.jpg.
  Quota after send: 45/50. Body 9,630 B (well under 13,000 limit).
- No Abnormal triggers. Max KDS 45 °C (SM-11-01 TV-DEC-2). Only SM-11-03 idle
  (AVoIP standby). All 4 multi-display rooms IN SYNC this run — first time all four
  (01/02/07/08) resolved; wall-only filter isolated 2 regions everywhere.
  Common Area offline but scheduled_down → excluded.

## 2026-09-29 13:15
- Pipeline clean (68.1 s, exit 0), no throttle skip. Verdict **Ok**.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260929_1316.jpg.
  Quota after send: 46/50. Body 9,696 B (under the 13,000 limit). Sent first try, no retry.
- No Abnormal triggers. Max KDS 42 °C (SM-11-01 TV-DEC-2) — well below the 49 alarm.
  Idle (AVoIP standby): 01 / 02 / 06 / 07 / 08. In use: 03 / 04 / 05.
  All four multi-display rooms (01/02/07/08) IN SYNC again.
  Common Area offline but scheduled_down → excluded.

## 2026-09-30 13:15
- Pipeline clean (77.0 s, exit 0), no throttle skip. Verdict **Ok**.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260930_1316.jpg.
  Quota after send: 46/50. Body 10,131 B (under the 13,000 limit). Sent first try, no retry.
- No Abnormal triggers. Max KDS 44 °C (SM-11-02 TV-DEC-2, and SM-11-01 TV-DEC-2) — below
  both the 46 warn band and the 49 alarm.
  Idle: 02 / 06 (Windows lock screen), 03 / 07 (AVoIP standby). In use: 01 / 04 / 05 / 08.
  All four multi-display rooms (01/02/07/08) IN SYNC — Room 1 resolved all 4 regions.
  Common Area offline but scheduled_down → excluded.

### Reusable notes for future runs
- Workflow that works: read `av_summary.json` for per-room display verdicts + KDS temps,
  read `.workbuddy/tmp/mail_body.html` and pass it verbatim as the body (never a placeholder).
- Upload both attachments with `agent_mail_upload_attachment` first, then send with
  `file_refs` + `skip_confirmation: true`.
- Check `av_monitor_config.json → scheduled_down` before calling an offline room a fault.
