"""
Project: HA Kanban Integration
Module: WebSocket API (websocket_api.py)
Author: Dave C. (ropeadope62)
https://github.com/ropeadope62
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, WS_TYPE_SUBSCRIBE, WS_TYPE_UNSUBSCRIBE
from .coordinator import KanbanCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_coordinator(hass: HomeAssistant) -> KanbanCoordinator | None:
    """Get the first available coordinator."""
    if DOMAIN not in hass.data:
        return None
    coordinators = hass.data[DOMAIN]
    if not coordinators:
        return None
    return next(iter(coordinators.values()), None)


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register WebSocket API handlers."""

    @websocket_api.websocket_command(
        {
            vol.Required("type"): WS_TYPE_SUBSCRIBE,
            vol.Required("board_id"): str,
        }
    )
    @websocket_api.async_response
    async def ws_subscribe(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """Subscribe to board updates."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            connection.send_error(msg["id"], "not_ready", "Kanban not initialized")
            return

        board_id = msg["board_id"]
        board_data = coordinator.get_full_board(board_id)
        
        if not board_data:
            connection.send_error(msg["id"], "not_found", f"Board {board_id} not found")
            return

        @callback
        def forward_event(event_data: dict[str, Any]) -> None:
            """Forward events to the WebSocket connection."""
            connection.send_message(
                websocket_api.event_message(msg["id"], event_data)
            )

        # Subscribe and store unsubscribe function
        unsubscribe = coordinator.subscribe(board_id, forward_event)

        @callback
        def on_close() -> None:
            """Handle connection close."""
            unsubscribe()

        connection.subscriptions[msg["id"]] = on_close

        # Send initial board data
        connection.send_result(msg["id"], board_data)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/get_boards",
        }
    )
    @websocket_api.async_response
    async def ws_get_boards(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """Get all boards."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            connection.send_error(msg["id"], "not_ready", "Kanban not initialized")
            return

        boards = coordinator.get_boards()
        connection.send_result(msg["id"], [b.to_dict() for b in boards])

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/get_board",
            vol.Required("board_id"): str,
        }
    )
    @websocket_api.async_response
    async def ws_get_board(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """Get a specific board with all data."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            connection.send_error(msg["id"], "not_ready", "Kanban not initialized")
            return

        board_data = coordinator.get_full_board(msg["board_id"])
        if not board_data:
            connection.send_error(msg["id"], "not_found", "Board not found")
            return

        connection.send_result(msg["id"], board_data)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/create_card",
            vol.Required("column_id"): str,
            vol.Required("title"): str,
            vol.Optional("description"): str,
            vol.Optional("assignee"): str,
            vol.Optional("due_date"): str,
            vol.Optional("labels"): [str],
            vol.Optional("position"): int,
        }
    )
    @websocket_api.async_response
    async def ws_create_card(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """Create a new card via WebSocket."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            connection.send_error(msg["id"], "not_ready", "Kanban not initialized")
            return

        user_id = connection.user.id if connection.user else "unknown"
        
        card = await coordinator.async_create_card(
            column_id=msg["column_id"],
            title=msg["title"],
            created_by=user_id,
            description=msg.get("description"),
            assignee=msg.get("assignee"),
            due_date=msg.get("due_date"),
            labels=msg.get("labels"),
            position=msg.get("position"),
        )

        if card:
            connection.send_result(msg["id"], card.to_dict())
        else:
            connection.send_error(msg["id"], "create_failed", "Failed to create card")

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/move_card",
            vol.Required("card_id"): str,
            vol.Required("target_column_id"): str,
            vol.Required("position"): int,
        }
    )
    @websocket_api.async_response
    async def ws_move_card(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """Move a card via WebSocket."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            connection.send_error(msg["id"], "not_ready", "Kanban not initialized")
            return

        user_id = connection.user.id if connection.user else "unknown"

        card = await coordinator.async_move_card(
            card_id=msg["card_id"],
            target_column_id=msg["target_column_id"],
            position=msg["position"],
            moved_by=user_id,
        )

        if card:
            connection.send_result(msg["id"], card.to_dict())
        else:
            connection.send_error(msg["id"], "move_failed", "Failed to move card")

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/update_card",
            vol.Required("card_id"): str,
            vol.Optional("title"): str,
            vol.Optional("description"): str,
            vol.Optional("assignee"): str,
            vol.Optional("due_date"): str,
            vol.Optional("labels"): [str],
        }
    )
    @websocket_api.async_response
    async def ws_update_card(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """Update a card via WebSocket."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            connection.send_error(msg["id"], "not_ready", "Kanban not initialized")
            return

        card_id = msg["card_id"]
        updates = {k: v for k, v in msg.items() if k not in ("id", "type", "card_id")}

        card = await coordinator.async_update_card(card_id, **updates)

        if card:
            connection.send_result(msg["id"], card.to_dict())
        else:
            connection.send_error(msg["id"], "update_failed", "Failed to update card")

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/delete_card",
            vol.Required("card_id"): str,
        }
    )
    @websocket_api.async_response
    async def ws_delete_card(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """Delete a card via WebSocket."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            connection.send_error(msg["id"], "not_ready", "Kanban not initialized")
            return

        await coordinator.async_delete_card(msg["card_id"])
        connection.send_result(msg["id"], {"success": True})

    # Register all WebSocket handlers
    websocket_api.async_register_command(hass, ws_subscribe)
    websocket_api.async_register_command(hass, ws_get_boards)
    websocket_api.async_register_command(hass, ws_get_board)
    websocket_api.async_register_command(hass, ws_create_card)
    websocket_api.async_register_command(hass, ws_move_card)
    websocket_api.async_register_command(hass, ws_update_card)
    websocket_api.async_register_command(hass, ws_delete_card)

    _LOGGER.info("Registered HA Kanban WebSocket API")
