#!/usr/bin/env python3
"""
Core Data Types for Skill Spec

Defines the SkillSpec data structure that controls all skill output generation.
Follows the Anthropic Agent Skills Spec (v1.0, 2025-10-16).

All dataclasses support:
- JSON/YAML serialization via to_dict(), from_dict(), to_json(), from_yaml()
- Human-readable output via to_markdown()
- Field validation via validate()
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_args, get_origin, get_type_hints

try:
    import yaml
except ImportError:
    yaml = None  # YAML support is optional

T = TypeVar("T", bound="SerializableSpec")

# Validation patterns
# Supports Unicode letters for international skill names
# Pattern: starts with letter/number, segments separated by single hyphens
# Uses Unicode property for letters (\p{L}) - Python re doesn't support \p, so we use a workaround
def _is_valid_skill_name(name: str) -> bool:
    """Check if name is valid kebab-case (supports Unicode letters, must be lowercase)."""
    if not name or name.startswith("-") or name.endswith("-") or "--" in name:
        return False
    # Each segment must contain only lowercase letters or digits (no underscores)
    for segment in name.split("-"):
        if not segment:
            return False
        for char in segment:
            # Must be alphanumeric AND not uppercase (to catch ASCII uppercase)
            if not char.isalnum() or (char.isalpha() and char.isupper()):
                return False
    return True

_VALID_STATUSES = {"pending", "approved", "applied", "rejected"}
_VALID_PRIORITIES = {"required", "optional"}
_VALID_TEMPLATE_TYPES = {"technical-guide", "workflow-skill", "course-tutorial", "brand-enterprise", "tool-utility"}


# =============================================================================
# Helper Functions
# =============================================================================

def _is_dataclass_type(candidate: Any) -> bool:
    """Check if candidate is a dataclass type (not instance)."""
    try:
        return isinstance(candidate, type) and is_dataclass(candidate)
    except TypeError:
        return False


def _coerce_value(expected_type: Any, value: Any) -> Any:
    """Recursively coerce dict/list values to dataclass instances."""
    if value is None:
        return None

    origin = get_origin(expected_type)
    args = get_args(expected_type)

    # Handle Optional[T]
    if origin is Union and type(None) in args:
        non_none = next(arg for arg in args if arg is not type(None))
        return _coerce_value(non_none, value)

    # Handle dataclass types
    if _is_dataclass_type(expected_type):
        if isinstance(value, expected_type):
            return value
        if isinstance(value, dict):
            return expected_type.from_dict(value)

    # Handle List[T]
    if origin in (list, List):
        item_type = args[0] if args else Any
        return [_coerce_value(item_type, item) for item in (value or [])]

    # Handle Dict[K, V]
    if origin in (dict, Dict):
        value_type = args[1] if len(args) > 1 else Any
        return {key: _coerce_value(value_type, item) for key, item in (value or {}).items()}

    return value


def _deserialize(cls: Type[T], payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a dict for dataclass instantiation with proper type coercion."""
    result: Dict[str, Any] = {}
    # Use get_type_hints to resolve forward references
    try:
        type_hints = get_type_hints(cls)
    except Exception:
        # Fallback if type hints can't be resolved
        type_hints = {f.name: f.type for f in fields(cls)}
    
    for field_def in fields(cls):
        key = field_def.name
        if key in payload:
            expected_type = type_hints.get(key, field_def.type)
            result[key] = _coerce_value(expected_type, payload[key])
    return result


# =============================================================================
# Base Class
# =============================================================================

@dataclass
class SerializableSpec:
    """
    Base class for serializable dataclasses.
    
    Provides common serialization methods for all spec types.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, recursively handling nested dataclasses."""
        def convert(obj: Any) -> Any:
            if is_dataclass(obj) and not isinstance(obj, type):
                return {k: convert(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [convert(item) for item in obj]
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj
        return convert(self)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary."""
        return cls(**_deserialize(cls, data))

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        if yaml is None:
            raise ImportError("PyYAML is required for YAML serialization. Install with: pip install pyyaml")
        return yaml.safe_dump(self.to_dict(), allow_unicode=True, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls: Type[T], yaml_str: str) -> T:
        """Deserialize from YAML string."""
        if yaml is None:
            raise ImportError("PyYAML is required for YAML deserialization. Install with: pip install pyyaml")
        return cls.from_dict(yaml.safe_load(yaml_str))

    def save(self, path: Path, format: Optional[str] = None) -> None:
        """Save to file (auto-detect format from extension if not specified)."""
        path = Path(path)
        fmt = format or path.suffix.lstrip(".")
        
        if fmt in ("yaml", "yml"):
            content = self.to_yaml()
        elif fmt == "json":
            content = self.to_json()
        else:
            raise ValueError(f"Unsupported format: {fmt}. Use 'json' or 'yaml'.")
        
        path.write_text(content, encoding="utf-8")

    @classmethod
    def load(cls: Type[T], path: Path, format: Optional[str] = None) -> T:
        """Load from file (auto-detect format from extension if not specified)."""
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        fmt = format or path.suffix.lstrip(".")
        
        if fmt in ("yaml", "yml"):
            return cls.from_yaml(content)
        elif fmt == "json":
            return cls.from_json(content)
        else:
            raise ValueError(f"Unsupported format: {fmt}. Use 'json' or 'yaml'.")


# =============================================================================
# Spec Metadata
# =============================================================================

@dataclass
class SpecMeta(SerializableSpec):
    """
    Metadata for SkillSpec state tracking.
    
    Tracks version, timestamps, and status for future state machine support.
    """
    spec_version: str = "1.0"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: str = "pending"  # pending | approved | applied | rejected
    applied_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def validate(self) -> None:
        """Validate metadata fields."""
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}'. Must be one of: {_VALID_STATUSES}")

    def mark_updated(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now().isoformat()

    def mark_applied(self) -> None:
        """Mark the spec as applied."""
        self.status = "applied"
        self.applied_at = datetime.now().isoformat()
        self.mark_updated()


# =============================================================================
# Section Spec
# =============================================================================

@dataclass
class SectionSpec(SerializableSpec):
    """
    SKILL.md section specification.
    
    Based on patterns observed in real skills like mcp-builder, skill-creator.
    """
    title: str                                              # 章节标题 (e.g., "## Overview")
    purpose: str = ""                                       # 章节目的描述
    expected_content: List[str] = field(default_factory=list)  # 期望包含的内容类型
    subsections: List["SectionSpec"] = field(default_factory=list)  # 嵌套子章节
    priority: str = "required"                              # required | optional

    def validate(self) -> None:
        """Validate section fields."""
        if not self.title or not self.title.strip():
            raise ValueError("Section title is required")
        if not self.purpose or not self.purpose.strip():
            raise ValueError("Section purpose is required")
        if self.priority not in _VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{self.priority}'. Must be one of: {_VALID_PRIORITIES}")
        for subsection in self.subsections:
            if not isinstance(subsection, SectionSpec):
                raise ValueError(f"Subsection must be SectionSpec, got {type(subsection).__name__}")
            subsection.validate()

    def to_markdown(self) -> str:
        """Generate markdown representation."""
        # Use title as-is if it already has markdown heading markers
        if self.title.startswith("#"):
            lines = [self.title]
        else:
            lines = [f"### {self.title}"]
        if self.purpose:
            lines.append(f"*Purpose*: {self.purpose}")
        if self.expected_content:
            lines.append("*Expected*: " + ", ".join(self.expected_content))
        lines.append(f"*Priority*: {self.priority}")
        for sub in self.subsections:
            lines.append("")
            lines.append(sub.to_markdown())
        return "\n".join(lines)


# =============================================================================
# Example, Reference, Script, Asset Specs
# =============================================================================

@dataclass
class ExampleSpec(SerializableSpec):
    """Example specification for SKILL.md."""
    title: str
    code_language: Optional[str] = None
    description: str = ""

    def validate(self) -> None:
        """Validate example fields."""
        if not self.title or not self.title.strip():
            raise ValueError("Example title is required")

    def to_markdown(self) -> str:
        """Generate markdown representation."""
        lines = [f"- **{self.title}**"]
        if self.description:
            lines.append(f"  {self.description}")
        if self.code_language:
            lines.append(f"  Language: `{self.code_language}`")
        return "\n".join(lines)


@dataclass
class ReferenceSpec(SerializableSpec):
    """
    references/ folder content specification.
    
    Based on patterns in mcp-builder and skill-creator.
    """
    filename: str                                           # e.g., "api_docs.md"
    purpose: str = ""                                       # 为什么需要这个参考文件
    content_sources: List[str] = field(default_factory=list)  # 从哪些数据源提取内容
    max_words: int = 10000                                  # 最大字数限制
    include_toc: bool = False                               # 是否包含目录

    def validate(self) -> None:
        """Validate reference fields."""
        if not self.filename or not self.filename.strip():
            raise ValueError("Reference filename is required")

    def to_markdown(self) -> str:
        """Generate markdown representation."""
        lines = [f"- `{self.filename}`: {self.purpose}"]
        if self.content_sources:
            lines.append(f"  Sources: {', '.join(self.content_sources)}")
        return "\n".join(lines)


@dataclass
class ScriptSpec(SerializableSpec):
    """
    scripts/ folder content specification.
    
    Based on patterns in webapp-testing and skill-creator.
    """
    filename: str                                           # e.g., "validate.py"
    purpose: str = ""                                       # 脚本目的
    language: str = "python"                                # python, bash, etc.
    supports_help: bool = True                              # 是否支持 --help 参数

    def validate(self) -> None:
        """Validate script fields."""
        if not self.filename or not self.filename.strip():
            raise ValueError("Script filename is required")

    def to_markdown(self) -> str:
        """Generate markdown representation."""
        return f"- `{self.filename}` ({self.language}): {self.purpose}"


@dataclass
class AssetSpec(SerializableSpec):
    """
    assets/ folder content specification.
    
    Based on patterns in brand-guidelines and frontend design skills.
    """
    filename: str                                           # e.g., "template.html"
    asset_type: str = "file"                                # template, icon, font, boilerplate
    source: Optional[str] = None                            # 从哪里获取
    copy_only: bool = True                                  # 是否仅复制（不加载到上下文）

    def validate(self) -> None:
        """Validate asset fields."""
        if not self.filename or not self.filename.strip():
            raise ValueError("Asset filename is required")

    def to_markdown(self) -> str:
        """Generate markdown representation."""
        line = f"- `{self.filename}` ({self.asset_type})"
        if self.source:
            line += f" from {self.source}"
        return line


# =============================================================================
# Spec Feedback
# =============================================================================

@dataclass
class SpecFeedback(SerializableSpec):
    """
    User feedback data structure for spec rejection workflow.
    
    Captures rejection reason and hints for re-scraping.
    """
    approved: bool = False
    rejection_reason: Optional[str] = None
    suggested_changes: List[str] = field(default_factory=list)
    additional_sources: List[str] = field(default_factory=list)   # 需要补充抓取的来源
    remove_sections: List[str] = field(default_factory=list)      # 需要移除的章节
    add_sections: List[str] = field(default_factory=list)         # 需要添加的章节
    focus_hints: List[str] = field(default_factory=list)          # 抓取时重点关注的内容

    def has_changes(self) -> bool:
        """Check if feedback contains any change requests."""
        return bool(
            self.suggested_changes or 
            self.additional_sources or 
            self.remove_sections or 
            self.add_sections or 
            self.focus_hints
        )

    def to_markdown(self) -> str:
        """Generate markdown representation of feedback."""
        lines = [f"**Approved**: {'Yes' if self.approved else 'No'}"]
        if self.rejection_reason:
            lines.append(f"**Reason**: {self.rejection_reason}")
        if self.suggested_changes:
            lines.append("**Suggested Changes**:")
            lines.extend(f"- {change}" for change in self.suggested_changes)
        if self.additional_sources:
            lines.append("**Additional Sources**:")
            lines.extend(f"- {src}" for src in self.additional_sources)
        if self.add_sections:
            lines.append("**Add Sections**:")
            lines.extend(f"- {sec}" for sec in self.add_sections)
        if self.remove_sections:
            lines.append("**Remove Sections**:")
            lines.extend(f"- {sec}" for sec in self.remove_sections)
        return "\n".join(lines)


# =============================================================================
# Main SkillSpec
# =============================================================================

@dataclass
class SkillSpec(SerializableSpec):
    """
    Complete Skill output specification.
    
    Controls ALL output: SKILL.md, references/, scripts/, assets/.
    Based on Anthropic Agent Skills Spec v1.0 (2025-10-16).
    """
    # === SKILL.md Frontmatter (Required) ===
    name: str = ""                                          # kebab-case, must match folder
    description: str = ""                                   # When Claude should use this skill

    # === SKILL.md Frontmatter (Optional) ===
    license: Optional[str] = None                           # Short license name
    allowed_tools: List[str] = field(default_factory=list)  # Pre-approved tools
    metadata: Dict[str, str] = field(default_factory=dict)  # Client-specific properties

    # === SKILL.md Body ===
    sections: List[SectionSpec] = field(default_factory=list)
    examples: List[ExampleSpec] = field(default_factory=list)
    guidelines: List[str] = field(default_factory=list)

    # === Bundled Resources ===
    references: List[ReferenceSpec] = field(default_factory=list)
    scripts: List[ScriptSpec] = field(default_factory=list)
    assets: List[AssetSpec] = field(default_factory=list)

    # === Generation Control ===
    template_type: Optional[str] = None                     # technical-guide, workflow-skill, etc.
    source_config: Dict[str, Any] = field(default_factory=dict)  # For re-scrape on rejection

    # === Metadata ===
    meta: SpecMeta = field(default_factory=SpecMeta)

    def validate(self) -> None:
        """
        Validate all fields according to Anthropic Agent Skills Spec.
        
        Raises:
            ValueError: If any validation fails.
        """
        errors: List[str] = []

        # Required fields
        if not self.name or not self.name.strip():
            errors.append("name is required")
        elif not _is_valid_skill_name(self.name):
            errors.append(f"name must be kebab-case (letters, digits, hyphens only; got '{self.name}')")

        if not self.description or not self.description.strip():
            errors.append("description is required")

        # Optional field validation
        if self.template_type and self.template_type not in _VALID_TEMPLATE_TYPES:
            errors.append(f"Invalid template_type '{self.template_type}'. Must be one of: {_VALID_TEMPLATE_TYPES}")

        # Validate metadata
        try:
            self.meta.validate()
        except ValueError as e:
            errors.append(f"meta: {e}")

        # Validate nested specs
        for i, section in enumerate(self.sections):
            try:
                section.validate()
            except ValueError as e:
                errors.append(f"sections[{i}]: {e}")

        for i, example in enumerate(self.examples):
            try:
                example.validate()
            except ValueError as e:
                errors.append(f"examples[{i}]: {e}")

        for i, ref in enumerate(self.references):
            try:
                ref.validate()
            except ValueError as e:
                errors.append(f"references[{i}]: {e}")

        for i, script in enumerate(self.scripts):
            try:
                script.validate()
            except ValueError as e:
                errors.append(f"scripts[{i}]: {e}")

        for i, asset in enumerate(self.assets):
            try:
                asset.validate()
            except ValueError as e:
                errors.append(f"assets[{i}]: {e}")

        if errors:
            raise ValueError("Validation failed: " + "; ".join(errors))

    def to_markdown(self) -> str:
        """Generate human-readable markdown summary."""
        lines = [
            f"# Skill Spec: {self.name or 'unnamed'}",
            "",
            f"**Status**: {self.meta.status} (v{self.meta.spec_version})",
            "",
            "## Description",
            self.description or "(no description)",
        ]

        # Allowed tools
        if self.allowed_tools:
            lines.extend(["", "## Allowed Tools"])
            lines.extend(f"- {tool}" for tool in self.allowed_tools)

        # Guidelines
        if self.guidelines:
            lines.extend(["", "## Guidelines"])
            lines.extend(f"- {rule}" for rule in self.guidelines)

        # Sections
        if self.sections:
            lines.extend(["", "## Sections"])
            for section in self.sections:
                lines.extend(["", section.to_markdown()])

        # Examples
        if self.examples:
            lines.extend(["", "## Examples"])
            for example in self.examples:
                lines.extend(["", example.to_markdown()])

        # References
        if self.references:
            lines.extend(["", "## References (references/)"])
            for ref in self.references:
                lines.append(ref.to_markdown())

        # Scripts
        if self.scripts:
            lines.extend(["", "## Scripts (scripts/)"])
            for script in self.scripts:
                lines.append(script.to_markdown())

        # Assets
        if self.assets:
            lines.extend(["", "## Assets (assets/)"])
            for asset in self.assets:
                lines.append(asset.to_markdown())

        return "\n".join(lines)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AssetSpec",
    "ExampleSpec",
    "ReferenceSpec",
    "ScriptSpec",
    "SectionSpec",
    "SerializableSpec",
    "SkillSpec",
    "SpecFeedback",
    "SpecMeta",
]
