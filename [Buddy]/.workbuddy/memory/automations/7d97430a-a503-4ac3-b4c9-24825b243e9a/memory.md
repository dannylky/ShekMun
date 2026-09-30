# Shek Mun AV audit — run history

## 2026-09-21 11:58 HKT (first recorded run)
- Time guard: 11:57 local, inside 07:15–22:15 window → ran.
- Pipeline `av_report.py` completed in 59.3 s (scan 58.5 / sheet 0.4 / mail 0.4).
- Result: **Status Ok**, no Abnormal rooms.
- Highest KDS: 44 °C (SM-11-01 TV-DEC-1) — within 1 °C of the 45 °C threshold, informational only.
- Common Area excluded (scheduled down, camera HTTP 502) — expected.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1158.jpg.
  Agent Mail daily quota: 45 of 50 remaining after this send.

## 2026-09-21 13:01 HKT
- Time guard: 13:01 local, inside window → ran. Pipeline 61.3 s.
- Result: **Status Abnormal (SM-11-01, SM-11-08)** — SM-11-01 KDS 45 °C (TV-DEC-2); SM-11-08 KDS 46 °C + displays out-of-sync.
- Highest KDS of the run: 46 °C (SM-11-08 TV-DEC-2 / 172.18.22.58).
- SM-11-07 mixed standby banners — note only, not abnormal. Common Area excluded (scheduled down, 502).
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1302.jpg.
  Agent Mail daily quota: 44 of 50 remaining after this send.

## 2026-09-21 14:08 HKT
- Time guard: 14:06 local, inside window → ran. Pipeline 57.7 s.
- Result: **Status Abnormal (SM-11-01)** — displays out of sync; all KDS below the 49 °C alarm.
- Highest KDS: 45 °C (SM-11-01 TV-DEC-2 and SM-11-08 TV-DEC-2, tied).
- SM-11-02 mixed standby banners, note only. Common Area excluded (scheduled down, 502).
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1408.jpg.
  Agent Mail daily quota: 43 of 50 remaining after this send.

## 2026-09-21 15:14 HKT
- Time guard: 15:13 local, inside window → ran. Pipeline 59.2 s.
- Result: **Status Ok** — no Abnormal rooms. SM-11-08 sync "not verified" (only 1 region isolated), note only.
- Display states: 01/02/03/04/05 in use; 06/07/08 idle. Common Area excluded (scheduled down, 502).
- Highest KDS: 45 °C (SM-11-08 TV-DEC-2 / 172.18.22.58) — below the 49 °C alarm, warn band only.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1514.jpg.
  Agent Mail daily quota: 42 of 50 remaining after this send.

## 2026-09-21 16:19 HKT
- Time guard: 16:18 local, inside window → ran. Pipeline 58.9 s.
- Result: **Status Ok** — no Abnormal rooms. SM-11-02 sync "not verified" (only 2 regions isolated), note only.
- Display states: 01/02/04/05/07 in use; 03/06/08 idle. Common Area excluded (scheduled down, 502).
- Highest KDS: 45 °C (SM-11-01 TV-DEC-2 / 172.18.22.51) — below the 49 °C alarm, warn band only.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1619.jpg.
  Agent Mail daily quota: 41 of 50 remaining after this send.

## 2026-09-21 17:24 HKT
- Time guard: 17:22 local, inside window → ran. Pipeline 61.2 s.
- Result: **Status Abnormal (SM-11-02)** — displays out of sync (one region idle, other
  "Active – Windows operational image"). All KDS below the 49 °C alarm.
- Display states: 03/04/05 in use; 01/02/06/07/08 idle. SM-11-08 sync "not verified"
  (1 region isolated), note only. Common Area excluded (scheduled down, 502).
- Highest KDS: 45 °C (SM-11-02 TV-DEC-2 / 172.18.22.52) — below the 49 °C alarm, warn band only.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1724.jpg.
  Agent Mail daily quota: 40 of 50 remaining after this send.
- Note: SM-11-02 out-of-sync is a repeat-offender room (also flagged 14:08 and 16:19 as
  "not verified"). Likely the known transient sensitivity — worth watching, but not yet
  raised with Danny.

## 2026-09-21 18:29 HKT
- Time guard: 18:28 local, inside window → ran. Pipeline 58.8 s (grab 48.3 / analyse 8.8).
- Result: **Status Ok** — no Abnormal rooms. All decoders online; all KDS well below 49 °C.
- Display states: SM-11-06 and SM-11-07 **in use** (07 showing AMS6101 Quantitative Methods
  in Risk Management / Lecture 2 Summary); 02/03/04/05/08 idle; SM-11-01 **unconfirmed**
  (lights off — lum 24, dark 99 %, motion 0.00 %, 0 regions isolated → sync not verified).
- Sync: 02 and 07 IN SYNC; 01 and 08 not verified (too few regions isolated), note only.
- Highest KDS: 44 °C (SM-11-02 TV-DEC-2 / 172.18.22.52) — warn band only, no alarm.
- Common Area excluded (scheduled down, camera HTTP 502) — expected.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1829.jpg.
  Agent Mail daily quota: 39 of 50 remaining after this send.
- Note for trend: SM-11-02 back to IN SYNC this run after the 17:24 out-of-sync flag —
  consistent with the known transient sensitivity, not a persistent fault.

## 2026-09-21 19:33 HKT
- Time guard: 19:32 local (+0800), inside window → ran. Pipeline 58.8 s (grab 48.6 / analyse 7.3).
- Result: **Status Abnormal (SM-11-07)** — displays out of sync (one region Windows desktop
  idle, others showing live Binomial Distribution content). All KDS below the 49 °C alarm.
- Display states: 03/04/05/06 in use; 02/07/08 idle; SM-11-01 **unconfirmed** (lights off —
  lum 23, dark 99 %, motion 0.00 %, 0 regions isolated → sync not verified).
- Sync: 02 and 08 IN SYNC; 01 not verified (0 regions), note only; 07 OUT OF SYNC → Abnormal.
- Highest KDS: 45 °C (SM-11-02 TV-DEC-2 / 172.18.22.52) — warn band only, no alarm.
- Common Area excluded (scheduled down, camera HTTP 502) — expected.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260921_1933.jpg.
  Agent Mail daily quota: 38 of 50 remaining after this send.
- Note: first time SM-11-07 is the flagged room (previously 01/02/08). Consistent with the
  known transient sensitivity of the sync check rather than a new persistent fault — watch
  whether it repeats on the 20:xx run before raising it.

## 2026-09-22 08:02 HKT
- Time guard: 08:01 local (+0800), inside window → ran. Pipeline 71.1 s (grab 48.6 / analyse 10.2).
- Result: **Status Abnormal (SM-11-02…SM-11-08, 7 rooms)** — but almost certainly a **monitoring
  poller restart artifact**, not real faults. Evidence: `snapshot_live.json` `generatedAt` =
  08:01:24, `updatedAt` = 08:01:48 (only ~24 s of polling), and 232 devices have
  `checkedAt = ""` + `rttMs -1` → `status: unknown`. Only the devices already polled (SM-11-01
  in full) came back ok. Cameras were all online and frames grabbed fine; all KDS ≤ 43 °C.
- Display states: 01/02/03/04/05/06 idle; 07/08 in use. Common Area excluded (scheduled down, 502).
- Highest KDS: 43 °C (SM-11-01 TV-DEC-2 / 172.18.22.51) — well below the 49 °C alarm.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260922_0802.jpg.
  Agent Mail daily quota: 49 of 50 remaining (quota had reset).
- Action: if a future run flags many rooms at once, check `generatedAt`/`updatedAt` in
  `.workbuddy/tmp/snapshot_live.json` before believing it — a fresh poller ⇒ mass "unknown".

## 2026-09-22 09:22 HKT
- Time guard: 09:21 local (+0800), inside window → ran. Pipeline 60.5 s (grab 48.3 / analyse 6.2).
- Result: **Status Ok** — no Abnormal rooms. All 8 rooms' cameras online, all decoders `ok`.
- Poller healthy this run (no restart artifact): `generatedAt` 08:01:24 vs `updatedAt` 09:21:51
  = ~80 min polling window, so the 08:02 mass-unknown issue has cleared.
- Display states: 04/05/08 **in use** (04 OCR: "CORPORATECOMMUNICATION"); 01/06/07 idle
  (Windows lock screen), 02/03 idle (AVoIP decoder standby). Common Area excluded (scheduled
  down, camera HTTP 502).
- Sync: 01 and 08 IN SYNC; 02 and 07 NOT VERIFIED (only 1 region isolated each) — note only.
  No out-of-sync flags at all, so the 09-21 transient-sensitivity streak (01/02/07/08) is quiet.
- Highest KDS: 44 °C (SM-11-01 TV-DEC-2 / 172.18.22.51) — warn band, well below the 49 °C alarm.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260922_0922.jpg.
  Agent Mail daily quota: 47 of 50 remaining after this send.
- Note: quota dropped by 2 vs the 08:02 run (49 → 47), suggesting one other run/send happened
  in between that is not in this log. Worth a glance if it recurs.

## 2026-09-23 09:25 HKT
- Throttle: last completed run ~08:36 (48 min earlier) → cleared the 45 min guard, ran normally.
  No `RESULT skip=` in the output.
- Result: **Status Ok** — no Abnormal rooms. Pipeline 63.3 s (grab 50.1 / analyse 7.1).
- Display states: 02 and 06 and 08 **in use**; 01/03/04/05/07 idle (01/04/05 AVoIP standby,
  03/07 Windows lock screen). Common Area excluded (scheduled down, camera 502).
- Sync: 01, 02, 08 IN SYNC; 07 NOT VERIFIED (1 region isolated) — note only.
- Highest KDS: 46 °C (SM-11-02 TV-DEC-2 / 172.18.22.52) — warn band, below the 49 °C alarm.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260923_0925.jpg.
  Agent Mail daily quota: 45 of 50 remaining after this send.

## 2026-09-24 09:24 HKT
- Result: **Status Ok** — no Abnormal rooms. No `RESULT skip=` (throttle cleared).
- Display states: 01/02/04/05/07/08 in use; 03 idle (Windows lock screen), 06 idle (AVoIP standby).
- Sync: 01, 02, 07, 08 all IN SYNC — no out-of-sync flags anywhere this run.
- Highest KDS: 44 °C (SM-11-01) — below the 49 °C alarm. All 8 rooms' cameras online, all decoders ok.
- Common Area excluded (scheduled down, camera 502) — expected.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260924_0924.jpg.
  Engine v2.1.0; body 9,698 B, well under the 13,000 B limit. Agent Mail quota: 48 of 50 remaining.

## 2026-09-25 09:24 HKT
- Result: **Status Ok** — no Abnormal rooms. No `RESULT skip=` (throttle cleared; last run 08:27).
- Pipeline 58.8 s (scan 57.7 / contact sheet 0.4 / body 0.8). Engine v2.1.0.
- Display states: 02/03/06/08 **in use**; 01 idle (Windows lock), 04 idle (AVoIP standby),
  05 idle (Windows lock); 07 **unconfirmed** (content not readable). Common Area excluded (502).
- Sync: 01 and 08 IN SYNC; 02 (1 region) and 07 (0 regions) NOT VERIFIED — note only, no flags.
- Highest KDS: 42 °C, tied SM-11-01 and SM-11-07 — well below the 49 °C alarm. All decoders online.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260925_0924.jpg.
  Agent Mail quota: 48 of 50 remaining.

## 2026-09-28 09:23 HKT
- Throttle cleared (last run 08:09 today, ~74 min earlier). No `RESULT skip=`.
- Result: **Status Ok** — no Abnormal rooms. Pipeline 62.1 s (grab 50.2 / analyse 7.1). Engine v2.1.0.
- Display states: 01/03/04/06 **in use**; 02/05/07 idle (Windows lock); 08 **unconfirmed** (content not readable). Common Area excluded (scheduled down, 502).
- Sync: 01 and 07 IN SYNC; 02 **OUT OF SYNC (1ST RUN)** (first occurrence, not Abnormal); 08 NOT VERIFIED (0 regions).
- Highest KDS: 44 °C (SM-11-01) — well below the 49 °C alarm. All decoders online.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260928_0923.jpg. Body 9,799 B. Agent Mail quota: 49 of 50 remaining.

## 2026-09-29 09:16 HKT
- **SKIPPED.** Pipeline printed `RESULT skip=last run was 4 min ago (min interval 45 min)`.
  No upload, no email — guard honoured (previous completed run ~09:12).
- Nothing to report for this slot; no attachments produced.

## 2026-09-30 09:18 HKT
- Throttle cleared (previous run 08:12 today, ~66 min earlier). No `RESULT skip=`.
- Result: **Status Abnormal (SM-11-01)** — OUT OF SYNC confirmed on two consecutive runs
  (previous raw out-of-sync at 08:12, inside the 3 h window). Pipeline 90.5 s (grab 52.5 / analyse 30.6).
- **Likely an OCR artifact, not a real desync.** All four SM-11-01 panels show the same Windows
  lock screen; OCR read the clock as `9:17` (#1, #3 → idle) vs `917` (#2) and `9-17` (#4) → those
  two failed `is_clock()` and fell through to "content on screen". Same pattern on SM-11-07
  (`9.17` vs no text) → OUT OF SYNC (1ST RUN). Reported as-is per the rules.
- Display states: 02 and 08 in use; 01/03/04/05/06/07 idle (03/04 AVoIP standby, 01/05/06/07 lock).
  Common Area excluded (scheduled down, 502).
- Highest KDS: 43 °C (SM-11-02 TV-DEC-2) — well below the 49 °C alarm. All decoders online,
  no poller-restart artifact.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260930_0918.jpg.
  Body 9,978 B. Agent Mail quota: 48 of 50 remaining.
- Watch item: if 01 keeps flagging while all panels read a clock, the fix is to make
  `is_clock()` accept `917` / `9-17` style OCR (digits with no separator), matching the
  v2.5.2 lesson — never key a verdict on one exact character.

### Notes for next run
- Time-zone lookup: `zoneinfo.ZoneInfo('Asia/Hong_Kong')` fails (no tzdata in the venv), and
  `TZ=Asia/Hong_Kong date` in Git Bash also misleads (prints UTC labelled GMT). The reliable
  check is `date "+%Y-%m-%d %H:%M:%S %z"` (returns +0800) or Python `datetime.now()`.
- `grep -E "^RESULT"` on the pipeline output cleanly isolates the four RESULT lines.
- Body must be read from `.workbuddy/tmp/mail_body.html` and passed verbatim; do not inline images.
