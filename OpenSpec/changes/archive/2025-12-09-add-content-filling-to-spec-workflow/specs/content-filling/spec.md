# content-filling Spec Delta

This spec delta extends the `spec-first-skill-workflow` capability with content filling requirements.

## MODIFIED Requirements

### Requirement: Apply spec to generate complete skill folder (MODIFIED)

The system SHALL fill generated files with actual content extracted from source_config, not placeholders.

#### Scenario: Apply spec generates SKILL.md with actual content
- **GIVEN** an approved SkillSpec with source_config containing transcript/lesson data
- **WHEN** the user runs `skill-seekers apply-spec --spec skill_spec.yaml`
- **THEN** the generated SKILL.md contains actual section content derived from source_config
- **AND** each section contains generated text relevant to its purpose and expected_content
- **AND** the output does NOT contain placeholder text like "Expected content:" or "TODO:"

#### Scenario: Apply spec fills reference files with extracted content
- **GIVEN** an approved SkillSpec with references defined and source_config containing raw data
- **WHEN** the spec is applied
- **THEN** each reference file (e.g., concepts.md, exercises.md, lesson_notes.md) contains actual content
- **AND** the content is extracted or synthesized from source_config data
- **AND** the files do NOT contain "TODO: Populate with content" placeholders

#### Scenario: LLM-enhanced content generation
- **GIVEN** ANTHROPIC_API_KEY environment variable is set
- **WHEN** apply-spec runs with a SkillSpec containing course-tutorial template
- **THEN** sections like 课程摘要, 关键要点, 实践练习 are generated using Claude API
- **AND** the generated content is relevant to the source transcript
- **AND** exercises include questions with reference answers

#### Scenario: Fallback to deterministic extraction
- **GIVEN** ANTHROPIC_API_KEY is NOT set or `--no-llm` flag is used
- **WHEN** apply-spec runs
- **THEN** the system extracts content using pattern-based methods
- **AND** summary sections contain the first N characters of transcript
- **AND** key points sections contain timestamped paragraph headings
- **AND** sections requiring synthesis (like exercises) display a notice that LLM is required

## ADDED Requirements

### Requirement: Content Synthesizer Component
The system SHALL provide a ContentSynthesizer component that generates section and reference content from source_config data.

#### Scenario: Synthesize section content
- **GIVEN** a SectionSpec with title, purpose, and expected_content
- **WHEN** ContentSynthesizer.synthesize_section_content() is called
- **THEN** it returns markdown content matching the section purpose
- **AND** the content is derived from available source_config data

#### Scenario: Synthesize reference content
- **GIVEN** a ReferenceSpec with filename, purpose, and content_sources
- **WHEN** ContentSynthesizer.synthesize_reference_content() is called
- **THEN** it returns content for the reference file
- **AND** if content_sources specifies "lessons", lesson data is included

### Requirement: CLI flag for LLM control
The apply-spec command SHALL support a `--no-llm` flag to disable LLM-based content generation.

#### Scenario: Force fallback mode
- **GIVEN** a valid SkillSpec
- **WHEN** the user runs `skill-seekers apply-spec --spec spec.yaml --no-llm`
- **THEN** the system uses only deterministic extraction
- **AND** no API calls are made to Claude

## Cross-References

- Extends: `spec-first-skill-workflow/spec.md` > "Spec Controls All Outputs"
- Relates to: `transcript-ingestion/spec.md` (uses similar LLM enhancement patterns)
