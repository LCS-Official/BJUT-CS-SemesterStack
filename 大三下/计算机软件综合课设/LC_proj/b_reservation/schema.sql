CREATE TABLE IF NOT EXISTS reservation (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    lab_id INTEGER NOT NULL,
    equipment_id INTEGER,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'rejected', 'cancelled', 'using',
        'completed', 'suspected_violation', 'no_show', 'violation_processed'
    )),
    approver_id INTEGER,
    approved_at TEXT,
    approve_comment TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reservation_equipment_time
    ON reservation (equipment_id, start_time, end_time, status);

CREATE INDEX IF NOT EXISTS idx_reservation_lab_time
    ON reservation (lab_id, start_time, end_time, status);

CREATE INDEX IF NOT EXISTS idx_reservation_user_created
    ON reservation (user_id, created_at DESC);
