# gdac Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-02

## Active Technologies
- JavaScript (ES2022) + React (existing site app) + Existing site stack (React + charting library already in repository), CSV/JSON parsing in browser runtime (002-dataviz-website-revamped)
- Read-only files from repository directories: `outputs/analytics/<year>/`, `outputs/analytics/<year>_full/` (or equivalent full-dataset path), raw dataset CSVs (002-dataviz-website-revamped)
- JavaScript (ES2022) + React + Existing `site/` stack, chart rendering library in current website, browser-side JSON/CSV parsing utilities (002-dataviz-website-revamped)
- Read-only repository files from `outputs/analytics/<year>` and `outputs/analytics/<year>_full`, plus raw CSV sources for brand/text extraction (002-dataviz-website-revamped)

- Python 3.11 + pandas (chunked IO), typer, pydantic, vaderSentiment, pyarrow (001-build-superbowl-analytics-pipeline)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes
- 002-dataviz-website-revamped: Added JavaScript (ES2022) + React + Existing `site/` stack, chart rendering library in current website, browser-side JSON/CSV parsing utilities
- 002-dataviz-website-revamped: Added JavaScript (ES2022) + React (existing site app) + Existing site stack (React + charting library already in repository), CSV/JSON parsing in browser runtime

- 001-build-superbowl-analytics-pipeline: Added Python 3.11 + pandas (chunked IO), typer, pydantic, vaderSentiment, pyarrow

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
