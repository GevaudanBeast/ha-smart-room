"""Groupes 3 et 4 : lumières (extinction auto) et VMC."""
from datetime import timedelta

from tests.conftest import at, make_coord, n, room

L = "light.l"
VMC = "switch.vmc"


async def _setup(hass, freezer, rooms, data=None):
    freezer.move_to(at(10))
    c = make_coord(hass, rooms, data)
    return c


# ---------- Groupe 3 ----------
async def test_couloir_extinction_300s(hass, freezer, calls):
    c = await _setup(hass, freezer, [room(room_type="corridor", lights=[L])])
    rm = c.get_room_manager("r1")
    hass.states.async_set(L, "on")
    await rm.async_update()
    freezer.tick(timedelta(seconds=290))
    await rm.async_update()
    assert n(calls, "light", "turn_off") == 0
    st = rm.light_controller.get_state()
    assert st["timer_active"] is True and 0 < st["time_remaining"] <= 10
    freezer.tick(timedelta(seconds=15))
    await rm.async_update()
    assert n(calls, "light", "turn_off") == 1
    assert calls[("light", "turn_off")][0].data["entity_id"] == L


async def test_salle_de_bain_900s_par_defaut(hass, freezer, calls):
    c = await _setup(hass, freezer, [room(room_type="bathroom", lights=[L])])
    rm = c.get_room_manager("r1")
    hass.states.async_set(L, "on")
    await rm.async_update()
    freezer.tick(timedelta(seconds=890))
    await rm.async_update()
    assert n(calls, "light", "turn_off") == 0
    freezer.tick(timedelta(seconds=15))
    await rm.async_update()
    assert n(calls, "light", "turn_off") == 1


async def test_delai_personnalise(hass, freezer, calls):
    c = await _setup(hass, freezer, [room(room_type="corridor", lights=[L], light_timeout=60)])
    rm = c.get_room_manager("r1")
    hass.states.async_set(L, "on")
    await rm.async_update()
    freezer.tick(timedelta(seconds=65))
    await rm.async_update()
    assert n(calls, "light", "turn_off") == 1


async def test_piece_normale_pas_extinction(hass, freezer, calls):
    c = await _setup(hass, freezer, [room(room_type="normal", lights=[L])])
    rm = c.get_room_manager("r1")
    hass.states.async_set(L, "on")
    await rm.async_update()
    freezer.tick(timedelta(hours=5))
    await rm.async_update()
    assert n(calls, "light", "turn_off") == 0
    assert rm.light_controller.get_state()["timer_active"] is False


async def test_timer_remis_a_zero(hass, freezer, calls):
    c = await _setup(hass, freezer, [room(room_type="corridor", lights=[L])])
    rm = c.get_room_manager("r1")
    hass.states.async_set(L, "on")
    await rm.async_update()
    freezer.tick(timedelta(seconds=200))
    hass.states.async_set(L, "off")
    await rm.async_update()
    assert rm.light_controller.get_state()["lights_tracked"] == 0
    hass.states.async_set(L, "on")
    await rm.async_update()
    freezer.tick(timedelta(seconds=200))
    await rm.async_update()
    assert n(calls, "light", "turn_off") == 0


async def test_switch_comme_lumiere(hass, freezer, calls):
    c = await _setup(hass, freezer, [room(room_type="corridor", lights=["switch.s"])])
    rm = c.get_room_manager("r1")
    hass.states.async_set("switch.s", "on")
    await rm.async_update()
    freezer.tick(timedelta(seconds=310))
    await rm.async_update()
    assert n(calls, "switch", "turn_off") == 1


# ---------- Groupe 4 : VMC ----------
def _bath(rid, light):
    return room(room_id=rid, room_name=rid, room_type="bathroom", lights=[light], light_timeout=1800)


async def test_vmc_cycle(hass, freezer, calls):
    c = await _setup(hass, freezer, [_bath("b1", L)], {"vmc_entity": VMC, "vmc_timer": 600})
    rm = c.get_room_manager("b1")
    hass.states.async_set(L, "off")
    await rm.async_update()
    hass.states.async_set(L, "on")
    await rm.async_update()
    assert n(calls, "switch", "turn_on") == 1
    assert rm.light_controller.get_state()["vmc_time_remaining"] == -1
    hass.states.async_set(L, "off")
    await rm.async_update()
    freezer.tick(timedelta(seconds=590))
    await rm.async_update()
    assert n(calls, "switch", "turn_off") == 0
    assert 0 < rm.light_controller.get_state()["vmc_time_remaining"] <= 10
    freezer.tick(timedelta(seconds=15))
    await rm.async_update()
    assert n(calls, "switch", "turn_off") == 1
    assert rm.light_controller.get_state()["vmc_active"] is False


async def test_vmc_rallumage_annule(hass, freezer, calls):
    c = await _setup(hass, freezer, [_bath("b1", L)], {"vmc_entity": VMC, "vmc_timer": 600})
    rm = c.get_room_manager("b1")
    hass.states.async_set(L, "off")
    await rm.async_update()
    hass.states.async_set(L, "on")
    await rm.async_update()
    hass.states.async_set(L, "off")
    await rm.async_update()
    freezer.tick(timedelta(seconds=300))
    hass.states.async_set(L, "on")
    await rm.async_update()
    freezer.tick(timedelta(seconds=400))
    await rm.async_update()
    assert n(calls, "switch", "turn_off") == 0


async def test_vmc_autre_sdb_active(hass, freezer, calls):
    c = await _setup(
        hass, freezer, [_bath("b1", "light.a"), _bath("b2", "light.b")],
        {"vmc_entity": VMC, "vmc_timer": 60},
    )
    b1, b2 = c.get_room_manager("b1"), c.get_room_manager("b2")
    for e in ("light.a", "light.b"):
        hass.states.async_set(e, "off")
    await b1.async_update(); await b2.async_update()
    hass.states.async_set("light.a", "on"); hass.states.async_set("light.b", "on")
    await b1.async_update(); await b2.async_update()
    hass.states.async_set("light.a", "off")
    await b1.async_update(); await b2.async_update()
    freezer.tick(timedelta(seconds=70))
    await b1.async_update(); await b2.async_update()
    assert n(calls, "switch", "turn_off") == 0  # b2 encore allumée
    hass.states.async_set("light.b", "off")
    await b1.async_update(); await b2.async_update()
    freezer.tick(timedelta(seconds=70))
    await b1.async_update(); await b2.async_update()
    assert n(calls, "switch", "turn_off") == 1


async def test_vmc_non_configuree(hass, freezer, calls):
    c = await _setup(hass, freezer, [_bath("b1", L)])
    rm = c.get_room_manager("b1")
    hass.states.async_set(L, "off"); await rm.async_update()
    hass.states.async_set(L, "on"); await rm.async_update()
    assert n(calls, "switch", "turn_on") == 0
