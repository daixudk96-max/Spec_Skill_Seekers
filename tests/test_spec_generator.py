#!/usr/bin/env python3
"""
Tests for Spec Generator

Covers:
- Factory methods (from_docs, from_github, from_transcript, from_unified)
- Spec generation and validation
- Template inference
- Export methods
"""

import pytest
import tempfile
from pathlib import Path

from skill_seekers.cli.spec_generator import SpecGenerator
from skill_seekers.core.skill_spec import SkillSpec


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def docs_data():
    """Sample documentation scraper output."""
    return {
        "title": "My API Documentation",
        "summary": "Complete API reference for My API",
        "pages": [
            {"url": "https://docs.example.com/api", "title": "API Reference"},
            {"url": "https://docs.example.com/guide", "title": "Getting Started"},
        ],
    }


@pytest.fixture
def github_data():
    """Sample GitHub scraper output."""
    return {
        "repo_name": "awesome-tool",
        "description": "An awesome CLI tool for developers",
        "has_cli": True,
        "readme": "# Awesome Tool\n\nA CLI tool...",
        "apis": [
            {"name": "main", "signature": "main() -> None"},
        ],
    }


@pytest.fixture
def transcript_data():
    """Sample transcript scraper output."""
    return {
        "course_name": "Python 入门课程",
        "course_description": "从零开始学 Python",
        "lessons": [
            {"title": "第一课：基础语法", "summary": "变量和数据类型"},
            {"title": "第二课：控制流", "summary": "条件和循环"},
        ],
    }


@pytest.fixture
def unified_data(docs_data, github_data):
    """Sample unified multi-source scraper output."""
    return {
        "name": "my-unified-skill",
        "description": "A skill built from multiple sources",
        "documentation": docs_data,
        "github": github_data,
    }


# =============================================================================
# Factory Method Tests
# =============================================================================

class TestFactoryMethods:
    """Test factory methods for different data sources."""

    def test_from_docs_scraper(self, docs_data):
        """from_docs_scraper creates generator with technical-guide template."""
        gen = SpecGenerator.from_docs_scraper(docs_data)
        
        assert gen.template_type == "technical-guide"
        assert "documentation" in gen.scraped_data

    def test_from_github_scraper(self, github_data):
        """from_github_scraper creates generator with inferred template."""
        gen = SpecGenerator.from_github_scraper(github_data)
        
        # has_cli=True should trigger tool-utility
        assert gen.template_type == "tool-utility"
        assert "github" in gen.scraped_data

    def test_from_transcript_scraper(self, transcript_data):
        """from_transcript_scraper uses course-tutorial template."""
        gen = SpecGenerator.from_transcript_scraper(transcript_data)
        
        assert gen.template_type == "course-tutorial"
        assert "lessons" in gen.scraped_data

    def test_from_unified(self, unified_data):
        """from_unified accepts combined data and infers template."""
        gen = SpecGenerator.from_unified(unified_data)
        
        assert gen.scraped_data == unified_data
        # Should infer technical-guide (github without is_tool)
        assert gen.template_type in ["technical-guide", "tool-utility"]


# =============================================================================
# Generation Tests
# =============================================================================

class TestGeneration:
    """Test SkillSpec generation."""

    def test_generate_returns_valid_spec(self, docs_data):
        """generate() returns a valid SkillSpec."""
        gen = SpecGenerator.from_docs_scraper(docs_data, name="test-docs")
        spec = gen.generate()
        
        assert isinstance(spec, SkillSpec)
        spec.validate()
        assert spec.name == "test-docs"
        assert spec.template_type == "technical-guide"

    def test_generate_infers_name(self, github_data):
        """generate() infers name from scraped data."""
        gen = SpecGenerator.from_github_scraper(github_data)
        spec = gen.generate()
        
        assert spec.name == "awesome-tool"

    def test_generate_infers_description(self, github_data):
        """generate() infers description from scraped data."""
        gen = SpecGenerator.from_github_scraper(github_data)
        spec = gen.generate()
        
        assert spec.description == "An awesome CLI tool for developers"

    def test_generate_adds_source_references(self, docs_data):
        """generate() adds source-specific references."""
        gen = SpecGenerator.from_docs_scraper(docs_data)
        spec = gen.generate()
        
        filenames = [r.filename for r in spec.references]
        assert "official_docs.md" in filenames

    def test_generate_adds_source_scripts(self, github_data):
        """generate() adds source-specific scripts."""
        gen = SpecGenerator.from_github_scraper(github_data)
        spec = gen.generate()
        
        filenames = [s.filename for s in spec.scripts]
        assert "sync_repo.py" in filenames

    def test_generate_cached(self, docs_data):
        """generate() returns same instance on repeated calls."""
        gen = SpecGenerator.from_docs_scraper(docs_data)
        spec1 = gen.generate()
        spec2 = gen.generate()
        
        assert spec1 is spec2


# =============================================================================
# Template Inference Tests
# =============================================================================

class TestTemplateInference:
    """Test automatic template type inference."""

    def test_infer_course_tutorial(self):
        """Lessons data triggers course-tutorial."""
        data = {"lessons": [{"title": "Lesson 1"}]}
        template = SpecGenerator._infer_template(data)
        assert template == "course-tutorial"

    def test_infer_tool_utility(self):
        """CLI tool triggers tool-utility."""
        data = {"github": {"has_cli": True}}
        template = SpecGenerator._infer_template(data)
        assert template == "tool-utility"

    def test_infer_brand_enterprise(self):
        """Brand data triggers brand-enterprise."""
        data = {"brand": {"colors": ["#000"]}}
        template = SpecGenerator._infer_template(data)
        assert template == "brand-enterprise"

    def test_infer_workflow_skill(self):
        """Meta-skill triggers workflow-skill."""
        data = {"is_meta_skill": True}
        template = SpecGenerator._infer_template(data)
        assert template == "workflow-skill"

    def test_infer_default(self):
        """Unknown data falls back to technical-guide."""
        data = {"random": "data"}
        template = SpecGenerator._infer_template(data)
        assert template == "technical-guide"


# =============================================================================
# Export Tests
# =============================================================================

class TestExport:
    """Test export methods."""

    def test_save_and_load_yaml(self, docs_data):
        """save() and load() work with YAML files."""
        gen = SpecGenerator.from_docs_scraper(docs_data, name="test-save")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "spec.yaml"
            gen.save(path)
            
            loaded = SpecGenerator.load(path)
            assert loaded.name == "test-save"
            loaded.validate()

    def test_save_and_load_json(self, github_data):
        """save() and load() work with JSON files."""
        gen = SpecGenerator.from_github_scraper(github_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "spec.json"
            gen.save(path)
            
            loaded = SpecGenerator.load(path)
            assert loaded.name == "awesome-tool"

    def test_export_for_review(self, docs_data):
        """export_for_review() generates markdown summary."""
        gen = SpecGenerator.from_docs_scraper(docs_data, name="review-test")
        md = gen.export_for_review()
        
        assert "# Skill Spec Review" in md
        assert "review-test" in md
        assert "technical-guide" in md
        assert "Approve this spec" in md

    def test_export_spec_file_adds_extension(self, docs_data):
        """export_spec_file() adds .yaml extension if missing."""
        gen = SpecGenerator.from_docs_scraper(docs_data, name="ext-test")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "spec"  # No extension
            gen.export_spec_file(path)
            
            assert (Path(tmpdir) / "spec.yaml").exists()


# =============================================================================
# Segmented Summary Tests
# =============================================================================

class TestSegmentedSummary:
    """Test segmented summary support for transcript workflows."""

    @pytest.fixture
    def sample_segmented_summary(self):
        """Sample segmented summary data."""
        return {
            "version": "1.0",
            "source_file": "第八章_原文.txt",
            "total_segments": 2,
            "segments": [
                {
                    "id": "1",
                    "timestamp": "00:00 - 05:00",
                    "marker": "好",
                    "reason": "讲者使用'好'开始新话题",
                    "summary_full": "详细总结内容...",
                    "summary_brief": "简短摘要",
                    "key_points": ["要点1", "要点2"],
                    "examples_simplified": ["例子1"],
                    "homophone_notes": [],
                    "subsegments": [],
                },
                {
                    "id": "2",
                    "timestamp": "05:00 - 10:00",
                    "marker": "下一个",
                    "reason": "话题转换标志",
                    "summary_full": "第二段详细总结...",
                    "summary_brief": "第二段摘要",
                    "key_points": ["要点3"],
                    "examples_simplified": [],
                    "homophone_notes": ["的/得"],
                    "subsegments": [
                        {"id": "2.1", "topic": "子话题", "summary": "子总结"}
                    ],
                },
            ],
            "metadata": {
                "generated_by": "AI_assistant",
                "generated_at": "2024-01-01T00:00:00Z",
            },
        }

    def test_load_segmented_summary_valid(self, sample_segmented_summary):
        """load_segmented_summary() loads valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "segmented_summary.json"
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sample_segmented_summary, f)
            
            result = SpecGenerator.load_segmented_summary(path)
            
            assert result["version"] == "1.0"
            assert result["total_segments"] == 2
            assert len(result["segments"]) == 2

    def test_load_segmented_summary_missing_file(self):
        """load_segmented_summary() returns empty dict for missing file."""
        result = SpecGenerator.load_segmented_summary(Path("/nonexistent/path.json"))
        assert result == {}

    def test_load_segmented_summary_invalid_json(self):
        """load_segmented_summary() returns empty dict for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            path.write_text("not valid json {{{", encoding="utf-8")
            
            result = SpecGenerator.load_segmented_summary(path)
            assert result == {}

    def test_from_transcript_with_segmented_summary(
        self, transcript_data, sample_segmented_summary
    ):
        """from_transcript_scraper() accepts segmented_summary parameter."""
        gen = SpecGenerator.from_transcript_scraper(
            transcript_data,
            name="test-transcript",
            segmented_summary=sample_segmented_summary,
        )
        
        assert gen.segmented_summary == sample_segmented_summary
        assert gen.template_type == "course-tutorial"

    def test_generate_includes_segments(
        self, transcript_data, sample_segmented_summary
    ):
        """generate() merges segmented summary into spec data."""
        gen = SpecGenerator.from_transcript_scraper(
            transcript_data,
            name="test-segments",
            segmented_summary=sample_segmented_summary,
        )
        
        spec = gen.generate()
        
        # Spec should be valid
        assert spec.name == "test-segments"
        spec.validate()

    def test_generate_without_segmented_summary_backward_compatible(
        self, transcript_data
    ):
        """generate() works without segmented summary (backward compatibility)."""
        gen = SpecGenerator.from_transcript_scraper(transcript_data, name="no-segments")
        spec = gen.generate()
        
        assert spec.name == "no-segments"
        spec.validate()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
