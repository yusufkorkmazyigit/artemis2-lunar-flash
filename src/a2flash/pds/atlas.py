"""Query the PDS Imaging Atlas search API for crew-camera frames in a time window.

The Atlas index holds every Artemis II product with its label already flattened
(``_source.pds4_label``), plus file locations, sizes and MD5 checksums. One query
therefore gives the ``frames`` table for a time window without downloading labels.

API: ``POST https://pds-imaging.jpl.nasa.gov/api/search/atlas/_search``
(Elasticsearch query DSL). Files: ``GET https://pds-imaging.jpl.nasa.gov/api/data/<uri>``
redirects to the file. Field names below were taken from a real Artemis II hit
(``tests/fixtures/atlas_hit_art002e009300.json``, 2026-11-04).

The query is deliberately loose (``match_phrase``); every hit is checked again
client-side, so an unexpected index mapping can only drop rows, never add wrong ones.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import pandas as pd

from a2flash.pds.download import USER_AGENT
from a2flash.pds.frames import to_frames
from a2flash.pds.labels import parse_utc

log = logging.getLogger(__name__)

SEARCH_URL = "https://pds-imaging.jpl.nasa.gov/api/search/atlas/_search"
DATA_URL = "https://pds-imaging.jpl.nasa.gov/api/data/"
# Each hit carries the whole flattened label (~10-15 kB). 500 hits per page made the API
# answer 502 (2026-11-04, response too large); 100 works. On a 5xx the page is halved.
MIN_PAGE = 10
MIN_SLICE = timedelta(milliseconds=1)

Post = Callable[[str, bytes], bytes]

# raw-row key (as produced by labels.parse_label) -> Atlas ``pds4_label`` key
_LABEL_KEYS = {
    "disc.Surface_Imaging/Instrument_Information/ops_instrument_key": (
        "img_surface:Instrument_Information/img_surface:ops_instrument_key"
    ),
    "disc.Surface_Imaging/Instrument_Information/instrument_serial_number": (
        "img_surface:Instrument_Information/img_surface:instrument_serial_number"
    ),
    "disc.Mission_Information/flight_day_number": "msn:Mission_Information/msn:flight_day_number",
    "disc.Mission_Information/product_type_name": "msn:Mission_Information/msn:product_type_name",
    "disc.Surface_Mission_Information/Observational_Intent/activity_id": (
        "msn_surface:Observational_Intent/msn_surface:activity_id"
    ),
    "disc.Surface_Mission_Information/Observational_Intent/target_id": (
        "msn_surface:Observational_Intent/msn_surface:target_id"
    ),
    "disc.Imaging/Optical_Properties/lens_name": "img:Optical_Properties/img:lens_name",
    "disc.Imaging/Optical_Properties/focal_length": "img:Optical_Properties/img:focal_length",
    "disc.Imaging/Optical_Properties/f_number": "img:Optical_Properties/img:f_number",
    "disc.Imaging/Exposure/exposure_duration": "img:Exposure/img:exposure_duration",
    "disc.Imaging/Detector/ISO/iso_number": "img:ISO/img:iso_number",
    "disc.COTS_Camera/Camera_Settings/shooting_mode": (
        "cots_camera:Camera_Settings/cots_camera:shooting_mode"
    ),
}

#: Extra columns appended to the frames table when it comes from the Atlas.
ATLAS_COLUMNS = ["image_uri", "image_bytes", "image_md5", "label_uri", "label_md5"]


def http_post(url: str, body: bytes, timeout: float = 120.0) -> bytes:
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data: bytes = resp.read()
        return data


def data_url(uri: str) -> str:
    """HTTP URL for an Atlas file URI (the API answers with a redirect to the file)."""
    return DATA_URL + quote(uri, safe=":/")


def _iso(t: datetime) -> str:
    # millisecond precision, matching the index; "Z" suffix
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def build_query(
    start: datetime,
    stop: datetime,
    *,
    bundle: str,
    collection: str,
    size: int,
) -> dict[str, Any]:
    return {
        "size": size,
        "track_total_hits": True,
        "_source": ["uri", "archive", "gather", "pds4_label"],
        "query": {
            "bool": {
                "filter": [
                    {"match_phrase": {"archive.bundle_id": bundle}},
                    {"match_phrase": {"archive.collection_id": collection}},
                    {"match_phrase": {"archive.file_extension": "tif"}},
                    {"range": {"gather.time.start_time": {"gte": _iso(start), "lt": _iso(stop)}}},
                ]
            }
        },
    }


def _first(label: dict[str, Any], key: str) -> Any:
    value = label.get(key)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def hit_to_row(hit: dict[str, Any]) -> dict[str, Any]:
    """Turn one Atlas hit into a raw row with the same keys as ``parse_label``."""
    src = hit["_source"]
    archive, gather, label = src["archive"], src["gather"], src.get("pds4_label", {})
    row: dict[str, Any] = {
        "lid": label.get("lid"),
        "vid": label.get("vid"),
        "lidvid": label.get("lidvid"),
        "start_utc": parse_utc(gather["time"]["start_time"]),
        "file_name": archive.get("name"),
        "bundle_id": archive.get("bundle_id"),
        "collection_id": archive.get("collection_id"),
        "file_extension": archive.get("file_extension"),
        "image_uri": archive.get("uri"),
        "image_bytes": archive.get("size"),
        "image_md5": archive.get("md5"),
        "label_uri": gather.get("pds_archive", {}).get("related", {}).get("label", {}).get("uri"),
        "label_md5": _first(label, "ops:Label_File_Info/ops:md5_checksum"),
    }
    for raw_key, atlas_key in _LABEL_KEYS.items():
        value = _first(label, atlas_key)
        if value is not None:
            row[raw_key] = value
    return row


def _query_slice(
    start: datetime,
    stop: datetime,
    *,
    bundle: str,
    collection: str,
    size: int,
    post: Post,
) -> tuple[int, list[dict[str, Any]]]:
    query = build_query(start, stop, bundle=bundle, collection=collection, size=size)
    resp = json.loads(post(SEARCH_URL, json.dumps(query).encode()))
    return int(resp["hits"]["total"]["value"]), list(resp["hits"]["hits"])


def iter_hits(
    start: datetime,
    stop: datetime,
    *,
    bundle: str = "artemis2_crew_camera",
    collection: str = "data_raw",
    page_size: int = 100,
    post: Post = http_post,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[dict[str, Any]]:
    """Yield every hit in ``[start, stop)`` without relying on from/size paging.

    from/size paging over this index returned repeated hits (and so skipped others,
    2026-11-04). Instead the window is bisected until each slice fits in a single
    response (``total <= page_size``), so every slice is fetched completely in one call.
    """
    pending = [(start, stop)]
    while pending:
        a, b = pending.pop()
        try:
            total, hits = _query_slice(
                a, b, bundle=bundle, collection=collection, size=page_size, post=post
            )
        except urllib.error.HTTPError as exc:
            if exc.code < 500 or page_size <= MIN_PAGE:
                raise
            page_size = max(MIN_PAGE, page_size // 2)
            log.warning("atlas HTTP %d; retrying with page size %d", exc.code, page_size)
            sleep(2.0)
            pending.append((a, b))
            continue
        if total <= page_size:
            if len(hits) != total:
                raise RuntimeError(f"atlas returned {len(hits)} of {total} hits for {a}..{b}")
            log.debug("slice %s .. %s: %d hits", a, b, total)
            yield from hits
            continue
        if b - a <= MIN_SLICE:
            raise RuntimeError(f"{total} hits within {b - a} at {a}; cannot split further")
        mid = a + (b - a) / 2
        mid = mid.replace(microsecond=mid.microsecond // 1000 * 1000)  # index has ms precision
        if mid <= a:
            mid = a + MIN_SLICE
        pending.extend([(mid, b), (a, mid)])  # (a, mid) is popped first: time order


#: A few example ``_id`` values per drop reason, from the last ``search_frames`` call.
DROP_EXAMPLES: dict[str, list[str]] = {}


def _drop_reason(
    row: dict[str, Any], start: datetime, stop: datetime, *, bundle: str, collection: str
) -> str | None:
    if row["bundle_id"] != bundle:
        return f"bundle={row['bundle_id']}"
    if row["collection_id"] != collection:
        return f"collection={row['collection_id']}"
    if row["file_extension"] != "tif":
        return f"extension={row['file_extension']}"
    if row["start_utc"] is None:
        return "no start time"
    if not start <= row["start_utc"] < stop:
        return "outside window"
    if not row["image_uri"]:
        return "no uri"
    return None


def search_frames(
    start: datetime,
    stop: datetime,
    *,
    bundle: str = "artemis2_crew_camera",
    collection: str = "data_raw",
    page_size: int = 100,
    post: Post = http_post,
    sleep: Callable[[float], None] = time.sleep,
) -> pd.DataFrame:
    """Frames (one row per image product) with ``start <= start_utc < stop``."""
    DROP_EXAMPLES.clear()
    rows: dict[str, dict[str, Any]] = {}
    seen_ids: Counter[str] = Counter()
    drops: Counter[str] = Counter()
    n_hits = 0
    for hit in iter_hits(
        start,
        stop,
        bundle=bundle,
        collection=collection,
        page_size=page_size,
        post=post,
        sleep=sleep,
    ):
        n_hits += 1
        seen_ids[str(hit.get("_id"))] += 1
        row = hit_to_row(hit)
        reason = _drop_reason(row, start, stop, bundle=bundle, collection=collection)
        if reason is None and row["image_uri"] in rows:
            reason = "duplicate image_uri"
        if reason is None:
            rows[row["image_uri"]] = row
        else:
            drops[reason] += 1
            if len(DROP_EXAMPLES.setdefault(reason, [])) < 3:
                DROP_EXAMPLES[reason].append(str(hit.get("_id")))

    repeated = sum(c - 1 for c in seen_ids.values() if c > 1)
    log.info(
        "atlas: %d hits read, %d kept, %d dropped %s; same _id returned twice: %d",
        n_hits,
        len(rows),
        sum(drops.values()),
        dict(drops),
        repeated,
    )
    for reason, ids in DROP_EXAMPLES.items():
        log.info("  e.g. %s: %s", reason, ids)
    if repeated:
        log.warning("paging returned %d repeated hits: some frames may be missing", repeated)

    raw = pd.DataFrame(list(rows.values()))
    if raw.empty:
        return pd.DataFrame(columns=[*to_frames(pd.DataFrame({"lid": []})).columns, *ATLAS_COLUMNS])
    raw["start_utc"] = pd.to_datetime(raw["start_utc"], utc=True)
    raw = raw.sort_values(["start_utc", "lidvid"], kind="stable").reset_index(drop=True)
    frames = to_frames(raw)
    frames["image_uri"] = raw["image_uri"].astype("string")
    frames["image_bytes"] = pd.to_numeric(raw["image_bytes"]).astype("Int64")
    frames["image_md5"] = raw["image_md5"].astype("string")
    frames["label_uri"] = raw["label_uri"].astype("string")
    frames["label_md5"] = raw["label_md5"].astype("string")
    return frames
