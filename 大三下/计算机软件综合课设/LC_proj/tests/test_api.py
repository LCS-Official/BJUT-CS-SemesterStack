import tempfile
import unittest
from pathlib import Path

from flask import Flask

from b_reservation import ReservationStore, create_app, register_routes


class ReservationApiTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.current_actor = {"user_id": 1, "role": "student"}
        self.audit_calls = []
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": Path(self.temp_dir.name) / "api.db",
                "CURRENT_ACTOR": lambda: self.current_actor,
                "STUDENT_IS_ELIGIBLE": lambda user_id: user_id == 1,
                "RESOURCE_IS_BOOKABLE": lambda lab, equipment, start, end: True,
                "CAN_MANAGE_LAB": lambda user_id, lab_id: user_id == 2 and lab_id == 1,
                "AUDIT": lambda **kwargs: self.audit_calls.append(kwargs),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create(self):
        return self.client.post(
            "/api/reservations",
            headers={"Idempotency-Key": "api-request-1"},
            json={
                "lab_id": 1,
                "equipment_id": 1,
                "start_time": "2026-07-03T09:00:00",
                "end_time": "2026-07-03T10:00:00",
                "purpose": "软件课程实验",
                # These untrusted fields must have no effect.
                "student_is_eligible": False,
                "resource_is_bookable": False,
            },
        )

    def test_health_does_not_require_integrations(self):
        response = self.client.get("/health")
        self.assertEqual(200, response.status_code)
        self.assertEqual("ok", response.json["status"])

    def test_create_uses_server_side_checks_and_lists_own_reservation(self):
        response = self.create()
        self.assertEqual(201, response.status_code)
        self.assertEqual("pending", response.json["reservation"]["status"])
        self.assertEqual("reservation.create", self.audit_calls[-1]["action"])
        listed = self.client.get("/api/reservations/me")
        self.assertEqual(1, len(listed.json["reservations"]))

    def test_query_reservations_by_time_range(self):
        reservation_id = self.create().json["reservation"]["reservation_id"]
        self.current_actor = {"user_id": 2, "role": "lab_admin"}
        response = self.client.get(
            "/api/reservations",
            query_string={
                "lab_id": 1,
                "start_time": "2026-07-03T08:30:00",
                "end_time": "2026-07-03T09:30:00",
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [reservation_id],
            [row["reservation_id"] for row in response.json["reservations"]],
        )

    def test_approval_requires_server_side_lab_scope(self):
        reservation_id = self.create().json["reservation"]["reservation_id"]
        denied = self.client.post(f"/api/reservations/{reservation_id}/approve", json={})
        self.assertEqual(403, denied.status_code)

        self.current_actor = {"user_id": 2, "role": "lab_admin"}
        approved = self.client.post(
            f"/api/reservations/{reservation_id}/approve",
            json={"comment": "同意"},
        )
        self.assertEqual(200, approved.status_code)
        self.assertEqual("approved", approved.json["reservation"]["status"])
        self.assertEqual("reservation.approve", self.audit_calls[-1]["action"])

    def test_missing_integration_returns_503(self):
        app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": Path(self.temp_dir.name) / "missing.db",
            }
        )
        response = app.test_client().get("/api/reservations/me")
        self.assertEqual(503, response.status_code)

    def test_register_routes_supports_group_unified_app_without_health(self):
        app = Flask(__name__)
        app.config.update(
            TESTING=True,
            DATABASE_PATH=Path(self.temp_dir.name) / "unified.db",
            CURRENT_ACTOR=lambda: self.current_actor,
            STUDENT_IS_ELIGIBLE=lambda user_id: True,
            RESOURCE_IS_BOOKABLE=lambda lab, equipment, start, end: True,
            CAN_MANAGE_LAB=lambda user_id, lab_id: False,
        )
        store = ReservationStore(app.config["DATABASE_PATH"])
        store.init_schema()
        register_routes(app, store, register_health=False)

        client = app.test_client()
        self.assertEqual(404, client.get("/health").status_code)
        self.assertEqual(201, self.create_with(client).status_code)

    def create_with(self, client):
        return client.post(
            "/api/reservations",
            headers={"Idempotency-Key": "api-request-2"},
            json={
                "lab_id": 1,
                "equipment_id": 1,
                "start_time": "2026-07-04T09:00:00",
                "end_time": "2026-07-04T10:00:00",
                "purpose": "统一入口测试",
            },
        )


if __name__ == "__main__":
    unittest.main()
