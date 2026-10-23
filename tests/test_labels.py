from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from a2flash.cli import main
from a2flash.pds.index import build_index
from a2flash.pds.labels import LabelParseError, parse_label, parse_utc

FIXTURES = Path(__file__).parent / "fixtures"
SYNTH = FIXTURES / "synthetic_crew_camera.xml"


def test_core_fields() -> None:
    row = parse_label(SYNTH)
    assert row["lid"].endswith("art002e000001_z9019_raw")
    assert row["lidvid"] == row["lid"] + "::1.0"
    assert row["product_class"] == "Product_Observational"
    assert row["file_name"] == "art002e000001_z9019_raw_v01.tif"


def test_times_are_aware_utc() -> None:
    row = parse_label(SYNTH)
    assert row["start_utc"] == datetime(2026, 4, 6, 23, 41, 12, 250000, tzinfo=UTC)
    assert row["start_utc"].tzinfo is not None
    assert row["stop_utc"] > row["start_utc"]


def test_discipline_area_flattened_with_units_and_repeats() -> None:
    row = parse_label(SYNTH)
    assert row["disc.Exposure/exposure_duration"] == "1.0"
    assert row["disc.Exposure/exposure_duration@unit"] == "s"
    assert row["disc.Optical_Filter/filter_name"] == "none"
    assert row["disc.Optical_Filter/filter_name[1]"] == "window2"


@pytest.mark.parametrize("value", ["2026-04-06T23:41:12", "not-a-date"])
def test_parse_utc_rejects_naive_or_bad(value: str) -> None:
    with pytest.raises(LabelParseError):
        parse_utc(value)


def test_non_pds4_root_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xml"
    bad.write_text("<root/>", encoding="utf-8")
    with pytest.raises(LabelParseError, match="Not a PDS4"):
        parse_label(bad)


def test_index_sorts_by_time_not_product_number(tmp_path: Path) -> None:
    # Product 000002 is captured *before* 000001: catalog order != capture order.
    early = SYNTH.read_text(encoding="utf-8")
    early = early.replace("art002e000001", "art002e000002").replace(
        "2026-04-06T23:41:12.250Z", "2026-04-06T23:00:00Z"
    )
    shutil.copy(SYNTH, tmp_path / "a.xml")
    (tmp_path / "b.xml").write_text(early, encoding="utf-8")
    (tmp_path / "junk.xml").write_text("<root/>", encoding="utf-8")

    df = build_index(tmp_path)
    assert len(df) == 2
    assert df.loc[0, "lid"].endswith("art002e000002_z9019_raw")
    assert df["start_utc"].is_monotonic_increasing


def test_cli_index_writes_parquet(tmp_path: Path) -> None:
    shutil.copy(SYNTH, tmp_path / "a.xml")
    out = tmp_path / "out" / "frames.parquet"
    assert main(["index", "--labels-dir", str(tmp_path), "--out", str(out)]) == 0
    assert out.exists()
