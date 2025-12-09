#!/usr/bin/env python3
"""
Tests for SkillSpec Core Data Types

Covers:
- SkillSpec creation and validation
- JSON/YAML serialization round-trips
- Nested dataclass handling
- Edge cases and error handling
"""

import json
import pytest
from pathlib import Path
import tempfile

from skill_seekers.core.skill_spec import (
    AssetSpec,
    ExampleSpec,
    ReferenceSpec,
    ScriptSpec,
    SectionSpec,
    SkillSpec,
    SpecFeedback,
    SpecMeta,
)


# =============================================================================
# Fixtures
# =============================================================================

def make_minimal_spec() -> SkillSpec:
    """Create a minimal valid SkillSpec."""
    return SkillSpec(
        name="test-skill",
        description="A test skill for unit testing",
    )


def make_full_spec() -> SkillSpec:
    """Create a fully populated SkillSpec."""
    return SkillSpec(
        name="full-test-skill",
        description="A complete test skill with all fields",
        license="MIT",
        allowed_tools=["bash", "python"],
        metadata={"author": "test"},
        sections=[
            SectionSpec(
                title="## Overview",
                purpose="Provide introduction",
                expected_content=["Summary", "Key features"],
                priority="required",
            ),
            SectionSpec(
                title="## Process",
                purpose="Step-by-step guide",
                subsections=[
                    SectionSpec(title="### Step 1", purpose="First step"),
                    SectionSpec(title="### Step 2", purpose="Second step"),
                ],
            ),
        ],
        examples=[
            ExampleSpec(title="Basic Usage", code_language="python", description="Simple example"),
        ],
        guidelines=["Keep it simple", "Follow best practices"],
        references=[
            ReferenceSpec(filename="api_docs.md", purpose="API reference"),
        ],
        scripts=[
            ScriptSpec(filename="validate.py", purpose="Validation script"),
        ],
        assets=[
            AssetSpec(filename="template.html", asset_type="template"),
        ],
        template_type="technical-guide",
    )


# =============================================================================
# Basic Creation Tests
# =============================================================================

class TestSpecCreation:
    """Test SkillSpec and related dataclass creation."""

    def test_create_minimal_spec(self):
        """Minimal spec with only required fields."""
        spec = make_minimal_spec()
        assert spec.name == "test-skill"
        assert spec.description == "A test skill for unit testing"
        assert spec.meta.status == "pending"
        assert spec.meta.spec_version == "1.0"

    def test_create_full_spec(self):
        """Full spec with all fields populated."""
        spec = make_full_spec()
        assert spec.name == "full-test-skill"
        assert len(spec.sections) == 2
        assert len(spec.sections[1].subsections) == 2
        assert spec.template_type == "technical-guide"

    def test_spec_meta_auto_timestamp(self):
        """SpecMeta should auto-generate created_at."""
        meta = SpecMeta()
        assert meta.created_at is not None
        assert meta.status == "pending"

    def test_spec_meta_mark_applied(self):
        """SpecMeta.mark_applied() should update status and timestamps."""
        meta = SpecMeta()
        meta.mark_applied()
        assert meta.status == "applied"
        assert meta.applied_at is not None
        assert meta.updated_at is not None


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidation:
    """Test SkillSpec validation logic."""

    def test_valid_spec_passes_validation(self):
        """Valid spec should pass validation without errors."""
        spec = make_full_spec()
        spec.validate()  # Should not raise

    def test_name_required(self):
        """Validation fails if name is empty."""
        spec = SkillSpec(name="", description="test")
        with pytest.raises(ValueError, match="name is required"):
            spec.validate()

    def test_name_must_be_kebab_case(self):
        """Validation fails if name is not kebab-case."""
        spec = SkillSpec(name="TestSkill", description="test")
        with pytest.raises(ValueError, match="kebab-case"):
            spec.validate()

        spec = SkillSpec(name="test_skill", description="test")
        with pytest.raises(ValueError, match="kebab-case"):
            spec.validate()

    def test_description_required(self):
        """Validation fails if description is empty."""
        spec = SkillSpec(name="test-skill", description="")
        with pytest.raises(ValueError, match="description is required"):
            spec.validate()

    def test_invalid_template_type(self):
        """Validation fails for unknown template type."""
        spec = make_minimal_spec()
        spec.template_type = "unknown-template"
        with pytest.raises(ValueError, match="Invalid template_type"):
            spec.validate()

    def test_valid_template_types(self):
        """All valid template types should pass validation."""
        valid_types = ["technical-guide", "workflow-skill", "course-tutorial", 
                       "brand-enterprise", "tool-utility"]
        for tmpl in valid_types:
            spec = make_minimal_spec()
            spec.template_type = tmpl
            spec.validate()  # Should not raise

    def test_section_requires_purpose(self):
        """SectionSpec validation requires purpose."""
        section = SectionSpec(title="## Overview", purpose="")
        with pytest.raises(ValueError, match="purpose is required"):
            section.validate()

    def test_section_invalid_priority(self):
        """SectionSpec validation checks priority enum."""
        section = SectionSpec(title="## Overview", purpose="Summary", priority="maybe")
        with pytest.raises(ValueError, match="Invalid priority"):
            section.validate()

    def test_spec_meta_invalid_status(self):
        """SpecMeta validation checks status enum."""
        meta = SpecMeta(status="invalid")
        with pytest.raises(ValueError, match="Invalid status"):
            meta.validate()


# =============================================================================
# Serialization Tests
# =============================================================================

class TestJsonSerialization:
    """Test JSON serialization round-trips."""

    def test_minimal_spec_json_round_trip(self):
        """Minimal spec survives JSON round-trip."""
        spec = make_minimal_spec()
        json_str = spec.to_json()
        loaded = SkillSpec.from_json(json_str)
        
        assert loaded.name == spec.name
        assert loaded.description == spec.description
        assert loaded.meta.status == spec.meta.status

    def test_full_spec_json_round_trip(self):
        """Full spec with all fields survives JSON round-trip."""
        spec = make_full_spec()
        json_str = spec.to_json()
        loaded = SkillSpec.from_json(json_str)
        
        assert loaded.name == spec.name
        assert len(loaded.sections) == 2
        assert len(loaded.sections[1].subsections) == 2
        assert loaded.template_type == spec.template_type
        loaded.validate()  # Should pass

    def test_nested_dataclasses_preserved(self):
        """Nested dataclasses should be proper instances after deserialization."""
        spec = make_full_spec()
        loaded = SkillSpec.from_json(spec.to_json())
        
        assert isinstance(loaded.sections[0], SectionSpec)
        assert isinstance(loaded.sections[1].subsections[0], SectionSpec)
        assert isinstance(loaded.references[0], ReferenceSpec)
        assert isinstance(loaded.scripts[0], ScriptSpec)
        assert isinstance(loaded.meta, SpecMeta)

    def test_json_is_valid_json(self):
        """to_json() should produce valid JSON."""
        spec = make_full_spec()
        json_str = spec.to_json()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["name"] == "full-test-skill"


class TestYamlSerialization:
    """Test YAML serialization round-trips."""

    def test_yaml_round_trip(self):
        """Spec survives YAML round-trip."""
        pytest.importorskip("yaml")
        
        spec = make_full_spec()
        yaml_str = spec.to_yaml()
        loaded = SkillSpec.from_yaml(yaml_str)
        
        assert loaded.name == spec.name
        assert len(loaded.sections) == 2
        loaded.validate()

    def test_yaml_matches_dict(self):
        """YAML round-trip should produce equivalent dict."""
        pytest.importorskip("yaml")
        
        spec = make_full_spec()
        original_dict = spec.to_dict()
        loaded = SkillSpec.from_yaml(spec.to_yaml())
        loaded_dict = loaded.to_dict()
        
        # Compare key fields (timestamps may differ slightly)
        assert loaded_dict["name"] == original_dict["name"]
        assert loaded_dict["sections"] == original_dict["sections"]


class TestFileSerialization:
    """Test file save/load operations."""

    def test_save_and_load_json(self):
        """Spec can be saved and loaded from JSON file."""
        spec = make_full_spec()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "spec.json"
            spec.save(path)
            loaded = SkillSpec.load(path)
            
            assert loaded.name == spec.name
            assert len(loaded.sections) == 2

    def test_save_and_load_yaml(self):
        """Spec can be saved and loaded from YAML file."""
        pytest.importorskip("yaml")
        
        spec = make_full_spec()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "spec.yaml"
            spec.save(path)
            loaded = SkillSpec.load(path)
            
            assert loaded.name == spec.name


# =============================================================================
# SpecFeedback Tests
# =============================================================================

class TestSpecFeedback:
    """Test SpecFeedback data structure."""

    def test_empty_feedback_no_changes(self):
        """Empty feedback should report no changes."""
        feedback = SpecFeedback(approved=True)
        assert feedback.has_changes() is False

    def test_feedback_with_changes_detected(self):
        """Feedback with any change field should report has_changes."""
        feedback = SpecFeedback(
            approved=False,
            rejection_reason="Missing API examples",
            suggested_changes=["Add authentication flow"],
            additional_sources=["https://docs.example.com/api"],
        )
        assert feedback.has_changes() is True

    def test_feedback_to_markdown(self):
        """Feedback should produce readable markdown."""
        feedback = SpecFeedback(
            approved=False,
            rejection_reason="Missing examples",
            add_sections=["API Reference"],
        )
        md = feedback.to_markdown()
        
        assert "No" in md  # approved: No
        assert "Missing examples" in md
        assert "API Reference" in md


# =============================================================================
# Markdown Output Tests
# =============================================================================

class TestMarkdownOutput:
    """Test to_markdown() output formatting."""

    def test_skillspec_to_markdown(self):
        """SkillSpec.to_markdown() produces readable output."""
        spec = make_full_spec()
        md = spec.to_markdown()
        
        assert "# Skill Spec: full-test-skill" in md
        assert "pending" in md
        assert "## Overview" in md
        assert "## Process" in md
        assert "api_docs.md" in md

    def test_section_title_not_double_prefixed(self):
        """Section titles with # should not get additional # prefix."""
        section = SectionSpec(title="## Already Prefixed", purpose="Test")
        md = section.to_markdown()
        
        # Should NOT start with "### ## Already Prefixed"
        assert md.startswith("## Already Prefixed")
        assert not md.startswith("### ##")

    def test_section_title_without_prefix(self):
        """Section titles without # should get ### prefix."""
        section = SectionSpec(title="No Prefix", purpose="Test")
        md = section.to_markdown()
        
        assert md.startswith("### No Prefix")


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_lists_handled(self):
        """Empty lists should be handled gracefully."""
        spec = make_minimal_spec()
        spec.validate()
        json_str = spec.to_json()
        loaded = SkillSpec.from_json(json_str)
        assert loaded.sections == []
        assert loaded.references == []

    def test_deeply_nested_sections(self):
        """Deeply nested sections should serialize correctly."""
        deep_section = SectionSpec(
            title="## Level 1",
            purpose="First level",
            subsections=[
                SectionSpec(
                    title="### Level 2",
                    purpose="Second level",
                    subsections=[
                        SectionSpec(title="#### Level 3", purpose="Third level"),
                    ],
                ),
            ],
        )
        spec = make_minimal_spec()
        spec.sections = [deep_section]
        
        loaded = SkillSpec.from_json(spec.to_json())
        assert len(loaded.sections[0].subsections[0].subsections) == 1
        assert loaded.sections[0].subsections[0].subsections[0].title == "#### Level 3"

    def test_unicode_content(self):
        """Unicode content should be preserved."""
        spec = SkillSpec(
            name="chinese-skill",
            description="中文技能描述",
            sections=[
                SectionSpec(title="## 概述", purpose="提供简介"),
            ],
        )
        
        loaded = SkillSpec.from_json(spec.to_json())
        assert loaded.description == "中文技能描述"
        assert loaded.sections[0].title == "## 概述"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
