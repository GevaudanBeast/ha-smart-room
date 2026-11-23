"""Groupes 5 et 6 : priorités du chauffage et fil pilote."""
from datetime import timedelta

from tests.conftest import at, last, make_coord, n, room

FP = "climate.fp"
WIN = "binary_sensor.win"
EXT = "switch.so"
ALARM = "alarm_control_panel.a"
SEASON = "calendar.ete"
TEMP = "sensor.t"


def fp(hass, preset="eco"):
    hass.states.async_set(FP, "heat", {"preset_modes": ["comfort", "eco", "away", "none"], "preset_mode": preset})


def fproom(**kw):
    return room(climate_mode="fil_pilote", climate_entity=FP, **kw)


async def run(hass, freezer, r, data=None, hour=15, times=1):
    freezer.move_to(at(hour))
    c = make_coord(hass, [r], data)
    rm = c.get_room_manager("r1")
    for _ in range(times):
        await rm.async_update()
    return rm


def preset_sent(calls):
    d = last(calls, "climate", "set_preset_mode")
    return d["preset_mode"] if d else None


# ---------- Groupe 5 : priorités ----------
async def test_bypass(hass, freezer, calls):
    fp(hass, "comfort")
    hass.states.async_set("switch.bypass", "on")
    rm = await run(hass, freezer, fproom(climate_bypass_switch="switch.bypass"))
    assert n(calls, "climate", "set_preset_mode") == 0
    assert rm.climate_controller._current_priority == "bypass"


async def test_pause(hass, freezer, calls):
    """Pause active : aucune commande (v0.3.9 : état tenu par la pièce)."""
    fp(hass, "comfort")
    freezer.move_to(at(15))
    c = make_coord(hass, [fproom()])
    rm = c.get_room_manager("r1")
    if hasattr(rm, "set_paused"):
        rm.set_paused(True)
    else:  # v0.3.8 : lecture de switch.smart_room_<room_id>_pause
        hass.states.async_set("switch.smart_room_r1_pause", "on")
    await rm.async_update()
    assert n(calls, "climate", "set_preset_mode") == 0
    assert rm.climate_controller._current_priority == "paused"


async def test_fenetre_preset_window(hass, freezer, calls):
    fp(hass, "comfort")
    hass.states.async_set(WIN, "on")
    freezer.move_to(at(15))
    c = make_coord(hass, [fproom(door_window_sensors=[WIN], preset_window="none")])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    freezer.tick(timedelta(minutes=3))
    await rm.async_update()
    assert preset_sent(calls) == "none"


async def test_controle_externe_attribut(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(EXT, "off", {"is_active": True})
    rm = await run(hass, freezer, fproom(external_control_switch=EXT))
    assert preset_sent(calls) == "comfort"
    assert rm.climate_controller._current_priority == "external_control"


async def test_controle_externe_etat_on(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(EXT, "on")
    rm = await run(hass, freezer, fproom(external_control_switch=EXT))
    assert rm.climate_controller._current_priority == "external_control"
    assert preset_sent(calls) == "comfort"


async def test_controle_externe_bloque_si_present(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(EXT, "on")
    hass.states.async_set(ALARM, "disarmed")
    rm = await run(hass, freezer, fproom(external_control_switch=EXT, allow_external_in_away=True), {"alarm_entity": ALARM})
    assert rm.climate_controller._current_priority == "normal"
    assert n(calls, "climate", "set_preset_mode") == 0


async def test_controle_externe_autorise_si_absent(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(EXT, "on")
    hass.states.async_set(ALARM, "armed_away")
    rm = await run(hass, freezer, fproom(external_control_switch=EXT, allow_external_in_away=True), {"alarm_entity": ALARM})
    assert rm.climate_controller._current_priority == "external_control"
    assert preset_sent(calls) == "comfort"


async def test_controle_externe_ete_ignore(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(EXT, "on")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, fproom(external_control_switch=EXT), {"season_calendar": SEASON})
    assert n(calls, "climate", "set_preset_mode") == 0


async def test_absence_preset_away(hass, freezer, calls):
    fp(hass, "comfort")
    hass.states.async_set(ALARM, "armed_away")
    rm = await run(hass, freezer, fproom(preset_away="eco"), {"alarm_entity": ALARM})
    assert preset_sent(calls) == "eco"
    assert rm.climate_controller._current_priority == "away"


async def test_absence_ignore_in_away(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(ALARM, "armed_away")
    hass.states.async_set("calendar.c", "on")
    rm = await run(hass, freezer, fproom(schedule_entity="calendar.c", ignore_in_away=True), {"alarm_entity": ALARM})
    assert preset_sent(calls) == "comfort"
    assert rm.climate_controller._current_priority == "schedule"


async def test_salle_de_bain_lumiere_chauffage(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set("light.l", "on")
    await run(hass, freezer, fproom(room_type="bathroom", lights=["light.l"], light_timeout=1800))
    assert preset_sent(calls) == "comfort"


async def test_planning(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set("calendar.c", "on")
    rm = await run(hass, freezer, fproom(schedule_entity="calendar.c"))
    assert preset_sent(calls) == "comfort"
    assert rm.climate_controller._current_priority == "schedule"


# ---------- Groupe 6 : fil pilote ----------
async def test_correspondance_modes(hass, freezer, calls):
    fp(hass, "comfort")
    await run(hass, freezer, fproom(preset_night="away"), hour=23)
    assert preset_sent(calls) == "away"


async def test_pas_d_envoi_si_deja_bon(hass, freezer, calls):
    fp(hass, "eco")
    await run(hass, freezer, fproom(), times=3)
    assert n(calls, "climate", "set_preset_mode") == 0


async def test_resynchronise_si_change_ailleurs(hass, freezer, calls):
    fp(hass, "eco")
    rm = await run(hass, freezer, fproom())
    fp(hass, "comfort")
    await rm.async_update()
    assert preset_sent(calls) == "eco"


async def test_ete_politique_off(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, fproom(), {"season_calendar": SEASON})
    assert preset_sent(calls) == "none"


async def test_ete_politique_eco(hass, freezer, calls):
    fp(hass, "comfort")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, fproom(summer_policy="eco"), {"season_calendar": SEASON})
    assert preset_sent(calls) == "eco"


async def test_ete_hors_gel_reste_away(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set(SEASON, "on")
    hass.states.async_set(ALARM, "armed_away")
    await run(hass, freezer, fproom(), {"season_calendar": SEASON, "alarm_entity": ALARM})
    assert preset_sent(calls) == "away"


async def _hyst(hass, freezer, calls, temp, start="eco", **kw):
    fp(hass, start)
    hass.states.async_set(TEMP, str(temp))
    hass.states.async_set("calendar.c", "on")
    return await run(hass, freezer, fproom(temperature_sensor=TEMP, schedule_entity="calendar.c", temp_comfort=20, **kw))


async def test_hysteresis_chauffe(hass, freezer, calls):
    rm = await _hyst(hass, freezer, calls, 19.4)
    assert preset_sent(calls) == "comfort"
    assert rm.climate_controller.get_state()["hysteresis_state"] == "heating"


async def test_hysteresis_repos(hass, freezer, calls):
    rm = await _hyst(hass, freezer, calls, 20.6, start="comfort")
    assert preset_sent(calls) == "eco"
    assert rm.climate_controller.get_state()["hysteresis_state"] == "idle"


async def test_hysteresis_zone_morte(hass, freezer, calls):
    rm = await _hyst(hass, freezer, calls, 20.0, start="away")
    assert n(calls, "climate", "set_preset_mode") == 0
    assert rm.climate_controller.get_state()["hysteresis_state"] == "deadband"


async def test_hysteresis_valeur_invalide(hass, freezer, calls):
    await _hyst(hass, freezer, calls, "unavailable")
    assert preset_sent(calls) == "comfort"  # repli : mode confort -> preset comfort


async def test_hysteresis_capteur_absent(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set("calendar.c", "on")
    await run(hass, freezer, fproom(temperature_sensor="sensor.absent", schedule_entity="calendar.c"))
    assert preset_sent(calls) == "comfort"


async def test_hysteresis_consigne_bornee(hass, freezer, calls):
    hass.states.async_set("input_number.sp", "30")
    rm = await _hyst(hass, freezer, calls, 22.0, setpoint_input="input_number.sp", max_setpoint=23)
    assert rm.climate_controller.get_state()["hysteresis_setpoint"] == 23
    assert preset_sent(calls) == "comfort"  # 22 <= 23 - 0.5


async def test_hysteresis_hors_gel(hass, freezer, calls):
    fp(hass, "comfort")
    hass.states.async_set(TEMP, "5")
    hass.states.async_set(WIN, "on")
    freezer.move_to(at(15))
    c = make_coord(hass, [fproom(temperature_sensor=TEMP, door_window_sensors=[WIN], preset_window="none")])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    freezer.tick(timedelta(minutes=3))
    await rm.async_update()
    assert preset_sent(calls) == "none"


async def test_climate_absent_pas_d_erreur(hass, freezer, calls):
    rm = await run(hass, freezer, fproom())
    assert rm.get_state()["climate_state"]["climate_type"] == "fil_pilote"
