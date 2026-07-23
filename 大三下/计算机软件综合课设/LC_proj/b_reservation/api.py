from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, jsonify, request

from .service import (
    ConflictError,
    InvalidReservationError,
    InvalidStateError,
    PermissionDenied,
    ReservationError,
    ReservationStore,
)


class IntegrationUnavailable(RuntimeError):
    pass


def create_app(config: dict | None = None) -> Flask:
    """创建 B 模块独立运行时的 Flask 接口。

    A/C/D 模块的能力通过 Flask config 中的回调函数注入。
    身份、权限、信用和设备状态都在服务端判断，不信任前端 JSON 自报。
    """

    app = Flask(__name__)
    # B 模块独立运行时使用默认数据库；接入全组系统时由 unified_app 传入统一数据库路径。
    app.config.from_mapping(
        DATABASE_PATH=os.getenv("DATABASE_PATH", "reservations.db"),
        CANCEL_EXEMPTION_HOURS=2,
    )
    if config:
        app.config.update(config)

    store = ReservationStore(app.config["DATABASE_PATH"])
    store.init_schema()
    register_routes(app, store)
    return app


def register_routes(
    app: Flask,
    store: ReservationStore | None = None,
    *,
    register_health: bool = True,
) -> Flask:
    """把 B 预约模块的接口注册到全组统一 Flask 应用上。"""

    if store is None:
        store = ReservationStore(app.config["DATABASE_PATH"])
        store.init_schema()
    app.extensions["reservation_store"] = store

    def integration(name: str):
        # 统一入口必须注入这些服务端能力；缺少时返回 503，避免用假数据冒充已接入。
        callback = app.config.get(name)
        if not callable(callback):
            raise IntegrationUnavailable(f"尚未接入服务端能力：{name}")
        return callback

    def actor() -> dict:
        # 当前用户只能从 A 模块会话取得，不能从请求体传 user_id。
        current = integration("CURRENT_ACTOR")()
        if not current or not isinstance(current.get("user_id"), int):
            raise PermissionDenied("请先登录")
        return current

    def can_manage(current: dict, lab_id: int) -> bool:
        return bool(integration("CAN_MANAGE_LAB")(current["user_id"], lab_id))

    def audit(
        current: dict,
        action: str,
        target_object_type: str,
        target_object_id: int,
        detail: str = "",
    ) -> None:
        # AUDIT 是可选集成：A 模块接入后记录关键操作日志，未接入时不影响预约主流程。
        callback = app.config.get("AUDIT")
        if callable(callback):
            callback(
                user_id=current["user_id"],
                role_code=current.get("role"),
                action=action,
                target_object_type=target_object_type,
                target_object_id=target_object_id,
                target_object_name=f"预约 {target_object_id}",
                detail=detail,
                ip_address=request.remote_addr,
            )

    @app.errorhandler(ReservationError)
    def reservation_error(error):
        # 预约业务异常统一转换成前端能识别的 HTTP 状态码。
        if isinstance(error, PermissionDenied):
            status = 403
        elif isinstance(error, (ConflictError, InvalidStateError)):
            status = 409
        else:
            status = 400
        return jsonify(error=str(error)), status

    @app.errorhandler(IntegrationUnavailable)
    def integration_error(error):
        return jsonify(error=str(error)), 503

    if register_health:
        @app.get("/health")
        def health():
            return jsonify(service="reservation", status="ok")

    @app.post("/api/reservations")
    def create_reservation():
        current = actor()
        payload = _json_object()
        try:
            # Idempotency-Key 对应数据库 request_id，用于防止重复点击生成多条预约。
            request_id = request.headers["Idempotency-Key"]
            lab_id = payload["lab_id"]
            equipment_id = payload.get("equipment_id")
            start_time = payload["start_time"]
            end_time = payload["end_time"]
            purpose = payload["purpose"]
        except KeyError as exc:
            raise InvalidReservationError(f"缺少字段：{exc.args[0]}") from exc

        # 信用资格和设备可约状态分别由 D、C 模块判断，B 只使用服务端返回的结论。
        eligible = integration("STUDENT_IS_ELIGIBLE")(current["user_id"])
        bookable = integration("RESOURCE_IS_BOOKABLE")(
            lab_id, equipment_id, start_time, end_time
        )
        reservation = store.create(
            request_id=request_id,
            user_id=current["user_id"],
            lab_id=lab_id,
            equipment_id=equipment_id,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            student_is_eligible=bool(eligible),
            resource_is_bookable=bool(bookable),
        )
        audit(current, "reservation.create", "reservation", reservation["reservation_id"])
        return jsonify(reservation=reservation), 201

    @app.get("/api/reservations/me")
    def my_reservations():
        current = actor()
        return jsonify(reservations=store.list_for_user(current["user_id"]))

    @app.get("/api/reservations")
    def search_reservations(): #按照时间查reserve
        current = actor()
        try:
            start_time = request.args["start_time"]
            end_time = request.args["end_time"]
        except KeyError as exc:
            raise InvalidReservationError(f"缺少查询参数：{exc.args[0]}") from exc
        lab_id_text = request.args.get("lab_id", "").strip()
        if lab_id_text:
            try:
                lab_id = int(lab_id_text)
            except ValueError as exc:
                raise InvalidReservationError("lab_id 必须为正整数") from exc
            # 管理员按实验室查询预约；学生不传 lab_id 时只查自己的预约。
            if not can_manage(current, lab_id):
                raise PermissionDenied("无权查询该实验室预约")
            reservations = store.list_by_time_range(
                start_time, end_time, lab_id=lab_id
            )
        else:
            reservations = store.list_by_time_range(
                start_time, end_time, user_id=current["user_id"]
            )
        return jsonify(reservations=reservations)

    @app.get("/api/labs/<int:lab_id>/reservations/pending")
    def pending_reservations(lab_id: int):
        current = actor()
        # 管理员只能查看自己管辖实验室的待审批预约。
        if not can_manage(current, lab_id):
            raise PermissionDenied("无权查看该实验室待审批预约")
        return jsonify(reservations=store.list_pending_for_lab(lab_id))

    @app.post("/api/reservations/<int:reservation_id>/approve")
    def approve_reservation(reservation_id: int):
        current = actor()
        payload = _json_object()
        existing = store.get(reservation_id)
        # 审批前再次检查管辖范围和设备状态，防止提交后设备已维修/停用。
        manageable = can_manage(current, existing["lab_id"])
        bookable = integration("RESOURCE_IS_BOOKABLE")(
            existing["lab_id"],
            existing["equipment_id"],
            existing["start_time"],
            existing["end_time"],
        )
        reservation = store.approve(
            reservation_id,
            approver_id=current["user_id"],
            comment=payload.get("comment", ""),
            can_manage_lab=manageable,
            resource_is_bookable=bool(bookable),
        )
        audit(
            current,
            "reservation.approve",
            "reservation",
            reservation_id,
            payload.get("comment", ""),
        )
        return jsonify(reservation=reservation)

    @app.post("/api/reservations/<int:reservation_id>/reject")
    def reject_reservation(reservation_id: int):
        current = actor()
        payload = _json_object()
        existing = store.get(reservation_id)
        reservation = store.reject(
            reservation_id,
            approver_id=current["user_id"],
            comment=payload.get("comment", ""),
            can_manage_lab=can_manage(current, existing["lab_id"]),
        )
        audit(
            current,
            "reservation.reject",
            "reservation",
            reservation_id,
            payload.get("comment", ""),
        )
        return jsonify(reservation=reservation)

    @app.post("/api/reservations/<int:reservation_id>/cancel")
    def cancel_reservation(reservation_id: int):
        current = actor()
        payload = _json_object()
        existing = store.get(reservation_id)
        manager = can_manage(current, existing["lab_id"])
        # maintenance_cancel 表示设备维护导致取消，只允许实验室管理员触发。
        maintenance = bool(payload.get("maintenance_cancel", False))
        if maintenance and not manager:
            raise PermissionDenied("只有实验室管理员可以执行维护取消")
        reservation = store.cancel(
            reservation_id,
            actor_can_cancel=current["user_id"] == existing["user_id"] or manager,
            now=datetime.now(),
            exemption_hours=float(app.config["CANCEL_EXEMPTION_HOURS"]),
            maintenance_cancel=maintenance,
        )
        audit(
            current,
            "reservation.maintenance_cancel" if maintenance else "reservation.cancel",
            "reservation",
            reservation_id,
        )
        return jsonify(reservation=reservation)

    return app


def _json_object() -> dict:
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise InvalidReservationError("请求体必须是 JSON 对象")
    return payload
