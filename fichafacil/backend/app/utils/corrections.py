"""Correction helpers for append-only fichaje reporting."""

from datetime import datetime
from typing import Mapping, Protocol


class HasTimestamp(Protocol):
    id: int
    timestamp: datetime


def get_effective_timestamp(
    fichaje: HasTimestamp,
    approved_corrections_by_fichaje_id: Mapping[int, datetime],
) -> datetime:
    """Return corrected timestamp for display/reporting without mutating the original row."""
    return approved_corrections_by_fichaje_id.get(fichaje.id, fichaje.timestamp)
