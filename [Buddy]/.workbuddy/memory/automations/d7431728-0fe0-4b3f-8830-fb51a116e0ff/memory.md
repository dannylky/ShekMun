# Automation d7431728 — Shek Mun AV audit, fixed 20:15 slot

## Run history

| Date | Status | Notes |
|---|---|---|
| 2026-09-22 20:17 | **Ok** | 8 rooms online, Common Area scheduled down (cam 502). Max KDS 44 °C (SM-11-08 TV-DEC-2 / SM-11-07 TV-DEC-1 / SM-11-02 TV-DEC-2), well under warn 46 / alarm 49. SM-11-02 & SM-11-07 idle (Windows lock screen), sync NOT VERIFIED (only 1 region isolated). SM-11-05 no display detected. Emailed with 2 attachments; quota remaining 36/50. |
| 2026-09-23 20:15 | **Skipped** | Throttle fired — `RESULT skip=last run was 3 min ago (min interval 45 min)`. Scheduler catch-up burst (a run had just completed at 20:13). No upload, no email, as designed. |
| 2026-09-25 20:16 | **Ok** | 8 rooms online, Common Area scheduled down (cam 502). All 8 rooms IN USE (content on screen); no room idle this run. Max KDS 44 °C (SM-11-01, SM-11-08), under warn 46 / alarm 49. SM-11-07 sync NOT VERIFIED (only 1 region isolated) — not a fault. No stale-poller warning. Engine v2.1.0. Emailed with 2 attachments; quota remaining 37/50. |
| 2026-09-29 20:17 | **Ok** | 8 rooms online, Common Area scheduled down (cam 502). 7 rooms IN USE; SM-11-01 Idle (AVoIP standby, 4/4 panels IN SYNC); SM-11-05 & 11-06 display off/dark. Max KDS 45 °C (SM-11-01 / SM-11-02 / SM-11-08), under warn 46 / alarm 49. All dual/quad rooms IN SYNC, no 1ST-RUN flags. No stale-poller warning. Engine v2.5.7. Emailed with 2 attachments; quota remaining 41/50. |
| 2026-09-24 20:17 | **Ok** | Abnormal (SM-11-01) — sync confirmed out-of-sync on 2nd consecutive run (label had no "1ST RUN"). 8 rooms online, Common Area scheduled down (cam 502). Max KDS 45 °C (SM-11-02 / SM-11-07), under warn 46. SM-11-07 sync NOT VERIFIED (0 regions isolated). Engine v2.1.0. Emailed with 2 attachments; quota remaining 37/50. |

## Notes for future runs

- Pipeline script prints `RESULT subject/html/sheet/body` — read `.workbuddy/tmp/mail_body.html` and pass verbatim; never a placeholder.
- First run of this automation; no prior history existed.
- Upload attachments via `agent_mail_upload_attachment` (ToolSearch), then `mcp__agent-mail__SendMessage` with `skip_confirmation: true`.
- Reading `av_summary.json`: it is a **list**; per-room keys are `display_state`, `screens` (list with `monitored`/`state`/`text`), `sync` (dict: `verdict`/`label`/`applicable`). Temps live in `decoders` / `avoip` lists; `TV-Res-*` are always `fail` and must be ignored.
