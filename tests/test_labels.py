from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from a2flash.cli import main
from a2flash.pds.frames import to_frames
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
    assert main(["index", "--labels-dir", str(tmp_path), "--out", str(out), "--schema", "raw"]) == 0
    assert out.exists()


# --- Real Artemis II labels (crew_camera/data_raw/fd06), downloaded 2026-11-04 ---

REAL = {
    "z9": FIXTURES / "art002e009291_nkz9019_raw_v01.xml",
    "d5_017": FIXTURES / "art002e009276_nkd5017_raw_v01.xml",
    "d5_015": FIXTURES / "art002e009279_nkd5015_raw_v01.xml",
}
LATE = {
    "z9_fd06_after_midnight": FIXTURES / "art002e009300_nkz9019_raw_v01.xml",
    "z9_fd07": FIXTURES / "art002e028292_nkz9019_raw_v01.xml",
}


@pytest.mark.parametrize("path", [*REAL.values(), *LATE.values()], ids=[*REAL, *LATE])
def test_real_labels_parse(path: Path) -> None:
    row = parse_label(path)
    assert row["lid"].startswith("urn:nasa:pds:artemis2_crew_camera:data_raw:")
    assert row["start_utc"].tzinfo is not None
    assert row["stop_utc"] is None  # nil (nilReason="missing") in real labels


def test_real_labels_to_frames(tmp_path: Path) -> None:
    for path in REAL.values():
        shutil.copy(path, tmp_path / path.name)
    frames = to_frames(build_index(tmp_path))

    assert list(frames["product_id"]) == ["art002e009276", "art002e009279", "art002e009291"]
    assert frames["start_utc"].is_monotonic_increasing
    z9 = frames.iloc[2]
    assert z9["camera"] == "nkz9019"
    assert z9["camera_model"] == "nikon_z9"
    assert z9["serial_number"] == "3920019"
    assert z9["start_utc"] == datetime(2026, 4, 6, 22, 34, 33, 980000, tzinfo=UTC)
    assert z9["flight_day"] == 6
    assert z9["focal_mm"] == 35.0
    assert z9["exposure_s"] == 0.001
    assert z9["iso"] == 400
    assert z9["activity_id"] == "17_Discussion #5: Limb"
    assert z9["target_id"] == "Limb"
    assert pd.isna(frames.iloc[0]["target_id"])  # absent in the D5-017 label
    assert set(frames["camera"]) == {"nkd5015", "nkd5017", "nkz9019"}


def test_to_frames_rejects_unexpected_unit(tmp_path: Path) -> None:
    path = REAL["z9"]
    text = path.read_text(encoding="utf-8").replace(
        '<img:exposure_duration unit="s">', '<img:exposure_duration unit="ms">'
    )
    (tmp_path / path.name).write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="expected unit"):
        to_frames(build_index(tmp_path))


def test_cli_index_frames_schema(tmp_path: Path) -> None:
    for path in REAL.values():
        shutil.copy(path, tmp_path / path.name)
    out = tmp_path / "frames.csv"
    assert main(["index", "--labels-dir", str(tmp_path), "--out", str(out)]) == 0
    df = pd.read_csv(out)
    assert list(df.columns)[:3] == ["lidvid", "product_id", "camera"]
    assert len(df) == 3


def test_flight_day_is_not_the_utc_date(tmp_path: Path) -> None:
    # Flight day 6 runs past UTC midnight: never derive flight_day from the UTC date.
    for path in LATE.values():
        shutil.copy(path, tmp_path / path.name)
    frames = to_frames(build_index(tmp_path))
    fd6, fd7 = frames.iloc[0], frames.iloc[1]
    assert fd6["start_utc"] == datetime(2026, 4, 7, 1, 4, 57, 460000, tzinfo=UTC)
    assert fd6["flight_day"] == 6
    assert fd7["start_utc"].date() == fd6["start_utc"].date()
    assert fd7["flight_day"] == 7
    # Long dark-side exposures (integer seconds in the label) parse as floats.
    assert fd6["exposure_s"] == 6.0
    assert fd6["iso"] == 1600
    assert fd6["f_number"] == 2.0
    assert fd6["activity_id"] == "i_Window Team Position Swap"
