# artemis2-lunar-flash 🌕

Detecting faint lunar impact flashes and surface features in NASA's **Artemis II** lunar science dataset using machine learning, with hyperparameters tuned by the **Artificial Bee Colony (ABC)** algorithm via [`abc-optimizer-lib`](https://github.com/yusufkorkmazyigit).

> Status: 🚧 early planning

## Motivation

On 7 October 2026, NASA released 800+ GB of Artemis II lunar science data to the Planetary Data System (PDS):
11,000+ full-resolution images and videos from crew handheld cameras and Orion cameras, 8.5 hours of crew audio observations, and crew-annotated images.

During the flyby, the crew reported **five faint flashes** on the lunar surface and marked their locations on images. These labeled events make a natural starting point for an anomaly-detection problem: can a model find them, and can it find more?

## Goals

1. **Impact flash detection** (main track): detect transient flashes in video frames; validate against the crew-marked events.
2. **ABC hyperparameter optimization**: tune the detector with `ABCSearchCV` and compare against grid/random/Bayesian search.
3. *(stretch)* **Crater detection & georeferencing** against LRO basemaps.
4. *(stretch)* **Audio → structured observations**: transcribe crew audio (Whisper) and link observations to images and coordinates.

## Data

- Source: NASA Planetary Data System → Moon → Artemis II
- Read the *Artemis II Lunar Science Data User Guide* first.
- Raw data is **not** stored in this repo (see `.gitignore`). Download into `data/raw/`.
- Credit: images and audio courtesy of NASA/CSA.

## Structure

```
data/          raw/ and processed/ (git-ignored)
notebooks/     exploration
src/           download, preprocessing, models, optimization
docs/          notes, paper drafts
```

## Roadmap

- [ ] Read Data User Guide + Preliminary Lunar Science Report
- [ ] Map PDS collection structure; list video/image collections
- [ ] Write selective download script (no full 800 GB download)
- [ ] Locate the five crew-marked flash events
- [ ] EDA notebook: frame stats, noise, exposure
- [ ] Baseline: frame differencing + thresholding
- [ ] ML detector (e.g. CNN on frame stacks)
- [ ] Tune with `ABCSearchCV`; benchmark against other searchers
- [ ] Run at scale on GPU server
- [ ] Write-up (blog / arXiv / conference)

## Author

Yusuf Korkmazyiğit · [yusufkorkmazyigit.com](https://yusufkorkmazyigit.com)

## License

MIT (code). Data belongs to NASA/CSA and follows NASA media usage guidelines.
