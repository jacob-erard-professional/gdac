# Data Model

## Entities

### TweetRecord

**Purpose**: Input tweet row with assigned brand and supporting context.

**Fields**:
- `text` (string, required): The tweet text. Primary signal.
- `brand` (string, required): Assigned brand to validate against.
- `metadata` (object, optional): Key/value map of all other CSV columns.
- `entities.annotations` (array, optional): Parsed list of annotations if present.
- `entities.mentions` (array, optional): Parsed list of mentions if present.
- `entities.hashtags` (array, optional): Parsed list of hashtags if present.
- `entities.cashtags` (array, optional): Parsed list of cashtags if present.
- `entities.urls` (array, optional): Parsed list of URLs if present.
- `referenced_tweets` (array, optional): Parsed list of referenced tweets if present.
- `public_metrics.*` (integers, optional): Engagement counts; missing treated as `0`.

**Validation rules**:
- `text` must be non-empty after trimming; otherwise mark as missing.
- `brand` must be non-empty after trimming; otherwise mark as missing.
- JSON-encoded columns must parse to arrays when present; malformed data becomes empty arrays.

### ClassificationResult

**Purpose**: Output decision for a TweetRecord.

**Fields**:
- `is_about_brand` (boolean, required): True if tweet is about the assigned brand.
- `confidence` (float, required): 0.0 to 1.0 confidence score.
- `rationale` (string, required): Brief explanation for auditing.
- `prompt_version` (string, optional): Version tag for prompt template.

**Validation rules**:
- `confidence` must be between 0.0 and 1.0.
- `rationale` must be non-empty.

## Relationships

- `TweetRecord` 1:1 `ClassificationResult`

## State Transitions

- None (stateless batch processing)
