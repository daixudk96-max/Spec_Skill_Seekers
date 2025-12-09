#!/usr/bin/env python3
"""
Tests for ContentSynthesizer

Covers:
- Section content generation (LLM and fallback modes)
- Reference content generation
- Source text extraction from various source_config formats
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch
import os

from skill_seekers.core.content_synthesizer import ContentSynthesizer
from skill_seekers.core.skill_spec import (
    ReferenceSpec,
    SectionSpec,
    SkillSpec,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_source_config():
    """Source config with transcript-style content."""
    return {
        "lessons": {
            "lessons": {
                "course_name": "测试课程",
                "course_description": "测试描述",
                "content": """这是课程内容的第一段，讲述了直播行业的发展。

直播行业是一个新兴行业，分别是主播、运营、中控三个关键岗位。

核心概念就是流量的获取和转化，意味着我们需要掌握内容制作能力。

关键知识点包含：用户运营、内容策划、数据分析。"""
            }
        }
    }


@pytest.fixture
def sample_spec(sample_source_config):
    """Create a sample SkillSpec with source_config."""
    spec = SkillSpec(
        name="test-skill",
        description="Test skill for unit tests",
        sections=[
            SectionSpec(
                title="## 📝 课程摘要",
                purpose="2-3段课程概述",
                expected_content=["课程背景", "核心主题"],
            ),
            SectionSpec(
                title="## 🎯 关键要点",
                purpose="核心概念列表",
                expected_content=["核心概念", "关键知识点"],
            ),
        ],
        references=[
            ReferenceSpec(
                filename="concepts.md",
                purpose="详细概念解释",
                content_sources=["lessons"],
            ),
        ],
    )
    spec.source_config = sample_source_config
    return spec


@pytest.fixture
def section_summary():
    """Sample summary section."""
    return SectionSpec(
        title="## 📝 课程摘要",
        purpose="2-3段课程概述",
        expected_content=["课程背景", "核心主题"],
    )


@pytest.fixture
def section_key_points():
    """Sample key points section."""
    return SectionSpec(
        title="## 🎯 关键要点",
        purpose="核心概念列表",
        expected_content=["核心概念", "关键知识点"],
    )


@pytest.fixture
def section_exercise():
    """Sample exercise section."""
    return SectionSpec(
        title="## 📋 实践练习",
        purpose="练习题",
        expected_content=["练习题目", "参考答案"],
    )


# =============================================================================
# Initialization Tests
# =============================================================================

class TestContentSynthesizerInit:
    """Test ContentSynthesizer initialization."""

    def test_init_without_api_key(self, sample_spec, sample_source_config):
        """Synthesizer initializes with use_llm=False when no API key."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=True)
            assert synth.use_llm is False
    
    def test_init_with_llm_disabled(self, sample_spec, sample_source_config):
        """Synthesizer respects use_llm=False."""
        synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=False)
        assert synth.use_llm is False
    
    def test_init_empty_source_config(self, sample_spec):
        """Synthesizer handles empty source_config."""
        synth = ContentSynthesizer(sample_spec, {}, use_llm=False)
        assert synth._get_source_text() == "{}"


# =============================================================================
# Source Text Extraction Tests
# =============================================================================

class TestSourceTextExtraction:
    """Test _get_source_text method."""

    def test_extract_from_nested_lessons(self, sample_spec, sample_source_config):
        """Extract content from nested lessons structure."""
        synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=False)
        text = synth._get_source_text()
        assert "直播行业" in text
        assert "核心概念" in text
    
    def test_extract_from_flat_content(self, sample_spec):
        """Extract content from flat content field."""
        source = {"content": "这是直接内容"}
        synth = ContentSynthesizer(sample_spec, source, use_llm=False)
        assert synth._get_source_text() == "这是直接内容"
    
    def test_extract_from_transcript(self, sample_spec):
        """Extract content from transcript field."""
        source = {"transcript": "这是转录文本"}
        synth = ContentSynthesizer(sample_spec, source, use_llm=False)
        assert synth._get_source_text() == "这是转录文本"


# =============================================================================
# Fallback Content Generation Tests
# =============================================================================

class TestFallbackContentGeneration:
    """Test deterministic fallback content generation."""

    def test_summary_section_fallback(self, sample_spec, sample_source_config, section_summary):
        """Summary section uses first N characters as fallback."""
        synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=False)
        content = synth.synthesize_section_content(section_summary)
        
        assert "课程内容" in content or "直播行业" in content
        assert "原始材料" in content  # Fallback marker
    
    def test_key_points_fallback(self, sample_spec, sample_source_config, section_key_points):
        """Key points section extracts bullet-style content."""
        synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=False)
        content = synth.synthesize_section_content(section_key_points)
        
        # Should contain extracted content or fallback summary
        assert len(content) > 0
    
    def test_exercise_section_placeholder(self, sample_spec, sample_source_config, section_exercise):
        """Exercise section shows LLM-required placeholder."""
        synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=False)
        content = synth.synthesize_section_content(section_exercise)
        
        assert "LLM" in content
        assert "ANTHROPIC_API_KEY" in content
    
    def test_empty_source_placeholder(self, sample_spec, section_summary):
        """Section with no source shows placeholder."""
        synth = ContentSynthesizer(sample_spec, {}, use_llm=False)
        content = synth.synthesize_section_content(section_summary)
        
        assert "无可用源内容" in content or "{}" in content


# =============================================================================
# Reference Content Generation Tests
# =============================================================================

class TestReferenceContentGeneration:
    """Test reference file content generation."""

    def test_reference_fallback_content(self, sample_spec, sample_source_config):
        """Reference file gets fallback content."""
        synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=False)
        ref = ReferenceSpec(filename="test.md", purpose="Test purpose")
        
        content = synth.synthesize_reference_content(ref)
        
        assert "内容" in content
        assert len(content) > 50
    
    def test_reference_empty_source(self, sample_spec):
        """Reference with no source shows message."""
        synth = ContentSynthesizer(sample_spec, {}, use_llm=False)
        ref = ReferenceSpec(filename="empty.md", purpose="Empty test")
        
        content = synth.synthesize_reference_content(ref)
        
        assert "无可用" in content


# =============================================================================
# LLM Content Generation Tests (Mocked)
# =============================================================================

class TestLLMContentGeneration:
    """Test LLM-based content generation with mocked API."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_llm_generation_success(self, sample_spec, sample_source_config, section_summary):
        """LLM generation returns content when API succeeds."""
        with patch("skill_seekers.core.content_synthesizer.anthropic") as mock_anthropic:
            # Setup mock
            mock_client = MagicMock()
            mock_anthropic.Anthropic.return_value = mock_client
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text="这是LLM生成的摘要内容")]
            mock_client.messages.create.return_value = mock_message
            
            synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=True)
            content = synth.synthesize_section_content(section_summary)
            
            assert "LLM生成的摘要" in content
            mock_client.messages.create.assert_called_once()
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_llm_generation_fallback_on_error(self, sample_spec, sample_source_config, section_summary):
        """Falls back to deterministic when LLM fails."""
        with patch("skill_seekers.core.content_synthesizer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.Anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("API Error")
            
            synth = ContentSynthesizer(sample_spec, sample_source_config, use_llm=True)
            content = synth.synthesize_section_content(section_summary)
            
            # Should fall back to deterministic content
            assert len(content) > 0
            assert "原始材料" in content or "直播" in content


# =============================================================================
# Integration with UnifiedSkillBuilder Tests
# =============================================================================

class TestUnifiedSkillBuilderIntegration:
    """Test integration with UnifiedSkillBuilder."""

    def test_builder_initializes_synthesizer(self, sample_spec, sample_source_config):
        """UnifiedSkillBuilder initializes ContentSynthesizer."""
        from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder
        
        sample_spec.source_config = sample_source_config
        
        config = {"name": "test", "description": "test", "sources": []}
        builder = UnifiedSkillBuilder(
            config=config,
            scraped_data={},
            skill_spec=sample_spec,
            use_llm=False,
        )
        
        # Trigger initialization
        builder.skill_spec = sample_spec
        builder.build_from_spec()
        
        assert builder.content_synthesizer is not None
        assert builder.content_synthesizer.use_llm is False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
