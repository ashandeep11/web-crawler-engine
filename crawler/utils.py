"""Shared utilities."""

from urllib.parse import urljoin, urlsplit, urlunsplit


def normalize_url(url):
    if not isinstance(url, str):
        return None

    url = url.strip()
    if not url:
        return None

    try:
        parts = urlsplit(url)

        if parts.scheme.lower() not in ("http", "https"):
            return None

        if not parts.hostname or parts.username or parts.password:
            return None

        # Reject malformed ports and invalid hostnames.
        _ = parts.port
        hostname = parts.hostname.encode("idna").decode("ascii").lower()

        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"

        if parts.port:
            default_port = (
                parts.scheme.lower() == "http" and parts.port == 80
            ) or (
                parts.scheme.lower() == "https" and parts.port == 443
            )

            if not default_port:
                hostname = f"{hostname}:{parts.port}"

        path = parts.path or "/"

        return urlunsplit((
            parts.scheme.lower(),
            hostname,
            path,
            parts.query,
            ""  # Fragments do not identify separate pages.
        ))

    except (ValueError, UnicodeError):
        return None


def resolve_url(base_url, href):
    if not href:
        return None

    try:
        return normalize_url(urljoin(base_url, href.strip()))
    except (ValueError, AttributeError):
        return None


def same_host(url_a, url_b):
    try:
        a = urlsplit(url_a)
        b = urlsplit(url_b)

        return (
            a.hostname is not None
            and a.hostname.lower() == b.hostname.lower()
            and a.port == b.port
        )
    except ValueError:
        return False
