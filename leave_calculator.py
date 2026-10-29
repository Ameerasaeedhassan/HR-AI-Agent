<<<<<<< HEAD
from datetime import date
import json
import math

from sql_tool import query_employee_data


# DemoCo fictional policy SL-02, version 1.0.
ANNUAL_SICK_LEAVE_DAYS = 10.0


def calculate_sick_leave_balance(employee_id):
    """Calculate the balance at the dataset's recorded snapshot."""
    employee_id = employee_id.strip().upper()

    if not employee_id:
        raise ValueError("An employee ID is required.")

    snapshot_result = query_employee_data(
        """
        SELECT value
        FROM dataset_metadata
        WHERE key = ?
        """,
        ("snapshot_date",),
    )

    if not snapshot_result["rows"]:
        raise ValueError("The dataset snapshot date is missing.")

    snapshot_date = snapshot_result["rows"][0][0]
    snapshot = date.fromisoformat(snapshot_date)

    employee_result = query_employee_data(
        """
        SELECT
            full_name,
            employment_type,
            employment_status,
            joining_date
        FROM employees
        WHERE employee_id = ?
        """,
        (employee_id,),
    )

    if not employee_result["rows"]:
        raise ValueError(f"Employee {employee_id} was not found.")

    name, employment_type, employment_status, joining_date = (
        employee_result["rows"][0]
    )

    if employment_type != "full_time":
        raise ValueError(
            "This policy does not define entitlement for this "
            "employment type. Please confirm with HR."
        )

    if employment_status != "active":
        raise ValueError(
            "This calculator supports active employees only. "
            "Please confirm with HR."
        )

    if date.fromisoformat(joining_date) > snapshot:
        raise ValueError(
            "The employee had not joined by the snapshot date."
        )

    leave_result = query_employee_data(
        """
        SELECT verified_paid_days_taken, pending_days
        FROM sick_leave_balances
        WHERE employee_id = ?
          AND leave_year = ?
          AND snapshot_date = ?
        """,
        (employee_id, snapshot.year, snapshot_date),
    )

    if not leave_result["rows"]:
        raise ValueError(
            "No sick-leave record exists for this employee "
            "at the dataset snapshot. Missing records are not "
            "treated as zero leave taken."
        )

    taken, pending = map(float, leave_result["rows"][0])

    if not all(math.isfinite(value) for value in (taken, pending)):
        raise ValueError("Leave records contain invalid numbers.")

    if not 0 <= taken <= ANNUAL_SICK_LEAVE_DAYS:
        raise ValueError(
            "Verified paid leave is outside the policy allowance. "
            "HR must review the record."
        )

    if pending < 0:
        raise ValueError("Pending leave cannot be negative.")

    if any(value * 2 != int(value * 2) for value in (taken, pending)):
        raise ValueError(
            "Leave must be recorded in half-day or full-day increments."
        )

    remaining = ANNUAL_SICK_LEAVE_DAYS - taken

    return {
        "employee_id": employee_id,
        "employee_name": name,
        "as_of": snapshot_date,
        "annual_allowance_days": ANNUAL_SICK_LEAVE_DAYS,
        "verified_paid_days_taken": taken,
        "remaining_paid_sick_leave_days": remaining,
        "pending_days": pending,
        "pending_exceeds_remaining": pending > remaining,
        "policy_sections": ["SL-02", "SL-07"],
        "note": (
            "Pending requests are shown separately and are not "
            "deducted until HR verifies them. This calculation "
            "does not approve a leave request."
        ),
    }


def main():
    print("Testing the sick-leave calculator...\n")

    result = calculate_sick_leave_balance("EMP001")

    assert result["verified_paid_days_taken"] == 3.0
    assert result["remaining_paid_sick_leave_days"] == 7.0
    assert result["pending_days"] == 1.0

    print(json.dumps(result, indent=2))
    print("\nPASS: EMP001 has 7 days remaining; 1 pending day is separate.")

    # Our synthetic EMP007 record has used all 10 paid days.
    exhausted = calculate_sick_leave_balance("EMP007")
    assert exhausted["remaining_paid_sick_leave_days"] == 0.0
    print("PASS: Fully used allowance returns 0 days.")

    try:
        calculate_sick_leave_balance("EMP999")
    except ValueError as error:
        assert "was not found" in str(error)
        print("PASS: Unknown employee rejected.")
    else:
        raise AssertionError("Unknown employee should have been rejected.")

    print("\nCalculator checks passed.")


if __name__ == "__main__":
    main()
=======
from datetime import date
import json
import math

from sql_tool import query_employee_data


# DemoCo fictional policy SL-02, version 1.0.
ANNUAL_SICK_LEAVE_DAYS = 10.0


def calculate_sick_leave_balance(employee_id):
    """Calculate the balance at the dataset's recorded snapshot."""
    employee_id = employee_id.strip().upper()

    if not employee_id:
        raise ValueError("An employee ID is required.")

    snapshot_result = query_employee_data(
        """
        SELECT value
        FROM dataset_metadata
        WHERE key = ?
        """,
        ("snapshot_date",),
    )

    if not snapshot_result["rows"]:
        raise ValueError("The dataset snapshot date is missing.")

    snapshot_date = snapshot_result["rows"][0][0]
    snapshot = date.fromisoformat(snapshot_date)

    employee_result = query_employee_data(
        """
        SELECT
            full_name,
            employment_type,
            employment_status,
            joining_date
        FROM employees
        WHERE employee_id = ?
        """,
        (employee_id,),
    )

    if not employee_result["rows"]:
        raise ValueError(f"Employee {employee_id} was not found.")

    name, employment_type, employment_status, joining_date = (
        employee_result["rows"][0]
    )

    if employment_type != "full_time":
        raise ValueError(
            "This policy does not define entitlement for this "
            "employment type. Please confirm with HR."
        )

    if employment_status != "active":
        raise ValueError(
            "This calculator supports active employees only. "
            "Please confirm with HR."
        )

    if date.fromisoformat(joining_date) > snapshot:
        raise ValueError(
            "The employee had not joined by the snapshot date."
        )

    leave_result = query_employee_data(
        """
        SELECT verified_paid_days_taken, pending_days
        FROM sick_leave_balances
        WHERE employee_id = ?
          AND leave_year = ?
          AND snapshot_date = ?
        """,
        (employee_id, snapshot.year, snapshot_date),
    )

    if not leave_result["rows"]:
        raise ValueError(
            "No sick-leave record exists for this employee "
            "at the dataset snapshot. Missing records are not "
            "treated as zero leave taken."
        )

    taken, pending = map(float, leave_result["rows"][0])

    if not all(math.isfinite(value) for value in (taken, pending)):
        raise ValueError("Leave records contain invalid numbers.")

    if not 0 <= taken <= ANNUAL_SICK_LEAVE_DAYS:
        raise ValueError(
            "Verified paid leave is outside the policy allowance. "
            "HR must review the record."
        )

    if pending < 0:
        raise ValueError("Pending leave cannot be negative.")

    if any(value * 2 != int(value * 2) for value in (taken, pending)):
        raise ValueError(
            "Leave must be recorded in half-day or full-day increments."
        )

    remaining = ANNUAL_SICK_LEAVE_DAYS - taken

    return {
        "employee_id": employee_id,
        "employee_name": name,
        "as_of": snapshot_date,
        "annual_allowance_days": ANNUAL_SICK_LEAVE_DAYS,
        "verified_paid_days_taken": taken,
        "remaining_paid_sick_leave_days": remaining,
        "pending_days": pending,
        "pending_exceeds_remaining": pending > remaining,
        "policy_sections": ["SL-02", "SL-07"],
        "note": (
            "Pending requests are shown separately and are not "
            "deducted until HR verifies them. This calculation "
            "does not approve a leave request."
        ),
    }


def main():
    print("Testing the sick-leave calculator...\n")

    result = calculate_sick_leave_balance("EMP001")

    assert result["verified_paid_days_taken"] == 3.0
    assert result["remaining_paid_sick_leave_days"] == 7.0
    assert result["pending_days"] == 1.0

    print(json.dumps(result, indent=2))
    print("\nPASS: EMP001 has 7 days remaining; 1 pending day is separate.")

    # Our synthetic EMP007 record has used all 10 paid days.
    exhausted = calculate_sick_leave_balance("EMP007")
    assert exhausted["remaining_paid_sick_leave_days"] == 0.0
    print("PASS: Fully used allowance returns 0 days.")

    try:
        calculate_sick_leave_balance("EMP999")
    except ValueError as error:
        assert "was not found" in str(error)
        print("PASS: Unknown employee rejected.")
    else:
        raise AssertionError("Unknown employee should have been rejected.")

    print("\nCalculator checks passed.")


if __name__ == "__main__":
    main()
>>>>>>> 5f75f3e2a6a326a8b59ded22f40711899ce28042
