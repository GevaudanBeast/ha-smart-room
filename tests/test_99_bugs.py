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


# B10 (point 24 h, 22/11) : une ouverture plus courte que le délai ne doit jamais
# déclencher le hors-gel, ni pendant l'ouverture ni après la fermeture.
async def _salon_fenetre(hass, freezer, delay_open=2, delay_close=2):
    freezer.move_to(at(10))
    fp(hass, "comfort")
    hass.states.async_set("binary_sensor.baie", "off")
    hass.states.async_set("calendar.c", "on")
    c = make_coord(hass, [room(climate_mode="fil_pilote", climate_entity=FP, schedule_entity="calendar.c",
                               door_window_sensors=["binary_sensor.baie"],
                               window_delay_open=delay_open, window_delay_close=delay_close)])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    return rm


async def _tick(rm, freezer, seconds):
    freezer.tick(timedelta(seconds=seconds))
    await rm.async_update()
    return rm.get_current_mode()


async def test_b10_ouverture_courte_46s_75s(hass, freezer, calls):
    rm = await _salon_fenetre(hass, freezer)
    modes = []
    hass.states.async_set("binary_sensor.baie", "on")          # ouverture 46 s
    for _ in range(2):
        modes.append(await _tick(rm, freezer, 23))
    hass.states.async_set("binary_sensor.baie", "off")
    modes.append(await _tick(rm, freezer, 30))
    hass.states.async_set("binary_sensor.baie", "on")          # ouverture 75 s
    for _ in range(3):
        modes.append(await _tick(rm, freezer, 25))
    hass.states.async_set("binary_sensor.baie", "off")
    for _ in range(10):                                       # 5 min après fermeture
        modes.append(await _tick(rm, freezer, 30))
    assert "frost_protection" not in modes, modes
    assert not [x for x in calls[("climate", "set_preset_mode")] if x.data["preset_mode"] == "away"]


async def test_b10_delai_compte_depuis_l_ouverture_reelle(hass, freezer, calls):
    """Le délai part du moment où le capteur s'est ouvert, pas du passage de boucle."""
    rm = await _salon_fenetre(hass, freezer)
    hass.states.async_set("binary_sensor.baie", "on")          # ouverture à t0
    freezer.tick(timedelta(seconds=110))                       # boucle en retard : 1er passage à t0+110 s
    assert await _tick(rm, freezer, 15) == "frost_protection"  # t0+125 s >= 2 min


async def test_b10_ouverture_longue_puis_delai_fermeture(hass, freezer, calls):
    rm = await _salon_fenetre(hass, freezer, delay_open=5)
    hass.states.async_set("binary_sensor.baie", "on")
    assert await _tick(rm, freezer, 240) != "frost_protection"   # 4 min < 5 min
    assert await _tick(rm, freezer, 70) == "frost_protection"    # 5 min 10 s
    hass.states.async_set("binary_sensor.baie", "off")
    assert await _tick(rm, freezer, 60) == "frost_protection"    # délai de fermeture en cours
    assert await _tick(rm, freezer, 70) != "frost_protection"    # 2 min 10 s après fermeture


# B11 (point 24 h) : le message « configuration anomalies » ne doit pas être répété
async def test_b11_message_anomalies_une_fois(hass, freezer, calls, caplog):
    freezer.move_to(at(15))
    await setup_srm(hass, [room(lights=["light.absente"])])
    for _ in range(3):
        freezer.tick(timedelta(minutes=16)); async_fire_time_changed(hass); await hass.async_block_till_done()
    assert caplog.text.count("configuration anomalies") == 1


# B12 (point 24 h) : salle de bain, lumière éteinte -> le calendrier s'applique
async def test_b12_salle_de_bain_suit_le_calendrier(hass, freezer, calls):
    freezer.move_to(at(9))
    fp(hass, "eco")
    hass.states.async_set("light.l", "off")
    hass.states.async_set("calendar.c", "on")
    c = make_coord(hass, [room(room_type="bathroom", lights=["light.l"], light_timeout=1800,
                               climate_mode="fil_pilote", climate_entity=FP, schedule_entity="calendar.c")])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.get_current_mode() == "comfort"
    assert rm.climate_controller._current_priority == "schedule"
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "comfort"
    fp(hass, "comfort")
    hass.states.async_set("calendar.c", "off")
    await rm.async_update()
    assert rm.get_current_mode() == "eco"
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "eco"


async def test_b12_lumiere_allumee_prioritaire(hass, freezer, calls):
    freezer.move_to(at(9))
    fp(hass, "eco")
    hass.states.async_set("light.l", "on")
    hass.states.async_set("calendar.c", "off")
    c = make_coord(hass, [room(room_type="bathroom", lights=["light.l"], light_timeout=1800,
                               climate_mode="fil_pilote", climate_entity=FP, schedule_entity="calendar.c")])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.get_current_mode() == "comfort"
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "comfort"


async def test_b12_sans_calendrier_eco(hass, freezer, calls):
    freezer.move_to(at(9))
    fp(hass, "comfort")
    hass.states.async_set("light.l", "off")
    c = make_coord(hass, [room(room_type="bathroom", lights=["light.l"], light_timeout=1800,
                               climate_mode="fil_pilote", climate_entity=FP)])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.get_current_mode() == "eco"


# ---- Point 8 du plan : détection des réglages manuels (B13) ----
from homeassistant.core import Context  # noqa: E402

USER = Context(user_id="aurelien")


def _set_fp_user(hass, preset, context=USER):
    hass.states.async_set(
        FP, "heat", {"preset_modes": ["comfort", "eco", "away", "none"], "preset_mode": preset},
        context=context,
    )


async def _tick_all(hass, freezer, seconds=31):
    freezer.tick(timedelta(seconds=seconds)); async_fire_time_changed(hass); await hass.async_block_till_done()


async def _sp(hass, freezer, **kw):
    """Suite parentale : hystérésis, calendrier confort jusqu'à 23:30, pièce à 19 °C."""
    freezer.move_to(at(23, 5))
    fp(hass, "eco")
    hass.states.async_set("sensor.t", "19")
    hass.states.async_set("calendar.c", "on", {"start_time": "2026-11-20 22:00:00", "end_time": "2026-11-20 23:30:00"})
    r = room(climate_mode="fil_pilote", climate_entity=FP, temperature_sensor="sensor.t",
             schedule_entity="calendar.c", temp_comfort=17, **kw)
    return await setup_srm(hass, [r])


async def test_b13_confort_manuel_non_annule(hass, freezer, calls):
    await _sp(hass, freezer)
    before = n(calls, "climate", "set_preset_mode")
    _set_fp_user(hass, "comfort")            # Aurélien met confort
    await hass.async_block_till_done()
    for _ in range(4):
        await _tick_all(hass, freezer)
    assert n(calls, "climate", "set_preset_mode") == before   # SRM ne remet pas eco
    prio = hass.states.get("sensor.smart_room_test_test_current_priority")
    assert prio.state == "paused" and prio.attributes["pause_reason"] == "manual_override"
    assert hass.states.get("sensor.smart_room_test_test_activite").state == "Réglage manuel"
    sw = hass.states.get("switch.smart_room_test_test_pause")
    assert sw.state == "on" and sw.attributes["reason"] == "réglage manuel"


async def test_b13_duree_fixe_meme_si_le_creneau_change(hass, freezer, calls):
    """Précision du 22/11 : durée fixe (2 h par défaut), pas de fin au changement de créneau."""
    await _sp(hass, freezer)
    _set_fp_user(hass, "comfort"); await hass.async_block_till_done()
    freezer.move_to(at(23, 31))                       # fin du créneau 23:30
    hass.states.async_set("calendar.c", "off", {"start_time": "2026-11-21 05:00:00", "end_time": "2026-11-21 07:30:00"})
    await _tick_all(hass, freezer)
    prio = hass.states.get("sensor.smart_room_test_test_current_priority")
    assert prio.state == "paused" and prio.attributes["manual_override_until"]
    freezer.move_to(at(1, 6, day=21))                 # 23:05 + 2 h 01
    await _tick_all(hass, freezer)
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state != "paused"
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "eco"


async def test_b13_duree_par_defaut_sans_calendrier(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    await setup_srm(hass, [room(climate_mode="fil_pilote", climate_entity=FP)])
    _set_fp_user(hass, "comfort"); await hass.async_block_till_done()
    await _tick_all(hass, freezer, 60 * 119)
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state == "paused"
    await _tick_all(hass, freezer, 60 * 2)
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state != "paused"


async def test_b13_duree_configurable_et_desactivable(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    await setup_srm(hass, [room(climate_mode="fil_pilote", climate_entity=FP, manual_override_minutes=0)])
    before = n(calls, "climate", "set_preset_mode")
    _set_fp_user(hass, "comfort"); await hass.async_block_till_done()
    await _tick_all(hass, freezer)
    assert n(calls, "climate", "set_preset_mode") == before + 1   # désactivé : SRM remet eco


async def test_b13_changement_srm_ou_automatisation_ignore(hass, freezer, calls):
    await _sp(hass, freezer)
    _set_fp_user(hass, "comfort", context=Context())                       # SRM lui-même
    await hass.async_block_till_done()
    _set_fp_user(hass, "comfort", context=Context(parent_id="automation"))  # automatisation
    await hass.async_block_till_done()
    await _tick_all(hass, freezer)
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state != "paused"


async def test_b13_hvac_manuel_detecte(hass, freezer, calls):
    await _sp(hass, freezer)
    hass.states.async_set(FP, "off", {"preset_modes": ["comfort", "eco"], "preset_mode": "eco"}, context=USER)
    await hass.async_block_till_done()
    await _tick_all(hass, freezer)
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state == "paused"


async def test_b13_desactiver_la_pause_reprend_la_main(hass, freezer, calls):
    await _sp(hass, freezer)
    _set_fp_user(hass, "comfort"); await hass.async_block_till_done()
    ent = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_test_test_pause")
    await ent.async_turn_off(); await hass.async_block_till_done()
    await _tick_all(hass, freezer)
    assert hass.states.get("sensor.smart_room_test_test_current_priority").state != "paused"
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "eco"


async def test_b13_lumieres_non_concernees(hass, freezer, calls):
    freezer.move_to(at(15))
    fp(hass, "eco")
    hass.states.async_set("light.l", "on")
    await setup_srm(hass, [room(room_type="bathroom", lights=["light.l"], light_timeout=60,
                                climate_mode="fil_pilote", climate_entity=FP)])
    _set_fp_user(hass, "away"); await hass.async_block_till_done()
    await _tick_all(hass, freezer, 70)
    await _tick_all(hass, freezer)
    assert n(calls, "light", "turn_off") >= 1      # le minuteur de lumière continue
