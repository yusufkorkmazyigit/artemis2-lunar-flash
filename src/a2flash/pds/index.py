"""Build a product index (one row per label) from a directory of PDS4 labels."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from a2flash.pds.labels import LabelParseError, parse_label

log = logging.getLogger(__name__)


def build_index(labels_dir: str | Path, pattern: str = "**/*.xml") -> pd.DataFrame:
    """Parse every label under ``labels_dir`` and return them sorted by capture time.

    Rows are sorted by ``start_utc`` (never by product number, which reflects
    catalog order, not capture order). Unparseable files are logged and skipped.
    """
    rows = []
    for label in sorted(Path(labels_dir).glob(pattern)):
        try:
            rows.append(parse_label(label))
        except LabelParseError as exc:
            log.warning("skipping %s: %s", label, exc)
    if not rows:
        return pd.DataFrame(columns=["lidvid", "start_utc"])
    df = pd.DataFrame(rows)
    df["start_utc"] = pd.to_datetime(df["start_utc"], utc=True)
    df["stop_utc"] = pd.to_datetime(df["stop_utc"], utc=True)
    return df.sort_values(["start_utc", "lidvid"], kind="stable").reset_index(drop=True)
