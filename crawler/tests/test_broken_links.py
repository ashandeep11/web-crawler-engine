
"""Tests for the broken link checker."""

import csv
from unittest.mock import MagicMock

from crawler.broken_links import (
    check_broken_links,
    export_broken_links
)


def make_config():
    """Create a lightweight test configuration."""
    config = MagicMock()
    config.user_agent = "TestCrawler/1.0"
    config.timeout = 5
    config.retries = 0
    config.delay = 0
    return config


def test_working_link_is_detected(monkeypatch):
    """A successful HTTP response should be Working."""

    records = [{
        "url": "https://example.com/",
        "links": [
            {
                "text": "Home",
                "url": "https://example.com/home"
            }
        ]
    }]

    fetcher = MagicMock()
    fetcher.check_link.return_value = {
        "url": "https://example.com/home",
        "status_code": 200,
        "status": "Working",
        "final_url": "https://example.com/home"
    }

    monkeypatch.setattr(
        "crawler.broken_links.PageFetcher",
        lambda config: fetcher
    )

    results = check_broken_links(records, make_config())

    assert len(results) == 1
    assert results[0]["status"] == "Working"
    fetcher.close.assert_called_once()


def test_broken_link_is_detected(monkeypatch):
    """A 404 response should be classified as Broken."""

    records = [{
        "url": "https://example.com/",
        "links": [
            {
                "text": "Missing",
                "url": "https://example.com/missing"
            }
        ]
    }]

    fetcher = MagicMock()
    fetcher.check_link.return_value = {
        "url": "https://example.com/missing",
        "status_code": 404,
        "status": "Broken",
        "final_url": "https://example.com/missing"
    }

    monkeypatch.setattr(
        "crawler.broken_links.PageFetcher",
        lambda config: fetcher
    )

    results = check_broken_links(records, make_config())

    assert len(results) == 1
    assert results[0]["status"] == "Broken"
    assert results[0]["status_code"] == 404


def test_duplicate_links_are_checked_once(monkeypatch):
    """Duplicate target URLs should only be checked once."""

    target = "https://example.com/about"

    records = [
        {
            "url": "https://example.com/",
            "links": [{"text": "About", "url": target}]
        },
        {
            "url": "https://example.com/contact",
            "links": [{"text": "About", "url": target}]
        }
    ]

    fetcher = MagicMock()
    fetcher.check_link.return_value = {
        "url": target,
        "status_code": 200,
        "status": "Working",
        "final_url": target
    }

    monkeypatch.setattr(
        "crawler.broken_links.PageFetcher",
        lambda config: fetcher
    )

    results = check_broken_links(records, make_config())

    assert len(results) == 1
    fetcher.check_link.assert_called_once_with(target)


def test_broken_links_csv_export(tmp_path):
    """The link report should be saved as a readable CSV."""

    results = [{
        "source_url": "https://example.com/",
        "url": "https://example.com/missing",
        "status_code": 404,
        "status": "Broken",
        "final_url": "https://example.com/missing"
    }]

    output_path = tmp_path / "reports" / "broken_links.csv"

    saved_path = export_broken_links(results, output_path)

    assert saved_path.exists()

    with saved_path.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["status"] == "Broken"
    assert rows[0]["status_code"] == "404"
