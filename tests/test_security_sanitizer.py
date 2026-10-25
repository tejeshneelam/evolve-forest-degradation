"""
EvOLve Test Suite — tests/test_security_sanitizer.py
Validates input sanitization against XSS, SQL injection, and invalid bounding box coordinates.
"""

import pytest
from fastapi import HTTPException
from dashboard.backend.utils.sanitizer import (
    sanitize_string,
    validate_coordinates,
    validate_iso_date,
    validate_date_range
)


def test_sanitize_string_strips_xss_and_sqli():
    """Validates that XSS scripts and SQL injection payloads are thoroughly stripped."""
    dirty_xss = "<script>alert('pwned')</script>Forest Region"
    clean_xss = sanitize_string(dirty_xss)
    assert "<script>" not in clean_xss
    assert "alert('pwned')" in clean_xss or "Forest Region" in clean_xss

    dirty_sqli = "Munnar' UNION SELECT * FROM users--"
    clean_sqli = sanitize_string(dirty_sqli)
    assert "UNION SELECT" not in clean_sqli
    assert "--" not in clean_sqli


def test_validate_coordinates_valid():
    """Valid bounding box [min_lon, min_lat, max_lon, max_lat] should pass."""
    bbox = [76.0, 11.5, 76.5, 12.0]
    out = validate_coordinates(bbox)
    assert out == (76.0, 11.5, 76.5, 12.0)


def test_validate_coordinates_out_of_bounds_lat():
    """Latitude beyond [-90, 90] should raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc_info:
        validate_coordinates([76.0, -95.0, 76.5, 12.0])
    assert exc_info.value.status_code == 400
    assert "Latitude" in exc_info.value.detail


def test_validate_coordinates_inverted_min_max():
    """min_lon >= max_lon or min_lat >= max_lat must raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc_info:
        validate_coordinates([76.8, 11.5, 76.2, 12.0])  # min_lon > max_lon
    assert exc_info.value.status_code == 400
    assert "Invalid longitude range" in exc_info.value.detail


def test_validate_coordinates_wrong_length():
    """Bounding box with fewer than 4 coordinates must raise 400."""
    with pytest.raises(HTTPException) as exc_info:
        validate_coordinates([76.0, 11.5, 76.5])
    assert exc_info.value.status_code == 400


def test_validate_iso_date():
    """Validates YYYY-MM and YYYY-MM-DD parsing and rejects invalid dates."""
    assert validate_iso_date("2024-05") == "2024-05"
    assert validate_iso_date("2024-05-15") == "2024-05-15"

    with pytest.raises(HTTPException):
        validate_iso_date("2024-13-40")  # Invalid month/day

    with pytest.raises(HTTPException):
        validate_iso_date("invalid-text")


def test_validate_date_range_inverted():
    """Start date after end date must raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc_info:
        validate_date_range("2025-06-01", "2024-01-01")
    assert exc_info.value.status_code == 400
    assert "must not be after end_date" in exc_info.value.detail
