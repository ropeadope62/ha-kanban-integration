"""
Project: HA Kanban Integration
Module: Integration Initialization (__init__.py)
Author: Dave C. (ropeadope62)
https://github.com/ropeadope62
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import KanbanCoordinator
from .services import async_register_services
from .websocket_api import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Kanban from a config entry."""
    _LOGGER.info("Setting up HA Kanban integration")

    # Initialize coordinator
    coordinator = KanbanCoordinator(hass, entry)
    await coordinator.async_setup()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register services (only once)
    if len(hass.data[DOMAIN]) == 1:
        async_register_services(hass)
        async_register_websocket_api(hass)

    _LOGGER.info("HA Kanban integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading HA Kanban integration")

    # Remove coordinator
    hass.data[DOMAIN].pop(entry.entry_id)

    # If no more entries, cleanup is complete
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
