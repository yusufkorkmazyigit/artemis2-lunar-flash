"""Parse a single PDS4 XML label into a flat, table-ready dictionary.

Design notes
------------
* Only PDS4 *core* elements are read by name (Identification_Area,
  Observation_Area/Time_Coordinates, File_Area_*/File). Their structure is
  fixed by the PDS4 Information Model, so these lookups are safe.
* Mission- and discipline-specific elements (camera, lens, exposure, ...) live
  under ``Discipline_Area`` / ``Mission_Area`` and use Artemis II local
  dictionaries we have not yet verified against real labels. Instead of
  guessing element names, every leaf under those areas is flattened into a
  ``disc.<path>`` key. Week 2 maps the verified keys to the ``frames`` schema.
* All times are returned as timezone-aware UTC ``datetime`` objects.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lxml import etree

PDS4_NS = "http://pds.nasa.gov/pds4/pds/v1"
_NS = {"pds": PDS4_NS}

# Hardened parser: no external entities, no network access (labels are untrusted input).
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, remove_comments=True)

_EXTRA_AREAS = ("Discipline_Area", "Mission_Area")


class LabelParseError(ValueError):
    """Raised when a file is not a usable PDS4 product label."""


def _local(tag: object) -> str:
    """Return the local name of an lxml tag (drops the ``{namespace}`` prefix)."""
    return etree.QName(tag).localname if isinstance(tag, str) else ""


def _text(root: etree._Element, xpath: str) -> str | None:
    node = root.find(xpath, _NS)
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def parse_utc(value: str | None) -> datetime | None:
    """Parse a PDS4 ``date_time_utc`` string into an aware UTC datetime.

    PDS4 requires UTC with a trailing ``Z``. A naive timestamp is treated as an
    error rather than silently assumed to be UTC.
    """
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise LabelParseError(f"Unparseable UTC time: {value!r}") from exc
    if parsed.tzinfo is None:
        raise LabelParseError(f"Time without timezone (PDS4 requires 'Z'): {value!r}")
    return parsed.astimezone(UTC)


def _flatten_area(area: etree._Element, prefix: str) -> dict[str, str]:
    """Flatten leaf elements of a discipline/mission area into path keys.

    Repeated paths get an ``[i]`` suffix so no value is ever overwritten.
    A ``unit`` attribute is kept as ``<key>@unit``.
    """
    out: dict[str, str] = {}
    seen: Counter[str] = Counter()
    for node in area.iter():
        if not isinstance(node.tag, str) or len(node):
            continue  # skip comments/PIs and non-leaf elements
        if node.text is None or not node.text.strip():
            continue
        # path from just below the area down to this leaf
        parts = [_local(node.tag)]
        for ancestor in node.iterancestors():
            if ancestor is area:
                break
            parts.append(_local(ancestor.tag))
        parts.reverse()
        key = f"{prefix}." + "/".join(parts)
        seen[key] += 1
        if seen[key] > 1:
            key = f"{key}[{seen[key] - 1}]"
        out[key] = node.text.strip()
        unit = node.get("unit")
        if unit:
            out[f"{key}@unit"] = unit
    return out


def parse_label(path: str | Path) -> dict[str, Any]:
    """Parse one PDS4 product label.

    Returns a flat dict with core keys (``lid``, ``vid``, ``lidvid``,
    ``product_class``, ``title``, ``start_utc``, ``stop_utc``, ``file_name``,
    ``label_path``) plus ``disc.*`` keys for discipline/mission metadata.
    """
    path = Path(path)
    try:
        root = etree.parse(str(path), _PARSER).getroot()
    except (OSError, etree.XMLSyntaxError) as exc:
        raise LabelParseError(f"Cannot read XML label {path}: {exc}") from exc

    if etree.QName(root).namespace != PDS4_NS:
        raise LabelParseError(f"Not a PDS4 label (root namespace): {path}")

    lid = _text(root, "pds:Identification_Area/pds:logical_identifier")
    vid = _text(root, "pds:Identification_Area/pds:version_id")
    if lid is None or vid is None:
        raise LabelParseError(f"Missing logical_identifier or version_id: {path}")

    time_xp = "pds:Observation_Area/pds:Time_Coordinates/pds:"
    file_nodes = root.findall(".//pds:File/pds:file_name", _NS)

    row: dict[str, Any] = {
        "lid": lid,
        "vid": vid,
        "lidvid": f"{lid}::{vid}",
        "product_class": _local(root.tag),
        "title": _text(root, "pds:Identification_Area/pds:title"),
        "start_utc": parse_utc(_text(root, time_xp + "start_date_time")),
        "stop_utc": parse_utc(_text(root, time_xp + "stop_date_time")),
        "file_name": file_nodes[0].text.strip() if file_nodes and file_nodes[0].text else None,
        "label_path": str(path),
    }

    obs = root.find("pds:Observation_Area", _NS)
    if obs is not None:
        for area_name in _EXTRA_AREAS:
            area = obs.find(f"pds:{area_name}", _NS)
            if area is not None:
                row.update(_flatten_area(area, prefix="disc"))
    return row
