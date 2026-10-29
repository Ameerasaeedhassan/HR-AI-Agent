from pathlib import Path
import sqlite3


PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "employees.db"
SNAPSHOT_DATE = "2026-10-26"
LEAVE_YEAR = 2026


def main():
    if not DB_PATH.is_file():
        raise FileNotFoundError(
            "employees.db is missing. Run create_employee_db.py first."
        )

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        with connection:
            snapshot = connection.execute(
                """
                SELECT value
                FROM dataset_metadata
                WHERE key = 'snapshot_date'
                """
            ).fetchone()

            if snapshot != (SNAPSHOT_DATE,):
                raise ValueError(
                    "The employee dataset snapshot does not match "
                    "this leave dataset."
                )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sick_leave_balances (
                    employee_id TEXT NOT NULL,
                    leave_year INTEGER NOT NULL,
                    snapshot_date TEXT NOT NULL,
                    verified_paid_days_taken REAL NOT NULL
                        CHECK (
                            verified_paid_days_taken BETWEEN 0 AND 10
                            AND verified_paid_days_taken * 2
                                = CAST(
                                    verified_paid_days_taken * 2 AS INTEGER
                                )
                        ),
                    pending_days REAL NOT NULL
                        CHECK (
                            pending_days >= 0
                            AND pending_days * 2
                                = CAST(pending_days * 2 AS INTEGER)
                        ),
                    PRIMARY KEY (employee_id, leave_year, snapshot_date),
                    FOREIGN KEY (employee_id)
                        REFERENCES employees(employee_id)
                )
                """
            )

            employees = connection.execute(
                """
                SELECT employee_id
                FROM employees
                WHERE employment_type = 'full_time'
                  AND employment_status = 'active'
                ORDER BY employee_id
                """
            ).fetchall()

            records = []

            for (employee_id,) in employees:
                number = int(employee_id.removeprefix("EMP"))

                # Invented, reproducible educational records.
                taken = float((number * 3) % 11)
                pending = 1.0 if number % 5 == 1 else 0.0

                records.append(
                    (
                        employee_id,
                        LEAVE_YEAR,
                        SNAPSHOT_DATE,
                        taken,
                        pending,
                    )
                )

            changes_before = connection.total_changes

            connection.executemany(
                """
                INSERT INTO sick_leave_balances (
                    employee_id,
                    leave_year,
                    snapshot_date,
                    verified_paid_days_taken,
                    pending_days
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (
                    employee_id, leave_year, snapshot_date
                ) DO NOTHING
                """,
                records,
            )

            added = connection.total_changes - changes_before

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM sick_leave_balances
            WHERE snapshot_date = ?
              AND leave_year = ?
            """,
            (SNAPSHOT_DATE, LEAVE_YEAR),
        ).fetchone()[0]

        example = connection.execute(
            """
            SELECT
                employee_id,
                verified_paid_days_taken,
                pending_days
            FROM sick_leave_balances
            WHERE employee_id = ?
              AND leave_year = ?
              AND snapshot_date = ?
            """,
            ("EMP001", LEAVE_YEAR, SNAPSHOT_DATE),
        ).fetchone()

        print(f"New records added: {added}")
        print(f"Total records for this snapshot: {count}")
        print(f"Snapshot date: {SNAPSHOT_DATE}")

        if example:
            print(f"\nExample employee: {example[0]}")
            print(f"Verified paid sick leave taken: {example[1]} days")
            print(f"Pending sick leave: {example[2]} days")

        print("\nExisting records were preserved.")
        print("No employee records were changed.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()