
"""SQLite database storage for the web crawler."""

import sqlite3
import json
from pathlib import Path


class CrawlerDatabase:

    def __init__(self, database_path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.connection = sqlite3.connect(
            str(self.database_path)
        )

        self.connection.row_factory = sqlite3.Row

        self.create_tables()

    def create_tables(self):
        """Create database tables."""

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS crawled_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                status_code INTEGER,
                depth INTEGER,
                canonical TEXT,
                headings TEXT,
                paragraphs TEXT,
                links TEXT,
                images TEXT,
                metadata TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                seed_urls TEXT,
                pages_visited INTEGER,
                urls_checked INTEGER,
                failed_downloads INTEGER,
                robots_skipped INTEGER,
                execution_time_seconds REAL
            )
        """)

        self.connection.commit()

    def save_pages(self, records):
        """Insert or update crawled page records."""

        query = """
            INSERT INTO crawled_pages (
                url, title, status_code, depth, canonical,
                headings, paragraphs, links, images, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                status_code = excluded.status_code,
                depth = excluded.depth,
                canonical = excluded.canonical,
                headings = excluded.headings,
                paragraphs = excluded.paragraphs,
                links = excluded.links,
                images = excluded.images,
                metadata = excluded.metadata,
                crawled_at = CURRENT_TIMESTAMP
        """

        rows = []

        for record in records:
            rows.append((
                record.get("url", ""),
                record.get("title", ""),
                record.get("status_code"),
                record.get("depth"),
                record.get("canonical", ""),
                json.dumps(record.get("headings", []), ensure_ascii=False),
                json.dumps(record.get("paragraphs", []), ensure_ascii=False),
                json.dumps(record.get("links", []), ensure_ascii=False),
                json.dumps(record.get("images", []), ensure_ascii=False),
                json.dumps(record.get("metadata", {}), ensure_ascii=False)
            ))

        self.connection.executemany(query, rows)
        self.connection.commit()

        return len(rows)

    def save_crawl_history(self, seed_urls, stats):
        """Save crawl execution statistics."""

        self.connection.execute("""
            INSERT INTO crawl_history (
                seed_urls,
                pages_visited,
                urls_checked,
                failed_downloads,
                robots_skipped,
                execution_time_seconds
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            json.dumps(seed_urls),
            stats.get("pages_visited", 0),
            stats.get("urls_checked", 0),
            stats.get("failed_downloads", 0),
            stats.get("robots_skipped", 0),
            stats.get("execution_time_seconds", 0)
        ))

        self.connection.commit()

    def get_all_pages(self):
        """Return all saved pages."""

        cursor = self.connection.execute("""
            SELECT * FROM crawled_pages
            ORDER BY crawled_at DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def get_page_count(self):
        """Return total saved page count."""

        cursor = self.connection.execute(
            "SELECT COUNT(*) FROM crawled_pages"
        )

        return cursor.fetchone()[0]

    def get_crawl_history(self):
        """Return saved crawl history."""

        cursor = self.connection.execute("""
            SELECT * FROM crawl_history
            ORDER BY started_at DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""

        if self.connection:
            self.connection.close()
            self.connection = None
