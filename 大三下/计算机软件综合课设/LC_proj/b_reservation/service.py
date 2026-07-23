from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


# 会参与冲突检测的有效预约状态：待审批、已通过、使用中。
ACTIVE_STATUSES = ("pending", "approved", "using")
# 学生或管理员还能取消的状态：已完成、已取消等状态不允许再次取消。
CANCELLABLE_STATUSES = ("pending", "approved")


class ReservationError(Exception):
    """预约业务规则异常的基类。"""


class InvalidReservationError(ReservationError):
    pass


class ConflictError(ReservationError):
    pass


class InvalidStateError(ReservationError):
    pass


class PermissionDenied(ReservationError):
    pass


class ReservationStore:
    """FR-03/04/05 的 SQLite 参考实现。

    A 的统一主入口可以直接复用这些业务方法。
    """

    def __init__(self, database_path: str | Path):
        # 作用：保存数据库文件路径，后续所有预约读写都基于这个 SQLite 文件。
        self.database_path = str(database_path)

    def connect(self) -> sqlite3.Connection:
        # 作用：创建数据库连接，并设置返回结果格式和等待锁的时间。
        conn = sqlite3.connect(self.database_path, timeout=10)
        # 让查询结果可以像字典一样按字段名读取，例如 row["status"]。
        conn.row_factory = sqlite3.Row
        # 开启外键约束，避免未来接入关联表时出现无效数据。
        conn.execute("PRAGMA foreign_keys = ON")
        # 数据库忙时最多等待 10 秒，降低并发写入时直接失败的概率。
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn

    @contextmanager
    def _connection(self, *, immediate: bool = False):
        # 作用：统一管理数据库连接、提交、回滚和关闭，避免每个函数重复写。
        conn = self.connect()
        try:
            if immediate:
                # 写预约前先拿 SQLite 写锁，保证“查冲突”和“插入”不会被并发穿透。
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            # 任何一步出错都回滚，避免只写入了一半的脏数据。
            conn.rollback()
            raise
        finally:
            # 无论成功还是失败，最后都释放数据库连接。
            conn.close()

    def init_schema(self) -> None:
        # 作用：初始化预约模块需要的数据表和索引。
        # 数据库结构统一放在 schema.sql，方便服务器初始化和文档对照。
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with self._connection() as conn:
            conn.executescript(schema)

    def create(
        self,
        *,
        request_id: str,
        user_id: int,
        lab_id: int,
        equipment_id: int | None,
        start_time: str | datetime,
        end_time: str | datetime,
        purpose: str,
        student_is_eligible: bool,
        resource_is_bookable: bool,
    ) -> dict:
        # 作用：创建一条待审批预约，是学生提交预约的核心入口。
        # 先做参数清洗和基础校验，避免非法数据进入事务。
        request_id = request_id.strip()
        purpose = purpose.strip()
        start = _local_time(start_time)
        end = _local_time(end_time)
        # 用户、实验室、设备编号都必须是正整数，防止无意义编号进入数据库。
        _positive_id("user_id", user_id)
        _positive_id("lab_id", lab_id)
        if equipment_id is not None:
            _positive_id("equipment_id", equipment_id)
        if not request_id or len(request_id) > 64:
            raise InvalidReservationError("request_id 必须为 1～64 个字符")
        if not purpose or len(purpose) > 255:
            raise InvalidReservationError("预约事由必须为 1～255 个字符")
        if start >= end:
            raise InvalidReservationError("预约结束时间必须晚于开始时间")
        # 信用/封禁资格由 D 模块判断，B 只根据结果决定能否预约。
        if not student_is_eligible:
            raise PermissionDenied("当前信用或封禁状态不允许预约")
        # 设备是否开放、维修、停用由 C 模块判断，B 不重复维护设备状态。
        if not resource_is_bookable:
            raise InvalidReservationError("目标资源当前不可预约")

        with self._connection(immediate=True) as conn:
            # 当前课程规模下用 SQLite 短写锁即可；真要高并发时再换成资源行锁。
            existing = conn.execute(
                "SELECT * FROM reservation WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing:
                # request_id 已存在时直接返回原预约，解决重复点击/网络重试问题。
                return dict(existing)
            # 插入前检查时间冲突，保证同一资源同一时间不能有多条有效预约。
            conflict = self._find_conflict(
                conn, lab_id, equipment_id, start, end, exclude_id=None
            )
            if conflict:
                raise ConflictError(f"预约时段与预约 {conflict['reservation_id']} 冲突")
            # 只有通过资格、资源状态和冲突检查后，才真正写入待审批预约。
            cursor = conn.execute(
                """
                INSERT INTO reservation (
                    request_id, user_id, lab_id, equipment_id,
                    start_time, end_time, purpose, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    request_id,
                    user_id,
                    lab_id,
                    equipment_id,
                    start,
                    end,
                    purpose,
                    _now(),
                ),
            )
            return self.get(cursor.lastrowid, conn=conn)

    def get(self, reservation_id: int, *, conn: sqlite3.Connection | None = None) -> dict:
        # 作用：按预约编号读取单条预约，其他审批/取消/联动函数都会先调用它。
        _positive_id("reservation_id", reservation_id)
        # 如果外部已经在事务中，就复用传入连接；否则本函数自己创建连接。
        owns_connection = conn is None
        conn = conn or self.connect()
        try:
            row = conn.execute(
                "SELECT * FROM reservation WHERE reservation_id = ?",
                (reservation_id,),
            ).fetchone()
            if not row:
                raise InvalidReservationError("预约不存在")
            return dict(row)
        finally:
            if owns_connection:
                conn.close()

    def list_for_user(self, user_id: int) -> list[dict]:
        _positive_id("user_id", user_id)
        with self._connection() as conn:
            # 作用：查询某个学生自己的全部预约，用于“我的预约”页面。
            # 学生“我的预约”按开始时间倒序展示，最近的预约排在前面。
            rows = conn.execute(
                """
                SELECT * FROM reservation
                WHERE user_id = ?
                ORDER BY start_time DESC, reservation_id DESC
                """,
                (user_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_by_time_range( # 按照时间查reserve
        self,
        start_time: str | datetime,
        end_time: str | datetime,
        *,
        lab_id: int | None = None,
        user_id: int | None = None,
    ) -> list[dict]:
        # 作用：按查询时间段筛选预约，用于管理员检索和演示窗口展示。
        # 使用半开区间重叠判断：[start_time, end_time)，首尾相接不算重叠。
        start = _local_time(start_time)
        end = _local_time(end_time)
        if start >= end:
            raise InvalidReservationError("查询结束时间必须晚于开始时间")
        clauses = ["start_time < ?", "end_time > ?"]
        params: list[object] = [end, start]
        if lab_id is not None:
            _positive_id("lab_id", lab_id)
            clauses.append("lab_id = ?")
            params.append(lab_id)
        if user_id is not None:
            _positive_id("user_id", user_id)
            clauses.append("user_id = ?")
            params.append(user_id)
        with self._connection() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM reservation
                WHERE {' AND '.join(clauses)}
                ORDER BY start_time, reservation_id
                """,
                params,
            ).fetchall()
            return [dict(row) for row in rows]

    def list_pending_for_lab(self, lab_id: int) -> list[dict]:
        _positive_id("lab_id", lab_id)
        with self._connection() as conn:
            # 作用：查询指定实验室的待审批预约，用于管理员审批页面。
            # 管理员审批页只取待审批预约，按预约时间从早到晚排列。
            rows = conn.execute(
                """
                SELECT * FROM reservation
                WHERE lab_id = ? AND status = 'pending'
                ORDER BY start_time, reservation_id
                """,
                (lab_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def approve(
        self,
        reservation_id: int,
        *,
        approver_id: int,
        comment: str = "",
        can_manage_lab: bool,
        resource_is_bookable: bool,
    ) -> dict:
        # 作用：管理员审批通过预约，把状态从 pending 改为 approved。
        _positive_id("approver_id", approver_id)
        # 审批权限和设备可用性由 A/C 模块在服务端给出结论。
        if not can_manage_lab:
            raise PermissionDenied("无权审批该实验室预约")
        if not resource_is_bookable:
            raise InvalidReservationError("设备维修、停用或时段不可用，不能通过审批")
        with self._connection(immediate=True) as conn:
            current = self.get(reservation_id, conn=conn)
            if current["status"] != "pending":
                raise InvalidStateError("只有待审批预约可以通过")
            # 审批时再查一次冲突，防止待审批期间出现新的有效预约。
            conflict = self._find_conflict(
                conn,
                current["lab_id"],
                current["equipment_id"],
                current["start_time"],
                current["end_time"],
                exclude_id=reservation_id,
            )
            if conflict:
                raise ConflictError(f"审批时发现预约 {conflict['reservation_id']} 冲突")
            # 记录审批人、审批时间和审批意见，方便后续追溯。
            conn.execute(
                """
                UPDATE reservation
                SET status = 'approved', approver_id = ?, approved_at = ?,
                    approve_comment = ?
                WHERE reservation_id = ?
                """,
                (approver_id, _now(), comment.strip()[:255], reservation_id),
            )
            return self.get(reservation_id, conn=conn)

    def reject(
        self,
        reservation_id: int,
        *,
        approver_id: int,
        comment: str,
        can_manage_lab: bool,
    ) -> dict:
        # 作用：管理员驳回预约，把状态从 pending 改为 rejected。
        _positive_id("approver_id", approver_id)
        # 只有有管辖权限的管理员才能驳回该实验室预约。
        if not can_manage_lab:
            raise PermissionDenied("无权审批该实验室预约")
        with self._connection(immediate=True) as conn:
            current = self.get(reservation_id, conn=conn)
            if current["status"] != "pending":
                raise InvalidStateError("只有待审批预约可以驳回")
            # 驳回时同样记录审批人、时间和原因。
            conn.execute(
                """
                UPDATE reservation
                SET status = 'rejected', approver_id = ?, approved_at = ?,
                    approve_comment = ?
                WHERE reservation_id = ?
                """,
                (approver_id, _now(), comment.strip()[:255], reservation_id),
            )
            return self.get(reservation_id, conn=conn)

    def cancel(
        self,
        reservation_id: int,
        *,
        actor_can_cancel: bool,
        now: str | datetime,
        exemption_hours: float,
        maintenance_cancel: bool = False,
    ) -> dict:
        # 作用：取消预约，可用于学生主动取消，也可用于管理员维护取消。
        if not actor_can_cancel:
            raise PermissionDenied("无权取消该预约")
        if exemption_hours < 0:
            raise InvalidReservationError("取消免责时限不能为负数")
        current_time = datetime.fromisoformat(_local_time(now))
        with self._connection(immediate=True) as conn:
            current = self.get(reservation_id, conn=conn)
            # 只有待审批和已通过预约还能取消，已完成/已取消不能重复操作。
            if current["status"] not in CANCELLABLE_STATUSES:
                raise InvalidStateError("当前预约状态不可取消")
            start = datetime.fromisoformat(current["start_time"])
            # 预约已经开始后，不能再按“主动取消”处理。
            if current_time >= start:
                raise InvalidStateError("预约开始后不可主动取消")
            # 临近开始时间取消需要通知 D 模块扣分；维护取消不扣学生信用。
            late_cancel = (
                not maintenance_cancel
                and start - current_time <= timedelta(hours=exemption_hours)
            )
            conn.execute(
                "UPDATE reservation SET status = 'cancelled' WHERE reservation_id = ?",
                (reservation_id,),
            )
            result = self.get(reservation_id, conn=conn)
            # 返回给 D 模块判断是否需要扣信用分，B 不直接改信用表。
            result["late_cancel"] = late_cancel
            result["credit_deduction_required"] = late_cancel
            return result

    def mark_using(
        self,
        reservation_id: int,
        now: str | datetime | None = None,
    ) -> dict:
        # 作用：C 模块签到核验通过后，把已通过预约改为使用中。
        with self._connection(immediate=True) as conn:
            current = self.get(reservation_id, conn=conn)
            # 只有已审批通过的预约才能签到进入使用状态。
            if current["status"] != "approved":
                raise InvalidStateError("只有已通过预约可以签到使用")
            conn.execute(
                "UPDATE reservation SET status = 'using' WHERE reservation_id = ?",
                (reservation_id,),
            )
            return self.get(reservation_id, conn=conn)

    def mark_completed(
        self,
        reservation_id: int,
        now: str | datetime | None = None,
    ) -> dict:
        # 作用：C 模块签退核验通过后，把使用中预约改为已完成。
        with self._connection(immediate=True) as conn:
            current = self.get(reservation_id, conn=conn)
            # 只有已经签到使用中的预约，才允许签退完成。
            if current["status"] != "using":
                raise InvalidStateError("只有使用中预约可以签退完成")
            conn.execute(
                "UPDATE reservation SET status = 'completed' WHERE reservation_id = ?",
                (reservation_id,),
            )
            return self.get(reservation_id, conn=conn)

    def list_affected_by_equipment(
        self,
        equipment_id: int,
        *,
        now: str | datetime,
    ) -> list[dict]:
        # 作用：查询某设备当前和未来仍会受维修影响的有效预约。
        _positive_id("equipment_id", equipment_id)
        current_time = _local_time(now)
        with self._connection() as conn:
            # 设备报修/维护时，C 模块用这里查询后续会受影响的预约。
            rows = conn.execute(
                """
                SELECT * FROM reservation
                WHERE equipment_id = ?
                  AND status IN (?, ?, ?)
                  AND end_time > ?
                ORDER BY start_time, reservation_id
                """,
                (equipment_id, *ACTIVE_STATUSES, current_time),
            ).fetchall()
            return [dict(row) for row in rows]

    def cancel_for_maintenance(
        self,
        reservation_id: int,
        *,
        now: str | datetime | None = None,
    ) -> dict:
        # 作用：设备维护导致的系统取消，不触发学生临期取消扣分。
        with self._connection(immediate=True) as conn:
            current = self.get(reservation_id, conn=conn)
            # 维护取消只处理还没结束业务流程的预约。
            if current["status"] not in CANCELLABLE_STATUSES:
                raise InvalidStateError("只有待审批或已通过预约可以维护取消")
            conn.execute(
                "UPDATE reservation SET status = 'cancelled' WHERE reservation_id = ?",
                (reservation_id,),
            )
            result = self.get(reservation_id, conn=conn)
            # 明确告诉调用方：这是系统维护取消，不是学生违约取消。
            result["late_cancel"] = False
            result["credit_deduction_required"] = False
            return result

    def student_has_equipment_relation(
        self,
        user_id: int,
        equipment_id: int,
        *,
        now: str | datetime,
        recent_days: int,
    ) -> bool:
        # 作用：判断学生近期是否和某设备存在预约/使用关系，辅助报修资格判断。
        # C 模块报修时使用：只有近期预约/使用过该设备的学生才算有关联。
        _positive_id("user_id", user_id)
        _positive_id("equipment_id", equipment_id)
        if not isinstance(recent_days, int) or recent_days < 0:
            raise InvalidReservationError("recent_days 必须为非负整数")
        current_time = datetime.fromisoformat(_local_time(now))
        # recent_days 控制“近期”的范围，例如最近 7 天内使用过该设备。
        cutoff = (current_time - timedelta(days=recent_days)).isoformat(
            timespec="seconds"
        )
        with self._connection() as conn:
            # 只要查到一条有效关联记录，就认为该学生可以对设备报修。
            row = conn.execute(
                """
                SELECT 1 FROM reservation
                WHERE user_id = ?
                  AND equipment_id = ?
                  AND status IN ('approved', 'using', 'completed')
                  AND start_time <= ?
                  AND end_time >= ?
                LIMIT 1
                """,
                (
                    user_id,
                    equipment_id,
                    current_time.isoformat(timespec="seconds"),
                    cutoff,
                ),
            ).fetchone()
            return row is not None

    def _find_conflict(
        self,
        conn: sqlite3.Connection,
        lab_id: int,
        equipment_id: int | None,
        start_time: str,
        end_time: str,
        *,
        exclude_id: int | None,
    ) -> sqlite3.Row | None:
        # 作用：查找是否存在与目标时间段重叠的有效预约。
        # 半开区间判断：[start_time, end_time)，首尾相接不算冲突，真正重叠才冲突。
        params: list[object] = [*ACTIVE_STATUSES, end_time, start_time]
        if equipment_id is None:
            # equipment_id 为空时表示预约整个实验室，按 lab_id 检查冲突。
            resource_clause = "lab_id = ? AND equipment_id IS NULL"
            params.append(lab_id)
        else:
            # 指定设备时按 equipment_id 检查冲突。
            resource_clause = "equipment_id = ?"
            params.append(equipment_id)
        exclude_clause = ""
        if exclude_id is not None:
            # 审批当前预约时，要排除它自己，否则会和自身冲突。
            exclude_clause = "AND reservation_id <> ?"
            params.append(exclude_id)
        return conn.execute(
            f"""
            SELECT * FROM reservation
            WHERE status IN (?, ?, ?)
              AND start_time < ?
              AND end_time > ?
              AND {resource_clause}
              {exclude_clause}
            LIMIT 1
            """,
            params,
        ).fetchone()


def _local_time(value: str | datetime) -> str:
    # 作用：把外部传入时间统一转换成服务器本地 ISO 字符串。
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise InvalidReservationError("时间必须使用 ISO 格式") from exc
    # 当前约定不接受带时区偏移的时间，避免各模块时间比较口径不一致。
    if parsed.tzinfo is not None:
        raise InvalidReservationError("当前版本统一使用服务器本地时间，不接受带时区时间")
    return parsed.isoformat(timespec="seconds")


def _positive_id(name: str, value: int) -> None:
    # 作用：统一校验各种 ID 字段必须是正整数。
    if not isinstance(value, int) or value <= 0:
        raise InvalidReservationError(f"{name} 必须为正整数")


def _now() -> str:
    # 作用：生成当前服务器本地时间，统一精确到秒。
    return datetime.now().isoformat(timespec="seconds")
