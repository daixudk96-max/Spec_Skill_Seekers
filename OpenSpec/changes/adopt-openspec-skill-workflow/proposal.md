# Adopt OpenSpec Skill Workflow

## Why
- Current Skill_Seekers flow can produce unpredictable SKILL.md because content is decided at generation time.
- Users lack a gated review step; issues surface only after SKILL.md is produced.
- The user asked to integrate Fission-AI/OpenSpec methodology (spec-before-build) to make outputs controllable and reviewable.
- We need templates aligned with anthropics/skills so specs stay rigorous but lightweight for common skill types.
- Rejections must trigger an informed re-scrape/spec regeneration loop, not ad-hoc retries.

## What
- Introduce a spec-first pipeline: **scrape → generate Skill spec → user review → apply spec to build SKILL.md + supporting artifacts**.
- Make the spec the single source of truth for all outputs (SKILL.md, references/, scripts/, assets/).
- Provide templates derived from anthropics/skills (framework, api, tutorial, enterprise) to keep spec authoring consistent; defaults should be extracted from the canonical repo https://github.com/anthropics/skills.
- Add a rejection path: capture feedback, re-scrape with targeted hints, regenerate spec, repeat until approval.
- Use the existing Unified Multi-Source Scraping (v2.0.0) from the Skill_Seekers project for resolving spec-vs-data conflicts, surfacing resolutions to the user.
- Keep scope to spec workflow and templates; defer MCP tooling to later as requested.

## Scope
- In: workflow definition, requirements/spec deltas, template expectations, conflict-handling rules, CLI/UX expectations for review/approval/rejection (design stage only).
- Out: MCP tool integration (explicitly deferred), unrelated scraping changes, non-skill artifacts.

## Success Criteria
- A validated OpenSpec change defining the spec-first skill workflow, templates, feedback loop, and conflict handling.
- Backward compatibility preserved for users who skip spec-first.

## Notes
- No project-level `openspec/project.md` was present; aligned to existing `OpenSpec` structure.
