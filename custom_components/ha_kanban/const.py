"""
Project: HA Kanban Integration
Module: Constants (const.py)
Author: Dave C. (ropeadope62)
https://github.com/ropeadope62
"""

DOMAIN = "ha_kanban"
NAME = "HA Kanban"
VERSION = "0.1.0"

# Storage
STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1

# Services
SERVICE_CREATE_BOARD = "create_board"
SERVICE_DELETE_BOARD = "delete_board"
SERVICE_ADD_COLUMN = "add_column"
SERVICE_REORDER_COLUMNS = "reorder_columns"
SERVICE_DELETE_COLUMN = "delete_column"
SERVICE_CREATE_CARD = "create_card"
SERVICE_UPDATE_CARD = "update_card"
SERVICE_MOVE_CARD = "move_card"
SERVICE_DELETE_CARD = "delete_card"

# WebSocket
WS_TYPE_SUBSCRIBE = f"{DOMAIN}/subscribe"
WS_TYPE_UNSUBSCRIBE = f"{DOMAIN}/unsubscribe"
WS_TYPE_BOARD_UPDATED = f"{DOMAIN}/board_updated"
WS_TYPE_CARD_MOVED = f"{DOMAIN}/card_moved"
WS_TYPE_CARD_UPDATED = f"{DOMAIN}/card_updated"
WS_TYPE_CARD_CREATED = f"{DOMAIN}/card_created"
WS_TYPE_CARD_DELETED = f"{DOMAIN}/card_deleted"

# Defaults
DEFAULT_COLUMNS = ["To Do", "In Progress", "Done"]

# Labels (predefined options)
PREDEFINED_LABELS = [
    "urgent",
    "weekly",
    "monthly",
    "shopping",
    "cleaning",
    "maintenance",
    "bills",
    "family",
]
