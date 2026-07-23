from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, jsonify, session

from a_platform import PlatformStore, register_routes as register_platform_routes
from b_reservation import ReservationStore, create_app as create_reservation_app

try:
    from b_reservation.api import register_routes as register_reservation_routes
except ImportError:  # Local B snapshot still exposes only create_app().
    register_reservation_routes = None

try:
    from c_field_equipment import FieldEquipmentStore
    from c_field_equipment.api import register_routes as register_field_equipment_routes
except ImportError:  # C may not exist in older local snapshots.
    FieldEquipmentStore = None
    register_field_equipment_routes = None


def create_app(config: dict | None = None):
    """Create the unified Flask application for the course demo."""

    database_path = os.getenv("DATABASE_PATH", "lab_system.db")
    secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")
    checkin_token_secret = os.getenv("CHECKIN_TOKEN_SECRET", "dev-c-token-secret")
    if config:
        database_path = config.get("DATABASE_PATH", database_path)
        secret_key = config.get("SECRET_KEY", secret_key)
        checkin_token_secret = config.get("CHECKIN_TOKEN_SECRET", checkin_token_secret)

    platform_store = PlatformStore(database_path)
    reservation_store = ReservationStore(database_path)
    field_store = (
        FieldEquipmentStore(database_path, token_secret=checkin_token_secret)
        if FieldEquipmentStore
        else None
    )

    platform_store.init_schema()
    platform_store.seed_demo_data()

    def current_actor() -> dict | None:
        return platform_store.actor_from_session(session)

    def can_manage_lab(user_id: int, lab_id: int) -> bool:
        current = current_actor()
        if not current or current["user_id"] != user_id:
            return False
        return platform_store.can_manage_lab(user_id, lab_id, current["role"])

    def student_is_eligible(user_id: int) -> bool:
        current = current_actor()
        if not current or current["user_id"] != user_id:
            return False
        try:
            return platform_store.get_user(user_id)["status"] == "active"
        except Exception:
            return False

    def resource_is_bookable(
        lab_id: int,
        equipment_id: int | None,
        start_time: str,
        end_time: str,
    ) -> bool:
        if field_store is not None:
            return bool(
                field_store.resource_is_bookable(
                    lab_id, equipment_id, start_time, end_time
                )
            )
        return lab_id > 0 and (equipment_id is None or equipment_id > 0) and start_time < end_time

    app_config = {
        "DATABASE_PATH": database_path,
        "SECRET_KEY": secret_key,
        "CHECKIN_TOKEN_SECRET": checkin_token_secret,
        "CURRENT_ACTOR": current_actor,
        "CAN_MANAGE_LAB": can_manage_lab,
        "GET_PARAMETER": platform_store.get_parameter,
        "AUDIT": platform_store.audit,
        "STUDENT_IS_ELIGIBLE": student_is_eligible,
        "RESOURCE_IS_BOOKABLE": resource_is_bookable,
        "CANCEL_EXEMPTION_HOURS": float(
            platform_store.get_parameter("cancel_exemption_hours", "2") or "2"
        ),
    }
    if config:
        app_config.update(config)
        app_config.update(
            {
                "CURRENT_ACTOR": current_actor,
                "CAN_MANAGE_LAB": can_manage_lab,
                "GET_PARAMETER": platform_store.get_parameter,
                "AUDIT": platform_store.audit,
                "STUDENT_IS_ELIGIBLE": student_is_eligible,
                "RESOURCE_IS_BOOKABLE": resource_is_bookable,
            }
        )

    if register_reservation_routes is None:
        app = create_reservation_app(app_config)
    else:
        app = Flask(__name__)
        app.config.update(app_config)
        reservation_store.init_schema()
        register_reservation_routes(app, reservation_store, register_health=False)
        app.extensions["reservation_store"] = reservation_store

    register_platform_routes(app, platform_store)
    app.extensions["platform_store"] = platform_store

    modules = ["platform", "reservation"]
    if field_store is not None and register_field_equipment_routes is not None:
        field_store.init_schema()
        field_store.seed_demo_data()
        now_provider = app.config.get("NOW_PROVIDER", datetime.now)
        if hasattr(reservation_store, "get"):
            app.config["GET_RESERVATION"] = reservation_store.get
        if hasattr(reservation_store, "mark_using"):
            app.config["MARK_RESERVATION_USING"] = reservation_store.mark_using
        if hasattr(reservation_store, "mark_completed"):
            app.config["MARK_RESERVATION_COMPLETED"] = reservation_store.mark_completed
        if hasattr(reservation_store, "list_affected_by_equipment"):
            app.config["LIST_AFFECTED_RESERVATIONS"] = (
                lambda equipment_id, now: reservation_store.list_affected_by_equipment(
                    equipment_id, now=now
                )
            )
        if hasattr(reservation_store, "cancel_for_maintenance"):
            app.config["CANCEL_RESERVATION_FOR_MAINTENANCE"] = (
                lambda reservation_id: reservation_store.cancel_for_maintenance(
                    reservation_id, now=now_provider()
                )
            )
        if hasattr(reservation_store, "student_has_equipment_relation"):
            app.config["STUDENT_HAS_EQUIPMENT_RELATION"] = (
                lambda user_id, equipment_id, now, recent_days: reservation_store.student_has_equipment_relation(
                    user_id,
                    equipment_id,
                    now=now,
                    recent_days=recent_days,
                )
            )
        register_field_equipment_routes(app, field_store)
        app.extensions["field_equipment_store"] = field_store
        modules.append("field-equipment")

    def integrated_health():
        return jsonify(service="lab-system", status="ok", modules=modules)

    if "health" in app.view_functions:
        app.view_functions["health"] = integrated_health
    else:
        app.add_url_rule("/health", "health", integrated_health, methods=["GET"])

    return app
