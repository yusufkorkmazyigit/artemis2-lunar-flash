from __future__ import annotations

import urllib.error
from pathlib import Path

import pytest

from a2flash.pds.download import download_labels, list_labels

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://example.org/artemis2_crew_camera/data_raw/fd06/"
LABEL = (FIXTURES / "art002e009291_nkz9019_raw_v01.xml").read_bytes()

# Shaped like an Apache autoindex page.
INDEX = """<html><body><h1>Index of /fd06</h1><table>
<tr><td><a href="../">Parent Directory</a></td></tr>
<tr><td><a href="art002e009291_nkz9019_raw_v01.tif">art002e009291_nkz9019_raw_v01.tif</a></td></tr>
<tr><td><a href="art002e009291_nkz9019_raw_v01.xml">art002e009291_nkz9019_raw_v01.xml</a></td></tr>
<tr><td><a href="art002e009300_nkz9019_raw_v01.xml">art002e009300_nkz9019_raw_v01.xml</a></td></tr>
<tr><td><a href="/abs/art002e000002_nkd5015_raw_v01.xml">abs</a></td></tr>
<tr><td><a href="collection_data_raw.xml">collection_data_raw.xml</a></td></tr>
<tr><td><a href="?C=N;O=D">Name</a></td></tr>
</table></body></html>"""


class FakeServer:
    def __init__(self, pages: dict[str, bytes | Exception]) -> None:
        self.pages = pages
        self.calls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.calls.append(url)
        page = self.pages.get(url)
        if page is None:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)  # type: ignore[arg-type]
        if isinstance(page, Exception):
            raise page
        return page


def _no_sleep(_: float) -> None:
    pass


def test_list_labels_keeps_only_product_labels() -> None:
    urls = list_labels(INDEX, BASE.rstrip("/"))
    assert urls == [
        BASE + "art002e009291_nkz9019_raw_v01.xml",
        BASE + "art002e009300_nkz9019_raw_v01.xml",
        "https://example.org/abs/art002e000002_nkd5015_raw_v01.xml",
    ]


def test_download_skips_existing_and_reports_failures(tmp_path: Path) -> None:
    server = FakeServer(
        {
            BASE: INDEX.encode(),
            BASE + "art002e009291_nkz9019_raw_v01.xml": LABEL,
            BASE + "art002e009300_nkz9019_raw_v01.xml": b"<not-closed",
        }
    )
    stats = download_labels(BASE, tmp_path, fetch=server, sleep=_no_sleep, retries=0)
    assert (stats.downloaded, stats.skipped, stats.failed) == (1, 0, 2)  # bad XML + 404
    assert (tmp_path / "art002e009291_nkz9019_raw_v01.xml").read_bytes() == LABEL
    assert not list(tmp_path.glob("*.part"))

    # Second run: the good label is skipped, not fetched again.
    server.calls.clear()
    stats = download_labels(BASE, tmp_path, fetch=server, sleep=_no_sleep, retries=0)
    assert stats.skipped == 1
    assert BASE + "art002e009291_nkz9019_raw_v01.xml" not in server.calls


def test_transient_errors_are_retried(tmp_path: Path) -> None:
    url = BASE + "art002e009291_nkz9019_raw_v01.xml"
    attempts = iter([urllib.error.URLError("reset"), LABEL])

    def flaky(u: str) -> bytes:
        if u == BASE:
            return INDEX.encode()
        if u == url:
            nxt = next(attempts)
            if isinstance(nxt, Exception):
                raise nxt
            return nxt
        raise urllib.error.HTTPError(u, 404, "Not Found", None, None)  # type: ignore[arg-type]

    sleeps: list[float] = []
    stats = download_labels(BASE, tmp_path, fetch=flaky, sleep=sleeps.append, retries=2)
    assert stats.downloaded == 1
    assert 1.0 in sleeps  # one backoff before the successful retry


def test_rate_limit_spaces_requests(tmp_path: Path) -> None:
    now = [0.0]
    sleeps: list[float] = []

    def sleep(dt: float) -> None:
        sleeps.append(dt)
        now[0] += dt

    server = FakeServer({BASE: INDEX.encode(), BASE + "art002e009291_nkz9019_raw_v01.xml": LABEL})
    download_labels(
        BASE,
        tmp_path,
        fetch=server,
        sleep=sleep,
        clock=lambda: now[0],
        retries=0,
        limit=1,
        max_requests_per_second=2.0,
    )
    assert sleeps == [0.5]  # index at t=0, label at t=0.5


def test_rejects_non_http_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="http"):
        download_labels("file:///etc/", tmp_path)
