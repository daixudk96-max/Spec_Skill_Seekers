#!/usr/bin/env python3
"""
Tests for Slash Command System

Covers:
- Template loading and existence
- Configurator logic
- CLI init command
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources  # type: ignore


# =============================================================================
# 模板存在性测试
# =============================================================================

TEMPLATE_PACKAGE = "skill_seekers.cli.slash_templates"


@pytest.mark.parametrize("template_name", ["proposal.md", "apply.md", "archive.md"])
def test_templates_exist(template_name: str) -> None:
    """验证三个模板文件存在"""
    template_path = resources.files(TEMPLATE_PACKAGE).joinpath(template_name)
    assert template_path.is_file(), f"Template {template_name} not found"


@pytest.mark.parametrize(
    ("template_name", "expected_phrase"),
    [
        ("proposal.md", "--output-raw"),
        ("apply.md", "apply-spec"),
        ("archive.md", "package"),
    ],
)
def test_templates_contain_core_guidance(template_name: str, expected_phrase: str) -> None:
    """验证模板包含核心指导内容"""
    content = resources.files(TEMPLATE_PACKAGE).joinpath(template_name).read_text(encoding="utf-8")
    assert expected_phrase in content, f"Template {template_name} missing '{expected_phrase}'"


def test_templates_reference_ai_assistant_role() -> None:
    """确保模板强调由 AI 助手承担增强角色"""
    for name in ("proposal.md", "apply.md", "archive.md"):
        content = resources.files(TEMPLATE_PACKAGE).joinpath(name).read_text(encoding="utf-8")
        assert "AI 编程助手" in content, f"Template {name} missing AI assistant role"


# =============================================================================
# 配置器测试
# =============================================================================

class TestConfigurators:
    """Test configurator classes and factory functions."""

    def test_ai_tools_list_not_empty(self) -> None:
        """AI_TOOLS list should contain tools."""
        from skill_seekers.cli.configurators import AI_TOOLS
        assert len(AI_TOOLS) >= 20
        assert all("name" in t and "value" in t for t in AI_TOOLS)

    def test_get_available_tool_ids(self) -> None:
        """get_available_tool_ids returns available tools."""
        from skill_seekers.cli.configurators import get_available_tool_ids
        tool_ids = get_available_tool_ids()
        assert "antigravity" in tool_ids
        assert "claude" in tool_ids
        assert "cursor" in tool_ids

    def test_get_configurator_known_tool(self, tmp_path: Path) -> None:
        """get_configurator returns appropriate configurator for known tools."""
        from skill_seekers.cli.configurators import get_configurator, AntigravityConfigurator
        
        configurator = get_configurator("antigravity", tmp_path)
        assert isinstance(configurator, AntigravityConfigurator)
        assert configurator.tool_id == "antigravity"

    def test_get_configurator_unknown_tool(self, tmp_path: Path) -> None:
        """get_configurator returns GenericConfigurator for unknown tools."""
        from skill_seekers.cli.configurators import get_configurator, GenericConfigurator
        
        configurator = get_configurator("unknown-tool", tmp_path)
        assert isinstance(configurator, GenericConfigurator)

    def test_antigravity_workflow_dir(self, tmp_path: Path) -> None:
        """Antigravity configurator uses .agent/workflows directory."""
        from skill_seekers.cli.configurators import AntigravityConfigurator
        
        configurator = AntigravityConfigurator(tmp_path)
        assert configurator.get_workflow_dir() == tmp_path / ".agent" / "workflows"

    def test_claude_workflow_dir(self, tmp_path: Path) -> None:
        """Claude configurator uses .claude/commands directory."""
        from skill_seekers.cli.configurators import ClaudeConfigurator
        
        configurator = ClaudeConfigurator(tmp_path)
        assert configurator.get_workflow_dir() == tmp_path / ".claude" / "commands"

    def test_cursor_workflow_uses_mdc_extension(self, tmp_path: Path) -> None:
        """Cursor configurator uses .mdc extension."""
        from skill_seekers.cli.configurators import CursorConfigurator
        
        configurator = CursorConfigurator(tmp_path)
        filename = configurator.get_workflow_filename("proposal")
        assert filename.endswith(".mdc")


# =============================================================================
# CLI 命令测试
# =============================================================================

class TestInitCommand:
    """Test init CLI command."""

    def test_handle_init_command_creates_files(self, tmp_path: Path) -> None:
        """handle_init_command creates workflow files."""
        from skill_seekers.cli.configurators import handle_init_command
        
        result = handle_init_command("antigravity", str(tmp_path))
        assert result == 0
        
        # 验证文件已创建
        workflow_dir = tmp_path / ".agent" / "workflows"
        assert workflow_dir.exists()
        assert (workflow_dir / "skill-seekers-proposal.md").exists()
        assert (workflow_dir / "skill-seekers-apply.md").exists()
        assert (workflow_dir / "skill-seekers-archive.md").exists()

    def test_handle_init_command_all_tools(self, tmp_path: Path) -> None:
        """handle_init_command with 'all' creates files for all tools."""
        from skill_seekers.cli.configurators import handle_init_command
        
        result = handle_init_command("all", str(tmp_path))
        assert result == 0
        
        # 验证多个工具目录已创建
        assert (tmp_path / ".agent" / "workflows").exists()
        assert (tmp_path / ".claude" / "commands").exists()


class TestUpdateCommand:
    """Test update CLI command."""

    def test_handle_update_command_no_files(self, tmp_path: Path) -> None:
        """handle_update_command returns 1 when no files exist."""
        from skill_seekers.cli.configurators import handle_update_command
        
        result = handle_update_command("antigravity", str(tmp_path))
        assert result == 1  # No files to update

    def test_handle_update_command_updates_existing(self, tmp_path: Path) -> None:
        """handle_update_command updates existing files."""
        from skill_seekers.cli.configurators import (
            handle_init_command, 
            handle_update_command,
            SKILL_SEEKERS_MARKERS,
        )
        
        # 先创建文件
        handle_init_command("antigravity", str(tmp_path))
        
        # 修改文件内容（模拟用户编辑）
        workflow_file = tmp_path / ".agent" / "workflows" / "skill-seekers-proposal.md"
        original_content = workflow_file.read_text(encoding="utf-8")
        
        # 更新
        result = handle_update_command("antigravity", str(tmp_path))
        assert result == 0
        
        # 验证文件仍包含标记
        updated_content = workflow_file.read_text(encoding="utf-8")
        assert SKILL_SEEKERS_MARKERS["start"] in updated_content
        assert SKILL_SEEKERS_MARKERS["end"] in updated_content


# =============================================================================
# 辅助函数测试
# =============================================================================

class TestResolveTools:
    """Test resolve_tools helper function."""

    def test_resolve_tools_all(self) -> None:
        """'all' returns all available tools."""
        from skill_seekers.cli.configurators import resolve_tools, AI_TOOLS
        
        result = resolve_tools("all", AI_TOOLS)
        assert len(result) >= 20
        assert "antigravity" in result

    def test_resolve_tools_comma_separated(self) -> None:
        """Comma-separated list returns specified tools."""
        from skill_seekers.cli.configurators import resolve_tools, AI_TOOLS
        
        result = resolve_tools("antigravity,claude,cursor", AI_TOOLS)
        assert result == ["antigravity", "claude", "cursor"]

    def test_resolve_tools_whitespace_handling(self) -> None:
        """Handles whitespace in tool list."""
        from skill_seekers.cli.configurators import resolve_tools, AI_TOOLS
        
        result = resolve_tools(" antigravity , claude ", AI_TOOLS)
        assert result == ["antigravity", "claude"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
