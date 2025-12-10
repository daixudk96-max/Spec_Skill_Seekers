# spec-first-skill-workflow Specification

## Purpose
TBD - created by archiving change standardize-spec-driven-workflow. Update Purpose after archive.
## Requirements
### Requirement: Enforce Spec-First Skill Generation Flow
The system SHALL implement the workflow: scrape data → generate Skill spec → pause for user review → apply approved spec to build all outputs.

#### Scenario: Generate spec and pause for approval
- **GIVEN** a scrape completes for a target project
- **WHEN** the user runs `skill-seekers scrape --config config.json --spec-first`
- **THEN** the system produces a SkillSpec file (`skill_spec.json` or `.yaml`) and displays a human-readable summary
- **AND** the system halts further output generation until the user approves or rejects the spec

#### Scenario: Generate spec from transcript with course-tutorial template
- **GIVEN** parsed transcript content from `.srt` or `.txt` files
- **WHEN** spec generation is invoked with `--template course-tutorial`
- **THEN** the system generates a SkillSpec with sections: 课程摘要, 关键要点, 核心概念详解, 实践练习, 延伸学习
- **AND** the spec defines references/ folder structure for concepts.md and exercises.md

### Requirement: Spec Controls All Outputs
The system SHALL ensure the approved SkillSpec is the single source of truth for every generated artifact, including SKILL.md sections, references/, scripts/, and assets/ contents.

#### Scenario: Apply spec to generate complete skill folder
- **GIVEN** an approved SkillSpec describing SKILL.md sections, references files, scripts, and assets
- **WHEN** the user runs `skill-seekers apply-spec --spec skill_spec.json`
- **THEN** the resulting SKILL.md matches the specified sections and ordering
- **AND** only the reference files listed in the spec are created in references/
- **AND** only the scripts listed in the spec are created in scripts/
- **AND** only the assets listed in the spec are created in assets/

#### Scenario: SKILL.md frontmatter follows Anthropic Agent Skills Spec
- **GIVEN** an approved SkillSpec with name, description, license, and allowed_tools
- **WHEN** the spec is applied
- **THEN** the generated SKILL.md contains YAML frontmatter with `name` (required), `description` (required)
- **AND** optional fields `license`, `allowed-tools`, `metadata` are included only if specified in spec

### Requirement: Provide Templates Based on Real anthropics/skills Examples and Project Patterns
The system SHALL offer templates derived from actual skills in the [anthropics/skills](https://github.com/anthropics/skills) repository and project patterns for at least: technical-guide, workflow-skill, course-tutorial, brand-enterprise, and tool-utility skill types.

#### Scenario: Select technical-guide template
- **GIVEN** a documentation source for a framework or SDK
- **WHEN** the user runs `skill-seekers scrape --spec-first --template technical-guide`
- **THEN** the system generates a SkillSpec with sections: Overview, Process (with Phases), Reference Files
- **AND** the spec includes defaults for references/ (best_practices.md, examples.md) and scripts/

#### Scenario: Select course-tutorial template
- **GIVEN** transcript files from an online course or training video
- **WHEN** the user runs `skill-seekers scrape --spec-first --template course-tutorial`
- **THEN** the system generates a SkillSpec with sections: 课程摘要, 关键要点, 核心概念详解, 实践练习, 延伸学习
- **AND** the spec includes defaults for references/ (concepts.md, exercises.md)
- **AND** the output structure matches the existing transcript_scraper enhanced output

#### Scenario: Select brand-enterprise template
- **GIVEN** company brand guidelines or style guide documents
- **WHEN** the user runs `skill-seekers scrape --spec-first --template brand-enterprise`
- **THEN** the system generates a SkillSpec with sections: Overview, Guidelines (with Colors, Typography), Features, Technical Details
- **AND** the spec includes defaults for assets/ folder (brand materials)
- **AND** the spec does NOT include references/ or scripts/ by default

#### Scenario: List available templates
- **WHEN** the user runs `skill-seekers templates list`
- **THEN** the system displays all available templates with descriptions and source skill references

### Requirement: Feedback-Driven Re-Scrape and Regeneration
The system SHALL support user rejection with feedback that triggers targeted re-scraping and regeneration of the Skill spec.

#### Scenario: Reject spec with feedback
- **GIVEN** a generated SkillSpec awaiting user review
- **WHEN** the user runs `skill-seekers reject-spec --spec skill_spec.json --reason "missing API examples" --add-source "https://docs.example.com/api" --add-section "API Reference"`
- **THEN** the system captures the rejection reason, additional sources, and section changes
- **AND** the system re-scrapes with the provided feedback as hints
- **AND** the system regenerates a new SkillSpec reflecting the updated data
- **AND** the system returns to the review gate before any outputs are built

#### Scenario: Approve spec and generate
- **GIVEN** a generated SkillSpec
- **WHEN** the user runs `skill-seekers apply-spec --spec skill_spec.json`
- **THEN** the system generates the complete skill folder structure matching the spec
- **AND** all output files and directories are controlled by the approved spec

### Requirement: Resolve Conflicts with Unified Multi-Source Scraping
The system SHALL use the existing Skill_Seekers Unified Multi-Source conflict detection/merge strategy (v2.0.0) when applying specs against scraped data, surfacing any resolutions to the user.

#### Scenario: Apply spec with conflicting sources
- **GIVEN** an approved SkillSpec and scraped data from multiple sources that contain conflicting details
- **WHEN** the spec is applied to build outputs
- **THEN** the system runs Unified Multi-Source conflict detection and merge before writing files
- **AND** any conflicts and their resolutions are reported to the user with inline ⚠️ warnings

#### Scenario: Display conflict resolution diff
- **GIVEN** conflicts detected between spec and scraped data
- **WHEN** the user requests to see the diff
- **THEN** the system displays the original conflicting content and the resolved content
- **AND** the user can accept or override the resolution

### Requirement: Preserve Non-Spec Workflow (Backward Compatibility)
The system SHALL preserve the existing direct skill generation path for users who do not opt into spec-first.

#### Scenario: Run without spec-first flag
- **GIVEN** a user runs `skill-seekers scrape --config config.json` without `--spec-first` flag
- **WHEN** the pipeline executes
- **THEN** the system produces outputs using the current direct workflow
- **AND** no spec file is required or generated
- **AND** existing flags and behaviors remain unchanged

#### Scenario: Auto-approve for CI/automation
- **GIVEN** a user runs `skill-seekers scrape --spec-first --auto-approve`
- **WHEN** the spec is generated
- **THEN** the system automatically approves and applies the spec without user intervention
- **AND** the complete skill folder is generated in a single command

### Requirement: CLI Commands for Spec Workflow (No MCP)
The system SHALL provide CLI commands for the complete spec-first workflow, with MCP tooling explicitly deferred to a future change.

#### Scenario: Show generated spec
- **GIVEN** a previously generated SkillSpec file
- **WHEN** the user runs `skill-seekers show-spec --spec skill_spec.json`
- **THEN** the system displays a human-readable summary of the spec
- **AND** the output includes sections, references, scripts, and assets defined in the spec

#### Scenario: Interactive feedback in CLI
- **GIVEN** spec-first mode is enabled
- **WHEN** the spec is generated and displayed
- **THEN** the CLI prompts the user to approve, reject with feedback, or cancel
- **AND** the user can provide rejection reasons and hints interactively

