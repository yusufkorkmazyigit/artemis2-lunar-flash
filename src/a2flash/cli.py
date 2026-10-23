"""Command-line entry point: ``a2flash <command>``."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from a2flash import __version__
from a2flash.pds.index import build_index
from a2flash.pds.labels import LabelParseError, parse_label


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
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix == ".csv":
        df.to_csv(out, index=False)
    else:
        df.to_parquet(out, index=False)
    print(f"wrote {len(df)} rows -> {out}")
    return 0


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
    ix.set_defaults(func=_cmd_index)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
