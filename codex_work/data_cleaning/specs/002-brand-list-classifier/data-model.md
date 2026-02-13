# Data Model

## Entities

### BrandCandidateSet

**Purpose**: Canonical set of candidate brands used for classification.

**Fields**:
- `brand` (string, required): one value per row in brand-list CSV.

**Validation rules**:
- source file must contain exactly one header named `brand`.
- blank brand values are rejected.
- matching is case-insensitive; output preserves source casing.

### TweetRow

**Purpose**: Input tweet row from primary CSV.

**Fields**:
- `text` (string, required for candidate classification)
- `is_about_brand` (string/bool, required for skip decision)
- `metadata` (object, optional): all other row columns.

**Validation rules**:
- true-like `is_about_brand` rows bypass model classification.
- missing/empty text on candidate rows yields `no_brand` with rationale.

### BrandListClassificationResult

**Purpose**: Classification outcome appended to output rows.

**Fields**:
- `category` (enum, required): `listed_brand | new_brand | no_brand | skipped`
- `assigned_brand` (string, optional)
- `suggested_brand` (string, optional)
- `confidence` (float 0.0-1.0, required)
- `rationale` (string, required)

**Validation rules**:
- `listed_brand`: `assigned_brand` must be in BrandCandidateSet, no suggestion.
- `new_brand`: `suggested_brand` required, `assigned_brand` empty.
- `no_brand`: both brand fields empty.
- `skipped`: both brand fields empty, `confidence=0`, rationale exactly
  `Skipped: already is_about_brand=true`.

## Relationships

- `BrandCandidateSet` 1:N `TweetRow`
- `TweetRow` 1:1 `BrandListClassificationResult`

## State Transitions

- Input row -> skip check (`is_about_brand`) ->
  - skip path: deterministic skipped result
  - candidate path: OpenRouter classification -> validated category result
