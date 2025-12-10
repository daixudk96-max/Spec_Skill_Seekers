#!/usr/bin/env python3
"""
Slash Command Configurators for Skill Seekers

仿照 OpenSpec 的架构，为多种 AI 编程助手生成 `/skill-seekers-*` 工作流。
支持 20+ AI 工具，包括 Antigravity、Claude Code、Cursor、Codex 等。

核心设计：让 AI 编程助手本身承担内容增强角色，替代外部 API 调用。
"""

from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources  # type: ignore


# =============================================================================
# 常量定义
# =============================================================================

# Slash 命令标识
SLASH_COMMAND_IDS: Sequence[str] = ("proposal", "apply", "archive")

# 模板标记（用于标识生成的内容边界）
SKILL_SEEKERS_MARKERS = {
    "start": "<!-- SKILL_SEEKERS:START -->",
    "end": "<!-- SKILL_SEEKERS:END -->",
}

# 与 OpenSpec 对齐的工具清单（名称保持一致，便于用户迁移）
AI_TOOLS: List[Dict[str, object]] = [
    {"name": "Amazon Q Developer", "value": "amazon-q", "available": True, "success_label": "Amazon Q Developer"},
    {"name": "Antigravity", "value": "antigravity", "available": True, "success_label": "Antigravity"},
    {"name": "Auggie (Augment CLI)", "value": "auggie", "available": True, "success_label": "Auggie"},
    {"name": "Claude Code", "value": "claude", "available": True, "success_label": "Claude Code"},
    {"name": "Cline", "value": "cline", "available": True, "success_label": "Cline"},
    {"name": "Codex", "value": "codex", "available": True, "success_label": "Codex"},
    {"name": "CodeBuddy Code (CLI)", "value": "codebuddy", "available": True, "success_label": "CodeBuddy Code"},
    {"name": "CoStrict", "value": "costrict", "available": True, "success_label": "CoStrict"},
    {"name": "Crush", "value": "crush", "available": True, "success_label": "Crush"},
    {"name": "Cursor", "value": "cursor", "available": True, "success_label": "Cursor"},
    {"name": "Factory", "value": "factory", "available": True, "success_label": "Factory"},
    {"name": "Gemini CLI", "value": "gemini", "available": True, "success_label": "Gemini CLI"},
    {"name": "GitHub Copilot CLI", "value": "copilot", "available": True, "success_label": "GitHub Copilot CLI"},
    {"name": "Goose", "value": "goose", "available": True, "success_label": "Goose"},
    {"name": "JetBrains AI", "value": "jetbrains", "available": True, "success_label": "JetBrains AI"},
    {"name": "Kilo", "value": "kilo", "available": True, "success_label": "Kilo"},
    {"name": "RooCode", "value": "roocode", "available": True, "success_label": "RooCode"},
    {"name": "Trae (Bytedance)", "value": "trae", "available": True, "success_label": "Trae"},
    {"name": "VSCode Copilot", "value": "vscode", "available": True, "success_label": "VSCode Copilot"},
    {"name": "Windsurf", "value": "windsurf", "available": True, "success_label": "Windsurf"},
    {"name": "Zed", "value": "zed", "available": True, "success_label": "Zed"},
]


# =============================================================================
# 配置器基类
# =============================================================================

@dataclass
class SlashCommandConfig:
    """单个 slash 命令的配置"""
    
    command_id: str  # proposal, apply, archive
    file_path: Path  # 工作流文件路径
    content: str     # 工作流文件内容


class SlashCommandConfigurator(ABC):
    """
    Slash 命令配置器基类
    
    每个 AI 工具需要实现自己的配置器子类，定义：
    - 工作流文件存放目录
    - 文件命名规则
    - 内容包装方式（YAML frontmatter 等）
    """
    
    tool_id: str = ""
    tool_name: str = ""
    
    def __init__(self, project_path: Path):
        """
        Args:
            project_path: 项目根目录路径
        """
        self.project_path = project_path
    
    @abstractmethod
    def get_workflow_dir(self) -> Path:
        """返回工作流文件存放目录"""
        pass
    
    @abstractmethod
    def get_workflow_filename(self, command_id: str) -> str:
        """返回工作流文件名"""
        pass
    
    def get_workflow_path(self, command_id: str) -> Path:
        """返回工作流文件完整路径"""
        return self.get_workflow_dir() / self.get_workflow_filename(command_id)
    
    def wrap_content(self, command_id: str, raw_content: str) -> str:
        """
        包装原始模板内容
        
        子类可重写此方法添加 YAML frontmatter 或其他格式
        """
        return (
            f"---\n"
            f"description: skill-seekers-{command_id} workflow\n"
            f"---\n"
            f"{SKILL_SEEKERS_MARKERS['start']}\n"
            f"{raw_content}\n"
            f"{SKILL_SEEKERS_MARKERS['end']}\n"
        )
    
    def load_template(self, command_id: str) -> str:
        """从包内加载模板内容"""
        template_pkg = "skill_seekers.cli.slash_templates"
        template_file = f"{command_id}.md"
        
        try:
            # Python 3.9+
            template_path = resources.files(template_pkg).joinpath(template_file)
            return template_path.read_text(encoding="utf-8")
        except (AttributeError, TypeError):
            # Python 3.7-3.8 fallback
            with resources.open_text(template_pkg, template_file) as f:
                return f.read()
    
    def generate_configs(self) -> List[SlashCommandConfig]:
        """生成所有 slash 命令的配置"""
        configs = []
        for cmd_id in SLASH_COMMAND_IDS:
            raw_content = self.load_template(cmd_id)
            wrapped_content = self.wrap_content(cmd_id, raw_content)
            configs.append(SlashCommandConfig(
                command_id=cmd_id,
                file_path=self.get_workflow_path(cmd_id),
                content=wrapped_content,
            ))
        return configs
    
    def install(self) -> List[str]:
        """
        安装工作流文件
        
        Returns:
            创建的文件路径列表
        """
        created_files = []
        for config in self.generate_configs():
            config.file_path.parent.mkdir(parents=True, exist_ok=True)
            config.file_path.write_text(config.content, encoding="utf-8")
            created_files.append(str(config.file_path))
        return created_files
    
    def update_existing(self) -> List[str]:
        """
        更新已存在的工作流文件
        
        只更新 SKILL_SEEKERS_MARKERS 标记之间的内容。
        
        Returns:
            更新的文件路径列表
        """
        updated_files = []
        for config in self.generate_configs():
            if not config.file_path.exists():
                continue
            
            existing_content = config.file_path.read_text(encoding="utf-8")
            start_marker = SKILL_SEEKERS_MARKERS["start"]
            end_marker = SKILL_SEEKERS_MARKERS["end"]
            
            # 查找标记位置
            start_idx = existing_content.find(start_marker)
            end_idx = existing_content.find(end_marker)
            
            if start_idx == -1 or end_idx == -1:
                # 没有标记，跳过
                continue
            
            # 替换标记之间的内容
            raw_content = self.load_template(config.command_id)
            new_section = f"{start_marker}\n{raw_content}\n{end_marker}"
            new_content = (
                existing_content[:start_idx] + 
                new_section + 
                existing_content[end_idx + len(end_marker):]
            )
            
            config.file_path.write_text(new_content, encoding="utf-8")
            updated_files.append(str(config.file_path))
        
        return updated_files


# =============================================================================
# 工具特定配置器
# =============================================================================

class AntigravityConfigurator(SlashCommandConfigurator):
    """Antigravity AI 编程助手配置器"""
    
    tool_id = "antigravity"
    tool_name = "Antigravity"
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / ".agent" / "workflows"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.md"


class ClaudeConfigurator(SlashCommandConfigurator):
    """Claude Code 配置器"""
    
    tool_id = "claude"
    tool_name = "Claude Code"
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / ".claude" / "commands"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.md"


class CursorConfigurator(SlashCommandConfigurator):
    """Cursor 配置器"""
    
    tool_id = "cursor"
    tool_name = "Cursor"
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / ".cursor" / "rules"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.mdc"
    
    def wrap_content(self, command_id: str, raw_content: str) -> str:
        """Cursor 使用 .mdc 格式"""
        return (
            f"---\n"
            f"description: skill-seekers-{command_id} workflow\n"
            f"globs:\n"
            f"alwaysApply: false\n"
            f"---\n"
            f"{SKILL_SEEKERS_MARKERS['start']}\n"
            f"{raw_content}\n"
            f"{SKILL_SEEKERS_MARKERS['end']}\n"
        )


class CodexConfigurator(SlashCommandConfigurator):
    """Codex CLI 配置器"""
    
    tool_id = "codex"
    tool_name = "Codex"
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / ".codex" / "commands"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.md"


class ClineConfigurator(SlashCommandConfigurator):
    """Cline 配置器"""
    
    tool_id = "cline"
    tool_name = "Cline"
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / ".cline" / "commands"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.md"


class WindsurfConfigurator(SlashCommandConfigurator):
    """Windsurf 配置器"""
    
    tool_id = "windsurf"
    tool_name = "Windsurf"
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / ".windsurf" / "rules"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.md"


class VSCodeCopilotConfigurator(SlashCommandConfigurator):
    """VSCode Copilot 配置器"""
    
    tool_id = "vscode"
    tool_name = "VSCode Copilot"
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / ".github"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.instructions.md"


class GenericConfigurator(SlashCommandConfigurator):
    """通用配置器（用于大多数工具）"""
    
    def __init__(self, project_path: Path, tool_id: str, tool_name: str):
        super().__init__(project_path)
        self.tool_id = tool_id
        self.tool_name = tool_name
    
    def get_workflow_dir(self) -> Path:
        return self.project_path / f".{self.tool_id}" / "commands"
    
    def get_workflow_filename(self, command_id: str) -> str:
        return f"skill-seekers-{command_id}.md"


# =============================================================================
# 配置器工厂
# =============================================================================

# 工具 ID 到配置器类的映射
_CONFIGURATOR_MAP: Dict[str, type] = {
    "antigravity": AntigravityConfigurator,
    "claude": ClaudeConfigurator,
    "cursor": CursorConfigurator,
    "codex": CodexConfigurator,
    "cline": ClineConfigurator,
    "windsurf": WindsurfConfigurator,
    "vscode": VSCodeCopilotConfigurator,
}


def get_configurator(tool_id: str, project_path: Path) -> SlashCommandConfigurator:
    """
    获取指定工具的配置器实例
    
    Args:
        tool_id: 工具标识（如 "antigravity", "claude"）
        project_path: 项目根目录
        
    Returns:
        对应的配置器实例
    """
    configurator_cls = _CONFIGURATOR_MAP.get(tool_id)
    if configurator_cls:
        return configurator_cls(project_path)
    
    # 对于未明确定义的工具，使用通用配置器
    tool_info = next((t for t in AI_TOOLS if t["value"] == tool_id), None)
    tool_name = str(tool_info["name"]) if tool_info else tool_id.title()
    return GenericConfigurator(project_path, tool_id, tool_name)


def get_configurators(tool_ids: List[str], project_path: Path) -> List[SlashCommandConfigurator]:
    """
    批量获取配置器实例
    
    Args:
        tool_ids: 工具标识列表
        project_path: 项目根目录
        
    Returns:
        配置器实例列表
    """
    return [get_configurator(tid, project_path) for tid in tool_ids]


def get_available_tool_ids() -> List[str]:
    """获取所有可用的工具 ID 列表"""
    return [str(t["value"]) for t in AI_TOOLS if t.get("available")]


def get_tool_by_id(tool_id: str) -> Optional[Dict[str, object]]:
    """根据 ID 获取工具信息"""
    return next((t for t in AI_TOOLS if t["value"] == tool_id), None)


# =============================================================================
# CLI 辅助函数
# =============================================================================

def resolve_tools(tools_arg: Optional[str], available: List[Dict[str, object]]) -> List[str]:
    """
    解析工具选择参数
    
    支持三种模式：
    1. "all" - 选择所有可用工具
    2. 逗号分隔列表 - 如 "antigravity,claude,cursor"
    3. 空值 - 进入交互式选择模式
    
    Args:
        tools_arg: --tools 参数值
        available: 可用工具列表
        
    Returns:
        选中的工具 ID 列表
    """
    if tools_arg:
        if tools_arg.strip().lower() == "all":
            return [str(t["value"]) for t in available if t.get("available")]
        return [t.strip() for t in tools_arg.split(",") if t.strip()]
    
    # 交互模式：列出可用工具并允许输入索引
    print("Select tools (comma-separated indices or names, empty = all available):")
    for idx, tool in enumerate(available):
        status = "✅" if tool.get("available") else "⏸"
        print(f"  [{idx}] {status} {tool['name']} ({tool['value']})")
    
    raw = input("Tools: ").strip()
    if not raw:
        return [str(t["value"]) for t in available if t.get("available")]
    
    selected: List[str] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if token.isdigit():
            idx = int(token)
            if 0 <= idx < len(available) and available[idx].get("available"):
                selected.append(str(available[idx]["value"]))
        else:
            selected.append(token)
    return selected


def handle_init_command(
    tools_arg: Optional[str],
    path_arg: Optional[str],
) -> int:
    """
    处理 skill-seekers init 命令
    
    Args:
        tools_arg: --tools 参数值
        path_arg: --path 参数值
        
    Returns:
        退出码（0 表示成功）
    """
    project_path = Path(path_arg) if path_arg else Path.cwd()
    
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}", file=sys.stderr)
        return 1
    
    tool_ids = resolve_tools(tools_arg, AI_TOOLS)
    
    if not tool_ids:
        print("No tools selected; nothing to do.", file=sys.stderr)
        return 1
    
    configurators = get_configurators(tool_ids, project_path)
    
    created: List[str] = []
    for configurator in configurators:
        try:
            created.extend(configurator.install())
        except Exception as e:
            print(f"Warning: Failed to install for {configurator.tool_name}: {e}", file=sys.stderr)
    
    if not created:
        print("No workflows created.", file=sys.stderr)
        return 1
    
    print(f"✅ Created {len(created)} workflow files:")
    for path in created:
        print(f"  - {path}")
    
    return 0


def handle_update_command(
    tools_arg: Optional[str],
    path_arg: Optional[str],
) -> int:
    """
    处理 skill-seekers update 命令
    
    Args:
        tools_arg: --tools 参数值
        path_arg: --path 参数值
        
    Returns:
        退出码（0 表示成功）
    """
    project_path = Path(path_arg) if path_arg else Path.cwd()
    
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}", file=sys.stderr)
        return 1
    
    tool_ids = resolve_tools(tools_arg, AI_TOOLS) if tools_arg else get_available_tool_ids()
    configurators = get_configurators(tool_ids, project_path)
    
    updated: List[str] = []
    for configurator in configurators:
        try:
            updated.extend(configurator.update_existing())
        except Exception as e:
            print(f"Warning: Failed to update for {configurator.tool_name}: {e}", file=sys.stderr)
    
    if not updated:
        print("No existing workflows found to update.", file=sys.stderr)
        return 1
    
    print(f"✅ Updated {len(updated)} workflow files:")
    for path in updated:
        print(f"  - {path}")
    
    return 0
