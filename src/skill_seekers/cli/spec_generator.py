#!/usr/bin/env python3
"""
Spec Generator for Skill_Seekers

Generates SkillSpec from scraped data (docs, GitHub, transcripts, unified).
Provides template-aware inference for sections, references, scripts, and assets.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from skill_seekers.core.skill_spec import (
    AssetSpec,
    ReferenceSpec,
    ScriptSpec,
    SectionSpec,
    SkillSpec,
)
from skill_seekers.cli.templates import apply_template, get_template_names


# Template fallback when no good match
_TEMPLATE_FALLBACK = "technical-guide"


def _slugify(text: str) -> str:
    """Convert free-form text to a kebab-case slug."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "unnamed-skill"


class SpecGenerator:
    """
    Generate SkillSpec instances from scraped data.
    
    Provides factory methods for different data sources and handles
    template-based inference for skill structure.
    
    Example:
        >>> generator = SpecGenerator.from_docs_scraper(scraped_data)
        >>> spec = generator.generate()
        >>> generator.save(Path("output/my-skill/spec.yaml"))
    """

    def __init__(
        self,
        template_type: str,
        scraped_data: Dict[str, Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        segmented_summary: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize SpecGenerator.
        
        Args:
            template_type: Template to use (technical-guide, workflow-skill, etc.)
            scraped_data: Data from scraper(s)
            name: Override skill name (auto-inferred if not provided)
            description: Override skill description
            segmented_summary: Optional segmented summary data for transcript lessons
        """
        self.template_type = template_type
        self.scraped_data = scraped_data
        self._name_override = name
        self._description_override = description
        self.segmented_summary = segmented_summary
        self._generated_spec: Optional[SkillSpec] = None

    # =========================================================================
    # Factory Methods
    # =========================================================================

    @classmethod
    def from_docs_scraper(
        cls,
        scraped_data: Dict[str, Any],
        name: Optional[str] = None,
    ) -> "SpecGenerator":
        """Create generator from documentation scraper output."""
        return cls(
            template_type="technical-guide",
            scraped_data={"documentation": scraped_data},
            name=name,
        )

    @classmethod
    def from_github_scraper(
        cls,
        scraped_data: Dict[str, Any],
        name: Optional[str] = None,
    ) -> "SpecGenerator":
        """Create generator from GitHub scraper output."""
        # 推断模板类型
        template = "technical-guide"
        if scraped_data.get("is_tool") or scraped_data.get("has_cli"):
            template = "tool-utility"
        
        return cls(
            template_type=template,
            scraped_data={"github": scraped_data},
            name=name or scraped_data.get("repo_name"),
        )

    @classmethod
    def from_transcript_scraper(
        cls,
        scraped_data: Dict[str, Any],
        name: Optional[str] = None,
        segmented_summary: Optional[Dict[str, Any]] = None,
    ) -> "SpecGenerator":
        """
        Create generator from transcript scraper output.
        
        Args:
            scraped_data: Data from transcript scraper
            name: Override skill name (auto-inferred if not provided)
            segmented_summary: Optional segmented summary data from AI analysis
        """
        return cls(
            template_type="course-tutorial",
            scraped_data={"lessons": scraped_data},
            name=name,
            segmented_summary=segmented_summary,
        )

    @classmethod
    def from_unified(
        cls,
        scraped_data: Dict[str, Any],
        template_type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> "SpecGenerator":
        """Create generator from unified multi-source scraper output."""
        # 自动推断模板类型
        if template_type is None:
            template_type = cls._infer_template(scraped_data)
        
        return cls(
            template_type=template_type,
            scraped_data=scraped_data,
            name=name or scraped_data.get("name"),
        )

    # =========================================================================
    # Core Generation
    # =========================================================================

    def generate(self) -> SkillSpec:
        """
        Generate SkillSpec from scraped data and template.
        
        Returns:
            Complete SkillSpec ready for review or application.
        """
        if self._generated_spec is not None:
            return self._generated_spec

        # 融合分段总结数据（如果存在）
        effective_data = self._merge_segmented_summary()

        # 从模板创建基础 spec
        spec = apply_template(
            self.template_type,
            scraped_data=effective_data,
            skill_name=self._name_override or self._infer_name(),
            skill_description=self._description_override or self._infer_description(),
        )

        # 增强 sections, references, scripts, assets
        spec.references = self._augment_references(spec.references, effective_data)
        spec.scripts = self._augment_scripts(spec.scripts, effective_data)
        spec.assets = self._augment_assets(spec.assets, effective_data)

        self._generated_spec = spec
        return spec

    # =========================================================================
    # Inference Methods
    # =========================================================================

    @staticmethod
    def _infer_template(data: Dict[str, Any]) -> str:
        """Infer best template type from scraped data contents."""
        # 包含课程/教程内容
        if "lessons" in data or "transcript" in data:
            return "course-tutorial"
        
        # 主要是工具或 CLI
        github = data.get("github", {})
        if github.get("is_tool") or github.get("has_cli"):
            return "tool-utility"
        
        # 包含品牌/设计资源
        if "brand" in data or "design_system" in data:
            return "brand-enterprise"
        
        # 是元技能/工作流（如 skill-creator）
        if data.get("is_meta_skill") or data.get("creates_skills"):
            return "workflow-skill"
        
        # 默认技术文档
        return "technical-guide"

    def _infer_name(self) -> str:
        """Infer skill name from scraped data."""
        data = self.scraped_data

        # 尝试多个来源
        candidates = [
            data.get("name"),
            data.get("title"),
            data.get("github", {}).get("repo_name"),
            data.get("documentation", {}).get("title"),
            data.get("lessons", {}).get("course_name"),
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str):
                return _slugify(candidate)
        
        return "unnamed-skill"

    def _infer_description(self) -> str:
        """Infer skill description from scraped data."""
        data = self.scraped_data

        candidates = [
            data.get("description"),
            data.get("github", {}).get("description"),
            data.get("documentation", {}).get("summary"),
            data.get("lessons", {}).get("course_description"),
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str):
                return candidate
        
        return f"A {self.template_type} skill generated from scraped data."

    # =========================================================================
    # Augmentation Methods
    # =========================================================================

    def _augment_references(
        self,
        base_refs: List[ReferenceSpec],
        data: Dict[str, Any],
    ) -> List[ReferenceSpec]:
        """Add source-specific references based on scraped data."""
        refs = list(base_refs)
        filenames = {r.filename for r in refs}

        def add_ref(filename: str, purpose: str, sources: List[str] = None) -> None:
            if filename in filenames:
                return
            refs.append(ReferenceSpec(
                filename=filename,
                purpose=purpose,
                content_sources=sources or [],
            ))
            filenames.add(filename)

        # 根据数据源添加参考文件
        if "github" in data:
            add_ref("api_reference.md", "API reference from source code", ["github"])
            add_ref("code_examples.md", "Code examples from repository", ["github"])
        
        if "documentation" in data:
            add_ref("official_docs.md", "Curated official documentation", ["documentation"])
        
        if "lessons" in data:
            add_ref("lesson_notes.md", "Key points from course lessons", ["lessons"])
            add_ref("exercises.md", "Practice exercises and solutions", ["lessons"])

        return refs

    def _augment_scripts(
        self,
        base_scripts: List[ScriptSpec],
        data: Dict[str, Any],
    ) -> List[ScriptSpec]:
        """Add source-specific scripts based on scraped data."""
        scripts = list(base_scripts)
        filenames = {s.filename for s in scripts}

        def add_script(filename: str, purpose: str, language: str = "python") -> None:
            if filename in filenames:
                return
            scripts.append(ScriptSpec(
                filename=filename,
                purpose=purpose,
                language=language,
            ))
            filenames.add(filename)

        # 根据数据源添加脚本
        if "github" in data:
            add_script("sync_repo.py", "Sync repository metadata and examples")
        
        if "documentation" in data:
            add_script("refresh_docs.py", "Re-scrape documentation and update references")
        
        if "lessons" in data:
            add_script("regenerate_summaries.py", "Regenerate lesson summaries from transcripts")

        return scripts

    def _augment_assets(
        self,
        base_assets: List[AssetSpec],
        data: Dict[str, Any],
    ) -> List[AssetSpec]:
        """Add source-specific assets based on scraped data."""
        assets = list(base_assets)
        filenames = {a.filename for a in assets}

        def add_asset(filename: str, asset_type: str, source: str = None) -> None:
            if filename in filenames:
                return
            assets.append(AssetSpec(
                filename=filename,
                asset_type=asset_type,
                source=source,
                copy_only=True,
            ))
            filenames.add(filename)

        # 根据数据源添加资产
        if "github" in data:
            add_asset("raw_data/github/", "folder", "GitHub scraper output")
        
        if "documentation" in data:
            add_asset("raw_data/docs/", "folder", "Documentation scraper output")
        
        if "lessons" in data:
            add_asset("raw_data/transcripts/", "folder", "Transcript scraper output")

        return assets

    # =========================================================================
    # Export Methods
    # =========================================================================

    def save(self, path: Path) -> None:
        """
        Save generated spec to file.
        
        Args:
            path: Output path (format detected from extension: .yaml, .yml, .json)
        """
        spec = self.generate()
        spec.save(path)

    @staticmethod
    def load(path: Path) -> SkillSpec:
        """
        Load SkillSpec from file.
        
        Args:
            path: Path to spec file
            
        Returns:
            Loaded SkillSpec
        """
        return SkillSpec.load(path)

    def export_for_review(self) -> str:
        """
        Generate markdown summary for human review.
        
        Returns:
            Markdown-formatted spec summary
        """
        spec = self.generate()
        
        lines = [
            "# Skill Spec Review",
            "",
            f"**Name**: `{spec.name}`",
            f"**Template**: {spec.template_type}",
            f"**Status**: {spec.meta.status}",
            "",
            "## Description",
            spec.description,
            "",
            "---",
            "",
            spec.to_markdown(),
            "",
            "---",
            "",
            "## Review Actions",
            "",
            "- [ ] Approve this spec",
            "- [ ] Request changes",
            "- [ ] Reject and re-scrape",
        ]
        
        return "\n".join(lines)

    def export_spec_file(self, path: Path) -> None:
        """
        Export spec to YAML file (convenience wrapper).
        
        Args:
            path: Output path for YAML file
        """
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix(".yaml")
        self.save(path)

    # =========================================================================
    # Segmented Summary Support
    # =========================================================================

    @staticmethod
    def load_segmented_summary(path: Path) -> Dict[str, Any]:
        """
        Load segmented summary from JSON file.
        
        Reads the segmented_summary.json file generated by AI assistant
        during the transcript analysis workflow.
        
        Args:
            path: Path to segmented_summary.json file
            
        Returns:
            Parsed segmented summary data, or empty dict if file not found.
            
        Example:
            >>> summary = SpecGenerator.load_segmented_summary(
            ...     Path("output/myskill/segmented_summary.json")
            ... )
            >>> gen = SpecGenerator.from_transcript_scraper(
            ...     scraped_data, segmented_summary=summary
            ... )
        """
        path = Path(path)
        if not path.exists():
            return {}
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 基本验证
            if not isinstance(data, dict):
                return {}
            
            # 验证版本兼容性（当前支持 1.0）
            version = data.get("version", "1.0")
            if version not in ("1.0",):
                # 未来版本可在此添加迁移逻辑
                pass
            
            return data
        except (json.JSONDecodeError, OSError):
            return {}

    def _merge_segmented_summary(self) -> Dict[str, Any]:
        """
        Merge segmented summary into scraped data for spec generation.
        
        Creates a deep copy of scraped_data and enriches the lessons
        structure with segment information when available.
        
        Returns:
            Merged data dict with segmented summary integrated into lessons.
        """
        # 无分段数据时直接返回原始数据
        if not self.segmented_summary:
            return self.scraped_data
        
        # 深拷贝避免修改原始数据
        merged = copy.deepcopy(self.scraped_data)
        
        # 获取或创建 lessons 容器
        lessons_container = merged.get("lessons", {})
        if not isinstance(lessons_container, dict):
            # 如果 lessons 是 list 或其他类型，包装为 dict
            lessons_container = {"lessons": lessons_container}
            merged["lessons"] = lessons_container
        
        # 添加分段总结元数据
        lessons_container["segmented_summary"] = self.segmented_summary
        
        # 提取分段列表
        segments = self.segmented_summary.get("segments", [])
        if not isinstance(segments, list):
            segments = []
        
        # 将分段列表附加到最匹配的 lesson
        self._attach_segments_to_lessons(
            lessons=lessons_container.get("lessons"),
            segments=segments,
            source_file=self.segmented_summary.get("source_file"),
        )
        
        return merged

    def _attach_segments_to_lessons(
        self,
        lessons: Any,
        segments: List[Dict[str, Any]],
        source_file: Optional[str],
    ) -> None:
        """
        Attach segment list to the best-matching lesson entry in-place.
        
        Matching strategy:
        1. Exact source_path/path match with source_file
        2. source_file stem contained in lesson title
        3. First lesson as fallback
        
        Args:
            lessons: List of lesson dicts or None
            segments: List of segment dicts to attach
            source_file: Original source filename for matching
        """
        if not segments or not isinstance(lessons, list):
            return
        
        normalized_source = Path(source_file).name.lower() if source_file else None
        source_stem = Path(source_file).stem.lower() if source_file else None
        primary_match: Optional[Dict[str, Any]] = None
        
        for lesson in lessons:
            if not isinstance(lesson, dict):
                continue
            
            # 默认使用第一个有效 lesson
            if primary_match is None:
                primary_match = lesson
            
            if not normalized_source:
                continue
            
            # 策略 1：精确路径匹配
            lesson_path = lesson.get("source_path") or lesson.get("path")
            if lesson_path and Path(lesson_path).name.lower() == normalized_source:
                primary_match = lesson
                break
            
            # 策略 2：标题包含源文件名
            title = lesson.get("title", "")
            if source_stem and title and source_stem in title.lower():
                primary_match = lesson
                break
        
        # 附加分段数据（不覆盖已有数据）
        if primary_match is not None:
            primary_match.setdefault("segments", segments)


__all__ = ["SpecGenerator"]
