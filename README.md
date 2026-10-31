
# Web Crawler & Data Extraction Engine

A modular Python application that crawls permitted webpages,
extracts structured content, and exports data to JSON and CSV.

## Features

- One or more seed URLs
- HTML parsing using BeautifulSoup and lxml
- Extraction of titles, headings, paragraphs, links, images and metadata
- Same-host internal link crawling
- Configurable depth and page limits
- Duplicate URL prevention
- robots.txt checks and configurable request delays
- Request timeouts and retries
- JSON and CSV exports
- Keyword search across collected content
- Crawl statistics and logging
- Automated tests using pytest

## Requirements

- Python 3.11 or newer
- pip
- VS Code (recommended)

## Setup on macOS

Create a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    python -m pip install -r requirements.txt

## Run

    python main.py https://example.com --depth 1 --max-pages 5

Search extracted content:

    python main.py https://example.com --keyword example

Show available options:

    python main.py --help

## Configuration

Copy `.env.example` to `.env` if you want to customize
the crawler settings.

Available settings include depth, maximum pages, delay,
timeout, retry count and User-Agent.

## Output

- `output/results.json`
- `output/results.csv`
- `output/stats.json`
- `logs/crawler.log`

## Tests

    python -m pytest crawler/tests -v

## Responsible Crawling

Crawl only pages you are authorized to access. Respect
robots.txt, website terms, rate limits and server resources.
This crawler does not bypass authentication or anti-bot controls.

## Limitations

This version extracts HTML available in the HTTP response.
It does not execute JavaScript or render dynamic webpages.
Crawling is limited to the same host and configured depth
and page limits.

## Future Improvements

- SQLite database storage
- Asynchronous crawling
- Sitemap generation
- Keyword frequency analysis
- Docker support
- GitHub Actions continuous integration
