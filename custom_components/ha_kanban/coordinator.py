"""
Project: HA Kanban Integration
Module: Data Coordinator (coordinator.py)
Author: Dave C. (ropeadope62)
https://github.com/ropeadope62
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .storage import KanbanStorage
from .models import Board, Column, Card

_LOGGER = logging.getLogger(__name__)


class KanbanCoordinator:
    """Coordinate Kanban data and subscriptions."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.storage = KanbanStorage(hass)
        self._subscribers: dict[str, set[Callable]] = {}  # board_id -> set of callbacks

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        await self.storage.async_load()
        _LOGGER.info("HA Kanban coordinator initialized")

    # Subscription management for real-time updates

    @callback
    def subscribe(self, board_id: str, callback_fn: Callable) -> Callable[[], None]:
        """Subscribe to board updates. Returns unsubscribe function."""
        if board_id not in self._subscribers:
            self._subscribers[board_id] = set()
        self._subscribers[board_id].add(callback_fn)

        def unsubscribe() -> None:
            self._subscribers[board_id].discard(callback_fn)
            if not self._subscribers[board_id]:
                del self._subscribers[board_id]

        return unsubscribe

    async def _notify_subscribers(self, board_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Notify all subscribers of a board about an event."""
        if board_id not in self._subscribers:
            return

        message = {"type": event_type, **data}
        for callback_fn in self._subscribers[board_id]:
            try:
                callback_fn(message)
            except Exception:
                _LOGGER.exception("Error notifying subscriber")

    # Board operations

    def get_boards(self) -> list[Board]:
        """Get all boards."""
        return self.storage.get_boards()

    def get_board(self, board_id: str) -> Board | None:
        """Get a specific board."""
        return self.storage.get_board(board_id)

    def get_full_board(self, board_id: str) -> dict[str, Any] | None:
        """Get complete board data for frontend."""
        return self.storage.get_full_board(board_id)

    async def async_create_board(
        self, name: str, created_by: str, columns: list[str] | None = None
    ) -> Board:
        """Create a new board with optional initial columns."""
        from .const import DEFAULT_COLUMNS

        board = Board.create(name=name, created_by=created_by)
        await self.storage.async_create_board(board)

        # Create initial columns
        column_names = columns or DEFAULT_COLUMNS
        for position, col_name in enumerate(column_names):
            column = Column.create(
                board_id=board.id,
                name=col_name,
                position=position,
            )
            await self.storage.async_create_column(column)

        # Reload board to get column IDs
        board = self.storage.get_board(board.id)
        return board

    async def async_delete_board(self, board_id: str) -> None:
        """Delete a board."""
        await self.storage.async_delete_board(board_id)
        await self._notify_subscribers(board_id, "board_deleted", {"board_id": board_id})

    # Column operations

    async def async_add_column(
        self, board_id: str, name: str, position: int | None = None, color: str | None = None
    ) -> Column | None:
        """Add a column to a board."""
        board = self.storage.get_board(board_id)
        if not board:
            return None

        if position is None:
            position = len(board.column_ids)

        column = Column.create(
            board_id=board_id,
            name=name,
            position=position,
            color=color,
        )
        await self.storage.async_create_column(column)

        await self._notify_subscribers(board_id, "column_added", {"column": column.to_dict()})
        return column

    async def async_reorder_columns(self, board_id: str, column_ids: list[str]) -> None:
        """Reorder columns in a board."""
        await self.storage.async_reorder_columns(board_id, column_ids)
        await self._notify_subscribers(
            board_id, "columns_reordered", {"column_ids": column_ids}
        )

    async def async_delete_column(self, column_id: str) -> None:
        """Delete a column."""
        column = self.storage.get_column(column_id)
        if not column:
            return

        board_id = column.board_id
        await self.storage.async_delete_column(column_id)
        await self._notify_subscribers(
            board_id, "column_deleted", {"column_id": column_id}
        )

    # Card operations

    async def async_create_card(
        self,
        column_id: str,
        title: str,
        created_by: str,
        description: str | None = None,
        assignee: str | None = None,
        due_date: str | None = None,
        labels: list[str] | None = None,
        position: int | None = None,
    ) -> Card | None:
        """Create a new card."""
        from datetime import date as date_type

        column = self.storage.get_column(column_id)
        if not column:
            return None

        if position is None:
            position = len(column.card_ids)

        parsed_due_date = None
        if due_date:
            parsed_due_date = date_type.fromisoformat(due_date)

        card = Card.create(
            column_id=column_id,
            title=title,
            position=position,
            created_by=created_by,
            description=description,
            assignee=assignee,
            due_date=parsed_due_date,
            labels=labels,
        )
        await self.storage.async_create_card(card)

        board_id = column.board_id
        await self._notify_subscribers(
            board_id, "card_created", {"card": card.to_dict()}
        )
        return card

    async def async_update_card(self, card_id: str, **updates) -> Card | None:
        """Update a card's properties."""
        from datetime import date as date_type

        card = self.storage.get_card(card_id)
        if not card:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(card, key) and value is not None:
                if key == "due_date" and isinstance(value, str):
                    value = date_type.fromisoformat(value)
                setattr(card, key, value)

        await self.storage.async_update_card(card)

        column = self.storage.get_column(card.column_id)
        if column:
            await self._notify_subscribers(
                column.board_id, "card_updated", {"card": card.to_dict()}
            )
        return card

    async def async_move_card(
        self, card_id: str, target_column_id: str, position: int, moved_by: str
    ) -> Card | None:
        """Move a card to a new column/position."""
        card = self.storage.get_card(card_id)
        if not card:
            return None

        from_column_id = card.column_id
        card = await self.storage.async_move_card(card_id, target_column_id, position)

        if card:
            column = self.storage.get_column(target_column_id)
            if column:
                await self._notify_subscribers(
                    column.board_id,
                    "card_moved",
                    {
                        "card_id": card_id,
                        "from_column": from_column_id,
                        "to_column": target_column_id,
                        "position": position,
                        "moved_by": moved_by,
                    },
                )
        return card

    async def async_delete_card(self, card_id: str) -> None:
        """Delete a card."""
        card = self.storage.get_card(card_id)
        if not card:
            return

        column = self.storage.get_column(card.column_id)
        await self.storage.async_delete_card(card_id)

        if column:
            await self._notify_subscribers(
                column.board_id, "card_deleted", {"card_id": card_id}
            )
