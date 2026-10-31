
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class CrawlerConfig:
    max_depth: int = 2
    max_pages: int = 20
    delay: float = 1.0
    timeout: int = 10
    retries: int = 2
    user_agent: str = "StudentWebCrawler/1.0"
    output_dir: Path = PROJECT_ROOT / "output"
    logs_dir: Path = PROJECT_ROOT / "logs"

    def __post_init__(self):
        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if self.max_pages < 1:
            raise ValueError("max_pages must be >= 1")
        if self.delay < 0:
            raise ValueError("delay must be >= 0")
        if self.timeout < 1:
            raise ValueError("timeout must be >= 1")
        if self.retries < 0:
            raise ValueError("retries must be >= 0")

        self.output_dir = Path(self.output_dir)
        self.logs_dir = Path(self.logs_dir)

    @classmethod
    def from_env(cls):
        return cls(
            max_depth=int(os.getenv("CRAWLER_MAX_DEPTH", "2")),
            max_pages=int(os.getenv("CRAWLER_MAX_PAGES", "20")),
            delay=float(os.getenv("CRAWLER_DELAY", "1.0")),
            timeout=int(os.getenv("CRAWLER_TIMEOUT", "10")),
            retries=int(os.getenv("CRAWLER_RETRIES", "2")),
            user_agent=os.getenv(
                "CRAWLER_USER_AGENT",
                "StudentWebCrawler/1.0"
            ),
        )
