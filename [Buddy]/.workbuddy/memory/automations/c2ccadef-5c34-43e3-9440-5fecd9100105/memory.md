# AV audit — 12:15 slot (automation c2ccadef)

## 2026-09-22 12:16 — run 1
- Pipeline `av_report.py` ok, exit 0, 66.6 s total (scan 65.3 s; grab 48.9 s dominated).
- Verdict: **Status: Ok** (no room flagged Abnormal). Subject verbatim:
  `HSUHK@Shek Mun Audit report- 2026-09-22 12:16 / Status: Ok`
- Flagged info-only: SM-11-02 & SM-11-08 sync NOT VERIFIED; SM-11-08 idle (Windows lock
  screen). Common Area scheduled down (camera HTTP 502) — excluded from verdict as designed.
- Highest KDS: 43 °C (SM-11-01 TV-DEC-2). All temps 34–43 °C, well under the 49 °C alarm.
- Email sent to dannylam@hsu.edu.hk with 2 attachments (AV_room_audit.html + contact sheet
  all_rooms_20260922_1216.jpg). Queue: 44/50 daily quota left.
- No `cleanup=` line emitted this run.

### Notes for next run
- Pipeline + Agent Mail flow worked first time with no deviations; nothing special to redo.
- `av_summary.json` is a **list**, not a dict — don't `.keys()` on it.
- Body must be read from `.workbuddy/tmp/mail_body.html` and sent verbatim; do not rebuild it.

## 2026-09-23 12:17 — run 2
- Pipeline ok, exit 0, 68.9 s (scan 67.6 s; grab 50.5 s dominated). No `RESULT skip=`.
- Verdict: **Status: Ok**, subject `HSUHK@Shek Mun Audit report- 2026-09-23 12:17 / Status: Ok`.
- No Abnormal room. Info-only: SM-11-01 idle (Windows lock screen), SM-11-06 idle (AVoIP
  decoder standby), Common Area scheduled down (camera HTTP 502) — excluded as designed.
- All dual/quad rooms IN SYNC (01/02/07/08); single-display rooms N/A.
- Highest KDS: 45 °C (SM-11-02 TV-DEC-2) — under the 49 °C alarm, but the warmest seen so far.
- Mail body 14,292 B sent verbatim **successfully** on the first attempt (queued:true).
  So the SendMessage payload limit is above 14.3 KB; earlier failure was at 14,855 B.
- Email sent with 2 attachments (AV_room_audit.html + all_rooms_20260923_1217.jpg).
  Quota after send: 40/50 remaining.

## 2026-09-24 12:17 — run 3
- Pipeline ok, exit 0, 64.7 s (scan 63.3 s; grab 49.9 s dominated). No `RESULT skip=`.
  Engine now v2.1.0 (wall-only display_filter for rooms 2/7/8).
- Verdict: **Status: Ok**, subject `HSUHK@Shek Mun Audit report- 2026-09-24 12:17 / Status: Ok`.
- No Abnormal room. Info-only: SM-11-04 idle (Windows lock screen, clock 12:15);
  SM-11-07 no display region isolated (UNCONFIRMED, sync NOT VERIFIED, 0 regions);
  SM-11-08 only 1 region isolated (sync NOT VERIFIED); Common Area scheduled down (HTTP 502).
- Dual/quad rooms 01 & 02 IN SYNC; 07/08 not verifiable this run.
- Highest KDS: 45 °C (SM-11-01 TV-DEC-1) — same as yesterday, under the 49 °C alarm.
- Body 9,679 B (+700 reserve, limit 13,000) — trim worked, sent verbatim first attempt
  (queued:true). Quota after send: 45/50.

### Notes for next run
- SM-11-07 now yields **zero** isolated display regions after the wall-only filter
  (max_center_y_frac 0.35). Worth watching: if it stays at 0 regions the threshold may be
  too tight for that room's camera angle.
- Pipeline + mail flow ran clean with no deviations again.

## 2026-09-25 12:16 — run 4
- Pipeline ok, exit 0, 56.3 s (scan 55.2 s; grab 49.7 s dominated). No `RESULT skip=`.
  Engine v2.1.0.
- Verdict: **Status: Ok**, subject `HSUHK@Shek Mun Audit report- 2026-09-25 12:16 / Status: Ok`.
- No Abnormal room. Info-only: SM-11-03 idle (Windows lock screen), SM-11-05 idle (AVoIP
  decoder standby), SM-11-08 UNCONFIRMED + sync NOT VERIFIED (0 regions isolated),
  Common Area scheduled down (HTTP 502).
- Sync: SM-11-01, 02, 07 all **IN SYNC** — SM-11-07 recovered to 2 regions this run
  (was 0 yesterday), so the 0.35 threshold is fine, just angle/frame dependent.
- Highest KDS: 44 °C (SM-11-01 TV-DEC-2) — all 36–44 °C, well under the 49 °C alarm.
- Body 9,660 B (+700 reserve, limit 13,000), sent verbatim first attempt (queued:true).
  Quota after send: 45/50.
- Confirmation that excluding `TV-Res-*` from the max-temp query is needed — reserve
  decoders otherwise pollute the top of the list.

## 2026-09-28 12:17 — run 5
- Pipeline ok, exit 0, 58.5 s (scan 57.3 s; grab 48.6 s dominated). No `RESULT skip=`.
  Engine v2.1.0.
- Verdict: **Status: Ok**, subject `HSUHK@Shek Mun Audit report- 2026-09-28 12:17 / Status: Ok`.
- No Abnormal room. Info-only: SM-11-03 idle (Windows lock screen, clock 12:16);
  Common Area scheduled down (camera HTTP 502).
- Sync: SM-11-01 (4 regions), 02, 07, 08 all **IN SYNC** — all four multi-display rooms
  verifiable this run, best coverage so far.
- Highest KDS: 44 °C (SM-11-01 TV-DEC-2); range 35–44 °C, under the 49 °C alarm.
- Body 9,642 B (+700 reserve, limit 13,000), sent verbatim first attempt (queued:true).
  Quota after send: 46/50.
- Note: 4 prior runs fired today already (08:09, 09:23, 10:18, 11:16) — the 11:16 one was
  61 min before, so the 45-min throttle correctly allowed this run.

## 2026-09-29 12:17 — run 6
- Pipeline ok, exit 0, 72.4 s (scan 71.2 s; grab 48.8 s dominated). No `RESULT skip=`.
  Engine v2.5.6 (Room 1 re-mark + Room 4 marked regions now in config).
- Verdict: **Status: Ok**, subject `HSUHK@Shek Mun Audit report- 2026-09-29 12:17 / Status: Ok`.
- No Abnormal room. Info-only: SM-11-02 OFF/PARTIAL lighting; Common Area scheduled down
  (camera HTTP 502) — excluded as designed.
- Sync: SM-11-02 **IN SYNC**; SM-11-01 **CHECK REGION** (3 standby vs 1 dissenter, low
  confidence); SM-11-07 and SM-11-08 both **OUT OF SYNC (1ST RUN)** — first occurrence for
  each, so not Abnormal. Watch the next run: if either repeats it escalates to Abnormal.
- Highest KDS: 42 °C (SM-11-01 TV-DEC-2), excluding `TV-Res-*`; range 30–42 °C.
- Body 9,937 B (+700 reserve, limit 13,000), sent verbatim first attempt (queued:true).
  Quota after send: 47/50.
- Note: today already had a 11:17 run (~60 min earlier), so the 45-min throttle allowed it.

## 2026-09-30 12:15 — run 7 — SKIPPED
- Pipeline printed `RESULT skip=last run was 12 min ago (min interval 45 min)`. A run had
  already gone out ~12:03 today (catch-up burst). No upload, no email, as the guard requires.
- Nothing else executed; no summary/JSON read this slot.
