"""Polite, resumable download of PDS4 labels from a web directory listing.

The collection inventory CSV lists LIDVIDs only, not the ``fdXX`` folder a product
lives in, so URLs cannot be built from it. Instead we read the HTML index of one
flight-day folder (e.g. ``.../artemis2_crew_camera/data_raw/fd06/``), keep the
product labels (``*.xml``) and download only those. Images are never fetched here.

* Resumable: a label already on disk that parses as XML is skipped.
* Atomic: each file is written to ``<name>.part`` and renamed when complete.
* Polite: requests are rate-limited and retried with backoff on transient errors.
* Stdlib only (``urllib``), so it runs on a bare server without extra packages.
"""

from __future__ import annotations

import logging
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from lxml import etree

log = logging.getLogger(__name__)

USER_AGENT = "a2flash (+https://github.com/yusufkorkmazyigit/artemis2-lunar-flash)"

# Product labels only: art002e009291_nkz9019_raw_v01.xml (not collection_*.xml)
LABEL_RE = re.compile(r"^art002[em]\d+_[a-z0-9]+_[a-z]+_v\d+\.xml$")

Fetch = Callable[[str], bytes]


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def list_labels(index_html: str, base_url: str) -> list[str]:
    """Return absolute URLs of product labels linked from a directory index page."""
    if not base_url.endswith("/"):
        base_url += "/"
    parser = _LinkParser()
    parser.feed(index_html)
    urls: dict[str, None] = {}  # ordered de-duplication
    for href in parser.hrefs:
        url = urljoin(base_url, href)
        name = unquote(Path(urlparse(url).path).name)
        if LABEL_RE.match(name):
            urls[url] = None
    return list(urls)


def _is_valid_xml(path: Path) -> bool:
    try:
        etree.parse(str(path), etree.XMLParser(resolve_entities=False, no_network=True))
    except (OSError, etree.XMLSyntaxError):
        return False
    return True


def http_fetch(url: str, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data: bytes = resp.read()
        return data


@dataclass
class DownloadStats:
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0


class _RateLimiter:
    def __init__(
        self, per_second: float, clock: Callable[[], float], sleep: Callable[[float], None]
    ):
        self.interval = 1.0 / per_second if per_second > 0 else 0.0
        self.clock, self.sleep = clock, sleep
        self._next = 0.0

    def wait(self) -> None:
        now = self.clock()
        if now < self._next:
            self.sleep(self._next - now)
            now = self._next
        self._next = now + self.interval


def _fetch_with_retry(
    fetch: Fetch, url: str, limiter: _RateLimiter, sleep: Callable[[float], None], retries: int
) -> bytes:
    for attempt in range(retries + 1):
        limiter.wait()
        try:
            return fetch(url)
        except urllib.error.HTTPError as exc:
            if exc.code < 500 and exc.code != 429:
                raise  # 404 etc.: retrying will not help
            err: Exception = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            err = exc
        if attempt == retries:
            raise err
        backoff = 2.0**attempt
        log.warning("retry %d/%d for %s in %.0fs: %s", attempt + 1, retries, url, backoff, err)
        sleep(backoff)
    raise AssertionError("unreachable")


def download_labels(
    folder_url: str,
    out_dir: str | Path,
    *,
    max_requests_per_second: float = 2.0,
    retries: int = 3,
    limit: int | None = None,
    fetch: Fetch = http_fetch,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> DownloadStats:
    """Download every product label linked from ``folder_url`` into ``out_dir``."""
    if urlparse(folder_url).scheme not in ("https", "http"):
        raise ValueError(f"folder_url must be http(s): {folder_url!r}")
    if not folder_url.endswith("/"):
        folder_url += "/"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    limiter = _RateLimiter(max_requests_per_second, clock, sleep)

    index = _fetch_with_retry(fetch, folder_url, limiter, sleep, retries)
    urls: Iterable[str] = list_labels(index.decode("utf-8", errors="replace"), folder_url)
    urls = list(urls)[:limit] if limit is not None else list(urls)
    log.info("%d labels listed in %s", len(urls), folder_url)

    stats = DownloadStats()
    for i, url in enumerate(urls, 1):
        target = out / unquote(Path(urlparse(url).path).name)
        if target.exists() and _is_valid_xml(target):
            stats.skipped += 1
            continue
        try:
            data = _fetch_with_retry(fetch, url, limiter, sleep, retries)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            log.error("failed %s: %s", url, exc)
            stats.failed += 1
            continue
        part = target.with_name(target.name + ".part")
        part.write_bytes(data)
        if not _is_valid_xml(part):
            log.error("not valid XML, discarded: %s", url)
            part.unlink()
            stats.failed += 1
            continue
        part.replace(target)
        stats.downloaded += 1
        if i % 100 == 0:
            log.info("%d/%d", i, len(urls))
    return stats
