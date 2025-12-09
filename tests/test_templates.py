#!/usr/bin/env python3
"""
Tests for Skill Templates

Covers:
- Template loading and listing
- Template application to create SkillSpec
- All 5 template types
"""

import pytest
from pathlib import Path

from skill_seekers.cli.templates import (
    apply_template,
    get_template_names,
    get_template_path,
    list_templates,
    load_template,
    TEMPLATES_DIR,
)
from skill_seekers.core.skill_spec import SkillSpec, SectionSpec


# =============================================================================
# Template Discovery Tests
# =============================================================================

class TestTemplateDiscovery:
    """Test template loading and discovery."""

    def test_templates_dir_exists(self):
        """Templates directory should exist."""
        assert TEMPLATES_DIR.exists()
        assert TEMPLATES_DIR.is_dir()

    def test_list_templates_returns_all_five(self):
        """list_templates should return all 5 configured templates."""
        templates = list_templates()
        names = [t["name"] for t in templates]
        
        expected = [
            "brand-enterprise",
            "course-tutorial",
            "technical-guide",
            "tool-utility",
            "workflow-skill",
        ]
        assert sorted(names) == sorted(expected)

    def test_get_template_names(self):
        """get_template_names returns list of template names."""
        names = get_template_names()
        assert len(names) == 5
        assert "technical-guide" in names
        assert "course-tutorial" in names

    def test_get_template_path_valid(self):
        """get_template_path returns correct path for valid template."""
        path = get_template_path("technical-guide")
        assert path.exists()
        assert path.suffix == ".yaml"

    def test_get_template_path_with_underscore(self):
        """get_template_path normalizes underscores to hyphens."""
        path = get_template_path("technical_guide")
        assert path.exists()

    def test_get_template_path_invalid(self):
        """get_template_path raises for unknown template."""
        with pytest.raises(FileNotFoundError, match="not found"):
            get_template_path("nonexistent-template")


# =============================================================================
# Template Loading Tests
# =============================================================================

class TestTemplateLoading:
    """Test loading template YAML files."""

    def test_load_template_returns_dict(self):
        """load_template returns a dict with expected keys."""
        template = load_template("technical-guide")
        
        assert isinstance(template, dict)
        assert "name" in template
        assert "description" in template
        assert "default_sections" in template

    def test_load_all_templates_valid(self):
        """All templates should load without errors."""
        for name in get_template_names():
            template = load_template(name)
            assert template["name"] == name
            assert "default_sections" in template


# =============================================================================
# Template Application Tests
# =============================================================================

class TestTemplateApplication:
    """Test applying templates to create SkillSpec."""

    def test_apply_technical_guide_template(self):
        """apply_template creates valid SkillSpec from technical-guide."""
        spec = apply_template("technical-guide", skill_name="my-api-docs")
        
        assert isinstance(spec, SkillSpec)
        assert spec.name == "my-api-docs"
        assert spec.template_type == "technical-guide"
        assert len(spec.sections) > 0
        assert len(spec.references) > 0  # technical-guide has default_references
        spec.validate()

    def test_apply_course_tutorial_template(self):
        """apply_template creates valid SkillSpec from course-tutorial."""
        spec = apply_template(
            "course-tutorial",
            skill_name="Python 入门课程",
            skill_description="Python 基础教程"
        )
        
        assert spec.name == "python-入门课程"  # slugified
        assert spec.description == "Python 基础教程"
        assert any("课程摘要" in s.title for s in spec.sections)
        assert any("关键要点" in s.title for s in spec.sections)
        spec.validate()

    def test_apply_workflow_skill_template(self):
        """apply_template creates valid SkillSpec from workflow-skill."""
        spec = apply_template("workflow-skill")
        
        assert spec.template_type == "workflow-skill"
        assert any("About" in s.title for s in spec.sections)
        assert any("Process" in s.title for s in spec.sections)
        assert len(spec.scripts) > 0  # workflow-skill has default_scripts
        spec.validate()

    def test_apply_brand_enterprise_template(self):
        """apply_template creates valid SkillSpec from brand-enterprise."""
        spec = apply_template("brand-enterprise", skill_name="Acme Brand")
        
        assert spec.template_type == "brand-enterprise"
        assert len(spec.assets) > 0  # brand-enterprise has default_assets
        assert len(spec.scripts) == 0  # brand-enterprise has no scripts
        spec.validate()

    def test_apply_tool_utility_template(self):
        """apply_template creates valid SkillSpec from tool-utility."""
        spec = apply_template("tool-utility")
        
        assert spec.template_type == "tool-utility"
        assert any("Quick Start" in s.title for s in spec.sections)
        assert any("Best Practices" in s.title for s in spec.sections)
        assert len(spec.scripts) > 0
        spec.validate()

    def test_apply_template_preserves_scraped_data(self):
        """apply_template stores scraped_data in source_config."""
        scraped = {"name": "test", "pages": [{"url": "https://example.com"}]}
        spec = apply_template("technical-guide", scraped_data=scraped)
        
        assert spec.source_config == scraped

    def test_apply_template_auto_generates_name(self):
        """apply_template generates name from template if not provided."""
        spec = apply_template("course-tutorial")
        
        assert spec.name == "untitled-course-tutorial"


# =============================================================================
# Section Structure Tests
# =============================================================================

class TestSectionStructure:
    """Test that templates create proper section hierarchies."""

    def test_technical_guide_has_nested_sections(self):
        """technical-guide should have Process with subsections."""
        spec = apply_template("technical-guide")
        
        process_section = next(
            (s for s in spec.sections if "Process" in s.title), None
        )
        assert process_section is not None
        assert len(process_section.subsections) >= 3  # Phase 1, 2, 3

    def test_sections_are_proper_instances(self):
        """All sections should be SectionSpec instances."""
        spec = apply_template("technical-guide")
        
        for section in spec.sections:
            assert isinstance(section, SectionSpec)
            for sub in section.subsections:
                assert isinstance(sub, SectionSpec)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
