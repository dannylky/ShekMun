# 16:15 AV audit automation — run history

Keep this high-level only (no full report bodies).

## 2026-09-22 16:16 (first recorded run for this slot)
- Pipeline ran clean in 59.0 s, no manual intervention.
- Verdict: **Status: Ok**. No Abnormal rooms.
- Common Area camera offline (HTTP 502) + its devices `fail`, but it is in
  `scheduled_down`, so correctly excluded from the verdict.
- Highest KDS: 44 °C (SM-11-08 TV-DEC-2) — below the 46 warn / 49 alarm bands.
- SM-11-02 picture sync came back NOT VERIFIED (only 1 display region isolated) —
  informational, not a fault.
- Email sent to dannylam@hsu.edu.hk with both attachments (HTML report + contact sheet).
  Quota after send: 40/50 remaining.

## 2026-09-23 16:16
- Pipeline ran clean in 58.1 s, no skip (59 min since 15:17 run), no manual intervention.
- Verdict: **Status: Ok**. No Abnormal rooms.
- Common Area camera offline (HTTP 502) + its device `fail`, but scheduled_down → excluded.
- Highest KDS: 45 °C (SM-11-01 TV-DEC-2) — below the 46 warn / 49 alarm bands.
- SM-11-07 picture sync NOT VERIFIED (only 1 display region isolated) — informational.
- Email sent with both attachments (13,775 B body sent verbatim, queued first try).
  Quota after send: 36/50 remaining.

## 2026-09-24 16:16
- Pipeline ran clean in 66.2 s, no skip (59 min since 15:17 run), no manual intervention.
- Verdict: **Status: Ok**. No Abnormal rooms.
- Common Area camera offline (HTTP 502) + its device `fail`, but scheduled_down → excluded.
- Highest KDS: 43 °C (SM-11-01) — below the 46 warn / 49 alarm bands.
- SM-11-08 picture sync NOT VERIFIED (only 1 region isolated) — informational.
- Engine v2.1.0. Email sent with both attachments (9,829 B body sent verbatim, queued
  first try). Quota after send: 41/50 remaining.

## 2026-09-25 16:16
- Pipeline ran clean in 59.1 s, no skip, no manual intervention.
- Verdict: **Status: Ok**. No Abnormal rooms.
- Common Area camera offline (HTTP 502) + its device `fail`, but scheduled_down → excluded.
- Highest KDS: 46 °C, tied between SM-11-01 and SM-11-07 (TV-DEC-1) — first run to reach
  the 46 warn band; still below the 49 alarm. Worth watching on the next slot.
- SM-11-02 / 07 / 08 picture sync NOT VERIFIED (0–1 region isolated) — informational.
- SM-11-08 display state UNCONFIRMED (no readable region), not a fault.
- Email sent with both attachments (9,896 B body sent verbatim, queued first try).
  Quota after send: 41/50 remaining.

## 2026-09-28 16:16
- **SKIPPED** by the 45-min throttle — last run was 9 min earlier (the 16:05/16:06 catch-up
  burst replaying missed slots). No attachments uploaded, no email sent.
- Note for future slots: 2026-09-28 had a replay burst around 16:02–16:06, so adjacent
  hourly slots may self-skip for the rest of that window. Expected, not a fault.

## 2026-09-29 16:16
- **SKIPPED** by the 45-min throttle — last run was 4 min earlier (16:11-ish catch-up run).
  No attachments uploaded, no email sent. Guard held.

## 2026-09-30 16:16
- Pipeline ran clean in 82.5 s, no skip, no manual intervention.
- Verdict: **Status: Abnormal (SM-11-01)** — first real Abnormal for this slot.
  SM-11-01 displays OUT OF SYNC confirmed on two consecutive runs (15:15 = 1ST RUN,
  16:17 confirmed → escalated). Regions #1/#2/#3 active, #4/#9 AVoIP standby.
  Needs eyeball confirmation against the HTML snapshot.
- Other rooms: 02 IN SYNC (content), 03/05/06 in use, 04/07/08 idle standby, 07/08 IN SYNC.
- Common Area camera offline (HTTP 502) + device fail, but scheduled_down → excluded.
- Highest KDS: 45 °C (SM-11-02 TV-DEC-2) — below the 49 alarm.
- Email sent with both attachments (9,972 B body sent verbatim, queued first try).
  Quota after send: 44/50 remaining.
