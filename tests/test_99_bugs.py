"""Bugs B1 à B7 : ces tests décrivent le comportement attendu.

Sur la v0.3.8 ils doivent échouer (preuve du bug), après correction ils doivent réussir.
"""
import json
from datetime import timedelta
from pathlib import Path

from homeassistant.core import State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache,
)

from custom_components.smart_room_manager import const
from custom_components.smart_room_manager.const import DOMAIN
from tests.conftest import at, last, make_coord, n, room

FP = "climate.fp"
TH = "climate.th"
ALARM = "alarm_control_panel.a"


async def setup_srm(hass, rooms, data=None):
    entry = MockConfigEntry(domain=DOMAIN, data=data or {}, options={"rooms": rooms}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def fp(hass, preset):
    hass.states.async_set(FP, "heat", {"preset_modes": ["comfort", "eco", "away", "none"], "preset_mode": preset})


# B1 : le switch Pause réel doit suspendre l'automatisation
async def test_b1_pause_switch_reel(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    await setup_srm(hass, [room(climate_mode="fil_pilote", climate_entity=FP)])
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_pause")
    await ent.async_turn_on(); await hass.async_block_till_done()
    fp(hass, "comfort")  # réglage manuel
    before = n(calls, "climate", "set_preset_mode")
    freezer.tick(timedelta(seconds=31)); async_fire_time_changed(hass); await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=31)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert n(calls, "climate", "set_preset_mode") == before


# B1b : la pause doit être restaurée après un redémarrage
async def test_b1_pause_restauree(hass, freezer, calls):
    freezer.move_to(at(15))
    mock_restore_cache(hass, [State("switch.smart_room_test_test_pause", "on")])
    await setup_srm(hass, [room(pause_infinite=True)])
    assert hass.states.get("switch.smart_room_test_test_pause").state == "on"


# B1c : le switch Automation doit être restauré après un redémarrage
async def test_b1_automation_restauree(hass, freezer, calls):
    freezer.move_to(at(15))
    mock_restore_cache(hass, [State("switch.smart_room_test_test_automation", "off")])
    await setup_srm(hass, [room()])
    assert hass.states.get("switch.smart_room_test_test_automation").state == "off"


# B2 : les presets doivent être relus si l'entité n'était pas prête
async def test_b2_presets_relus(hass, freezer, calls):
    freezer.move_to(at(15))
    hass.states.async_set(TH, "unavailable", {})
    hass.states.async_set("calendar.c", "on")
    c = make_coord(hass, [room(climate_mode="thermostat_heat", climate_entity=TH, schedule_entity="calendar.c")])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    hass.states.async_set(TH, "heat", {"hvac_modes": ["heat", "off"], "preset_modes": ["comfort", "eco", "away"], "preset_mode": "eco"})
    await rm.async_update()
    assert last(calls, "climate", "set_preset_mode") == {"entity_id": TH, "preset_mode": "comfort"}


# B2b : aucune commande vers une entité indisponible
async def test_b2_pas_de_commande_si_indisponible(hass, freezer, calls):
    freezer.move_to(at(15))
    hass.states.async_set(TH, "unavailable", {})
    c = make_coord(hass, [room(climate_mode="thermostat_heat", climate_entity=TH)])
    await c.get_room_manager("r1").async_update()
    assert sum(len(v) for k, v in calls.items() if k[0] == "climate") == 0


# B3 : absence -> preset away (pas d'arrêt) quand les presets arrivent après le démarrage
async def test_b3_absence_away_apres_demarrage(hass, freezer, calls):
    freezer.move_to(at(15))
    hass.states.async_set(TH, "unavailable", {})
    hass.states.async_set(ALARM, "armed_away")
    c = make_coord(hass, [room(climate_mode="thermostat_heat", climate_entity=TH)], {"alarm_entity": ALARM})
    rm = c.get_room_manager("r1")
    await rm.async_update()
    hass.states.async_set(TH, "heat", {"hvac_modes": ["heat", "off"], "preset_modes": ["comfort", "eco", "away"], "preset_mode": "comfort"})
    await rm.async_update()
    assert last(calls, "climate", "set_preset_mode") == {"entity_id": TH, "preset_mode": "away"}
    assert n(calls, "climate", "set_hvac_mode") == 0


# B4 : la consigne d'hystérésis doit suivre le mode ; setpoint_input = consigne confort
async def test_b4_consigne_suit_le_mode(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "comfort")
    hass.states.async_set("sensor.t", "19")
    hass.states.async_set("input_number.sp", "21")
    hass.states.async_set("calendar.c", "off")  # période eco
    c = make_coord(hass, [room(climate_mode="fil_pilote", climate_entity=FP, temperature_sensor="sensor.t",
                               setpoint_input="input_number.sp", schedule_entity="calendar.c", temp_eco=18)])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.climate_controller.get_state()["hysteresis_setpoint"] == 18
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "eco"
    fp(hass, "eco")  # le radiateur a suivi la commande
    hass.states.async_set("calendar.c", "on")  # période confort
    await rm.async_update()
    assert rm.climate_controller.get_state()["hysteresis_setpoint"] == 21
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "comfort"


# B5 : diagnostic des anomalies
async def test_b5_diagnostic_entite_absente(hass, freezer, calls):
    from custom_components.smart_room_manager.diagnostics_check import check_rooms
    hass.states.async_set("light.ok", "off")
    rooms = [room(lights=["light.ok", "light.absente"], climate_mode="fil_pilote")]
    codes = {(a["code"], a.get("entity_id")) for a in check_rooms(hass, rooms, {})}
    assert ("missing_entity", "light.absente") in codes
    assert ("climate_without_actuator", None) in codes
    assert not any(e == "light.ok" for _, e in codes)


# B6 : version alignée
def test_b6_version_alignee():
    manifest = json.loads(Path(const.__file__).with_name("manifest.json").read_text())
    assert const.VERSION == manifest["version"]


# B7 : contrôle externe fil pilote, pas de commande inutile
async def test_b7_externe_pas_de_commande_inutile(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "comfort")
    hass.states.async_set("switch.so", "on")
    c = make_coord(hass, [room(climate_mode="fil_pilote", climate_entity=FP, external_control_switch="switch.so")])
    await c.get_room_manager("r1").async_update()
    assert n(calls, "climate", "set_preset_mode") == 0


# B7b : contrôle externe fil pilote, ré-appliqué si changé à la main
async def test_b7_externe_reapplique(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    hass.states.async_set("switch.so", "on")
    c = make_coord(hass, [room(climate_mode="fil_pilote", climate_entity=FP, external_control_switch="switch.so")])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    fp(hass, "eco")  # remis à eco par quelqu'un d'autre
    await rm.async_update()
    assert n(calls, "climate", "set_preset_mode") == 2


# B2c : un thermostat sans presets ne doit pas répéter l'avertissement à chaque passage
async def test_b2_avertissement_une_fois(hass, freezer, calls, caplog):
    freezer.move_to(at(15))
    hass.states.async_set(TH, "heat", {"hvac_modes": ["heat", "off"]})
    c = make_coord(hass, [room(climate_mode="thermostat_heat", climate_entity=TH)])
    rm = c.get_room_manager("r1")
    for _ in range(5):
        await rm.async_update()
    assert caplog.text.count("No preset for mode") <= 1


# B8 : version minimale HA cohérente avec le flux d'options (self.config_entry, HA >= 2024.11)
def test_b8_version_min_hacs():
    hacs = json.loads((Path(const.__file__).parents[2] / "hacs.json").read_text())
    major, minor = (int(x) for x in hacs["homeassistant"].split(".")[:2])
    assert (major, minor) >= (2024, 11)


# B9 : décharger l'intégration pendant une pause minutée ne doit laisser aucun timer
async def test_b9_pas_de_timer_orphelin(hass, freezer, calls):
    freezer.move_to(at(15))
    entry = await setup_srm(hass, [room(pause_duration_minutes=30)])
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_pause")
    await ent.async_turn_on(); await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert ent._pause_timer is None


# Diagnostic : actionneur piloté aussi par Solar Optimizer
async def test_b5_diagnostic_multi_pilote(hass, freezer, calls):
    from custom_components.smart_room_manager.diagnostics_check import check_rooms
    MockConfigEntry(domain="solar_optimizer", data={"entity_id": FP}).add_to_hass(hass)
    fp(hass, "eco")
    codes = {a["code"] for a in check_rooms(hass, [room(climate_mode="fil_pilote", climate_entity=FP)], {})}
    assert "multi_controller" in codes


# Diagnostic : entité indisponible depuis plus de 10 min
async def test_b5_diagnostic_indisponible(hass, freezer, calls):
    from custom_components.smart_room_manager.diagnostics_check import check_rooms
    freezer.move_to(at(15))
    hass.states.async_set("light.l", "unavailable")
    rooms = [room(lights=["light.l"])]
    assert not [a for a in check_rooms(hass, rooms, {}) if a["code"] == "unavailable_entity"]
    freezer.tick(timedelta(minutes=11))
    assert [a for a in check_rooms(hass, rooms, {}) if a["code"] == "unavailable_entity"]


# Diagnostic : consigne confort (helper) inférieure à la consigne eco
async def test_b5_diagnostic_consigne_incoherente(hass, freezer, calls):
    from custom_components.smart_room_manager.diagnostics_check import check_rooms
    hass.states.async_set("input_number.sp", "15")
    hass.states.async_set("sensor.t", "19")
    fp(hass, "eco")
    rooms = [room(climate_mode="fil_pilote", climate_entity=FP, temperature_sensor="sensor.t",
                  setpoint_input="input_number.sp", min_setpoint=17, temp_eco=18)]
    assert "setpoint_below_eco" in {a["code"] for a in check_rooms(hass, rooms, {})}


# Diagnostic de bout en bout : une réparation HA et un capteur d'anomalies
async def test_b5_reparation_et_capteur(hass, freezer, calls):
    from homeassistant.helpers import issue_registry as ir
    freezer.move_to(at(15))
    await setup_srm(hass, [room(lights=["light.absente"])])
    hass.bus.async_fire("homeassistant_started")
    await hass.async_block_till_done()
    issues = [i for (d, _), i in ir.async_get(hass).issues.items() if d == DOMAIN]
    assert issues
    st = hass.states.get("sensor.smart_room_manager_anomalies")
    assert st is not None and int(st.state) >= 1


# B1d : pause minutée restaurée avec son échéance, ou ignorée si elle a expiré
async def test_b1_pause_minutee_restauree(hass, freezer, calls):
    freezer.move_to(at(15))
    until = (at(15) + timedelta(minutes=20)).isoformat()
    mock_restore_cache(hass, [State("switch.smart_room_test_test_pause", "on", {"pause_until": until})])
    await setup_srm(hass, [room(pause_duration_minutes=30)])
    assert hass.states.get("switch.smart_room_test_test_pause").state == "on"
    freezer.tick(timedelta(minutes=21)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert hass.states.get("switch.smart_room_test_test_pause").state == "off"


async def test_b1_pause_expiree_pendant_arret(hass, freezer, calls):
    freezer.move_to(at(15))
    until = (at(15) - timedelta(minutes=5)).isoformat()
    mock_restore_cache(hass, [State("switch.smart_room_test_test_pause", "on", {"pause_until": until})])
    await setup_srm(hass, [room(pause_duration_minutes=30)])
    assert hass.states.get("switch.smart_room_test_test_pause").state == "off"


# B1e (trouvé en direct le 21/11) : désactiver la pause doit relâcher la pièce
async def test_b1_fin_de_pause_relache_la_piece(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    await setup_srm(hass, [room(climate_mode="fil_pilote", climate_entity=FP)])
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_pause")
    await ent.async_turn_on(); await hass.async_block_till_done()
    await ent.async_turn_off(); await hass.async_block_till_done()
    fp(hass, "comfort")
    freezer.tick(timedelta(seconds=31)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state != "paused"
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "eco"


# B1f : la fin automatique d'une pause minutée doit aussi relâcher la pièce
async def test_b1_fin_auto_de_pause(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    await setup_srm(hass, [room(climate_mode="fil_pilote", climate_entity=FP, pause_duration_minutes=15)])
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_pause")
    await ent.async_turn_on(); await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=16)); async_fire_time_changed(hass); await hass.async_block_till_done()
    fp(hass, "comfort")
    freezer.tick(timedelta(seconds=31)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state != "paused"
