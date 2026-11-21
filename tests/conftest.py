"""Fixtures communes."""
from __future__ import annotations

from datetime import datetime

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.smart_room_manager.const import DOMAIN
from custom_components.smart_room_manager.coordinator import SmartRoomCoordinator

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def calls(hass):
    """Services simulés, appels enregistrés par (domaine, service)."""
    reg = {}
    for dom, srv in [
        ("climate", "set_preset_mode"),
        ("climate", "set_hvac_mode"),
        ("climate", "set_temperature"),
        ("light", "turn_off"),
        ("light", "turn_on"),
        ("switch", "turn_on"),
        ("switch", "turn_off"),
    ]:
        reg[(dom, srv)] = async_mock_service(hass, dom, srv)
    return reg


def at(h, m=0, s=0, day=20):
    """Heure locale (fuseau HA du test)."""
    return datetime(2026, 11, day, h, m, s, tzinfo=dt_util.DEFAULT_TIME_ZONE)


def room(**kw):
    base = {
        "room_id": "r1",
        "room_name": "Test",
        "room_type": "normal",
        "climate_mode": "none",
        "lights": [],
        "door_window_sensors": [],
    }
    base.update(kw)
    return base


def make_coord(hass, rooms, data=None):
    entry = MockConfigEntry(
        domain=DOMAIN, data=data or {}, options={"rooms": rooms}, unique_id=DOMAIN
    )
    entry.add_to_hass(hass)
    return SmartRoomCoordinator(hass, entry)


def n(calls, dom, srv):
    return len(calls[(dom, srv)])


def last(calls, dom, srv):
    return calls[(dom, srv)][-1].data if calls[(dom, srv)] else None
