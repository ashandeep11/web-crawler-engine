
"""Tests for SEO analyzer."""

import csv

from crawler.seo_analyzer import (
    analyze_seo,
    export_seo_report
)


def test_detects_missing_seo_elements():
    records = [{
        "url": "https://example.com/",
        "title": "",
        "metadata": {},
        "headings": [],
        "images": [],
        "canonical": ""
    }]

    reports = analyze_seo(records)

    assert len(reports) == 1
    assert "Missing title" in reports[0]["issues"]
    assert "Missing meta description" in reports[0]["issues"]
    assert "Missing H1 heading" in reports[0]["issues"]
    assert "Missing canonical URL" in reports[0]["issues"]


def test_detects_images_without_alt():
    records = [{
        "url": "https://example.com/",
        "title": "Example Website Home Page",
        "metadata": {
            "description": (
                "This is a sufficiently detailed example "
                "meta description for testing purposes."
            )
        },
        "headings": [
            {"tag": "h1", "text": "Welcome"}
        ],
        "images": [
            {"alt": "", "url": "https://example.com/image.jpg"}
        ],
        "canonical": "https://example.com/"
    }]

    reports = analyze_seo(records)

    assert reports[0]["images_missing_alt"] == 1
    assert "1 images missing ALT text" in reports[0]["issues"]


def test_detects_multiple_h1_headings():
    records = [{
        "url": "https://example.com/",
        "title": "Example Website Home Page",
        "metadata": {
            "description": (
                "This is a sufficiently detailed example "
                "meta description for testing purposes."
            )
        },
        "headings": [
            {"tag": "h1", "text": "Heading One"},
            {"tag": "h1", "text": "Heading Two"}
        ],
        "images": [],
        "canonical": "https://example.com/"
    }]

    reports = analyze_seo(records)

    assert reports[0]["h1_count"] == 2
    assert "Multiple H1 headings" in reports[0]["issues"]


def test_exports_seo_csv(tmp_path):
    reports = [{
        "url": "https://example.com/",
        "title": "Example",
        "title_length": 7,
        "meta_description": "",
        "description_length": 0,
        "h1_count": 0,
        "image_count": 0,
        "images_missing_alt": 0,
        "canonical_url": "",
        "seo_score": 40,
        "issues": ["Missing title"]
    }]

    output_path = tmp_path / "reports" / "seo_report.csv"

    saved_path = export_seo_report(reports, output_path)

    assert saved_path.exists()

    with saved_path.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["seo_score"] == "40"
