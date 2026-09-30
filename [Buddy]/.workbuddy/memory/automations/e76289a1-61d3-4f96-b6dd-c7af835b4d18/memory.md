# Shek Mun AV audit — 21:15 slot

## 2026-09-23 (first recorded run)
- Executed 08:07 (manual/automation trigger; scheduled slot is 21:15).
- Pipeline `av_report.py` ran clean, exit 0, 66.1 s. Engine v1.5.0.
- Verdict: **Ok**. No room flagged. Common Area offline but `scheduled_down` → excluded.
- Highest KDS seen: 42 °C (SM-11-01 TV-DEC-2, SM-11-02 TV-DEC-2, SM-11-08 TV-DEC-2).
- Email sent to dannylam@hsu.edu.hk with both attachments; Agent Mail quota 49/50 left.
- Note: run stamped 08:07 while the automation is the 21:15 slot — subject carries the
  actual generation timestamp, not the slot time.

## 2026-09-24 (run at 08:14)
- Pipeline clean, exit 0, 61.9 s. Engine v2.1.0 (still uses `av_report.py` single entry).
- Verdict: **Ok**. No room flagged. Common Area scheduled down (HTTP 502) as usual.
- Highest KDS: 42 °C (SM-11-01). All 8 rooms' decoders online.
- SM-11-02 / 07 sync NOT VERIFIED (only 1 region isolated); SM-11-07 + 08 IN USE (content).
- Email sent to dannylam@hsu.edu.hk, 2 attachments; quota 49/50 remained after send.
- Throttle did not trigger (last run was the previous evening, well over 45 min).

## 2026-09-25 (run at 08:27)
- Pipeline clean, exit 0, 62.6 s. Engine v2.1.0. Throttle did not trigger.
- Verdict: **Ok**. No room flagged. Common Area scheduled down (HTTP 502) as usual.
- Highest KDS: 40 °C (SM-11-02, SM-11-07). SM-11-01 KDS n/a this run.
- SM-11-01 / 02 / 08 sync IN SYNC; SM-11-07 NOT VERIFIED (0 regions isolated).
- SM-11-03/05 lock screen idle, SM-11-04 AVoIP standby, SM-11-06 + 08 IN USE (content).
- Email sent to dannylam@hsu.edu.hk, 2 attachments; quota 49/50 remained after send.

## 2026-09-28 (run at 08:11) — SKIPPED
- Pipeline printed `RESULT skip=last run was 2 min ago (min interval 45 min)`.
- A real run had already completed at 08:09 this morning (contact sheet
  `all_rooms_20260928_0809.jpg` present), so this was scheduler catch-up.
- No attachment uploaded, no email sent. Quota untouched.

## 2026-09-30 (run at 08:12)
- Pipeline clean, exit 0, 77.9 s. Engine v2.5.7. Throttle did not trigger (no `RESULT skip=`).
- Verdict: **Ok**. No room flagged. Common Area scheduled down (HTTP 502) as usual.
- Highest KDS: 39 °C (SM-11-08 TV-DEC-2; 01/02/07 also 39). All 8 rooms' decoders online.
- Sync: SM-11-01 / 02 / 07 / 08 all **IN SYNC** (4/4 and 2/2 regions isolated — full coverage,
  no NOT VERIFIED this run). Rooms 03–06 single-display → N/A.
- Display states: 01/02/05/07/08 AVoIP standby, 03/04 Windows lock screen, 06 IN USE (content).
- Body 9,684 B + 700 reserve, under the 13,000 limit — sent verbatim, no trimming needed.
- Email sent to dannylam@hsu.edu.hk with both attachments; quota 49/50 remained after send.
- Note: this is the 21:15 slot automation; the machine was off overnight so it replayed at
  08:12. First real run of the day, so the throttle correctly allowed it.

## Standard flow (unchanged each run)
1. Load skill `shekmun-av-audit`.
2. Run `av_report.py` with the managed python venv exe.
3. Upload `RESULT html=` + `RESULT sheet=` via agent_mail_upload_attachment.
4. Read `.workbuddy/tmp/mail_body.html` and send verbatim as HTML body + file_refs.
5. Reply summary: status, flagged rooms, per-room idle/in-use, max KDS temp.
