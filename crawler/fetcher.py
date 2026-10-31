
"""HTTP fetching and link checking layer."""

import logging
import time
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests


class PageFetcher:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": config.user_agent
        })

        self.robots_cache = {}
        self.last_request_time = {}

    def _origin(self, url):
        parts = urlsplit(url)
        return urlunsplit((
            parts.scheme,
            parts.netloc,
            "",
            "",
            ""
        ))

    def allowed_by_robots(self, url):
        origin = self._origin(url)

        if origin not in self.robots_cache:
            robots_url = origin + "/robots.txt"

            try:
                response = self.session.get(
                    robots_url,
                    timeout=self.config.timeout,
                    allow_redirects=False
                )

                if response.status_code in (404, 410):
                    self.robots_cache[origin] = True

                elif response.status_code == 200:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse(response.text.splitlines())
                    self.robots_cache[origin] = parser

                else:
                    self.robots_cache[origin] = False

            except requests.RequestException as error:
                logging.warning(
                    "Could not read robots.txt for %s: %s",
                    origin,
                    error
                )
                self.robots_cache[origin] = False

        rules = self.robots_cache[origin]

        if rules is True:
            return True

        if rules is False:
            return False

        return rules.can_fetch(self.config.user_agent, url)

    def _wait_for_host(self, host):
        previous = self.last_request_time.get(host)

        if previous is not None:
            elapsed = time.monotonic() - previous
            wait = self.config.delay - elapsed

            if wait > 0:
                time.sleep(wait)

        self.last_request_time[host] = time.monotonic()

    def fetch(self, url):
        host = urlsplit(url).netloc

        for attempt in range(self.config.retries + 1):
            self._wait_for_host(host)

            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                    allow_redirects=True
                )

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                if "text/html" not in content_type:
                    logging.info("Skipping non-HTML: %s", url)
                    return None

                return (
                    response.url,
                    response.text,
                    response.status_code
                )

            except requests.RequestException as error:
                logging.warning(
                    "Fetch attempt %d failed for %s: %s",
                    attempt + 1,
                    url,
                    error
                )

                if attempt < self.config.retries:
                    time.sleep(min(2 ** attempt, 8))

        return None

    def check_link(self, url):
        """Check a URL and classify its HTTP response."""

        if not self.allowed_by_robots(url):
            return {
                "url": url,
                "status_code": None,
                "status": "Robots blocked",
                "final_url": url
            }

        host = urlsplit(url).netloc

        for attempt in range(self.config.retries + 1):
            self._wait_for_host(host)

            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                    allow_redirects=True,
                    stream=True
                )

                status_code = response.status_code
                final_url = response.url
                response.close()

                if 200 <= status_code < 300:
                    status = "Working"
                elif 300 <= status_code < 400:
                    status = "Redirect"
                else:
                    status = "Broken"

                return {
                    "url": url,
                    "status_code": status_code,
                    "status": status,
                    "final_url": final_url
                }

            except requests.RequestException as error:
                logging.warning(
                    "Link check attempt %d failed for %s: %s",
                    attempt + 1,
                    url,
                    error
                )

                if attempt == self.config.retries:
                    return {
                        "url": url,
                        "status_code": None,
                        "status": "Request Error",
                        "final_url": url
                    }

                time.sleep(min(2 ** attempt, 8))

    def close(self):
        self.session.close()
