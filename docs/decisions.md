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
