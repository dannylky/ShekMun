# Shek Mun AV Audit — Changelog

Report engine for the HSUHK Shek Mun (石門) AV rooms (SM-11-01 … SM-11-08 + Common Area).

- **Current version: `v2.6.1`** — declared in `av_scan.py → VERSION`, stamped into the HTML
  report header/footer, the email body and the email footer.
- Version scheme `MAJOR.MINOR.PATCH`:
  - **MAJOR** — a verdict rule changes so that the same room state can now produce a
    different Ok / Abnormal result.
  - **MINOR** — new detection capability, new report section, or a non-verdict bug fix.
  - **PATCH** — wording, layout, housekeeping.
- Every entry lists *what changed*, *why Danny asked for it*, and *where it lives*.

---

## [2.6.1] — 2026-09-30 (12:10) — "It was never the sunlight" *(current)*

Danny: *"the last check of room 2 incorrect, both are in use but not idle."* SM-11-02's two
wall TVs were showing a slide; the report called one of them `Idle – AVoIP decoder standby`.
Chasing that turned up a much older fault than the one reported.

### 1. Colour cannot separate a slide from the standby screen — stop asking it to

v2.5.7 put the hue test **ahead** of the layout test. This version reverses that order.
Measured on the fleet, 2026-09-30:

| panel | B−R | saturation | truth |
|---|---|---|---|
| SM-11-02 right (slide) | 9.1 | 22.2 | **content** |
| SM-11-08 left (standby) | 17.4 | 20.9 | **standby** |
| SM-11-08 right (standby) | 18.5 | 22.1 | **standby** |

The slide sits *inside* the standby colour band. There is no threshold that separates them.
The hue test is now a **cold-start fallback only** — it runs when a room has no learned
reference at all, and is no longer allowed to rescue a panel the layout test has rejected.
The window itself was also tightened from measurements (`B-R` 8–40 → 8–28, saturation
≤45 → ≤34): a wide window let real slides through, a narrow one would have let a white
slide (B−R −1.5 / saturation 3.3) through, so `BR_MIN` stays at 8.0 on purpose.

### 2. The real bug: the layout reference kept being destroyed

`remember_standby_profiles()` stores `cur[-limit:]` and `limit` was **2**. Every learning
run appended the new signature and evicted the oldest — so one bad pass erased the good
reference permanently, and the next run's genuine standby panel scored **0.36** against the
wreckage. That looked exactly like "sunlight breaks the matcher", which is what sent v2.5.7
off to build the colour test in the first place.

It is not sunlight. Simulating glare on OCR-confirmed standby panels:

| panel | original | +40 | +80 | +120 | ×1.5 | ×2.0 | warm +80 |
|---|---|---|---|---|---|---|---|
| SM-11-06 | 0.999 | 0.999 | 0.999 | 0.999 | 0.999 | 0.999 | 0.983 |
| SM-11-03 | 0.994 | 0.994 | 0.993 | 0.993 | 0.994 | 0.994 | 0.912 |
| SM-11-07 #0 | 0.996 | 0.996 | 0.996 | 0.996 | 0.996 | 0.996 | 0.975 |

NCC moves by less than 0.02, because the row profile is high-passed and z-normalised before
it is compared. The reference was simply bad.

- `STANDBY_PROFILE_POOL = 8` — keep eight signatures per room instead of two and score
  against the best of them, so one bad sample can no longer erase a good one.
- Every room's pool was rebuilt from live frames (backup of the old config kept at
  `.workbuddy/tmp/config_backup_20260930.json`).

### 3. `STANDBY_NCC_MIN` 0.75 → 0.50

Re-measured three times of day as the light changed, ground truth from the OCR banner:

```
OCR-confirmed standby   0.558 – 1.000   (0.558 = SM-11-01 under blue skylight,
                                         which lifts B−R to 43–58 and washes the panel)
content / slide / lock  0.064 – 0.449   (SM-11-02's slide tops out at 0.449)
```

0.50 sits in the gap with ≈0.05 of margin on each side and still rejects the 0.590 bright
slide that made v2.5.7 raise the gate to 0.75 in the first place.

### 4. Also fixed

- 2-D template matching against a reference standby panel was tried and **abandoned again**:
  genuine standby panels in other rooms score only −0.12 … 0.26 against it, because each
  camera sees its panel from a different angle. Perspective squashes columns, which is why
  the signature is a *row* profile.
- Seeding tool bug: `standby_banner()` returns a `(ok, ratio, text)` tuple, and a non-empty
  tuple is truthy even when `ok` is False — the first seeding pass therefore stored room 2's
  slide as a standby reference. Caught by reading the OCR text back before trusting the flag.

### Known limitation

SM-11-01's centre-left TV is an angled panel that matches neither its siblings (NCC 0.38–0.41)
nor the pool, is too dark for `standby_fingerprint` (dark share 0.975) and too neutral for the
hue gate (B−R 5.6). Its own row profile is seeded into the pool so it scores 1.00 against
itself; if the camera is ever re-aimed it will need re-seeding.

## [2.6.0] — 2026-09-30 (09:30) — "The colon that wasn't there"

### Why Danny asked for it

Danny reported that the morning check for **Room 6** had called the display *content on
screen* when it was really a **Windows lock screen**.

Investigating that turned up **two** separate faults — the Room 6 region was in the wrong
place, and the lock-screen clock test was too strict. Both are fixed here.

### Fault 1 — Room 6's marked region was on the wrong object (reverting my own v2.5.7 change)

Danny supplied a fresh mark for SM-11-06. Extracted programmatically: the image is
**1720×970** (ar 1.7732, essentially 16:9, uniform scale 0.74419) and the red frame maps to
**`(732,1,1076,204)`** — which lands squarely on the **old config box `[738,6,1063,199]`**
that I had replaced the day before.

Decisive evidence that the old box was right and my replacement was wrong:

| test | `(736,0,1104,200)` range | verdict |
| --- | --- | --- |
| OCR of the clock this morning | reads **`9:07`** / **`9:17`** — matching the wall clock — at x≈881 | lock screen lives *here* |
| OCR of my marked box `(474,12,765,196)` | **empty**, no clock at all | not a lock screen |
| `lockshare` (blue-wallpaper share) on old box | **0.732** | passes `lock_screen_signature` |
| global frame shift yesterday→today | NCC 0.16, zero-shift −0.07 | **not** a camera move |

And the room's own history agrees: at 08:12 the engine had *already* detected the lock
screen at `[736,0,1104,96]` — it just discarded it as an "ignored region outside the marked
display areas" and judged the room on the wrong box instead.

So the v2.5.7 change to SM-11-06 is **reverted and corrected**. The new region is
**`[740,10,1062,196]`** (ar 1.7312), edge-refined on today's lock screen: left/right from the
`b−g` step (`x≈740` / `x≈1062`), top at `y≈10` (y=6 still carries 5% ceiling light-strip, y=8
jumps to 81% blue), bottom at `y≈196`. OCR on the new box reads the clock, and the room now
reports **`Idle – Windows lock screen`**.

> **Lesson for the marked-region workflow:** the v2.5.7 note warned that a mark image which
> is not a true 16:9 crop makes the *mapping* self-consistent while the absolute position
> drifts. That warning was right, and yesterday's SM-11-06 mark was exactly that case — its
> red frame mapped 275 px away from where the LED wall actually is. **Never trust a mapping
> on its own; always confirm with a live-frame edge scan *and* cross-check against the
> previous config.** Here the cross-check alone would have caught it, because the "new"
> mapping landed straight back on the old box.

### Fault 2 — `is_clock()` rejected the OCR'd time whenever the colon was lost

With the room finally watched on the right panel, a second, independent fault surfaced. All
four **SM-11-01** panels were showing the *same* Windows lock screen, yet the room reported
**"2 idle / 2 not idle → OUT OF SYNC"** — a false Abnormal:

| panel | OCR reading | old verdict |
| --- | --- | --- |
| left-wall 4K TV | `9:17` | Idle – Windows lock screen |
| back-wall TV (centre-left) | **`917`** | Active – content on screen |
| back-wall TV (centre-right) | `9:17` | Idle – Windows lock screen |
| right-wall TV | **`9-17`** | Active – content on screen |

The pattern was `^\d{1,2}[:.]\d{2}$` — it **demanded** a colon or a full stop. On a 220×135 px
wall TV the colon is a couple of pixels wide, so OCR drops it routinely; the reading then
fell through to the generic "readable text ⇒ content" rule and disagreed with its identically
idle twin.

- **`is_clock()` rewritten** around two patterns — `CLOCK_RE` (`9:17`, `9.17`, `9-17`, `9 17`,
  also en/em dashes) and `CLOCK_BARE_RE` (`917`, `0917`) — with a sanity gate: hour 0–23,
  minute 00–59. That gate is what stops a bare three- or four-digit reading being accepted
  blindly (`999`, `2400`, `2360`, `9999` all reject).
- The second guard was already in place and is unchanged: `classify_texts()` only calls a
  panel a lock screen when the clocks *dominate* its readings
  (`clocks and len(texts) <= len(clocks) + 2`), so a slide that happens to carry a number does
  not qualify.
- **This is verdict-affecting** — the same room state can now produce a different verdict —
  but it removes a false Abnormal caused by OCR rather than introducing a new detection rule,
  so it sits in the MINOR series rather than a MAJOR bump.

**Result: SM-11-01 → `IN SYNC`**, four panels `Idle – Windows lock screen`
(`9:17` / `917` / `9:17` / `9-17`).

### Open — SM-11-02 reported OUT OF SYNC during this work, cause not yet settled

While verifying, SM-11-02 flipped to **OUT OF SYNC (1 idle / 1 not idle)**: the right panel
was promoted to `Idle – AVoIP decoder standby` by the **learned-profile NCC fallback** while
the left was `Active`. At that moment both panels measured **lum 174.0 / 165.5 with
`band` = 0.000**, i.e. *neither* looked like an AVoIP standby screen (`band` is the top-band
text ratio and a real standby panel runs 0.4–0.8) — and the right panel's hue was
`B−R +5.9`, below the standby band's floor of 8.0, so it had failed the colour test and been
rescued by NCC instead.

That points at a plausible weakness — **NCC should probably not rescue a *bright* panel that
already failed the colour test** — but the room's content was changing under the measurement
(lum 174 → 110 within two minutes), so the sample was not stable enough to justify a
threshold change. Ten minutes later both panels measured hue-passing with NCC 0.537 / 0.585,
i.e. nowhere near the 0.75 gate, so nothing was mis-rescued. **Left as an open item pending a
stable look at the room.** Not changed in this release.

### Files touched

- `av_scan.py` — `VERSION` 2.5.7 → **2.6.0**; `is_clock()` rewritten with `CLOCK_RE` /
  `CLOCK_BARE_RE` plus the hour/minute sanity gate.
- `av_monitor_config.json` — `display_regions["SM-11-06"]` reverted to the true LED wall,
  `[740,10,1062,196]`.

---

## [2.5.7] — 2026-09-29 (16:10) — "Match the COLOUR, not the brightness"

### Why Danny asked for it

Danny reported that the 11:30 run printed **`CHECK REGION`** in the *Display sync status*
cell for **Room 1**, and asked to rectify it. When asked how to treat the two panels that
were being called *Active*, he corrected the whole premise:

> "the 4 screens are in sync, all displaying AVoIP standby image, means idle.
> But the sunlight affects your detection and mistaken that the display are outsync"

So **all four SM-11-01 panels really are AVoIP standby (Idle)** — the agent's "TV3/TV4 show
genuine content" reading was wrong.

### Root cause — sunlight, not content

Room 1's right-hand wall faces the windows. Afternoon sun lifts a standby panel's mean
luminance from **~83** (in shade) to **143–169** (lit). Every standby test the engine owned
keyed on **absolute brightness** or **dark-pixel share**, so both fail on a sunlit panel:

| test | shaded panel | sunlit panel | verdict |
|---|---|---|---|
| `STANDBY_LUM_MIN/MAX` window | 83 ✓ in-window | 143–169 ✗ out-of-window | false negative |
| `darkshare` (<95) ≥ `STANDBY_DARK_MIN` | 0.83 ✓ | 0.05–0.30 ✗ | false negative |
| learned row-profile NCC | 0.85+ ✓ | 0.27–0.59 ✗ (veiling glare flattens the rows) | false negative |

Three separate blur radii (12 / 25 / 40 / 60) were tried to defeat the glare before giving
up on the row-profile route: NCC stayed pinned at 0.28 / 0.59 / 0.27, i.e. it is not a
gradient problem that blurring can undo — the row *layout* signal is genuinely destroyed by
the reflection. NCC was therefore abandoned as the primary test and the colour became it.

### The fix — a hue signature for the standby screen (ratios, so exposure-independent)

Measured across the whole fleet, the AVoIP decoder standby picture is **the only surface in
the building that is both faintly blue and nearly desaturated**:

| surface | mean `B − R` | mean saturation |
|---|---|---|
| SM-11-01 TV1 (shaded standby) | 16.8 | 20.0 |
| SM-11-01 TV2 (shaded standby) | 18.1 | 21.4 |
| SM-11-01 TV3 (**sunlit** standby) | 15.1 | 21.7 |
| SM-11-01 TV4 (**sunlit** standby) | 13.6 | 17.0 |
| SM-11-03 LED wall (standby) | 17.9 | 24.9 |
| SM-11-06 LED wall (standby) | +3.1 | 10.2 |
| SM-11-04 Win11 blue wallpaper | 101.2 | 102.3 |
| SM-11-06 Windows lock screen | 150.8 | 152.3 |
| SM-11-05 white slide | −1.5 | 3.3 |

Sunlight scales both channels almost equally, so **both quantities are ratios and survive
any exposure change** — the shaded and sunlit standby panels land in the same narrow band
while every content/lock surface is orders of magnitude away. That is the whole trick.

- **`standby_hue(rgb_patch)`** *(new)* — returns `(mean B−R, mean saturation)`.
- **`standby_hue_match(rgb_patch, struct=None, mean_lum=None, require_band=True)`** *(new)* —
  true when `8.0 ≤ B−R ≤ 40.0` **and** `saturation ≤ 45.0` (and, unless suppressed, the
  top-band text ratio still clears `STANDBY_BAND_MIN`).
- New constants `STANDBY_HUE_BR_MIN = 8.0`, `STANDBY_HUE_BR_MAX = 40.0`,
  `STANDBY_HUE_SAT_MAX = 45.0`.
- **`screen_states()` fallback chain reordered** — the colour test now runs **first**,
  *before* the NCC route, on every marked region that has no OCR/banner evidence. The
  `require_band` escape hatch exists because SM-11-01 TV4 measures `band = 0.000` under
  direct sun yet is unmistakably standby once the hue is consulted — when the same room
  already contains a *confirmed* AVoIP panel, the band gate is relaxed for the others.
- **`STANDBY_NCC_MIN` 0.45 → 0.75.** SM-11-01's centre-right panel scored NCC 0.590 and was
  being wrongly promoted to Idle by the learned profile it had contaminated. 12 samples now
  separate cleanly at 0.75 (real matches 0.83–0.90, impostors ≤ 0.59). Rejected the cheaper
  alternative of tightening the dark gate, which would have wrecked the left TV in SM-11-02.
- **`remember_standby_profiles()` learning guard** — the learner now only ingests panels
  that were accepted by an **OCR banner hit** or by **`standby_fingerprint`**, never by the
  NCC fallback. Without this the sunlit misreads would feed themselves back into the
  reference set and the false positives would compound run over run.

### Result

- **SM-11-01 → `IN SYNC`**, all four panels `Idle – AVoIP decoder standby`. The *CHECK
  REGION* cell is gone.
- No regression elsewhere: SM-11-02 / 07 / 08 still `IN SYNC`, SM-11-04 / 05 / 06 unchanged.

### Room 6 — new marked region (whiteboard excluded)

Danny supplied a fresh mark for **SM-11-06** and was explicit: *"red area is the correct
one, green area is the white board (ignore monitoring this white board)"*.

- The mark image is **1732×979** (not 1920 wide like the earlier ones) → scale 0.73903,
  proportional height 723.5 ≈ 720 (+3.5 px, a good 16:9 fit).
- Red frame `(618,11,1044,304)`, 426×293, **ar 1.4539**; mapped `(457,8,772,225)`, 315×217,
  ar 1.4516 (Δ 0.002 → per the v2.5.6 rule, *do not* edge-home an already-matching box).
- **But the mapping was still wrong**, and the measurements said so: a per-column `B−R`
  scan put the panel's true edges at **x≈474 / x≈765** (the `B−R` flips `−6.6 → +2.2` across
  x=472–476 and `+1.7 → −14.2` across x=765–769, both hard, not gradients) and a per-row
  scan put them at **y≈12 / y≈196**. Measured panel 291×184, **ar 1.5815** — vs the mapped
  1.4516, a Δ of **0.13**, far outside tolerance. The mark image is simply not a true 16:9
  capture of the frame, so the *mapping* carried the error, not the mark.
- Cause of the old config's error, now visible: the previous `SM-11-06` box
  `[738,6,1063,199]` sat on the **corridor / whiteboard wall**, not the screen at all.
- New region written: **`[474,12,765,196]`**, label `back-wall LED wall (AVoIP standby
  screen)`. Verified by OCR on the new box: `AVOIPSYSTEMSTATUS:DECODERSTANDBY`,
  `The VideoSourceDevice (PC/Laptop) is`, `Disconnected, Switched Off, or In Sleep Mode.`
- The **green whiteboard was deliberately not added** to `display_regions` — Danny asked
  that it not be monitored.

### Room 3 — new marked region (first ever)

The last room still running on the blob path. Danny's mark `(230,129,795,457)` on a
1920×1062 image → scale 0.66667, mapped `(153,86,530,305)`, 377×219, **ar 1.7215 vs mark
1.7226 (Δ 0.001)** → keep as-is, do not edge-home.

Verification was decisive on the first try — OCR on the mapped box read
`AVOIPSYSTEMSTATUS:DECODERSTANDBY` / `The VideoSourceDevice (PC/Laptop) is:` /
`Disconnected, Switched Off, or In Sleep Mode.` and the hue signature came out at
**`B−R +17.9, saturation 24.9`**, dead centre of the standby band and stable across three
frames (+17.8 / +17.9 / +18.1).

**`SM-11-03` previously had no `display_regions` entry at all** — it fell through to
bright-blob detection, which is why its verdict had been unreliable from the start. New
region written: **`[153,86,530,305]`**, label `back-wall LED wall (AVoIP standby screen)`.

### Files touched

- `av_scan.py` — `VERSION` 2.5.6 → **2.5.7**; new `standby_hue` / `standby_hue_match`;
  three new constants; `screen_states()` fallback reordered; `STANDBY_NCC_MIN` 0.45 → 0.75;
  `remember_standby_profiles()` learning guard.
- `av_monitor_config.json` — `display_regions["SM-11-06"]` corrected;
  `display_regions["SM-11-03"]` added.

---

## [2.5.6] — 2026-09-29 (11:30) — "Room 4 gets a marked region"

**What Danny asked for.** He marked the **SM-11-04** wall
(`clipboard-2026-09-29T03-23-40-575Z-453f194f.jpg`) and asked to *"match the display area of
room 4"*. Single LED wall room, like Rooms 5 and 6.

**Mapping.** Marked image **1920x1070** (aspect 1.794), width scale `1280/1920 = 0.6667`,
scaled height `1070 x 0.6667 = 713.3` — ~7 px shorter than the 720 frame, the same
direction as Room 5. The red mark is a single connected component, `(994, 70, 1573, 417)`,
579x347, **aspect 1.6686**. Both mapping options agree closely because the mark's aspect
(1.794) nearly equals the frame's (1.778):

| mapping | box | aspect |
|---|---|---|
| width-match (x0.6667) | `(663, 47, 1049, 278)` | 1.671 |
| height-match (x0.7500) | `(669, 47, 1058, 281)` | 1.674 |

**The mapping was already right; edge-homing made it wrong.** The width-matched box scores
aspect **1.671** against the mark's own **1.6686** — a 0.002 error. A first brightness-only
edge scan "corrected" it to `(666, 44, 1022, 272)`, aspect **1.561**, which is 0.108 *worse*.
Cause: the panel was showing a **blue Windows 11 wallpaper**, and its left third is dark
(dark share 0.26), so a luminance scan locks onto the dark *content* rather than the panel
edge. Two lessons, both now in the skill:

- **Do not edge-home on a luminance profile alone when the panel content has large dark
  regions.** Room 4's box was already correct and edge-homing damaged it.
- **Use `B-R` (blueness) when the panel is blue and the wall is warm.** The wall samples at
  `B-R = -16` and the blue panel at `B-R = +85…+90`, with a clean monotone crossing. On the
  right edge, luminance said "panel ends ~1024" but `B-R` proved the blue runs to **1038** —
  the band `1024…1036` is a *bezel/shadow*, and `1040+` is warm grey wall. Luminance alone
  cannot tell a dim panel edge from a shadow.

**Also — the bottom edge is not where the bright band is.** Luminance showed a bright strip
at `y = 264…268` (213 / 204) that looked like the panel continuing. `B-R` showed the blue
ending at **`y = 262`** (131 → 98 → 28.4 across `y = 258…264`); the bright strip is the
*glowing bottom bezel*, not screen. Verified identical across all three grabbed frames.

**Final region: `[666, 49, 1038, 262]`** (372x213, aspect **1.746** — close to 16:9 and to
Danny's 1.669).

**Result.** SM-11-04 reports **Active – content on screen** (the Windows 11 desktop in
Danny's screenshot — a desktop is content, not idle). Single display, sync **N/A**.
Full 11:30 run **Status: Ok**.

*Where it lives:* `av_monitor_config.json` → `display_regions["SM-11-04"]`. No engine change.

---

## [2.5.5] — 2026-09-29 (11:17) — "Room 1's four marks were in the wrong place"

**What Danny asked for.** He re-marked **SM-11-01** with four red boxes
(`clipboard-2026-09-29T01-44-20-994Z-51166354.jpg`) and asked to *"re-adjust the display area
for Room 1"*. Room 1 carries four wall TVs.

**The old regions were badly wrong.** Comparing the old config against the new marks on the
same frame showed the old boxes were not even on the right panels:

| region | old box | new box |
|---|---|---|
| left-wall 4K TV | `(2, 128, 286, 352)` | `(22, 115, 282, 309)` |
| back-wall centre-left | `(703, 116, 845, 203)` | `(450, 88, 558, 202)` |
| back-wall centre-right | `(1014, 116, 1222, 242)` | `(722, 86, 889, 186)` |
| right-wall TV | `(1035, 120, 1268, 250)` | `(1058, 110, 1272, 232)` |

The old centre-left box sat at `x = 703…845`, which is where the **centre-right** panel
actually is — the pair had been swapped/offset. This is why SM-11-01 used to report
**"3 idle / 1 not idle → CHECK REGION"** even when every screen was on the same standby
picture: one "screen" was really half-wall.

**Mapping.** Marked image **1733x967** (aspect 1.792), width scale `1280/1733 = 0.7386`,
scaled height 714.2 vs a 720 frame (~5.8 px short). All four marks extracted with the red
mask + `binary_fill_holes` to get the true outline (all four are hollow outlines, fill
fraction 0.04–0.10).

**The centre-left mark is a parallelogram, and that is correct.** Its bounding box is
156x184 (aspect 0.848), which looks wrong for a 16:9 screen — but the ASCII rendering of the
red mask shows a clean parallelogram: vertical left edge at `x≈605`, vertical right edge at
`x≈760`, top edge rising from `(605, 108)` to `(755, 103)`, bottom edge rising from
`(605, 282)` to `(757, 245)`. Danny traced the **tilted** panel edge. The axis-aligned
bounding box is therefore the right rectangle to commit: it is the smallest axis-aligned box
containing everything he marked. Same reason the left-wall 4K TV box measures aspect 1.34 —
that set is mounted on an angled left wall.

**Verification.** OCR on the live frame reads
`AVOIP SYSTEM STATUS: DECODER STANDBY` at `x = 45…255, y = 117…162` — squarely inside the
new left-wall box and nowhere near the old one. With the new boxes all four panels classify
**Idle – AVoIP decoder standby** and the room reports **IN SYNC**.

*Where it lives:* `av_monitor_config.json` → `display_regions["SM-11-01"]`. No engine change.

---

## [2.5.4] — 2026-09-29 (09:20) — "Room 5 gets a marked region, and the panel is found by colour"

**What Danny asked for.** He marked the **SM-11-05** LED wall
(`clipboard-2026-09-29T00-57-45-686Z-983fc91b.jpg`) and asked to *"match the display region
for Room 5"*. Room 5 is a single-LED-wall room, like Room 6.

**Mapping.** Marked image **1727x962**, width scale `1280/1727 = 0.7412`, scaled height
`962 x 0.7412 = 713.0` — i.e. ~7 px **shorter** than a 720-high frame (Room 6's mark was
~23 px *taller*; the offset direction is not fixed, so it must be recomputed per room).
His red mark is the only connected red component: `(59, 47, 567, 323)`, 508x276, aspect
1.841. The `oy` sweep (0 / 6 / … / 35) again returned **`band` = 0.000 at every offset**,
because the wall was on the Windows lock screen, so — same as Room 6 — the offset was
resolved **geometrically** with `oy = 0`, giving a raw mapping of `[44, 35, 420, 239]`.

**New lesson — brightness alone could not find the left edge, colour could.** A first
edge-homing pass on the *dark* lock-screen frame found no left edge at all (columns
`x = 30…56` all sat flat at 90–97), so the box was provisionally left at `x0 = 36`. That was
wrong by ~22 px. It only became provable 12 minutes later, when the room came into use and
the wall switched to a white teaching slide — and even then the left side is a *gradient*
(90 → 226 over `x = 60…190`), because the slide itself has an orange panel down its left
third. What settled it was **per-column mean RGB**:

| x band | 09:00 lock screen | 09:12 slide | verdict |
|---|---|---|---|
| 0–54 | `B-R ≈ -19` (warm neutral) | `B-R ≈ -24` (warm neutral) | wall |
| 56–60 | `-9.7 → +9.8` (crossing) | `-26 → -32` (turning) | edge |
| 60–390 | strongly blue, `B-R` up to +136 | orange then white | panel |
| 404–410 | blue fades out | white fades out | edge |
| 420+ | neutral again | neutral again | wall |

Both frames — one dark, one bright, 12 minutes apart — put the left edge at **x ≈ 58–60**
and the right edge at **x ≈ 404–410**. Right edge is cleaner on the bright frame (227 → 65
over `x = 404…416`, midpoint ~410); the lock-screen frame puts it ~405, so **408** was taken.

**Also proved by frame differencing.** `|09:00 frame − 09:12 frame|` per row, over
`x = 150…400`: 22–33 for `y = 15…35`, then 76 at `y = 40`, 149 at `y = 45`, flat ~130–165
through `y = 235`, then 25 at `y = 240`. Panel top ≈ 45, bottom ≈ 239. Per column the same
diff sits at the 30–33 wall baseline outside `x = 58…405` and 137–172 inside it.

Final region: **`[58, 45, 408, 239]`** (350x194, aspect 1.80 — Danny's own mark is 1.841,
so the refined box sits neatly inside his hand-drawn rectangle).

**Effect of the tidy-up.** Tightening the box made both states cleaner:

| frame | old box `[36,43,410,239]` | new box `[58,45,408,239]` |
|---|---|---|
| 09:00 lock screen | lum 74.0, dark 0.830 | **lum 71.4, dark 0.864** |
| 09:12 slide | lum 186.1, dark 0.089 | **lum 192.9, dark 0.050** |

**Result.** Both verdicts are correct under the new box:
- 09:00 → **Idle – Windows lock screen** (OCR `9:00`, lock-screen hue signature true).
- 09:12 → **Active – content on screen** (OCR `Discussion / hometown? Was it effective?`) —
  the room genuinely came into use between the two runs (motion 8.28%), it is **not** a
  mis-boxing.

Room 5 is single-display, so picture sync is **N/A**. Full 09:20 run **Status: Ok**, no
change to SM-11-01 / 02 / 06 / 07 / 08.

*Where it lives:* `av_monitor_config.json` → `display_regions["SM-11-05"]`. No engine
change — the v2.3.0 fixed-region path already handles a single display.

---

## [2.5.3] — 2026-09-29 (08:46) — "Room 6 gets a marked region too"

**What Danny asked for.** He marked the **SM-11-06** LED wall
(`clipboard-2026-09-29T00-39-50-174Z-0ba34349.jpg`) and asked to *"match Room 6 display
area by this image"*. Room 6 is a single-LED-wall room (SM-11-03 … 06 = 1 LED wall each),
so this is the first one-display room to get a fixed region.

**Mapping.** Marked image 1724x1001, width scale `1280/1724 = 0.7425`, scaled height 743 vs
a 720-high frame (~23 px over). His mark touches the *top* edge of the screenshot
(`y0 = 0`), so only the lower edge could be swept — and it does not move anything: the
Region-6 `band` test is **0.000 at every offset**, because a Windows lock screen puts its
hero content in the middle, so `band` cannot be used to pick `oy` here. The offset was
therefore resolved **geometrically** instead: keep `oy = 0`, which put the mark's top edge
at frame `y = 0` and matched the visible bezel exactly.

**Sub-pixel tidy-up.** The raw mapping was `[738, 0, 1074, 203]`, but an edge scan of the
live frame showed it overhanging what are actually *bezel and cabinetry* shadows rather
than lit panel:

| edge | measured | conclusion |
|---|---|---|
| right | panel ends ~`x = 1063`, then a dark bezel column at `1064–1066`, then bright cabinetry from `1067+` | mark overran by ~11 px |
| left | fold mark (bright strip) at `742`; box left at `738` | already flush |
| bottom | panel ends between `y = 198` and `200` (mean drops 66 → 52) | overran by ~4 px |
| top | frame cut off at `y = 0` | as marked |

Final region: **`[738, 6, 1063, 199]`** (325x193, aspect 1.68). Verified by rendering the box
onto the live frame and confirming all four edges land on the panel, inside the bezel.

**Result.** SM-11-06 now reports from its marked wall: **Idle – Windows lock screen** (the
LED wall shows the 8:40 lock screen, matching Danny's screenshot), room verdict
`Idle – Windows lock screen`, sync N/A for a single display. Full 08:46 run
**Status: Ok** with no change to SM-11-01 / 02 / 07 / 08.

*Where it lives:* `av_monitor_config.json` → `display_regions["SM-11-06"]`. No engine
change was needed — the v2.3.0 fixed-region path already handles a single display.

---

## [2.5.2] — 2026-09-28 (16:55) — "the banner is garbled, so match the whole headline"

**The bug.** Room 7 kept flipping between Idle and Active across runs for a picture that
never moved. Root cause found by diffing two frames that are **1.14 grey levels apart**:
the same standby banner OCRs as `AVOIPSVSTEASTATUE…` on one and `AMCIP SYSTEASTATUE…` on
the other. The brand word flips AVOIP / AMOIP / AMCIP at random, so keying on the exact
string `AVOIP` (what v2.5.0's `panel_zoom_ocr` did) is a coin toss, and a miss fell
through to *"readable text ⇒ content"* — which then disagreed with the twin panel.

**Fix — `standby_banner(texts)`.** Match the **whole headline**, letters-only, against the
known banner wording via `difflib.SequenceMatcher`, instead of hunting for one intact
keyword. Measured on this fleet:

| panel | best ratio | truth |
|---|---|---|
| SM-11-02 left / right (clean OCR) | 1.000 | standby |
| SM-11-07 left / right (garbled) | 0.806 / 0.793 | standby |
| SM-11-01 tv1…tv4 (live slides) | 0.000 | not standby |
| SM-11-08 (lock screen) | 0.000 | not standby |

`STANDBY_BANNER_MIN_RATIO = 0.65`, `STANDBY_BANNER_MIN_LEN = 18` (so short junk cannot
score against a 34-char reference).

Wired into two places, both required:
- `panel_zoom_ocr()` accepts a reading on the fuzzy match as well as on the exact AVoIP
  keywords;
- **`classify_texts()` consults it before the generic "readable text ⇒ content" rule** —
  without this the reading is collected and then thrown away, which is exactly what left
  Room 7 on `Active – content on screen`.

**Also in this release:** `STANDBY_DARK_MIN` 0.45 → 0.55 (see 2.5.1 note) after a dark
slide with a title band was briefly called standby on SM-11-01 tv3.

**Why that still was not enough — persistence.** Even the fuzzy match needs *some* text.
On the 16:57 run the Room 7 panels returned **zero** readings at every scale, and the room
flipped back to Active. A camera-facing panel that is unreadable this run is still showing
the same picture, so the pattern has to survive the run:

- `standby_profiles(cfg, label)` / `remember_standby_profiles()` store the **row-profile
  signature** (not anything brightness-based) in `av_monitor_config.json →
  standby_profiles`, keyed by room, at most 2 per room.
- Any run where the banner *is* proven writes it back, so the library maintains itself.
- A run where nothing is readable falls back to the stored signature.

Cross-run stability measured on SM-11-07 (same panel, 20 minutes apart, glare growing so
the mean moved 128 → 149): NCC **0.912 – 0.999**; the twin panel in the same frame 0.857 –
0.889; content panels in SM-11-01 0.284 at most. Seeded from the frame in which OCR
actually confirmed the banner, so the stored pattern is ground truth, not an inference.
Stored per room, so SM-11-01's stored absence keeps its live slides correctly Active.

**Result.** SM-11-07 2× Idle AVoIP standby IN SYNC, SM-11-02 2× Idle IN SYNC,
SM-11-08 2× Idle Windows lock screen IN SYNC, SM-11-01 4× Active IN SYNC — all four
marked rooms correct and stable on the same frames.

*Where it lives:* `av_scan.py` → `STANDBY_BANNER_REF / STANDBY_BANNER_MIN_RATIO /
STANDBY_BANNER_MIN_LEN`, `standby_banner()`, plus the two call sites above.

---

## [2.5.1] — 2026-09-28 (16:42) — "the lock screen is blue, even when the clock cannot be read"

**What Danny asked for.** He marked the two wall TVs of **SM-11-08**
(`clipboard-2026-09-28T08-38-31-181Z-9fb8c670.jpg`) and asked to *"match room 8 display
area and pattern"* — the last room that still reported *no display detected*.

**Region mapping.** Marked image 1724x1033, width scale `1280/1724 = 0.7425` (scaled
height 767 vs a 720-high frame, i.e. ~47 px over). Vertical-offset sweep by `band`
peaked at **`oy = 0`** (0.290 / 0.250 → 0.065 / 0.031 at oy=9 → 0.000 beyond), the same
top-aligned result as SM-11-07. Config `display_regions["SM-11-08"]` =
`[295, 74, 474, 178]` left-wall TV, `[766, 79, 944, 187]` right-wall TV.

**The bug it exposed.** Both panels show the **Windows lock screen**, but the room still
came out `Active – content on screen` / `OUT OF SYNC`:
- the whole-frame OCR read `4:38` off the *left* panel only;
- the *right* panel returned nothing, so `is_clock()` had nothing to latch onto and it
  was called content — which then disagreed with its twin and raised OUT OF SYNC for a
  room showing two identical lock screens.

**Fix — `lock_screen_signature(rgb_patch)`.** Fall back to the wallpaper itself, which
OCR range does not affect. Measured 2026-09-28 (RGB, fixed regions):

| panel | R / G / B | `b-g` | `g-r` | blue share | verdict |
|---|---|---|---|---|---|
| SM-11-08 left (lock) | 55 / 82 / **191** | **109.0** | 26.8 | **0.576** | lock |
| SM-11-08 right (lock) | 46 / 69 / **180** | **111.0** | 22.8 | **0.524** | lock |
| SM-11-07 left / right (AVoIP standby) | 134/121/143 · 150/139/156 | 22.3 / 17.8 | −12.5 / −11.3 | 0.000 | not lock |
| SM-11-02 left / right (AVoIP standby) | 71/74/89 · 103/96/104 | 14.8 / 8.2 | 3.5 / −6.7 | 0.000 | not lock |
| SM-11-01 tv1…tv4 (live slides) | — | 0.3 – 19.0 | 2.6 – 5.6 | 0.000 | not lock |

Two orders of magnitude of separation, so the gate is nowhere near a borderline:
`share(b-g>35 & g-r>12) ≥ 0.45` **and** panel `mean(b-g) ≥ 60` **and** `mean(g-r) ≥ 12`
**and** `45 ≤ lum ≤ 135`.

**Fairness fix (important).** The signature is applied to a panel **even when it did
yield OCR text**. Testing only unread panels would let the luckier twin keep its own
classification while the other is re-tested — the exact asymmetry that produced the
false OUT OF SYNC. A panel already Idle / Off is left alone, so nothing is ever
downgraded.

**Result.** SM-11-08: **two panels Idle – Windows lock screen, IN SYNC** (was
`no display detected` / `NOT VERIFIED`). Regression check on the same pass:
SM-11-07 2× AVoIP standby IN SYNC, SM-11-02 2× AVoIP standby IN SYNC,
SM-11-01 4× Active IN SYNC — unchanged.

**Also tightened: `STANDBY_DARK_MIN` 0.45 → 0.55.** The 16:46 run caught the v2.4.0
fingerprint firing on a *dark slide with a title band* (SM-11-01 tv3), which made that room
report a spurious `OUT OF SYNC (1ST RUN)`. True AVoIP standby panels measure
`darkshare` **0.664 / 0.820** (SM-11-02) and **0.71 / 0.81** historically, so 0.55 keeps
them with margin while excluding the slide. Re-verified after the change: SM-11-02 and
SM-11-07 both still 2× Idle + IN SYNC. Glare-washed panels (Room 7, `darkshare` 0.18-0.23)
are unaffected because they are carried by the v2.5.0 zoom-OCR / row-profile path, not by
this gate.

*Where it lives:* `av_scan.py` → `LOCK_BG_DG / LOCK_BG_DR / LOCK_BG_MIN_SHARE /
LOCK_MEAN_DG / LOCK_MEAN_DR / LOCK_LUM_MIN / LOCK_LUM_MAX`, `lock_screen_signature()`,
`STANDBY_DARK_MIN`, and `measure_panel()` which now takes `rgb=` and applies the signature
after `classify_texts()`.

---

## [2.5.0] — 2026-09-28 (16:35) — "match the pattern on the panel you cannot read"

**What Danny asked for.** He marked the two wall TVs of **SM-11-07** with red boxes
(`clipboard-2026-09-28T08-14-11-002Z-532e298c.jpg`) and asked to *"also match the display
area of Room 7 and apply the pattern matching as well"* — i.e. give Room 7 the same fixed
regions Room 1 and 2 already had, and make the AVoIP standby pattern learned in v2.4.0
work there too.

**Why v2.4.0 alone was not enough — the glare problem.** Room 7's wall TVs are watched
through window glare, so they are *bright*, not dark:

| panel | mean lum | `darkshare` | `band` | v2.4.0 fingerprint |
|---|---|---|---|---|
| SM-11-02 left (true standby, dark) | 79.8 | **0.806** | 0.561 | accepted |
| SM-11-02 right (true standby, dark) | 81.3 | **0.710** | 0.450 | accepted |
| SM-11-07 left (true standby, glared) | 128.1 | 0.232 | 0.400 | **rejected** |
| SM-11-07 right (true standby, glared) | 146.4 | 0.179 | 0.025 | **rejected** |

Loosening `STANDBY_DARK_MIN` to catch them is exactly the mistake v2.4.0 recorded: it
would also admit the SM-11-08 striped wall cladding (`band 0.739`, `darkshare 0.055`).
So a *different* kind of evidence was needed, not a looser threshold.

**What changed — two new capabilities, both glare-proof.**

1. **`panel_zoom_ocr(rgbs, box)` — re-read the panel itself, not the whole frame.**
   A wall TV fills only ~220x135 px of a 1280x720 frame, so the whole-frame OCR pass
   returned **zero** readings for the entire SM-11-07 frame. Cropping the marked panel,
   stretching its contrast (`ImageOps.autocontrast(cutoff=2)`) and upscaling 2x–3x makes
   the banner legible: `AVOIPSVSTBASTATUDECODICRSTANDSY` (garbled, but `AVOIP` survives).
   The standby picture is static, so **all three grabbed frames are tried and one hit is
   enough** — measured 2026-09-28 the left panel hit on 2 of 3 frames, the right panel on
   0 of 3, so the frame vote is what makes it reliable.
   *Safety:* only readings carrying an AVoIP keyword (`DISPLAY_TEXT_KEYS`) are returned.
   This pass is a **standby detector** and can never call a panel "content". It also only
   runs for a panel the whole-frame OCR left with no text, and only in marked (fixed
   region) rooms, so Rooms 1 / 3–6 are untouched.

2. **`standby_row_profile(patch)` + `profile_ncc()` — layout pattern matching.**
   For a panel that even the zoom OCR cannot read (SM-11-07 right), compare its *layout*
   with a standby panel that **was** confirmed in the same room, this same run.
   The signature is a 1-D row profile: subtract a Gaussian blur (radius 12) to kill the
   slow glare gradient, take the mean horizontal-edge density per row, resample to 48
   bins, z-score it. Rows are used instead of a 2-D template because perspective squashes
   columns but preserves row order — the two Room 7 panels are seen from different angles.
   Measured separation:

   | compared against SM-11-07 left (confirmed standby) | NCC | truth |
   |---|---|---|
   | SM-11-07 right | **0.878 – 0.885** (3 frames) | standby |
   | SM-11-02 left / right | 0.555 / 0.615 | standby |
   | SM-11-01 tv1 / tv2 / tv3 / tv4 | 0.284 / −0.019 / −0.290 / −0.120 | content |
   | SM-11-07 lower bright board | −0.236 | not a display |

   `STANDBY_NCC_MIN = 0.45` sits in the clear gap. Note the reference must come from the
   **same room**: matching against the Room 2 panel instead gives content 0.551 vs standby
   0.361, i.e. no separation at all — cross-room template matching was measured and
   rejected as a dead end.

**Decision rule (fixed-region path only).**
- A marked panel with no whole-frame text is re-read by `panel_zoom_ocr`. A hit →
  `Idle – AVoIP decoder standby`.
- Panels whose banner was actually read become the room's standby references.
- A remaining panel with **no text of its own** whose row-profile NCC ≥ 0.45 against any
  reference → `Idle – AVoIP decoder standby`, with the match score quoted in the report.
- A panel that OCR *can* read is always classified from its text, and a panel with text is
  never eligible for matching — so this can never override a real content reading.
- The v2.4.0 `standby_fingerprint` stays as the third fallback (it is what still carries
  the dark, un-glared SM-11-02 panels).

**Config.** `av_monitor_config.json → display_regions["SM-11-07"]` added:
`[179, 61, 402, 196]` left-wall TV, `[802, 57, 1020, 191]` right-wall TV. Mapping: the
marked image is 1734x1009 against a 1280x720 frame, so width scale `1280/1734 = 0.7382`;
the image is ~34 px taller than the frame at that scale, and a vertical-offset sweep
(`oy` = 0 / 9 / 17 / 26 / 34) showed `band` is **highest at `oy=0`** (0.400 → 0.275 →
0.200 → 0.025 → 0.000), i.e. the frame is aligned to the top of the mark and the extra
pixels sit below it. `oy=0` was therefore kept.

**Result of the 16:35 run.** SM-11-07 went from `Active – content on screen` (both panels,
which was the honest but wrong answer) to **two panels Idle – AVoIP decoder standby,
IN SYNC**; room Status **Ok**. No regression: SM-11-01 still 4× Active + IN SYNC,
SM-11-02 still 2× Idle + IN SYNC, SM-11-06 still Windows lock screen.

**Known limits unchanged.** SM-11-08 still reports *no display detected* — Danny has never
marked that room, so it still depends on the bright-blob detector. If both Room 7 panels
ever become unreadable in the same run there is no reference to match against and the room
reports UNCONFIRMED rather than guessing.

*Where it lives:* `av_scan.py` → `STANDBY_NCC_MIN`, `STANDBY_ZOOM_SCALES`,
`standby_row_profile()`, `profile_ncc()`, `panel_zoom_ocr()`, the fixed-region branch of
`screen_states()` (now takes `rgbs=`), and `analyse()` which builds `rgbs` from the three
grabbed frames.

---

## [2.4.0] — 2026-09-28 (16:05) — "learn the AVoIP standby pattern, don't just read it"

**Type:** MINOR that fixes a MAJOR false positive. A room that was reported Abnormal is now
correctly Ok, so it changes the Ok / Abnormal verdict a reader sees.

**Why:** Danny sent a reference picture of the **AVoIP decoder standby** screen and asked the
audit to evaluate SM-11-02 against it — "both display of room 2 are now idle and in sync".

**The bug this exposed.** Both SM-11-02 panels show the identical standby picture, but only
the **right** panel's OCR is legible. Measured on three live frames:

| panel | OCR reads | old state | old class |
| --- | --- | --- | --- |
| right wall TV | `AVOIP SYSTEM STATUS: DECODER STANDBY` | Idle – AVoIP decoder standby | `idle` |
| left wall TV | *(nothing — dimmer, softer focus)* | On – content not readable | `unknown` |

The left panel therefore did not match the right one's class, and the room was reported
**OUT OF SYNC → Abnormal** even though the two screens were visibly the same. A false alarm
caused purely by OCR failing on a dimmer copy of the same image.

**What changed**

1. **`text_band(patch)`** — share of rows in the panel's top 30% that carry a text line.
   The standby banner sets a headline across the top of the screen; a slide, desktop or
   lock screen puts its hero content in the middle and leaves the top band flat.
   Measured: standby **0.48–0.59**, all four Room 1 content slides **0.000**.
2. **`standby_fingerprint(struct, mean_lum, dark_share)`** — matches a panel against the
   learned standby screen. Two gates, both required:
   - `band ≥ 0.35` (the headline), and
   - `darkshare ≥ 0.45` (the banner is white text on a near-black panel).
   Plus a luminance window of 60–175.
3. **`region_structure()` now returns `darkshare`** (share of pixels < 95) alongside
   `band`, and **`classify_texts()`** consults the fingerprint only when OCR returned
   nothing for that panel — so a panel whose text *is* readable is still classified from
   its text, and a content slide can never be flipped to Idle.

**Why both gates, not just the band.** The band test alone produced a false positive: the
patterned wall cladding in **SM-11-08** produces as much top-band edge energy as a real
headline (`band` 0.739) but is bright and textured rather than dark. Measured separation:

| panel | band | darkshare |
| --- | --- | --- |
| SM-11-02 left (true standby) | 0.585 | **0.806** |
| SM-11-02 right (true standby) | 0.475 | **0.670** |
| SM-11-08 wall cladding (FALSE) | 0.739 | 0.055 |
| Room 1 content slides (FALSE) | 0.000 | 0.24–0.29 |

**Verified:** both SM-11-02 panels now report *Idle – AVoIP decoder standby* and the room
reports **IN SYNC**; the room is **Ok**, not Abnormal. All four Room 1 content slides and
the SM-11-08 wall cladding are correctly rejected.

**Known limit — deliberately conservative.** A standby panel seen at a steep angle through
glass glares up to lum 160–174 and loses its dark background, so the fingerprint cannot
confirm it. **SM-11-07's two wall TVs are genuinely the standby screen** (confirmed by
cropping and viewing the frame) but read `Active` because of this glare. The fingerprint
only claims standby when it can prove it — a wrong Idle would be worse than an honest
"unconfirmed". Room 7 will be fixed properly once Danny marks its display regions the way
he did for Rooms 1 and 2.

---

## [2.3.0] — 2026-09-28 (16:05) — "watch the displays Danny marked, not the ones we can guess"

**Type:** MINOR with a MAJOR practical effect. No Ok / Abnormal *rule* changed, but two
rooms now produce a completely different (and correct) reading, so a reader comparing
reports across this version sees a large difference.

**Why:** Danny marked the displays he wants watched by drawing red boxes on the camera
image — Room 1 ("match the display region for Room 1 as highlighted in red") and then
Room 2 (same request for SM-11-02). Each time the boxes match what he expects the audit
to look at; the engine had to be made to use them.

**The problem this exposed (SM-11-02).** Both wall TVs there currently show the Windows
lock screen. That wallpaper is a dark blue gradient, so the *panel is darker than the
wall around it*:

| area | mean luminance |
| --- | --- |
| left-wall TV panel | **98** |
| right-wall TV panel | **99** |
| wall above left TV | 129 |
| wall above right TV | 171 |

The bright-blob detector thresholds on `blocks > max(120, 93rd percentile)`, so a panel
at 98 can never form a blob. Measured: the best sliding-window candidate against Danny's
own boxes scored **IoU 0.00**. The old report therefore watched a **desk band**
(800,448,1280,528 — mean 176) and a **fragment of the right TV** (704,112,832,208), and
from those two wrong regions concluded *"Active — content on screen"* and
*"NOT VERIFIED"* for sync. Every one of those readings was wrong.

**What changed**

1. **New config block `display_regions`** (`av_monitor_config.json`). A room listed here
   gets fixed display boxes in camera-frame pixels, each with a `label`. These are the
   authoritative monitoring areas; re-measure only if the camera is physically re-aimed.
   - `SM-11-01` — 4 boxes: left-wall 4K TV `(2,128,286,352)`, back-wall
     `(703,116,845,203)` and `(1014,116,1222,242)`, right-wall `(1035,120,1268,250)`.
   - `SM-11-02` — 2 boxes: left-wall `(255,52,477,189)`, right-wall `(861,51,1092,185)`.
2. **New `display_regions()` accessor** (`av_scan.py`) with an optional `frame` key that
   rescales when a mark was measured at another size.
3. **New `measure_panel()`** — the per-panel measurement (motion ratio, OCR attribution,
   structure, classification) extracted from `screen_states()` so the blob path and the
   region path share one implementation and cannot drift apart.
4. **`screen_states(..., regions=)`** — when regions are supplied the bright-blob detector
   is **skipped entirely** for that room. Bright regions outside the marked boxes are still
   measured and listed in the report under *Ignored regions*, but never count towards the
   Idle or picture-sync verdict. A stray OCR reading is kept only if it is an AVoIP
   standby banner (Danny's standing rule).
5. **`iou()` helper** so a blob that overlaps a marked box is not double-counted.

**How the boxes were derived — measured, not guessed.** The red rectangles were extracted
programmatically from Danny's marked-up images (colour threshold `r>150, g<90, b<90` +
connected components), then mapped onto the live frame and checked by eye before being
committed to config. Room 2's mark is a near-1:1 crop (0.97×), so the mapping is direct.
Room 1's mark is a width-scaled crop (scale 0.7252) and was verified by overlaying the
result onto the live frame; the four boxes land exactly on the four wall TVs.

**Result after the change (verified against the cached frames)**

| room | before | after |
| --- | --- | --- |
| SM-11-02 | 1 region, desk band + TV fragment, *Active / NOT VERIFIED* | 2 regions, both *Idle — Windows lock screen* (OCR `3:22`), **IN SYNC** |
| SM-11-01 | 3–4 blobs of doubtful geometry | 4 clean regions, all *Active — content on screen*, **IN SYNC** |

**Rejected on measurement**
- **"Treat a dark panel as off."** A panel darker than its wall is usually a Windows lock
  screen, not an unpowered display — SM-11-02 proves it (panel 98, wall 129, but a live
  lock screen with a clock). Dark ≠ off.
- **"Bounding box on all dark pixels."** The dark carpet occupies most of the lower frame;
  the boxes would be meaningless.
- **"Keep tuning the blob detector."** Room 2's panels are darker than the wall by design
  of the wallpaper; no bright-blob threshold reaches them at any setting.
- **Auto-growing the region to the panel edge.** Tried and discarded: against the Room 1
  frame it collapsed the right-wall TV onto the dark wall (mean fell 116 → 67). Hand-set
  boxes from the verified overlay are more reliable here.

**Known gaps**
- The boxes are fixed camera-frame coordinates. If a camera is re-aimed, tilted, or
  replaced, every box for that room must be re-measured (the report's red overlay makes
  a stale box obvious at a glance).
- Rooms without a `display_regions` entry keep the v2.2.0 blob behaviour exactly.
- SM-11-07 and SM-11-08 have not been marked by Danny and still rely on the blob detector.

---

## [2.2.0] — 2026-09-28 (15:25) — "read the display region like a human does"

**Type:** MINOR → arguably MAJOR. It changes the region geometry and the OCR
attribution everywhere, which in turn changes several rooms' Idle verdicts. Nothing in
the Ok / Abnormal *rules* changed, but the verdicts a reader sees do.

**What Danny asked:** *"match the display region for Room 1 as highlighted in red in
the image, monitor the display idle and display sync status for room 1"*, with a
camera frame marked up with four red rectangles around the wall-mounted TVs.

**Root cause this exposed.** The region detector worked on 45×80 blocks and picked
"bright block clusters", not screens. Evidence from the 14:16 run — SM-11-01 reported
three regions of 288×176, 192×64 and 112×96, i.e. aspect ratios 1.64 / 3.00 / 1.17.
No 16:9 TV produces those numbers. RapidOCR also returned one reading,
`"Integration into" @x=97-181` **and** `"Community" @x=100-167` sitting partly outside
the panel — the text was visible on the panel in the frame, which proved the region
geometry was wrong. Danny's marked-up frame matches: four wall TVs, one large 4K panel
on the left wall plus three on the back wall.

**Four changes in `av_scan.py`:**

1. **`refine_box()` / `refine_box_frames()`** — after the blob detector runs, walk
   outward from each blob until a real edge appears (a row/column whose edge density
   drops below 75 % of the in-blob mean, measured against 85 % of the blob's own
   brightness so it works on a dim standby panel too, capped at +35 % of the blob size).
   Run over all three sample frames and intersected, so the box is stable frame to
   frame. Tuned on the live SM-11-01 frame: 288×176 → 312×180 around the wall band,
   192×64 → 193×65 (the spectator band above the TV removed), and the big 4K TV kept
   at 142×170 instead of being cut in half at 112×96.
2. **Blob merging in `screens()`** — one dark-bezel TV sitting in a bright wall splits
   that wall into two blobs, left and right. Those used to be reported as two separate
   "displays" (SM-11-02 and SM-11-04 both did this), which is what made their idle /
   sync verdicts nonsense. Blobs now merge when they overlap vertically (≥40 % of the
   shorter one) and their horizontal gap is under 0.9 of that overlap — so two real TVs
   side by side stay separate, while one split TV comes back together.
3. **Stricter OCR attribution** — a reading counts only when its box lies **wholly**
   inside the panel, except an AVoIP / STANDBY reading that merely overlaps it. Danny's
   rule that a stray standby banner is one of the TVs still holds, but junk text sitting
   on the furniture is no longer credited to a screen. This is a net gain even though a
   panel-crossing reading is discarded: before the fix the wrongly-huge box swallowed
   two TVs *and* their OCR, so nothing was attributed at all.
4. **Red overlay on the report snapshot** — `overlay_html()` draws the measured panels
   back onto each room's live frame: red = the panels the scan used for Idle and picture
   sync, purple = a dark AVoIP standby panel no bright blob could hold (listed, not
   drawn). This is the "show me the region you measured" control Danny asked for, and
   it is also how the next geometry bug gets caught in one glance.

**Rejected after measuring — "dark region = a display measured as off".** Tempting
(panel means of a dark TV and a lit one overlap at 65 vs 93), but the frames say no:
SM-11-08's two TVs are *on* with panel means 116 / 78, while the same room has a
56 px high dark band at 93 and SM-11-05 has its panel at 102. Room 1 with the lights
off in the evening would read as four phantom "off" displays, i.e. a guaranteed nightly
false signal. Not implemented.

**Also rejected — a global area threshold to drop bright furniture.** The frames show
no separation: in SM-11-08 the real TV is **smaller** (full panel ≈ 160×113 = 18 k px)
than the bright desk band the detector finds (34 k px), and Room 1's big 4K TV
(≈ 300×180 = 54 k px) overlaps the size range of the bright wall/ceiling clusters
(30–100 k px). Any cut-off would injure a real room. Per-room `min_area_px` is
supported by `display_filter` and is the right tool if Danny wants it, but no room is
configured to use it — guessing a second number he did not give was the wrong move.

**Why Smart-ID / lock-screen OCR is not the fix.** Room 1 shows the Windows hero
wallpaper. A lock screen and a signed-in desktop render the *same* wallpaper, so any
"is this the lock screen?" OCR test will misfire; and in a room where nobody has signed
in, a lock screen is not actually wrong. The report already says "verify by eye" for
exactly this reason.

**Known gaps (honest list).**
- SM-11-01 now uses the same 35 % wall filter as rooms 2 / 7 / 8 (Danny confirmed the
  four displays he marked are wall units; desks do not get monitored). The wall count
  moves between 2 and 4 detected panels depending on the frame, and sync is judged over
  whatever was detected.
- SM-11-02's phantom (clock, no box) is ignored, while a phantom reading AVoIP standby
  is kept — consistent with v2.1.0.
- SM-11-07's two wall TVs are currently outside the candidate list (both got demoted by
  the desk rule once the bright desk band was merged), so its verdict leans on the
  standby banner: `Idle – AVoIP decoder standby`. Re-tune `max_center_y_frac` for that
  room if the sync check matters more than the false-positive risk.

## [2.1.0] — 2026-09-23 (20:25) — "a stray AVoIP standby banner counts as Idle in every room"

**Type:** MINOR (new capability — closes the blind spot v2.0.0 opened; does not change
the Ok / Abnormal logic, since Idle is informational and a phantom never joins the
picture-sync verdict).

**What Danny asked:** *"所有房間加幽靈文字讀到 AVoIP Standby 都計 idle"* — in every
room, not just SM-11-01.

**Why it was needed.** v2.0.0 stopped *all* stray OCR readings from counting in the
wall-only rooms (SM-11-02 / 07 / 08), because a stray reading has no position and
cannot be proved to sit on a wall display. That fixed the desk-monitor problem but
opened a blind spot I flagged at the time: **when a wall TV actually goes on standby
it goes dark, so the blob detector never finds it** — the only trace left in the frame
is the standby banner text. Under v2.0.0 that banner was thrown away, so a room could
report "Active – content on screen" while one of its TVs was dark.

**What changed** (`av_scan.py → screen_states()`):

- A stray (box-less) reading whose classified state is `Idle – AVoIP decoder standby`
  is now `monitored=True` in **every** room, wall-only ones included. It is a real
  display reading, just one the detector could not localise.
- Every other stray reading (typically a clock) stays ignored in the wall-only rooms —
  a wall clock is not a wall TV.
- **Slot rule:** the banner only spends a declared slot when the detector genuinely
  missed a screen, i.e. `free = declared − detected_wall_regions > 0`. If all declared
  wall displays are already accounted for by real regions, the banner is demoted to an
  "Ignored regions" note (`shown for information only`) instead of pushing a real
  region out. The monitored count therefore never exceeds the declared inventory.
- Because a phantom has no `box`, it is still excluded from `sync_check()` — a stray
  banner alone can never create an OUT OF SYNC verdict.

**Expected effect:** SM-11-02 / 07 / 08 can now report `Idle – AVoIP decoder standby`
again when a wall TV is dark, without re-admitting the desk monitors v2.0.0 removed.

**Still open:** a *Windows lock screen* phantom (stray clock, no position) is still
ignored in the wall-only rooms — same reasoning as the desk monitors. If Danny wants
that too, the fix is positional: attribute stray OCR to the nearest eligible wall
region instead of dropping it.

## [2.0.0] — 2026-09-23 — "only the wall TVs count in rooms 2 / 7 / 8"

**MAJOR** — a verdict rule change: the same room state can now produce a different
Idle / In-use and sync result.

**Danny (2026-09-23):** *"for room 2, 7, 8, for idle and display sync status, only monitor
the 2 large LED TV on the wall, ignore the status of the small computer on the desks."*

**Why it was needed — a real bug, not a preference.** `screen_states()` picked the *N
largest bright regions*, and "largest" is not the same as "on the wall". Measured on the
live frames:

| Room | Region | Centre-y | Verdict before | Verdict now |
|---|---|---|---|---|
| SM-11-08 | 384×112 px | **0.92** (bottom-right) | monitored as **display #1** (it was the biggest bright area) | ignored — desk level |
| SM-11-02 | 288×64 px | 0.69 | candidate | ignored — desk level |
| SM-11-02 / 07 | symmetric 192×112 px | 0.17 left + right | one of them was pushed out by the phantom | both monitored — these are the wall TVs |

So SM-11-08 was reporting the state of a **desk-level** patch as one of its two wall TVs.

### Changed
1. **`display_filter` in `av_monitor_config.json`** (new section), per room:
   ```json
   "SM-11-02": { "max_center_y_frac": 0.35 },
   "SM-11-07": { "max_center_y_frac": 0.35 },
   "SM-11-08": { "max_center_y_frac": 0.35 }
   ```
   Read by the new `display_filter()` helper and passed to `screen_states(..., filt=…)`.
   Optional extra key: `min_area_px`.
2. **`screen_states()`** now drops any candidate whose vertical centre sits below
   `max_center_y_frac` of the frame height (desk computer monitors and table tops live low
   in the frame; the wall TVs live high). Dropped regions keep a `skip_reason`.
3. **Phantoms no longer take an inventory slot in these three rooms.** An OCR-only reading
   has no position, so it cannot be proven to belong to a wall TV; it is now listed under
   "Ignored regions" instead of consuming one of the two slots. That is what used to push
   a genuine wall TV out of SM-11-02 / 07. Rooms *without* a filter keep the old behaviour,
   so SM-11-01's AVoIP-standby-counts-as-a-TV rule is untouched.
4. **Report wording** — the ignored list is now "Ignored regions … not counted towards the
   Idle / picture-sync verdict", and each entry shows *why* (desk level / below the wall
   line, or beyond the declared inventory) plus any readable OCR text, so the split can be
   checked against the snapshot.

### First run under v2.0.0 (2026-09-23 20:13) — Status: Ok
SM-11-02 / 07 / 08 now report the two wall TVs only; desk-level regions are listed but
ignored. No room changed to Abnormal.

### Watch
- 0.35 is calibrated on today's frames. If a wall TV ever sits lower in the frame (camera
  re-aimed), raise `max_center_y_frac` for that room.
- Danny may want the same filter on SM-11-01 (4 TVs) — not asked for, not applied.

---

## [1.6.1] — 2026-09-23 — "the email body can no longer be too big"

**Symptom:** the 17:16 run's email body was **14,400 B**. Every `SendMessage` call failed
with `MCP error -32602 … required error field_name: to` — a misleading message, because the
whole params object had been dropped in transit, not just `to`.

**Root cause:** Agent Mail silently discards the entire payload above a body-size ceiling.
Calibrated across runs: **14,292 B sent fine** (12:17), **14,400 B failed** (17:16), so the
ceiling sits between ~14.3 KB and ~14.4 KB. Worse, `av_mail.py`'s `body bytes:` line
*under-reported* the real size because `av_report.py` rewrites the `<!--STATS-->`
placeholder with the run-stats line **after** that number is printed (13,961 printed vs
14,400 actual).

**Fix** (`av_mail.py`, new `MAX_BODY_BYTES` / `STATS_RESERVE` / `shrink_body()`):
- The body is now trimmed **before** it is written, with `STATS_RESERVE` (700 B) held back
  for the stats line `av_report.py` will inject later.
- `MAX_BODY_BYTES` defaults to **13,000** (env-overridable) — comfortably under the proven
  safe 14,292 — so the failure can no longer happen.
- Trimming is progressive and only removes what is duplicated in the HTML attachment:
  1. per-screen region listings (`<div class='sub' style='margin-top:4px'>`), then
  2. the long "How to read this" note → a one-paragraph version.
  Step 2 runs only if step 1 was not enough; on 2026-09-23 17:16 step 1 alone brought it to
  9,959 B and the full note was kept.
- The printed line now reports the real byte count, the reserve and the limit, and warns
  `STILL OVER LIMIT` if a future body cannot be trimmed enough.

**Not a verdict change** — MINOR bump only; no room can change Ok/Abnormal because of this.

---

## [1.6.0] — 2026-09-23 — "stop the catch-up burst"

**Symptom Danny reported:** four reports/emails arrived at 08:07, 08:12, 08:17 and 08:21
instead of one per hour.

**Root cause — not a schedule bug.** All 16 automations are correct
(`FREQ=DAILY;BYHOUR=<h>;BYMINUTE=15`, verified). What happened is that WorkBuddy was shut
down after the 20:17 run, so the **21:15 and 22:15 slots (and 07:15 this morning) were
missed**. When WorkBuddy started again at ~08:07 the scheduler **replayed every missed slot
back to back**, and each replay produced a fresh report because it reads live camera frames
— so the four emails were near-identical snapshots taken minutes apart.

### Added
1. **Run throttle** (`av_report.py`, new `MIN_RUN_MIN` / `LAST_RUN` / `last_run_age_min()`
   / `note_last_run()`)
   - A run is refused unless ≥ **45 minutes** (`MIN_RUN_MIN`, env-overridable, `0`
     disables) have passed since the last *completed* run, recorded in
     `.workbuddy/tmp/last_run.json`. 45 min never blocks the hourly cadence; it only kills
     a catch-up burst, where replays arrive 4–5 minutes apart.
   - Refused runs print `RESULT skip=last run was N min ago (min interval 45 min) …` and
     write nothing — no scan, no HTML, no email.
   - `FORCE=1` overrides it for a genuine manual run.
2. **Automation prompts now delegate to the skill.** All 16 prompts were reduced to
   "load `shekmun-av-audit` and follow its *Automation run* section", which now holds the
   pipeline command, the `RESULT` contract, the throttle rule and the email steps. Rule
   changes are edited in **one** place from now on instead of 16.
3. Skill gained a **"Run throttle — NEVER send twice in a row"** and an
   **"Automation run (what a scheduled slot does)"** section.

### Expected behaviour from now on
Start WorkBuddy after a night off → the first replayed slot runs and emails one report;
the remaining replays print `RESULT skip=` and send nothing.

### Still open
- The scheduler's replay behaviour itself cannot be configured — the throttle is a
  guard at the pipeline level, not a fix for the scheduler.
- If Danny ever wants a missed slot genuinely re-run within 45 min, use `FORCE=1`.

---

## [1.5.0] — 2026-09-22 — "false-alarm sweep + versioning"

Five outstanding items from the 2026-09-22 review, plus version control.

### Fixed
1. **`unknown` no longer counts as a device fault** (`av_mail.py`, `av_scan.py`)
   - Was: `status != 'ok'` → fault. Right after the monitoring poller restarts,
     `snapshot.json` republishes every device as `status: "unknown"` with an empty
     `checkedAt` and `rttMs: -1`, which made **7 rooms (SM-11-02 … SM-11-08) report
     Abnormal at 08:02** and emailed that false alarm to Danny.
   - Now: `is_fault(d)` is true **only** for an explicit `fail`. `unknown` means
     "not measured yet".
   - Added `poller_state(snap)`: if ≥ 50 % of all devices are un-polled, the run is marked
     *poller stale* — device reachability is skipped entirely and a warning banner is
     shown at the top of both the HTML report and the email.
2. **Phantom (OCR-only) displays no longer exceed the declared inventory**
   (`av_scan.py → screen_states`)
   - An AVoIP standby banner is often read far away from any detected bright region
     (measured 200–540 px from the nearest region centre — standby screens are too dark
     for the blob detector), so it becomes a `box=None` "phantom" display.
   - Phantoms now **take a slot from the declared inventory first**
     (`limit = declared − n_phantom`). A 4-TV room can no longer show 5 monitored displays.
3. **Clearer room verdict when a standby banner is read** (`aggregate_screen_state`)
   - Old wording `Idle – AVoIP decoder standby (1 idle / 4 other)` was confusing.
   - New: `Idle – AVoIP decoder standby (standby banner read in frame; 4 detected
     region(s) not attributable — possibly whiteboard / window)`.
4. **Old contact sheets are cleaned up** (`av_report.py → cleanup()`)
   - 16 runs/day were piling up ~16 jpg per day in the project root.
   - Files older than **48 h** are now deleted (contact sheets `all_rooms_*.jpg` and raw
     frames in `.workbuddy/tmp/s1|s2|s3`). Override with `KEEP_HOURS=<hours>`;
     `KEEP_HOURS=0` disables it. Reported as `RESULT cleanup=removed N file(s)`.

### Added
5. **OUT OF SYNC must repeat on two consecutive runs** (`av_scan.py`)
   - New `SYNC_CONFIRM_WINDOW_S = 3 h`; raw verdicts persist in
     `.workbuddy/tmp/sync_history.json` (keyed by room).
   - A first-time mismatch is downgraded to `check` and labelled
     **OUT OF SYNC (1ST RUN)** — reported for a visual check, **not** Abnormal. Only a
     second run within 3 h that agrees raises the Abnormal.
6. **Version number in the report and the email** — `VERSION` in `av_scan.py` is the single
   source of truth; `av_mail.py` imports it. Shown in the HTML subtitle, the HTML footer
   (links `changelog.md`), the email subtitle and the email footer.
7. **Schedule changed to a true 07:15–22:15 hourly cadence** — replaced the single
   `FREQ=HOURLY` automation (which the scheduler fired at :55 / drifting) with **16 daily
   automations**, one per hour: `FREQ=DAILY;BYHOUR=<h>;BYMINUTE=15`, hours 7…22.
   `BYHOUR` lists and `BYMINUTE` on `FREQ=HOURLY` are **not** supported by the scheduler;
   `DAILY` + a single `BYHOUR` + `BYMINUTE=15` is exact.

---

## [1.4.0] — 2026-09-21 (evening) — "sync only when highly unmatched"

**Verdict-affecting.** Danny: *"only treat as out sync when the display is highly unmatch"*.

- `sync_confidence()` — `high` = OCR text or measured luminance (`Off / dark`, AVoIP
  standby, Windows lock, content *with* readable text); `medium` = structural reading only
  (blank, content without text); `low` = unreadable → excluded from the verdict.
- Four gates, all must pass for `out-of-sync`, otherwise `check` / `unverified`:
  1. ≥ 2 usable readings (else `NOT VERIFIED`)
  2. **hard mismatch** — standby / lock / off vs real content (two differing *content*
     readings are not enough, OCR is angle-dependent)
  3. at least one side is `high` (both sides structural → `CHECK REGION`)
  4. **dominance** — disagreeing area ≥ `SYNC_MIN_AREA_RATIO` (**30 %**, raised from 15 %);
     with 3+ evidenced displays a lone dissenter must itself be `high`
- Area threshold constant `SYNC_MIN_AREA_RATIO = 0.30` next to `SYNC_MIN_DECODERS`.
- Verified with synthetic cases: standby-vs-content (2 screens) → OUT OF SYNC; 3 standby
  vs 1 content-with-text → OUT OF SYNC; off vs content → OUT OF SYNC; tiny patch,
  both-sides-structural, lone low-confidence dissenter → CHECK REGION; all content with
  different text → IN SYNC.

---

## [1.3.0] — 2026-09-21 (20:25) — "Idle is narrow"

**Verdict-affecting.** Danny: *"for idle status, only take Windows lock screen, AVoIP
standby screen and all blank; a Windows desktop or application kept static for long is
content on screen"*.

- Idle is now exactly three states:
  1. `Idle – AVoIP decoder standby` — standby banner OCR
  2. `Idle – Windows lock screen` — only a clock readable, no application
  3. `Idle – blank screen (no content)` — no text and featureless
     (`nonflat < BLANK_NONFLAT_MAX 0.10` **and** `rowstd < BLANK_ROWSTD_MAX 12`)
- Everything else lit: `Active – content on screen` — **a static Windows desktop counts as
  content, not idle**. `On – content not readable` remains only when there is no structural
  evidence at all.
- **Removed** the old "no text + ≥98.5 % static ⇒ idle desktop" rule and the
  "one idle display makes its static siblings idle" propagation — both contradict the above.
- `region_structure()` gained `std`; `idle_subtype()` now maps lock / blank.
- Effect: the 13:41 false Abnormal on SM-11-01 / SM-11-08 disappeared — their static
  desktops became content, so the rooms went back to IN SYNC.

---

## [1.2.0] — 2026-09-21 (13:41) — "declared display inventory"

**Verdict-affecting.** Danny confirmed the inventory and the AVoIP exception.

- Authoritative list in `av_monitor_config.json → displays`
  (overrides the decoder count reported by `snapshot.json`):
  SM-11-01 = 4 LED TV, SM-11-02 = 2, SM-11-03…06 = 1 LED wall each, SM-11-07 = 2,
  SM-11-08 = 2, Common Area = 1.
- Only the `N` largest bright regions are monitored; smaller ones are traditional
  whiteboards / noticeboards and are listed under "Ignored bright regions".
- **AVoIP exception** — Danny: *"display AVoIP standby is one of the TV"*. Any bright region
  whose OCR matches `DISPLAY_TEXT_KEYS` (AVOIP, DECODER, STANDBY, VIDEO SOURCE,
  DISCONNECTED) is force-set `monitored=True` + `promoted=True`, never treated as a board.
- Report labels such a region "counted as a TV (AVoIP standby text read from this region)".

---

## [1.1.0] — 2026-09-21 (13:23) — "49 °C alarm threshold"

**Verdict-affecting.** Danny raised the KDS alarm from 45 °C to **49 °C**.

- Threshold is config-driven: `av_monitor_config.json → scan.temp_alarm_c`
  (warn band `temp_warn_c` = 46). Code default `KDS_ALARM = 49` is only a fallback.

---

## [1.0.0] — 2026-09-21 (morning) — first automated report

- Camera snapshots 172.18.22.101-109 + `http://10.107.147.121:8080/snapshot.json`.
- 4-part per-room report: lighting / use / TV-LED wall / other observations.
- Snapshot embedded inside the room's display cell; HTML attachment + 3×3 contact sheet;
  hourly email to `dannylam@hsu.edu.hk`.
- Subject: `HSUHK@Shek Mun Audit report- {Datetime} / Status: Ok|Abnormal (Room names)`.
- Common Area is `scheduled_down`: still scanned every run, tagged SCHEDULED DOWN,
  excluded from the verdict.
- **Lighting never creates an Abnormal verdict** (information only).
- Multi-display picture sync introduced (dual / quad rooms share one AVoIP source).
- Run statistics (per-stage time + estimated LLM tokens) in the report and email footer.

---

# Planned / under consideration

Not yet built — recorded so the next session can pick them up.

| # | Item | Why | Status |
|---|---|---|---|
| P1 | Attribute a stray standby banner to the nearest display region when it is close enough, instead of always creating a phantom | Phantoms have no box, so they can never take part in the sync verdict | Open — needs a distance threshold validated against real frames |
| P2 | Suppress the 24 devices that the dashboard's own `suspended.js` whitelist already excludes | Baseline `fail` devices that are intentionally suspended still count as Abnormal | Open — needs the whitelist pulled from the monitoring host |
| P3 | Track KDS temperature trend per room (rolling max / delta) | Everything is judged against a fixed 49 °C; a rising trend would warn earlier | Open |
| P4 | Reduce report size (HTML is ~530 KB with embedded snapshots) | Attachment weight | Open — could shrink the JPEG quality of the embedded frames |
| P5 | Emit a short "what changed since the last run" diff line in the email | Danny reads 16 emails a day | Open — needs a previous-run snapshot to diff against |

---

# Known limitations

- `WebFetch` cannot reach the private monitoring host — use `curl`.
- OCR must run on the full 1280×720 frame; cropping each bright blob and OCR-ing that fails,
  because the blob detector often misses the real display.
- Pixel correlation between displays is **not** used for the sync verdict (same content seen
  at two angles measures ~0.0–0.4, overlapping with genuinely different content). It is
  printed as information only.
- Camera clocks return `Date: Thu, 06 Jul 2000` (no NTP) — never use camera headers for timing.
- `172.18.22.109` (Common Area) returns HTTP 502 while scheduled down.
- The scheduler rejects `BYHOUR` lists and `BYMINUTE` on `FREQ=HOURLY`; an exact
  `:15` cadence needs one `FREQ=DAILY` automation per hour (that is what v1.5.0 does).
- Agent Mail daily quota is 50 messages; 16 runs/day is fine.
