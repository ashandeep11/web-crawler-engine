
import csv
import json
from pathlib import Path


def export_json(records, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    return output_path


def export_csv(records, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "url",
        "title",
        "status_code",
        "depth",
        "paragraphs",
        "headings",
        "links",
        "images",
        "metadata",
    ]

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fieldnames, extrasaction="ignore"
        )
        writer.writeheader()

        for record in records:
            row = record.copy()

            for key in ["paragraphs", "headings", "links", "images", "metadata"]:
                row[key] = json.dumps(
                    row.get(key, [] if key != "metadata" else {}),
                    ensure_ascii=False
                )

            writer.writerow(row)

    return output_path


def export_stats(stats, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(stats, file, indent=4, ensure_ascii=False)

    return output_path
