"""Branches complémentaires (erreurs de service, replis), pour la couverture."""
from homeassistant.exceptions import HomeAssistantError

from tests.conftest import at, last, make_coord, n, room

FP = "climate.fp"
TH = "climate.th"
ALARM = "alarm_control_panel.a"
SEASON = "calendar.ete"


def fp(hass, preset="eco"):
    hass.states.async_set(FP, "heat", {"preset_modes": ["comfort", "eco", "away", "none"], "preset_mode": preset})


async def run(hass, freezer, r, data=None, hour=15):
    freezer.move_to(at(hour))
    c = make_coord(hass, [r], data)
    rm = c.get_room_manager("r1")
    await rm.async_update()
    return rm


def failing(hass, dom, srv):
    async def boom(call):
        raise HomeAssistantError("échec simulé")
    hass.services.async_register(dom, srv, boom)


def fph(**kw):
    return room(climate_mode="fil_pilote", climate_entity=FP, temperature_sensor="sensor.t", **kw)


async def test_fp_hysteresis_planning_hors_gel(hass, freezer, calls):
    fp(hass, "comfort"); hass.states.async_set("sensor.t", "19")
    hass.states.async_set("calendar.c", "off")
    await run(hass, freezer, fph(schedule_entity="calendar.c", preset_schedule_off="frost_protection"))
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "away"


async def test_fp_hysteresis_planning_hors_gel_deja_away(hass, freezer, calls):
    fp(hass, "away"); hass.states.async_set("sensor.t", "19")
    hass.states.async_set("calendar.c", "off")
    await run(hass, freezer, fph(schedule_entity="calendar.c", preset_schedule_off="frost_protection"))
    assert n(calls, "climate", "set_preset_mode") == 0


async def test_fp_hysteresis_ete(hass, freezer, calls):
    fp(hass, "comfort"); hass.states.async_set("sensor.t", "19")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, fph(summer_policy="eco"), {"season_calendar": SEASON})
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "eco"


async def test_fp_hysteresis_ete_off(hass, freezer, calls):
    fp(hass, "comfort"); hass.states.async_set("sensor.t", "19")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, fph(), {"season_calendar": SEASON})
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "none"


async def test_fp_setpoint_invalide_repli_mode(hass, freezer, calls):
    fp(hass, "eco"); hass.states.async_set("sensor.t", "16")
    hass.states.async_set("input_number.sp", "abc")
    rm = await run(hass, freezer, fph(setpoint_input="input_number.sp", temp_eco=18))
    assert rm.climate_controller.get_state()["hysteresis_setpoint"] == 18


async def test_fp_setpoint_absent_repli_mode(hass, freezer, calls):
    fp(hass, "eco"); hass.states.async_set("sensor.t", "16")
    rm = await run(hass, freezer, fph(setpoint_input="input_number.absent", temp_night=15.5), hour=23)
    assert rm.climate_controller.get_state()["hysteresis_setpoint"] == 15.5


async def test_fp_erreur_service(hass, freezer, calls):
    fp(hass, "comfort")
    failing(hass, "climate", "set_preset_mode")
    rm = await run(hass, freezer, room(climate_mode="fil_pilote", climate_entity=FP))
    assert rm.get_current_mode() == "eco"  # pas d'exception propagée


async def test_fp_erreur_service_hysteresis(hass, freezer, calls):
    fp(hass, "comfort"); hass.states.async_set("sensor.t", "25")
    failing(hass, "climate", "set_preset_mode")
    await run(hass, freezer, fph())


async def test_fp_erreur_service_hors_gel(hass, freezer, calls):
    fp(hass, "comfort")
    hass.states.async_set(ALARM, "armed_away")
    failing(hass, "climate", "set_preset_mode")
    await run(hass, freezer, room(climate_mode="fil_pilote", climate_entity=FP), {"alarm_entity": ALARM})


async def test_fp_erreur_service_externe(hass, freezer, calls):
    fp(hass, "eco")
    hass.states.async_set("switch.so", "on")
    failing(hass, "climate", "set_preset_mode")
    await run(hass, freezer, room(climate_mode="fil_pilote", climate_entity=FP, external_control_switch="switch.so"))


async def test_fp_get_state_hysteresis(hass, freezer, calls):
    fp(hass, "eco"); hass.states.async_set("sensor.t", "16")
    rm = await run(hass, freezer, fph(temp_eco=18, hysteresis=0.3))
    st = rm.climate_controller.get_state()
    assert st["hysteresis_lower_threshold"] == 17.7 and st["hysteresis_upper_threshold"] == 18.3


# ---------- thermostat ----------
def th(hass, state="heat", **attrs):
    attrs.setdefault("hvac_modes", ["heat", "off"])
    hass.states.async_set(TH, state, attrs)


def throom(**kw):
    base = dict(climate_mode="thermostat_heat", climate_entity=TH)
    base.update(kw)
    return room(**base)


async def test_th_entite_absente(hass, freezer, calls):
    rm = await run(hass, freezer, throom())
    assert rm.climate_controller.get_state()["climate_type"] == "thermostat"
    assert sum(len(v) for v in calls.values()) == 0


async def test_th_detection_entite_absente_mode_none(hass, freezer, calls):
    rm = await run(hass, freezer, room(climate_mode="none", climate_entity=TH))
    assert rm.climate_controller.get_state()["climate_type"] == "thermostat"


async def test_th_repli_hors_gel_sans_preset_off(hass, freezer, calls):
    th(hass, preset_modes=[])
    hass.states.async_set("calendar.c", "off")
    await run(hass, freezer, throom(schedule_entity="calendar.c", preset_schedule_off="frost_protection"))
    assert last(calls, "climate", "set_hvac_mode")["hvac_mode"] == "off"


async def test_th_repli_ete_cool(hass, freezer, calls):
    th(hass, "off", preset_modes=[], hvac_modes=["off", "cool", "heat"])
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, throom(), {"season_calendar": SEASON})
    assert last(calls, "climate", "set_hvac_mode")["hvac_mode"] == "cool"


async def test_th_repli_heat_cool(hass, freezer, calls):
    th(hass, "off", preset_modes=[], hvac_modes=["off", "heat_cool"])
    await run(hass, freezer, throom())
    assert last(calls, "climate", "set_hvac_mode")["hvac_mode"] == "heat_cool"


async def test_th_rallume_heat_cool(hass, freezer, calls):
    th(hass, "off", preset_modes=["eco"], preset_mode="eco", hvac_modes=["off", "heat_cool"])
    await run(hass, freezer, throom())
    assert last(calls, "climate", "set_hvac_mode")["hvac_mode"] == "heat_cool"


async def test_th_temperature_ete_confort(hass, freezer, calls):
    th(hass, "cool", temperature=20, hvac_modes=["off", "cool", "heat"])
    hass.states.async_set(SEASON, "on"); hass.states.async_set("calendar.c", "on")
    await run(hass, freezer, throom(thermostat_control_mode="temperature", schedule_entity="calendar.c", temp_cool_comfort=23.5), {"season_calendar": SEASON})
    assert last(calls, "climate", "set_temperature")["temperature"] == 23.5


async def test_th_temperature_ete_hors_gel(hass, freezer, calls):
    th(hass, "cool", temperature=20, hvac_modes=["off", "cool", "heat"])
    hass.states.async_set(SEASON, "on"); hass.states.async_set("calendar.c", "off")
    await run(hass, freezer, throom(thermostat_control_mode="temperature", schedule_entity="calendar.c", preset_schedule_off="frost_protection"), {"season_calendar": SEASON})
    assert last(calls, "climate", "set_hvac_mode")["hvac_mode"] == "off"


async def test_th_temperature_ete_confort_non_reversible(hass, freezer, calls):
    th(hass, "heat", temperature=20)
    hass.states.async_set(SEASON, "on"); hass.states.async_set("calendar.c", "on")
    await run(hass, freezer, throom(thermostat_control_mode="temperature", schedule_entity="calendar.c"), {"season_calendar": SEASON})
    assert last(calls, "climate", "set_hvac_mode")["hvac_mode"] == "off"


async def test_th_hors_gel_preset_and_temp(hass, freezer, calls):
    th(hass, preset_modes=["away", "comfort"], preset_mode="comfort", temperature=20)
    hass.states.async_set(ALARM, "armed_away")
    await run(hass, freezer, throom(thermostat_control_mode="preset_and_temp"), {"alarm_entity": ALARM})
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "away"
    assert last(calls, "climate", "set_temperature")["temperature"] == 7


async def test_th_erreurs_services(hass, freezer, calls):
    th(hass, "off", preset_modes=["comfort"], preset_mode="eco", temperature=10)
    for s in ("set_preset_mode", "set_hvac_mode", "set_temperature"):
        failing(hass, "climate", s)
    hass.states.async_set("calendar.c", "on")
    await run(hass, freezer, throom(thermostat_control_mode="preset_and_temp", schedule_entity="calendar.c"))


async def test_th_externe_erreurs(hass, freezer, calls):
    th(hass, "off", temperature=10)
    hass.states.async_set("switch.so", "on")
    failing(hass, "climate", "set_hvac_mode")
    await run(hass, freezer, throom(external_control_switch="switch.so"))
    failing(hass, "climate", "set_temperature")
    th(hass, "heat", temperature=10)
    await run(hass, freezer, throom(external_control_switch="switch.so"))


async def test_th_get_state(hass, freezer, calls):
    th(hass, preset_modes=["comfort", "eco"], preset_mode="eco")
    hass.states.async_set("calendar.c", "on")
    rm = await run(hass, freezer, throom(schedule_entity="calendar.c"))
    st = rm.climate_controller.get_state()
    assert st["control_mode"] == "preset_only" and st["available_presets"] == ["comfort", "eco"]
