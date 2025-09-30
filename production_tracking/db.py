"""Database helpers for the production tracking application."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable

DEFAULT_DB_PATH = Path("production.db")


@dataclass
class DatabaseConfig:
    """Configuration for connecting to the SQLite database."""

    path: Path = DEFAULT_DB_PATH
    timeout: float = 5.0


def get_connection(config: DatabaseConfig | None = None) -> sqlite3.Connection:
    """Return a SQLite connection based on the provided configuration."""

    config = config or DatabaseConfig()
    connection = sqlite3.connect(config.path, timeout=config.timeout)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db(connection: sqlite3.Connection) -> None:
    """Create the database tables if they do not already exist."""

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            elevator_type TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planlama'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            planned_hours REAL,
            actual_hours REAL,
            status TEXT NOT NULL DEFAULT 'beklemede',
            notes TEXT,
            UNIQUE(order_id, name),
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quality_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            inspector TEXT NOT NULL,
            result TEXT NOT NULL,
            notes TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
        """
    )

    connection.commit()


def iter_rows(cursor: sqlite3.Cursor) -> Iterable[dict]:
    """Yield rows from a cursor as dictionaries."""

    for row in cursor:
        yield dict(row)
