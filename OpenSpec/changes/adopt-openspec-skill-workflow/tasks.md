# Tasks: Adopt OpenSpec Skill Workflow

1) Capture current state
- [ ] Inspect existing spec-first draft (`add-spec-driven-skill-generation`) for reusable concepts.
- [ ] Inventory existing Unified Multi-Source conflict tooling.

2) Define SkillSpec template set
- [ ] Draft template defaults (framework/api/tutorial/enterprise) aligned with anthropics/skills section patterns.
- [ ] Extract baseline sections/reference files from the canonical anthropics/skills repository examples.
- [ ] Specify how templates map to SKILL.md sections and references/ files.

3) Spec-first workflow requirements
- [ ] Describe scrape → spec → user review → apply flow, including approval gate and pause behavior.
- [ ] Define how spec controls SKILL.md, references/, scripts/, and assets/ outputs.
- [ ] Define rejection + feedback-driven re-scrape/regenerate loop (inputs, hints, reuse of scrape config).
- [ ] Define conflict-handling expectations using Unified Multi-Source merge/diff reporting.
- [ ] Document backward-compatibility expectations when spec-first is not used.

4) Spec deltas
- [ ] Write spec delta(s) capturing the above requirements and scenarios.
- [ ] Cross-check against existing specs to avoid duplication and ensure clarity.

5) Validation
- [ ] Run `openspec validate adopt-openspec-skill-workflow --strict` and resolve all issues.

6) Handoff
- [ ] Summarize proposal and validation status for approval.
