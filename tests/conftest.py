"""
EvOLve Test Suite — tests/conftest.py
Global fixtures and TestClient configuration for FastAPI testing.
"""

import pytest
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from dashboard.backend.main import app


@pytest.fixture(scope="session")
def client():
    """Session-wide FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client
