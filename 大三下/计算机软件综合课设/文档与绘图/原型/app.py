from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory


app = Flask(__name__, static_folder=None)
ROOT = Path(__file__).resolve().parent


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def initial_state() -> dict:
    return {
        "reservation": {
            "id": "R-20260713-001",
            "request_id": "demo-20260713-001",
            "student": "学生 LC",
            "device": "GPU-01 工作站",
            "lab": "信息楼 436 - 智能实验室",
            "date": "2026-07-13",
            "start": "09:00",
            "end": "10:00",
            "purpose": "软件课设联调与模型测试",
            "status": "none",
            "late_cancel": False,
            "credit_deduction_required": False,
        },
        "equipment": {
            "GPU-01 工作站": "normal",
            "GPU-02 工作站": "repairing",
            "普通机位 A12": "normal",
        },
        "repairs": [],
        "credit": {
            "score": 96,
            "banned": False,
            "logs": [
                {"time": "2026-07-10", "type": "临期取消", "score": -2, "detail": "距离开始不足 2 小时取消"},
                {"time": "2026-07-06", "type": "规范使用恢复", "score": 5, "detail": "连续 5 次按时签到签退"},
            ],
        },
        "parameters": {
            "cancel_exemption_hours": "2",
            "checkin_window_minutes": "15",
            "ban_threshold": "60",
            "version": 1,
        },
        "logs": [f"[{now()}] Flask 动态原型已启动：后端状态保存在当前进程内。"],
    }


STATE = initial_state()


def log(message: str) -> None:
    STATE["logs"].insert(0, f"[{now()}] {message}")
    STATE["logs"] = STATE["logs"][:80]


def payload() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def reservation_response(message: str, *, status: int = 200):
    return jsonify(ok=status < 400, message=message, state=STATE), status


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.get("/README.md")
def readme():
    return send_from_directory(ROOT, "README.md")


@app.get("/api/state")
def get_state():
    return jsonify(ok=True, state=STATE)


@app.post("/api/reset")
def reset():
    STATE.clear()
    STATE.update(initial_state())
    return reservation_response("已重置演示数据")


@app.post("/api/reservations")
def create_reservation():
    data = payload()
    reservation = STATE["reservation"]
    request_id = data.get("request_id") or reservation["request_id"]
    if request_id == reservation["request_id"] and reservation["status"] != "none":
        log("B.create 幂等命中：同一 Idempotency-Key 返回已有预约，不新增记录。")
        return reservation_response("重复提交已按幂等处理，返回已有预约")

    device = data.get("device") or reservation["device"]
    if STATE["equipment"].get(device) != "normal":
        log(f"B.create 拒绝：{device} 当前不可预约。")
        return reservation_response("目标设备维修中或停用，不能预约", status=409)

    reservation.update(
        request_id=request_id,
        device=device,
        start=data.get("start") or reservation["start"],
        end=data.get("end") or reservation["end"],
        purpose=data.get("purpose") or reservation["purpose"],
        status="pending",
        late_cancel=False,
        credit_deduction_required=False,
    )
    log("B.create 创建预约：状态 pending，已完成信用、资源、冲突和幂等校验。")
    return reservation_response("预约已提交，等待管理员审批", status=201)


@app.post("/api/reservations/approve")
def approve_reservation():
    if STATE["reservation"]["status"] != "pending":
        return reservation_response("只有待审批预约可以通过", status=409)
    if STATE["equipment"].get(STATE["reservation"]["device"]) != "normal":
        return reservation_response("设备当前不可用，不能通过审批", status=409)
    STATE["reservation"]["status"] = "approved"
    log("B.approve 审批通过：A 校验管辖范围，C 再次校验资源可约性，写入操作日志。")
    return reservation_response("审批通过，学生可以签到")


@app.post("/api/reservations/reject")
def reject_reservation():
    if STATE["reservation"]["status"] != "pending":
        return reservation_response("只有待审批预约可以驳回", status=409)
    STATE["reservation"]["status"] = "rejected"
    log("B.reject 驳回预约：记录审批意见并通知学生。")
    return reservation_response("预约已驳回")


@app.post("/api/reservations/cancel")
def cancel_reservation():
    data = payload()
    maintenance = bool(data.get("maintenance"))
    if STATE["reservation"]["status"] not in {"pending", "approved"}:
        return reservation_response("当前预约状态不可取消", status=409)
    STATE["reservation"]["status"] = "cancelled"
    STATE["reservation"]["late_cancel"] = not maintenance
    STATE["reservation"]["credit_deduction_required"] = not maintenance
    if maintenance:
        log("B.cancel_for_maintenance 维护取消：不扣学生信用分，并通知学生。")
        return reservation_response("设备维护导致预约取消，不扣学生信用分")
    log("B.cancel 学生取消：若临期，返回 credit_deduction_required=True，交由 D 扣分。")
    return reservation_response("学生取消预约，临期取消将进入信用处理")


@app.post("/api/check-in")
def check_in():
    if STATE["reservation"]["status"] != "approved":
        return reservation_response("只有 approved 状态才能签到", status=409)
    STATE["reservation"]["status"] = "using"
    log("C.check_in -> B.mark_using：二维码和定位校验通过，写 check_record 和 IoT 日志。")
    return reservation_response("签到成功，预约进入使用中")


@app.post("/api/check-out")
def check_out():
    if STATE["reservation"]["status"] != "using":
        return reservation_response("只有 using 状态才能签退", status=409)
    STATE["reservation"]["status"] = "completed"
    log("C.check_out -> B.mark_completed：签退成功，预约状态 completed。")
    return reservation_response("签退成功，预约已完成")


@app.post("/api/repairs")
def create_repair():
    data = payload()
    repair = {
        "id": f"REP-{len(STATE['repairs']) + 1:03d}",
        "reporter": "学生 LC",
        "device": data.get("device") or STATE["reservation"]["device"],
        "fault": data.get("fault") or "无法开机",
        "status": "pending",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    STATE["repairs"].insert(0, repair)
    STATE["equipment"][repair["device"]] = "fault_pending"
    log(f"C.repair 创建报修 {repair['id']}：设备状态变为 fault_pending，通知管理员。")
    return reservation_response("已提交报修，设备进入待确认故障状态", status=201)


@app.post("/api/equipment/maintenance")
def equipment_maintenance():
    device = STATE["reservation"]["device"]
    STATE["equipment"][device] = "repairing"
    if STATE["reservation"]["status"] in {"pending", "approved"}:
        STATE["reservation"]["status"] = "cancelled"
        STATE["reservation"]["late_cancel"] = False
        STATE["reservation"]["credit_deduction_required"] = False
        log("C.maintenance -> B.cancel_for_maintenance：设备维修，取消受影响预约，不扣分。")
        return reservation_response("设备设为维修中，受影响预约已维护取消")
    log("C.maintenance：设备设为维修中，当前无可取消预约。")
    return reservation_response("设备设为维修中")


@app.post("/api/equipment/restore")
def equipment_restore():
    data = payload()
    device = data.get("device") or STATE["reservation"]["device"]
    STATE["equipment"][device] = "normal"
    log(f"C.equipment_restore：{device} 恢复 normal，可重新预约。")
    return reservation_response("设备已恢复正常")


@app.post("/api/repairs/handle")
def handle_repair():
    data = payload()
    status = data.get("status") or "repairing"
    if not STATE["repairs"]:
        create_repair()
    repair = STATE["repairs"][0]
    repair["status"] = status
    if status == "repairing":
        STATE["equipment"][repair["device"]] = "repairing"
        message = "已开始维修，设备状态变为 repairing"
    elif status in {"completed", "no_fault"}:
        STATE["equipment"][repair["device"]] = "normal"
        message = "报修已关闭，设备恢复 normal"
    else:
        message = f"报修状态已更新为 {status}"
    log(f"C.repair_handle：{repair['id']} -> {status}，{message}。")
    return reservation_response(message)


@app.post("/api/violations/confirm")
def confirm_violation():
    STATE["credit"]["score"] = max(0, STATE["credit"]["score"] - 5)
    STATE["credit"]["logs"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d"),
        "type": "迟到签到",
        "score": -5,
        "detail": "管理员确认违规，生成 credit_log",
    })
    log("D.violation 确认违规：生成 violation_record 和 credit_log，并通知学生。")
    return reservation_response("已确认违规并扣 5 分")


@app.post("/api/parameters")
def update_parameters():
    data = payload()
    for key in ("cancel_exemption_hours", "checkin_window_minutes", "ban_threshold"):
        if key in data:
            STATE["parameters"][key] = str(data[key])
    STATE["parameters"]["version"] += 1
    log(f"A.parameter 更新系统参数：版本变为 {STATE['parameters']['version']}，写入参数历史和操作日志。")
    return reservation_response("系统参数已发布")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
