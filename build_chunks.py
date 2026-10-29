from pathlib import Path
import json
import re

PROJECT_DIR = Path(__file__).resolve().parent
POLICY_DIR = PROJECT_DIR / "data" / "policies"
OUTPUT_PATH = PROJECT_DIR / "data" / "processed" / "policy_chunks.json"


def load_policy_chunks(policy_dir):
    chunks = []
    seen_ids = set()

    for file_path in sorted(policy_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8-sig")

        title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
        if not title_match:
            raise ValueError(f"Missing document title: {file_path.name}")

        document_title = title_match.group(1).strip()

        # Find headings such as: ## AL-01: Purpose and Scope
        headings = list(re.finditer(
            r"^## ([A-Z]+-\d+):[ \t]*(.+)$",
            text,
            re.MULTILINE,
        ))

        if not headings:
            raise ValueError(f"No valid sections: {file_path.name}")

        for index, heading in enumerate(headings):
            section_id = heading.group(1)
            section_title = heading.group(2).strip()

            start = heading.end()
            end = (
                headings[index + 1].start()
                if index + 1 < len(headings)
                else len(text)
            )
            body = text[start:end].strip()

            if not body:
                raise ValueError(f"Empty section: {section_id}")

            if section_id in seen_ids:
                raise ValueError(f"Duplicate section ID: {section_id}")

            seen_ids.add(section_id)

            chunks.append({
                "id": section_id,
                "text": (
                    f"{document_title}\n"
                    f"{section_id}: {section_title}\n\n"
                    f"{body}"
                ),
                "metadata": {
                    "source": file_path.name,
                    "document_title": document_title,
                    "section_id": section_id,
                    "section_title": section_title,
                },
            })

    return chunks


if __name__ == "__main__":
    chunks = load_policy_chunks(POLICY_DIR)

    if not chunks:
        raise ValueError("No policy chunks found. Check the policy folder.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Created {len(chunks)} chunks.")
    print(f"Saved to: {OUTPUT_PATH}")
    print("\nFirst chunk:")
    print(json.dumps(chunks[0], indent=2, ensure_ascii=False))