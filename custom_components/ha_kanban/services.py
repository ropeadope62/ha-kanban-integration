"""
Project: HA Kanban Integration
Module: Service Handlers (services.py)
Author: Dave C. (ropeadope62)
https://github.com/ropeadope62
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Service schemas
CREATE_BOARD_SCHEMA = vol.Schema({
    vol.Required("name"): cv.string,
    vol.Required("columns"): vol.All(cv.ensure_list, [cv.string]),
})

DELETE_BOARD_SCHEMA = vol.Schema({
    vol.Required("board_id"): cv.string,
})

ADD_COLUMN_SCHEMA = vol.Schema({
    vol.Required("board_id"): cv.string,
    vol.Required("name"): cv.string,
    vol.Optional("position"): cv.positive_int,
})

CREATE_CARD_SCHEMA = vol.Schema({
    vol.Required("column_id"): cv.string,
    vol.Required("title"): cv.string,
    vol.Optional("description"): cv.string,
    vol.Optional("assignee"): cv.string,
    vol.Optional("due_date"): cv.string,
    vol.Optional("labels"): vol.All(cv.ensure_list, [cv.string]),
})

UPDATE_CARD_SCHEMA = vol.Schema({
    vol.Required("card_id"): cv.string,
    vol.Optional("title"): cv.string,
    vol.Optional("description"): cv.string,
    vol.Optional("assignee"): cv.string,
    vol.Optional("due_date"): cv.string,
    vol.Optional("labels"): vol.All(cv.ensure_list, [cv.string]),
})

MOVE_CARD_SCHEMA = vol.Schema({
    vol.Required("card_id"): cv.string,
    vol.Required("target_column_id"): cv.string,
    vol.Optional("position"): cv.positive_int,
})

DELETE_CARD_SCHEMA = vol.Schema({
    vol.Required("card_id"): cv.string,
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for HA Kanban."""
    
    async def handle_create_board(call: ServiceCall) -> None:
        """Handle create_board service call."""
        _LOGGER.info("Creating board: %s", call.data)
        # Get coordinator from first entry
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            _LOGGER.error("No HA Kanban integration configured")
            return
        
        coordinator = hass.data[DOMAIN][entries[0].entry_id]
        board = await coordinator.async_create_board(
            call.data["name"],
            call.data["columns"]
        )
        _LOGGER.info("Board created: %s", board.id)
    
    async def handle_delete_board(call: ServiceCall) -> None:
        """Handle delete_board service call."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        coordinator = hass.data[DOMAIN][entries[0].entry_id]
        await coordinator.async_delete_board(call.data["board_id"])
    
    async def handle_add_column(call: ServiceCall) -> None:
        """Handle add_column service call."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        coordinator = hass.data[DOMAIN][entries[0].entry_id]
        await coordinator.async_add_column(
            call.data["board_id"],
            call.data["name"],
            call.data.get("position")
        )
    
    async def handle_create_card(call: ServiceCall) -> None:
        """Handle create_card service call."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        coordinator = hass.data[DOMAIN][entries[0].entry_id]
        await coordinator.async_create_card(
            call.data["column_id"],
            call.data["title"],
            call.data.get("description"),
            call.data.get("assignee"),
            call.data.get("due_date"),
            call.data.get("labels", [])
        )
    
    async def handle_update_card(call: ServiceCall) -> None:
        """Handle update_card service call."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        coordinator = hass.data[DOMAIN][entries[0].entry_id]
        await coordinator.async_update_card(
            call.data["card_id"],
            call.data.get("title"),
            call.data.get("description"),
            call.data.get("assignee"),
            call.data.get("due_date"),
            call.data.get("labels")
        )
    
    async def handle_move_card(call: ServiceCall) -> None:
        """Handle move_card service call."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        coordinator = hass.data[DOMAIN][entries[0].entry_id]
        await coordinator.async_move_card(
            call.data["card_id"],
            call.data["target_column_id"],
            call.data.get("position")
        )
    
    async def handle_delete_card(call: ServiceCall) -> None:
        """Handle delete_card service call."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return
        coordinator = hass.data[DOMAIN][entries[0].entry_id]
        await coordinator.async_delete_card(call.data["card_id"])
    
    # Register all services
    hass.services.async_register(
        DOMAIN, "create_board", handle_create_board, schema=CREATE_BOARD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "delete_board", handle_delete_board, schema=DELETE_BOARD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "add_column", handle_add_column, schema=ADD_COLUMN_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "create_card", handle_create_card, schema=CREATE_CARD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "update_card", handle_update_card, schema=UPDATE_CARD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "move_card", handle_move_card, schema=MOVE_CARD_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "delete_card", handle_delete_card, schema=DELETE_CARD_SCHEMA
    )
    
    _LOGGER.info("HA Kanban services registered")