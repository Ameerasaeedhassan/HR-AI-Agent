from pathlib import Path
from datetime import date
import random
import sqlite3


PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "employees.db"

# Fixed snapshot makes our evaluation results reproducible.
SNAPSHOT_DATE = date(2026, 10, 26)

DEPARTMENTS = {
    "IT": ("Software Developer", 9000, 16000),
    "HR": ("HR Coordinator", 7000, 12000),
    "Finance": ("Accountant", 8000, 14000),
    "Operations": ("Operations Coordinator", 6500, 11000),
    "Sales": ("Sales Executive", 7000, 13000),
}


def create_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Avoid overwriting an existing database.
    if DB_PATH.exists():
        print(f"Database already exists: {DB_PATH}")
        print("No changes made.")
        return

    rng = random.Random(42)
    employees = []

    for number in range(1, 31):
        department = list(DEPARTMENTS)[(number - 1) % 5]
        job_title, minimum_salary, maximum_salary = (
            DEPARTMENTS[department]
        )

        # These are deliberately assigned fictional HR records.
        # Confirmation is not inferred automatically from tenure.
        if number <= 20:
            joining_date = date(
                2025,
                ((number - 1) % 12) + 1,
                1,
            )
            probation_status = "confirmed"
            confirmation_date = date(2026, 4, 1).isoformat()

        elif number <= 25:
            joining_date = date(2026, 9, 1)
            probation_status = "in_probation"
            confirmation_date = None

        else:
            joining_date = date(2026, 6, 1)
            probation_status = "pending_review"
            confirmation_date = None

        monthly_salary = rng.randrange(
            minimum_salary,
            maximum_salary + 1,
            500,
        )

        employees.append(
            (
                f"EMP{number:03d}",
                f"Demo Employee {number:03d}",
                department,
                job_title,
                "full_time",
                joining_date.isoformat(),
                monthly_salary,
                probation_status,
                confirmation_date,
                "active",
            )
        )

    connection = sqlite3.connect(DB_PATH)

    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE dataset_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE employees (
                    employee_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    department TEXT NOT NULL
                        CHECK (department IN (
                            'IT', 'HR', 'Finance',
                            'Operations', 'Sales'
                        )),
                    job_title TEXT NOT NULL,
                    employment_type TEXT NOT NULL
                        CHECK (employment_type = 'full_time'),
                    joining_date TEXT NOT NULL,
                    monthly_salary_aed INTEGER NOT NULL
                        CHECK (monthly_salary_aed > 0),
                    probation_status TEXT NOT NULL
                        CHECK (probation_status IN (
                            'confirmed',
                            'in_probation',
                            'pending_review'
                        )),
                    confirmation_date TEXT,
                    employment_status TEXT NOT NULL
                        CHECK (employment_status IN (
                            'active', 'inactive'
                        )),
                    CHECK (
                        (
                            probation_status = 'confirmed'
                            AND confirmation_date IS NOT NULL
                            AND confirmation_date >= joining_date
                        )
                        OR
                        (
                            probation_status != 'confirmed'
                            AND confirmation_date IS NULL
                        )
                    )
                )
                """
            )

            connection.executemany(
                """
                INSERT INTO dataset_metadata (key, value)
                VALUES (?, ?)
                """,
                [
                    ("dataset_type", "synthetic educational data"),
                    ("company", "DemoCo"),
                    ("snapshot_date", SNAPSHOT_DATE.isoformat()),
                    ("currency", "AED"),
                    ("salary_basis", "monthly"),
                    ("seed", "42"),
                ],
            )

            connection.executemany(
                """
                INSERT INTO employees (
                    employee_id,
                    full_name,
                    department,
                    job_title,
                    employment_type,
                    joining_date,
                    monthly_salary_aed,
                    probation_status,
                    confirmation_date,
                    employment_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                employees,
            )

        # Check the saved data with actual SQL queries.
        employee_count = connection.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        department_counts = connection.execute(
            """
            SELECT department, COUNT(*)
            FROM employees
            GROUP BY department
            ORDER BY department
            """
        ).fetchall()

        probation_counts = connection.execute(
            """
            SELECT probation_status, COUNT(*)
            FROM employees
            GROUP BY probation_status
            ORDER BY probation_status
            """
        ).fetchall()

        print(f"Created: {DB_PATH}")
        print(f"Snapshot date: {SNAPSHOT_DATE}")
        print(f"Fictional employees: {employee_count}")

        print("\nEmployees by department:")
        for department, count in department_counts:
            print(f"- {department}: {count}")

        print("\nRecorded probation status:")
        for status, count in probation_counts:
            print(f"- {status}: {count}")

    finally:
        connection.close()


if __name__ == "__main__":
    create_database()