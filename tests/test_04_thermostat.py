"""Groupe 7 : thermostats."""
from tests.conftest import at, last, make_coord, n, room

TH = "climate.th"
ALARM = "alarm_control_panel.a"
SEASON = "calendar.ete"
EXT = "switch.so"


def th(hass, state="heat", presets=None, hvac=None, preset=None, temp=None):
    attrs = {"hvac_modes": hvac or ["heat", "off"]}
    if presets is not None:
        attrs["preset_modes"] = presets
    if preset is not None:
        attrs["preset_mode"] = preset
    if temp is not None:
        attrs["temperature"] = temp
    hass.states.async_set(TH, state, attrs)


def throom(**kw):
    base = dict(climate_mode="thermostat_heat", climate_entity=TH)
    base.update(kw)
    return room(**base)


async def run(hass, freezer, r, data=None, hour=15, cal=None):
    freezer.move_to(at(hour))
    if cal is not None:
        hass.states.async_set("calendar.c", cal)
        r["schedule_entity"] = "calendar.c"
    c = make_coord(hass, [r], data)
    rm = c.get_room_manager("r1")
    await rm.async_update()
    return rm


def sent(calls, srv, key):
    d = last(calls, "climate", srv)
    return d[key] if d else None


# preset_only
async def test_preset_only_confort(hass, freezer, calls):
    th(hass, presets=["comfort", "eco", "away"], preset="eco")
    await run(hass, freezer, throom(), cal="on")
    assert sent(calls, "set_preset_mode", "preset_mode") == "comfort"
    assert n(calls, "climate", "set_temperature") == 0


async def test_preset_only_nuit_repli_eco(hass, freezer, calls):
    th(hass, presets=["comfort", "eco", "away"], preset="comfort")
    await run(hass, freezer, throom(), hour=23)
    assert sent(calls, "set_preset_mode", "preset_mode") == "eco"


async def test_preset_repli_home_boost(hass, freezer, calls):
    th(hass, presets=["home", "boost"], preset="boost")
    await run(hass, freezer, throom(), cal="on")
    assert sent(calls, "set_preset_mode", "preset_mode") == "home"


async def test_preset_repli_sleep(hass, freezer, calls):
    th(hass, presets=["sleep", "eco"], preset="eco")
    await run(hass, freezer, throom(), hour=23)
    assert sent(calls, "set_preset_mode", "preset_mode") == "sleep"


async def test_preset_only_rallume_si_off(hass, freezer, calls):
    th(hass, state="off", presets=["comfort", "eco"], preset="comfort")
    await run(hass, freezer, throom(), cal="on")
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "heat"


async def test_preset_only_sans_preset_repli_hvac(hass, freezer, calls):
    th(hass, state="off", presets=[])
    await run(hass, freezer, throom(), cal="on")
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "heat"


async def test_preset_only_ete_non_reversible_off(hass, freezer, calls):
    th(hass, presets=["comfort", "eco"], preset="comfort")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, throom(), {"season_calendar": SEASON}, cal="on")
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "off"


async def test_preset_only_ete_reversible_cool(hass, freezer, calls):
    th(hass, state="off", presets=["comfort", "eco"], preset="comfort", hvac=["off", "heat", "cool"])
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, throom(climate_mode="thermostat_heat_cool"), {"season_calendar": SEASON}, cal="on")
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "cool"


async def test_preset_only_absence_away(hass, freezer, calls):
    th(hass, presets=["comfort", "eco", "away"], preset="comfort")
    hass.states.async_set(ALARM, "armed_away")
    await run(hass, freezer, throom(), {"alarm_entity": ALARM})
    assert sent(calls, "set_preset_mode", "preset_mode") == "away"
    assert n(calls, "climate", "set_hvac_mode") == 0


async def test_preset_only_absence_sans_away_off(hass, freezer, calls):
    """Comportement actuel : pas de preset away -> arrêt complet."""
    th(hass, presets=["comfort", "eco"], preset="comfort")
    hass.states.async_set(ALARM, "armed_away")
    await run(hass, freezer, throom(), {"alarm_entity": ALARM})
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "off"


# temperature
async def test_temperature_hiver(hass, freezer, calls):
    th(hass, state="off", temp=15)
    await run(hass, freezer, throom(thermostat_control_mode="temperature", temp_comfort=21), cal="on")
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "heat"
    assert sent(calls, "set_temperature", "temperature") == 21


async def test_temperature_seuil_05(hass, freezer, calls):
    th(hass, temp=20.7)
    await run(hass, freezer, throom(thermostat_control_mode="temperature", temp_comfort=21), cal="on")
    assert n(calls, "climate", "set_temperature") == 0


async def test_temperature_modes(hass, freezer, calls):
    th(hass, temp=10)
    await run(hass, freezer, throom(thermostat_control_mode="temperature", temp_night=16.5), hour=23)
    assert sent(calls, "set_temperature", "temperature") == 16.5


async def test_temperature_ete_cool(hass, freezer, calls):
    th(hass, temp=20, hvac=["off", "heat", "cool"])
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, throom(climate_mode="thermostat_heat_cool", thermostat_control_mode="temperature"), {"season_calendar": SEASON}, cal="off")
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "cool"
    assert sent(calls, "set_temperature", "temperature") == 26


async def test_temperature_ete_non_reversible(hass, freezer, calls):
    th(hass, temp=20)
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, throom(thermostat_control_mode="temperature"), {"season_calendar": SEASON}, cal="on")
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "off"


async def test_temperature_hors_gel(hass, freezer, calls):
    th(hass, temp=20)
    hass.states.async_set(ALARM, "armed_away")
    await run(hass, freezer, throom(thermostat_control_mode="temperature", temp_frost_protection=8), {"alarm_entity": ALARM})
    assert sent(calls, "set_temperature", "temperature") == 8


async def test_preset_and_temp(hass, freezer, calls):
    th(hass, presets=["comfort", "eco"], preset="eco", temp=15)
    await run(hass, freezer, throom(thermostat_control_mode="preset_and_temp", temp_comfort=21), cal="on")
    assert sent(calls, "set_preset_mode", "preset_mode") == "comfort"
    assert sent(calls, "set_temperature", "temperature") == 21


# contrôle externe thermostat
async def test_externe_hiver(hass, freezer, calls):
    th(hass, state="off", temp=15)
    hass.states.async_set(EXT, "on")
    await run(hass, freezer, throom(external_control_switch=EXT, external_control_temp=19))
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "heat"
    assert sent(calls, "set_temperature", "temperature") == 19


async def test_externe_ete_reversible(hass, freezer, calls):
    th(hass, temp=20, hvac=["off", "heat", "cool"])
    hass.states.async_set(EXT, "on")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, throom(external_control_switch=EXT, external_control_temp_summer=26), {"season_calendar": SEASON})
    assert sent(calls, "set_hvac_mode", "hvac_mode") == "cool"
    assert sent(calls, "set_temperature", "temperature") == 26


async def test_externe_ete_non_reversible(hass, freezer, calls):
    th(hass, temp=20)
    hass.states.async_set(EXT, "on")
    hass.states.async_set(SEASON, "on")
    await run(hass, freezer, throom(external_control_switch=EXT), {"season_calendar": SEASON})
    assert n(calls, "climate", "set_hvac_mode") == 0 and n(calls, "climate", "set_temperature") == 0


# détection du type
async def test_detection_auto_fil_pilote(hass, freezer, calls):
    hass.states.async_set(TH, "heat", {"preset_modes": ["comfort", "eco"], "preset_mode": "comfort"})
    rm = await run(hass, freezer, room(climate_mode="none", climate_entity=TH))
    assert rm.climate_controller.get_state()["climate_type"] == "fil_pilote"
    assert sent(calls, "set_preset_mode", "preset_mode") == "eco"


async def test_detection_auto_thermostat(hass, freezer, calls):
    hass.states.async_set(TH, "heat", {"hvac_modes": ["heat", "off"]})
    rm = await run(hass, freezer, room(climate_mode="none", climate_entity=TH))
    assert rm.climate_controller.get_state()["climate_type"] == "thermostat"
