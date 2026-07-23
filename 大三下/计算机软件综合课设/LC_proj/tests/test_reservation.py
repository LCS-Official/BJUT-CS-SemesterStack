import tempfile
import threading
import unittest
from pathlib import Path

from b_reservation import (
    ConflictError,
    InvalidReservationError,
    InvalidStateError,
    PermissionDenied,
    ReservationStore,
)


class ReservationStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = ReservationStore(Path(self.temp_dir.name) / "test.db")
        self.store.init_schema()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create(self, request_id="req-1", start="2026-07-02T09:00:00", end="2026-07-02T10:00:00"):
        return self.store.create(
            request_id=request_id,
            user_id=1,
            lab_id=1,
            equipment_id=1,
            start_time=start,
            end_time=end,
            purpose="软件课程实验",
            student_is_eligible=True,
            resource_is_bookable=True,
        )

    def test_create_is_idempotent(self):
        first = self.create()
        second = self.create()
        self.assertEqual(first["reservation_id"], second["reservation_id"])
        self.assertEqual("pending", second["status"])

    def test_overlap_conflicts_but_adjacent_time_is_allowed(self):
        self.create()
        with self.assertRaises(ConflictError):
            self.create("overlap", "2026-07-02T09:30:00", "2026-07-02T10:30:00")
        adjacent = self.create("adjacent", "2026-07-02T10:00:00", "2026-07-02T11:00:00")
        self.assertEqual("pending", adjacent["status"])

    def test_list_by_time_range_returns_overlapping_reservations(self):
        first = self.create("range-a", "2026-07-02T09:00:00", "2026-07-02T10:00:00")
        second = self.create("range-b", "2026-07-02T10:00:00", "2026-07-02T11:00:00")
        self.store.create(
            request_id="range-other-lab",
            user_id=2,
            lab_id=2,
            equipment_id=2,
            start_time="2026-07-02T09:30:00",
            end_time="2026-07-02T10:30:00",
            purpose="其它实验室预约",
            student_is_eligible=True,
            resource_is_bookable=True,
        )

        rows = self.store.list_by_time_range(
            "2026-07-02T09:30:00",
            "2026-07-02T10:30:00",
            lab_id=1,
        )
        self.assertEqual(
            [first["reservation_id"], second["reservation_id"]],
            [row["reservation_id"] for row in rows],
        )
        with self.assertRaises(InvalidReservationError):
            self.store.list_by_time_range(
                "2026-07-02T10:30:00",
                "2026-07-02T09:30:00",
            )

    def test_twenty_concurrent_requests_create_one_active_reservation(self):
        count = 20
        barrier = threading.Barrier(count)
        results = []
        lock = threading.Lock()

        def submit(number):
            barrier.wait()
            try:
                self.create(f"concurrent-{number}")
                outcome = "created"
            except ConflictError:
                outcome = "conflict"
            with lock:
                results.append(outcome)

        threads = [threading.Thread(target=submit, args=(i,)) for i in range(count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(1, results.count("created"))
        self.assertEqual(19, results.count("conflict"))

    def test_approve_requires_scope_and_changes_state(self):
        reservation = self.create()
        with self.assertRaises(PermissionDenied):
            self.store.approve(
                reservation["reservation_id"],
                approver_id=2,
                can_manage_lab=False,
                resource_is_bookable=True,
            )
        approved = self.store.approve(
            reservation["reservation_id"],
            approver_id=2,
            comment="同意",
            can_manage_lab=True,
            resource_is_bookable=True,
        )
        self.assertEqual("approved", approved["status"])

    def test_late_cancel_returns_credit_action_without_writing_credit_table(self):
        reservation = self.create()
        cancelled = self.store.cancel(
            reservation["reservation_id"],
            actor_can_cancel=True,
            now="2026-07-02T08:30:00",
            exemption_hours=2,
        )
        self.assertEqual("cancelled", cancelled["status"])
        self.assertTrue(cancelled["credit_deduction_required"])

    def test_completed_reservation_cannot_be_cancelled(self):
        reservation = self.create()
        with self.store._connection() as conn:
            conn.execute(
                "UPDATE reservation SET status = 'completed' WHERE reservation_id = ?",
                (reservation["reservation_id"],),
            )
        with self.assertRaises(InvalidStateError):
            self.store.cancel(
                reservation["reservation_id"],
                actor_can_cancel=True,
                now="2026-07-02T08:00:00",
                exemption_hours=2,
            )

    def test_field_equipment_integration_methods(self):
        reservation = self.create()
        approved = self.store.approve(
            reservation["reservation_id"],
            approver_id=2,
            can_manage_lab=True,
            resource_is_bookable=True,
        )

        affected = self.store.list_affected_by_equipment(
            1,
            now="2026-07-02T08:30:00",
        )
        self.assertEqual([approved["reservation_id"]], [item["reservation_id"] for item in affected])

        using = self.store.mark_using(reservation["reservation_id"])
        self.assertEqual("using", using["status"])
        self.assertTrue(
            self.store.student_has_equipment_relation(
                1,
                1,
                now="2026-07-02T09:30:00",
                recent_days=1,
            )
        )
        completed = self.store.mark_completed(reservation["reservation_id"])
        self.assertEqual("completed", completed["status"])

    def test_maintenance_cancel_does_not_require_credit_deduction(self):
        reservation = self.create()
        cancelled = self.store.cancel_for_maintenance(
            reservation["reservation_id"],
            now="2026-07-02T09:30:00",
        )
        self.assertEqual("cancelled", cancelled["status"])
        self.assertFalse(cancelled["credit_deduction_required"])


if __name__ == "__main__":
    unittest.main()
