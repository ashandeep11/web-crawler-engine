# Architecture


# Architecture Documentation

## Overview

The application follows a modular architecture. Each module
has a separate responsibility.

## Components

- `main.py`: CLI arguments, orchestration and summary display.
- `crawler/config.py`: Environment settings and validation.
- `crawler/utils.py`: URL normalization and same-host checks.
- `crawler/fetcher.py`: HTTP requests, robots rules, delays and retries.
- `crawler/parser.py`: HTML content extraction.
- `crawler/engine.py`: Crawl queue, depth control and duplicate prevention.
- `crawler/exporter.py`: JSON, CSV and statistics exports.
- `crawler/tests/`: Automated unit tests.

## Data Flow

1. The user provides one or more seed URLs.
2. The crawler validates and queues URLs.
3. Robots rules are checked before downloading.
4. The fetcher downloads permitted HTML pages.
5. The parser extracts structured content.
6. Internal links are queued within the configured depth.
7. The exporter writes JSON, CSV and statistics files.
8. Logs record crawl activity and failures.

## Error Handling

HTTP failures, timeouts and connection errors are logged.
Temporary request failures are retried up to the configured
retry count. Pages that cannot be fetched are skipped.

## Safety and Resource Limits

The crawler uses configurable page limits, crawl depth,
timeouts and request delays. It avoids crawling links outside
the seed page's host and does not bypass access controls.
