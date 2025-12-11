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

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_CREATE_BOARD,
    SERVICE_DELETE_BOARD,
    SERVICE_ADD_COLUMN,
    SERVICE_REORDER_COLUMNS,
    SERVICE_DELETE_COLUMN,
    SERVICE_CREATE_CARD,
    SERVICE_UPDATE_CARD,
    SERVICE_MOVE_CARD,
    SERVICE_DELETE_CARD,
)
from .coordinator import KanbanCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
SCHEMA_CREATE_BOARD = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("columns"): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_DELETE_BOARD = vol.Schema(
    {
        vol.Required("board_id"): cv.string,
    }
)

SCHEMA_ADD_COLUMN = vol.Schema(
    {
        vol.Required("board_id"): cv.string,
        vol.Required("name"): cv.string,
        vol.Optional("position"): cv.positive_int,
        vol.Optional("color"): cv.string,
    }
)

SCHEMA_REORDER_COLUMNS = vol.Schema(
    {
        vol.Required("board_id"): cv.string,
        vol.Required("column_ids"): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_DELETE_COLUMN = vol.Schema(
    {
        vol.Required("column_id"): cv.string,
    }
)

SCHEMA_CREATE_CARD = vol.Schema(
    {
        vol.Required("column_id"): cv.string,
        vol.Required("title"): cv.string,
        vol.Optional("description"): cv.string,
        vol.Optional("assignee"): cv.string,
        vol.Optional("due_date"): cv.string,  # ISO format date
        vol.Optional("labels"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("position"): cv.positive_int,
    }
)

SCHEMA_UPDATE_CARD = vol.Schema(
    {
        vol.Required("card_id"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("description"): cv.string,
        vol.Optional("assignee"): cv.string,
        vol.Optional("due_date"): cv.string,
        vol.Optional("labels"): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_MOVE_CARD = vol.Schema(
    {
        vol.Required("card_id"): cv.string,
        vol.Required("target_column_id"): cv.string,
        vol.Required("position"): cv.positive_int,
    }
)

SCHEMA_DELETE_CARD = vol.Schema(
    {
        vol.Required("card_id"): cv.string,
    }
)


def _get_coordinator(hass: HomeAssistant) -> KanbanCoordinator | None:
    """Get the first available coordinator."""
    if DOMAIN not in hass.data:
        return None
    coordinators = hass.data[DOMAIN]
    if not coordinators:
        return None
    return next(iter(coordinators.values()), None)


def _get_user_id(call: ServiceCall) -> str:
    """Get the user ID from the service call context."""
    if call.context.user_id:
        return call.context.user_id
    return "unknown"


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register HA Kanban services."""

    async def handle_create_board(call: ServiceCall) -> None:
        """Handle create_board service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("No Kanban coordinator available")
            return

        name = call.data["name"]
        columns = call.data.get("columns")
        user_id = _get_user_id(call)

        board = await coordinator.async_create_board(
            name=name,
            created_by=user_id,
            columns=columns,
        )
        _LOGGER.info("Created board '%s' with ID %s", name, board.id)

    async def handle_delete_board(call: ServiceCall) -> None:
        """Handle delete_board service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        board_id = call.data["board_id"]
        await coordinator.async_delete_board(board_id)
        _LOGGER.info("Deleted board %s", board_id)

    async def handle_add_column(call: ServiceCall) -> None:
        """Handle add_column service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        column = await coordinator.async_add_column(
            board_id=call.data["board_id"],
            name=call.data["name"],
            position=call.data.get("position"),
            color=call.data.get("color"),
        )
        if column:
            _LOGGER.info("Added column '%s' with ID %s", column.name, column.id)

    async def handle_reorder_columns(call: ServiceCall) -> None:
        """Handle reorder_columns service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        await coordinator.async_reorder_columns(
            board_id=call.data["board_id"],
            column_ids=call.data["column_ids"],
        )
        _LOGGER.info("Reordered columns for board %s", call.data["board_id"])

    async def handle_delete_column(call: ServiceCall) -> None:
        """Handle delete_column service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        await coordinator.async_delete_column(call.data["column_id"])
        _LOGGER.info("Deleted column %s", call.data["column_id"])

    async def handle_create_card(call: ServiceCall) -> None:
        """Handle create_card service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        user_id = _get_user_id(call)
        card = await coordinator.async_create_card(
            column_id=call.data["column_id"],
            title=call.data["title"],
            created_by=user_id,
            description=call.data.get("description"),
            assignee=call.data.get("assignee"),
            due_date=call.data.get("due_date"),
            labels=call.data.get("labels"),
            position=call.data.get("position"),
        )
        if card:
            _LOGGER.info("Created card '%s' with ID %s", card.title, card.id)

    async def handle_update_card(call: ServiceCall) -> None:
        """Handle update_card service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        card_id = call.data["card_id"]
        updates = {k: v for k, v in call.data.items() if k != "card_id"}
        
        card = await coordinator.async_update_card(card_id, **updates)
        if card:
            _LOGGER.info("Updated card %s", card_id)

    async def handle_move_card(call: ServiceCall) -> None:
        """Handle move_card service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        user_id = _get_user_id(call)
        card = await coordinator.async_move_card(
            card_id=call.data["card_id"],
            target_column_id=call.data["target_column_id"],
            position=call.data["position"],
            moved_by=user_id,
        )
        if card:
            _LOGGER.info(
                "Moved card %s to column %s at position %d",
                call.data["card_id"],
                call.data["target_column_id"],
                call.data["position"],
            )

    async def handle_delete_card(call: ServiceCall) -> None:
        """Handle delete_card service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return

        await coordinator.async_delete_card(call.data["card_id"])
        _LOGGER.info("Deleted card %s", call.data["card_id"])

    # Register all services
    hass.services.async_register(DOMAIN, SERVICE_CREATE_BOARD, handle_create_board, SCHEMA_CREATE_BOARD)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_BOARD, handle_delete_board, SCHEMA_DELETE_BOARD)
    hass.services.async_register(DOMAIN, SERVICE_ADD_COLUMN, handle_add_column, SCHEMA_ADD_COLUMN)
    hass.services.async_register(DOMAIN, SERVICE_REORDER_COLUMNS, handle_reorder_columns, SCHEMA_REORDER_COLUMNS)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_COLUMN, handle_delete_column, SCHEMA_DELETE_COLUMN)
    hass.services.async_register(DOMAIN, SERVICE_CREATE_CARD, handle_create_card, SCHEMA_CREATE_CARD)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_CARD, handle_update_card, SCHEMA_UPDATE_CARD)
    hass.services.async_register(DOMAIN, SERVICE_MOVE_CARD, handle_move_card, SCHEMA_MOVE_CARD)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_CARD, handle_delete_card, SCHEMA_DELETE_CARD)

    _LOGGER.info("Registered HA Kanban services")
