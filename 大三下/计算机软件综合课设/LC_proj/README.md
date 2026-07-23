# LC_proj：B 资源与预约模块

当前提交是可独立验证、可接入小组主程序的 Flask 预约模块，依据：

- FR-03：预约提交、时间冲突、事务和幂等。
- FR-04：管理员审批和管辖范围校验入口。
- FR-05：学生取消、临期取消和维护取消边界。
- Handoff B：资源与预约负责人。

## 已完成

- `reservation` 表和查询索引。
- 同设备/同实验室的重叠时间检测。
- SQLite 短事务串行化并发写入。
- `request_id` 幂等提交。
- 审批、驳回和取消状态校验。
- 临期取消结果返回，信用扣分由 D 模块执行。
- 20 个线程同时抢约时只创建 1 条有效预约的测试。
- 预约创建、个人列表、待审批列表、通过、驳回、取消 HTTP API。
- 所有身份、权限、信用和资源状态均从服务端集成函数取得。
- 已对齐组长 2026-07-10 统一入口：B 可通过 `register_routes(app, store, register_health=False)` 挂到 `unified_app:create_app()`。
- 已补充 C 模块联动方法：签到使用、签退完成、设备维护影响预约查询、维护取消、学生与设备近期预约关系判断。
- 创建、审批、驳回、取消预约时可调用 A 的 `AUDIT` 写操作日志。

## 运行测试

在 `LC_proj` 目录执行：

```powershell
conda run -n csv python -m pip install -r requirements.txt
conda run -n csv python -m unittest discover -s tests -v
```

当前测试共 13 项，包括 20 路并发冲突、HTTP 权限边界、统一入口挂载和 C 模块联动方法。

## B 模块课堂 Mini Demo

在 `LC_proj` 目录执行以下命令，会打开一个只使用 B 模块代码和独立演示数据库的桌面窗口：

```powershell
conda run -n csv python demo_gui.py
```

如果已经进入 `csv` 环境，也可以直接执行 `python demo_gui.py`。窗口包含学生预约、管理员审批/驳回/取消、冲突与幂等、20 路并发抢约，以及签到签退和设备维护联动。每次操作都会在下方标明对应的 HTTP 接口或 `ReservationStore` 方法。

演示数据保存在 `demo_reservations.db`，不会读写服务器数据库。可先运行无界面自检：

```powershell
conda run -n csv python demo_gui.py --self-test
```

## HTTP 接口

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/reservations` | 提交预约，须带 `Idempotency-Key` 请求头 |
| `GET` | `/api/reservations/me` | 当前用户的预约 |
| `GET` | `/api/reservations?start_time=...&end_time=...&lab_id=...` | 按预约时间段查询预约 |
| `GET` | `/api/labs/<lab_id>/reservations/pending` | 管理员查看待审批预约 |
| `POST` | `/api/reservations/<id>/approve` | 通过预约 |
| `POST` | `/api/reservations/<id>/reject` | 驳回预约 |
| `POST` | `/api/reservations/<id>/cancel` | 学生取消自己的预约或管理员维护取消 |

独立运行 B 模块时使用 `create_app(config)` 创建应用。接入全组统一 Flask 主入口时使用：

```python
from b_reservation import ReservationStore, register_routes

reservation_store = ReservationStore(database_path)
reservation_store.init_schema()
register_routes(app, reservation_store, register_health=False)
```

主程序需要注入以下服务端函数：

- `CURRENT_ACTOR() -> {"user_id": int, "role": str}`（A）
- `CAN_MANAGE_LAB(user_id, lab_id) -> bool`（A）
- `STUDENT_IS_ELIGIBLE(user_id) -> bool`（D）
- `RESOURCE_IS_BOOKABLE(lab_id, equipment_id, start_time, end_time) -> bool`（C）
- `AUDIT(...) -> None`（A，可选但建议接入关键操作日志）

缺少必要集成时，业务接口返回 `503`，不会采用前端传入的权限或资格值冒充结果。

## 给统一入口和 C 模块的 B 能力

`ReservationStore` 当前可直接提供给组长的 `unified_app.py`：

- `get(reservation_id)`：按编号读取预约。
- `mark_using(reservation_id, now=...)`：C 签到核验通过后，将已通过预约置为 `using`。
- `mark_completed(reservation_id, now=...)`：C 签退核验通过后，将使用中预约置为 `completed`。
- `list_affected_by_equipment(equipment_id, now=...)`：设备报修/维护时，查询受影响的待审批、已通过、使用中预约。
- `cancel_for_maintenance(reservation_id, now=...)`：设备维护导致的系统取消，不触发学生临期取消扣分。
- `student_has_equipment_relation(user_id, equipment_id, now=..., recent_days=...)`：C 报修校验学生是否近期使用过该设备。

## 服务器部署说明

`ReservationStore` 接收数据库路径，不包含个人绝对路径。当前 SQLite 实现适合本地开发和课程规模的单机在线部署；它通过 `BEGIN IMMEDIATE` 保证冲突检查与写入处于同一事务。

以下部署示例使用示例域名，部署时请替换为实际地址：

- 健康检查：`http://example.com/health`
- Ubuntu 24.04、Python 3.12.3、SQLite 3.45.1、Flask 3.1.3、Gunicorn 23、Nginx 1.24
- 代码：`/srv/lab-system`
- 数据库：`/var/lib/lab-system/reservations.db`
- 每日备份：`/var/backups/lab-system`，保留 7 天
- 服务管理：`systemctl status|restart lab-system`
- 日志：`journalctl -u lab-system`

部署文件保存在 `deploy/`。线上只开放 SSH 和 HTTP；Gunicorn 仅监听 `127.0.0.1:8000`，SQLite 不开放网络端口。

若全组确定使用 MySQL 或 PostgreSQL，保留 `ReservationStore` 的公开方法和测试语义，仅替换 SQL/连接层，并将全局写锁改为目标资源行锁。不要同时维护两套业务规则。

## 等待 A/C/D 的集成契约

- A：登录会话、当前角色、管辖范围、系统参数、操作日志；当前已按 `CURRENT_ACTOR`、`CAN_MANAGE_LAB`、`GET_PARAMETER`、`AUDIT` 的方式预留。
- C：实验室、设备、设备状态、可用时段；当前已按 `RESOURCE_IS_BOOKABLE` 和预约状态联动方法预留。
- D：信用/封禁查询、扣分、通知。

核心层的 `create()` 接收已经校验的资格结果；HTTP 层只会从上述服务端函数取得这些值。A/C/D 合并时替换函数实现即可，不需要改预约规则。

## 下一步

1. D 提供通知和信用接口后，接通审批通知与临期取消扣分。
2. 与 A/C 在线联调 `unified_app:create_app()`，确认 `/health` 返回包含 `reservation`。
3. 根据最终页面安排补浏览器页面或 API 调用截图。
4. 取得域名后为 Nginx 配置 HTTPS，并在正式演示前更换或禁用 root 密码登录。
