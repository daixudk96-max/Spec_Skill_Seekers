# transcript-ingestion

## MODIFIED Requirements

### Requirement: Structured Data Extraction
ContentSynthesizer MUST be able to extract readable text content from multiple `source_config` structures including both string-based content fields and array-based lessons structures.

#### Scenario: Extract from lessons array
- **Given** source_config with lessons.lessons as array of lesson objects with summary_full/summary fields
- **When** `_get_source_text()` is called
- **Then** it returns concatenated readable text from all lessons
- **And** it does NOT return JSON serialization.

#### Scenario: Extract from segmented_summary segments
- **Given** source_config.lessons.segments as array with summary_full fields
- **When** `_get_source_text()` is called
- **Then** it extracts and concatenates segment summaries
- **And** it includes key_points as bullet list content.

#### Scenario: Fallback to JSON only when no extractable content
- **Given** source_config with unrecognized structure and no lessons/transcript/content fields
- **When** `_get_source_text()` is called
- **Then** it returns JSON serialization as last resort fallback.

