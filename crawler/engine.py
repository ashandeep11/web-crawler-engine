
"""Crawl pages within starting domains."""

import logging
import time
from collections import deque

from crawler.fetcher import PageFetcher
from crawler.parser import parse_html
from crawler.utils import normalize_url, same_host


class WebCrawler:
    def __init__(self, config):
        self.config = config
        self.fetcher = PageFetcher(config)

        self.visited = set()
        self.records = []
        self.failures = 0
        self.skipped = 0

    def crawl(self, seed_urls, extra_urls=None):
        """
        Crawl starting URLs and optional URLs discovered from sitemaps.

        Sitemap URLs are added at depth 1.
        """

        queue = deque()
        start_time = time.monotonic()

        normalized_seeds = []

        # Add starting URLs at depth 0.
        for seed in seed_urls:
            url = normalize_url(seed)

            if url and url not in normalized_seeds:
                normalized_seeds.append(url)
                queue.append((url, 0))

        # Add sitemap URLs at depth 1.
        # Only accept URLs belonging to a starting domain.
        sitemap_added = 0

        for sitemap_url in extra_urls or []:
            url = normalize_url(sitemap_url)

            if not url:
                continue

            belongs_to_seed = any(
                same_host(seed, url)
                for seed in normalized_seeds
            )

            if not belongs_to_seed:
                continue

            if url not in self.visited:
                queue.append((url, 1))
                sitemap_added += 1

        logging.info(
            "Starting crawl with %s seeds and %s sitemap URLs",
            len(normalized_seeds),
            sitemap_added
        )

        try:
            while queue and len(self.visited) < self.config.max_pages:
                url, depth = queue.popleft()

                if url in self.visited:
                    continue

                if depth > self.config.max_depth:
                    continue

                self.visited.add(url)
                logging.info("Processing URL: %s", url)

                # Respect robots.txt.
                if not self.fetcher.allowed_by_robots(url):
                    logging.info("Skipped by robots policy: %s", url)
                    self.skipped += 1
                    continue

                result = self.fetcher.fetch(url)

                if result is None:
                    self.failures += 1
                    continue

                final_url, html, status_code = result

                if any(
                    item["url"] == final_url
                    for item in self.records
                ):
                    continue

                record = parse_html(html, final_url)
                record["status_code"] = status_code
                record["depth"] = depth

                self.records.append(record)

                if depth >= self.config.max_depth:
                    continue

                # Add same-domain links discovered on the page.
                for link in record.get("links", []):
                    next_url = normalize_url(link.get("url"))

                    if not next_url:
                        continue

                    if not same_host(final_url, next_url):
                        continue

                    if next_url not in self.visited:
                        queue.append((next_url, depth + 1))

        finally:
            self.fetcher.close()

        elapsed = round(
            time.monotonic() - start_time,
            2
        )

        stats = {
            "seed_urls": len(normalized_seeds),
            "sitemap_urls_added": sitemap_added,
            "pages_visited": len(self.records),
            "urls_checked": len(self.visited),
            "failed_downloads": self.failures,
            "robots_skipped": self.skipped,
            "execution_time_seconds": elapsed
        }

        logging.info("Crawl finished: %s", stats)

        return self.records, stats
