"""Fixtures partagées."""

from __future__ import annotations

import pytest

from maturai.referential.loader import load_referential


@pytest.fixture(scope="session")
def referential():
    """Le référentiel par défaut, chargé une fois pour toute la session."""
    return load_referential()
