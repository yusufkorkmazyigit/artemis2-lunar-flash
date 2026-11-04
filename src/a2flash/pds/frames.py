"""Map raw label rows (``parse_label`` output) to the ``frames`` table schema.

Key paths below were verified against real Artemis II crew-camera labels
(Nikon D5 SN 3500015 and 3500017, Nikon Z9 SN 3920019; fd06, 2026-11-04).
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from pandas.api.types import pandas_dtype

_D = "disc."
_IMG = _D + "Imaging/"
_MSN = _D + "Mission_Information/"
_INTENT = _D + "Surface_Mission_Information/Observational_Intent/"
_INSTR = _D + "Surface_Imaging/Instrument_Information/"

# Product ids look like ``art002e009291_nkz9019_raw.tif``: <product_id>_<camera>_<level>
_LID_RE = re.compile(r":(?P<product_id>art002[em]\d+)_(?P<camera>[a-z0-9]+)_")

#: frames column -> (source key, dtype). ``None`` source = derived below.
FRAME_COLUMNS: dict[str, tuple[str | None, str]] = {
    "lidvid": ("lidvid", "string"),
    "product_id": (None, "string"),
    "camera": (None, "string"),
    "camera_model": (_INSTR + "ops_instrument_key", "string"),
    "serial_number": (_INSTR + "instrument_serial_number", "string"),
    "start_utc": ("start_utc", "datetime64[ns, UTC]"),
    "flight_day": (_MSN + "flight_day_number", "Int64"),
    "activity_id": (_INTENT + "activity_id", "string"),
    "target_id": (_INTENT + "target_id", "string"),
    "lens": (_IMG + "Optical_Properties/lens_name", "string"),
    "focal_mm": (_IMG + "Optical_Properties/focal_length", "Float64"),
    "f_number": (_IMG + "Optical_Properties/f_number", "Float64"),
    "exposure_s": (_IMG + "Exposure/exposure_duration", "Float64"),
    "iso": (_IMG + "Detector/ISO/iso_number", "Int64"),
    "shooting_mode": (_D + "COTS_Camera/Camera_Settings/shooting_mode", "string"),
    "processing_level": (_MSN + "product_type_name", "string"),
    "file_name": ("file_name", "string"),
}

# Units we rely on; a label using a different unit would silently corrupt the column.
_EXPECTED_UNITS = {
    _IMG + "Optical_Properties/focal_length": "mm",
    _IMG + "Exposure/exposure_duration": "s",
}


def _ids_from_lid(lid: Any) -> tuple[str | None, str | None]:
    m = _LID_RE.search(lid) if isinstance(lid, str) else None
    return (m["product_id"], m["camera"]) if m else (None, None)


def to_frames(raw: pd.DataFrame) -> pd.DataFrame:
    """Select, rename and type the ``frames`` columns from a raw label index.

    Missing source keys become nulls (not every product has e.g. ``target_id``).
    Rows keep the input order, which ``build_index`` sorts by ``start_utc``.
    """
    for key, unit in _EXPECTED_UNITS.items():
        ukey = key + "@unit"
        if ukey in raw:
            bad = raw[ukey].dropna()
            bad = bad[bad != unit]
            if not bad.empty:
                raise ValueError(f"{key}: expected unit {unit!r}, got {sorted(set(bad))}")

    out = pd.DataFrame(index=raw.index)
    ids = raw["lid"].map(_ids_from_lid) if "lid" in raw else pd.Series(dtype=object)
    for col, (src, dtype) in FRAME_COLUMNS.items():
        if col == "product_id":
            values = ids.map(lambda t: t[0])
        elif col == "camera":
            values = ids.map(lambda t: t[1])
        elif src in raw:
            values = raw[src]
        else:
            values = pd.Series(pd.NA, index=raw.index)
        if dtype.startswith("datetime"):
            out[col] = pd.to_datetime(values, utc=True)
        elif dtype in ("Int64", "Float64"):
            out[col] = pd.to_numeric(values, errors="raise").astype(pandas_dtype(dtype))
        else:
            out[col] = values.astype(pandas_dtype(dtype)).str.strip()
    return out.reset_index(drop=True)
