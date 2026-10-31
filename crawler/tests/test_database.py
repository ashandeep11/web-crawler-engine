
"""Tests for SQLite database storage."""

import sqlite3

from crawler.database import CrawlerDatabase


def test_database_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"

    database = CrawlerDatabase(db_path)

    cursor = database.connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
    """)

    tables = {row[0] for row in cursor.fetchall()}

    database.close()

    assert "crawled_pages" in tables
    assert "crawl_history" in tables


def test_save_and_count_pages(tmp_path):
    database = CrawlerDatabase(tmp_path / "test.db")

    records = [
        {
            "url": "https://example.com",
            "title": "Example Website",
            "status_code": 200,
            "depth": 0,
            "canonical": "https://example.com",
            "headings": [{"tag": "h1", "text": "Welcome"}],
            "paragraphs": ["Example paragraph"],
            "links": [],
            "images": [],
            "metadata": {"description": "Example site"}
        }
    ]

    saved = database.save_pages(records)

    assert saved == 1
    assert database.get_page_count() == 1

    database.close()


def test_duplicate_url_updates_existing_page(tmp_path):
    database = CrawlerDatabase(tmp_path / "test.db")

    first_record = {
        "url": "https://example.com",
        "title": "Old Title"
    }

    updated_record = {
        "url": "https://example.com",
        "title": "New Title"
    }

    database.save_pages([first_record])
    database.save_pages([updated_record])

    pages = database.get_all_pages()

    assert len(pages) == 1
    assert pages[0]["title"] == "New Title"

    database.close()


def test_save_crawl_history(tmp_path):
    database = CrawlerDatabase(tmp_path / "test.db")

    stats = {
        "pages_visited": 5,
        "urls_checked": 6,
        "failed_downloads": 1,
        "robots_skipped": 0,
        "execution_time_seconds": 2.5
    }

    database.save_crawl_history(
        ["https://example.com"],
        stats
    )

    history = database.get_crawl_history()

    assert len(history) == 1
    assert history[0]["pages_visited"] == 5

    database.close()


def test_empty_database_has_zero_pages(tmp_path):
    database = CrawlerDatabase(tmp_path / "test.db")

    assert database.get_page_count() == 0

    database.close()
