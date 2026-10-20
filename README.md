# artemis2-lunar-flash 🌕

**Did a camera catch what the astronauts saw?**

During the Artemis II lunar flyby (April 2026), the crew reported **five faint impact flashes** on the Moon's far side during a ~54-minute total solar eclipse. They were seen with the unaided eye, possibly the faintest lunar impact flashes ever observed by humans, and recorded through crew audio and hand-drawn annotations. No flash has been reported in imagery so far.

This project builds an open, time-aligned **audio ↔ image** index of the Artemis II lunar science archive, then uses it to search the crew camera frames taken around each reported sighting for a photographic counterpart.

> Status: 🚧 Phase 1 in progress

## Why this matters

- Small-impactor flux on the Moon is a real hazard input for future lunar habitats and infrastructure.
- Artemis II is the first planetary science dataset gathered primarily by humans in more than 50 years. Its value depends on linking what the crew *said* to what the cameras *recorded*, and today nothing does that directly.
- A camera detection (or a well-constrained non-detection) of an eye-witnessed flash would be a useful, citable result.

## Plan

### Phase 1: Observation index & explorer (target: mid-December 2026)
Open dataset and tool linking crew speech to images by time.
- [ ] Map PDS bundles; list eclipse-window products (crew Nikon Z9/D5, Orion cameras)
- [ ] Parse PDS4 XML labels → table of image ID, camera, lens, exposure, `start_date_time`
- [ ] Parse PCD audio transcripts (Whisper where transcripts are missing) → timestamped utterances
- [ ] Join utterances ↔ images on synchronized Orion clock time
- [ ] Publish dataset (Hugging Face + Zenodo DOI)
- [ ] Web explorer: pick a moment, hear/read the crew, see the frames

### Phase 2: Flash search (target: early January 2027)
- [ ] Extract each "flash" callout time from audio/transcripts and annotations
- [ ] Pull Z9/D5 frames within a window around each callout
- [ ] Transient search: frame differencing, PSF-like point-source detection on the night side
- [ ] Reject false positives: cosmic-ray hits, hot pixels, window/cabin reflections, solar-array glare
- [ ] Report detections or upper limits per event
- [ ] Short abstract: LPSC 2027 (15–19 March 2027) or Europlanet Science Congress 2027

### Phase 3: Stretch
- [ ] Geolocate frames once the SPICE bundle is released
- [ ] Extend the index to all flyby observation targets

## Data

- Source: [PDS Artemis II archive](https://pds-geosciences.wustl.edu/missions/artemis2/index.htm), with the crew camera, Orion camera and mission audio bundles
- Start with the [Lunar Science Data User Guide](https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf)
- Caveats from the guide: no science-grade radiometric calibration, uncharacterized multi-layer windows, cabin glare, and NASA ID order ≠ observation time (always sort by `start_date_time`)
- Raw data is **not** stored in this repo. Download into `data/raw/`.
- Credit: images and audio courtesy of NASA/CSA.

## Structure

```
data/          raw/ and processed/ (git-ignored)
notebooks/     exploration
src/           download, label parsing, alignment, flash search
docs/          notes, abstract drafts
```

## Author

Yusuf Korkmazyiğit · [yusufkorkmazyigit.com](https://yusufkorkmazyigit.com)

## License

MIT (code). Data belongs to NASA/CSA and follows NASA media usage guidelines.
