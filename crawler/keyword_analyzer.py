
"""Keyword frequency analysis for crawled webpages."""

import csv
import json
import re
from collections import Counter
from pathlib import Path


STOP_WORDS = {
    "the", "and", "for", "are", "but", "not", "you",
    "your", "with", "this", "that", "from", "have",
    "has", "was", "were", "will", "would", "could",
    "should", "can", "our", "their", "they", "them",
    "then", "than", "there", "here", "what", "when",
    "where", "which", "who", "how", "why", "all",
    "any", "some", "more", "most", "such", "into",
    "about", "also", "just", "only", "other", "over",
    "under", "after", "before", "between", "while",
    "been", "being", "its", "it's", "you", "your",
    "www", "http", "https", "com"
}


def extract_page_text(record):
    """Get readable text from a crawler record."""

    parts = []

    if record.get("text"):
        parts.append(str(record["text"]))
    else:
        parts.append(str(record.get("title", "")))

        for heading in record.get("headings", []):
            if isinstance(heading, dict):
                parts.append(str(heading.get("text", "")))

        for paragraph in record.get("paragraphs", []):
            parts.append(str(paragraph))

    return " ".join(parts)


def tokenize_text(text):
    """Convert text into clean lowercase words."""

    words = re.findall(r"[a-zA-Z][a-zA-Z']+", text.lower())

    return [
        word for word in words
        if len(word) >= 3 and word not in STOP_WORDS
    ]


def analyze_keyword_frequency(records, top_n=20):
    """Analyze keyword frequency across crawled pages."""

    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    counter = Counter()
    pages_analyzed = 0
    total_words = 0

    for record in records:
        if not isinstance(record, dict):
            continue

        page_text = extract_page_text(record)

        if not page_text.strip():
            continue

        words = tokenize_text(page_text)

        if words:
            counter.update(words)
            total_words += len(words)
            pages_analyzed += 1

    top_keywords = [
        {
            "keyword": word,
            "frequency": count,
            "percentage": round(
                (count / total_words) * 100, 2
            ) if total_words else 0
        }
        for word, count in counter.most_common(top_n)
    ]

    return {
        "pages_analyzed": pages_analyzed,
        "total_words": total_words,
        "unique_keywords": len(counter),
        "top_keywords": top_keywords
    }


def export_keyword_report(report, output_dir="output"):
    """Export keyword analysis into JSON and CSV."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_file = output_path / "keyword_frequency.json"
    csv_file = output_path / "keyword_frequency.csv"

    with json_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "keyword",
                "frequency",
                "percentage"
            ]
        )

        writer.writeheader()
        writer.writerows(report.get("top_keywords", []))

    return json_file, csv_file
