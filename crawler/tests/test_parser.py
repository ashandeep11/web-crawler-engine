
from crawler.parser import parse_html


def test_parse_html_extracts_title_and_heading():
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <p>Sample paragraph</p>
        </body>
    </html>
    """

    result = parse_html(html, "https://example.com")

    assert result["title"] == "Test Page"
    assert any(
        heading["text"] == "Hello World"
        for heading in result["headings"]
    )
