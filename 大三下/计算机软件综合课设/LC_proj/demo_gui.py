from __future__ import annotations

import argparse
import json
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from uuid import uuid4

from b_reservation import ConflictError, ReservationStore, create_app


STATUS_TEXT = {
    "pending": "待审批",
    "approved": "已通过",
    "rejected": "已驳回",
    "cancelled": "已取消",
    "using": "使用中",
    "completed": "已完成",
}


def default_slot() -> tuple[str, str]:
    day = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return day.isoformat(timespec="seconds"), (day + timedelta(hours=1)).isoformat(timespec="seconds")


class ReservationDemo:
    """只用于课堂演示的 B 模块桌面窗口。"""

    def __init__(self, root: Tk, database_path: Path):
        self.root = root
        self.database_path = database_path
        self.integration = {
            "actor": {"user_id": 1, "role": "student"},
            "eligible": True,
            "bookable": True,
            "manageable": True,
        }
        # Flask 测试客户端让桌面窗口真正经过 api.py，再进入 service.py。
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": database_path,
                "CURRENT_ACTOR": lambda: self.integration["actor"],
                "STUDENT_IS_ELIGIBLE": lambda _user_id: self.integration["eligible"],
                "RESOURCE_IS_BOOKABLE": lambda *_args: self.integration["bookable"],
                "CAN_MANAGE_LAB": lambda *_args: self.integration["manageable"],
            }
        )
        self.client = self.app.test_client()
        self.store: ReservationStore = self.app.extensions["reservation_store"]
        self._build_window()

    def _build_window(self) -> None:
        self.root.title("B 同学：资源与预约模块 Mini Demo")
        self.root.geometry("1100x760")
        self.root.minsize(900, 650)

        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text=f"演示数据库：{self.database_path}").pack(side="left")
        ttk.Button(top, text="载入示例数据", command=lambda: self.run("载入示例数据", self.seed)).pack(side="right", padx=3)
        ttk.Button(top, text="清空演示数据", command=self.confirm_reset).pack(side="right", padx=3)
        ttk.Button(top, text="查看全部记录", command=lambda: self.run("全部预约记录", self.list_all)).pack(side="right", padx=3)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=8)
        self._student_tab()
        self._admin_tab()
        self._integration_tab()
        self._rules_tab()

        result = ttk.LabelFrame(self.root, text="执行结果（同时标出对应 API / service 函数）", padding=6)
        result.pack(fill="both", expand=True, padx=8, pady=8)
        self.output = ScrolledText(result, height=13, wrap="word", font=("Consolas", 10))
        self.output.pack(fill="both", expand=True)
        self.show("准备完成", {"提示": "先点“载入示例数据”，也可直接填写表单。", "数据库": str(self.database_path)})

    @staticmethod
    def field(parent, label: str, variable: StringVar, row: int, column: int = 0, width: int = 28) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="e", padx=5, pady=5)
        ttk.Entry(parent, textvariable=variable, width=width).grid(row=row, column=column + 1, sticky="ew", padx=5, pady=5)

    def _student_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="学生预约")
        ttk.Label(tab, text="POST /api/reservations → ReservationStore.create()；GET /api/reservations/me → list_for_user()")\
            .grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        start, end = default_slot()
        self.request_id = StringVar(value=f"demo-{uuid4().hex[:8]}")
        self.user_id = StringVar(value="1")
        self.lab_id = StringVar(value="1")
        self.equipment_id = StringVar(value="101")
        self.start_time = StringVar(value=start)
        self.end_time = StringVar(value=end)
        self.purpose = StringVar(value="软件综合课设实验")
        self.eligible = BooleanVar(value=True)
        self.bookable = BooleanVar(value=True)

        self.field(tab, "幂等键 request_id", self.request_id, 1)
        self.field(tab, "学生 user_id", self.user_id, 2)
        self.field(tab, "实验室 lab_id", self.lab_id, 3)
        self.field(tab, "设备 equipment_id（可空）", self.equipment_id, 4)
        self.field(tab, "开始时间", self.start_time, 1, 2, 30)
        self.field(tab, "结束时间", self.end_time, 2, 2, 30)
        self.field(tab, "预约事由", self.purpose, 3, 2, 30)
        ttk.Checkbutton(tab, text="信用/封禁资格通过（模拟 D）", variable=self.eligible).grid(row=4, column=2, sticky="w", padx=5)
        ttk.Checkbutton(tab, text="资源可预约（模拟 C）", variable=self.bookable).grid(row=4, column=3, sticky="w", padx=5)

        buttons = ttk.Frame(tab)
        buttons.grid(row=5, column=0, columnspan=4, sticky="w", pady=12)
        ttk.Button(buttons, text="提交预约", command=lambda: self.run("POST /api/reservations → create()", self.create_reservation)).pack(side="left", padx=4)
        ttk.Button(buttons, text="查询我的预约", command=lambda: self.run("GET /api/reservations/me → list_for_user()", self.my_reservations)).pack(side="left", padx=4)
        for column in range(4):
            tab.columnconfigure(column, weight=1)

    def _admin_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="审批与取消")
        ttk.Label(tab, text="待审批、通过、驳回和取消均经过 api.py 的权限入口，再调用 service.py 状态规则。")\
            .grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        self.operation_reservation_id = StringVar(value="1")
        self.admin_id = StringVar(value="9")
        self.comment = StringVar(value="同意")
        self.query_lab_id = StringVar(value="1")
        self.exemption_hours = StringVar(value="2")
        query_start, query_end = default_slot()
        self.query_start_time = StringVar(value=query_start)
        self.query_end_time = StringVar(value=query_end)
        self.can_manage = BooleanVar(value=True)
        self.approve_bookable = BooleanVar(value=True)

        self.field(tab, "预约编号", self.operation_reservation_id, 1)
        self.field(tab, "管理员 user_id", self.admin_id, 2)
        self.field(tab, "审批意见", self.comment, 3)
        self.field(tab, "查询实验室", self.query_lab_id, 1, 2)
        self.field(tab, "临期免责小时", self.exemption_hours, 2, 2)
        self.field(tab, "查询开始时间", self.query_start_time, 4, 0, 30)
        self.field(tab, "查询结束时间", self.query_end_time, 4, 2, 30)
        ttk.Checkbutton(tab, text="具有实验室管辖权（模拟 A）", variable=self.can_manage).grid(row=3, column=2, sticky="w", padx=5)
        ttk.Checkbutton(tab, text="审批时资源仍可用（模拟 C）", variable=self.approve_bookable).grid(row=3, column=3, sticky="w", padx=5)

        buttons = ttk.Frame(tab)
        buttons.grid(row=5, column=0, columnspan=4, sticky="w", pady=12)
        actions = (
            ("查询待审批", "GET pending → list_pending_for_lab()", self.pending_reservations),
            ("按时间查询", "GET /api/reservations → list_by_time_range()", self.search_by_time),
            ("审批通过", "POST approve → approve()", self.approve),
            ("审批驳回", "POST reject → reject()", self.reject),
            ("学生取消", "POST cancel → cancel()", self.student_cancel),
            ("维护取消", "POST cancel(maintenance) → cancel()", self.maintenance_cancel_api),
        )
        for text, title, action in actions:
            ttk.Button(buttons, text=text, command=lambda t=title, a=action: self.run(t, a)).pack(side="left", padx=4)
        for column in range(4):
            tab.columnconfigure(column, weight=1)

    def _integration_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="C 模块联动")
        ttk.Label(tab, text="这些是 B 提供给现场签到、设备维修和报修校验模块的公开方法。")\
            .grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        self.link_reservation_id = StringVar(value="1")
        self.link_equipment_id = StringVar(value="101")
        self.link_user_id = StringVar(value="1")
        self.recent_days = StringVar(value="7")
        self.reference_time = StringVar(value=datetime.now().isoformat(timespec="seconds"))
        self.field(tab, "预约编号", self.link_reservation_id, 1)
        self.field(tab, "设备编号", self.link_equipment_id, 2)
        self.field(tab, "学生编号", self.link_user_id, 3)
        self.field(tab, "近期天数", self.recent_days, 1, 2)
        self.field(tab, "参考时间", self.reference_time, 2, 2, 30)

        buttons = ttk.Frame(tab)
        buttons.grid(row=4, column=0, columnspan=4, sticky="w", pady=12)
        actions = (
            ("签到→使用中", "ReservationStore.mark_using()", self.mark_using),
            ("签退→已完成", "ReservationStore.mark_completed()", self.mark_completed),
            ("查询维修影响", "ReservationStore.list_affected_by_equipment()", self.affected),
            ("维护直接取消", "ReservationStore.cancel_for_maintenance()", lambda: self.store.cancel_for_maintenance(self.link_reservation())),
            ("检查近期设备关联", "ReservationStore.student_has_equipment_relation()", self.equipment_relation),
        )
        for text, title, action in actions:
            ttk.Button(buttons, text=text, command=lambda t=title, a=action: self.run(t, a)).pack(side="left", padx=4)
        for column in range(4):
            tab.columnconfigure(column, weight=1)

    def _rules_tab(self) -> None:
        tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(tab, text="规则专项演示")
        ttk.Label(tab, text="三个按钮自动构造独立数据，可直接证明幂等、冲突检测和 SQLite 并发抢约控制。")\
            .pack(anchor="w", pady=(0, 12))
        for text, title, action in (
            ("重复提交幂等", "相同 request_id 两次提交 → create()", self.demo_idempotency),
            ("时间冲突检测", "重叠时段 → _find_conflict()", self.demo_conflict),
            ("20 路并发抢约", "BEGIN IMMEDIATE：20 路仅 1 条成功", self.demo_concurrency),
        ):
            ttk.Button(tab, text=text, command=lambda t=title, a=action: self.run(t, a), width=24).pack(anchor="w", pady=6)

    def api_result(self, response) -> dict:
        body = response.get_json(silent=True) or {}
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}：{body.get('error', body)}")
        return {"HTTP状态": response.status_code, **body}

    def create_reservation(self) -> dict:
        self.integration.update(
            actor={"user_id": int(self.user_id.get()), "role": "student"},
            eligible=self.eligible.get(),
            bookable=self.bookable.get(),
        )
        response = self.client.post(
            "/api/reservations",
            headers={"Idempotency-Key": self.request_id.get()},
            json={
                "lab_id": int(self.lab_id.get()),
                "equipment_id": self.optional_int(self.equipment_id.get()),
                "start_time": self.start_time.get(),
                "end_time": self.end_time.get(),
                "purpose": self.purpose.get(),
            },
        )
        return self.api_result(response)

    def my_reservations(self) -> dict:
        self.integration["actor"] = {"user_id": int(self.user_id.get()), "role": "student"}
        return self.api_result(self.client.get("/api/reservations/me"))

    def pending_reservations(self) -> dict:
        self.as_admin()
        return self.api_result(self.client.get(f"/api/labs/{int(self.query_lab_id.get())}/reservations/pending"))

    def search_by_time(self) -> dict:
        self.as_admin()
        response = self.client.get(
            "/api/reservations",
            query_string={
                "lab_id": int(self.query_lab_id.get()),
                "start_time": self.query_start_time.get(),
                "end_time": self.query_end_time.get(),
            },
        )
        return self.api_result(response)

    def approve(self) -> dict:
        self.as_admin()
        self.integration["bookable"] = self.approve_bookable.get()
        return self.api_result(self.client.post(f"/api/reservations/{self.operation_id()}/approve", json={"comment": self.comment.get()}))

    def reject(self) -> dict:
        self.as_admin()
        return self.api_result(self.client.post(f"/api/reservations/{self.operation_id()}/reject", json={"comment": self.comment.get()}))

    def student_cancel(self) -> dict:
        reservation = self.store.get(self.operation_id())
        self.integration["actor"] = {"user_id": reservation["user_id"], "role": "student"}
        self.integration["manageable"] = False
        self.app.config["CANCEL_EXEMPTION_HOURS"] = float(self.exemption_hours.get())
        return self.api_result(self.client.post(f"/api/reservations/{self.operation_id()}/cancel", json={}))

    def maintenance_cancel_api(self) -> dict:
        self.as_admin()
        return self.api_result(self.client.post(f"/api/reservations/{self.operation_id()}/cancel", json={"maintenance_cancel": True}))

    def as_admin(self) -> None:
        self.integration["actor"] = {"user_id": int(self.admin_id.get()), "role": "lab_admin"}
        self.integration["manageable"] = self.can_manage.get()

    def affected(self) -> list[dict]:
        return self.store.list_affected_by_equipment(
            int(self.link_equipment_id.get()), now=self.reference_time.get()
        )

    def mark_using(self) -> dict:
        reservation = self.store.mark_using(self.link_reservation())
        # 演示器允许操作未来预约；这里把参考时间同步到预约开始后，便于后续关联检查命中。
        self.reference_time.set(reservation["start_time"])
        return {
            **reservation,
            "演示说明": "参考时间已同步到预约开始时间，近期设备关联可直接继续演示",
        }

    def mark_completed(self) -> dict:
        reservation = self.store.mark_completed(self.link_reservation())
        # 已完成后按预约结束时间作为参考点，符合“近期使用/预约关系”的查询口径。
        self.reference_time.set(reservation["end_time"])
        return {
            **reservation,
            "演示说明": "参考时间已同步到预约结束时间，近期设备关联可直接继续演示",
        }

    def equipment_relation(self) -> dict:
        related = self.store.student_has_equipment_relation(
            int(self.link_user_id.get()),
            int(self.link_equipment_id.get()),
            now=self.reference_time.get(),
            recent_days=int(self.recent_days.get()),
        )
        return {"存在近期预约/使用关系": related}

    def demo_idempotency(self) -> dict:
        values = self.unique_values("idem")
        first = self.store.create(**values)
        second = self.store.create(**values)
        return {
            "第一次预约编号": first["reservation_id"],
            "第二次预约编号": second["reservation_id"],
            "结论": "编号相同，未重复写入",
        }

    def demo_conflict(self) -> dict:
        first_values = self.unique_values("conflict-a")
        first = self.store.create(**first_values)
        second_values = {**first_values, "request_id": f"conflict-b-{uuid4().hex[:8]}"}
        try:
            self.store.create(**second_values)
        except ConflictError as error:
            return {"已有预约": first["reservation_id"], "冲突提示": str(error), "结论": "重叠预约被拒绝"}
        raise AssertionError("冲突测试未按预期拒绝第二条预约")

    def demo_concurrency(self) -> dict:
        base = self.unique_values("concurrent")
        count = 20
        barrier = threading.Barrier(count)
        results: list[str] = []
        lock = threading.Lock()

        def submit(number: int) -> None:
            barrier.wait()
            try:
                self.store.create(**{**base, "request_id": f"concurrent-{uuid4().hex[:8]}-{number}"})
                outcome = "成功"
            except ConflictError:
                outcome = "冲突"
            with lock:
                results.append(outcome)

        threads = [threading.Thread(target=submit, args=(number,)) for number in range(count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return {"并发请求": count, "成功": results.count("成功"), "冲突": results.count("冲突"), "结论": "仅一条有效预约写入"}

    def unique_values(self, prefix: str) -> dict:
        token = uuid4().int % 800000 + 100000
        start = datetime.now().replace(microsecond=0) + timedelta(days=30, seconds=token % 20000)
        return {
            "request_id": f"{prefix}-{uuid4().hex[:8]}",
            "user_id": 1,
            "lab_id": 900000 + token,
            "equipment_id": 900000 + token,
            "start_time": start,
            "end_time": start + timedelta(hours=1),
            "purpose": f"{prefix} 规则演示",
            "student_is_eligible": True,
            "resource_is_bookable": True,
        }

    def seed(self) -> list[dict]:
        start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=2)
        rows = []
        for number, equipment in enumerate((101, 102, 103), start=1):
            row = self.store.create(
                request_id=f"seed-{number}", user_id=number, lab_id=1,
                equipment_id=equipment, start_time=start + timedelta(days=number),
                end_time=start + timedelta(days=number, hours=1), purpose=f"示例预约 {number}",
                student_is_eligible=True, resource_is_bookable=True,
            )
            rows.append(row)
        if rows[2]["status"] == "pending":
            rows[2] = self.store.approve(rows[2]["reservation_id"], approver_id=9, comment="示例已通过", can_manage_lab=True, resource_is_bookable=True)
        return rows

    def list_all(self) -> list[dict]:
        with self.store._connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM reservation ORDER BY reservation_id DESC").fetchall()]

    def confirm_reset(self) -> None:
        if messagebox.askyesno("确认", "只会清空 demo_reservations.db，是否继续？"):
            self.run("清空演示数据", self.reset)

    def reset(self) -> dict:
        with self.store._connection(immediate=True) as conn:
            conn.execute("DELETE FROM reservation")
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'reservation'")
        return {"结果": "演示预约已清空"}

    def run(self, title: str, action) -> None:
        try:
            result = action()
        except Exception as error:
            self.show(title, {"错误类型": type(error).__name__, "错误": str(error)})
            messagebox.showerror("操作未完成", str(error))
        else:
            self.show(title, result)

    def show(self, title: str, value) -> None:
        def translated(item):
            if isinstance(item, dict):
                return {key: STATUS_TEXT.get(val, val) if key == "status" else translated(val) for key, val in item.items()}
            if isinstance(item, list):
                return [translated(value) for value in item]
            return item

        self.output.delete("1.0", "end")
        self.output.insert("end", f"【{title}】\n")
        self.output.insert("end", json.dumps(translated(value), ensure_ascii=False, indent=2, default=str))

    def operation_id(self) -> int:
        return int(self.operation_reservation_id.get())

    def link_reservation(self) -> int:
        return int(self.link_reservation_id.get())

    @staticmethod
    def optional_int(value: str) -> int | None:
        value = value.strip()
        return int(value) if value else None


def self_test() -> None:
    """不打开窗口，检查 GUI 依赖的 API 和状态流。"""
    with tempfile.TemporaryDirectory() as directory:
        actor = {"value": {"user_id": 1, "role": "student"}}
        app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": Path(directory) / "demo-test.db",
                "CURRENT_ACTOR": lambda: actor["value"],
                "STUDENT_IS_ELIGIBLE": lambda _user_id: True,
                "RESOURCE_IS_BOOKABLE": lambda *_args: True,
                "CAN_MANAGE_LAB": lambda user_id, lab_id: user_id == 9 and lab_id == 1,
            }
        )
        client = app.test_client()
        payload = {
            "lab_id": 1,
            "equipment_id": 101,
            "start_time": "2030-01-01T09:00:00",
            "end_time": "2030-01-01T10:00:00",
            "purpose": "GUI 自检",
        }
        created = client.post("/api/reservations", headers={"Idempotency-Key": "gui-check"}, json=payload)
        assert created.status_code == 201
        reservation_id = created.get_json()["reservation"]["reservation_id"]
        actor["value"] = {"user_id": 9, "role": "lab_admin"}
        searched = client.get(
            "/api/reservations",
            query_string={
                "lab_id": 1,
                "start_time": "2030-01-01T08:30:00",
                "end_time": "2030-01-01T09:30:00",
            },
        )
        assert searched.status_code == 200
        assert len(searched.get_json()["reservations"]) == 1
        approved = client.post(f"/api/reservations/{reservation_id}/approve", json={"comment": "通过"})
        assert approved.status_code == 200
        store: ReservationStore = app.extensions["reservation_store"]
        assert store.mark_using(reservation_id)["status"] == "using"
        assert store.mark_completed(reservation_id)["status"] == "completed"
    print("B 模块 Mini Demo 自检通过")


def main() -> None:
    parser = argparse.ArgumentParser(description="B 资源与预约模块 Mini Demo")
    parser.add_argument("--database", type=Path, default=Path(__file__).with_name("demo_reservations.db"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    root = Tk()
    ReservationDemo(root, args.database.resolve())
    root.mainloop()


if __name__ == "__main__":
    main()
