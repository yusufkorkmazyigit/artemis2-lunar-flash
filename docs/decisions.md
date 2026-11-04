# Decision log

Format: date — decision — rationale.

- **2026-10-20** — Repository created (`master`).
- **2026-10-20** — Dropped "train a detector on 5 labelled flashes"; the flashes were seen by
  eye, not recorded. New direction: audio ↔ image index + flash search.
- **2026-10-20** — ABC (Artificial Bee Colony) will not be forced into this project.
- **2026-10-20** — Budget: 1 day/week for ~9 weeks; the graduation project has priority.
- **2026-10-22** — This is the main portfolio project for German MSc applications and the
  Airbus career goal. No second portfolio project will be started in parallel.
- **2026-10-23** — Packaging: `src/` layout, hatchling, `argparse` CLI (no extra CLI
  dependency), ruff + pytest + mypy, CI on Python 3.11–3.13.
- **2026-10-23** — `parse_label` reads only PDS4 core elements by name. Discipline/Mission
  area leaves are flattened generically into `disc.<path>` keys (units as `@unit`, repeats as
  `[i]`) because Artemis II local dictionary names are not yet verified against real labels.
  Mapping to the `frames` schema happens after real labels are inspected (Week 2).
- **2026-10-23** — Naive timestamps raise an error instead of being assumed UTC (PDS4
  `date_time_utc` requires `Z`).
- **2026-10-23** — The current test fixture is **synthetic**. It must be replaced or joined
  by 3 real Artemis II labels in `tests/fixtures/` (Week 2).
- **2026-10-23** — `a2flash index` currently reads a local labels directory. The
  `--bundle/--flight-day` interface from the plan will wrap this once the download module
  exists (Week 3).
- **2026-11-04** — Provisional eclipse search window `2026-04-07T01:10Z`–`02:57Z` (secondary
  sources: eclipse 01:35–02:32 UTC, padded ±25 min). Marked `verified: false` until real
  Z9/D5 label timestamps confirm it. Note: the eclipse came *after* the far-side
  communications blackout (22:46–23:24 UTC on 2026-04-06), not during it. The UTC date is
  2026-04-07 while NASA calls it mission day 6, so the `fdXX` folder must be checked.
- **2026-11-04** — Removed leftover `src/__init__.py` and `src/download.py` from the first
  scaffold (they broke mypy module resolution); added `py.typed`; mypy now runs in CI.
- **2026-11-04** — Added 3 real labels from `crew_camera/data_raw/fd06` as fixtures (Z9 SN
  3920019, D5 SN 3500015, D5 SN 3500017). `parse_label` handles them unchanged. Findings:
  `stop_date_time` is nil; labels carry `msn:flight_day_number` and an observational intent
  (`activity_id`, e.g. `17_Discussion #5: Limb`; `target_id` only sometimes). The Z9 serial is
  `3920019` (not `39200019`). Camera ids in file names are `nkz9019` / `nkd5015` / `nkd5017`.
- **2026-11-04** — New `a2flash.pds.frames.to_frames` maps verified label keys to the typed
  `frames` table; `a2flash index` now writes it by default (`--schema raw` keeps every key).
  Units for focal length (mm) and exposure (s) are checked, not assumed.
- **2026-11-04** — fd06 frames so far span 2026-04-06 15:25–22:34 UTC with
  `flight_day_number = 6`. Whether the eclipse (~2026-04-07 01:35 UTC) sits in fd06 or fd07 is
  still open. The three sampled frames are 1/1000 s at ISO 400 (daylit Moon), so eclipse
  frames should look very different (long exposures) — check that when they are found.
- **2026-11-04** — Eclipse frames are expected in **fd06**: a Z9 frame at
  2026-04-07T01:04:57Z (art002e009300) still has `flight_day_number = 6`, and a fd07 Z9 frame
  is at 2026-04-07T21:37Z. So flight day 6 crosses UTC midnight; `flight_day` must always come
  from the label, never from the UTC date (test added).
- **2026-11-04** — Widened the provisional window to 00:30–03:00 UTC. Reason: NASA's simulated
  eclipse image is captioned 01:04 UTC, earlier than the 01:35 start from Wikipedia, and
  art002e009300 at 01:04 is already a dark-side setting (6 s, ISO 1600, f/2 vs 1/1000 s,
  ISO 400, f/8 on the lit Moon). Narrow it once the eclipse activity frames are found.
- **2026-11-04** — The `data_raw` inventory CSV (10,329 products) lists LIDVIDs only, not the
  `fdXX` folder, so download URLs cannot be built from it. `a2flash download-labels` instead
  reads one folder's HTML index and fetches only product labels (`*.xml`): stdlib `urllib`,
  2 req/s, retries with backoff on 5xx/429/network errors, `.part` + rename, existing valid
  labels skipped. Images are a separate, later step limited to the eclipse window.
- **2026-11-04** — The archive's CloudFront/S3 folders do not allow directory listing
  (`AccessDenied`), so `download-labels` cannot list fd06. Switched discovery to the PDS
  Imaging Atlas search API (Elasticsearch, `POST /api/search/atlas/_search`). Each hit already
  carries the flattened label plus file URI, size and MD5 for both the TIF and the label.
  `a2flash atlas-frames` builds the `frames` table for a UTC window in one query, mapping Atlas
  keys onto the same raw keys as `parse_label` so both paths share `to_frames` (a test checks
  that the API row equals the label row for art002e009300). The query is loose; every hit is
  re-checked client-side (bundle, collection, `.tif`, time window).  `download-labels` stays for servers that do list folders.
- **2026-11-04** — Known gap: the Atlas does not carry units, so the unit check in
  `to_frames` only runs on the label path. Units were verified on the label fixtures.
- **2026-11-04** — First live Atlas run: the provisional window 00:30–03:00 UTC holds 2,189
  crew-camera raw frames. Pages of 500 hits made the API return 502 (response too large;
  each hit carries the full flattened label). Default page size is now 100, halved on 5xx
  down to 10; 4xx errors are not retried.
- **2026-11-04** — from/size paging is unreliable on this index: a 2,189-hit window
  returned 669 repeated hits, so 669 frames were silently missing (first table had 1,520
  rows). Replaced paging with time-window bisection: a slice is fetched only when its total
  fits in one response (`total <= page_size`), otherwise it is split in half (ms precision).
  No reliance on sort order or offsets. Repeated `_id`s are still counted and warned about.
- **2026-11-04** — Eclipse frames are labelled by activity: `26_Eclipsed Moon (1/2)` and
  `28_Eclipsed Moon (2/2)`, between `24_Sunset` and `30_Sunrise` (D5-015, D5-017, Z9). The
  Z9 also has `h_Observation Break` frames in the window, to be checked for Moon coverage.
