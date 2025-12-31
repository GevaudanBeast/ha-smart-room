"""Helper functions for config flow."""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def parse_comfort_ranges(comfort_ranges_text: str) -> list[dict[str, str]]:
    """Parse comfort time ranges from text format.

    Format: "HH:MM-HH:MM,HH:MM-HH:MM"
    Example: "07:00-09:00,18:00-22:00"

    Returns list of dicts with "start" and "end" keys.
    """
    comfort_ranges = []
    if comfort_ranges_text:
        for range_str in comfort_ranges_text.split(","):
            range_str = range_str.strip()
            if "-" in range_str:
                try:
                    start, end = range_str.split("-")
                    comfort_ranges.append(
                        {
                            "start": start.strip(),
                            "end": end.strip(),
                        }
                    )
                except Exception:
                    _LOGGER.warning("Invalid time range format: %s", range_str)
    return comfort_ranges


def format_comfort_ranges(comfort_ranges: list[dict[str, str]]) -> str:
    """Format comfort time ranges to text.

    Converts list of dicts to "HH:MM-HH:MM,HH:MM-HH:MM" format.
    """
    return ",".join(
        [
            f"{r['start']}-{r['end']}"
            for r in comfort_ranges
            if r.get("start") and r.get("end")
        ]
    )


def should_save_field(user_input: dict[str, Any], field_name: str) -> bool:
    """Check if a field should be saved (is configured and non-empty)."""
    value = user_input.get(field_name)
    if value is None:
        return False
    if isinstance(value, (list, tuple)) and len(value) == 0:
        return False
    return True


def build_room_list_choices(rooms: list[dict[str, Any]]) -> dict[str, str]:
    """Build choices dict for room list selection."""
    room_choices = {}
    for idx, room in enumerate(rooms):
        room_name = room.get("room_name", f"Room {idx + 1}")
        room_type = room.get("room_type", "normal")
        room_choices[f"edit_{idx}"] = f"✏️ Modifier: {room_name} ({room_type})"
        room_choices[f"delete_{idx}"] = f"🗑️ Supprimer: {room_name}"
    room_choices["back"] = "⬅️ Retour au menu"
    return room_choices
