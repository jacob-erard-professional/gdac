"""Utility script for recover grouping from partial operations."""

import json
from pathlib import Path

import typer

app = typer.Typer(add_completion=False)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_parse_failure_blocks(path: Path | None) -> int:
    if not path or not path.exists():
        return 0
    content = path.read_text(encoding="utf-8")
    return content.count("\n\n---\n\n")


def _read_partial_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _recover_brand(
    *,
    source_file: Path,
    partial_file: Path,
    output_file: Path,
    parse_failures_file: Path | None,
) -> None:
    payload = _load_json(source_file)
    year = str(payload.get("year", "unknown"))
    raw_hashtags = payload.get("hashtags", [])
    if isinstance(raw_hashtags, dict):
        raw_hashtags = [{"hashtag": tag, "count": count} for tag, count in raw_hashtags.items()]

    hashtags = []
    for item in raw_hashtags:
        tag = str(item.get("hashtag", "")).strip().lower()
        if not tag:
            continue
        count = int(item.get("count", 0))
        hashtags.append({"hashtag": tag, "count": max(count, 0)})

    partial_rows = _read_partial_jsonl(partial_file)

    hashtag_to_brand: dict[str, str] = {}
    alias_map: dict[str, str] | None = None

    for row in partial_rows:
        phase = str(row.get("phase", ""))
        if phase.startswith("map_chunk"):
            for mapping in row.get("mappings", []):
                tag = str(mapping.get("hashtag", "")).strip().lower()
                brand = str(mapping.get("brand", "")).strip().lower() or tag
                if tag:
                    hashtag_to_brand[tag] = brand
        elif phase == "normalize_labels":
            alias_map = {}
            for alias in row.get("aliases", []):
                label = str(alias.get("label", "")).strip().lower()
                canonical = str(alias.get("canonical", "")).strip().lower() or label
                if label:
                    alias_map[label] = canonical

    for item in hashtags:
        hashtag_to_brand.setdefault(item["hashtag"], item["hashtag"])
    if alias_map is None:
        alias_map = {label: label for label in hashtag_to_brand.values()}

    grouped: dict[str, list[dict[str, int | str]]] = {}
    for item in hashtags:
        label = hashtag_to_brand.get(item["hashtag"], item["hashtag"])
        brand = alias_map.get(label, label)
        grouped.setdefault(brand, []).append({"hashtag": item["hashtag"], "count": item["count"]})

    brands = []
    for brand, items in grouped.items():
        ordered_items = sorted(items, key=lambda x: (-int(x["count"]), str(x["hashtag"])))
        total = sum(int(i["count"]) for i in ordered_items)
        brands.append({"brand": brand, "total_count": total, "hashtags": ordered_items})
    brands.sort(key=lambda x: (-int(x["total_count"]), str(x["brand"])))

    result = {
        "year": year,
        "model": "recovered-from-partial",
        "recovered_from_partial": True,
        "source_file": str(source_file),
        "partial_file": str(partial_file),
        "parse_failures_file": str(parse_failures_file) if parse_failures_file else "",
        "parse_failure_blocks": _count_parse_failure_blocks(parse_failures_file),
        "brands": brands,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")


def _recover_parent(
    *,
    source_file: Path,
    partial_file: Path,
    output_file: Path,
    parse_failures_file: Path | None,
) -> None:
    payload = _load_json(source_file)
    year = str(payload.get("year", "unknown"))
    raw_groups = payload.get("brands", [])

    groups = []
    for item in raw_groups:
        brand = str(item.get("brand", "")).strip().lower()
        if not brand:
            continue
        total_count = int(item.get("total_count", 0))
        hashtags = item.get("hashtags", [])
        if not isinstance(hashtags, list):
            hashtags = []
        groups.append({"brand": brand, "total_count": max(total_count, 0), "hashtags": hashtags})

    partial_rows = _read_partial_jsonl(partial_file)

    brand_to_parent: dict[str, str] = {}
    alias_map: dict[str, str] | None = None

    for row in partial_rows:
        phase = str(row.get("phase", ""))
        if phase.startswith("map_chunk"):
            for mapping in row.get("mappings", []):
                brand = str(mapping.get("brand", "")).strip().lower()
                parent = str(mapping.get("parent_company", "")).strip().lower() or brand
                if brand:
                    brand_to_parent[brand] = parent
        elif phase == "normalize_labels":
            alias_map = {}
            for alias in row.get("aliases", []):
                label = str(alias.get("label", "")).strip().lower()
                canonical = str(alias.get("canonical", "")).strip().lower() or label
                if label:
                    alias_map[label] = canonical

    for item in groups:
        brand_to_parent.setdefault(item["brand"], item["brand"])
    if alias_map is None:
        alias_map = {label: label for label in brand_to_parent.values()}

    grouped: dict[str, list[dict]] = {}
    for group in groups:
        raw_parent = brand_to_parent.get(group["brand"], group["brand"])
        parent = alias_map.get(raw_parent, raw_parent)
        grouped.setdefault(parent, []).append(group)

    parent_companies = []
    for parent, children in grouped.items():
        ordered_children = sorted(children, key=lambda x: (-int(x["total_count"]), str(x["brand"])))
        total = sum(int(c["total_count"]) for c in ordered_children)
        parent_companies.append({"parent_company": parent, "total_count": total, "brands": ordered_children})
    parent_companies.sort(key=lambda x: (-int(x["total_count"]), str(x["parent_company"])))

    result = {
        "year": year,
        "model": "recovered-from-partial",
        "recovered_from_partial": True,
        "source_file": str(source_file),
        "partial_file": str(partial_file),
        "parse_failures_file": str(parse_failures_file) if parse_failures_file else "",
        "parse_failure_blocks": _count_parse_failure_blocks(parse_failures_file),
        "parent_companies": parent_companies,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")


@app.command()
def main(
    kind: str = typer.Option(..., "--kind", help="brand or parent"),
    source_file: Path = typer.Option(..., "--source-file", help="hashtags_frequency.json for brand, brand_groups.json for parent"),
    partial_file: Path = typer.Option(..., "--partial-file", help="Partial JSONL file from interrupted run"),
    output_file: Path = typer.Option(None, "--output-file", help="Recovered output file path"),
    parse_failures_file: Path = typer.Option(None, "--parse-failures-file", help="Optional parse failures text file"),
) -> None:
    normalized_kind = kind.strip().lower()
    if normalized_kind not in {"brand", "parent"}:
        raise typer.BadParameter("--kind must be either 'brand' or 'parent'")

    if not source_file.exists():
        raise typer.BadParameter(f"Source file not found: {source_file}")
    if not partial_file.exists():
        raise typer.BadParameter(f"Partial file not found: {partial_file}")

    if output_file is None:
        default_name = "brand_groups.json" if normalized_kind == "brand" else "parent_company_groups.json"
        output_file = source_file.parent / default_name

    if normalized_kind == "brand":
        _recover_brand(
            source_file=source_file,
            partial_file=partial_file,
            output_file=output_file,
            parse_failures_file=parse_failures_file,
        )
    else:
        _recover_parent(
            source_file=source_file,
            partial_file=partial_file,
            output_file=output_file,
            parse_failures_file=parse_failures_file,
        )

    typer.echo(f"Recovered {normalized_kind} output written to {output_file}")


if __name__ == "__main__":
    app()
