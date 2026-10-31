
"""SEO analysis module for crawled web pages."""

import csv
from pathlib import Path
from urllib.parse import urlsplit


def analyze_seo(records):
    """Analyze SEO elements and return page-wise SEO reports."""

    reports = []

    for record in records:
        title = record.get("title", "").strip()
        metadata = record.get("metadata", {})
        headings = record.get("headings", [])
        images = record.get("images", [])

        # Find meta description (case-insensitive)
        description = ""

        for key, value in metadata.items():
            if key.lower() == "description":
                description = value.strip()
                break

        # Collect H1 headings
        h1_headings = [
            heading.get("text", "").strip()
            for heading in headings
            if heading.get("tag", "").lower() == "h1"
            and heading.get("text", "").strip()
        ]

        # Count images without ALT text
        missing_alt = sum(
            1 for image in images
            if not image.get("alt", "").strip()
        )

        # Find canonical URL
        canonical = record.get("canonical", "").strip()

        issues = []

        if not title:
            issues.append("Missing title")
        elif len(title) < 10:
            issues.append("Title too short")
        elif len(title) > 60:
            issues.append("Title too long")

        if not description:
            issues.append("Missing meta description")
        elif len(description) < 50:
            issues.append("Meta description too short")
        elif len(description) > 160:
            issues.append("Meta description too long")

        if not h1_headings:
            issues.append("Missing H1 heading")
        elif len(h1_headings) > 1:
            issues.append("Multiple H1 headings")

        if missing_alt:
            issues.append(
                f"{missing_alt} images missing ALT text"
            )

        if not canonical:
            issues.append("Missing canonical URL")

        reports.append({
            "url": record.get("url", ""),
            "title": title,
            "title_length": len(title),
            "meta_description": description,
            "description_length": len(description),
            "h1_count": len(h1_headings),
            "image_count": len(images),
            "images_missing_alt": missing_alt,
            "canonical_url": canonical,
            "seo_score": max(0, 100 - len(issues) * 15),
            "issues": issues
        })

    return reports


def export_seo_report(reports, output_path):
    """Export SEO analysis results to CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "url",
        "title",
        "title_length",
        "meta_description",
        "description_length",
        "h1_count",
        "image_count",
        "images_missing_alt",
        "canonical_url",
        "seo_score",
        "issues"
    ]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for report in reports:
            row = report.copy()
            row["issues"] = "; ".join(row["issues"])
            writer.writerow(row)

    return output_path
