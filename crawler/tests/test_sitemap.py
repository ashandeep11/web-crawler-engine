
"""Tests for sitemap discovery."""

from unittest.mock import Mock

import pytest

from crawler.sitemap import (
    discover_sitemaps,
    extract_sitemap_urls
)


def test_discover_sitemaps_from_robots(monkeypatch):
    response = Mock()
    response.status_code = 200
    response.text = (
        "User-agent: *\n"
        "Sitemap: https://example.com/custom-sitemap.xml\n"
    )

    monkeypatch.setattr(
        "crawler.sitemap.requests.get",
        lambda *args, **kwargs: response
    )

    results = discover_sitemaps("https://example.com")

    assert "https://example.com/custom-sitemap.xml" in results
    assert "https://example.com/sitemap.xml" in results


def test_extract_urls_from_sitemap(monkeypatch):
    xml_content = b"""
    <?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
        </url>
        <url>
            <loc>https://example.com/about</loc>
        </url>
    </urlset>
    """

    response = Mock()
    response.content = xml_content
    response.raise_for_status.return_value = None

    monkeypatch.setattr(
        "crawler.sitemap.requests.get",
        lambda *args, **kwargs: response
    )

    results = extract_sitemap_urls(
        "https://example.com/sitemap.xml"
    )

    assert len(results) == 2
    assert "https://example.com/" in results
    assert "https://example.com/about" in results


def test_extract_sitemap_respects_max_urls(monkeypatch):
    xml_content = b"""
    <urlset>
        <url><loc>https://example.com/1</loc></url>
        <url><loc>https://example.com/2</loc></url>
        <url><loc>https://example.com/3</loc></url>
    </urlset>
    """

    response = Mock()
    response.content = xml_content
    response.raise_for_status.return_value = None

    monkeypatch.setattr(
        "crawler.sitemap.requests.get",
        lambda *args, **kwargs: response
    )

    results = extract_sitemap_urls(
        "https://example.com/sitemap.xml",
        max_urls=2
    )

    assert len(results) == 2


def test_invalid_website_url():
    with pytest.raises(ValueError):
        discover_sitemaps("not-a-valid-url")
