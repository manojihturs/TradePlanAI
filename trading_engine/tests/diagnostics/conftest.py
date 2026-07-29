"""Shared fixtures for the diagnostics test suite."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest


@pytest.fixture
def valid_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def another_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def valid_datetime() -> datetime:
    return datetime(2026, 7, 3, 9, 20, 0)  # noqa: DTZ001
