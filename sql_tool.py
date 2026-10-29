from pathlib import Path
import json
import sqlite3
import time


PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "employees.db"

ALLOWED_TABLES = {
    "employees",
    "dataset_metadata",
    "sick_leave_balances",
}
ALLOWED_FUNCTIONS = {
    "count", "sum", "avg", "min", "max",
    "round", "lower", "upper", "coalesce",
    "length", "abs",
}

MAX_ROWS = 100
MAX_QUERY_SECONDS = 3


def authorize(action, arg1, arg2, database, trigger):
    """Allow approved reads and functions; deny other operations."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK

    if action == sqlite3.SQLITE_READ:
        if arg1 in ALLOWED_TABLES:
            normal_read = database == "main"

            # COUNT(*) can report an empty column name
            # and no database name.
            count_read = database is None and arg2 == ""

            if normal_read or count_read:
                return sqlite3.SQLITE_OK

    if action == sqlite3.SQLITE_FUNCTION:
        function_name = (arg2 or "").lower()
        if function_name in ALLOWED_FUNCTIONS:
            return sqlite3.SQLITE_OK

    return sqlite3.SQLITE_DENY

def query_employee_data(sql, parameters=()):
    """
    Execute one read-only SQL query.

    Returns column names, rows, and whether results were truncated.
    Use ? placeholders for values supplied through parameters.
    """
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Please provide a SQL query.")

    if len(sql) > 10000:
        raise ValueError("SQL query is too long.")

    if not DB_PATH.is_file():
        raise FileNotFoundError(
            "employees.db is missing. Run create_employee_db.py first."
        )

    # mode=ro prevents this connection from changing the database.
    database_uri = DB_PATH.resolve().as_uri() + "?mode=ro"

    connection = sqlite3.connect(
        database_uri,
        uri=True,
        timeout=3,
    )

    try:
        connection.execute("PRAGMA query_only = ON")
        connection.set_authorizer(authorize)

        deadline = time.monotonic() + MAX_QUERY_SECONDS

        # Interrupt queries that take too long.
        connection.set_progress_handler(
            lambda: int(time.monotonic() > deadline),
            1000,
        )

        # execute accepts one statement, rather than a SQL script.
        cursor = connection.execute(sql, parameters)

        if cursor.description is None:
            raise ValueError("The query must return results.")

        columns = [
            description[0]
            for description in cursor.description
        ]

        # Fetch one extra row to detect truncation.
        rows = cursor.fetchmany(MAX_ROWS + 1)
        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]

        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
        }

    except sqlite3.Error as error:
        raise ValueError(
            f"Query failed or was blocked: {error}"
        ) from error

    finally:
        connection.close()


def main():
    print("Testing the employee SQL tool...\n")

    # Test 1: Known total from our synthetic dataset.
    total = query_employee_data(
        "SELECT COUNT(*) AS employee_count FROM employees"
    )
    assert total["rows"] == [[30]], "Expected 30 employees."
    print("PASS: Total employees = 30")

    # Test 2: A parameterized query.
    it_count = query_employee_data(
        """
        SELECT COUNT(*) AS employee_count
        FROM employees
        WHERE department = ?
        """,
        ("IT",),
    )
    assert it_count["rows"] == [[6]], "Expected 6 IT employees."
    print("PASS: IT employees = 6")

    # Test 3: Grouped analysis.
    departments = query_employee_data(
        """
        SELECT
            department,
            COUNT(*) AS employee_count,
            ROUND(AVG(monthly_salary_aed), 2)
                AS average_monthly_salary_aed
        FROM employees
        GROUP BY department
        ORDER BY department
        """
    )
    assert len(departments["rows"]) == 5
    assert all(row[1] == 6 for row in departments["rows"])

    print("\nDepartment summary:")
    print(json.dumps(departments, indent=2))

    # Test 4: Attempt a harmless zero-row write.
    # It must still be blocked because writes are forbidden.
    try:
        query_employee_data(
            "DELETE FROM employees WHERE 1 = 0"
        )
    except ValueError:
        print("\nPASS: DELETE was blocked.")
    else:
        raise AssertionError("Write protection test failed.")

    # Confirm the data remains present.
    final_count = query_employee_data(
        "SELECT COUNT(*) FROM employees"
    )
    assert final_count["rows"] == [[30]]

    print("PASS: All 30 employees remain.")
    print("\nSQL tool checks passed.")


if __name__ == "__main__":
    main()