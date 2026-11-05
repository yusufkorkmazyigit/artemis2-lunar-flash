# Project overview

**artemis2-lunar-flash: did the cameras catch what the astronauts saw?**

*Status as of 2026-11-04 · Phase 1 in progress · Author: Yusuf Korkmazyigit*

---

## In one paragraph

During the Artemis II lunar flyby in April 2026, Orion passed through the Moon's shadow and
the crew saw a total solar eclipse that lasted about 54 minutes. In that darkness they reported
five faint, pinpoint flashes of light on the lunar surface, seen **by naked eye**. NASA's
preliminary science material describes these as possibly the faintest lunar impact flashes ever
seen by humans, but it does not report any of them in the photos or video. This project
builds an open, time-aligned index of the Artemis II crew-camera and audio archive, and uses it
to ask a precise question: **was any of the five flashes recorded by a camera, and if not, how
bright could a flash have been and still be missed?**

## Why this is worth doing

- **Science.** How often small meteoroids strike the Moon is an input to risk assessments for
  future lunar surface infrastructure. Impact flashes are one of the few ways to measure that
  flux directly.
- **Data.** Artemis II produced the first planetary science data set in more than 50 years that
  was collected mainly by people rather than robots. The archive holds what the crew *said*
  (audio, transcripts, notes) and what the cameras *recorded*, but no public tool links the two.
- **Openness.** The data were released on 2026-10-07 through NASA's Planetary Data System
  (PDS). Every product used here is public, and every row this project produces keeps the PDS
  identifier (LIDVID) of the product it came from.

## Research questions

1. **Index.** For any moment of the flight, which crew photos were taken, with which camera,
   lens and exposure, and what was the crew saying at that time?
2. **Coverage.** For each reported flash, was any camera exposing, and pointed at the Moon,
   when it happened?
3. **Detection or limit.** If a flash falls inside an exposure, can it be found as a transient
   point source? If none is found, what is the per-event brightness upper limit?

## Data

Five PDS4 bundles, a little over 800 GB in total. This project uses mainly:

| Bundle | Content | DOI |
|---|---|---|
| `artemis2_crew_camera` | Handheld Nikon D5 (×2) and Nikon Z9 images | [10.17189/x52v-tb80](https://doi.org/10.17189/x52v-tb80) |
| `artemis2_mission_audio` | Crew tablet audio, comm loops, transcripts, crew notes | [10.17189/4a29-dz64](https://doi.org/10.17189/4a29-dz64) |
| `artemis2_orion_camera` | Spacecraft cameras (incl. solar-array wing cameras) | [10.17189/hzev-nq50](https://doi.org/10.17189/hzev-nq50) |
| `artemis2_mission` | Documentation, cabin environment data | [10.17189/36fx-pd80](https://doi.org/10.17189/36fx-pd80) |

Known limitations, from the Data User Guide: there is no radiometric calibration, the cabin
windows were not characterised before flight, and reflections from the cabin and solar arrays
can mimic point sources. The method below is built around these limits.

## What has been done so far

**Software** (Python package `a2flash`, CI on Python 3.11–3.13, ruff, strict mypy, 32 tests):

| Command | What it does |
|---|---|
| `a2flash parse-label` | Reads one PDS4 XML label into a flat record, with timezone-aware UTC times |
| `a2flash index` | Turns a folder of labels into a typed `frames` table (Parquet/CSV) |
| `a2flash atlas-frames` | Builds the same `frames` table for any UTC window from the PDS Imaging Atlas API |
| `a2flash download-labels` | Rate-limited, resumable label download for PDS folders that allow listing |

The `frames` table has one row per image: product id, camera and serial number, flight day,
crew activity, lens, focal length, f-number, exposure time, ISO and capture time. The
parser was validated on real Artemis II labels from all three crew cameras.

**Findings from the camera metadata** (all derived from PDS labels, not from secondary
sources):

- The eclipse images are in **flight day 6** (`fd06`). Flight day 6 crosses UTC midnight, so
  the flight day is always read from the label, never inferred from the UTC date.
- The crew labelled the eclipse imaging as `Eclipsed Moon (1/2)` and `(2/2)`, between
  `Sunset` and `Sunrise` activities. From these labels the dark period lies within roughly
  **00:34–01:35 UTC on 2026-04-07**. This does not match some secondary sources, so the window
  is marked *provisional* until confirmed from primary NASA documents or the transcripts.
- The provisional window holds **2,189 crew-camera frames**; **279** are labelled *Eclipsed
  Moon* (D5-015: 196, D5-017: 21, Z9: 62; about 14.7 GB of TIFF images).
- **Exposure duty cycle:** during the eclipse imaging, at least one camera was exposing for
  only about **4 %** of the time. A flash that lasts a fraction of a second therefore had only a
  few-percent chance of falling inside any exposure, before camera pointing is even considered.
  The most likely result is a per-event non-detection with a stated probability of coverage,
  and the analysis is designed to report exactly that.

A data-engineering note: the Atlas search API silently returned repeated hits under
offset-based paging (669 of 2,189 frames went missing in the first run). The tool now splits
the time window recursively until each slice fits in one response, and it warns on duplicates.

Every technical decision, with its date and reason, is logged in
[`docs/decisions.md`](decisions.md).

## Method

**Phase 1: observation index and explorer** (target: mid-December 2026)

1. Download only the eclipse-window images, with checksum verification and resume.
2. Parse transcripts into a time-stamped utterance table; use speech-to-text only where
   transcripts are missing.
3. Link each utterance to the frames taken within a fixed time window; verify by hand on a
   sample.
4. Publish the index as an open dataset with a DOI, plus a simple web explorer.

**Phase 2: flash search** (target: January 2027)

1. Extract the time of each flash call-out from audio, transcripts and crew notes, stored as
   an interval to keep the uncertainty.
2. Select frames whose exposure overlaps a call-out interval and whose field covers the Moon.
3. Pre-process raw images: hot-pixel and bad-pixel masks from dark frames of the same camera.
4. Search for transients with difference imaging and PSF-matched point-source detection.
5. Vet candidates against cosmic rays, hot pixels and window or cabin reflections, and check
   them against the regions the crew marked.
6. Quantify the result: false-alarm rate from frames outside the call-outs, detection
   efficiency from injection–recovery of synthetic sources, and a per-event upper limit
   (in instrument units, or relative magnitudes if stars are in the frame).

**Phase 3: extension** (after the SPICE geometry bundle is released): place frames on lunar
maps and extend the index to the whole flight.

## Planned outputs

| Output | Where | When |
|---|---|---|
| Open dataset (frames, utterances, links) | Hugging Face + Zenodo DOI | December 2026 |
| Web explorer | GitHub Pages or Streamlit | December 2026 |
| Short scientific abstract | Planetary science conference, or arXiv preprint | Early 2027 |

## Principles

- **Reproducible:** every output can be rebuilt from public PDS data with one CLI command.
- **Traceable:** every row carries the PDS identifier of its source product.
- **Honest about uncertainty:** provisional values are marked as such, and a non-detection is
  reported as a quantified upper limit rather than as a null result.
- **Polite to the archive:** selective, rate-limited, resumable downloads only.

## Acknowledgements and disclaimer

Data: NASA/CSA, via the NASA Planetary Data System. This is an independent project and is not
affiliated with or endorsed by NASA, CSA, ESA or Airbus.

Contact: [github.com/yusufkorkmazyigit](https://github.com/yusufkorkmazyigit) ·
[linkedin.com/in/yusufkorkmazyigit](https://www.linkedin.com/in/yusufkorkmazyigit/)
