import argparse
import csv
from pathlib import Path

from src.cli.classify_brand_mentions import run


def fake_client(api_key, model, messages, timeout=30, response_format=None, plugins=None):
    return {
        "choices": [
            {
                "message": {
                    "content": '{"results":[{"id":1,"is_about_brand":true,"confidence":0.77,"rationale":"Brand mention"}]}'
                }
            }
        ]
    }


def write_input(path: Path):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "brand"])
        writer.writeheader()
        writer.writerow({"text": "Angel Soft rocks", "brand": "Angel Soft"})


def test_cli_batch_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "out.csv"
    write_input(input_path)

    args = argparse.Namespace(
        input=str(input_path),
        output=str(output_path),
        format="csv",
        model="openrouter/test",
        batch_size=100,
        progress_every=1,
        start_row=1,
    )
    run(args, client=fake_client)

    assert output_path.exists()
    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8")))
    assert rows[0]["is_about_brand"] == "True"
    assert rows[0]["rationale"] == "Brand mention"


def test_cli_batch_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "out.jsonl"
    write_input(input_path)

    args = argparse.Namespace(
        input=str(input_path),
        output=str(output_path),
        format="jsonl",
        model="openrouter/test",
        batch_size=100,
        progress_every=1,
        start_row=1,
    )
    run(args, client=fake_client)

    assert output_path.exists()
    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert "\"is_about_brand\": true" in lines[0]


def test_cli_batch_start_row(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "out.csv"
    with input_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "brand"])
        writer.writeheader()
        writer.writerow({"text": "row1", "brand": "Brand A"})
        writer.writerow({"text": "row2", "brand": "Brand B"})
        writer.writerow({"text": "row3", "brand": "Brand C"})

    args = argparse.Namespace(
        input=str(input_path),
        output=str(output_path),
        format="csv",
        model="openrouter/test",
        batch_size=100,
        progress_every=1,
        start_row=3,
    )
    run(args, client=fake_client)

    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["text"] == "row3"
