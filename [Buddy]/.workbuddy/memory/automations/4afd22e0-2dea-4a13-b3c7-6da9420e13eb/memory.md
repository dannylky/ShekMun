# 18:15 AV audit — execution log

## 2026-09-22 18:16
- Pipeline ran clean, 59.8 s. Verdict **Ok**.
- Sent to dannylam@hsu.edu.hk with 2 attachments (AV_room_audit.html + all_rooms_20260922_1816.jpg). Queue accepted, quota 38/50 left.
- Watch item: SM-11-01 logged **OUT OF SYNC (1ST RUN)** — not abnormal under the v1.5.0 two-run rule. If the 19:15 run agrees it escalates to Abnormal.
- Max KDS 45 °C (SM-11-07 TV-DEC-1), under the 49 °C alarm.
- Common Area still scheduled down / camera HTTP 502 — expected.

## 2026-09-23 18:16
- Pipeline ran clean, 63.2 s. Verdict **Ok** (engine v1.6.1).
- Sent with 2 attachments; queue accepted, quota 33/50 left.
- Watch item moved: **SM-11-07** now OUT OF SYNC (1ST RUN) (mixed standby banners); SM-11-01 clean this time (0 regions isolated → NOT VERIFIED). If 19:15 agrees, escalates.
- Max KDS 42 °C (SM-11-02 TV-DEC-2) — well under 49 °C.
- Common Area scheduled down / HTTP 502 — expected.

## 2026-09-24 18:17
- Pipeline ran clean, 59.9 s. Verdict **Abnormal (SM-11-01)** — engine v2.1.0.
- Sent with 2 attachments; queue accepted, quota 39/50 left.
- Abnormal cause: SM-11-01 OUT OF SYNC confirmed on two consecutive runs (17:16 + 18:17):
  #1 AVoIP standby vs #2/#3 active content, 100% of main display area. Not the two-run
  guard — this is a real escalation, first Abnormal of this kind since the v1.5.0 rule.
- Max KDS 41 °C (SM-11-08 TV-DEC-2) — well under 49 °C.
- SM-11-07 / SM-11-08 sync NOT VERIFIED (only 1 / 0 wall regions isolated after the
  v2.0.0 desk filter) — worth watching; the filter may be over-pruning SM-11-08.
- Common Area scheduled down / HTTP 502 — expected.

## 2026-09-25 18:16
- Pipeline ran clean, 57.8 s. Verdict **Ok** (engine v2.1.0).
- Sent with 2 attachments; queue accepted, quota 39/50 left.
- Yesterday's Abnormal (SM-11-01) cleared — back to IN SYNC.
- Watch item: SM-11-01 sync reads IN SYNC on "3 evidenced displays all active" while
  display #4 is the AVoIP standby banner and the room pill says Idle. The standby
  display looks excluded from the sync comparison — possible v2.x regression in
  sync_check() region selection. Worth a look if it recurs.
- Wall-only rooms SM-11-02 (0 regions) and SM-11-08 (0 regions) sync NOT VERIFIED again;
  SM-11-07 only 1. The v2.0.0 desk filter is over-pruning all three.
- Max KDS 45 °C (SM-11-01 TV-DEC-2), under the 49 °C alarm but highest of the week.
- Common Area scheduled down / HTTP 502 — expected.

## 2026-09-29 18:16
- Pipeline ran clean, 62.6 s. Verdict **Ok** (engine v2.5.7). No throttle hit.
- Sent with 2 attachments; queue accepted, quota 43/50 left.
- Watch item cleared: SM-11-02's OUT OF SYNC (1ST RUN) from the 17:15 run did **not**
  escalate — back to IN SYNC. SM-11-01 remains CHECK REGION (4 regions isolated, 3
  standby vs 1 low-confidence dissenter) — recurring all day, still not Abnormal.
- Max KDS 44 °C (SM-11-08 TV-DEC-2), down from 47 °C at 17:15.
- Common Area scheduled down / HTTP 502 — expected.
