"""The Smart Room Manager integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from datetime import timedelta

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.start import async_at_started

from .const import CONF_ROOM_ID, CONF_ROOMS, DOMAIN, NOTIFY_CONFIG_ISSUES, VERSION
from .coordinator import SmartRoomCoordinator
from .diagnostics_check import check_rooms, issue_id

DIAGNOSTIC_INTERVAL = timedelta(minutes=15)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


def _clean_none_values_from_config(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean None values from room configurations (migration from v0.2.1).

    In v0.2.1 and earlier, optional fields were saved with None values.
    This function removes those None values to prevent 'Entity None' errors.
    """
    rooms = list(entry.options.get("rooms", []))
    cleaned = False

    for room in rooms:
        # List of optional fields that should not be saved as None
        optional_fields = [
            "door_window_sensors",  # Added: can be None instead of []
            "lights",  # Added: can be None instead of []
            "temperature_sensor",
            "humidity_sensor",
            "climate_entity",
            "climate_bypass_switch",
        ]

        for field in optional_fields:
            if field in room and room[field] is None:
                del room[field]
                cleaned = True
                _LOGGER.debug(
                    "Cleaned None value for field '%s' in room '%s'",
                    field,
                    room.get("room_name", "unknown"),
                )

    # Update the config entry if we cleaned anything
    if cleaned:
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, "rooms": rooms},
        )
        _LOGGER.info("Cleaned None values from room configurations (v0.2.1 migration)")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Room Manager from a config entry."""
    _LOGGER.debug("Setting up Smart Room Manager integration")

    hass.data.setdefault(DOMAIN, {})

    # Clean up None values from old configurations (v0.2.1 migration)
    _clean_none_values_from_config(hass, entry)

    # Create coordinator
    coordinator = SmartRoomCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_setup_listeners()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register device for the integration
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Smart Room Manager",
        manufacturer="HA-SMART",
        model="Room Manager",
        sw_version=VERSION,
    )

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options flow
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Register services
    register_services(hass, entry)

    # v0.3.9: configuration diagnostics (repair issues + anomalies sensor)
    async def _run_diagnostics(*_args) -> None:
        async_update_diagnostics(hass, entry, coordinator)

    entry.async_on_unload(async_at_started(hass, _run_diagnostics))
    entry.async_on_unload(
        async_track_time_interval(hass, _run_diagnostics, DIAGNOSTIC_INTERVAL)
    )

    _LOGGER.info("Smart Room Manager integration setup completed")
    return True


def async_update_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: SmartRoomCoordinator
) -> list[dict]:
    """Check the configuration, sync repair issues and the anomalies sensor."""
    anomalies = check_rooms(hass, entry.options.get(CONF_ROOMS, []), dict(entry.data))
    wanted = {issue_id(a): a for a in anomalies}
    registry = ir.async_get(hass)
    for domain, existing_id in list(registry.issues):
        if domain == DOMAIN and existing_id not in wanted:
            ir.async_delete_issue(hass, DOMAIN, existing_id)
    for iid, anomaly in wanted.items():
        ir.async_create_issue(
            hass,
            DOMAIN,
            iid,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=anomaly["code"],
            translation_placeholders={
                "room": str(anomaly.get("room_name")),
                "entity": str(anomaly.get("entity_id") or ""),
                "other": str(anomaly.get("other", "")),
                "comfort": str(anomaly.get("comfort", "")),
                "eco": str(anomaly.get("eco", "")),
            },
        )
    coordinator.anomalies = anomalies
    coordinator.async_update_listeners()
    # v0.3.9: log only when the set of anomalies changes (not every 15 min)
    previous_ids = getattr(coordinator, "_last_anomaly_ids", None)
    new_ids = set(wanted) - (previous_ids or set())
    notifier = getattr(coordinator, "notifier", None)
    if new_ids and notifier is not None:
        new_anomalies = [wanted[i] for i in wanted if i in new_ids]
        notifier.notify(
            NOTIFY_CONFIG_ISSUES,
            None,
            {
                "count": len(new_anomalies),
                "details": notifier.issue_details(hass, new_anomalies),
            },
            [a.get("entity_id") for a in new_anomalies if a.get("entity_id")],
        )
    if set(wanted) != previous_ids:
        coordinator._last_anomaly_ids = set(wanted)
        if anomalies:
            _LOGGER.warning(
                "Smart Room Manager: %d configuration anomalies", len(anomalies)
            )
        elif previous_ids:
            _LOGGER.info("Smart Room Manager: no configuration anomaly left")
    return anomalies


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Smart Room Manager integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: SmartRoomCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Stop the coordinator
        await coordinator.async_shutdown()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Options updated, reloading integration")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # Migration logic if needed in future
        _LOGGER.info("Migration to version %s successful", config_entry.version)
        return True

    return False


async def async_cleanup_orphaned_entities(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, int]:
    """Clean up orphaned entities and devices that no longer belong to any configured room.

    Returns a dict with counts of entities and devices found and removed.
    """
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    # Get all configured room IDs
    rooms = entry.options.get(CONF_ROOMS, [])
    configured_room_ids = {
        room.get(CONF_ROOM_ID) for room in rooms if room.get(CONF_ROOM_ID)
    }

    # Find all entities belonging to this integration
    entities_to_remove = []
    orphaned_room_ids = set()
    for entity_entry in list(entity_registry.entities.values()):
        if entity_entry.platform != DOMAIN:
            continue

        # Extract room_id from unique_id (format: smart_room_{room_id}_{suffix})
        unique_id = entity_entry.unique_id
        if unique_id and unique_id.startswith("smart_room_"):
            parts = unique_id.split("_")
            if len(parts) >= 3:
                # room_id is the 3rd part (index 2)
                room_id = parts[2]
                if room_id not in configured_room_ids:
                    entities_to_remove.append(entity_entry)
                    orphaned_room_ids.add(room_id)
                    _LOGGER.debug(
                        "Found orphaned entity: %s (room_id: %s)",
                        entity_entry.entity_id,
                        room_id,
                    )

    # Remove orphaned entities
    removed_entities = 0
    for entity_entry in entities_to_remove:
        try:
            entity_registry.async_remove(entity_entry.entity_id)
            removed_entities += 1
            _LOGGER.info("Removed orphaned entity: %s", entity_entry.entity_id)
        except Exception as err:
            _LOGGER.warning(
                "Failed to remove entity %s: %s", entity_entry.entity_id, err
            )

    # Remove orphaned devices
    removed_devices = 0
    for room_id in orphaned_room_ids:
        device = device_registry.async_get_device(identifiers={(DOMAIN, room_id)})
        if device:
            try:
                device_registry.async_remove_device(device.id)
                removed_devices += 1
                _LOGGER.info("Removed orphaned device for room_id: %s", room_id)
            except Exception as err:
                _LOGGER.warning(
                    "Failed to remove device for room_id %s: %s", room_id, err
                )

    # Also check for orphaned devices that have no entities left
    for device_entry in list(device_registry.devices.values()):
        for identifier in device_entry.identifiers:
            if identifier[0] == DOMAIN and identifier[1] not in configured_room_ids:
                # This is an orphaned device
                if identifier[1] not in orphaned_room_ids:
                    try:
                        device_registry.async_remove_device(device_entry.id)
                        removed_devices += 1
                        _LOGGER.info(
                            "Removed orphaned device: %s (room_id: %s)",
                            device_entry.name,
                            identifier[1],
                        )
                    except Exception as err:
                        _LOGGER.warning(
                            "Failed to remove device %s: %s", device_entry.name, err
                        )

    return {
        "entities_found": len(entities_to_remove),
        "entities_removed": removed_entities,
        "devices_removed": removed_devices,
    }


def register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register integration services."""

    async def handle_cleanup_entities(call: ServiceCall) -> None:
        """Handle the cleanup_entities service call."""
        result = await async_cleanup_orphaned_entities(hass, entry)
        _LOGGER.info(
            "Cleanup completed: found %d orphaned entities, removed %d entities and %d devices",
            result["entities_found"],
            result["entities_removed"],
            result["devices_removed"],
        )
        # Create a persistent notification with the result
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Smart Room Manager - Nettoyage",
                "message": (
                    f"Nettoyage terminé :\n"
                    f"- Entités orphelines trouvées : {result['entities_found']}\n"
                    f"- Entités supprimées : {result['entities_removed']}\n"
                    f"- Appareils supprimés : {result['devices_removed']}"
                ),
                "notification_id": "smart_room_cleanup",
            },
        )

    # Register the service if not already registered
    if not hass.services.has_service(DOMAIN, "cleanup_entities"):
        hass.services.async_register(
            DOMAIN, "cleanup_entities", handle_cleanup_entities
        )
