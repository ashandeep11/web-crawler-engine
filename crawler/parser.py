
"""HTML parsing and link extraction."""

from bs4 import BeautifulSoup

from crawler.utils import resolve_url


def parse_html(html, page_url):
    """Parse HTML and extract webpage content."""

    soup = BeautifulSoup(html, "lxml")

    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title
        else ""
    )

    headings = [
        {
            "tag": tag.name,
            "text": tag.get_text(" ", strip=True)
        }
        for tag in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        )
        if tag.get_text(" ", strip=True)
    ]

    # Extract canonical URL
    canonical_tag = soup.find(
        "link",
        rel=lambda value: (
            value and "canonical" in [
                item.lower() for item in (
                    value if isinstance(value, list)
                    else value.split()
                )
            ]
        )
    )

    canonical_url = ""

    if canonical_tag and canonical_tag.get("href"):
        canonical_url = resolve_url(
            page_url,
            canonical_tag.get("href")
        ) or ""

    # Remove non-readable elements
    for element in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "template",
        "iframe"
    ]):
        element.decompose()

    # Extract paragraphs
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in soup.find_all("p")
        if p.get_text(" ", strip=True)
    ]

    # Extract all readable page text for keyword analysis
    text = soup.get_text(" ", strip=True)

    # Extract links
    links = []

    for tag in soup.find_all("a", href=True):
        link_url = resolve_url(page_url, tag.get("href"))

        if link_url:
            links.append({
                "text": tag.get_text(" ", strip=True),
                "url": link_url
            })

    # Extract images
    images = []

    for tag in soup.find_all("img", src=True):
        image_url = resolve_url(page_url, tag.get("src"))

        if image_url:
            images.append({
                "alt": tag.get("alt", ""),
                "url": image_url
            })

    # Extract metadata
    metadata = {}

    for tag in soup.find_all("meta"):
        key = tag.get("name") or tag.get("property")
        value = tag.get("content")

        if key and value:
            metadata[key.lower()] = value

    return {
        "url": page_url,
        "title": title,
        "headings": headings,
        "paragraphs": paragraphs,
        "text": text,
        "links": links,
        "images": images,
        "metadata": metadata,
        "canonical": canonical_url
    }
