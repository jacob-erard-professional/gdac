# Data Model: Dataset Comparison Visualization Website

## Entity: YearOption

- **Description**: A selectable year in the top dropdown.
- **Fields**:
  - `year` (string, required): 4-digit year.
  - `regular_path` (string, required): resolved path to `outputs/analytics/<year>`.
  - `full_path` (string, required): resolved path to `outputs/analytics/<year>_full`.
- **Validation Rules**:
  - `year` must match `^[0-9]{4}$`.
  - Year is valid only if both regular and full paths exist.

## Entity: DatasetScope

- **Description**: Comparison side label.
- **Fields**:
  - `scope` (enum, required): `regular | full`.
  - `year` (string, required).
  - `status` (enum, required): `loaded | missing | partial`.

## Entity: WordCloudTerm

- **Description**: Normalized term-count row for cloud rendering.
- **Fields**:
  - `term` (string, required).
  - `count` (integer, required).
  - `scope` (enum, required): `regular | full`.
  - `cloud_type` (enum, required): `full_hashtag_parent | celebrity | raw_brand`.
  - `year` (string, required).
- **Validation Rules**:
  - `term` must be non-empty after trim.
  - `count` must be >= 1.
  - `cloud_type=full_hashtag_parent` requires `scope=full`.

## Entity: TweetCardEntry

- **Description**: A display-ready tweet item for one card.
- **Fields**:
  - `tweet_id` (string, optional).
  - `text` (string, required).
  - `normalized_text_key` (string, required).
  - `scope` (enum, required): `regular | full`.
  - `year` (string, required).
  - `is_about_brand` (boolean, optional).
- **Validation Rules**:
  - `text` must be non-empty.
  - `normalized_text_key` must be unique within `(year, scope)` card entries.
  - For `scope=full`: include entry only when `is_about_brand=false`; if field missing, treat as `false`.

## Entity: TweetCardNavigatorState

- **Description**: Arrow-navigation state for one card.
- **Fields**:
  - `scope` (enum, required): `regular | full`.
  - `current_index` (integer, required).
  - `total_count` (integer, required).
  - `has_previous` (boolean, required).
  - `has_next` (boolean, required).
- **Validation Rules**:
  - `total_count >= 0`.
  - If `total_count=0`, then `current_index=0` and both arrows disabled.
  - If `total_count>0`, then `0 <= current_index < total_count`.

## Relationships

- One `YearOption` has two `DatasetScope` rows (`regular`, `full`).
- One `DatasetScope` has many `WordCloudTerm` rows.
- One `DatasetScope` has many `TweetCardEntry` rows.
- One `DatasetScope` has one `TweetCardNavigatorState` at runtime.

## State Transitions

### TweetCardNavigatorState

- `initialize`: set from filtered, deduplicated entries; start at index 0.
- `next`: advance index by 1 only when `has_next=true`.
- `previous`: decrement index by 1 only when `has_previous=true`.
- `year_change`: reset both scope navigator states from newly loaded entries.
