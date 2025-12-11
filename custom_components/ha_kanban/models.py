"""
Project: HA Kanban Integration
Module: Data Models (models.py)
Author: Dave C. (ropeadope62)
https://github.com/ropeadope62
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any
import uuid


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


@dataclass
class Card:
    """Represents a Kanban card (task)."""

    id: str
    column_id: str
    title: str
    position: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    assignee: str | None = None
    due_date: date | None = None
    labels: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        column_id: str,
        title: str,
        position: int,
        created_by: str,
        description: str | None = None,
        assignee: str | None = None,
        due_date: date | None = None,
        labels: list[str] | None = None,
    ) -> Card:
        """Create a new card with generated ID and timestamps."""
        now = datetime.now()
        return cls(
            id=generate_id(),
            column_id=column_id,
            title=title,
            position=position,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
            assignee=assignee,
            due_date=due_date,
            labels=labels or [],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "column_id": self.column_id,
            "title": self.title,
            "position": self.position,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "description": self.description,
            "assignee": self.assignee,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "labels": self.labels,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Card:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            column_id=data["column_id"],
            title=data["title"],
            position=data["position"],
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            description=data.get("description"),
            assignee=data.get("assignee"),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            labels=data.get("labels", []),
        )


@dataclass
class Column:
    """Represents a Kanban column."""

    id: str
    board_id: str
    name: str
    position: int
    color: str | None = None
    card_ids: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        board_id: str,
        name: str,
        position: int,
        color: str | None = None,
    ) -> Column:
        """Create a new column with generated ID."""
        return cls(
            id=generate_id(),
            board_id=board_id,
            name=name,
            position=position,
            color=color,
            card_ids=[],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "board_id": self.board_id,
            "name": self.name,
            "position": self.position,
            "color": self.color,
            "card_ids": self.card_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Column:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            board_id=data["board_id"],
            name=data["name"],
            position=data["position"],
            color=data.get("color"),
            card_ids=data.get("card_ids", []),
        )


@dataclass
class Board:
    """Represents a Kanban board."""

    id: str
    name: str
    created_by: str
    created_at: datetime
    column_ids: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, created_by: str) -> Board:
        """Create a new board with generated ID and timestamp."""
        return cls(
            id=generate_id(),
            name=name,
            created_by=created_by,
            created_at=datetime.now(),
            column_ids=[],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "column_ids": self.column_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Board:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]),
            column_ids=data.get("column_ids", []),
        )
