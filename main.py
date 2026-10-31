
"""Main entry point for Web Crawler & Data Extraction Engine."""

import argparse
import csv
import logging
from pathlib import Path

from crawler.config import CrawlerConfig
from crawler.engine import WebCrawler
from crawler.exporter import export_csv, export_json
from crawler.broken_links import check_broken_links, export_broken_links
from crawler.seo_analyzer import analyze_seo, export_seo_report
from crawler.sitemap import discover_sitemaps, extract_sitemap_urls
from crawler.database import CrawlerDatabase


def parse_arguments():
    """Read command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Advanced Web Crawler & Data Extraction Engine"
    )

    parser.add_argument(
        "urls",
        nargs="+",
        help="Starting website URLs"
    )

    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum crawl depth"
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum pages to crawl"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Request timeout in seconds"
    )

    parser.add_argument(
        "--keyword",
        type=str,
        default=None,
        help="Search keyword in extracted content"
    )

    return parser.parse_args()


def configure_logging(log_dir):
    """Configure application logging."""

    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=log_dir / "crawler.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
        force=True
    )


def search_keyword(records, keyword):
    """Search keyword in extracted page content."""

    if not keyword:
        return []

    keyword = keyword.lower()
    matches = []

    for record in records:
        title = record.get("title", "")

        headings = " ".join(
            item.get("text", "")
            for item in record.get("headings", [])
        )

        paragraphs = " ".join(
            record.get("paragraphs", [])
        )

        content = f"{title} {headings} {paragraphs}".lower()

        if keyword in content:
            matches.append({
                "url": record.get("url", ""),
                "title": title,
                "keyword": keyword
            })

    return matches


def save_keyword_report(matches, output_dir):
    """Save keyword search results to CSV."""

    output_path = output_dir / "keyword_report.csv"

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        fieldnames = ["url", "title", "keyword"]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(matches)

    return output_path


def run_sitemap_discovery(urls, config):
    """Discover sitemap files and extract page URLs."""

    print("\nDiscovering XML sitemaps...")

    sitemap_urls = set()

    for website_url in urls:
        try:
            discovered = discover_sitemaps(
                website_url,
                timeout=config.timeout,
                user_agent=config.user_agent
            )

            sitemap_urls.update(discovered)

        except Exception as error:
            logging.warning(
                "Sitemap discovery failed for %s: %s",
                website_url,
                error
            )

    sitemap_pages = set()

    for sitemap_url in sorted(sitemap_urls):

        remaining = 5000 - len(sitemap_pages)

        if remaining <= 0:
            break

        try:
            pages = extract_sitemap_urls(
                sitemap_url,
                timeout=config.timeout,
                user_agent=config.user_agent,
                max_urls=remaining
            )

            sitemap_pages.update(pages)

        except Exception as error:
            logging.warning(
                "Sitemap extraction failed for %s: %s",
                sitemap_url,
                error
            )

    sitemap_path = config.output_dir / "sitemap_urls.txt"

    sitemap_path.write_text(
        "\n".join(sorted(sitemap_pages)),
        encoding="utf-8"
    )

    print(f"Sitemaps discovered: {len(sitemap_urls)}")
    print(f"Sitemap URLs extracted: {len(sitemap_pages)}")

    return sorted(sitemap_pages), sitemap_path


def main():
    """Execute the complete crawler workflow."""

    args = parse_arguments()

    if args.depth < 0:
        raise SystemExit("Error: --depth cannot be negative.")

    if args.max_pages < 1:
        raise SystemExit("Error: --max-pages must be at least 1.")

    if args.delay < 0:
        raise SystemExit("Error: --delay cannot be negative.")

    if args.timeout < 1:
        raise SystemExit("Error: --timeout must be at least 1.")

    base_dir = Path(__file__).resolve().parent

    output_dir = base_dir / "output"
    log_dir = base_dir / "logs"

    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    configure_logging(log_dir)

    config = CrawlerConfig()

    config.max_depth = args.depth
    config.max_pages = args.max_pages
    config.delay = args.delay
    config.timeout = args.timeout
    config.output_dir = output_dir
    config.log_dir = log_dir

    database_path = output_dir / "crawler_data.db"
    database = CrawlerDatabase(database_path)

    try:
        print("\n======================================")
        print(" WEB CRAWLER & DATA EXTRACTION ENGINE")
        print("======================================")

        # 1. Sitemap discovery.
        sitemap_pages, sitemap_path = run_sitemap_discovery(
            args.urls,
            config
        )

        # 2. Main crawling with sitemap URLs.
        print("\nStarting crawler...")

        crawler = WebCrawler(config)

        records, stats = crawler.crawl(
            args.urls,
            extra_urls=sitemap_pages
        )

        print(f"Pages extracted: {len(records)}")

        # 3. Save pages and crawl history in SQLite.
        print("\nSaving data to SQLite database...")

        saved_pages = database.save_pages(records)

        database.save_crawl_history(
            args.urls,
            stats
        )

        print(f"Database records saved: {saved_pages}")
        print(
            "Total pages in database: "
            f"{database.get_page_count()}"
        )

        # 4. Keyword search.
        keyword_path = None

        if args.keyword:
            print("\nSearching keyword...")

            matches = search_keyword(
                records,
                args.keyword
            )

            keyword_path = save_keyword_report(
                matches,
                output_dir
            )

            print(f"Keyword matches: {len(matches)}")

        # 5. SEO analysis.
        print("\nRunning SEO analysis...")

        seo_reports = analyze_seo(records)

        seo_path = output_dir / "seo_report.csv"

        export_seo_report(
            seo_reports,
            seo_path
        )

        print(f"SEO pages analyzed: {len(seo_reports)}")

        # 6. Broken link checking.
        print("\nChecking website links...")

        broken_links = check_broken_links(
            records,
            config
        )

        broken_links_path = output_dir / "broken_links.csv"

        export_broken_links(
            broken_links,
            broken_links_path
        )

        broken_count = sum(
            1 for item in broken_links
            if item.get("status") in ("Broken", "Request Error")
        )

        print(f"Links checked: {len(broken_links)}")
        print(f"Broken links: {broken_count}")

        # 7. Export crawler results.
        print("\nExporting crawler data...")

        json_path = output_dir / "crawler_results.json"
        csv_path = output_dir / "crawler_results.csv"
        stats_path = output_dir / "crawler_stats.json"

        export_json(records, json_path)
        export_csv(records, csv_path)
        export_json(stats, stats_path)

        # 8. Final summary.
        print("\n======================================")
        print("          CRAWL SUMMARY")
        print("======================================")

        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\nGenerated Reports:")
        print(f"JSON: {json_path}")
        print(f"CSV: {csv_path}")
        print(f"Statistics: {stats_path}")
        print(f"SEO report: {seo_path}")
        print(f"Broken links: {broken_links_path}")
        print(f"Sitemap URLs: {sitemap_path}")
        print(f"SQLite Database: {database_path}")

        if keyword_path:
            print(f"Keyword report: {keyword_path}")

        print("\nCrawler execution completed successfully.")

        logging.info(
            "Crawler execution completed successfully."
        )

    finally:
        database.close()


if __name__ == "__main__":
    main()
