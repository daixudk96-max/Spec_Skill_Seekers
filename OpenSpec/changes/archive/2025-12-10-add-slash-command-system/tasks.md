## 1. Core Infrastructure

- [x] 1.1 Create `src/skill_seekers/cli/configurators.py` with:
  - `AI_TOOLS` list (matching OpenSpec's 20+ tools)
  - `SlashCommandConfigurator` base class
  - Tool-specific configurators (Antigravity, Claude, Cursor, etc.)

- [x] 1.2 Create `src/skill_seekers/cli/slash_templates/` directory with:
  - `proposal.md`, `apply.md`, `archive.md` external template files
  - Template content for each command (guardrails, steps, references)

## 2. CLI Commands

- [x] 2.1 Add `init` subcommand to `main.py`:
  - `--tools` option (comma-separated or "all")
  - `--path` option (target directory)
  - Interactive tool selection if no `--tools` specified

- [x] 2.2 Add `update` subcommand to `main.py`:
  - Update existing workflow files with latest templates

- [x] 2.3 Add `--output-raw` flag to scrape command:
  - Output `scraped_data.json` with structured raw content
  - Skip LLM enhancement, provide data for AI assistant consumption

## 3. Workflow Content

- [x] 3.1 Write proposal workflow template:
  - Guides user to select source and template
  - Runs `skill-seekers scrape --spec-first`
  - Displays spec for review

- [x] 3.2 Write apply workflow template:
  - Loads approved spec
  - Runs `skill-seekers apply-spec`
  - Validates generated outputs

- [x] 3.3 Write archive workflow template:
  - Packages completed skill
  - Optionally uploads to Claude

## 4. Testing & Documentation

- [x] 4.1 Create `tests/test_slash_commands.py`:
  - Test configurator logic
  - Test template generation
  - Test CLI init command

- [x] 4.2 Update README.md:
  - Document slash command system
  - Add usage examples
