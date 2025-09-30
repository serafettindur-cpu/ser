"""Komut satirindan üretim takip uygulamasini kullanmak icin arayüz."""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3

from production_tracking import db, service


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Asansör üretim takip araci"
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=db.DEFAULT_DB_PATH,
        help="SQLite veritabani dosyasi (varsayilan: production.db)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Veritabani tablolarini olustur")
    init_parser.set_defaults(func=_handle_init)

    create_order = subparsers.add_parser("create-order", help="Yeni siparis olustur")
    create_order.add_argument("customer")
    create_order.add_argument("elevator_type")
    create_order.add_argument("quantity", type=int)
    create_order.add_argument("due_date", help="Teslim tarihi (YYYY-MM-DD)")
    create_order.add_argument(
        "--status",
        default="planlama",
        help="Baslangic siparis durumu",
        choices=sorted(service.ORDER_STATUSES),
    )
    create_order.set_defaults(func=_handle_create_order)

    add_step = subparsers.add_parser("add-step", help="Siparise operasyon adimi ekle")
    add_step.add_argument("order_id", type=int)
    add_step.add_argument("name")
    add_step.add_argument("sequence", type=int)
    add_step.add_argument("--planned-hours", type=float, default=None)
    add_step.set_defaults(func=_handle_add_step)

    update_step = subparsers.add_parser("update-step", help="Operasyon durumu guncelle")
    update_step.add_argument("order_id", type=int)
    update_step.add_argument("step_name")
    update_step.add_argument(
        "--status",
        required=True,
        choices=sorted(service.STEP_STATUSES),
    )
    update_step.add_argument("--actual-hours", type=float, default=None)
    update_step.add_argument("--notes", default=None)
    update_step.set_defaults(func=_handle_update_step)

    list_orders = subparsers.add_parser("list-orders", help="Siparisleri listele")
    list_orders.add_argument(
        "--status",
        choices=sorted(service.ORDER_STATUSES),
        help="Duruma gore filtrele",
    )
    list_orders.set_defaults(func=_handle_list_orders)

    summary = subparsers.add_parser("summary", help="Siparis ozetini yazdir")
    summary.add_argument("order_id", type=int)
    summary.set_defaults(func=_handle_summary)

    qc = subparsers.add_parser("quality-check", help="Kalite kaydi olustur")
    qc.add_argument("order_id", type=int)
    qc.add_argument("inspector")
    qc.add_argument("result")
    qc.add_argument("--notes", default=None)
    qc.set_defaults(func=_handle_quality_check)

    return parser.parse_args()


def _connect(path: Path) -> sqlite3.Connection:
    config = db.DatabaseConfig(path=path)
    connection = db.get_connection(config)
    return connection


def _handle_init(args: argparse.Namespace) -> None:
    connection = _connect(args.database)
    db.initialize_db(connection)
    print(f"Veritabani hazir: {args.database}")


def _handle_create_order(args: argparse.Namespace) -> None:
    connection = _connect(args.database)
    db.initialize_db(connection)
    order_id = service.create_order(
        connection,
        customer=args.customer,
        elevator_type=args.elevator_type,
        quantity=args.quantity,
        due_date=args.due_date,
        status=args.status,
    )
    print(f"Siparis olusturuldu: {order_id}")


def _handle_add_step(args: argparse.Namespace) -> None:
    connection = _connect(args.database)
    db.initialize_db(connection)
    step_id = service.add_step(
        connection,
        args.order_id,
        name=args.name,
        sequence=args.sequence,
        planned_hours=args.planned_hours,
    )
    print(f"Operasyon eklendi: {step_id}")


def _handle_update_step(args: argparse.Namespace) -> None:
    connection = _connect(args.database)
    db.initialize_db(connection)
    service.update_step(
        connection,
        order_id=args.order_id,
        step_name=args.step_name,
        status=args.status,
        actual_hours=args.actual_hours,
        notes=args.notes,
    )
    print("Operasyon guncellendi")


def _handle_list_orders(args: argparse.Namespace) -> None:
    connection = _connect(args.database)
    db.initialize_db(connection)
    orders = service.list_orders(connection, status=args.status)
    if not orders:
        print("Kayitli siparis yok")
        return

    for order in orders:
        print(
            f"#{order.id} | {order.customer} | {order.elevator_type} | "
            f"adet: {order.quantity} | teslim: {order.due_date} | durum: {order.status}"
        )


def _handle_summary(args: argparse.Namespace) -> None:
    connection = _connect(args.database)
    db.initialize_db(connection)
    summary = service.order_summary(connection, args.order_id)
    order = summary["order"]
    print(
        f"Siparis #{order.id} - {order.customer} ({order.elevator_type})\n"
        f"Adet: {order.quantity} | Termin: {order.due_date} | Durum: {order.status}"
    )
    print("Operasyonlar:")
    for step in summary["steps"]:
        print(
            f"  {step.sequence:02d}. {step.name} - durum: {step.status}"
            f" | planlanan: {step.planned_hours or '-'} saat"
            f" | gerceklesen: {step.actual_hours or '-'}"
        )
        if step.notes:
            print(f"     not: {step.notes}")

    if summary["quality_checks"]:
        print("Kalite Kayıtları:")
        for check in summary["quality_checks"]:
            print(
                f"  {check.timestamp} - {check.inspector}: {check.result}" +
                (f" ({check.notes})" if check.notes else "")
            )
    print(
        f"Toplam planlanan saat: {summary['planned_hours']} | "
        f"Toplam gerceklesen saat: {summary['actual_hours']}"
    )


def _handle_quality_check(args: argparse.Namespace) -> None:
    connection = _connect(args.database)
    db.initialize_db(connection)
    check_id = service.record_quality_check(
        connection,
        order_id=args.order_id,
        inspector=args.inspector,
        result=args.result,
        notes=args.notes,
    )
    print(f"Kalite kaydi olusturuldu: {check_id}")


def main() -> None:
    args = _parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
