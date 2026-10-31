
from crawler.utils import normalize_url, same_host


def test_normalize_url_removes_fragment():
    assert normalize_url(
        "https://example.com/page#section"
    ) == "https://example.com/page"


def test_same_host_returns_true_for_same_domain():
    assert same_host(
        "https://example.com/page",
        "https://example.com/about",
    )
