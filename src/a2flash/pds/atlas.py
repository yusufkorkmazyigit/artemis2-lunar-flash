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
from collections.abc import Callable, Iterator
from datetime import datetime
from typing import Any
from urllib.parse import quote

import pandas as pd

from a2flash.pds.download import USER_AGENT
from a2flash.pds.frames import to_frames
from a2flash.pds.labels import parse_utc

log = logging.getLogger(__name__)

SEARCH_URL = "https://pds-imaging.jpl.nasa.gov/api/search/atlas/_search"
DATA_URL = "https://pds-imaging.jpl.nasa.gov/api/data/"
MAX_WINDOW = 10_000  # Elasticsearch default max_result_window
# Each hit carries the whole flattened label (~10-15 kB). 500 hits per page made the API
# answer 502 (2026-11-04, response too large); 100 works. On a 5xx the page is halved.
MIN_PAGE = 10

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


def build_query(
    start: datetime,
    stop: datetime,
    *,
    bundle: str,
    collection: str,
    size: int,
    offset: int,
) -> dict[str, Any]:
    return {
        "from": offset,
        "size": size,
        "track_total_hits": True,
        "sort": ["_doc"],
        "_source": ["uri", "archive", "gather", "pds4_label"],
        "query": {
            "bool": {
                "filter": [
                    {"match_phrase": {"archive.bundle_id": bundle}},
                    {"match_phrase": {"archive.collection_id": collection}},
                    {"match_phrase": {"archive.file_extension": "tif"}},
                    {
                        "range": {
                            "gather.time.start_time": {
                                "gte": start.isoformat().replace("+00:00", "Z"),
                                "lt": stop.isoformat().replace("+00:00", "Z"),
                            }
                        }
                    },
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
    offset, total = 0, None
    while total is None or offset < total:
        query = build_query(
            start, stop, bundle=bundle, collection=collection, size=page_size, offset=offset
        )
        try:
            resp = json.loads(post(SEARCH_URL, json.dumps(query).encode()))
        except urllib.error.HTTPError as exc:
            if exc.code < 500 or page_size <= MIN_PAGE:
                raise
            page_size = max(MIN_PAGE, page_size // 2)
            log.warning("atlas HTTP %d; retrying with page size %d", exc.code, page_size)
            sleep(2.0)
            continue
        hits = resp["hits"]["hits"]
        if total is None:
            total = int(resp["hits"]["total"]["value"])
            log.info("atlas: %d hits for %s .. %s", total, start, stop)
            if total > MAX_WINDOW:
                raise RuntimeError(
                    f"{total} hits exceed the API paging window ({MAX_WINDOW}); "
                    "split the time range"
                )
        if not hits:
            break
        yield from hits
        offset += len(hits)


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
    rows: dict[str, dict[str, Any]] = {}
    for hit in iter_hits(
        start,
        stop,
        bundle=bundle,
        collection=collection,
        page_size=page_size,
        post=post,
        sleep=sleep,
    ):
        row = hit_to_row(hit)
        ok = (
            row["bundle_id"] == bundle
            and row["collection_id"] == collection
            and row["file_extension"] == "tif"
            and row["start_utc"] is not None
            and start <= row["start_utc"] < stop
        )
        if ok and row["image_uri"]:
            rows[row["image_uri"]] = row  # de-duplicate across pages
        elif not ok:
            log.debug("dropped hit outside filter: %s", hit.get("_id"))

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
