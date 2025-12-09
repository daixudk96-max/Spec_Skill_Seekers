# Add Spec-Driven Skill Generation

## Why

AI coding assistants are powerful but unpredictable when requirements live in chat history. Currently, Skill_Seekers generates skills directly from scraped data without any intermediate specification step. This means:

1. **Unpredictable Output**: The final SKILL.md content is unknown until generation completes
2. **No Review Gate**: Users cannot review or adjust the skill structure before AI processing
3. **Uncontrollable Scope**: Sections, key concepts, and examples are decided by the AI at runtime
4. **Iteration Waste**: If output is unsatisfactory, the entire generation must be rerun

By adopting OpenSpec's "spec-before-implementation" methodology, we can lock intent before execution, giving users deterministic, reviewable outputs.

## What Changes

We will implement a **spec-driven skill generation workflow** with feedback loop:

### Workflow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   ┌───────────┐     ┌────────────┐     ┌────────────┐               │
│   │  Scrape   │ ──▶ │  Generate  │ ──▶ │   User     │               │
│   │   Data    │     │   Spec     │     │  Reviews   │               │
│   └───────────┘     └────────────┘     └──────┬─────┘               │
│                                               │                      │
│                     ┌─────────────────────────┼─────────────────┐   │
│                     │                         │                 │   │
│                     ▼                         ▼                 │   │
│              ┌────────────┐           ┌────────────┐            │   │
│              │  Approved  │           │  Rejected  │            │   │
│              └──────┬─────┘           └──────┬─────┘            │   │
│                     │                        │                  │   │
│                     ▼                        ▼                  │   │
│              ┌────────────┐           ┌────────────┐            │   │
│              │   Apply    │           │  Re-scrape │ ◀──────────┘   │
│              │   Spec     │           │ w/Feedback │                │
│              └──────┬─────┘           └────────────┘                │
│                     │                                                │
│                     ▼                                                │
│              ┌────────────┐                                          │
│              │  Output    │                                          │
│              │ Skill.zip  │                                          │
│              └────────────┘                                          │
└──────────────────────────────────────────────────────────────────────┘
```

### Key Features

1. **Feedback Loop**: When spec review fails, system re-scrapes based on user feedback
2. **Full Output Control**: Spec controls **ALL** output including SKILL.md, references/, scripts/, and assets/
3. **Skill Templates**: Pre-built templates based on [anthropics/skills](https://github.com/anthropics/skills) for common skill types
4. **Conflict Resolution**: Use existing Unified Multi-Source Scraping for conflict merging

### Integration Points

1. **New Data Type**: `SkillSpec` dataclass defining complete skill output structure
2. **New Generator**: `spec_generator.py` - creates skill specs from scraped data
3. **Skill Templates**: `templates/` folder with framework, tutorial, API templates
4. **Modified Builder**: `unified_skill_builder.py` - accepts spec to guide ALL output
5. **Feedback Engine**: Re-scrape logic based on user rejection feedback
6. **CLI Extension**: `--spec-first` flag with feedback workflow
7. **MCP Tools**: `generate_skill_spec`, `apply_skill_spec`, `reject_skill_spec`

### Spec Controls Everything

The SkillSpec will control the **complete** output structure following [Anthropic Agent Skills Spec](https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md):

```
skill-name/
├── SKILL.md              # Controlled by spec: sections, examples, guidelines
│   ├── Frontmatter       # name, description (required)
│   └── Body              # Instructions, examples, guidelines
├── references/           # Controlled by spec: which docs to include
│   ├── api_docs.md
│   ├── tutorials.md
│   └── ...
├── scripts/              # Controlled by spec: which scripts to generate
│   └── ...
└── assets/               # Controlled by spec: templates, icons
    └── ...
```

## Impact

- **Specs**: New `skill-spec-generation` capability
- **Codebase**:
  - New `src/skill_seekers/cli/skill_spec.py` (SkillSpec dataclass)
  - New `src/skill_seekers/cli/spec_generator.py` (spec generation logic)
  - New `src/skill_seekers/templates/` (skill templates)
  - Modified `unified_skill_builder.py` (spec-guided building for ALL output)
  - Modified `main.py` (feedback loop CLI)
  - Modified MCP server (new tools with reject/re-scrape)

## Methodology Preservation

> **IMPORTANT**: This proposal strictly follows OpenSpec methodology principles:
> - Human and AI stakeholders agree on specs before work begins
> - Structured change folders keep scope explicit and auditable
> - Shared visibility into proposed, active, and archived changes
> - Feedback loop ensures continuous alignment

The skill spec format is adapted from:
- **OpenSpec**: requirement/scenario format for rigor
- **Anthropic Skills Spec**: SKILL.md structure and folder layout
