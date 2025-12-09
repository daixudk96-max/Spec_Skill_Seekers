# Standardize Spec-Driven Skill Workflow

## Why

AI coding assistants are powerful but unpredictable when requirements live in chat history. Currently, Skill_Seekers generates skills directly from scraped data without any intermediate specification step. This creates several problems:

1. **Unpredictable Output**: The final SKILL.md content is unknown until generation completes
2. **No Review Gate**: Users cannot review or adjust the skill structure before AI processing
3. **Uncontrollable Scope**: Sections, key concepts, and examples are decided by the AI at runtime
4. **Iteration Waste**: If output is unsatisfactory, the entire generation must be rerun

By adopting **OpenSpec's "spec-before-implementation" methodology** adapted for skill generation, we can lock intent before execution, giving users deterministic, reviewable outputs.

> **Note**: This proposal merges the strengths of `add-spec-driven-skill-generation` and `adopt-openspec-skill-workflow`, excluding MCP tooling (deferred to a future change).

## What Changes

We implement a **spec-driven skill generation workflow** with user feedback loop:

### Workflow Diagram (Following OpenSpec Pattern)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Spec-Driven Skill Generation                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│   │   Scrape    │ ──▶ │ Generate Skill  │ ──▶ │  User Reviews   │          │
│   │    Data     │     │      Spec       │     │   Skill Spec    │          │
│   └─────────────┘     └─────────────────┘     └────────┬────────┘          │
│                                                        │                   │
│                         ┌──────────────────────────────┼─────────────┐     │
│                         │                              │             │     │
│                         ▼                              ▼             │     │
│                  ┌────────────┐                 ┌────────────┐       │     │
│                  │  APPROVED  │                 │  REJECTED  │       │     │
│                  └──────┬─────┘                 └──────┬─────┘       │     │
│                         │                              │             │     │
│                         ▼                              ▼             │     │
│                  ┌────────────┐                 ┌────────────┐       │     │
│                  │   Apply    │                 │ Re-scrape  │ ◀─────┘     │
│                  │   Spec     │                 │ w/Feedback │             │
│                  └──────┬─────┘                 └────────────┘             │
│                         │                                                  │
│                         ▼                                                  │
│          ┌────────────────────────────┐                                    │
│          │  Generate Complete Skill   │                                    │
│          │  Folder (All Outputs)      │                                    │
│          └────────────────────────────┘                                    │
│                         │                                                  │
│                         ▼                                                  │
│                  ┌────────────┐                                            │
│                  │   Output   │                                            │
│                  │ skill.zip  │                                            │
│                  └────────────┘                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Spec-First Gate** | Skill spec is generated and reviewed before any final output is produced |
| **Feedback Loop** | Rejected specs trigger re-scraping based on user feedback |
| **Full Output Control** | Spec controls **ALL** output: SKILL.md, references/, scripts/, assets/ |
| **Anthropic Templates** | Pre-built templates extracted from [anthropics/skills](https://github.com/anthropics/skills) |
| **Conflict Resolution** | Uses existing Unified Multi-Source Scraping v2.0.0 for merge conflicts |

### Template System (Based on Real anthropics/skills + Project Patterns)

Templates are derived from actual skills in the official repository **and** existing project patterns:

| Template | 产出类别 | 参考来源 | 典型输出章节 | 典型资源 |
|----------|---------|---------|-------------|----------|
| **technical-guide** | 技术开发指南 | `mcp-builder` | Overview, Process(Phases), Reference Files | references/ + scripts/ |
| **workflow-skill** | 工作流/元技能 | `skill-creator` | About, Core Principles, Process(Steps) | references/ + scripts/ |
| **course-tutorial** | 课程/教程内容 | `transcript_scraper` | 课程摘要, 关键要点, 核心概念, 实践练习, 延伸学习 | references/ |
| **brand-enterprise** | 企业品牌/规范 | `brand-guidelines` | Overview, Guidelines, Features, Technical Details | assets/ |
| **tool-utility** | 工具集成/测试 | `webapp-testing` | Decision Tree, Examples, Best Practices | scripts/ |

### Integration Points

| Component | File/Location | Purpose |
|-----------|---------------|---------|
| SkillSpec dataclass | `src/skill_seekers/cli/skill_spec.py` | Complete skill output specification |
| Spec Generator | `src/skill_seekers/cli/spec_generator.py` | Creates skill specs from scraped data |
| Skill Templates | `src/skill_seekers/templates/` | Pre-built templates per skill type |
| Skill Builder (Modified) | `unified_skill_builder.py` | Accepts spec to guide ALL output |
| Feedback Engine | `src/skill_seekers/cli/spec_feedback.py` | Re-scrape logic based on rejection |
| CLI Extension | `main.py` | `--spec-first` flag with feedback workflow |

### Spec Controls Everything (Following Agent Skills Spec)

The SkillSpec controls the **complete** output structure per [Anthropic Agent Skills Spec](https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md):

```
skill-name/
├── SKILL.md              # Controlled by spec: frontmatter + body
│   ├── Frontmatter       # name (required), description (required), license, allowed-tools, metadata
│   └── Body              # Sections, examples, guidelines (no restrictions per spec)
├── references/           # Controlled by spec: which docs to include
│   ├── api_docs.md
│   ├── tutorials.md
│   └── ...
├── scripts/              # Controlled by spec: which scripts to generate
│   └── ...
└── assets/               # Controlled by spec: templates, icons
    └── ...
```

## Scope

### In Scope
- Workflow definition and requirements/spec deltas
- SkillSpec data types with complete field definitions
- Template expectations derived from real anthropics/skills
- Conflict-handling rules using Unified Multi-Source Scraping
- CLI/UX expectations for spec-first, review, approval, rejection
- Feedback-driven re-scrape mechanism

### Out of Scope
- **MCP tool integration** (explicitly deferred to future change)
- Unrelated scraping changes beyond feedback loop needs
- Non-skill artifacts

## Success Criteria

1. A validated OpenSpec change defining the spec-first skill workflow
2. SkillSpec dataclass with complete output control
3. Templates aligned with real anthropics/skills examples
4. Feedback loop for re-scraping on rejection
5. Conflict handling via Unified Multi-Source Scraping
6. Backward compatibility preserved for users who skip spec-first

## Methodology Preservation

> **IMPORTANT**: This proposal strictly follows OpenSpec methodology principles:
> - Human and AI stakeholders agree on specs before work begins
> - Structured change folders keep scope explicit and auditable
> - Shared visibility into proposed, active, and archived changes
> - Feedback loop ensures continuous alignment

The skill spec format is adapted from:
- **OpenSpec**: requirement/scenario format for rigor
- **Anthropic Agent Skills Spec**: SKILL.md structure and folder layout
