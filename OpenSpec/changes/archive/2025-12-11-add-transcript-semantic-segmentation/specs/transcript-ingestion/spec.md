# transcript-ingestion Specification

## Purpose

扩展 transcript 处理能力，支持语义分段预处理和结构化总结。

---

## ADDED Requirements

### Requirement: Semantic Segmentation Support

The system MUST support semantic segmentation of transcript content based on marker words and topic boundaries, producing structured segment data with summaries.

#### Scenario: Process transcript with semantic markers
- **Given** a cleaned transcript text containing marker words ('好', '下一个', '第一个', etc.)
- **When** the AI assistant executes the segmented summary workflow step
- **Then** the output `segmented_summary.json` MUST contain:
  - Segments divided at semantic marker boundaries
  - Timestamp ranges preserved per segment
  - Full and brief summaries for each segment
  - Reasons explaining each segmentation decision

#### Scenario: Process transcript without clear markers
- **Given** a cleaned transcript text without obvious semantic markers
- **When** the AI assistant executes the segmented summary workflow step
- **Then** the system SHOULD fall back to paragraph-based segmentation
- **And** record the fallback reason in each segment's `reason` field

### Requirement: Two-Source Spec Generation

The system MUST support combining original transcript with segmented summary data for enhanced spec generation.

#### Scenario: Generate spec from transcript and segmented summary
- **Given** an original transcript in `scraped_data.json`
- **And** a corresponding `segmented_summary.json` from the segmentation step
- **When** the AI assistant generates the spec
- **Then** the spec MUST:
  - Reference original transcript for accuracy verification
  - Use segment structure from segmented summary
  - Incorporate full summaries into lesson content
  - Preserve segment boundaries in skill sections

#### Scenario: Validate summary against original text
- **Given** a `segmented_summary.json` with summary content
- **And** the original transcript in `scraped_data.json`
- **When** generating the spec
- **Then** the AI assistant SHOULD verify summary accuracy against original
- **And** flag any potential discrepancies for review

### Requirement: Subsegment Identification

The system MUST identify and structure subsegments within major segments where distinct topic shifts occur.

#### Scenario: Identify subsegments in a major segment
- **Given** a major segment containing multiple distinct topics
- **When** the AI assistant analyzes the segment content
- **Then** subsegments MUST be created with:
  - Unique hierarchical IDs (e.g., "1.1", "1.2")
  - Topic descriptions
  - Individual summaries

### Requirement: Homophone Correction Notes

The system MUST support documenting and correcting speech-to-text homophone errors based on context analysis.

#### Scenario: Correct homophone in transcript
- **Given** a transcript containing the text "这个按理是很重要的" (应为"案例")
- **When** the AI assistant analyzes the context
- **Then** the segment's `homophone_notes` MUST contain:
  - Original text: "按理"
  - Corrected text: "案例"
  - Reason: "根据上下文关于示例讨论的主题推断"

### Requirement: Simplified Example Preservation

The system MUST preserve examples from the original content in simplified form within segment summaries.

#### Scenario: Preserve and simplify example
- **Given** a segment containing a detailed example about team structure
- **When** the AI assistant summarizes the segment
- **Then** `examples_simplified` MUST contain:
  - Essence of the example preserved
  - Unnecessary details removed
  - Core lesson/point maintained

---

## MODIFIED Requirements

### Requirement: Enhanced scraped_data Integration

The existing `scraped_data.json` output SHOULD be extended to reference segmented summary data when available.

#### Scenario: Reference segmented summary in scraped data
- **Given** both `scraped_data.json` and `segmented_summary.json` exist
- **When** the SpecGenerator processes the data
- **Then** lessons in the generated SkillSpec MUST reflect segment structure
- **And** segment summaries SHOULD be used as primary content source

---

## Cross-References

- **spec-first-skill-workflow**: SkillSpec generation should incorporate segment structure
- **slash-command-system**: Workflow documentation for segmented summary step
