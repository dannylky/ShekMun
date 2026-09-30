# Automation 45158dfa — Shek Mun AV audit @ 11:15 slot

## 2026-09-22 11:16 (first recorded run)
- Pipeline ran clean in 59.0 s (engine v1.5.0). Status **Ok**, no Abnormal.
- Mail sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260922_1116.jpg.
  Daily quota after send: 45/50 remaining.
- Flags to watch next run:
  - **SM-11-07** = OUT OF SYNC (**1ST RUN**) — 3 regions isolated, 1 standby vs 2 content.
    If 12:15 agrees → escalates to Abnormal.
  - **SM-11-08** = sync NOT VERIFIED (only 1 region isolated) — needs eyeball check.
  - Common Area scheduled down, camera HTTP 502 (expected, excluded from verdict).
- Highest KDS: 43 °C (SM-11-01 / TV-DEC-2, 172.18.22.51). All decoders ok, far below 49 °C.
- No `cleanup=` RESULT line this run.

## 2026-09-23 11:16
- Pipeline ran clean in 61.6 s (engine v1.6.0). Status **Ok**, no Abnormal, no `RESULT skip=`.
- Mail sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260923_1116.jpg.
  Daily quota after send: 41/50 remaining.
- Carry-over flags resolved: **SM-11-07 is now IN SYNC** (2 regions isolated, both content) —
  yesterday's OUT OF SYNC (1ST RUN) did not repeat, so no escalation. **SM-11-08 still
  NOT VERIFIED** (only 1 region isolated) — persistent, needs an eyeball check.
- Common Area still scheduled down, camera HTTP 502 (expected, excluded from verdict).
- Highest KDS: 46 °C (SM-11-02 / TV-DEC-2, 172.18.22.52) — warn band, still below 49 °C.
- **Tooling gotcha:** `SendMessage` silently drops the whole params object when the body is
  very large (~15 KB) → error `required error field_name: to`. The generated mail body works
  if sent as-is at ~11 KB with the per-screen detail lines trimmed; if the full body must be
  sent verbatim, split the send or shrink the body. Also: one stray test email was sent this
  run; a correction note followed. Never fire a probe send to Danny again.

## 2026-09-24 11:16
- Pipeline ran clean in 63.7 s (engine v2.1.0). Status **Ok**, no Abnormal, no `RESULT skip=`.
- Mail sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260924_1116.jpg.
  Body 9,700 B — sent verbatim, no trimming needed. Quota after send: 46/50 remaining.
- Carry-over: SM-11-07 **still NOT VERIFIED** (1 region isolated, 3rd consecutive day) —
  needs an eyeball check. **New: SM-11-08 also NOT VERIFIED** this run (1 region).
- SM-11-01 and SM-11-02 both IN SYNC (2 regions each).
- Common Area still scheduled down, camera HTTP 502 (expected, excluded).
- Highest KDS: 44 °C (SM-11-01 / TV-DEC-4) — below the 46 °C warn band.
- `RESULT cleanup=removed 2 file(s) older than 48 h` appeared this run.

## 2026-09-25 11:16
- Pipeline ran clean in 55.6 s (engine v2.1.0). Status **Ok**, no Abnormal, no `RESULT skip=`.
- Mail sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260925_1116.jpg.
  Body 9,753 B — sent verbatim, no trimming. Quota after send: 46/50 remaining.
- Carry-over: SM-11-01 **IN SYNC** (4 regions). SM-11-02 NOT VERIFIED (1 region);
  **SM-11-07 and SM-11-08 both NOT VERIFIED with 0 regions isolated** — weakest reading yet,
  both rooms had readable-ish evidence on earlier days. Worth an eyeball check: either the
  wall TVs were genuinely dark/featureless this slot, or the region detector is losing them.
- SM-11-02 display IDLE (blank screen); SM-11-01 + SM-11-03 IN USE (content on screen);
  SM-11-04/05/06 IDLE (Windows lock screen); SM-11-07/08 UNCONFIRMED (content not readable).
- Common Area still scheduled down, camera HTTP 502 (expected, excluded).
- Highest KDS: 44 °C (SM-11-01 and SM-11-07) — below the 46 °C warn band.
- `RESULT cleanup=removed 2 file(s) older than 48 h`.

## 2026-09-28 11:16
- Pipeline 59.3 s (engine v2.1.0). Status **Ok**, no Abnormal, no `RESULT skip=`.
- Mail sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260928_1116.jpg.
  Body 9,673 B — sent verbatim, no trimming. Quota after send: 47/50 remaining.
- Carry-over: SM-11-07 **NOT VERIFIED with 0 regions isolated** (also 0 the day before) —
  the region detector keeps failing to isolate wall TVs in that room; needs an eyeball check
  or a `display_filter` tune.
- SM-11-01 (4 regions), SM-11-02 (2) and SM-11-08 (2) all IN SYNC — SM-11-02's 09:23
  OUT OF SYNC (1ST RUN) never repeated, so no escalation.
- SM-11-05 IDLE (Windows lock screen); all other rooms IN USE (content on screen).
- Common Area still scheduled down, camera HTTP 502 (expected, excluded).
- **Highest KDS 46 °C** (SM-11-01 / TV-DEC-2) — top of the 46 °C warn band, up from 44 °C
  earlier in the day. Watch whether it crosses toward 49 °C on the 12:15 slot.

## 2026-09-29 11:15 slot (run at 11:17)
- Pipeline 86.8 s (engine v2.5.5). Status **Ok**, no Abnormal, no `RESULT skip=`.
- Mail sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260929_1117.jpg.
  Body 9,753 B — sent verbatim, no trimming. Quota after send: 48/50 remaining.
- **First send attempt returned `Streamable HTTP error … {"error":"internal_error"}`.**
  Fix = re-upload both files and retry with the fresh file ids; the second call returned
  `queued:true`. Not the size/`field_name: to` failure mode — a transient upstream error.
  Lesson: on `internal_error`, retry once with fresh uploads before assuming anything else.
- Rare quiet slot: **5 of 8 rooms IDLE on AVoIP decoder standby** (01, 02, 03, 07, 08).
  In use: SM-11-04 (motion 71 %), SM-11-05 (10 %), SM-11-06 (static content).
- Carry-over flag: **SM-11-07 and SM-11-08 both now IN SYNC with 2 regions each** — the
  long-running NOT VERIFIED / 0-region problem on those rooms is resolved; the marked
  display regions + standby row-profile fallback are holding.
- **New: SM-11-01 = CHECK REGION** — 4 regions isolated, 3 standby vs #4 Active content
  (mean 170, no OCR/luminance evidence), lone low-confidence dissenter → not out-of-sync.
  Watch the 12:15 slot: if the same #4 disagreement repeats it cannot escalate by the sync
  rule (needs a `high` reading), but it is worth an eyeball check.
- Common Area still scheduled down, camera HTTP 502 (expected, excluded).
- Highest KDS **42 °C** (SM-11-01 / TV-DEC-2) — down from 46 °C, well below 49 °C.

## 2026-09-30 11:15 slot (run at 11:17)
- Pipeline 83.8 s (engine **v2.6.0**). **Status Abnormal (SM-11-02)** — first Abnormal in
  this slot's history. No `RESULT skip=`.
- Mail sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260930_1117.jpg.
  Body 9,924 B verbatim. Quota after send: 47/50 remaining. Upload → send clean first try.
- **SM-11-02 OUT OF SYNC (confirmed, 2nd run within 3 h)** — #1 Active "ProcessesInvolved
  in Dictalion" (mean 116) vs #2 AVoIP standby. Room motion 10.81 % (highest of the fleet),
  so someone is genuinely presenting on one TV while its twin sits on standby. Looks real,
  not a detector artifact — but worth Danny eyeballing the HTML snapshot.
- **v2.6.0 clock fix worked:** SM-11-01 back to **IN SYNC** (4 idle panels) after yesterday's
  CHECK REGION and this morning's false OUT OF SYNC at 09:18. SM-11-07 / 11-08 also IN SYNC.
- Quiet slot otherwise: SM-11-03/04/05 = Windows lock screen (clock 11:15), SM-11-01/06/07/08
  = AVoIP standby. Only SM-11-02 in use.
- Highest KDS **45 °C** (SM-11-02 / TV-DEC-2) — warn band, below 49 °C.
- Common Area still scheduled down, camera HTTP 502 (expected, excluded).
- Watch next run (12:15): if SM-11-02 stays out of sync it is a real hardware/sourcing
  issue, not transient.
