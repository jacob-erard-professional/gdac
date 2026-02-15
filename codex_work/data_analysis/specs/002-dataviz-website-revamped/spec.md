# Feature Specification: Dataset Comparison Visualization Website

**Feature Branch**: `002-dataviz-website-revamped`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "The following needs to be implemented in the website: A dropdown should be provided at the top of the page to select which year the analysis is about There needs to be a word cloud based on the _full version of the data, specifically the hashtag_frequency and parent_company_groups There needs to be a word cloud that pulls from a csv names celebrity_freq from both the regular and full dataset There needs to be a word cloud that counts the frequency of the brand column in the raw dataset for both the full and regualr dataset There needs to be a box that shows example tweets from the text column. These should be formatted like tweets to look nice. For the _full data, it needs to come from rows that have is_about_brand set to false. There should be an arrow that lets users navigate between the total number of tweets. Ensure that no duplicate text is allowed for this card."

## Clarifications

### Session 2026-02-14

- Q: Which full-dataset analytics path convention should be used per year? → A: Use `outputs/analytics/<year>_full` alongside regular `outputs/analytics/<year>`.
- Q: Should the tweet card be available for both regular and full datasets or full only? → A: Show tweet cards for both datasets; full remains filtered by `is_about_brand=false`.
- Q: Which years should appear in the top dropdown? → A: Include only years where both regular and full datasets exist.
- Q: If `is_about_brand` is missing in full tweet data, how should filtering behave? → A: Treat missing `is_about_brand` as `false`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Year and Compare Sources (Priority: P1)

An analyst selects a year from a dropdown at the top of the page and immediately sees visualizations that compare regular and full datasets for that year.

**Why this priority**: Year selection is the entry point for all analysis and comparison behavior.

**Independent Test**: Can be tested by loading multiple year folders, changing the dropdown selection, and verifying all visualizations update to the chosen year.

**Acceptance Scenarios**:

1. **Given** multiple years exist in analytics outputs, **When** the page loads, **Then** the dropdown lists only years where both regular (`outputs/analytics/<year>`) and full (`outputs/analytics/<year>_full`) datasets exist.
2. **Given** a year is selected, **When** the selection changes, **Then** all comparison visualizations refresh using only that year’s data.

---

### User Story 2 - Review Required Word Clouds (Priority: P1)

A user views required word clouds for hashtags/parent groups (full dataset), celebrities (regular and full), and brand frequency from raw data (regular and full).

**Why this priority**: Word clouds are the core requested visual outputs.

**Independent Test**: Can be tested by loading a year with known values and confirming each required word cloud appears and uses the correct source files/columns.

**Acceptance Scenarios**:

1. **Given** full dataset analytics exist for a year, **When** the page renders, **Then** a word cloud is shown using terms derived from `hashtag_frequency` and `parent_company_groups` from the full dataset.
2. **Given** `celebrity_freq.csv` exists for regular and full datasets, **When** the page renders, **Then** a celebrity word cloud is shown for each dataset.
3. **Given** raw regular and raw full datasets exist, **When** the page renders, **Then** brand-frequency word clouds are shown for both datasets using the `brand` column.

---

### User Story 3 - Browse Example Tweets (Priority: P2)

A user browses example tweets in tweet-styled cards for both regular and full datasets, with arrow navigation, no duplicate text entries, and full-dataset filtering by `is_about_brand = false`.

**Why this priority**: Example tweets provide qualitative context and were explicitly requested.

**Independent Test**: Can be tested by loading sample data with duplicates and mixed `is_about_brand` values, then validating filtering, de-duplication, and arrow navigation behavior.

**Acceptance Scenarios**:

1. **Given** full dataset rows include `is_about_brand` values, **When** example tweets are loaded for full data, **Then** only rows with `is_about_brand = false` are used.
2. **Given** duplicated text values exist, **When** tweets are prepared for either dataset card, **Then** each displayed tweet text is unique within that card.
3. **Given** multiple unique tweets are available, **When** the user clicks navigation arrows, **Then** the card advances through the total tweet set and displays position context.

### Edge Cases

- A selected year exists in one dataset source but not the other.
- `celebrity_freq.csv` is missing for one source while present for the other.
- `brand` column is missing or blank in parts of raw data.
- `is_about_brand` column is missing from full data rows (treated as `false`).
- Tweet text contains repeated whitespace/casing differences that could hide duplicates.

## Requirements *(mandatory)*

### Constitutional Alignment *(mandatory)*

- Feature MUST read from year-scoped repository outputs and MUST NOT mutate source data files.
- Feature MUST preserve deterministic rendering for unchanged files and year selection.
- Feature MUST keep regular and full dataset scopes separate and clearly labeled.
- Feature MUST include documentation updates describing required files and supported year selection behavior.

### Functional Requirements

- **FR-001**: System MUST provide a top-level year dropdown populated only from years where both `outputs/analytics/<year>` (regular) and `outputs/analytics/<year>_full` (full) are present.
- **FR-002**: System MUST update all visualizations to the currently selected year.
- **FR-003**: System MUST render a full-dataset word cloud derived from full-data `hashtag_frequency` and `parent_company_groups` sources.
- **FR-004**: System MUST render celebrity word clouds sourced from `celebrity_freq.csv` for both regular and full datasets.
- **FR-005**: System MUST render brand-frequency word clouds for both regular and full datasets using the raw `brand` column counts.
- **FR-006**: System MUST display example tweet cards styled as tweet presentations for both regular and full datasets.
- **FR-007**: System MUST source full-dataset tweet-card entries only from rows where `is_about_brand` is `false`; if the field is missing, rows MUST be treated as `is_about_brand=false`.
- **FR-008**: System MUST enforce tweet text uniqueness in the card data set so no duplicate text is displayed.
- **FR-009**: System MUST provide arrow navigation through the total tweet-card entry set and show current position relative to total.
- **FR-010**: System MUST show clear, non-blocking empty/error states for missing files, missing columns, or unavailable data.

### Key Entities *(include if feature involves data)*

- **YearOption**: A selectable year value with availability status for required data artifacts.
- **DatasetScope**: One of `regular` or `full`, used to resolve source files and labels.
- **WordCloudDataset**: A normalized term-frequency collection generated from a source artifact.
- **TweetCardEntry**: A unique text entry prepared for display in the tweet-style card with dataset/year metadata.
- **TweetCardNavigatorState**: Current index, total count, and boundary status for arrow navigation.

### Assumptions

- Regular and full dataset directory conventions are stable and discoverable per selected year.
- `celebrity_freq.csv` has enough information to derive term frequencies.
- Raw datasets contain a `text` column for tweet-card rendering.

### Dependencies

- Availability of year-scoped artifacts under `outputs/analytics/<year>` for regular and `outputs/analytics/<year>_full` for full datasets.
- Availability of raw dataset files for regular and full sources with the `brand` and `text` columns.
- Full tweet-card filtering assumes missing `is_about_brand` values are interpreted as `false`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a selected year with complete inputs, the page displays all required word clouds and the tweet card within 10 seconds.
- **SC-002**: In acceptance testing across available years, year dropdown options match discovered valid year folders with 100% accuracy.
- **SC-003**: In validation runs with injected duplicates, tweet card output contains 0 duplicate `text` values.
- **SC-004**: In user testing, at least 95% of participants can switch years and identify at least one difference between regular and full views without guidance.
