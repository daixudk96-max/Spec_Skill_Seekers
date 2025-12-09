# Design: OpenSpec-Aligned Skill Workflow

## Context
The user wants the Skill_Seekers flow to follow Fission-AI/OpenSpec rigor: spec-first, reviewable, and deterministic. Existing repo already has a draft change (`add-spec-driven-skill-generation`); this design creates a new, scoped change ID to implement the requested workflow with minimal, skill-focused adaptations and without MCP for now.

## Goals
- Spec-first gate: scrape → generate Skill spec → user review → apply → SKILL.md outputs.
- Spec controls all outputs (SKILL.md, references/, scripts/, assets/).
- Templates based on anthropics/skills to standardize sections/content expectations.
- Rejection path triggers feedback-driven re-scrape and spec regeneration.
- Use existing Unified Multi-Source Scraping for conflict detection/resolution.
- Preserve current non-spec path for users who skip spec-first.

## Non-Goals
- MCP tool surface (explicitly deferred).
- Broad scraping refactors beyond what the feedback loop needs.

## Decisions
- **SkillSpec as source of truth**: A spec object/file enumerates all required outputs and sections; application step must not deviate.
- **Template set (anthropics/skills-inspired)**: Provide framework/api/tutorial/enterprise templates; each predefines section layout and reference expectations, extracted from the canonical anthropics/skills repository examples.
- **Review gate**: After spec generation, system pauses for user approval; only approved specs proceed to build.
- **Feedback and re-scrape**: Rejections capture reasons + focus/avoid hints; re-scrape uses these to refresh data before regenerating spec.
- **Conflict handling**: When applying spec against scraped data, run the existing Skill_Seekers Unified Multi-Source conflict detection/merge (NEW - v2.0.0); surface resolutions/warnings to user.
- **Backward compatibility**: Spec-first is opt-in; legacy direct generation path remains.

## Open Questions / Assumptions
- Assume templates can be stored locally with section/reference defaults; users may tweak before approval.
- Assume CLI (or equivalent driver) will host approval/rejection prompts; exact UX to be finalized in apply phase.
- Assume merge/conflict tooling already exists in repo and can be invoked during apply.
