"""
EvOLve Security Hardening — dashboard/backend/utils/sanitizer.py
Input sanitization and validation utilities to defend against XSS, SQLi,
malformed geographic coordinates, and path traversal vectors.
"""

import re
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException


DATE_REGEX = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?$")
HTML_TAG_REGEX = re.compile(r"<[^>]*?>")
DANGEROUS_PATTERNS = re.compile(
    r"(?:<script|javascript:|onerror=|onload=|eval\(|UNION\s+SELECT|--|\bDROP\b|\bINSERT\b)",
    re.IGNORECASE
)


def sanitize_string(text: Optional[str], max_length: int = 120) -> Optional[str]:
    """
    Sanitizes string inputs by stripping HTML tags, removing dangerous injection patterns,
    and enforcing maximum length constraints.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)

    # Strip dangerous HTML tags
    cleaned = HTML_TAG_REGEX.sub("", text)
    # Strip script and injection patterns
    cleaned = DANGEROUS_PATTERNS.sub("", cleaned)
    # Strip null bytes and non-printable control characters
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in " \t\n")
    cleaned = cleaned.strip()

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


def validate_coordinates(bbox: List[float]) -> List[float]:
    """
    Validates geographic bounding box [min_lon, min_lat, max_lon, max_lat].
    Enforces WGS84 range: latitude in [-90, 90], longitude in [-180, 180],
    and strictly min < max.
    """
    if not bbox or len(bbox) != 4:
        raise HTTPException(
            status_code=400,
            detail="Bounding box must be an array of exactly 4 numeric coordinates: [min_lon, min_lat, max_lon, max_lat]."
        )

    try:
        min_lon = float(bbox[0])
        min_lat = float(bbox[1])
        max_lon = float(bbox[2])
        max_lat = float(bbox[3])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Bounding box coordinates must be valid floating point numbers."
        )

    if not (-90.0 <= min_lat <= 90.0) or not (-90.0 <= max_lat <= 90.0):
        raise HTTPException(
            status_code=400,
            detail=f"Latitude coordinates out of bounds [-90.0, 90.0]: min_lat={min_lat}, max_lat={max_lat}"
        )

    if min_lat >= max_lat:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid latitude range: min_lat ({min_lat}) must be strictly less than max_lat ({max_lat})."
        )

    if not (-180.0 <= min_lon <= 180.0) or not (-180.0 <= max_lon <= 180.0):
        raise HTTPException(
            status_code=400,
            detail=f"Longitude coordinates out of bounds [-180.0, 180.0]: min_lon={min_lon}, max_lon={max_lon}"
        )

    if min_lon >= max_lon:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid longitude range: min_lon ({min_lon}) must be strictly less than max_lon ({max_lon})."
        )

    return min_lon, min_lat, max_lon, max_lat


def validate_iso_date(date_str: Optional[str], field_name: str = "date") -> Optional[str]:
    """
    Validates ISO calendar date format (YYYY-MM or YYYY-MM-DD) with calendar validation.
    """
    if not date_str:
        return None

    date_str = date_str.strip()
    if not DATE_REGEX.match(date_str):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format '{date_str}'. Must follow ISO YYYY-MM or YYYY-MM-DD."
        )

    try:
        if len(date_str) == 7:
            datetime.strptime(date_str, "%Y-%m")
        else:
            datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid calendar date for {field_name}: {str(e)}"
        )

    return date_str


def validate_date_range(start_date: Optional[str], end_date: Optional[str]):
    """
    Ensures start_date <= end_date when both are specified.
    Supports both YYYY-MM and YYYY-MM-DD format.
    """
    v_start = validate_iso_date(start_date, "start_date")
    v_end = validate_iso_date(end_date, "end_date")

    if v_start and v_end:
        dt_s_str = v_start if len(v_start) == 10 else f"{v_start}-01"
        dt_e_str = v_end if len(v_end) == 10 else f"{v_end}-01"
        dt_start = datetime.strptime(dt_s_str, "%Y-%m-%d")
        dt_end = datetime.strptime(dt_e_str, "%Y-%m-%d")
        if dt_start > dt_end:
            raise HTTPException(
                status_code=400,
                detail=f"start_date ({v_start}) must not be after end_date ({v_end})."
            )

    return v_start, v_end
