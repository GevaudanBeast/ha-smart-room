"""Groupe 10 (v0.3.9) : module Notifications.

Cibles (entités notify, actions classiques, scripts), types choisis,
cibles par pièce (ajout / remplacement), plage de silence avec repli,
anti-répétition, événement générique, textes FR/EN, options.
"""
from datetime import timedelta

import pytest
from homeassistant.core import Context
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.smart_room_manager import config_flow as cf
from custom_components.smart_room_manager.const import DOMAIN
from custom_components.smart_room_manager.notifier import in_quiet_period
from tests.conftest import at, last, room

FP = "climate.fp"
WIN = "binary_sensor.fenetre"
USER = Context(user_id="aurelien")


@pytest.fixture
def ncalls(hass):
    return {
        "entity": async_mock_service(hass, "notify", "send_message"),
        "legacy": async_mock_service(hass, "notify", "mobile_app_tel"),
        "quiet": async_mock_service(hass, "notify", "mobile_app_nuit"),
        "script": async_mock_service(hass, "script", "turn_on"),
    }


def fp(hass, preset, context=None):
    hass.states.async_set(
        FP, "heat", {"preset_modes": ["comfort", "eco", "away", "none"], "preset_mode": preset},
        context=context,
    )


async def tick(hass, freezer, seconds=30):
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


NOTIF = {
    "notify_types": ["heating_blocked", "heating_unblocked", "manual_override",
                     "manual_override_end", "config_issues", "frost_protection"],
    "notify_entities": ["notify.tel"],
    "notify_services": ["notify.mobile_app_tel"],
    "notify_scripts": ["script.srm_annonce"],
    "notify_cooldown_minutes": 10,
}


async def setup_n(hass, freezer, notif=None, extra=None, cal="on", hour=(22, 10), lang="fr"):
    hass.config.language = lang
    freezer.move_to(at(*hour))
    fp(hass, "eco")
    hass.states.async_set(WIN, "off", {"friendly_name": "Fenêtre SP"})
    hass.states.async_set("calendar.c", cal)
    r = room(climate_mode="fil_pilote", climate_entity=FP, schedule_entity="calendar.c",
             door_window_sensors=[WIN], window_delay_open=2, window_delay_close=2,
             room_name="Suite", **(extra or {}))
    options = {"rooms": [r]}
    if notif is not None:
        options["notifications"] = notif
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=options, unique_id=DOMAIN)
    events = async_capture_events(hass, "smart_room_manager_notification")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, events


async def open_window(hass, freezer, seconds=240):
    hass.states.async_set(WIN, "on", {"friendly_name": "Fenêtre SP"})
    for _ in range(seconds // 30):
        await tick(hass, freezer)


async def close_window(hass, freezer, seconds=240):
    hass.states.async_set(WIN, "off", {"friendly_name": "Fenêtre SP"})
    for _ in range(seconds // 30):
        await tick(hass, freezer)


def types(events):
    return [e.data["type"] for e in events]


async def test_n1_trois_cibles_et_evenement(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, NOTIF)
    await open_window(hass, freezer)
    assert "heating_blocked" in types(events)
    ev = [e for e in events if e.data["type"] == "heating_blocked"][0].data
    assert ev["room_name"] == "Suite" and ev["title"] == "Suite : fenêtre ouverte"
    assert FP in ev["entities"] and WIN in ev["entities"]
    ent = [c.data for c in ncalls["entity"] if c.data["title"] == ev["title"]]
    assert ent and ent[0]["entity_id"] == "notify.tel" and ent[0]["message"] == ev["message"]
    assert "data" not in ent[0]
    leg = [c.data for c in ncalls["legacy"] if c.data["data"]["type"] == "heating_blocked"][0]
    assert leg["data"]["room_id"] == "r1" and leg["title"] == ev["title"]
    scr = [c.data for c in ncalls["script"] if c.data["variables"]["type"] == "heating_blocked"][0]
    assert scr["entity_id"] == "script.srm_annonce"
    assert scr["variables"]["type"] == "heating_blocked" and scr["variables"]["room_name"] == "Suite"


async def test_n2_types_non_choisis_ignores(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, {**NOTIF, "notify_types": ["manual_override"]})
    await open_window(hass, freezer)
    assert events == [] and ncalls["entity"] == []


async def test_n3_sans_configuration_rien_n_est_envoye(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, None)
    await open_window(hass, freezer)
    # types par défaut : l'événement est émis, aucune cible configurée
    assert "heating_blocked" in types(events)
    assert ncalls["entity"] == [] and ncalls["legacy"] == [] and ncalls["script"] == []


async def test_n4_deblocage_et_hors_gel(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, NOTIF)
    await open_window(hass, freezer)
    await close_window(hass, freezer)
    t = types(events)
    assert t.count("heating_blocked") == 1 and t.count("heating_unblocked") == 1
    assert t.count("frost_protection") == 1
    frost = [e for e in events if e.data["type"] == "frost_protection"][0].data
    assert "fenêtre ouverte" in frost["message"]


async def test_n5_anti_repetition(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, NOTIF)
    for _ in range(2):
        await open_window(hass, freezer)
        await close_window(hass, freezer)
    assert types(events).count("heating_blocked") == 1   # 2e dans les 10 min
    await tick(hass, freezer, 600)
    await open_window(hass, freezer)
    assert types(events).count("heating_blocked") == 2


async def test_n6_anti_repetition_desactivee(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, {**NOTIF, "notify_cooldown_minutes": 0})
    for _ in range(2):
        await open_window(hass, freezer)
        await close_window(hass, freezer)
    assert types(events).count("heating_blocked") == 2


async def test_n7_silence_vers_repli(hass, freezer, calls, ncalls):
    notif = {**NOTIF, "notify_quiet_start": "22:00:00", "notify_quiet_end": "07:00:00",
             "notify_quiet_services": ["notify.mobile_app_nuit"]}
    _, events = await setup_n(hass, freezer, notif)
    await open_window(hass, freezer)
    assert events[0].data["quiet"] is True
    assert ncalls["quiet"] and ncalls["entity"] == [] and ncalls["script"] == []


async def test_n8_silence_sans_repli_rien(hass, freezer, calls, ncalls):
    notif = {**NOTIF, "notify_quiet_start": "22:00:00", "notify_quiet_end": "07:00:00"}
    _, events = await setup_n(hass, freezer, notif)
    await open_window(hass, freezer)
    assert events and ncalls["entity"] == [] and ncalls["legacy"] == [] and ncalls["script"] == []


def test_n9_plage_de_silence_heures():
    assert in_quiet_period("22:00:00", "07:00:00", at(23))
    assert in_quiet_period("22:00", "07:00", at(6, 59))
    assert not in_quiet_period("22:00:00", "07:00:00", at(7))
    assert in_quiet_period("12:00", "14:00", at(13))
    assert not in_quiet_period("12:00", "14:00", at(14))
    assert not in_quiet_period(None, "07:00", at(3))
    assert not in_quiet_period("07:00", "07:00", at(7))
    assert not in_quiet_period("xx", "07:00", at(3))


async def test_n10_cibles_piece_ajout(hass, freezer, calls, ncalls):
    extra = {"room_notify_scripts": ["script.autre"], "room_notify_mode": "add"}
    await setup_n(hass, freezer, NOTIF, extra)
    await open_window(hass, freezer)
    scripts = {c.data["entity_id"] for c in ncalls["script"]}
    assert scripts == {"script.srm_annonce", "script.autre"}
    assert ncalls["entity"]


async def test_n11_cibles_piece_remplacement(hass, freezer, calls, ncalls):
    extra = {"room_notify_scripts": ["script.autre"], "room_notify_mode": "replace"}
    await setup_n(hass, freezer, NOTIF, extra)
    await open_window(hass, freezer)
    assert {c.data["entity_id"] for c in ncalls["script"]} == {"script.autre"}
    assert ncalls["entity"] == [] and ncalls["legacy"] == []


async def test_n12_reglage_manuel_debut_et_fin(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, NOTIF, {"manual_override_minutes": 30}, cal="off")
    fp(hass, "comfort", context=USER)
    await hass.async_block_till_done()
    ev = [e.data for e in events if e.data["type"] == "manual_override"]
    assert len(ev) == 1 and "22:40" in ev[0]["message"]
    for _ in range(62):
        await tick(hass, freezer)
    assert types(events).count("manual_override_end") == 1


async def test_n13_fin_par_switch_pause(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, NOTIF, {"manual_override_minutes": 30}, cal="off")
    fp(hass, "comfort", context=USER)
    await hass.async_block_till_done()
    sw = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_suite_suite_pause")
    assert sw.is_on
    await sw.async_turn_off(); await hass.async_block_till_done()
    await tick(hass, freezer)
    assert types(events).count("manual_override_end") == 1


async def test_n14_anomalies(hass, freezer, calls, ncalls):
    from custom_components.smart_room_manager import async_update_diagnostics
    entry, events = await setup_n(hass, freezer, NOTIF, {"lights": ["light.absente"]})
    coord = hass.data[DOMAIN][entry.entry_id]
    async_update_diagnostics(hass, entry, coord)
    await hass.async_block_till_done()
    ev = [e.data for e in events if e.data["type"] == "config_issues"]
    assert len(ev) == 1 and "light.absente" in ev[0]["message"] and ev[0]["room_id"] is None
    async_update_diagnostics(hass, entry, coord)       # même anomalie : pas de renvoi
    await hass.async_block_till_done()
    assert types(events).count("config_issues") == 1


async def test_n15_textes_anglais(hass, freezer, calls, ncalls):
    _, events = await setup_n(hass, freezer, NOTIF, lang="en")
    await open_window(hass, freezer)
    ev = [e.data for e in events if e.data["type"] == "heating_blocked"][0]
    assert ev["title"] == "Suite: window open"
    assert ev["message"].startswith("Heating is waiting")


async def test_n16_cible_en_erreur_sans_casser(hass, freezer, calls, ncalls):
    notif = {**NOTIF, "notify_services": ["notify.inexistant"]}
    _, events = await setup_n(hass, freezer, notif)
    await open_window(hass, freezer)
    assert ncalls["entity"] and ncalls["script"]          # les autres cibles partent
    assert last(calls, "climate", "set_preset_mode")["preset_mode"] == "away"


async def test_n17_pas_de_hors_gel_au_demarrage(hass, freezer, calls, ncalls):
    hass.states.async_set("alarm_control_panel.a", "armed_away")
    entry = MockConfigEntry(domain=DOMAIN, data={"alarm_entity": "alarm_control_panel.a"},
                            options={"rooms": [room(climate_mode="fil_pilote", climate_entity=FP)],
                                     "notifications": NOTIF}, unique_id=DOMAIN)
    freezer.move_to(at(15))
    hass.config.language = "fr"
    fp(hass, "eco")
    events = async_capture_events(hass, "smart_room_manager_notification")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await tick(hass, freezer)
    assert "frost_protection" not in types(events)
    hass.states.async_set("alarm_control_panel.a", "disarmed")
    await tick(hass, freezer)
    hass.states.async_set("alarm_control_panel.a", "armed_away")
    await tick(hass, freezer)
    frost = [e.data for e in events if e.data["type"] == "frost_protection"]
    assert len(frost) == 1 and "absence" in frost[0]["message"]


# ---- options -------------------------------------------------------------
@pytest.fixture
def shim(monkeypatch):
    monkeypatch.setattr(
        cf.SmartRoomManagerOptionsFlow, "config_entry",
        property(lambda self: self.hass.config_entries.async_get_entry(self.handler)),
        raising=False,
    )


async def test_n18_options_notifications(hass, shim, ncalls):
    e = MockConfigEntry(domain=DOMAIN, data={}, options={"rooms": []}, unique_id=DOMAIN)
    e.add_to_hass(hass)
    r = await hass.config_entries.options.async_init(e.entry_id)
    assert "notifications" in r["menu_options"]
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"next_step_id": "notifications"})
    assert r["type"] == "form" and r["step_id"] == "notifications"
    r = await hass.config_entries.options.async_configure(r["flow_id"], {
        "notify_types": ["heating_blocked"], "notify_scripts": ["script.srm_annonce"],
        "notify_services": ["notify.mobile_app_tel"],
        "notify_quiet_start": "22:00:00", "notify_quiet_end": "07:00:00",
        "notify_cooldown_minutes": 5,
    })
    assert r["type"] == "create_entry"
    saved = r["data"]["notifications"]
    assert saved["notify_types"] == ["heating_blocked"]
    assert saved["notify_scripts"] == ["script.srm_annonce"]
    assert saved["notify_services"] == ["notify.mobile_app_tel"]
    assert saved["notify_quiet_start"] == "22:00:00" and saved["notify_cooldown_minutes"] == 5
    assert r["data"]["rooms"] == []


def test_n19_liste_actions_notify(hass, ncalls):
    services = cf.list_legacy_notify_services(hass)
    assert "notify.mobile_app_tel" in services and "notify.send_message" not in services


def test_n20_traductions_completes():
    import json
    from pathlib import Path
    base = Path(cf.__file__).parent
    for f in ["strings.json", "translations/fr.json", "translations/en.json"]:
        d = json.loads((base / f).read_text(encoding="utf-8"))
        step = d["options"]["step"]
        assert "notifications" in step and "notifications" in step["init"]["menu_options"]
        assert set(d["selector"]["notify_types"]["options"]) == {
            "heating_blocked", "heating_unblocked", "manual_override",
            "manual_override_end", "config_issues", "frost_protection"}
        assert "room_notify_mode" in step["room_control"]["data"]


async def test_n21_description_reglage_manuel(hass, freezer, calls, ncalls):
    await setup_n(hass, freezer, NOTIF, {"manual_override_minutes": 30}, cal="off")
    fp(hass, "comfort", context=USER)
    await hass.async_block_till_done()
    await tick(hass, freezer)
    st = hass.states.get("sensor.smart_room_suite_suite_current_priority")
    assert st.attributes["description"].startswith("Réglage manuel respecté jusqu'à 22:4")
    sw = hass.data["entity_components"]["switch"].get_entity("switch.smart_room_suite_suite_pause")
    await sw.async_turn_off(); await hass.async_block_till_done()
    await sw.async_turn_on(); await hass.async_block_till_done()
    await tick(hass, freezer)
    st = hass.states.get("sensor.smart_room_suite_suite_current_priority")
    assert st.attributes["description"] == "Pause manuelle active"
