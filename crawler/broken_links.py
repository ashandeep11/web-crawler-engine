
"""Broken link checking module."""

import csv
from pathlib import Path

from crawler.fetcher import PageFetcher
from crawler.utils import same_host


def check_broken_links(records, config):
    """Check unique same-domain links found in crawled pages."""

    fetcher = PageFetcher(config)
    checked_urls = set()
    results = []

    try:
        for record in records:
            source_url = record["url"]

            for link in record.get("links", []):
                target_url = link.get("url")

                if not target_url:
                    continue

                # Check only links from the same host.
                if not same_host(source_url, target_url):
                    continue

                # Avoid checking duplicate URLs.
                if target_url in checked_urls:
                    continue

                checked_urls.add(target_url)

                result = fetcher.check_link(target_url)
                result["source_url"] = source_url

                results.append(result)

    finally:
        fetcher.close()

    return results


def export_broken_links(results, output_path):
    """Export link checking results to CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "source_url",
        "url",
        "status_code",
        "status",
        "final_url"
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
        writer.writerows(results)

    return output_path
