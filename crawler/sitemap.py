
"""XML sitemap discovery and URL extraction."""

import logging
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit

import requests


def discover_sitemaps(
    website_url,
    timeout=10,
    user_agent="StudentWebCrawler/1.0"
):
    """Find sitemap URLs using robots.txt and common paths."""

    parts = urlsplit(website_url)

    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("A valid HTTP or HTTPS website URL is required.")

    origin = f"{parts.scheme}://{parts.netloc}"
    robots_url = urljoin(origin, "/robots.txt")

    sitemap_urls = set()
    headers = {"User-Agent": user_agent}

    try:
        response = requests.get(
            robots_url,
            timeout=timeout,
            headers=headers
        )

        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.strip().lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()

                    if sitemap_url:
                        sitemap_urls.add(sitemap_url)

    except requests.RequestException as error:
        logging.warning(
            "Robots sitemap discovery failed: %s",
            error
        )

    sitemap_urls.add(urljoin(origin, "/sitemap.xml"))
    sitemap_urls.add(urljoin(origin, "/sitemap_index.xml"))

    return sorted(sitemap_urls)


def extract_sitemap_urls(
    sitemap_url,
    timeout=10,
    user_agent="StudentWebCrawler/1.0",
    max_urls=5000
):
    """Extract page URLs from a sitemap or sitemap index."""

    if max_urls < 1:
        raise ValueError("max_urls must be at least 1.")

    headers = {"User-Agent": user_agent}

    try:
        response = requests.get(
            sitemap_url,
            timeout=timeout,
            headers=headers
        )

        response.raise_for_status()

        # FIX: Remove whitespace/BOM before XML parsing.
        xml_content = response.content

        if isinstance(xml_content, bytes):
            xml_content = xml_content.lstrip(b"\xef\xbb\xbf \t\r\n")
        else:
            xml_content = xml_content.lstrip("\ufeff \t\r\n")

        root = ET.fromstring(xml_content)

    except (requests.RequestException, ET.ParseError) as error:
        logging.warning(
            "Could not read sitemap %s: %s",
            sitemap_url,
            error
        )
        return []

    namespace = ""

    if root.tag.startswith("{"):
        namespace = root.tag.split("}", 1)[0] + "}"

    results = []
    seen = set()

    # Sitemap index: contains other sitemap files.
    if root.tag.endswith("sitemapindex"):

        for sitemap in root.findall(namespace + "sitemap"):
            location = sitemap.find(namespace + "loc")

            if location is None or not location.text:
                continue

            child_url = location.text.strip()

            remaining = max_urls - len(results)

            if remaining <= 0:
                break

            child_pages = extract_sitemap_urls(
                child_url,
                timeout=timeout,
                user_agent=user_agent,
                max_urls=remaining
            )

            for page_url in child_pages:
                if page_url not in seen:
                    seen.add(page_url)
                    results.append(page_url)

                if len(results) >= max_urls:
                    return results

    # Normal sitemap: contains page URLs.
    elif root.tag.endswith("urlset"):

        for item in root.findall(namespace + "url"):
            location = item.find(namespace + "loc")

            if location is None or not location.text:
                continue

            page_url = location.text.strip()

            if page_url not in seen:
                seen.add(page_url)
                results.append(page_url)

            if len(results) >= max_urls:
                break

    return results
