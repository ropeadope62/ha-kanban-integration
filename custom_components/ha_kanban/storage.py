"""
Project: HA Kanban Integration
Module: Storage Layer (storage.py)
Author: Dave C. (ropeadope62)
https://github.com/ropeadope62
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .models import Board, Column, Card

_LOGGER = logging.getLogger(__name__)


class KanbanStorage:
    """Handle storage of Kanban data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the storage."""
        self.hass = hass
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {
            "boards": {},
            "columns": {},
            "cards": {},
        }

    async def async_load(self) -> None:
        """Load data from storage."""
        stored = await self._store.async_load()
        if stored:
            self._data = stored
        _LOGGER.debug("Loaded Kanban data: %s boards", len(self._data.get("boards", {})))

    async def async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(self._data)

    # Board operations
    
    def get_boards(self) -> list[Board]:
        """Get all boards."""
        return [Board.from_dict(b) for b in self._data["boards"].values()]

    def get_board(self, board_id: str) -> Board | None:
        """Get a specific board."""
        data = self._data["boards"].get(board_id)
        return Board.from_dict(data) if data else None

    async def async_create_board(self, board: Board) -> Board:
        """Create a new board."""
        self._data["boards"][board.id] = board.to_dict()
        await self.async_save()
        return board

    async def async_update_board(self, board: Board) -> Board:
        """Update an existing board."""
        self._data["boards"][board.id] = board.to_dict()
        await self.async_save()
        return board

    async def async_delete_board(self, board_id: str) -> None:
        """Delete a board and all its columns and cards."""
        board = self.get_board(board_id)
        if not board:
            return

        # Delete all cards in all columns
        for column_id in board.column_ids:
            column = self.get_column(column_id)
            if column:
                for card_id in column.card_ids:
                    self._data["cards"].pop(card_id, None)
                self._data["columns"].pop(column_id, None)

        self._data["boards"].pop(board_id, None)
        await self.async_save()

    # Column operations

    def get_columns(self, board_id: str) -> list[Column]:
        """Get all columns for a board."""
        board = self.get_board(board_id)
        if not board:
            return []
        return [
            Column.from_dict(self._data["columns"][cid])
            for cid in board.column_ids
            if cid in self._data["columns"]
        ]

    def get_column(self, column_id: str) -> Column | None:
        """Get a specific column."""
        data = self._data["columns"].get(column_id)
        return Column.from_dict(data) if data else None

    async def async_create_column(self, column: Column) -> Column:
        """Create a new column."""
        self._data["columns"][column.id] = column.to_dict()
        
        # Add to board's column list
        board = self.get_board(column.board_id)
        if board:
            board.column_ids.append(column.id)
            self._data["boards"][board.id] = board.to_dict()
        
        await self.async_save()
        return column

    async def async_update_column(self, column: Column) -> Column:
        """Update an existing column."""
        self._data["columns"][column.id] = column.to_dict()
        await self.async_save()
        return column

    async def async_delete_column(self, column_id: str) -> None:
        """Delete a column and all its cards."""
        column = self.get_column(column_id)
        if not column:
            return

        # Delete all cards in column
        for card_id in column.card_ids:
            self._data["cards"].pop(card_id, None)

        # Remove from board's column list
        board = self.get_board(column.board_id)
        if board and column_id in board.column_ids:
            board.column_ids.remove(column_id)
            self._data["boards"][board.id] = board.to_dict()

        self._data["columns"].pop(column_id, None)
        await self.async_save()

    async def async_reorder_columns(self, board_id: str, column_ids: list[str]) -> None:
        """Reorder columns in a board."""
        board = self.get_board(board_id)
        if not board:
            return

        board.column_ids = column_ids
        
        # Update position on each column
        for position, column_id in enumerate(column_ids):
            column = self.get_column(column_id)
            if column:
                column.position = position
                self._data["columns"][column_id] = column.to_dict()

        self._data["boards"][board_id] = board.to_dict()
        await self.async_save()

    # Card operations

    def get_cards(self, column_id: str) -> list[Card]:
        """Get all cards for a column."""
        column = self.get_column(column_id)
        if not column:
            return []
        return [
            Card.from_dict(self._data["cards"][cid])
            for cid in column.card_ids
            if cid in self._data["cards"]
        ]

    def get_card(self, card_id: str) -> Card | None:
        """Get a specific card."""
        data = self._data["cards"].get(card_id)
        return Card.from_dict(data) if data else None

    async def async_create_card(self, card: Card) -> Card:
        """Create a new card."""
        self._data["cards"][card.id] = card.to_dict()
        
        # Add to column's card list
        column = self.get_column(card.column_id)
        if column:
            column.card_ids.insert(card.position, card.id)
            # Reindex positions
            for idx, cid in enumerate(column.card_ids):
                if cid in self._data["cards"]:
                    self._data["cards"][cid]["position"] = idx
            self._data["columns"][column.id] = column.to_dict()
        
        await self.async_save()
        return card

    async def async_update_card(self, card: Card) -> Card:
        """Update an existing card."""
        from datetime import datetime
        card.updated_at = datetime.now()
        self._data["cards"][card.id] = card.to_dict()
        await self.async_save()
        return card

    async def async_move_card(
        self, card_id: str, target_column_id: str, position: int
    ) -> Card | None:
        """Move a card to a new column and/or position."""
        card = self.get_card(card_id)
        if not card:
            return None

        old_column = self.get_column(card.column_id)
        new_column = self.get_column(target_column_id)

        if not new_column:
            return None

        # Remove from old column
        if old_column and card_id in old_column.card_ids:
            old_column.card_ids.remove(card_id)
            self._data["columns"][old_column.id] = old_column.to_dict()

        # Add to new column at position
        position = min(position, len(new_column.card_ids))
        new_column.card_ids.insert(position, card_id)
        
        # Update card's column reference
        card.column_id = target_column_id
        card.position = position
        
        # Reindex all cards in the new column
        for idx, cid in enumerate(new_column.card_ids):
            if cid in self._data["cards"]:
                self._data["cards"][cid]["position"] = idx
                self._data["cards"][cid]["column_id"] = target_column_id

        self._data["columns"][new_column.id] = new_column.to_dict()
        
        from datetime import datetime
        card.updated_at = datetime.now()
        self._data["cards"][card.id] = card.to_dict()
        
        await self.async_save()
        return card

    async def async_delete_card(self, card_id: str) -> None:
        """Delete a card."""
        card = self.get_card(card_id)
        if not card:
            return

        # Remove from column's card list
        column = self.get_column(card.column_id)
        if column and card_id in column.card_ids:
            column.card_ids.remove(card_id)
            self._data["columns"][column.id] = column.to_dict()

        self._data["cards"].pop(card_id, None)
        await self.async_save()

    # Full board data (for frontend)

    def get_full_board(self, board_id: str) -> dict[str, Any] | None:
        """Get complete board data including all columns and cards."""
        board = self.get_board(board_id)
        if not board:
            return None

        columns_data = []
        for column_id in board.column_ids:
            column = self.get_column(column_id)
            if column:
                cards_data = [
                    self.get_card(cid).to_dict()
                    for cid in column.card_ids
                    if self.get_card(cid)
                ]
                columns_data.append({
                    **column.to_dict(),
                    "cards": cards_data,
                })

        return {
            **board.to_dict(),
            "columns": columns_data,
        }
