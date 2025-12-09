#!/usr/bin/env python3
"""
Tests for Spec Feedback Handling

Covers:
- handle_spec_rejection: Re-scrape config generation
- apply_feedback_to_spec: Section modifications
- prompt_user_feedback: Non-interactive mode
"""

import pytest
from copy import deepcopy

from skill_seekers.cli.spec_feedback import (
    apply_feedback_to_spec,
    create_feedback,
    handle_spec_rejection,
    prompt_user_feedback,
)
from skill_seekers.core.skill_spec import SectionSpec, SkillSpec, SpecFeedback


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_spec():
    """Create a sample SkillSpec for testing."""
    return SkillSpec(
        name="test-skill",
        description="A test skill for feedback testing",
        sections=[
            SectionSpec(title="## Overview", purpose="Introduction"),
            SectionSpec(title="## Getting Started", purpose="How to begin"),
            SectionSpec(title="## API Reference", purpose="API docs"),
        ],
        source_config={
            "sources": ["https://docs.example.com"],
        },
    )


# =============================================================================
# handle_spec_rejection Tests
# =============================================================================

class TestHandleSpecRejection:
    """Test handle_spec_rejection function."""

    def test_adds_additional_sources(self, sample_spec):
        """Additional sources are merged into config."""
        feedback = create_feedback(
            additional_sources=["https://github.com/example/repo"]
        )
        config = handle_spec_rejection(sample_spec, feedback)
        
        assert "https://github.com/example/repo" in config["sources"]
        assert "https://docs.example.com" in config["sources"]

    def test_adds_exclude_sections(self, sample_spec):
        """Remove sections become exclude_sections in config."""
        feedback = create_feedback(remove_sections=["API Reference"])
        config = handle_spec_rejection(sample_spec, feedback)
        
        assert "API Reference" in config["exclude_sections"]

    def test_adds_focus_sections(self, sample_spec):
        """Add sections become focus_sections in config."""
        feedback = create_feedback(add_sections=["Examples", "Troubleshooting"])
        config = handle_spec_rejection(sample_spec, feedback)
        
        assert "Examples" in config["focus_sections"]
        assert "Troubleshooting" in config["focus_sections"]

    def test_adds_focus_hints(self, sample_spec):
        """Focus hints are preserved in config."""
        feedback = create_feedback(focus_hints=["authentication", "error handling"])
        config = handle_spec_rejection(sample_spec, feedback)
        
        assert "authentication" in config["focus_hints"]
        assert "error handling" in config["focus_hints"]

    def test_preserves_rejection_reason(self, sample_spec):
        """Rejection reason is stored in config."""
        feedback = create_feedback(rejection_reason="Missing authentication docs")
        config = handle_spec_rejection(sample_spec, feedback)
        
        assert config["last_rejection_reason"] == "Missing authentication docs"

    def test_deduplicates_sources(self, sample_spec):
        """Duplicate sources are removed."""
        feedback = create_feedback(
            additional_sources=["https://docs.example.com", "https://new.com"]
        )
        config = handle_spec_rejection(sample_spec, feedback)
        
        # Should only appear once
        assert config["sources"].count("https://docs.example.com") == 1
        assert "https://new.com" in config["sources"]


# =============================================================================
# apply_feedback_to_spec Tests
# =============================================================================

class TestApplyFeedbackToSpec:
    """Test apply_feedback_to_spec function."""

    def test_removes_sections(self, sample_spec):
        """Sections matching remove_sections are removed."""
        feedback = create_feedback(remove_sections=["API Reference"])
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        titles = [s.title for s in updated.sections]
        assert "## API Reference" not in titles
        assert "## Overview" in titles  # Others preserved

    def test_removes_sections_by_keyword(self, sample_spec):
        """Sections containing keywords are removed."""
        feedback = create_feedback(remove_sections=["API"])
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        titles = [s.title for s in updated.sections]
        assert "## API Reference" not in titles

    def test_adds_new_sections(self, sample_spec):
        """New sections are added with placeholder purposes."""
        feedback = create_feedback(add_sections=["Examples"])
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        titles = [s.title for s in updated.sections]
        assert any("Examples" in t for t in titles)

    def test_adds_markdown_heading_prefix(self, sample_spec):
        """Added sections get ## prefix if not present."""
        feedback = create_feedback(add_sections=["New Section"])
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        new_section = next(s for s in updated.sections if "New Section" in s.title)
        assert new_section.title.startswith("##")

    def test_preserves_existing_heading_prefix(self, sample_spec):
        """Sections with # prefix keep their heading."""
        feedback = create_feedback(add_sections=["### Subsection"])
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        new_section = next(s for s in updated.sections if "Subsection" in s.title)
        assert new_section.title == "### Subsection"

    def test_resets_status_to_pending(self, sample_spec):
        """Status is reset to pending after feedback."""
        sample_spec.meta.status = "approved"
        feedback = create_feedback(add_sections=["Test"])
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        assert updated.meta.status == "pending"

    def test_updates_timestamp(self, sample_spec):
        """updated_at timestamp is refreshed."""
        original_updated = sample_spec.meta.updated_at
        feedback = create_feedback(add_sections=["Test"])
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        assert updated.meta.updated_at != original_updated

    def test_stores_rescrape_config(self, sample_spec):
        """Re-scrape config is stored in source_config."""
        feedback = create_feedback(
            additional_sources=["https://new.com"],
            focus_hints=["auth"],
        )
        updated = apply_feedback_to_spec(sample_spec, feedback)
        
        assert "https://new.com" in updated.source_config["sources"]
        assert "auth" in updated.source_config["focus_hints"]

    def test_does_not_modify_original(self, sample_spec):
        """Original spec is not modified."""
        original_sections_count = len(sample_spec.sections)
        feedback = create_feedback(add_sections=["New"])
        apply_feedback_to_spec(sample_spec, feedback)
        
        assert len(sample_spec.sections) == original_sections_count


# =============================================================================
# prompt_user_feedback Tests
# =============================================================================

class TestPromptUserFeedback:
    """Test prompt_user_feedback function."""

    def test_non_interactive_returns_pending(self, sample_spec):
        """Non-interactive mode returns pending feedback."""
        feedback = prompt_user_feedback(sample_spec, interactive=False)
        
        assert feedback.approved is False
        assert "Pending" in feedback.rejection_reason


# =============================================================================
# create_feedback Tests
# =============================================================================

class TestCreateFeedback:
    """Test create_feedback convenience function."""

    def test_creates_approved_feedback(self):
        """Can create approved feedback."""
        feedback = create_feedback(approved=True)
        
        assert feedback.approved is True
        assert feedback.has_changes() is False

    def test_creates_feedback_with_changes(self):
        """Can create feedback with multiple change requests."""
        feedback = create_feedback(
            approved=False,
            rejection_reason="Incomplete",
            suggested_changes=["Add more examples"],
            additional_sources=["https://api.com"],
            remove_sections=["Old Section"],
            add_sections=["New Section"],
            focus_hints=["performance"],
        )
        
        assert feedback.approved is False
        assert feedback.has_changes() is True
        assert len(feedback.suggested_changes) == 1
        assert len(feedback.additional_sources) == 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
