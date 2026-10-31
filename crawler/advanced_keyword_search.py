
"""Advanced keyword search across crawled webpages."""

import csv
import json
import re
from pathlib import Path


def get_page_text(record):
    """Extract searchable text from a crawler record."""

    parts = []

    if record.get("text"):
        parts.append(str(record["text"]))
    else:
        parts.append(str(record.get("title", "")))

        for heading in record.get("headings", []):
            if isinstance(heading, dict):
                parts.append(str(heading.get("text", "")))
            else:
                parts.append(str(heading))

        for paragraph in record.get("paragraphs", []):
            parts.append(str(paragraph))

    return " ".join(parts)


def find_snippets(text, keyword, context=60):
    """Return short text snippets around keyword matches."""

    snippets = []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)

    for match in pattern.finditer(text):
        start = max(0, match.start() - context)
        end = min(len(text), match.end() + context)

        snippet = text[start:end].strip()
        snippets.append(snippet)

        if len(snippets) >= 5:
            break

    return snippets


def search_keywords(records, keywords):
    """Search one or more keywords across crawled pages."""

    if isinstance(keywords, str):
        keywords = [keywords]

    keywords = [
        str(keyword).strip()
        for keyword in keywords
        if str(keyword).strip()
    ]

    if not keywords:
        raise ValueError("Please provide at least one keyword.")

    results = []

    for record in records:
        if not isinstance(record, dict):
            continue

        text = get_page_text(record)
        title = str(record.get("title", "Untitled"))
        url = str(record.get("url", ""))

        matched_keywords = []

        for keyword in keywords:
            count = len(
                re.findall(re.escape(keyword), text, re.IGNORECASE)
            )

            if count:
                matched_keywords.append({
                    "keyword": keyword,
                    "count": count,
                    "snippets": find_snippets(text, keyword)
                })

        if matched_keywords:
            results.append({
                "title": title,
                "url": url,
                "total_matches": sum(
                    item["count"] for item in matched_keywords
                ),
                "matched_keywords": matched_keywords
            })

    results.sort(
        key=lambda item: item["total_matches"],
        reverse=True
    )

    return {
        "keywords": keywords,
        "pages_matched": len(results),
        "total_matches": sum(
            item["total_matches"] for item in results
        ),
        "results": results
    }


def export_search_report(report, output_dir="output"):
    """Export search results into JSON and CSV."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_file = output_path / "advanced_keyword_search.json"
    csv_file = output_path / "advanced_keyword_search.csv"

    with json_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    with csv_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "title",
                "url",
                "total_matches",
                "matched_keywords"
            ]
        )

        writer.writeheader()

        for result in report.get("results", []):
            writer.writerow({
                "title": result["title"],
                "url": result["url"],
                "total_matches": result["total_matches"],
                "matched_keywords": ", ".join(
                    f'{item["keyword"]}: {item["count"]}'
                    for item in result["matched_keywords"]
                )
            })

    return json_file, csv_file
