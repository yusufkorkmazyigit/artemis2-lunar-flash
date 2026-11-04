"""Command-line entry point: ``a2flash <command>``."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from a2flash import __version__
from a2flash.pds.atlas import search_frames
from a2flash.pds.download import download_labels
from a2flash.pds.frames import to_frames
from a2flash.pds.index import build_index
from a2flash.pds.labels import LabelParseError, parse_label, parse_utc


def _cmd_parse_label(args: argparse.Namespace) -> int:
    try:
        row = parse_label(args.label)
    except LabelParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(row, indent=2, default=str, ensure_ascii=False))
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    df = build_index(args.labels_dir)
    if args.schema == "frames":
        df = to_frames(df)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix == ".csv":
        df.to_csv(out, index=False)
    else:
        df.to_parquet(out, index=False)
    print(f"wrote {len(df)} rows -> {out}")
    return 0


def _cmd_atlas_frames(args: argparse.Namespace) -> int:
    start, stop = parse_utc(args.start), parse_utc(args.stop)
    if start is None or stop is None or stop <= start:
        print("error: need --start < --stop (UTC with 'Z')", file=sys.stderr)
        return 2
    df = search_frames(start, stop, bundle=args.bundle, collection=args.collection)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix == ".csv":
        df.to_csv(out, index=False)
    else:
        df.to_parquet(out, index=False)
    print(f"wrote {len(df)} frames -> {out}")
    if len(df):
        print(df.groupby(["camera", "activity_id"], dropna=False).size().to_string())
    return 0


def _cmd_download_labels(args: argparse.Namespace) -> int:
    stats = download_labels(
        args.url,
        args.out,
        max_requests_per_second=args.rate,
        limit=args.limit,
    )
    print(f"downloaded {stats.downloaded}, skipped {stats.skipped}, failed {stats.failed}")
    return 1 if stats.failed else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="a2flash", description=__doc__)
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    pl = sub.add_parser("parse-label", help="print one PDS4 label as JSON")
    pl.add_argument("label", type=Path)
    pl.set_defaults(func=_cmd_parse_label)

    ix = sub.add_parser("index", help="index a directory of labels to Parquet/CSV")
    ix.add_argument("--labels-dir", type=Path, required=True)
    ix.add_argument("--out", type=Path, required=True, help="*.parquet or *.csv")
    ix.add_argument(
        "--schema",
        choices=["frames", "raw"],
        default="frames",
        help="frames: typed frames table (default); raw: every label key",
    )
    ix.set_defaults(func=_cmd_index)

    af = sub.add_parser("atlas-frames", help="frames table for a UTC window from the Atlas API")
    af.add_argument("--start", required=True, help="UTC, e.g. 2026-04-07T00:30:00Z")
    af.add_argument("--stop", required=True, help="UTC, exclusive")
    af.add_argument("--out", type=Path, required=True, help="*.parquet or *.csv")
    af.add_argument("--bundle", default="artemis2_crew_camera")
    af.add_argument("--collection", default="data_raw")
    af.set_defaults(func=_cmd_atlas_frames)

    dl = sub.add_parser(
        "download-labels", help="download all product labels (*.xml) of one PDS folder"
    )
    dl.add_argument("url", help="folder URL, e.g. .../artemis2_crew_camera/data_raw/fd06/")
    dl.add_argument("--out", type=Path, required=True, help="e.g. data/raw/labels/fd06")
    dl.add_argument("--rate", type=float, default=2.0, help="max requests per second")
    dl.add_argument("--limit", type=int, default=None, help="only the first N labels (testing)")
    dl.set_defaults(func=_cmd_download_labels)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
