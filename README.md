# artemis2-lunar-flash

[![CI](https://github.com/yusufkorkmazyigit/artemis2-lunar-flash/actions/workflows/ci.yml/badge.svg)](https://github.com/yusufkorkmazyigit/artemis2-lunar-flash/actions/workflows/ci.yml)

**Did the cameras catch what the astronauts saw?**

During the ~54-minute total solar eclipse behind the Moon in April 2026, the Artemis II crew
reported five faint lunar impact flashes **by naked eye**. NASA's released material does not
report any of them in photos or video.

This project builds an open, time-aligned index that links every crew utterance to the
photographs taken at that moment, then uses it to search the Nikon Z9/D5 frames around each
flash call-out for a transient point source — or to set a per-event brightness upper limit.

> Data: NASA/CSA, Planetary Data System (PDS4). This project is not affiliated with or
> endorsed by NASA, CSA, ESA or Airbus.

## Why it matters

- **Science:** small-impactor flux on the Moon is a risk input for future lunar infrastructure.
- **Data:** the Artemis II archive is the first planetary science data set collected mainly
  by humans in over 50 years. No public tool yet links what the crew *said* to what the
  cameras *recorded*.
- **Hardware:** the archive also includes imagery from cameras on the solar-array wings of the
  European Service Module (ESM).

## Roadmap

### Phase 1: Observation index and explorer (target: 2026-12-14)
- [x] Repository scaffold, packaging, CI (lint + tests)
- [x] PDS4 label parser (`parse_label`) and `a2flash index` command
- [ ] Locate eclipse flight day and UTC window (Data User Guide + Archive Explorer)
- [ ] Validate parser against 3 real Artemis II labels; map camera/lens/exposure keys
- [ ] Download eclipse-window subset (selective, resumable, checksummed)
- [ ] Transcript parser → time-stamped utterance table (Whisper fallback)
- [ ] Utterance ↔ frame alignment, manually verified on 10 samples
- [ ] Publish dataset (Hugging Face + Zenodo DOI)
- [ ] Web explorer

### Phase 2: Flash search (target: 2027-01-10)
- [ ] Candidate frames per call-out window
- [ ] Hot-pixel masks, difference imaging, PSF-matched transient detection
- [ ] Vetting: cosmic rays, hot pixels, window/cabin reflections
- [ ] Injection–recovery efficiency, false-alarm rate, per-event upper limits
- [ ] One-page abstract

### Phase 3: Extension (when the SPICE bundle is released)
- [ ] Georeference frames onto lunar maps

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest && ruff check . && ruff format --check .

a2flash parse-label path/to/label.xml           # one label as JSON
a2flash index --labels-dir data/raw/labels --out data/interim/frames.parquet
```

Rows are always sorted by `start_utc`. Product numbers reflect catalog order, not capture
order. Every row keeps its `lidvid` so each value traces back to its PDS product.

## Repository layout

```
src/a2flash/      package (pds/, audio/, align/, flash/, explorer/)
tests/            pytest suite and label fixtures
configs/          paths, time windows, thresholds
docs/             decisions log and project context
data/             raw/ (read-only), interim/, processed/ — not tracked by git
```

## Data sources

| Bundle | DOI |
|---|---|
| `artemis2_crew_camera` | [10.17189/x52v-tb80](https://doi.org/10.17189/x52v-tb80) |
| `artemis2_orion_camera` | [10.17189/hzev-nq50](https://doi.org/10.17189/hzev-nq50) |
| `artemis2_mission_audio` | [10.17189/4a29-dz64](https://doi.org/10.17189/4a29-dz64) |
| `artemis2_mission` | [10.17189/36fx-pd80](https://doi.org/10.17189/36fx-pd80) |

- [Artemis II Data User Guide](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf)
- [Artemis II Preliminary Lunar Science Report](https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/)

## License

Code: MIT. Data remain subject to NASA/CSA media usage guidelines; credit "NASA/CSA" and
the PDS bundle DOIs when using derived products.
