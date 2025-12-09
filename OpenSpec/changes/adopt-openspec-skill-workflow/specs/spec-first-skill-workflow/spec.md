# Delta for spec-first-skill-workflow

## ADDED Requirements

### Requirement: Enforce Spec-First Skill Flow
The system SHALL implement the workflow: scrape data → generate a Skill spec → pause for user review → apply the approved spec to build outputs.

#### Scenario: Generate and pause for approval
- **GIVEN** a scrape completes for a target project
- **WHEN** the user runs skill generation with spec-first enabled
- **THEN** the system produces a Skill spec file (e.g., `skill_spec.json` or `.md`) and displays a human-readable summary
- **AND** the system halts further output generation until the user approves or rejects the spec.

### Requirement: Spec Controls All Outputs
The system SHALL ensure the approved spec is the single source of truth for every generated artifact, including SKILL.md sections, references/, scripts/, and assets/ contents.

#### Scenario: Apply spec to generate outputs
- **GIVEN** an approved Skill spec describing SKILL.md sections, references files, scripts, and assets
- **WHEN** the spec is applied
- **THEN** the resulting SKILL.md matches the specified sections and ordering
- **AND** only the reference files listed in the spec are created in references/
- **AND** only the scripts listed in the spec are created in scripts/
- **AND** only the assets listed in the spec are created in assets/.

### Requirement: Provide Anthropic-Inspired Templates
The system SHALL offer templates inspired by anthropics/skills for at least framework, api, tutorial, and enterprise skill types to accelerate spec creation, using defaults extracted from the canonical anthropics/skills repository.

#### Scenario: Select tutorial template
- **GIVEN** a user wants to build a learning-style skill
- **WHEN** they generate a spec with the tutorial template
- **THEN** the spec includes sections such as Summary, Key Concepts, Step-by-Step Guide, and Practice Exercises
- **AND** the spec predefines reference files (e.g., concepts.md, exercises.md) consistent with anthropics/skills patterns.

#### Scenario: Templates align with canonical examples
- **GIVEN** the anthropics/skills repository as the template source
- **WHEN** the template defaults are generated
- **THEN** the sections and reference file expectations reflect the canonical examples from that repository.

### Requirement: Feedback-Driven Re-Scrape and Regeneration
The system SHALL support user rejection with feedback that triggers targeted re-scraping and regeneration of the Skill spec.

#### Scenario: Reject and regenerate
- **GIVEN** a generated Skill spec awaiting review
- **WHEN** the user rejects it with reasons and additional focus/avoid hints
- **THEN** the system re-scrapes using the provided feedback
- **AND** regenerates a new Skill spec reflecting the updated data and user feedback
- **AND** returns to the review gate before any outputs are built.

### Requirement: Resolve Conflicts with Unified Multi-Source Scraping
The system SHALL use the existing Skill_Seekers Unified Multi-Source conflict detection/merge strategy (NEW - v2.0.0) when applying specs against scraped data, surfacing any resolutions to the user.

#### Scenario: Apply spec with conflicting sources
- **GIVEN** an approved spec and scraped data from multiple sources that contain conflicting details
- **WHEN** the spec is applied to build outputs
- **THEN** the system runs Unified Multi-Source conflict detection and merge before writing files
- **AND** any conflicts and their resolutions are reported to the user with warnings in the review/apply output.

### Requirement: Preserve Non-Spec Workflow
The system SHALL preserve the existing direct skill generation path for users who do not opt into spec-first.

#### Scenario: Run without spec-first
- **GIVEN** a user runs skill generation without enabling spec-first
- **WHEN** the pipeline executes
- **THEN** the system produces outputs using the current direct workflow
- **AND** no spec file is required or generated
- **AND** existing flags and behaviors remain unchanged.
