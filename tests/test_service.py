import sqlite3

import pytest

from production_tracking import db, service


def create_memory_db():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    db.initialize_db(connection)
    return connection


def test_create_order_and_steps():
    connection = create_memory_db()
    order_id = service.create_order(
        connection,
        customer="Mega Asansor",
        elevator_type="Panoramik",
        quantity=4,
        due_date="2024-07-15",
    )
    assert order_id == 1

    service.add_step(
        connection,
        order_id,
        name="Kesim",
        sequence=1,
        planned_hours=5.5,
    )
    service.add_step(
        connection,
        order_id,
        name="Kaynak",
        sequence=2,
        planned_hours=8,
    )

    service.update_step(
        connection,
        order_id=order_id,
        step_name="Kesim",
        status="tamamlandi",
        actual_hours=5.0,
        notes="Programdan once tamamlandi",
    )

    summary = service.order_summary(connection, order_id)
    assert summary["planned_hours"] == pytest.approx(13.5)
    assert summary["actual_hours"] == pytest.approx(5.0)
    assert summary["steps"][0].notes == "Programdan once tamamlandi"


def test_list_orders_filters_by_status():
    connection = create_memory_db()
    order1 = service.create_order(
        connection,
        customer="Mega Asansor",
        elevator_type="Yuk Asansoru",
        quantity=2,
        due_date="2024-05-01",
    )
    order2 = service.create_order(
        connection,
        customer="Hizli Cözüm",
        elevator_type="Konutsal",
        quantity=1,
        due_date="2024-05-15",
        status="uretimde",
    )

    service.update_order_status(connection, order1, "montaj")

    montaj_orders = service.list_orders(connection, status="montaj")
    assert [o.id for o in montaj_orders] == [order1]

    all_orders = service.list_orders(connection)
    assert [o.id for o in all_orders] == [order1, order2]


def test_quality_checks_are_recorded_with_timestamp():
    connection = create_memory_db()
    order_id = service.create_order(
        connection,
        customer="Mega Asansor",
        elevator_type="Seyir",
        quantity=3,
        due_date="2024-06-10",
    )

    check_id = service.record_quality_check(
        connection,
        order_id=order_id,
        inspector="Ahmet",
        result="Basarili",
        notes="Tolerans icinde",
        timestamp="2024-03-01T10:00:00",
    )
    assert check_id == 1

    checks = service.list_quality_checks(connection, order_id)
    assert len(checks) == 1
    assert checks[0].inspector == "Ahmet"
    assert checks[0].timestamp == "2024-03-01T10:00:00"
