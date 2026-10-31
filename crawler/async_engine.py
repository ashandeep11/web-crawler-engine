import asyncio
import csv
import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import aiohttp
from bs4 import BeautifulSoup


class AsyncWebCrawler:
    """Asynchronous, same-domain web crawler."""

    def __init__(
        self,
        max_depth=2,
        max_pages=20,
        concurrency=5,
        delay=1.0,
        timeout=15,
        retries=2,
        user_agent="WebCrawlerEngine/1.0",
    ):
        if max_depth < 0:
            raise ValueError("max_depth cannot be negative")
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        if delay < 0:
            raise ValueError("delay cannot be negative")

        self.max_depth = max_depth
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.delay = delay
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self.user_agent = user_agent

        self.visited = set()
        self.records = []
        self.failures = 0
        self.robots_skipped = 0
        self.urls_checked = 0

        self.robots_cache = {}
        self.domain_locks = defaultdict(asyncio.Lock)
        self.last_request_time = {}

    @staticmethod
    def normalize_url(url):
        parts = urlsplit(url.strip())

        if parts.scheme not in ("http", "https") or not parts.netloc:
            return None

        path = parts.path or "/"

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            parts.query,
            "",
        ))

    @staticmethod
    def same_host(url, seed_hosts):
        try:
            return urlsplit(url).netloc.lower() in seed_hosts
        except ValueError:
            return False

    async def get_robots_parser(self, url, session):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"

        if origin in self.robots_cache:
            return self.robots_cache[origin]

        robots_url = f"{origin}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            async with session.get(robots_url) as response:
                if response.status == 404:
                    parser.parse([])
                elif response.status >= 400:
                    parser.parse(["User-agent: *", "Disallow: /"])
                else:
                    content = await response.text(errors="replace")
                    parser.parse(content.splitlines())

        except (aiohttp.ClientError, asyncio.TimeoutError):
            # If robots.txt cannot be checked, do not crawl that origin.
            parser.parse(["User-agent: *", "Disallow: /"])

        self.robots_cache[origin] = parser
        return parser

    async def wait_for_domain(self, url):
        host = urlsplit(url).netloc.lower()

        async with self.domain_locks[host]:
            previous = self.last_request_time.get(host, 0)
            elapsed = time.monotonic() - previous
            remaining = self.delay - elapsed

            if remaining > 0:
                await asyncio.sleep(remaining)

            self.last_request_time[host] = time.monotonic()

    @staticmethod
    def parse_html(html, page_url):
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.get_text(" ", strip=True) if soup.title else ""

        headings = [
            heading.get_text(" ", strip=True)
            for heading in soup.find_all(
                ["h1", "h2", "h3", "h4", "h5", "h6"]
            )
        ]

        paragraphs = [
            paragraph.get_text(" ", strip=True)
            for paragraph in soup.find_all("p")
            if paragraph.get_text(" ", strip=True)
        ]

        links = []
        for tag in soup.find_all("a", href=True):
            link = urljoin(page_url, tag["href"])
            links.append(link)

        images = [
            urljoin(page_url, image.get("src"))
            for image in soup.find_all("img", src=True)
        ]

        metadata = {}
        for tag in soup.find_all("meta"):
            key = tag.get("name") or tag.get("property")
            value = tag.get("content")

            if key and value:
                metadata[key] = value

        return {
            "url": page_url,
            "title": title,
            "headings": headings,
            "paragraphs": paragraphs,
            "links": list(dict.fromkeys(links)),
            "images": list(dict.fromkeys(images)),
            "metadata": metadata,
        }

    async def fetch_page(self, url, session, semaphore):
        async with semaphore:
            robots = await self.get_robots_parser(url, session)

            if not robots.can_fetch(self.user_agent, url):
                self.robots_skipped += 1
                logging.info("Robots.txt skipped: %s", url)
                return None

            await self.wait_for_domain(url)

            for attempt in range(self.retries + 1):
                try:
                    async with session.get(
                        url,
                        allow_redirects=True,
                    ) as response:

                        if response.status >= 500:
                            if attempt < self.retries:
                                await asyncio.sleep(2 ** attempt)
                                continue

                            self.failures += 1
                            return None

                        if response.status >= 400:
                            self.failures += 1
                            return None

                        content_type = response.headers.get(
                            "Content-Type", ""
                        ).lower()

                        if "html" not in content_type:
                            logging.info("Non-HTML page skipped: %s", url)
                            return None

                        html = await response.text(errors="replace")
                        record = self.parse_html(
                            html,
                            str(response.url),
                        )

                        record["status_code"] = response.status
                        record["content_type"] = content_type

                        return record

                except (aiohttp.ClientError, asyncio.TimeoutError) as error:
                    logging.warning(
                        "Attempt %s failed for %s: %s",
                        attempt + 1,
                        url,
                        error,
                    )

                    if attempt < self.retries:
                        await asyncio.sleep(2 ** attempt)

            self.failures += 1
            return None

    async def crawl(self, seed_urls):
        start_time = time.monotonic()

        normalized_seeds = []
        for url in seed_urls:
            normalized = self.normalize_url(url)
            if normalized and normalized not in normalized_seeds:
                normalized_seeds.append(normalized)

        if not normalized_seeds:
            raise ValueError("Provide at least one valid HTTP/HTTPS URL.")

        seed_hosts = {
            urlsplit(url).netloc.lower()
            for url in normalized_seeds
        }

        frontier = [(url, 0) for url in normalized_seeds]
        semaphore = asyncio.Semaphore(self.concurrency)

        headers = {"User-Agent": self.user_agent}

        connector = aiohttp.TCPConnector(
            limit=self.concurrency,
            enable_cleanup_closed=True,
        )

        async with aiohttp.ClientSession(
            headers=headers,
            timeout=self.timeout,
            connector=connector,
        ) as session:

            while frontier and len(self.visited) < self.max_pages:
                current_batch = []

                while frontier and len(current_batch) < self.concurrency:
                    url, depth = frontier.pop(0)

                    if url in self.visited:
                        continue

                    if len(self.visited) >= self.max_pages:
                        break

                    self.visited.add(url)
                    self.urls_checked += 1
                    current_batch.append((url, depth))

                if not current_batch:
                    break

                results = await asyncio.gather(
                    *[
                        self.fetch_page(url, session, semaphore)
                        for url, depth in current_batch
                    ],
                    return_exceptions=True,
                )

                for (requested_url, depth), result in zip(
                    current_batch, results
                ):
                    if isinstance(result, Exception):
                        self.failures += 1
                        logging.exception(
                            "Unexpected crawling error for %s",
                            requested_url,
                            exc_info=result,
                        )
                        continue

                    if result is None:
                        continue

                    result["depth"] = depth
                    self.records.append(result)

                    if depth >= self.max_depth:
                        continue

                    for link in result["links"]:
                        normalized = self.normalize_url(link)

                        if not normalized:
                            continue

                        if not self.same_host(normalized, seed_hosts):
                            continue

                        if normalized not in self.visited:
                            frontier.append((normalized, depth + 1))

        execution_time = time.monotonic() - start_time

        stats = {
            "mode": "asynchronous",
            "seed_urls": len(normalized_seeds),
            "pages_visited": len(self.records),
            "urls_checked": self.urls_checked,
            "failed_downloads": self.failures,
            "robots_skipped": self.robots_skipped,
            "execution_time_seconds": round(execution_time, 2),
            "concurrency": self.concurrency,
        }

        return self.records, stats


def export_async_results(records, stats, output_dir="output"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "async_crawler_results.json"
    csv_path = output_path / "async_crawler_results.csv"
    stats_path = output_path / "async_crawler_stats.json"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    columns = [
    "url",
    "title",
    "status_code",
    "content_type",
    "depth",
    "headings",
    "paragraphs",
    "links",
    "images",
    "metadata",

    ]

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for record in records:
            row = record.copy()

            for key in (
                "headings",
                "paragraphs",
                "links",
                "images",
                "metadata",
            ):
                row[key] = json.dumps(
                    row.get(key, []),
                    ensure_ascii=False,
                )

            writer.writerow(row)

    with stats_path.open("w", encoding="utf-8") as file:
        json.dump(stats, file, indent=4)

    return json_path, csv_path, stats_path