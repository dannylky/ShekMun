# Automation 49e94f9b — Shek Mun AV audit @ 10:15

## 2026-09-22 10:25 (first recorded run)
- Pipeline ran clean, 62.8 s. RESULT lines: subject / html / sheet / body all produced.
- Verdict: **Ok** (no Abnormal room). No KDS alarm, no explicit `fail` outside scheduled down,
  all 8 room cameras online, no out-of-sync.
- Common Area (172.18.22.109) still HTTP 502 — scheduled down, excluded from verdict as expected.
- Highest KDS: 44 °C (SM-11-01 TV-DEC-2); alarm threshold 49 °C.
- Email sent to dannylam@hsu.edu.hk, 2 attachments (AV_room_audit.html + all_rooms_20260922_1025.jpg).
  Quota after send: 46/50 remaining.
- No poller-restart / mass-`unknown` artifact this run (the 08:02 issue did not recur).

## 2026-09-24 10:19
- No `RESULT skip=` (throttle passed). Pipeline 60.5 s, exit 0. Engine v2.1.0.
- Verdict **Ok**; no Abnormal room. Max KDS 44 °C (SM-11-01), alarm 49 °C.
- Common Area (172.18.22.109) still HTTP 502 — scheduled down, excluded.
- Sync: SM-11-01 IN SYNC, SM-11-07 IN SYNC, SM-11-02 / SM-11-08 NOT VERIFIED (1 region).
- Email sent, 2 attachments; quota 47/50 remaining. Body 9,708 B — well under the
  13,000 B limit, no trimming needed, sent first try.

### Notes for next run
- Body must be read from `.workbuddy/tmp/mail_body.html` verbatim — do not send a placeholder.
- Do not inline base64 images; snapshots live in the HTML attachment.

## 2026-09-25 10:21
- No `RESULT skip=` (throttle passed). Pipeline 55.4 s, exit 0. Engine v2.1.0.
- Verdict **Ok**; no Abnormal room. Max KDS 43 °C (SM-11-01 / 07 / 08), alarm 49 °C.
- Common Area still HTTP 502 (scheduled down, excluded).
- Sync: SM-11-01 IN SYNC (4 regions), SM-11-02 IN SYNC, SM-11-07 IN SYNC;
  SM-11-08 NOT VERIFIED (0 regions isolated) — same weak-signal pattern as recent runs.
- Email sent first try, 2 attachments; quota 47/50 remaining. Body 10,389 B, under
  the 13,000 B limit — no manual trimming needed.

## 2026-09-28 10:18
- No `RESULT skip=` (throttle passed). Pipeline 66.1 s total, exit 0. Engine v2.1.0.
- Verdict **Ok**; no Abnormal room. Max KDS 44 °C (SM-11-01), alarm 49 °C.
- Common Area still HTTP 502 (scheduled down, excluded). All 8 room cameras online.
- Display states: 01/03/04/06/08 IN USE (content on screen); 02/05/07 IDLE (AVoIP standby).
- Sync: SM-11-01 IN SYNC (4 regions), SM-11-08 IN SYNC (2); SM-11-02 CHECK REGION
  (mixed standby banners, 1 idle / 1 not idle); SM-11-07 NOT VERIFIED (0 regions).
- Email sent first try, 2 attachments; quota 48/50 remaining. Body 9,806 B — under the
  13,000 B limit, no trimming needed.

## 2026-09-29 10:19
- **SKIPPED** by the throttle (v1.6.0): last completed run was 27 min ago (< 45 min min-interval).
  Pipeline printed `RESULT skip=` only; nothing written, no upload, no email sent.
- Cause: scheduler catch-up replay (09:52 run already covered this window). Correct behaviour —
  no action needed beyond reporting the one-line skip.

## 2026-09-30 10:16
- **SKIPPED** by the throttle: pipeline printed only `RESULT skip=last run was 28 min ago
  (min interval 45 min)`. Nothing written, no upload, no email. Correct behaviour — a
  09:4x run already covered this window. Same pattern as 2026-09-29.

## 2026-09-23 10:26
- No `RESULT skip=` (throttle v1.6.0 passed, >45 min since previous run). Pipeline 61.6 s, exit 0.
- Verdict **Ok**; no Abnormal room. Max KDS 47 °C (SM-11-02 TV-DEC-2), alarm 49 °C.
- Common Area still HTTP 502 (scheduled down, excluded). SM-11-08 sync NOT VERIFIED (1 region).
- Email sent, 2 attachments; quota 44/50 remaining.
- Body transcribed verbatim from mail_body.html — send succeeded first try (no 40401 this time).
