# Tasks for fix-apply-spec-output-dir

## Implementation Tasks

### Phase 1: Core Fix (Parallel)

- [x] **T1: Update UnifiedSkillBuilder constructor**
  - Add `output_dir: Optional[str] = None` parameter
  - Use provided path or default to `output/{skill_name}`
  - File: `src/skill_seekers/cli/unified_skill_builder.py`
  - Verification: Unit test passes

- [x] **T2: Fix build_from_spec() directory handling**
  - Remove hardcoded `self.skill_dir = f"output/{self.skill_spec.name}"`
  - Only set default when no output_dir was provided at init
  - File: `src/skill_seekers/cli/unified_skill_builder.py`
  - Verification: Unit test passes

### Phase 2: CLI Integration

- [x] **T3: Update _handle_apply_spec()**
  - Read `args.output_dir` if provided
  - Pass `output_dir` to `UnifiedSkillBuilder` constructor
  - File: `src/skill_seekers/cli/main.py`
  - Depends on: T1
  - Verification: CLI test passes

### Phase 3: Testing

- [x] **T4: Add unit tests for output_dir parameter**
  - Test: `UnifiedSkillBuilder(..., output_dir=tmp)` uses custom path
  - Test: Default path is `output/{spec.name}` when omitted
  - File: `tests/test_unified.py`
  - Depends on: T1, T2

- [x] **T5: Add CLI integration test**
  - Test: `apply-spec --output-dir <tmp>` writes to custom path
  - Test: Without flag, output lands in default location
  - File: `tests/test_unified.py` (added `test_skill_builder_build_from_spec_respects_custom_output_dir`)
  - Depends on: T3

### Phase 4: Documentation

- [x] **T6: Update CLI help text** (if needed)
  - Ensure `--output-dir` help text is accurate
  - File: `src/skill_seekers/cli/main.py`
  - Note: Help text already accurate at line 201

## Dependencies

```
T1, T2 (parallel) → T3 → T4, T5 (parallel) → T6
```

## Verification Checklist

- [x] All existing tests pass: `pytest tests/` (2 pre-existing failures unrelated to this change)
- [x] New tests cover custom output_dir path
- [x] New tests cover default path fallback
- [x] CLI help shows correct description for `--output-dir`
