import argparse
import asyncio
import logging

from crawler.async_engine import (
    AsyncWebCrawler,
    export_async_results,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Asynchronous Web Crawler"
    )

    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more seed URLs",
    )
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--retries", type=int, default=2)

    return parser.parse_args()


async def main():
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    crawler = AsyncWebCrawler(
        max_depth=args.depth,
        max_pages=args.max_pages,
        concurrency=args.concurrency,
        delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
    )

    records, stats = await crawler.crawl(args.urls)

    json_file, csv_file, stats_file = export_async_results(
        records,
        stats,
    )

    print("\n========== ASYNC CRAWLER REPORT ==========")
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\nFiles generated:")
    print(json_file)
    print(csv_file)
    print(stats_file)


if __name__ == "__main__":
    asyncio.run(main())