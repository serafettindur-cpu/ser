"""Domain services for the elevator production tracking application."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable, Sequence

import sqlite3

from .db import iter_rows

ORDER_STATUSES = {
    "planlama",
    "uretimde",
    "montaj",
    "kalite_kontrol",
    "sevkiyat",
    "tamamlandi",
    "beklemede",
}

STEP_STATUSES = {
    "beklemede",
    "devam",
    "tamamlandi",
    "bekleyen_parca",
    "revizyon",
}


class OrderNotFoundError(RuntimeError):
    """Raised when an order cannot be found in the database."""


@dataclass
class Order:
    id: int
    customer: str
    elevator_type: str
    quantity: int
    due_date: str
    status: str


@dataclass
class Step:
    id: int
    order_id: int
    name: str
    sequence: int
    planned_hours: float | None
    actual_hours: float | None
    status: str
    notes: str | None


@dataclass
class QualityCheck:
    id: int
    order_id: int
    inspector: str
    result: str
    notes: str | None
    timestamp: str


def _ensure_order_exists(connection: sqlite3.Connection, order_id: int) -> None:
    cursor = connection.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
    if cursor.fetchone() is None:
        raise OrderNotFoundError(f"Siparis bulunamadi: {order_id}")


def create_order(
    connection: sqlite3.Connection,
    *,
    customer: str,
    elevator_type: str,
    quantity: int,
    due_date: str,
    status: str = "planlama",
) -> int:
    """Create a production order and return its identifier."""

    if status not in ORDER_STATUSES:
        raise ValueError(f"Gecersiz durum: {status}")

    cursor = connection.execute(
        """
        INSERT INTO orders(customer, elevator_type, quantity, due_date, status)
        VALUES(?, ?, ?, ?, ?)
        """,
        (customer, elevator_type, quantity, due_date, status),
    )
    connection.commit()
    return cursor.lastrowid


def update_order_status(
    connection: sqlite3.Connection, order_id: int, status: str
) -> None:
    if status not in ORDER_STATUSES:
        raise ValueError(f"Gecersiz durum: {status}")
    _ensure_order_exists(connection, order_id)
    connection.execute(
        "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
    )
    connection.commit()


def list_orders(
    connection: sqlite3.Connection, status: str | None = None
) -> Sequence[Order]:
    if status and status not in ORDER_STATUSES:
        raise ValueError(f"Gecersiz durum: {status}")

    if status:
        cursor = connection.execute(
            "SELECT * FROM orders WHERE status = ? ORDER BY due_date", (status,)
        )
    else:
        cursor = connection.execute("SELECT * FROM orders ORDER BY due_date")
    return [Order(**row) for row in iter_rows(cursor)]


def add_step(
    connection: sqlite3.Connection,
    order_id: int,
    *,
    name: str,
    sequence: int,
    planned_hours: float | None = None,
) -> int:
    _ensure_order_exists(connection, order_id)
    cursor = connection.execute(
        """
        INSERT INTO order_steps(order_id, name, sequence, planned_hours)
        VALUES(?, ?, ?, ?)
        """,
        (order_id, name, sequence, planned_hours),
    )
    connection.commit()
    return cursor.lastrowid


def list_steps(connection: sqlite3.Connection, order_id: int) -> Sequence[Step]:
    _ensure_order_exists(connection, order_id)
    cursor = connection.execute(
        "SELECT * FROM order_steps WHERE order_id = ? ORDER BY sequence", (order_id,)
    )
    return [Step(**row) for row in iter_rows(cursor)]


def update_step(
    connection: sqlite3.Connection,
    *,
    order_id: int,
    step_name: str,
    status: str,
    actual_hours: float | None = None,
    notes: str | None = None,
) -> None:
    if status not in STEP_STATUSES:
        raise ValueError(f"Gecersiz operasyon durumu: {status}")
    _ensure_order_exists(connection, order_id)
    cursor = connection.execute(
        "SELECT id FROM order_steps WHERE order_id = ? AND name = ?",
        (order_id, step_name),
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Adim bulunamadi: {step_name}")

    connection.execute(
        """
        UPDATE order_steps
           SET status = ?, actual_hours = COALESCE(?, actual_hours), notes = COALESCE(?, notes)
         WHERE order_id = ? AND name = ?
        """,
        (status, actual_hours, notes, order_id, step_name),
    )
    connection.commit()


def order_summary(connection: sqlite3.Connection, order_id: int) -> dict:
    """Return a structured summary of an order including its steps and quality checks."""

    _ensure_order_exists(connection, order_id)
    order_cursor = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = Order(**dict(order_cursor.fetchone()))

    steps = list_steps(connection, order_id)
    checks = list_quality_checks(connection, order_id)

    planned_hours = sum(step.planned_hours or 0 for step in steps)
    actual_hours = sum((step.actual_hours or 0) for step in steps)

    return {
        "order": order,
        "steps": steps,
        "quality_checks": checks,
        "planned_hours": planned_hours,
        "actual_hours": actual_hours,
    }


def record_quality_check(
    connection: sqlite3.Connection,
    *,
    order_id: int,
    inspector: str,
    result: str,
    notes: str | None = None,
    timestamp: str | None = None,
) -> int:
    _ensure_order_exists(connection, order_id)
    timestamp = timestamp or dt.datetime.now().isoformat(timespec="seconds")
    cursor = connection.execute(
        """
        INSERT INTO quality_checks(order_id, inspector, result, notes, timestamp)
        VALUES(?, ?, ?, ?, ?)
        """,
        (order_id, inspector, result, notes, timestamp),
    )
    connection.commit()
    return cursor.lastrowid


def list_quality_checks(
    connection: sqlite3.Connection, order_id: int
) -> Sequence[QualityCheck]:
    cursor = connection.execute(
        "SELECT * FROM quality_checks WHERE order_id = ? ORDER BY timestamp DESC",
        (order_id,),
    )
    return [QualityCheck(**row) for row in iter_rows(cursor)]
