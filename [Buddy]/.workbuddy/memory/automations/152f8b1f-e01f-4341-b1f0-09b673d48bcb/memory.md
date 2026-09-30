# 17:15 AV audit automation — run history

## 2026-09-22 17:16 (first recorded run)
- Pipeline ran clean, exit 0, 58.7 s. Result: **Status Ok** — no Abnormal triggers.
- All 8 cameras online; Common Area scheduled down (HTTP 502, expected).
- Max KDS 46 °C (SM-11-07 TV-DEC-1) — below the 49 °C alarm / inside the 46 °C warn band.
- Dual/quad rooms (01, 02, 07, 08) all IN SYNC — no sync persistence escalation.
- Emailed to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260922_1716.jpg.
  Agent Mail daily quota remaining after send: 39/50.

## 2026-09-23 17:16
- No `RESULT skip=` (60 min since 16:16). Pipeline 59.5 s, verdict **Ok**, no Abnormal.
- SM-11-01 OUT OF SYNC (1ST RUN) — first occurrence, watch the next run. 02/08 IN SYNC,
  07 NOT VERIFIED. Max KDS 43 °C (SM-11-01 TV-DEC-2/4). Common Area 502 (scheduled down).
- Emailed with AV_room_audit.html + all_rooms_20260923_1716.jpg. Quota after: 34/50.
- **Incident:** body was 14,400 B (over the Agent Mail ceiling) → 4 failed sends. Also fired
  one junk `TEST`-body probe to Danny while diagnosing. Real report sent after.

## 2026-09-24 17:16
- No `RESULT skip=`. Pipeline 58.3 s, exit 0, verdict **Ok**, no Abnormal.
- SM-11-01 **OUT OF SYNC (1ST RUN)** again — 2nd day running (the 3 h confirm window
  had expired, so it re-armed as a first run). Not abnormal; watch the 18:16 run.
  02/07/08 IN SYNC. Max KDS 42 °C (SM-11-01 TV-DEC-2). Common Area 502 (scheduled down).
- Emailed with AV_room_audit.html + all_rooms_20260924_1716.jpg. Quota after: 40/50.
- Smooth send: body 9,821 B (v1.6.1 auto-trim), verbatim paste, `skip_confirmation: true`,
  fresh file ids — one call, no retries.

## 2026-09-25 17:17
- No `RESULT skip=`. Pipeline 54.9 s, exit 0, verdict **Ok**, no Abnormal.
- **SM-11-01 back to IN SYNC** (4/4 displays) — the OUT OF SYNC (1ST RUN) seen on 09-23 and
  09-24 has cleared, no escalation. 07 IN SYNC; 02 and 08 NOT VERIFIED (too few regions).
- Max KDS 46 °C (SM-11-01 TV-DEC-2) — at the warn band edge, still below the 49 °C alarm.
  Highest reading in 4 days; watch the 18:16 run.
- Common Area 502 (scheduled down), excluded from verdict.
- Emailed with AV_room_audit.html + all_rooms_20260925_1717.jpg. Quota after: 40/50.
- Clean one-call send: body 9,736 B, `skip_confirmation: true`, fresh file ids.

## 2026-09-29 17:16
- No `RESULT skip=`. Pipeline 63.7 s, exit 0, verdict **Ok**, no Abnormal.
- Rooms 01/03/04/06/07/08 Idle, 05 In use. 01 (4/4), 07, 08 IN SYNC.
  **SM-11-02 OUT OF SYNC (1ST RUN)** — #1 idle standby vs #2 `AVPSYSTENSTATUR` garbled banner
  read as content; downgraded to `check`, not Abnormal. Watch the 18:16 run to confirm.
- Max KDS **47 °C** (SM-11-08 TV-DEC-2) — highest reading recorded so far, inside the warn
  band (46) and below the 49 °C alarm. Watch it.
- Common Area 502 (scheduled down), excluded from verdict.
- Emailed with AV_room_audit.html + all_rooms_20260929_1716.jpg. Quota after: 44/50.
- Clean one-call send: body 9,815 B, `skip_confirmation: true`, fresh file ids.

### Reusable notes
- Body was transcribed verbatim from `.workbuddy/tmp/mail_body.html` (13.8 KB) — read the
  file first, then paste; do not summarise or placeholder.
- Upload both attachments before SendMessage; file ids expire ~12 h (expires_at 2026-09-23T05:17Z).
- `skip_confirmation: true` works, no confirmation token needed.
- **Ceiling calibrated: 14,292 B OK, 14,400 B fails.** As of v1.6.1 `av_mail.py` trims
  automatically to ≤13,000 B, so just send the file verbatim — no hand-shrinking.
- **If `SendMessage` reports `required error field_name: to`, first re-check that you
  actually passed `params`** — that error is identical when the params object is omitted.
  Never send a probe mail to Danny to distinguish the two cases.
- After any probe/correction send, re-upload both attachments: a file ref is consumed by
  the message it was attached to.
