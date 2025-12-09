# Delta for skill-spec-generation

## ADDED Requirements

### Requirement: Generate Skill Specification
The system SHALL generate a structured skill specification (SkillSpec) from scraped data before generating the final skill output. The SkillSpec MUST control ALL output including SKILL.md, references/, scripts/, and assets/.

#### Scenario: Generate spec from documentation
- **GIVEN** scraped documentation data from a website
- **WHEN** the user runs `skill-seekers scrape --config config.json --spec-first`
- **THEN** the system generates a `skill_spec.json` file in the output directory
- **AND** the system displays a summary of the proposed skill structure
- **AND** the system waits for user approval before proceeding

#### Scenario: Generate spec from transcript
- **GIVEN** parsed transcript content from `.srt` or `.txt` files
- **WHEN** spec generation is invoked with `--template tutorial`
- **THEN** the system generates a SkillSpec with sections: Summary, Key Points, Practice Exercises
- **AND** the spec defines references/ folder structure for detailed content

#### Scenario: Spec controls all output
- **GIVEN** an approved SkillSpec
- **WHEN** the spec is applied
- **THEN** the system generates SKILL.md exactly matching the spec sections
- **AND** the system generates references/ folder matching the spec references list
- **AND** the system generates scripts/ folder matching the spec scripts list
- **AND** the system generates assets/ folder matching the spec assets list

### Requirement: Skill Templates
The system SHALL provide pre-built templates based on Anthropic Agent Skills Spec for common skill types including framework, api, tutorial, and enterprise.

#### Scenario: Select framework template
- **GIVEN** a documentation source for a framework like React or Django
- **WHEN** the user runs `skill-seekers scrape --spec-first --template framework`
- **THEN** the system generates a SkillSpec with sections: Overview, Installation, Core Concepts, API Reference, Examples, Best Practices
- **AND** the spec includes references for api_docs.md and tutorials.md

#### Scenario: Select tutorial template
- **GIVEN** a transcript source for learning content
- **WHEN** the user runs `skill-seekers scrape --spec-first --template tutorial`
- **THEN** the system generates a SkillSpec with sections: Summary, Key Concepts, Step-by-Step Guide, Practice Exercises
- **AND** the spec includes references for concepts.md and exercises.md

#### Scenario: List available templates
- **WHEN** the user runs `skill-seekers templates list`
- **THEN** the system displays all available templates with descriptions

### Requirement: Feedback Loop for Spec Rejection
The system SHALL support a feedback loop where rejected specs trigger re-scraping based on user feedback.

#### Scenario: Reject spec with feedback
- **GIVEN** a generated SkillSpec awaiting user review
- **WHEN** the user runs `skill-seekers reject-spec --reason "missing API examples"`
- **THEN** the system captures the rejection reason
- **AND** the system prompts for additional data sources or focus areas
- **AND** the system re-scrapes with the updated configuration
- **AND** the system generates a new SkillSpec

#### Scenario: Approve spec and generate
- **GIVEN** a generated SkillSpec
- **WHEN** the user runs `skill-seekers apply-spec --spec skill_spec.json`
- **THEN** the system generates the complete skill folder structure
- **AND** all output matches the approved spec

### Requirement: Conflict Resolution via Unified Multi-Source
The system SHALL use the existing Unified Multi-Source Scraping conflict detection and resolution for handling spec vs data conflicts.

#### Scenario: Detect and resolve conflicts
- **GIVEN** a SkillSpec and scraped data with conflicting information
- **WHEN** the spec is applied
- **THEN** the system uses ConflictDetector to identify conflicts
- **AND** the system uses MergeEngine to resolve conflicts
- **AND** the system reports resolved conflicts to the user with inline ⚠️ warnings

### Requirement: Backward Compatibility
The system SHALL maintain backward compatibility with existing workflows that do not use spec-driven generation.

#### Scenario: Direct generation without spec
- **GIVEN** a user runs the scrape command without `--spec-first` flag
- **WHEN** the skill builder runs
- **THEN** the system generates the skill using existing direct generation logic
- **AND** no spec file is created
- **AND** all existing CLI flags continue to work
