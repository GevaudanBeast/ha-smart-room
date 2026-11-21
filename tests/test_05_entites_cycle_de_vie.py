"""Groupes 8 et 9 : entités, services, configuration et cycle de vie."""
from datetime import timedelta

from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from homeassistant.util import dt as dt_util

from custom_components.smart_room_manager.const import DOMAIN
from tests.conftest import at, n, room

FP = "climate.fp"


async def setup_srm(hass, rooms, data=None):
    entry = MockConfigEntry(domain=DOMAIN, data=data or {}, options={"rooms": rooms}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def fp(hass, preset="comfort"):
    hass.states.async_set(FP, "heat", {"preset_modes": ["comfort", "eco", "away", "none"], "preset_mode": preset})


async def test_entites_creees(hass, freezer, calls):
    freezer.move_to(at(15))
    await setup_srm(hass, [room(), room(room_id="r2", room_name="Deux")])
    ids = [e for e in hass.states.async_entity_ids() if "smart_room" in e]
    # 12 par pièce, + 1 capteur global « Anomalies » depuis la v0.3.9
    assert len([i for i in ids if "anomalies" not in i]) == 24
    for suffix in ["state", "current_priority", "hysteresis_state", "activite"]:
        assert f"sensor.smart_room_test_test_{suffix}" in ids
    for suffix in ["occupied", "light_needed", "external_control_active", "schedule_active", "timer_lumiere", "vmc_grande_vitesse"]:
        assert f"binary_sensor.smart_room_test_test_{suffix}" in ids
    for suffix in ["automation", "pause"]:
        assert f"switch.smart_room_test_test_{suffix}" in ids


async def test_valeurs_capteurs(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    hass.states.async_set("calendar.c", "on")
    await setup_srm(hass, [room(climate_mode="fil_pilote", climate_entity=FP, schedule_entity="calendar.c")])
    assert hass.states.get("sensor.smart_room_test_test_state").state == "comfort"
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state == "schedule"
    assert hass.states.get("sensor.smart_room_test_test_activite").state == "Selon planning"
    assert hass.states.get("binary_sensor.smart_room_test_test_schedule_active").state == "on"
    assert hass.states.get("binary_sensor.smart_room_test_test_occupied").state == "on"
    assert hass.states.get("binary_sensor.smart_room_test_test_light_needed").state == "off"
    assert n(calls, "climate", "set_preset_mode") == 1


async def test_switch_automation_off(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    await setup_srm(hass, [room(climate_mode="fil_pilote", climate_entity=FP)])
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.smart_room_test_test_automation"}, blocking=True)
    # le service switch.turn_off est simulé par la fixture calls : on agit sur l'entité directement
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_automation")
    await ent.async_turn_off()
    await hass.async_block_till_done()
    fp(hass, "comfort")
    before = n(calls, "climate", "set_preset_mode")
    freezer.tick(timedelta(seconds=31)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert n(calls, "climate", "set_preset_mode") == before
    assert hass.states.get("sensor.smart_room_test_test_activite").state == "Automation désactivée"


async def test_pause_minutee_s_arrete(hass, freezer, calls):
    freezer.move_to(at(15))
    await setup_srm(hass, [room(pause_duration_minutes=15)])
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_pause")
    await ent.async_turn_on(); await hass.async_block_till_done()
    st = hass.states.get("switch.smart_room_test_test_pause")
    assert st.state == "on" and st.attributes["remaining_minutes"] in (14, 15)
    freezer.tick(timedelta(minutes=16)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert hass.states.get("switch.smart_room_test_test_pause").state == "off"


async def test_pause_infinie(hass, freezer, calls):
    freezer.move_to(at(15))
    await setup_srm(hass, [room(pause_infinite=True)])
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_pause")
    await ent.async_turn_on(); await hass.async_block_till_done()
    freezer.tick(timedelta(hours=10)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert hass.states.get("switch.smart_room_test_test_pause").state == "on"


async def test_timer_lumiere_capteur(hass, freezer, calls):
    freezer.move_to(at(15))
    hass.states.async_set("light.l", "on")
    await setup_srm(hass, [room(room_type="corridor", lights=["light.l"])])
    st = hass.states.get("binary_sensor.smart_room_test_test_timer_lumiere")
    assert st.state == "on" and st.attributes["timeout_seconds"] == 300


async def test_service_cleanup(hass, freezer, calls):
    freezer.move_to(at(15))
    from homeassistant.setup import async_setup_component
    assert await async_setup_component(hass, "persistent_notification", {})
    entry = await setup_srm(hass, [room()])
    reg = er.async_get(hass)
    reg.async_get_or_create("sensor", DOMAIN, "smart_room_old_state", config_entry=entry)
    await hass.services.async_call(DOMAIN, "cleanup_entities", {}, blocking=True)
    uids = {e.unique_id for e in reg.entities.values() if e.platform == DOMAIN}
    assert "smart_room_old_state" not in uids
    assert "smart_room_r1_state" in uids


async def test_migration_valeurs_none(hass, freezer, calls):
    freezer.move_to(at(15))
    entry = await setup_srm(hass, [room(lights=None, door_window_sensors=None, climate_entity=None)])
    r = entry.options["rooms"][0]
    assert "lights" not in r and "door_window_sensors" not in r and "climate_entity" not in r


async def test_dechargement_rechargement(hass, freezer, calls):
    freezer.move_to(at(15))
    entry = await setup_srm(hass, [room()])
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state == config_entries.ConfigEntryState.NOT_LOADED
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state == config_entries.ConfigEntryState.LOADED


async def test_config_flow_creation_et_unicite(hass, calls):
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert r["type"] == "form"
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"alarm_entity": "alarm_control_panel.a"})
    assert r["type"] == "create_entry" and r["options"] == {"rooms": []}
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {})
    assert r["type"] == "abort"
