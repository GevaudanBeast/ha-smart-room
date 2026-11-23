"""Generic notifications for Smart Room Manager (v0.3.9).

SRM builds a short title and message (French or English, from the Home
Assistant language) and sends them to the targets chosen in the options:

* notify entities  -> notify.send_message (title + message only)
* legacy actions   -> notify.<service> (title, message and data)
* scripts          -> script.turn_on with variables

A global quiet period can redirect notifications to fallback targets (or
drop them). A cooldown limits repeats of the same type in the same room.
Every notification is also fired as the ``smart_room_manager_notification``
event, so users can route it themselves.
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_NOTIFICATIONS,
    CONF_NOTIFY_COOLDOWN,
    CONF_NOTIFY_ENTITIES,
    CONF_NOTIFY_QUIET_END,
    CONF_NOTIFY_QUIET_ENTITIES,
    CONF_NOTIFY_QUIET_SCRIPTS,
    CONF_NOTIFY_QUIET_SERVICES,
    CONF_NOTIFY_QUIET_START,
    CONF_NOTIFY_SCRIPTS,
    CONF_NOTIFY_SERVICES,
    CONF_NOTIFY_TYPES,
    CONF_ROOM_NOTIFY_ENTITIES,
    CONF_ROOM_NOTIFY_MODE,
    CONF_ROOM_NOTIFY_SCRIPTS,
    CONF_ROOM_NOTIFY_SERVICES,
    DEFAULT_NOTIFY_COOLDOWN,
    DEFAULT_NOTIFY_TYPES,
    EVENT_NOTIFICATION,
    NOTIFY_CONFIG_ISSUES,
    NOTIFY_FROST_PROTECTION,
    NOTIFY_HEATING_BLOCKED,
    NOTIFY_HEATING_UNBLOCKED,
    NOTIFY_MANUAL_OVERRIDE,
    NOTIFY_MANUAL_OVERRIDE_END,
    ROOM_NOTIFY_MODE_REPLACE,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

# Default texts. Placeholders: room, equip, windows, until, reason, count, details
MESSAGES: dict[str, dict[str, tuple[str, str]]] = {
    "fr": {
        NOTIFY_HEATING_BLOCKED: (
            "{room} : fenêtre ouverte",
            "{equip} attend la fermeture de la fenêtre{windows}.",
        ),
        NOTIFY_HEATING_UNBLOCKED: (
            "{room} : fenêtre fermée",
            "{equip} reprend.",
        ),
        NOTIFY_MANUAL_OVERRIDE: (
            "{room} : réglage manuel",
            "Réglage manuel détecté, la pièce est laissée telle quelle jusqu'à {until}.",
        ),
        NOTIFY_MANUAL_OVERRIDE_END: (
            "{room} : fin du réglage manuel",
            "Smart Room Manager reprend la gestion de la pièce.",
        ),
        NOTIFY_CONFIG_ISSUES: (
            "Smart Room Manager : configuration",
            "{count} anomalie(s) de configuration : {details}.",
        ),
        NOTIFY_FROST_PROTECTION: (
            "{room} : hors-gel",
            "La pièce passe en hors-gel ({reason}).",
        ),
    },
    "en": {
        NOTIFY_HEATING_BLOCKED: (
            "{room}: window open",
            "{equip} is waiting for the window to close{windows}.",
        ),
        NOTIFY_HEATING_UNBLOCKED: (
            "{room}: window closed",
            "{equip} resumes.",
        ),
        NOTIFY_MANUAL_OVERRIDE: (
            "{room}: manual change",
            "Manual change detected, the room is left as is until {until}.",
        ),
        NOTIFY_MANUAL_OVERRIDE_END: (
            "{room}: manual change ended",
            "Smart Room Manager manages the room again.",
        ),
        NOTIFY_CONFIG_ISSUES: (
            "Smart Room Manager: configuration",
            "{count} configuration issue(s): {details}.",
        ),
        NOTIFY_FROST_PROTECTION: (
            "{room}: frost protection",
            "The room switches to frost protection ({reason}).",
        ),
    },
}

WORDS = {
    "fr": {
        "heat": "Le chauffage",
        "cool": "La climatisation",
        "window": "fenêtre ouverte",
        "away": "absence",
        "issue": {
            "missing_entity": "entité introuvable",
            "unavailable_entity": "entité indisponible",
            "climate_without_actuator": "chauffage sans équipement",
            "multi_controller": "équipement piloté deux fois",
            "setpoint_below_eco": "consigne sous l'éco",
        },
    },
    "en": {
        "heat": "Heating",
        "cool": "Cooling",
        "window": "window open",
        "away": "away",
        "issue": {
            "missing_entity": "missing entity",
            "unavailable_entity": "unavailable entity",
            "climate_without_actuator": "heating without device",
            "multi_controller": "device driven twice",
            "setpoint_below_eco": "setpoint below eco",
        },
    },
}


def _lang(hass: HomeAssistant) -> str:
    return "fr" if (hass.config.language or "en").lower().startswith("fr") else "en"


def _parse_time(value: Any) -> time | None:
    if not value:
        return None
    if isinstance(value, time):
        return value
    try:
        parts = [int(p) for p in str(value).split(":")]
        return time(parts[0], parts[1] if len(parts) > 1 else 0)
    except (ValueError, IndexError):
        return None


def in_quiet_period(start: Any, end: Any, now: datetime) -> bool:
    """True when ``now`` (local) is inside [start, end), across midnight too."""
    t_start, t_end = _parse_time(start), _parse_time(end)
    if t_start is None or t_end is None or t_start == t_end:
        return False
    current = now.time().replace(second=0, microsecond=0)
    if t_start < t_end:
        return t_start <= current < t_end
    return current >= t_start or current < t_end


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return [v for v in value if v]


class Notifier:
    """Send SRM notifications to the configured targets."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._last_sent: dict[tuple[str, str], datetime] = {}

    # ---- configuration -------------------------------------------------
    @property
    def config(self) -> dict[str, Any]:
        return dict(self.entry.options.get(CONF_NOTIFICATIONS) or {})

    def enabled_types(self) -> list[str]:
        cfg = self.config
        if CONF_NOTIFY_TYPES in cfg:
            return list(cfg.get(CONF_NOTIFY_TYPES) or [])
        return list(DEFAULT_NOTIFY_TYPES)

    def targets_for(
        self, room_config: dict[str, Any] | None, quiet: bool
    ) -> dict[str, list[str]]:
        cfg = self.config
        if quiet:
            return {
                "entities": _as_list(cfg.get(CONF_NOTIFY_QUIET_ENTITIES)),
                "services": _as_list(cfg.get(CONF_NOTIFY_QUIET_SERVICES)),
                "scripts": _as_list(cfg.get(CONF_NOTIFY_QUIET_SCRIPTS)),
            }
        targets = {
            "entities": _as_list(cfg.get(CONF_NOTIFY_ENTITIES)),
            "services": _as_list(cfg.get(CONF_NOTIFY_SERVICES)),
            "scripts": _as_list(cfg.get(CONF_NOTIFY_SCRIPTS)),
        }
        if room_config:
            room_targets = {
                "entities": _as_list(room_config.get(CONF_ROOM_NOTIFY_ENTITIES)),
                "services": _as_list(room_config.get(CONF_ROOM_NOTIFY_SERVICES)),
                "scripts": _as_list(room_config.get(CONF_ROOM_NOTIFY_SCRIPTS)),
            }
            has_room = any(room_targets.values())
            if (
                has_room
                and room_config.get(CONF_ROOM_NOTIFY_MODE) == ROOM_NOTIFY_MODE_REPLACE
            ):
                targets = room_targets
            else:
                for key, values in room_targets.items():
                    targets[key] = targets[key] + [
                        v for v in values if v not in targets[key]
                    ]
        return targets

    # ---- texts ---------------------------------------------------------
    def build_text(self, ntype: str, values: dict[str, Any]) -> tuple[str, str]:
        lang = _lang(self.hass)
        words = WORDS[lang]
        title_tpl, message_tpl = MESSAGES[lang][ntype]
        windows = values.get("windows") or []
        fields = {
            "room": values.get("room_name") or "Smart Room Manager",
            "equip": (
                words["cool"] if values.get("direction") == "cool" else words["heat"]
            ),
            "windows": f" ({', '.join(windows)})" if windows else "",
            "until": values.get("until_text", ""),
            "reason": words.get(values.get("reason") or "", values.get("reason") or ""),
            "count": values.get("count", 0),
            "details": values.get("details", ""),
        }
        return title_tpl.format(**fields), message_tpl.format(**fields)

    @staticmethod
    def issue_details(hass: HomeAssistant, anomalies: list[dict[str, Any]]) -> str:
        words = WORDS[_lang(hass)]["issue"]
        parts = []
        for anomaly in anomalies[:5]:
            label = words.get(anomaly.get("code"), anomaly.get("code"))
            room = anomaly.get("room_name") or ""
            entity = anomaly.get("entity_id") or ""
            parts.append(
                " ".join(p for p in (f"{room} :" if room else "", label, entity) if p)
            )
        if len(anomalies) > 5:
            parts.append("…")
        return ", ".join(parts)

    # ---- sending -------------------------------------------------------
    def notify(
        self,
        ntype: str,
        room_config: dict[str, Any] | None = None,
        values: dict[str, Any] | None = None,
        entities: list[str] | None = None,
    ) -> bool:
        """Schedule a notification. Returns True if it passed the filters."""
        values = dict(values or {})
        if ntype not in self.enabled_types():
            return False
        room_id = (room_config or {}).get("room_id") or "_global"
        now = dt_util.utcnow()
        cooldown = int(
            self.config.get(CONF_NOTIFY_COOLDOWN, DEFAULT_NOTIFY_COOLDOWN) or 0
        )
        key = (room_id, ntype)
        last = self._last_sent.get(key)
        if cooldown and last and now - last < timedelta(minutes=cooldown):
            _LOGGER.debug("Notification %s for %s skipped (cooldown)", ntype, room_id)
            return False
        self._last_sent[key] = now

        if room_config:
            values.setdefault("room_name", room_config.get("room_name"))
        title, message = self.build_text(ntype, values)
        cfg = self.config
        quiet = in_quiet_period(
            cfg.get(CONF_NOTIFY_QUIET_START),
            cfg.get(CONF_NOTIFY_QUIET_END),
            dt_util.now(),
        )
        payload = {
            "type": ntype,
            "room_id": None if room_id == "_global" else room_id,
            "room_name": values.get("room_name"),
            "title": title,
            "message": message,
            "entities": list(entities or []),
            "quiet": quiet,
        }
        self.hass.bus.async_fire(EVENT_NOTIFICATION, dict(payload))
        targets = self.targets_for(room_config, quiet)
        if any(targets.values()):
            self.hass.async_create_task(self._async_send(targets, payload))
        return True

    async def _async_send(
        self, targets: dict[str, list[str]], payload: dict[str, Any]
    ) -> None:
        title, message = payload["title"], payload["message"]
        data = {k: payload[k] for k in ("type", "room_id", "room_name", "entities")}
        for entity_id in targets["entities"]:
            await self._call(
                "notify",
                "send_message",
                {"entity_id": entity_id, "title": title, "message": message},
            )
        for service in targets["services"]:
            domain, _, name = service.partition(".")
            if not name:
                domain, name = "notify", service
            await self._call(
                domain, name, {"title": title, "message": message, "data": data}
            )
        for script in targets["scripts"]:
            await self._call(
                "script",
                "turn_on",
                {
                    "entity_id": script,
                    "variables": {"title": title, "message": message, **data},
                },
            )

    async def _call(self, domain: str, service: str, data: dict[str, Any]) -> None:
        try:
            await self.hass.services.async_call(domain, service, data, blocking=False)
        except Exception as err:  # noqa: BLE001 - a bad target must not break SRM
            _LOGGER.warning("Notification to %s.%s failed: %s", domain, service, err)
