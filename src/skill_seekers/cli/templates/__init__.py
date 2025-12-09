"""
Template loader and applier for Skill_Seekers.

Provides helpers to load YAML-based templates, list available templates,
and materialize a SkillSpec with template defaults merged with scraped data.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError as exc:
    yaml = None
    _yaml_import_error = exc
else:
    _yaml_import_error = None

from skill_seekers.core.skill_spec import (
    AssetSpec,
    ReferenceSpec,
    ScriptSpec,
    SectionSpec,
    SkillSpec,
    SpecMeta,
)

TEMPLATES_DIR = Path(__file__).parent


def _require_yaml() -> None:
    """Ensure PyYAML is available before parsing template files."""
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load templates. Install with `pip install pyyaml`."
        ) from _yaml_import_error


def get_template_path(name: str) -> Path:
    """Return the path to a template YAML file by normalized name."""
    normalized = (name or "").strip().lower().replace("_", "-")
    path = TEMPLATES_DIR / f"{normalized}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Template '{name}' not found at {path}")
    return path


def load_template(name: str) -> Dict[str, Any]:
    """Load a template YAML file into a dictionary."""
    _require_yaml()
    path = get_template_path(name)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Template '{name}' is not a YAML mapping")
    return data


def list_templates() -> List[Dict[str, Any]]:
    """
    Return all available templates with their basic info.
    
    Returns:
        List of dicts with name, description, and path for each template.
    """
    _require_yaml()
    templates = []
    for yaml_file in sorted(TEMPLATES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                templates.append({
                    "name": data.get("name", yaml_file.stem),
                    "description": data.get("description", ""),
                    "path": str(yaml_file),
                    "scripts_expected": data.get("scripts_expected", False),
                    "assets_expected": data.get("assets_expected", False),
                })
        except Exception:
            continue  # Skip malformed templates
    return templates


def get_template_names() -> List[str]:
    """Return list of available template names."""
    return [t["name"] for t in list_templates()]


def _build_sections(raw_sections: List[Dict]) -> List[SectionSpec]:
    """Recursively build SectionSpec list from raw YAML data."""
    sections = []
    for item in raw_sections:
        subsections = _build_sections(item.get("subsections", []))
        sections.append(SectionSpec(
            title=item.get("title", ""),
            purpose=item.get("purpose", ""),
            expected_content=item.get("expected_content", []),
            priority=item.get("priority", "required"),
            subsections=subsections,
        ))
    return sections


def _build_references(raw_refs: List[Dict]) -> List[ReferenceSpec]:
    """Build ReferenceSpec list from raw YAML data."""
    return [
        ReferenceSpec(
            filename=item.get("filename", ""),
            purpose=item.get("purpose", ""),
            content_sources=item.get("content_sources", []),
            max_words=item.get("max_words", 10000),
            include_toc=item.get("include_toc", False),
        )
        for item in raw_refs
    ]


def _build_scripts(raw_scripts: List[Dict]) -> List[ScriptSpec]:
    """Build ScriptSpec list from raw YAML data."""
    return [
        ScriptSpec(
            filename=item.get("filename", ""),
            purpose=item.get("purpose", ""),
            language=item.get("language", "python"),
            supports_help=item.get("supports_help", True),
        )
        for item in raw_scripts
    ]


def _build_assets(raw_assets: List[Dict]) -> List[AssetSpec]:
    """Build AssetSpec list from raw YAML data."""
    return [
        AssetSpec(
            filename=item.get("filename", ""),
            asset_type=item.get("asset_type", "file"),
            source=item.get("source"),
            copy_only=item.get("copy_only", True),
        )
        for item in raw_assets
    ]


def _slugify(text: str) -> str:
    """Convert text to kebab-case slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def apply_template(
    template_name: str,
    scraped_data: Optional[Dict[str, Any]] = None,
    skill_name: Optional[str] = None,
    skill_description: Optional[str] = None,
) -> SkillSpec:
    """
    Create a SkillSpec from a template, optionally merging scraped data.
    
    Args:
        template_name: Name of the template to use
        scraped_data: Optional scraped data to merge (for source_config)
        skill_name: Override skill name (auto-generated from template if not provided)
        skill_description: Override skill description
        
    Returns:
        A new SkillSpec with template defaults applied
    """
    template = load_template(template_name)
    
    # Determine skill name
    if skill_name:
        name = _slugify(skill_name)
    elif scraped_data and scraped_data.get("name"):
        name = _slugify(scraped_data["name"])
    else:
        name = f"untitled-{template_name}"
    
    # Determine description
    if skill_description:
        description = skill_description
    elif scraped_data and scraped_data.get("description"):
        description = scraped_data["description"]
    else:
        description = template.get("description", f"A {template_name} skill")
    
    # Build spec components from template
    sections = _build_sections(template.get("default_sections", []))
    references = _build_references(template.get("default_references", []))
    scripts = _build_scripts(template.get("default_scripts", []))
    assets = _build_assets(template.get("default_assets", []))
    
    return SkillSpec(
        name=name,
        description=description,
        sections=sections,
        references=references,
        scripts=scripts,
        assets=assets,
        template_type=template_name,
        source_config=scraped_data or {},
        meta=SpecMeta(),
    )


__all__ = [
    "apply_template",
    "get_template_names",
    "get_template_path",
    "list_templates",
    "load_template",
    "TEMPLATES_DIR",
]
