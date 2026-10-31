from crawler.async_engine import AsyncWebCrawler


def test_normalize_url_removes_fragment():
    result = AsyncWebCrawler.normalize_url(
        "https://example.com/page#section"
    )
    assert result == "https://example.com/page"


def test_normalize_url_rejects_invalid_scheme():
    assert AsyncWebCrawler.normalize_url("ftp://example.com") is None


def test_same_host():
    assert AsyncWebCrawler.same_host(
        "https://example.com/about",
        {"example.com"},
    )


def test_different_host():
    assert not AsyncWebCrawler.same_host(
        "https://other.com",
        {"example.com"},
    )


def test_parse_html():
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Hello World</h1>
            <p>Testing async crawler.</p>
            <a href="/about">About</a>
            <img src="/image.png">
        </body>
    </html>
    """

    result = AsyncWebCrawler.parse_html(
        html,
        "https://example.com",
    )

    assert result["title"] == "Test Page"
    assert "Hello World" in result["headings"]
    assert "Testing async crawler." in result["paragraphs"]
    assert "https://example.com/about" in result["links"]
    assert "https://example.com/image.png" in result["images"]
    assert result["metadata"]["description"] == "Test description"