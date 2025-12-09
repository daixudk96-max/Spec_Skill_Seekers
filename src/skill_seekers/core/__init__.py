"""
Skill Seekers Core Package

Contains core data types and domain logic that can be used by both CLI and MCP layers.
"""

from skill_seekers.core.skill_spec import (
    AssetSpec,
    ExampleSpec,
    ReferenceSpec,
    ScriptSpec,
    SectionSpec,
    SerializableSpec,
    SkillSpec,
    SpecFeedback,
    SpecMeta,
)

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
