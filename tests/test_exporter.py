
import json

from crawler.exporter import export_json


def test_export_json_creates_file(tmp_path):
    records = [
        {
            "url": "https://example.com",
            "title": "Example",
            "headings": [],
            "paragraphs": [],
            "links": [],
            "images": [],
            "metadata": {},
            "status_code": 200,
            "depth": 0,
        }
    ]

    output_file = tmp_path / "results.json"
    export_json(records, output_file)

    assert output_file.exists()

    with output_file.open(encoding="utf-8") as file:
        data = json.load(file)

    assert data[0]["title"] == "Example"
