"""Groupe 9 : options (ajout, modification, suppression de pièce, réglages globaux).

Le flux d'options utilise self.config_entry fourni par HA >= 2024.11.
Sur HA 2023.7 (seule version testable ici), on émule ce comportement.
"""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_room_manager import config_flow as cf
from custom_components.smart_room_manager.const import DOMAIN
from tests.conftest import room


@pytest.fixture(autouse=True)
def shim_config_entry(monkeypatch):
    if not hasattr(cf.SmartRoomManagerOptionsFlow, "config_entry") or isinstance(
        getattr(cf.SmartRoomManagerOptionsFlow, "config_entry", None), type(None)
    ):
        monkeypatch.setattr(
            cf.SmartRoomManagerOptionsFlow, "config_entry",
            property(lambda self: self.hass.config_entries.async_get_entry(self.handler)),
            raising=False,
        )


ANSWERS = {
    "edit_room_basic": {"room_name": "Renommée", "room_type": "bathroom", "room_icon": "mdi:home"},
    "add_room": {"room_name": "Nouvelle", "room_type": "corridor", "room_icon": "mdi:home"},
    "room_sensors": {"door_window_sensors": ["binary_sensor.w"]},
    "room_actuators": {"lights": ["light.l"], "climate_mode": "fil_pilote", "climate_entity": "climate.fp"},
    "room_light_config": {"light_timeout": 600},
    "room_climate_config": {"climate_window_check": True, "window_delay_open": 3, "window_delay_close": 1, "summer_policy": "eco"},
    "room_climate_advanced": {},
    "fil_pilote_hysteresis": {"hysteresis": 0.4, "min_setpoint": 16, "max_setpoint": 22, "preset_heat": "comfort", "preset_idle": "eco"},
    "fil_pilote_presets": {"preset_comfort": "comfort", "preset_eco": "eco", "preset_night": "away", "preset_away": "away",
                           "preset_window": "none", "external_control_preset": "comfort", "allow_external_in_away": False},
    "thermostat_advanced": {},
    "thermostat_temperatures": {},
    "room_schedule": {"preset_schedule_on": "comfort", "preset_schedule_off": "eco", "ignore_in_away": False},
    "room_control": {"pause_duration_minutes": "60", "pause_infinite": False},
}


async def drive(hass, entry, first_menu, first_answer=None, answers=ANSWERS):
    r = await hass.config_entries.options.async_init(entry.entry_id)
    assert r["type"] == "menu"
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": first_menu})
    if first_answer is not None:
        r = await hass.config_entries.options.async_configure(r["flow_id"], first_answer)
    steps = []
    for _ in range(20):
        if r["type"] != "form":
            break
        steps.append(r["step_id"])
        r = await hass.config_entries.options.async_configure(r["flow_id"], answers[r["step_id"]])
    return r, steps


def entry_with(hass, rooms, data=None):
    e = MockConfigEntry(domain=DOMAIN, data=data or {}, options={"rooms": rooms}, unique_id=DOMAIN)
    e.add_to_hass(hass)
    return e


async def test_modifier_piece(hass, calls):
    e = entry_with(hass, [room()])
    r, steps = await drive(hass, e, "list_rooms", {"room_action": "edit_0"})
    assert r["type"] == "create_entry", steps
    saved = e.options["rooms"][0]
    assert saved["room_id"] == "r1" and saved["room_name"] == "Renommée"
    assert saved["climate_entity"] == "climate.fp" and saved["window_delay_open"] == 3
    assert saved["preset_window"] == "none" and saved["pause_duration_minutes"] in ("60", 60)
    assert "fil_pilote_presets" in steps


async def test_ajouter_piece(hass, calls):
    e = entry_with(hass, [room()])
    r, steps = await drive(hass, e, "add_room", ANSWERS["add_room"])
    assert r["type"] == "create_entry", steps
    assert len(e.options["rooms"]) == 2
    new = e.options["rooms"][1]
    assert new["room_name"] == "Nouvelle" and len(new["room_id"]) == 8


async def test_supprimer_piece(hass, calls):
    e = entry_with(hass, [room(), room(room_id="r2", room_name="Deux")])
    r, _ = await drive(hass, e, "list_rooms", {"room_action": "delete_1"}, {"delete_room": {"confirm": True}})
    assert r["type"] == "create_entry"
    assert [x["room_id"] for x in e.options["rooms"]] == ["r1"]


async def test_supprimer_annule(hass, calls):
    e = entry_with(hass, [room(), room(room_id="r2", room_name="Deux")])
    r, steps = await drive(hass, e, "list_rooms", {"room_action": "delete_1"}, {"delete_room": {"confirm": False}, "list_rooms": {"room_action": "back"}})
    assert len(e.options["rooms"]) == 2


async def test_reglages_globaux(hass, calls):
    e = entry_with(hass, [room()], {"alarm_entity": "alarm_control_panel.a"})
    r, _ = await drive(hass, e, "global_settings",
                       {"alarm_entity": "alarm_control_panel.b", "vmc_entity": "switch.vmc", "vmc_timer": 300})
    assert r["type"] == "create_entry"
    assert e.data["alarm_entity"] == "alarm_control_panel.b" and e.data["vmc_entity"] == "switch.vmc"
    assert e.options["rooms"][0]["room_id"] == "r1"


async def test_thermostat_chemin(hass, calls):
    e = entry_with(hass, [room()])
    ans = dict(ANSWERS)
    ans["room_actuators"] = {"lights": [], "climate_mode": "thermostat_heat", "climate_entity": "climate.th"}
    ans["room_climate_config"] = {"climate_window_check": True, "window_delay_open": 2, "window_delay_close": 2}
    r, steps = await drive(hass, e, "list_rooms", {"room_action": "edit_0"}, ans)
    assert r["type"] == "create_entry", steps
    assert e.options["rooms"][0]["climate_mode"] == "thermostat_heat"
