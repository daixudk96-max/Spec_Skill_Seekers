# Tasks: Add Spec-Driven Skill Generation

## 1. Core Data Types
- [ ] 1.1 Create `src/skill_seekers/cli/skill_spec.py` with complete SkillSpec dataclass
  - SkillSpec, SectionSpec, ReferenceSpec, ScriptSpec, AssetSpec
  - ExampleSpec, SpecFeedback
- [ ] 1.2 Add JSON/YAML serialization/deserialization methods
- [ ] 1.3 Add validation logic for spec structure (following Anthropic Agent Skills Spec)
- [ ] 1.4 Write unit tests for data types

## 2. Skill Templates
- [ ] 2.1 Create `src/skill_seekers/templates/` directory structure
- [ ] 2.2 Create `framework` template (React, Vue, Django style)
- [ ] 2.3 Create `api` template (REST API, SDK style)
- [ ] 2.4 Create `tutorial` template (course/learning content style)
- [ ] 2.5 Create `enterprise` template (brand guidelines, policies style)
- [ ] 2.6 Add template loading and validation logic
- [ ] 2.7 Write unit tests for templates

## 3. Spec Generator
- [ ] 3.1 Create `src/skill_seekers/cli/spec_generator.py`
- [ ] 3.2 Implement `generate_spec_from_docs()` - for documentation source
- [ ] 3.3 Implement `generate_spec_from_github()` - for GitHub source
- [ ] 3.4 Implement `generate_spec_from_transcript()` - for transcript source
- [ ] 3.5 Implement `generate_unified_spec()` - for multi-source with template selection
- [ ] 3.6 Add spec-to-markdown export for human review
- [ ] 3.7 Write unit tests for spec generation

## 4. Feedback Loop Engine
- [ ] 4.1 Create feedback handling in `src/skill_seekers/cli/spec_feedback.py`
- [ ] 4.2 Implement `handle_spec_rejection()` - generate new scrape config from feedback
- [ ] 4.3 Implement `apply_feedback_to_spec()` - modify spec based on user changes
- [ ] 4.4 Add scrape hints system for targeted re-scraping
- [ ] 4.5 Write unit tests for feedback handling

## 5. Skill Builder Integration
- [ ] 5.1 Modify `UnifiedSkillBuilder.__init__()` to accept SkillSpec
- [ ] 5.2 Implement spec-guided SKILL.md generation with all sections
- [ ] 5.3 Implement spec-guided `references/` folder generation
- [ ] 5.4 Implement spec-guided `scripts/` folder generation
- [ ] 5.5 Implement spec-guided `assets/` folder generation
- [ ] 5.6 Integrate with `merge_sources.py` for conflict resolution
- [ ] 5.7 Ensure backward compatibility when no spec is provided
- [ ] 5.8 Write integration tests

## 6. CLI Integration
- [ ] 6.1 Add `--spec-first` flag to `skill-seekers scrape` command
- [ ] 6.2 Add `--template` flag for template selection (framework/api/tutorial/enterprise)
- [ ] 6.3 Add `skill-seekers apply-spec` command
- [ ] 6.4 Add `skill-seekers reject-spec` command with feedback prompts
- [ ] 6.5 Implement interactive feedback loop in CLI
- [ ] 6.6 Add `--auto-approve` flag for automated workflows
- [ ] 6.7 Update help text and documentation
- [ ] 6.8 Write CLI integration tests

## 7. MCP Server Integration
- [ ] 7.1 Add `generate_skill_spec` MCP tool
- [ ] 7.2 Add `apply_skill_spec` MCP tool
- [ ] 7.3 Add `reject_skill_spec` MCP tool (with feedback handling)
- [ ] 7.4 Add `list_skill_templates` MCP tool
- [ ] 7.5 Update MCP server documentation
- [ ] 7.6 Write MCP tool tests

## 8. Documentation
- [ ] 8.1 Update README with spec-driven workflow section
- [ ] 8.2 Create template usage guide
- [ ] 8.3 Add troubleshooting guide for spec-related issues
- [ ] 8.4 Document feedback loop workflow

## Dependencies

```
Task 1 (Data Types) ← Task 2 (Templates) ← Task 3 (Generator)
                                        ← Task 4 (Feedback)
                   ← Task 5 (Builder) ← Task 6 (CLI)
                                      ← Task 7 (MCP)
Task 8 (Docs) depends on all above
```

## Parallelizable Work

- Tasks 2 (Templates) and 4 (Feedback) can start in parallel after Task 1
- Tasks 6 (CLI) and 7 (MCP) can be done in parallel after Task 5
- Task 8 (Docs) can start partially after Task 2 for template documentation
