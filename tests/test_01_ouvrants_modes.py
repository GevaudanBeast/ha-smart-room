"""Groupes 1 et 2 : ouvrants, horaires, priorité des modes."""
from datetime import timedelta

from tests.conftest import at, make_coord, room

FP = "climate.fp"
WIN = "binary_sensor.win"


def fp_room(**kw):
    return room(
        climate_mode="fil_pilote",
        climate_entity=FP,
        door_window_sensors=[WIN],
        **kw,
    )


def _fp_state(hass, preset="eco"):
    hass.states.async_set(
        FP, "heat", {"preset_modes": ["comfort", "eco", "away", "none"], "preset_mode": preset}
    )


# ---------- Groupe 1 : ouvrants ----------
async def test_fenetre_delai_ouverture(hass, freezer, calls):
    freezer.move_to(at(10))
    _fp_state(hass)
    hass.states.async_set(WIN, "off")
    c = make_coord(hass, [fp_room()])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    hass.states.async_set(WIN, "on")
    await rm.async_update()
    assert rm.is_windows_open() is True
    assert rm.is_windows_open_delayed() is False
    freezer.tick(timedelta(minutes=1, seconds=50))
    assert rm.is_windows_open_delayed() is False
    freezer.tick(timedelta(seconds=15))
    await rm.async_update()
    assert rm.is_windows_open_delayed() is True
    assert rm.get_current_mode() == "frost_protection"


async def test_fenetre_delai_fermeture(hass, freezer, calls):
    freezer.move_to(at(10))
    _fp_state(hass)
    hass.states.async_set(WIN, "on")
    c = make_coord(hass, [fp_room()])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    freezer.tick(timedelta(minutes=3))
    await rm.async_update()
    assert rm.is_windows_open_delayed() is True
    hass.states.async_set(WIN, "off")
    await rm.async_update()
    assert rm.is_windows_open_delayed() is True  # encore dans le délai de fermeture
    freezer.tick(timedelta(minutes=2, seconds=5))
    await rm.async_update()
    assert rm.is_windows_open_delayed() is False


async def test_une_fenetre_suffit(hass, freezer, calls):
    freezer.move_to(at(10))
    hass.states.async_set("binary_sensor.a", "off")
    hass.states.async_set("binary_sensor.b", "on")
    c = make_coord(hass, [room(door_window_sensors=["binary_sensor.a", "binary_sensor.b"])])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.is_windows_open() is True


async def test_sans_capteur_jamais_ouvert(hass, calls):
    c = make_coord(hass, [room()])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.is_windows_open() is False
    assert rm.is_windows_open_delayed() is False


async def test_window_check_desactive(hass, freezer, calls):
    freezer.move_to(at(10))
    _fp_state(hass, "eco")
    hass.states.async_set(WIN, "on")
    c = make_coord(hass, [fp_room(climate_window_check=False)])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    freezer.tick(timedelta(minutes=10))
    await rm.async_update()
    assert rm.get_current_mode() == "eco"
    assert not [x for x in calls[("climate", "set_preset_mode")] if x.data["preset_mode"] == "away"]


# ---------- Groupe 2 : horaires et modes ----------
async def _mode_at(hass, freezer, hour, minute=0, **kw):
    freezer.move_to(at(hour, minute))
    c = make_coord(hass, [room(**kw)])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    return rm


async def test_nuit_avant_minuit(hass, freezer, calls):
    rm = await _mode_at(hass, freezer, 23)
    assert rm.is_night_period() and rm.get_current_mode() == "night"


async def test_nuit_apres_minuit(hass, freezer, calls):
    rm = await _mode_at(hass, freezer, 5, 59)
    assert rm.get_current_mode() == "night"


async def test_jour_6h(hass, freezer, calls):
    rm = await _mode_at(hass, freezer, 6, 0)
    assert rm.get_current_mode() == "eco"


async def test_jour_21h59(hass, freezer, calls):
    rm = await _mode_at(hass, freezer, 21, 59)
    assert rm.get_current_mode() == "eco"


async def test_night_start_personnalise(hass, freezer, calls):
    rm = await _mode_at(hass, freezer, 21, 30, night_start="21:00:00")
    assert rm.get_current_mode() == "night"


async def test_plage_confort(hass, freezer, calls):
    rm = await _mode_at(
        hass, freezer, 11, comfort_time_ranges=[{"start": "10:00", "end": "12:00"}]
    )
    assert rm.get_current_mode() == "comfort"


async def test_plage_confort_passe_minuit(hass, freezer, calls):
    freezer.move_to(at(0, 30))
    c = make_coord(hass, [room(comfort_time_ranges=[{"start": "23:00", "end": "01:00"}])])
    assert c.get_room_manager("r1")._is_in_comfort_time_range() is True


async def test_plage_invalide_ignoree(hass, freezer, calls):
    rm = await _mode_at(
        hass, freezer, 11, comfort_time_ranges=[{"start": "xx", "end": "12:00"}, {"start": "10:00"}]
    )
    assert rm.get_current_mode() == "eco"


async def test_planning_on_off(hass, freezer, calls):
    hass.states.async_set("calendar.c", "on")
    rm = await _mode_at(hass, freezer, 15, schedule_entity="calendar.c")
    assert rm.get_current_mode() == "comfort"
    hass.states.async_set("calendar.c", "off")
    await rm.async_update()
    assert rm.get_current_mode() == "eco"


async def test_planning_presets_personnalises(hass, freezer, calls):
    hass.states.async_set("calendar.c", "off")
    rm = await _mode_at(
        hass, freezer, 15, schedule_entity="calendar.c",
        preset_schedule_on="night", preset_schedule_off="frost_protection",
    )
    assert rm.get_current_mode() == "frost_protection"
    hass.states.async_set("calendar.c", "on")
    await rm.async_update()
    assert rm.get_current_mode() == "night"


async def test_planning_prioritaire_sur_nuit(hass, freezer, calls):
    """Comportement actuel : avec planning, le mode nuit ne s'applique jamais."""
    hass.states.async_set("calendar.c", "off")
    rm = await _mode_at(hass, freezer, 23, schedule_entity="calendar.c")
    assert rm.get_current_mode() == "eco"


async def test_calendrier_absent_ignore(hass, freezer, calls):
    rm = await _mode_at(hass, freezer, 23, schedule_entity="calendar.inexistant")
    assert rm.get_current_mode() == "night"


async def test_priorite_fenetre_sur_absence(hass, freezer, calls):
    freezer.move_to(at(10))
    hass.states.async_set("alarm_control_panel.a", "armed_away")
    hass.states.async_set(WIN, "on")
    _fp_state(hass)
    c = make_coord(hass, [fp_room()], data={"alarm_entity": "alarm_control_panel.a"})
    rm = c.get_room_manager("r1")
    await rm.async_update()
    freezer.tick(timedelta(minutes=3))
    await rm.async_update()
    assert rm.get_current_mode() == "frost_protection"
    assert c.get_room_manager("r1").climate_controller._current_priority == "windows_open"


async def test_absence_hors_gel(hass, freezer, calls):
    freezer.move_to(at(10))
    hass.states.async_set("alarm_control_panel.a", "armed_away")
    c = make_coord(hass, [room()], data={"alarm_entity": "alarm_control_panel.a"})
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.get_current_mode() == "frost_protection"
    assert rm.get_state()["occupied"] is False


async def test_absence_ignore_in_away_planning(hass, freezer, calls):
    freezer.move_to(at(10))
    hass.states.async_set("alarm_control_panel.a", "armed_away")
    hass.states.async_set("calendar.c", "on")
    c = make_coord(
        hass, [room(schedule_entity="calendar.c", ignore_in_away=True)],
        data={"alarm_entity": "alarm_control_panel.a"},
    )
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.get_current_mode() == "comfort"


async def test_salle_de_bain_lumiere(hass, freezer, calls):
    freezer.move_to(at(23))
    hass.states.async_set("light.l", "on")
    hass.states.async_set("calendar.c", "off")
    c = make_coord(hass, [room(room_type="bathroom", lights=["light.l"], schedule_entity="calendar.c")])
    rm = c.get_room_manager("r1")
    await rm.async_update()
    assert rm.get_current_mode() == "comfort"
    hass.states.async_set("light.l", "off")
    await rm.async_update()
    assert rm.get_current_mode() == "eco"


async def test_automation_desactivee_aucune_commande(hass, freezer, calls):
    freezer.move_to(at(10))
    _fp_state(hass, "comfort")
    c = make_coord(hass, [fp_room()])
    rm = c.get_room_manager("r1")
    rm.set_automation_enabled(False)
    await rm.async_update()
    assert sum(len(v) for v in calls.values()) == 0
    rm.set_automation_enabled(True)
    await rm.async_update()
    assert calls[("climate", "set_preset_mode")][-1].data["preset_mode"] == "eco"


async def test_update_config(hass, freezer, calls):
    c = make_coord(hass, [room()])
    rm = c.get_room_manager("r1")
    rm.update_config(room(room_name="Nouveau", room_type="corridor"))
    assert rm.room_name == "Nouveau" and rm.room_type == "corridor"
    rm.update_config({"room_id": "r1"})  # nom manquant : ignoré
    assert rm.room_name == "Nouveau"
