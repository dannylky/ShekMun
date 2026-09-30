# Automation 6d15b393 — Shek Mun AV audit @ 15:15

## 2026-09-22 15:15
- Ran `av_report.py` (57.2 s, engine v1.5.0). Status **Ok**, no rooms flagged.
- Max KDS 43 °C (SM-11-08 TV-DEC-2). All decoders `ok`, all 8 cameras online.
- Common Area scheduled down (camera HTTP 502) — excluded from verdict.
- Email sent to dannylam@hsu.edu.hk with AV_room_audit.html + all_rooms_20260922_1516.jpg.
- Daily quota remaining after send: 41/50.

## 2026-09-23 15:17
- Ran `av_report.py` (60.8 s, engine v1.6.0). Status **Ok**, no rooms flagged.
- Throttle did not trip; no `RESULT skip=`. Max KDS 46 °C (SM-11-01, all 4 decoders).
- Idle: 01 (AVoIP standby), 04 (Windows lock), 06 (AVoIP standby), 07 (Windows lock).
  In use: 02, 03, 05, 08. Sync not verified: 07, 08.
- Common Area still scheduled down (camera HTTP 502) — excluded from verdict.
- Body 13,975 B sent verbatim, first try OK. Email sent; quota remaining 37/50.

## 2026-09-24 15:16
- Ran `av_report.py` (56.2 s, engine v2.1.0). Status **Ok**, no rooms flagged. No `RESULT skip=`.
- Max KDS 45 °C (SM-11-01 TV-DEC-2). All decoders ok, 8/9 cameras online.
- Idle: 01, 03, 04, 05, 06 (AVoIP standby, 03 = Windows lock). In use: 02, 07.
  08 UNCONFIRMED (no wall region isolated → sync NOT VERIFIED).
- Common Area still scheduled down (camera HTTP 502) — excluded from verdict.
- Body 9,786 B, first try OK. Email sent; quota remaining 42/50.

## 2026-09-25 15:16
- Ran `av_report.py` (56.3 s, engine v2.1.0). Status **Ok**, no rooms flagged. No `RESULT skip=`.
- Max KDS 46 °C (SM-11-07 TV-DEC-1, and SM-11-01 also 46 °C). All decoders ok, 8/9 cameras online.
- Idle: 03 (AVoIP standby). In use: 01, 02, 04, 05, 06. 07 & 08 UNCONFIRMED
  (0 wall regions isolated → sync NOT VERIFIED; 07 had a desk-level Windows lock at 3:14).
- Common Area still scheduled down (camera HTTP 502) — excluded from verdict.
- Body 10,383 B, first try OK. Email sent; quota remaining 42/50.
- Observation (not acted on): SM-11-02 region #5 OCR reads an AVoIP standby banner but is
  `monitored=False` — the wall filter (max_center_y_frac 0.35) drops it before the AVoIP
  promotion rule fires. Possible gap vs the v2.0.0 exception; flagged to Danny for a call.

## 2026-09-28 15:16
- Ran `av_report.py` (60.0 s, engine v2.1.0). Status **Ok**, no rooms flagged. No `RESULT skip=`.
- Max KDS 43 °C (SM-11-01 / 02 / 08). All decoders ok, 8/9 cameras online.
- Idle: 06 (Windows lock). In use: 01, 02, 03, 04, 05, 07. 08 UNCONFIRMED (content not
  readable). Sync NOT VERIFIED: 02, 07, 08 (only 1/1/0 wall regions isolated). 01 IN SYNC (4/4).
- Common Area still scheduled down (camera HTTP 502) — excluded from verdict.
- Body 9,688 B, first try OK. Email sent; quota remaining 43/50.
- Note: project was idle 09-26 → 09-27 (no runs); throttle did not interfere.

## 2026-09-29 15:15 — run OK, **email NOT sent**
- `av_report.py` 76.2 s (engine v2.5.6). Status **Ok**, no rooms flagged. No `RESULT skip=`.
- Idle: 01, 02, 07 (AVoIP standby), 03, 04 (Windows lock), 06 (standby).
  In use: 05, 08 (content on screen). Sync: 01 (4/4), 02, 07, 08 all **IN SYNC** —
  the 14:15 SM-11-08 OUT OF SYNC / Abnormal cleared this run.
- Max KDS 43 °C (SM-11-08). All decoders ok, 8/9 cameras online.
  Common Area still scheduled down (camera HTTP 502) — excluded from verdict.
- **BLOCKER:** both attachments uploaded fine, but the `mcp__agent-mail` tool group
  (`SendMessage`) never entered the deferred tools index this session — it stayed
  "still connecting". `WaitForMcpServers` is also not available here. Waited ~4 min,
  6 retries, no change. Confirmed via `.workbuddy/mcp-tool-list.json` that `SendMessage`
  does exist on that server, so it is a connection problem, not a renamed tool.
- Per the skill rule, no email was fabricated as sent. Report delivered locally instead.
- To backfill: the report + body are already on disk, so only a re-upload (fresh
  `file_id`s) + send is needed — **no re-scan**, the 45-min throttle only gates re-runs.
