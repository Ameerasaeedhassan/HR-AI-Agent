from pathlib import Path

# Locate the project using this script's location.
PROJECT_DIR = Path(__file__).resolve().parent
POLICY_DIR = PROJECT_DIR / "data" / "policies"

expected_files = [
    "annual_leave.md",
    "sick_leave.md",
    "working_hours.md",
    "benefits.md",
    "probation.md",
]

valid_count = 0

for filename in expected_files:
    file_path = POLICY_DIR / filename

    if not file_path.is_file():
        print(f"MISSING: {filename}")
        continue

    text = file_path.read_text(encoding="utf-8")

    # Each numbered policy section starts with "## ".
    sections = [
        line for line in text.splitlines()
        if line.startswith("## ")
    ]

    if not text.strip() or not sections:
        print(f"CHECK: {filename} — empty or missing section headings")
        continue

    print(f"OK: {filename} — {len(sections)} sections")
    valid_count += 1

print(f"\nReady: {valid_count}/{len(expected_files)} policy files")