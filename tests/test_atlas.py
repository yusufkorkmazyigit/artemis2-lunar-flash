from __future__ import annotations

import copy
import json
import shutil
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from a2flash.cli import main
from a2flash.pds import atlas
from a2flash.pds.atlas import data_url, hit_to_row, search_frames
from a2flash.pds.frames import to_frames
from a2flash.pds.index import build_index

FIXTURES = Path(__file__).parent / "fixtures"
HIT: dict[str, Any] = json.loads((FIXTURES / "atlas_hit_art002e009300.json").read_text())["hits"][
    "hits"
][0]
START = datetime(2026, 4, 7, 0, 30, tzinfo=UTC)
STOP = datetime(2026, 4, 7, 3, 0, tzinfo=UTC)


def _hit(product: str, time: str, **archive: Any) -> dict[str, Any]:
    h = copy.deepcopy(HIT)
    src = h["_source"]
    uri = src["archive"]["uri"].replace("art002e009300", product)
    src["archive"].update(uri=uri, name=uri.rsplit("/", 1)[1], **archive)
    src["gather"]["time"]["start_time"] = time
    src["pds4_label"]["lidvid"] = src["pds4_label"]["lidvid"].replace("art002e009300", product)
    src["pds4_label"]["lid"] = src["pds4_label"]["lid"].replace("art002e009300", product)
    return h


class FakeAtlas:
    def __init__(self, hits: list[dict[str, Any]], total: int | None = None) -> None:
        self.hits, self.total = hits, total
        self.queries: list[dict[str, Any]] = []

    def __call__(self, url: str, body: bytes) -> bytes:
        assert url == atlas.SEARCH_URL
        q = json.loads(body)
        self.queries.append(q)
        page = self.hits[q["from"] : q["from"] + q["size"]]
        total = self.total if self.total is not None else len(self.hits)
        return json.dumps({"hits": {"total": {"value": total}, "hits": page}}).encode()


def test_atlas_row_matches_label_parser(tmp_path: Path) -> None:
    # Same product via the API and via its label must give the same frames row.
    shutil.copy(FIXTURES / "art002e009300_nkz9019_raw_v01.xml", tmp_path)
    from_label = to_frames(build_index(tmp_path)).iloc[0]
    raw = pd.DataFrame([hit_to_row(HIT)])
    from_api = to_frames(raw).iloc[0]
    for col in from_label.index:
        if col == "file_name":
            continue  # label: data file name; API: same
        a, b = from_label[col], from_api[col]
        assert (pd.isna(a) and pd.isna(b)) or a == b, col
    assert from_api["file_name"] == from_label["file_name"]


def test_search_pages_filters_and_sorts() -> None:
    hits = [
        _hit("art002e000003", "2026-04-07T02:00:00.000Z"),
        _hit("art002e000001", "2026-04-07T01:00:00.000Z"),
        _hit("art002e000002", "2026-04-07T05:00:00.000Z"),  # outside window
        _hit("art002e000004", "2026-04-07T01:30:00.000Z", bundle_id="other"),  # wrong bundle
        _hit("art002e000005", "2026-04-07T01:45:00.000Z"),
    ]
    fake = FakeAtlas(hits)
    df = search_frames(START, STOP, page_size=2, post=fake)

    assert [q["from"] for q in fake.queries] == [0, 2, 4]
    assert list(df["product_id"]) == ["art002e000001", "art002e000005", "art002e000003"]
    assert df["start_utc"].is_monotonic_increasing
    assert df.loc[0, "image_md5"] == "df2edbf850381172fab1733ac68db287"
    assert df.loc[0, "image_bytes"] == 91412576
    assert df.loc[0, "label_md5"] == "0a2dc83c3975bfe569ab5194625c9292"
    assert df.loc[0, "label_uri"].endswith(".xml")
    assert df.loc[0, "image_uri"].endswith("/fd06/art002e000001_nkz9019_raw_v01.tif")

    rng = fake.queries[0]["query"]["bool"]["filter"][3]["range"]["gather.time.start_time"]
    assert rng == {"gte": "2026-04-07T00:30:00Z", "lt": "2026-04-07T03:00:00Z"}


def test_too_many_hits_raises() -> None:
    with pytest.raises(RuntimeError, match="split the time range"):
        search_frames(START, STOP, post=FakeAtlas([HIT], total=20_000))


def test_empty_result_has_schema() -> None:
    df = search_frames(START, STOP, post=FakeAtlas([]))
    assert df.empty
    assert {"product_id", "activity_id", "image_uri", "label_md5"} <= set(df.columns)


def test_data_url() -> None:
    uri = HIT["_source"]["archive"]["uri"]
    assert data_url(uri) == (
        "https://pds-imaging.jpl.nasa.gov/api/data/atlas:pds4:artemis2:artemis2:"
        "/artemis2_crew_camera/data_raw/fd06/art002e009300_nkz9019_raw_v01.tif"
    )


def test_cli_atlas_frames(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeAtlas([HIT])
    monkeypatch.setattr(atlas, "http_post", fake)
    monkeypatch.setattr(
        "a2flash.cli.search_frames",
        lambda *a, **k: search_frames(*a, **{**k, "post": fake}),
    )
    out = tmp_path / "eclipse.csv"
    rc = main(
        [
            "atlas-frames",
            "--start",
            "2026-04-07T00:30:00Z",
            "--stop",
            "2026-04-07T03:00:00Z",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert pd.read_csv(out)["activity_id"].tolist() == ["i_Window Team Position Swap"]


def test_5xx_halves_page_size() -> None:
    hits = [_hit(f"art002e00000{i}", f"2026-04-07T01:0{i}:00.000Z") for i in range(1, 6)]
    fake = FakeAtlas(hits)
    sizes: list[int] = []

    def picky(url: str, body: bytes) -> bytes:
        size = json.loads(body)["size"]
        sizes.append(size)
        if size > 15:
            raise urllib.error.HTTPError(url, 502, "Bad Gateway", None, None)  # type: ignore[arg-type]
        return fake(url, body)

    df = search_frames(START, STOP, page_size=40, post=picky, sleep=lambda _: None)
    assert len(df) == 5
    assert sizes[:3] == [40, 20, 10]


def test_4xx_is_not_retried() -> None:
    def bad(url: str, body: bytes) -> bytes:
        raise urllib.error.HTTPError(url, 400, "Bad Request", None, None)  # type: ignore[arg-type]

    with pytest.raises(urllib.error.HTTPError):
        search_frames(START, STOP, post=bad, sleep=lambda _: None)
