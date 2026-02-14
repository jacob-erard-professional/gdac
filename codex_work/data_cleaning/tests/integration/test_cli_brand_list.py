import argparse
import csv

from src.cli.classify_brand_list import run


def fake_client(api_key, model, messages, timeout=30, response_format=None, plugins=None):
    return {
        "choices": [
            {
                "message": {
                    "content": '{"results":[{"id":1,"category":"listed_brand","assigned_brand":"Nike","confidence":0.8,"rationale":"Brand match"},{"id":2,"category":"new_brand","suggested_brand":"Patanjali","confidence":0.6,"rationale":"Not in list"}]}'
                }
            }
        ]
    }


def _write_tweets(path):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "is_about_brand", "id"])
        writer.writeheader()
        writer.writerow({"text": "already labeled", "is_about_brand": "true", "id": "1"})
        writer.writerow({"text": "Nike launch", "is_about_brand": "false", "id": "2"})
        writer.writerow({"text": "Patanjali promo", "is_about_brand": "false", "id": "3"})


def _write_brands(path):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["brand"])
        writer.writeheader()
        writer.writerow({"brand": "Nike"})
        writer.writerow({"brand": "Adidas"})


def test_cli_brand_list_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    in_csv = tmp_path / "tweets.csv"
    brands_csv = tmp_path / "brands.csv"
    out_csv = tmp_path / "out.csv"
    _write_tweets(in_csv)
    _write_brands(brands_csv)

    args = argparse.Namespace(
        input=str(in_csv),
        brand_list=str(brands_csv),
        output=str(out_csv),
        format="csv",
        model="openrouter/test",
        batch_size=100,
        progress_every=1,
        start_row=1,
    )
    run(args, client=fake_client)

    rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8")))
    assert len(rows) == 3
    assert rows[0]["category"] == "skipped"
    assert rows[0]["confidence"] == "0.0"
    assert rows[1]["category"] == "listed_brand"
    assert rows[1]["assigned_brand"] == "Nike"
    assert rows[2]["category"] == "new_brand"
    assert rows[2]["suggested_brand"] == "Patanjali"


def test_cli_brand_list_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    in_csv = tmp_path / "tweets.csv"
    brands_csv = tmp_path / "brands.csv"
    out_jsonl = tmp_path / "out.jsonl"
    _write_tweets(in_csv)
    _write_brands(brands_csv)

    args = argparse.Namespace(
        input=str(in_csv),
        brand_list=str(brands_csv),
        output=str(out_jsonl),
        format="jsonl",
        model="openrouter/test",
        batch_size=100,
        progress_every=1,
        start_row=1,
    )
    run(args, client=fake_client)

    lines = out_jsonl.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    assert '"category": "skipped"' in lines[0]


def test_cli_brand_list_parity_flags(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    in_csv = tmp_path / "tweets.csv"
    brands_csv = tmp_path / "brands.csv"
    out_csv = tmp_path / "out.csv"
    _write_tweets(in_csv)
    _write_brands(brands_csv)

    args = argparse.Namespace(
        input=str(in_csv),
        brand_list=str(brands_csv),
        output=str(out_csv),
        format="csv",
        model="openrouter/test",
        batch_size=2,
        progress_every=1,
        start_row=1,
    )
    run(args, client=fake_client)
    assert out_csv.exists()


def test_cli_brand_list_start_row(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "testkey")
    in_csv = tmp_path / "tweets.csv"
    brands_csv = tmp_path / "brands.csv"
    out_csv = tmp_path / "out.csv"
    with in_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "is_about_brand", "id"])
        writer.writeheader()
        writer.writerow({"text": "row1", "is_about_brand": "false", "id": "1"})
        writer.writerow({"text": "row2", "is_about_brand": "false", "id": "2"})
        writer.writerow({"text": "row3", "is_about_brand": "false", "id": "3"})
    _write_brands(brands_csv)

    args = argparse.Namespace(
        input=str(in_csv),
        brand_list=str(brands_csv),
        output=str(out_csv),
        format="csv",
        model="openrouter/test",
        batch_size=100,
        progress_every=1,
        start_row=3,
    )
    run(args, client=fake_client)

    rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["text"] == "row3"
